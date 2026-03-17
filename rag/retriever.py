"""
Recupera trechos normativos com filtro temporal.
Otimizado com cache em memória para performance.
"""


import sqlite3
import numpy as np
from typing import List, Dict

from config import DB_PATH
from rag.embeddings import carregar_modelo

# ─────────────────────────────────────────────────────────
# CACHE DE VETORES EM MEMÓRIA
# ─────────────────────────────────────────────────────────

_VETORES_CACHE = None
_METADADOS_CACHE = None
_MATRIX_CACHE = None


def _carregar_vetores():
    """Carrega todos os vetores e metadados do banco uma única vez.
    Armazena em memória para buscas subsequentes instantâneas."""
    global _VETORES_CACHE, _METADADOS_CACHE, _MATRIX_CACHE

    if _MATRIX_CACHE is not None:
        return _METADADOS_CACHE, _MATRIX_CACHE

    print("Carregando vetores na memória (primeira vez)...")
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
    _MATRIX_CACHE = np.vstack(vetores)  # Matriz (N, dim) para dot-product vetorizado
    print(f"  {len(metadados)} vetores carregados ({_MATRIX_CACHE.shape})")
    return _METADADOS_CACHE, _MATRIX_CACHE


def invalidar_cache():
    """Força recarga dos vetores (chamar após re-indexação)."""
    global _VETORES_CACHE, _METADADOS_CACHE, _MATRIX_CACHE
    _VETORES_CACHE = None
    _METADADOS_CACHE = None
    _MATRIX_CACHE = None
    print("Cache de vetores invalidado.")


def recuperar_contexto(pergunta: str, top_k: int = 5, filtro_tipos: List[str] = None) -> List[Dict]:
    """
    Retorna documentos mais relevantes baseados na pergunta.
    Usa cache em memória e operações vetorizadas com numpy.
    Opcionalmente filtra por uma lista de `filtro_tipos` (ex: ["Guia_Pratico_EFD", "Parecer"]).
    """
    metadados, matrix = _carregar_vetores()

    if len(metadados) == 0:
        return []

    # Gerar vetor da query
    modelo = carregar_modelo()
    vetor_query = modelo.encode([pergunta], normalize_embeddings=True)[0]

    # Busca vetorizada: dot-product de uma vez com toda a matriz
    scores = matrix @ vetor_query  # (N,) = (N, dim) @ (dim,)
    
    # Se houver filtro de tipos, zeramos os scores de quem não passar no filtro
    if filtro_tipos:
        filtro_tipos = [t.lower() for t in filtro_tipos]
        mask = np.array([m["tipo"].lower() in filtro_tipos for m in metadados])
        scores = np.where(mask, scores, -9999.0)

    # Top-K mais eficiente com argpartition
    k = min(top_k, len(scores))
    top_indices = np.argpartition(scores, -k)[-k:]
    top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]

    resultados = []
    for idx in top_indices:
        if scores[idx] > -9998.0: # Ignorar os que foram zerados pelo filtro
            resultado = metadados[idx].copy()
            resultado["score"] = float(scores[idx])
            resultados.append(resultado)

    return resultados


if __name__ == "__main__":
    resp = recuperar_contexto("Aliquota de combustivel aviação")
    for r in resp:
        print(f"Score: {r['score']:.4f} | {r['norma']} - {r['identificador']}")
        print(f"{r['texto'][:100]}...\n")

