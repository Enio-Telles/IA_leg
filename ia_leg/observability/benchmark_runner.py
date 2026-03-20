"""
Runner de benchmark do IA_leg.

Mede:
- recuperação de contexto
- presença de fallback
- presença de âncoras verificáveis
- presença de palavras esperadas
- tempo por etapa

Uso:
    python -m ia_leg.observability.benchmark_runner
    python -m ia_leg.observability.benchmark_runner --backend ollama --output benchmark_resultados.json
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

from ia_leg.rag.answer_engine import definir_filtros_por_pergunta
from ia_leg.rag.answer_engine_safe import consultar_seguro
from ia_leg.rag.citation_guard import possui_ancoras_verificaveis, score_maximo
from ia_leg.rag.retriever import recuperar_contexto

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_QUERY_FILE = BASE_DIR / "benchmark_queries.json"
DEFAULT_OUTPUT_FILE = BASE_DIR / "benchmark_resultados.json"


FALLBACK_MARKERS = [
    "Resultado seguro",
    "Fontes verificadas",
    "base suficiente",
    "trechos mais relevantes localizados",
]


def carregar_queries(path: Path) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)



def contem_qualquer(texto: str, termos: List[str]) -> bool:
    texto_norm = (texto or "").lower()
    return any((termo or "").lower() in texto_norm for termo in termos)



def avaliar_query(item: Dict[str, Any], backend: str = "ollama", top_k: int = 5, min_score: float = 0.20) -> Dict[str, Any]:
    pergunta = item["pergunta"]
    expected_keywords = item.get("expected_keywords", [])
    expected_anchor_terms = item.get("expected_anchor_terms", [])

    filtros = definir_filtros_por_pergunta(pergunta)

    t0 = time.time()
    contextos, search_time_ms = recuperar_contexto(pergunta, top_k=top_k * 2, filtro_tipos=filtros)
    retrieval_elapsed_ms = (time.time() - t0) * 1000

    top_contextos = contextos[:top_k] if contextos else []
    max_score = score_maximo(top_contextos)

    t1 = time.time()
    resposta = consultar_seguro(
        pergunta,
        top_k=top_k,
        backend=backend,
        min_score=min_score,
        exigir_ancoras=True,
    )
    answer_elapsed_ms = (time.time() - t1) * 1000

    fallback = contem_qualquer(resposta, FALLBACK_MARKERS)
    anchor_terms_ok = contem_qualquer(resposta, expected_anchor_terms) if expected_anchor_terms else True
    keywords_ok = contem_qualquer(resposta, expected_keywords) if expected_keywords else True
    source_anchor_ok = possui_ancoras_verificaveis(resposta, top_contextos) if top_contextos else False

    return {
        "id": item.get("id"),
        "pergunta": pergunta,
        "backend": backend,
        "filtros": filtros,
        "context_count": len(contextos),
        "max_score": max_score,
        "retrieval_time_ms": retrieval_elapsed_ms,
        "search_time_ms": search_time_ms,
        "answer_time_ms": answer_elapsed_ms,
        "fallback": fallback,
        "keywords_ok": keywords_ok,
        "anchor_terms_ok": anchor_terms_ok,
        "source_anchor_ok": source_anchor_ok,
        "top_context_identifiers": [ctx.get("identificador") for ctx in top_contextos],
        "top_context_normas": [ctx.get("norma") for ctx in top_contextos],
        "resposta_preview": resposta[:700],
    }



def resumir_resultados(resultados: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not resultados:
        return {
            "total_queries": 0,
            "fallback_rate": 0.0,
            "keywords_ok_rate": 0.0,
            "anchor_terms_ok_rate": 0.0,
            "source_anchor_ok_rate": 0.0,
            "avg_retrieval_time_ms": 0.0,
            "avg_answer_time_ms": 0.0,
            "avg_max_score": 0.0,
        }

    total = len(resultados)
    return {
        "total_queries": total,
        "fallback_rate": sum(1 for r in resultados if r["fallback"]) / total,
        "keywords_ok_rate": sum(1 for r in resultados if r["keywords_ok"]) / total,
        "anchor_terms_ok_rate": sum(1 for r in resultados if r["anchor_terms_ok"]) / total,
        "source_anchor_ok_rate": sum(1 for r in resultados if r["source_anchor_ok"]) / total,
        "avg_retrieval_time_ms": mean(r["retrieval_time_ms"] for r in resultados),
        "avg_answer_time_ms": mean(r["answer_time_ms"] for r in resultados),
        "avg_max_score": mean(r["max_score"] for r in resultados),
    }



def executar_benchmark(query_file: Path, output_file: Path, backend: str = "ollama", top_k: int = 5, min_score: float = 0.20) -> Dict[str, Any]:
    queries = carregar_queries(query_file)
    resultados = [avaliar_query(item, backend=backend, top_k=top_k, min_score=min_score) for item in queries]
    resumo = resumir_resultados(resultados)
    payload = {
        "query_file": str(query_file),
        "backend": backend,
        "top_k": top_k,
        "min_score": min_score,
        "summary": resumo,
        "results": resultados,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return payload



def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark do IA_leg")
    parser.add_argument("--query-file", default=str(DEFAULT_QUERY_FILE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_FILE))
    parser.add_argument("--backend", default="ollama", choices=["ollama", "openai"])
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--min-score", type=float, default=0.20)
    args = parser.parse_args()

    payload = executar_benchmark(
        query_file=Path(args.query_file),
        output_file=Path(args.output),
        backend=args.backend,
        top_k=args.top_k,
        min_score=args.min_score,
    )

    summary = payload["summary"]
    print("=" * 60)
    print("BENCHMARK IA_leg")
    print("=" * 60)
    print(f"Queries:              {summary['total_queries']}")
    print(f"Fallback rate:       {summary['fallback_rate']:.1%}")
    print(f"Keywords OK rate:    {summary['keywords_ok_rate']:.1%}")
    print(f"Anchor terms rate:   {summary['anchor_terms_ok_rate']:.1%}")
    print(f"Source anchor rate:  {summary['source_anchor_ok_rate']:.1%}")
    print(f"Avg retrieval ms:    {summary['avg_retrieval_time_ms']:.2f}")
    print(f"Avg answer ms:       {summary['avg_answer_time_ms']:.2f}")
    print(f"Avg max score:       {summary['avg_max_score']:.4f}")
    print(f"Saída salva em:      {args.output}")


if __name__ == "__main__":
    main()
