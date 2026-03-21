"""
Patches automáticos do IA_leg aplicados na inicialização do Python.

Objetivo:
- consolidar o hardening do RAG no fluxo principal sem depender de entrypoints paralelos
- fazer `dashboard/app.py` usar a trilha segura por padrão
- fazer `etl/versionamento_pipeline.py` usar parser jurídico hierárquico por padrão
- garantir que `processar_tudo()` exista no pipeline principal

Desative definindo:
    IA_LEG_ENABLE_SAFE_PATCHES=0
Falhas podem ser forçadas em ambiente de teste/dev com:
    IA_LEG_PATCH_FAIL_FAST=1
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ENABLE_PATCHES = os.environ.get("IA_LEG_ENABLE_SAFE_PATCHES", "1") != "0"
FAIL_FAST = os.environ.get("IA_LEG_PATCH_FAIL_FAST", "0") == "1"


def _handle_patch_error(area: str, exc: Exception) -> None:
    msg = f"[IA_leg patch error] {area}: {type(exc).__name__}: {exc}"
    print(msg, file=sys.stderr)
    if FAIL_FAST:
        raise exc


if ENABLE_PATCHES:
    try:
        from ia_leg.rag.answer_engine_safe import consultar_seguro
        import ia_leg.rag.answer_engine as answer_engine

        SAFE_TOP_K = int(os.environ.get("IA_LEG_SAFE_TOP_K", "5"))
        SAFE_MIN_SCORE = float(os.environ.get("IA_LEG_SAFE_MIN_SCORE", "0.20"))
        SAFE_REQUIRE_ANCHORS = os.environ.get("IA_LEG_SAFE_REQUIRE_ANCHORS", "1") != "0"

        def _consultar_proxy(pergunta: str, top_k: int = 5, backend: str = "ollama") -> str:
            return consultar_seguro(
                pergunta,
                top_k=top_k or SAFE_TOP_K,
                backend=backend,
                min_score=SAFE_MIN_SCORE,
                exigir_ancoras=SAFE_REQUIRE_ANCHORS,
            )

        answer_engine.consultar = _consultar_proxy
        answer_engine._IA_LEG_SAFE_PATCHED = True
    except Exception as exc:
        _handle_patch_error("answer_engine", exc)

    try:
        import etl.versionamento_pipeline as versionamento_pipeline
        from ia_leg.core.config.settings import BASE_DIR
        from ia_leg.etl.legal_parser import (
            quebrar_dispositivos_hierarquicos,
            quebrar_texto_generico_em_chunks,
        )

        def _quebrar_dispositivos_proxy(texto: str):
            texto = (texto or "").strip()
            if not texto:
                return []

            if "Art." in texto or "ART." in texto:
                chunks = quebrar_dispositivos_hierarquicos(texto)
                if chunks:
                    return chunks

            return quebrar_texto_generico_em_chunks(texto)

        def _processar_tudo_proxy():
            text_dir = Path(BASE_DIR) / "documentos" / "texto"
            arquivos = sorted(text_dir.glob("*.json"))

            print(f"Iniciando processamento ETL consolidado de {len(arquivos)} arquivos JSON.")
            for arq in arquivos:
                try:
                    print("----------------------------------------")
                    print(f"Processando {arq.name}...")
                    versionamento_pipeline.processar_norma_json(str(arq))
                except Exception as exc:
                    import traceback

                    print(f"Falha ao processar {arq.name}: {exc}")
                    traceback.print_exc()

        versionamento_pipeline.quebrar_dispositivos = _quebrar_dispositivos_proxy
        versionamento_pipeline.processar_tudo = _processar_tudo_proxy
        versionamento_pipeline._IA_LEG_SAFE_PATCHED = True
    except Exception as exc:
        _handle_patch_error("versionamento_pipeline", exc)
