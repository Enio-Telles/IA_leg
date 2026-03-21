"""
Recupera trechos normativos com filtro temporal.
Otimizado com cache em memória baseado em versão do índice e queries repetidas.
"""

import sqlite3
import numpy as np
import hashlib
import time
from typing import List, Dict, Tuple

from ia_leg.core.config.settings import DB_PATH
from ia_leg.rag.embedding_service import carregar_modelo

# ─────────────────────────────────────────────────────────
# CACHE DE VETORES EM MEMÓRIA
# ─────────────────────────────────────────────────────────

_METADADOS_CACHE = None
_MATRIX_CACHE = None
_INDEX_VERSION = None

# Cache de queries repetidas
_QUERY_CACHE = {}


def obter_versao_indice() -> str:
    """Obtém a versão atual do índice vetorial baseada na data da última indexação."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # O(1) index lookup using primary key instead of O(N) full table scan on unindexed criado_em
        cursor.execute("SELECT criado_em FROM embeddings ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        ultima_data = row[0] if row else None
        conn.close()
        return ultima_data or "v0"
    except Exception:
        return "v0"


def invalidar_cache():
    """Força recarga dos vetores e limpa queries (chamar após re-indexação)."""
    global _METADADOS_CACHE, _MATRIX_CACHE, _INDEX_VERSION, _QUERY_CACHE
    _METADADOS_CACHE = None
    _MATRIX_CACHE = None
    _INDEX_VERSION = None
    _QUERY_CACHE.clear()
    print("Cache de vetores invalidado.")


def _carregar_vetores():
    """Carrega todos os vetores e metadados do banco, gerenciando a versão do cache."""
    global _METADADOS_CACHE, _MATRIX_CACHE, _INDEX_VERSION, _QUERY_CACHE

    versao_atual = obter_versao_indice()

    if _MATRIX_CACHE is not None and _INDEX_VERSION == versao_atual:
        return _METADADOS_CACHE, _MATRIX_CACHE

    print(f"Carregando vetores na memória (versão: {versao_atual})...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT e.dispositivo_id, d.identificador, d.texto,
               n.tipo, n.numero, n.ano, n.tema, e.vetor
        FROM embeddings e
        JOIN dispositivos d ON e.dispositivo_id = d.id
        JOIN versoes_norma v ON d.versao_id = v.id
        JOIN normas n ON v.norma_id = n.id
        WHERE v.vigencia_fim IS NULL
    ''')
    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        _METADADOS_CACHE = []
        _MATRIX_CACHE = np.array([])
        _INDEX_VERSION = versao_atual
        return _METADADOS_CACHE, _MATRIX_CACHE

    # Separar metadados e vetores para operação vetorizada
    metadados = []
    vetores = []
    for row in resultados:
        disp_id, ident, texto, tipo, num, ano, tema, vetor_bytes = row
        metadados.append({
            "id": disp_id,
            "norma": f"{tipo} {num}/{ano}" if num != "S/N" else f"{tipo} do Ano {ano}",
            "identificador": ident,
            "texto": texto,
            "tipo": tipo,
            "tema": tema
        })
        vetores.append(np.frombuffer(vetor_bytes, dtype=np.float32))

    _METADADOS_CACHE = metadados
    _MATRIX_CACHE = np.vstack(vetores)
    _INDEX_VERSION = versao_atual

    # Limpar cache de queries pois o índice base mudou
    _QUERY_CACHE.clear()

    print(f"  {len(metadados)} vetores carregados ({_MATRIX_CACHE.shape})")
    return _METADADOS_CACHE, _MATRIX_CACHE


def _gerar_hash_query(pergunta: str, filtros: List[str] = None) -> str:
    """Gera um hash único para a query + filtros."""
    chave = pergunta + (str(sorted(filtros)) if filtros else "")
    return hashlib.sha256(chave.encode('utf-8')).hexdigest()


def recuperar_contexto(pergunta: str, top_k: int = 5, filtro_tipos: List[str] = None) -> Tuple[List[Dict], float]:
    """
    Retorna documentos relevantes baseados na pergunta.
    Retorna a lista de contextos e o tempo de busca_ms.
    """
    inicio = time.time()

    # Verificar cache de queries
    hash_query = _gerar_hash_query(pergunta, filtro_tipos)
    if hash_query in _QUERY_CACHE:
        return _QUERY_CACHE[hash_query], (time.time() - inicio) * 1000

    metadados, matrix = _carregar_vetores()

    if len(metadados) == 0:
        return [], 0.0

    # Gerar vetor da query
    modelo = carregar_modelo()
    vetor_query = modelo.encode([pergunta], normalize_embeddings=True)[0]

    # Busca vetorizada: dot-product
    scores = matrix @ vetor_query  # (N,)
    
    # Filtro
    if filtro_tipos:
        filtro_tipos = [t.lower() for t in filtro_tipos]
        mask = np.array([m["tipo"].lower() in filtro_tipos for m in metadados])
        scores = np.where(mask, scores, -9999.0)

    # Top-K
    k = min(top_k, len(scores))
    top_indices = np.argpartition(scores, -k)[-k:]
    top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]

    resultados = []
    for idx in top_indices:
        if scores[idx] > -9998.0:
            resultado = metadados[idx].copy()
            resultado["score"] = float(scores[idx])
            resultados.append(resultado)

    _QUERY_CACHE[hash_query] = resultados
    tempo_ms = (time.time() - inicio) * 1000

    return resultados, tempo_ms

