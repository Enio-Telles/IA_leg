from ia_leg.observability.benchmark_runner_audited import resumir_resultados


def test_resumo_resultados_auditados():
    resultados = [
        {
            "fallback": True,
            "fallback_reason": "score_baixo",
            "keywords_ok": True,
            "anchor_terms_ok": False,
            "source_anchor_ok": False,
            "search_time_ms": 10.0,
            "rerank_time_ms": 5.0,
            "llm_time_ms": 0.0,
            "total_time_ms": 20.0,
            "max_score": 0.1,
            "context_count": 3,
        },
        {
            "fallback": False,
            "fallback_reason": None,
            "keywords_ok": True,
            "anchor_terms_ok": True,
            "source_anchor_ok": True,
            "search_time_ms": 20.0,
            "rerank_time_ms": 10.0,
            "llm_time_ms": 100.0,
            "total_time_ms": 140.0,
            "max_score": 0.8,
            "context_count": 5,
        },
    ]

    resumo = resumir_resultados(resultados)

    assert resumo["total_queries"] == 2
    assert resumo["fallback_rate"] == 0.5
    assert resumo["keywords_ok_rate"] == 1.0
    assert resumo["anchor_terms_ok_rate"] == 0.5
    assert resumo["source_anchor_ok_rate"] == 0.5
    assert resumo["avg_search_time_ms"] == 15.0
    assert resumo["avg_rerank_time_ms"] == 7.5
    assert resumo["avg_llm_time_ms"] == 50.0
    assert resumo["avg_total_time_ms"] == 80.0
    assert resumo["avg_max_score"] == 0.45
    assert resumo["avg_context_count"] == 4.0
    assert resumo["fallback_reasons"]["score_baixo"] == 1
    assert resumo["fallback_reasons"]["sem_fallback"] == 1
