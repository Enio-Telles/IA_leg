from ia_leg.observability.benchmark_runner import resumir_resultados


def test_resumo_resultados_calcula_taxas():
    resultados = [
        {
            "fallback": True,
            "keywords_ok": True,
            "anchor_terms_ok": False,
            "source_anchor_ok": True,
            "retrieval_time_ms": 10.0,
            "answer_time_ms": 100.0,
            "max_score": 0.8,
        },
        {
            "fallback": False,
            "keywords_ok": False,
            "anchor_terms_ok": True,
            "source_anchor_ok": True,
            "retrieval_time_ms": 20.0,
            "answer_time_ms": 200.0,
            "max_score": 0.6,
        },
    ]

    resumo = resumir_resultados(resultados)

    assert resumo["total_queries"] == 2
    assert resumo["fallback_rate"] == 0.5
    assert resumo["keywords_ok_rate"] == 0.5
    assert resumo["anchor_terms_ok_rate"] == 0.5
    assert resumo["source_anchor_ok_rate"] == 1.0
    assert resumo["avg_retrieval_time_ms"] == 15.0
    assert resumo["avg_answer_time_ms"] == 150.0
    assert resumo["avg_max_score"] == 0.7
