"""
Entry-point do dashboard com trilha segura de resposta.

Uso:
    streamlit run dashboard/app_safe.py

Estratégia:
- faz monkeypatch da função `consultar` do fluxo padrão
- reaproveita integralmente o dashboard atual
- ativa a engine segura sem duplicar a interface
"""

from __future__ import annotations

import os

import ia_leg.rag.answer_engine as answer_engine
from ia_leg.rag.answer_engine_safe import consultar_seguro


SAFE_TOP_K = int(os.environ.get("IA_LEG_SAFE_TOP_K", "5"))
SAFE_MIN_SCORE = float(os.environ.get("IA_LEG_SAFE_MIN_SCORE", "0.20"))
SAFE_REQUIRE_ANCHORS = os.environ.get("IA_LEG_SAFE_REQUIRE_ANCHORS", "1") != "0"


def consultar_proxy(pergunta: str, top_k: int = 5, backend: str = "ollama") -> str:
    return consultar_seguro(
        pergunta,
        top_k=top_k or SAFE_TOP_K,
        backend=backend,
        min_score=SAFE_MIN_SCORE,
        exigir_ancoras=SAFE_REQUIRE_ANCHORS,
    )


answer_engine.consultar = consultar_proxy

# Reaproveita a aplicação Streamlit já existente.
import dashboard.app  # noqa: E402,F401
