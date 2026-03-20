"""Trilha segura com auditoria detalhada por consulta."""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List

from ia_leg.core.config.settings import LLM_MODEL
from ia_leg.observability.audit_logger import registrar_query_audit
from ia_leg.rag.citation_guard import (
    montar_fontes_verificadas,
    possui_ancoras_verificaveis,
    resposta_fallback_contextual,
    score_maximo,
)
from ia_leg.rag.answer_engine_safe import (
    _chamar_ollama,
    _chamar_openai,
    _montar_prompt_seguro,
    _rerankar_se_disponivel,
)
from ia_leg.rag.answer_engine import definir_filtros_por_pergunta
from ia_leg.rag.retriever import recuperar_contexto

OLLAMA_MODELO = os.environ.get("OLLAMA_MODELO", LLM_MODEL)
OPENAI_MODELO = os.environ.get("OPENAI_MODELO", "gpt-4o-mini")


def consultar_seguro_detalhado(
    pergunta: str,
    top_k: int = 5,
    backend: str = "ollama",
    min_score: float = 0.20,
    exigir_ancoras: bool = True,
) -> Dict[str, Any]:
    inicio_total = time.time()
    filtros = definir_filtros_por_pergunta(pergunta)
    contextos, search_time_ms = recuperar_contexto(
        pergunta,
        top_k=top_k * 2,
        filtro_tipos=filtros,
    )

    if not contextos:
        total_time_ms = (time.time() - inicio_total) * 1000
        payload = {
            "pergunta": pergunta,
            "backend": backend,
            "model": OPENAI_MODELO if backend == "openai" else OLLAMA_MODELO,
            "filtros": filtros,
            "top_k": top_k,
            "min_score": min_score,
            "exigir_ancoras": exigir_ancoras,
            "context_count": 0,
            "max_score": 0.0,
            "fallback_reason": "sem_contexto",
            "source_anchor_ok": False,
            "source_identifiers": [],
            "source_normas": [],
            "response_preview": "Não localizei trechos suficientes na base vetorial para responder com segurança.",
            "prompt_chars": 0,
            "search_time_ms": search_time_ms,
            "rerank_time_ms": 0.0,
            "llm_time_ms": 0.0,
            "total_time_ms": total_time_ms,
        }
        registrar_query_audit(payload)
        payload["response"] = payload["response_preview"]
        return payload

    inicio_rerank = time.time()
    contextos = _rerankar_se_disponivel(pergunta, contextos, top_k=top_k)
    rerank_time_ms = (time.time() - inicio_rerank) * 1000
    max_score = score_maximo(contextos)

    if max_score < min_score:
        response = resposta_fallback_contextual(
            pergunta,
            contextos,
            motivo=f"score máximo abaixo do limiar configurado ({min_score:.2f})",
        )
        total_time_ms = (time.time() - inicio_total) * 1000
        payload = {
            "pergunta": pergunta,
            "backend": backend,
            "model": OPENAI_MODELO if backend == "openai" else OLLAMA_MODELO,
            "filtros": filtros,
            "top_k": top_k,
            "min_score": min_score,
            "exigir_ancoras": exigir_ancoras,
            "context_count": len(contextos),
            "max_score": max_score,
            "fallback_reason": "score_baixo",
            "source_anchor_ok": False,
            "source_identifiers": [c.get("identificador") for c in contextos],
            "source_normas": [c.get("norma") for c in contextos],
            "response_preview": response[:1000],
            "prompt_chars": 0,
            "search_time_ms": search_time_ms,
            "rerank_time_ms": rerank_time_ms,
            "llm_time_ms": 0.0,
            "total_time_ms": total_time_ms,
        }
        registrar_query_audit(payload)
        payload["response"] = response
        return payload

    prompt = _montar_prompt_seguro(pergunta, contextos)
    if backend == "openai":
        resposta, llm_time_ms = _chamar_openai(prompt)
        model = OPENAI_MODELO
    else:
        resposta, llm_time_ms = _chamar_ollama(prompt)
        model = OLLAMA_MODELO

    fallback_reason = None
    source_anchor_ok = False

    if not resposta:
        resposta = resposta_fallback_contextual(
            pergunta,
            contextos,
            motivo="backend indisponível ou sem resposta",
        )
        fallback_reason = "backend_sem_resposta"
    else:
        source_anchor_ok = possui_ancoras_verificaveis(resposta, contextos)
        if exigir_ancoras and not source_anchor_ok:
            resposta = resposta_fallback_contextual(
                pergunta,
                contextos,
                motivo="a resposta do LLM não trouxe âncoras verificáveis nas fontes recuperadas",
            )
            fallback_reason = "sem_ancoras_verificaveis"
        else:
            resposta = resposta.strip() + montar_fontes_verificadas(contextos)

    total_time_ms = (time.time() - inicio_total) * 1000
    payload = {
        "pergunta": pergunta,
        "backend": backend,
        "model": model,
        "filtros": filtros,
        "top_k": top_k,
        "min_score": min_score,
        "exigir_ancoras": exigir_ancoras,
        "context_count": len(contextos),
        "max_score": max_score,
        "fallback_reason": fallback_reason,
        "source_anchor_ok": source_anchor_ok,
        "source_identifiers": [c.get("identificador") for c in contextos],
        "source_normas": [c.get("norma") for c in contextos],
        "response_preview": resposta[:1000],
        "prompt_chars": len(prompt),
        "search_time_ms": search_time_ms,
        "rerank_time_ms": rerank_time_ms,
        "llm_time_ms": llm_time_ms,
        "total_time_ms": total_time_ms,
    }
    registrar_query_audit(payload)
    payload["response"] = resposta
    return payload


def consultar_seguro(*args, **kwargs) -> str:
    return consultar_seguro_detalhado(*args, **kwargs)["response"]
