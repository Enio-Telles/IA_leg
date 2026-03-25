"""
Fábrica central para a resolução de componentes do sistema IA_leg.

Esta fábrica substitui a dependência arquitetural em monkey patches
em tempo de importação (`sitecustomize.py`, `usercustomize.py`), tornando a
seleção da engine RAG e estratégias ETL explícitas, determinísticas e auditáveis.

A configuração é orientada pela variável de ambiente `IA_LEG_ENGINE_MODE`.
Opções disponíveis:
- 'standard': Utiliza a engine de consulta base.
- 'safe': Utiliza a engine com restrições e top_k controlados.
- 'safe_audited': Utiliza a engine segura acrescida de hooks para auditoria.
"""

import os
import logging
from typing import Callable

logger = logging.getLogger(__name__)


def get_answer_engine() -> Callable:
    """
    Retorna a função de consulta RAG apropriada baseada no modo configurado.
    """
    mode = os.environ.get("IA_LEG_ENGINE_MODE", "standard").strip().lower()

    if mode == "safe":
        logger.info("[IA_leg Factory] Carregando engine RAG: SAFE")
        from ia_leg.rag.answer_engine_safe import consultar_seguro

        safe_top_k = int(os.environ.get("IA_LEG_SAFE_TOP_K", "5"))
        safe_min_score = float(os.environ.get("IA_LEG_SAFE_MIN_SCORE", "0.20"))
        safe_require_anchors = os.environ.get("IA_LEG_SAFE_REQUIRE_ANCHORS", "1") != "0"

        def _consultar_safe(pergunta: str, top_k: int = 5, backend: str = "ollama") -> str:
            return consultar_seguro(
                pergunta,
                top_k=top_k or safe_top_k,
                backend=backend,
                min_score=safe_min_score,
                exigir_ancoras=safe_require_anchors,
            )
        return _consultar_safe

    elif mode == "safe_audited":
        logger.info("[IA_leg Factory] Carregando engine RAG: SAFE_AUDITED")
        from ia_leg.rag.answer_engine_safe_audited import consultar_seguro

        safe_top_k = int(os.environ.get("IA_LEG_SAFE_TOP_K", "5"))
        safe_min_score = float(os.environ.get("IA_LEG_SAFE_MIN_SCORE", "0.20"))
        safe_require_anchors = os.environ.get("IA_LEG_SAFE_REQUIRE_ANCHORS", "1") != "0"

        def _consultar_safe_audited(pergunta: str, top_k: int = 5, backend: str = "ollama") -> str:
            return consultar_seguro(
                pergunta,
                top_k=top_k or safe_top_k,
                backend=backend,
                min_score=safe_min_score,
                exigir_ancoras=safe_require_anchors,
            )
        return _consultar_safe_audited

    else:
        logger.info("[IA_leg Factory] Carregando engine RAG: STANDARD")
        from ia_leg.rag.answer_engine import consultar
        return consultar


def get_chunking_strategy() -> Callable:
    """
    Retorna a estratégia de chunking para documentos jurídicos.
    """
    mode = os.environ.get("IA_LEG_ENGINE_MODE", "standard").strip().lower()

    if mode in ("safe", "safe_audited"):
        logger.info("[IA_leg Factory] Carregando chunking jurídico hierárquico (SAFE mode).")
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

        return _quebrar_dispositivos_proxy

    else:
        logger.info("[IA_leg Factory] Carregando chunking jurídico padrão (STANDARD mode).")

        def quebrar_dispositivos_padrao(texto: str):
            """Estratégia legada simples baseada em 'Art.'"""
            partes = (texto or "").split("Art.")
            dispositivos = []

            for parte in partes[1:]:
                identificador = "Art. " + parte.split("\n")[0].strip()
                conteudo = "Art." + parte
                dispositivos.append((identificador, conteudo.strip()))

            return dispositivos

        return quebrar_dispositivos_padrao
