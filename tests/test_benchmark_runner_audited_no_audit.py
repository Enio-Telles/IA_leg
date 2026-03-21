from unittest.mock import patch

from ia_leg.observability.benchmark_runner_audited import avaliar_query


def test_benchmark_audited_does_not_register_operational_audit():
    item = {
        "id": "q1",
        "pergunta": "Qual a alíquota interna do ICMS em Rondônia?",
        "expected_keywords": ["ICMS"],
        "expected_anchor_terms": ["Art."],
    }

    with patch("ia_leg.observability.benchmark_runner_audited.consultar_seguro_detalhado") as mock_consulta:
        mock_consulta.return_value = {
            "response": "Resposta de teste com Art. 1º e ICMS.",
            "filtros": ["Decreto"],
            "context_count": 3,
            "max_score": 0.9,
            "search_time_ms": 10.0,
            "rerank_time_ms": 5.0,
            "llm_time_ms": 100.0,
            "total_time_ms": 120.0,
            "fallback_reason": None,
            "source_anchor_ok": True,
            "source_identifiers": ["Art. 1º"],
            "source_normas": ["Decreto X"],
            "response_preview": "Resposta de teste",
        }

        avaliar_query(item)

        assert mock_consulta.call_args.kwargs["registrar_auditoria"] is False
