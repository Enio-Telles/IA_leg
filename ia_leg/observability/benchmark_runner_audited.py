"""
Runner de benchmark auditado do IA_leg.

Usa a trilha segura detalhada para gerar benchmark com:
- motivo de fallback
- score máximo
- fontes usadas
- tempos por etapa
- validação de palavras e âncoras esperadas

Uso:
    python -m ia_leg.observability.benchmark_runner_audited
    python -m ia_leg.observability.benchmark_runner_audited --query-file ia_leg/observability/benchmark_queries_sefin_expanded.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

from ia_leg.rag.answer_engine_safe_audited import consultar_seguro_detalhado

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_QUERY_FILE = BASE_DIR / "benchmark_queries_sefin_expanded.json"
DEFAULT_OUTPUT_FILE = BASE_DIR / "benchmark_resultados_auditados.json"


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

    detalhado = consultar_seguro_detalhado(
        pergunta,
        top_k=top_k,
        backend=backend,
        min_score=min_score,
        exigir_ancoras=True,
    )

    resposta = detalhado.get("response", "")
    fallback_reason = detalhado.get("fallback_reason")
    fallback = bool(fallback_reason) or contem_qualquer(resposta, FALLBACK_MARKERS)
    anchor_terms_ok = contem_qualquer(resposta, expected_anchor_terms) if expected_anchor_terms else True
    keywords_ok = contem_qualquer(resposta, expected_keywords) if expected_keywords else True

    return {
        "id": item.get("id"),
        "pergunta": pergunta,
        "backend": backend,
        "filtros": detalhado.get("filtros"),
        "context_count": detalhado.get("context_count", 0),
        "max_score": detalhado.get("max_score", 0.0),
        "search_time_ms": detalhado.get("search_time_ms", 0.0),
        "rerank_time_ms": detalhado.get("rerank_time_ms", 0.0),
        "llm_time_ms": detalhado.get("llm_time_ms", 0.0),
        "total_time_ms": detalhado.get("total_time_ms", 0.0),
        "fallback": fallback,
        "fallback_reason": fallback_reason,
        "keywords_ok": keywords_ok,
        "anchor_terms_ok": anchor_terms_ok,
        "source_anchor_ok": detalhado.get("source_anchor_ok", False),
        "source_identifiers": detalhado.get("source_identifiers", []),
        "source_normas": detalhado.get("source_normas", []),
        "response_preview": detalhado.get("response_preview", ""),
    }



def resumir_resultados(resultados: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not resultados:
        return {
            "total_queries": 0,
            "fallback_rate": 0.0,
            "keywords_ok_rate": 0.0,
            "anchor_terms_ok_rate": 0.0,
            "source_anchor_ok_rate": 0.0,
            "avg_search_time_ms": 0.0,
            "avg_rerank_time_ms": 0.0,
            "avg_llm_time_ms": 0.0,
            "avg_total_time_ms": 0.0,
            "avg_max_score": 0.0,
            "avg_context_count": 0.0,
            "fallback_reasons": {},
        }

    total = len(resultados)
    fallback_reasons: Dict[str, int] = {}
    for r in resultados:
        motivo = r.get("fallback_reason") or "sem_fallback"
        fallback_reasons[motivo] = fallback_reasons.get(motivo, 0) + 1

    return {
        "total_queries": total,
        "fallback_rate": sum(1 for r in resultados if r["fallback"]) / total,
        "keywords_ok_rate": sum(1 for r in resultados if r["keywords_ok"]) / total,
        "anchor_terms_ok_rate": sum(1 for r in resultados if r["anchor_terms_ok"]) / total,
        "source_anchor_ok_rate": sum(1 for r in resultados if r["source_anchor_ok"]) / total,
        "avg_search_time_ms": mean(r["search_time_ms"] for r in resultados),
        "avg_rerank_time_ms": mean(r["rerank_time_ms"] for r in resultados),
        "avg_llm_time_ms": mean(r["llm_time_ms"] for r in resultados),
        "avg_total_time_ms": mean(r["total_time_ms"] for r in resultados),
        "avg_max_score": mean(r["max_score"] for r in resultados),
        "avg_context_count": mean(r["context_count"] for r in resultados),
        "fallback_reasons": fallback_reasons,
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
    parser = argparse.ArgumentParser(description="Benchmark auditado do IA_leg")
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
    print("BENCHMARK IA_leg — AUDITADO")
    print("=" * 60)
    print(f"Queries:              {summary['total_queries']}")
    print(f"Fallback rate:       {summary['fallback_rate']:.1%}")
    print(f"Keywords OK rate:    {summary['keywords_ok_rate']:.1%}")
    print(f"Anchor terms rate:   {summary['anchor_terms_ok_rate']:.1%}")
    print(f"Source anchor rate:  {summary['source_anchor_ok_rate']:.1%}")
    print(f"Avg search ms:       {summary['avg_search_time_ms']:.2f}")
    print(f"Avg rerank ms:       {summary['avg_rerank_time_ms']:.2f}")
    print(f"Avg llm ms:          {summary['avg_llm_time_ms']:.2f}")
    print(f"Avg total ms:        {summary['avg_total_time_ms']:.2f}")
    print(f"Avg max score:       {summary['avg_max_score']:.4f}")
    print(f"Avg contexts:        {summary['avg_context_count']:.2f}")
    print(f"Fallback reasons:    {summary['fallback_reasons']}")
    print(f"Saída salva em:      {args.output}")


if __name__ == "__main__":
    main()
