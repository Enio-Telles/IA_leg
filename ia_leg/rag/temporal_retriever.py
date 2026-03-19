"""
Retriever temporal para consultas normativas com recorte de vigência.

Objetivo:
- permitir buscas vetoriais considerando a legislação vigente em uma data específica;
- manter compatibilidade conceitual com o retriever principal do projeto;
- oferecer cache por versão do índice + data de referência + filtros.
"""

from __future__ import annotations

import hashlib
import sqlite3
import time
from typing import Dict, List, Optional, Tuple

import numpy as np

from ia_leg.core.config.settings import DB_PATH
from ia_leg.rag.embedding_service import carregar_modelo

# Cache em memória por chave lógica do índice temporal
_VECTOR_CACHE: Dict[str, np.ndarray] = {}
_METADATA_CACHE: Dict[str, List[Dict]] = {}
_QUERY_CACHE: Dict[str, List[Dict]] = {}


def _normalizar_data(data_referencia: Optional[str]) -> str:
    """Normaliza a data para uso interno no cache."""
    return (data_referencia or "vigente").strip()


def obter_versao_indice() -> str:
    """Obtém a versão atual do índice vetorial baseada na última carga em embeddings."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(criado_em) FROM embeddings")
        ultima_data = cursor.fetchone()[0]
        conn.close()
        return ultima_data or "v0"
    except Exception:
        return "v0"


def invalidar_cache_temporal() -> None:
    """Limpa todos os caches temporais."""
    _VECTOR_CACHE.clear()
    _METADATA_CACHE.clear()
    _QUERY_CACHE.clear()
    print("Cache temporal invalidado.")


def _cache_key_base(data_referencia: Optional[str]) -> str:
    return f"{obter_versao_indice()}::{_normalizar_data(data_referencia)}"


def _query_hash(
    pergunta: str,
    data_referencia: Optional[str] = None,
    filtro_tipos: Optional[List[str]] = None,
) -> str:
    chave = {
        "pergunta": pergunta.strip(),
        "data_referencia": _normalizar_data(data_referencia),
        "filtro_tipos": sorted([t.lower() for t in (filtro_tipos or [])]),
        "versao_indice": obter_versao_indice(),
    }
    return hashlib.sha256(str(chave).encode("utf-8")).hexdigest()


def _montar_sql(data_referencia: Optional[str]) -> Tuple[str, Tuple]:
    base_sql = """
        SELECT
            e.dispositivo_id,
            d.versao_id,
            d.identificador,
            d.texto,
            n.tipo,
            n.numero,
            n.ano,
            n.tema,
            v.vigencia_inicio,
            v.vigencia_fim,
            e.vetor
        FROM embeddings e
        JOIN dispositivos d ON e.dispositivo_id = d.id
        JOIN versoes_norma v ON d.versao_id = v.id
        JOIN normas n ON v.norma_id = n.id
    """

    if data_referencia:
        sql = (
            base_sql
            + """
            WHERE v.vigencia_inicio <= ?
              AND (v.vigencia_fim IS NULL OR v.vigencia_fim > ?)
            """
        )
        return sql, (data_referencia, data_referencia)

    sql = base_sql + " WHERE v.vigencia_fim IS NULL "
    return sql, tuple()


def _carregar_vetores_temporais(
    data_referencia: Optional[str] = None,
) -> Tuple[List[Dict], np.ndarray]:
    """Carrega vetores e metadados conforme a data de vigência solicitada."""
    chave = _cache_key_base(data_referencia)
    if chave in _VECTOR_CACHE and chave in _METADATA_CACHE:
        return _METADATA_CACHE[chave], _VECTOR_CACHE[chave]

    sql, params = _montar_sql(data_referencia)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(sql, params)
    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        _METADATA_CACHE[chave] = []
        _VECTOR_CACHE[chave] = np.array([])
        return _METADATA_CACHE[chave], _VECTOR_CACHE[chave]

    metadados: List[Dict] = []
    vetores = []

    for row in resultados:
        (
            dispositivo_id,
            versao_id,
            identificador,
            texto,
            tipo,
            numero,
            ano,
            tema,
            vigencia_inicio,
            vigencia_fim,
            vetor_bytes,
        ) = row

        metadados.append(
            {
                "id": dispositivo_id,
                "versao_id": versao_id,
                "norma": f"{tipo} {numero}/{ano}" if numero != "S/N" else f"{tipo} do Ano {ano}",
                "identificador": identificador,
                "texto": texto,
                "tipo": tipo,
                "tema": tema,
                "vigencia_inicio": vigencia_inicio,
                "vigencia_fim": vigencia_fim,
            }
        )
        vetores.append(np.frombuffer(vetor_bytes, dtype=np.float32))

    _METADATA_CACHE[chave] = metadados
    _VECTOR_CACHE[chave] = np.vstack(vetores)
    return _METADATA_CACHE[chave], _VECTOR_CACHE[chave]


def recuperar_contexto_temporal(
    pergunta: str,
    top_k: int = 5,
    filtro_tipos: Optional[List[str]] = None,
    data_referencia: Optional[str] = None,
) -> Tuple[List[Dict], float]:
    """
    Recupera contexto considerando a data de vigência informada.

    Args:
        pergunta: pergunta do usuário.
        top_k: quantidade de trechos desejada.
        filtro_tipos: tipos documentais permitidos.
        data_referencia: data no formato YYYY-MM-DD. Se None, usa a base vigente atual.

    Returns:
        (resultados, tempo_ms)
    """
    inicio = time.time()
    chave_query = _query_hash(pergunta, data_referencia=data_referencia, filtro_tipos=filtro_tipos)
    if chave_query in _QUERY_CACHE:
        return _QUERY_CACHE[chave_query], (time.time() - inicio) * 1000

    metadados, matrix = _carregar_vetores_temporais(data_referencia=data_referencia)
    if len(metadados) == 0:
        return [], 0.0

    modelo = carregar_modelo()
    vetor_query = modelo.encode([pergunta], normalize_embeddings=True)[0]
    scores = matrix @ vetor_query

    if filtro_tipos:
        tipos_norm = [t.lower() for t in filtro_tipos]
        mask = np.array([m["tipo"].lower() in tipos_norm for m in metadados])
        scores = np.where(mask, scores, -9999.0)

    k = min(top_k, len(scores))
    top_indices = np.argpartition(scores, -k)[-k:]
    top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]

    resultados: List[Dict] = []
    for idx in top_indices:
        if scores[idx] > -9998.0:
            item = metadados[idx].copy()
            item["score"] = float(scores[idx])
            resultados.append(item)

    _QUERY_CACHE[chave_query] = resultados
    return resultados, (time.time() - inicio) * 1000


if __name__ == "__main__":
    consulta = "prazo de recolhimento do ICMS"
    resultados, tempo_ms = recuperar_contexto_temporal(
        consulta,
        top_k=5,
        data_referencia=None,
    )
    print(f"Consulta: {consulta}")
    print(f"Resultados: {len(resultados)} | Tempo: {tempo_ms:.2f}ms")
    for r in resultados:
        print(
            f"- {r['norma']} | {r['identificador']} | vigência: {r['vigencia_inicio']} -> {r['vigencia_fim']}"
        )
