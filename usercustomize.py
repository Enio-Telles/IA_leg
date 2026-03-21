"""
Sobrescreve os patches de inicialização com a trilha segura auditada.

Python importa `usercustomize` após `sitecustomize`, então este arquivo
permite consolidar a engine auditada no fluxo principal sem alterar o
arquivo `sitecustomize.py` diretamente.
"""

from __future__ import annotations

import os
import sys

try:
    import ia_leg.rag.answer_engine as answer_engine
    from ia_leg.rag.answer_engine_safe_audited import consultar_seguro

    SAFE_TOP_K = int(os.environ.get("IA_LEG_SAFE_TOP_K", "5"))
    SAFE_MIN_SCORE = float(os.environ.get("IA_LEG_SAFE_MIN_SCORE", "0.20"))
    SAFE_REQUIRE_ANCHORS = os.environ.get("IA_LEG_SAFE_REQUIRE_ANCHORS", "1") != "0"
    FAIL_FAST = os.environ.get("IA_LEG_PATCH_FAIL_FAST", "0") == "1"

    def _consultar_proxy(pergunta: str, top_k: int = 5, backend: str = "ollama") -> str:
        return consultar_seguro(
            pergunta,
            top_k=top_k or SAFE_TOP_K,
            backend=backend,
            min_score=SAFE_MIN_SCORE,
            exigir_ancoras=SAFE_REQUIRE_ANCHORS,
        )

    answer_engine.consultar = _consultar_proxy
    answer_engine._IA_LEG_SAFE_AUDITED_PATCHED = True
except Exception as exc:
    print(f"[IA_leg patch error] usercustomize: {type(exc).__name__}: {exc}", file=sys.stderr)
    if os.environ.get("IA_LEG_PATCH_FAIL_FAST", "0") == "1":
        raise
