"""
Reranker cross-encoder para refinar resultados da busca vetorial.
Segunda passada de relevância que melhora a precisão das respostas do RAG.
"""

import torch
from typing import List, Dict

_RERANKER = None


def carregar_reranker():
    """Carrega o modelo cross-encoder para reranking.
    Usa GPU automaticamente se disponível."""
    global _RERANKER
    if _RERANKER is None:
        try:
            from sentence_transformers import CrossEncoder
        except ImportError:
            raise ImportError("Instale 'sentence-transformers' para usar o reranker")

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Carregando reranker no dispositivo: {device}")
        _RERANKER = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", device=device)
    return _RERANKER


def rerankar(pergunta: str, candidatos: List[Dict], top_k: int = 3) -> List[Dict]:
    """
    Reordena candidatos usando cross-encoder para scores mais precisos.

    Args:
        pergunta: Pergunta do usuário.
        candidatos: Lista de dicts do retriever com chave 'texto'.
        top_k: Número de resultados a retornar.
    Returns:
        Lista reordenada com os top_k mais relevantes.
    """
    if not candidatos:
        return []

    reranker = carregar_reranker()
    pares = [(pergunta, c["texto"]) for c in candidatos]
    scores = reranker.predict(pares)

    for i, c in enumerate(candidatos):
        c["score_rerank"] = float(scores[i])

    candidatos.sort(key=lambda x: x["score_rerank"], reverse=True)
    return candidatos[:top_k]
