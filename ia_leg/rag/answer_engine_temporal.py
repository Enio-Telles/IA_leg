"""
Camada de resposta com suporte a recorte temporal de vigência.

Este módulo preserva a lógica principal do answer_engine atual,
mas direciona a recuperação de contexto para o retriever temporal
quando uma data de referência é informada.
"""

from __future__ import annotations

import os
import time
from typing import Dict, List, Optional, Tuple

from ia_leg.rag.answer_engine import (
    SYSTEM_PROMPT,
    OPENAI_KEY,
    OPENAI_MODELO,
    OPENAI_URL,
    OLLAMA_MODELO,
    OLLAMA_URL,
    definir_filtros_por_pergunta,
    registrar_metricas,
)
from ia_leg.rag.answer_engine import chamar_ollama as _chamar_ollama_base
from ia_leg.rag.answer_engine import chamar_openai as _chamar_openai_base
from ia_leg.rag.retriever import recuperar_contexto
from ia_leg.rag.temporal_retriever import recuperar_contexto_temporal


def montar_prompt_temporal(
    pergunta: str,
    contextos: List[Dict],
    data_referencia: Optional[str] = None,
) -> str:
    blocos = []
    for i, ctx in enumerate(contextos, 1):
        vigencia_inicio = ctx.get("vigencia_inicio") or "N/D"
        vigencia_fim = ctx.get("vigencia_fim") or "Atual"
        bloco = (
            f"### Trecho {i} — {ctx['norma']} ({ctx['identificador']})\n"
            f"Relevância: {ctx['score']:.2%}\n"
            f"Vigência: {vigencia_inicio} até {vigencia_fim}\n"
            f"```\n{ctx['texto']}\n```"
        )
        blocos.append(bloco)

    contexto_formatado = "\n\n".join(blocos) if blocos else "(Nenhum trecho normativo/manual encontrado na base.)"
    recorte = data_referencia or "vigência atual"

    return f"""## Contexto Recuperado (Manuais, Pareceres e Leis):
{contexto_formatado}

## Recorte Temporal da Consulta:
{recorte}

## Pergunta do Usuário:
{pergunta}

## Sua Resposta Especializada:"""


def chamar_ollama(prompt_usuario: str, modelo: str = None) -> Tuple[Optional[str], float]:
    return _chamar_ollama_base(prompt_usuario, modelo=modelo)


def chamar_openai(prompt_usuario: str, modelo: str = None) -> Tuple[Optional[str], float]:
    return _chamar_openai_base(prompt_usuario, modelo=modelo)


def consultar_temporal(
    pergunta: str,
    top_k: int = 5,
    backend: str = "ollama",
    data_referencia: Optional[str] = None,
) -> str:
    inicio_total = time.time()
    filtros = definir_filtros_por_pergunta(pergunta)
    metricas = {
        "backend": backend,
        "model": OLLAMA_MODELO if backend == "ollama" else OPENAI_MODELO,
        "success": False,
    }

    if filtros:
        print(f"🚦 Roteamento de Query: Aplicando filtros: {filtros}")

    if data_referencia:
        print(f"🕒 Aplicando recorte temporal de vigência: {data_referencia}")
        contextos, metricas["search_time_ms"] = recuperar_contexto_temporal(
            pergunta,
            top_k=top_k * 2,
            filtro_tipos=filtros,
            data_referencia=data_referencia,
        )
    else:
        contextos, metricas["search_time_ms"] = recuperar_contexto(
            pergunta,
            top_k=top_k * 2,
            filtro_tipos=filtros,
        )

    if not contextos:
        metricas["total_time_ms"] = (time.time() - inicio_total) * 1000
        registrar_metricas(pergunta, filtros, metricas)
        if data_referencia:
            return f"Não foram encontrados dispositivos ou trechos normativos para a data de referência {data_referencia}."
        return "Não foram encontrados dispositivos ou trechos normativos na base vetorial que correspondam à sua busca."

    try:
        from ia_leg.rag.reranker import rerankar
        inicio_rerank = time.time()
        contextos = rerankar(pergunta, contextos, top_k=top_k)
        metricas["rerank_time_ms"] = (time.time() - inicio_rerank) * 1000
    except Exception as e:
        print(f"⚠️ Reranker indisponível ({e}), usando scores originais.")
        contextos = contextos[:top_k]
        metricas["rerank_time_ms"] = 0.0

    metricas["chunks_used"] = len(contextos)
    prompt = montar_prompt_temporal(pergunta, contextos, data_referencia=data_referencia)

    if backend == "ollama":
        resposta, metricas["llm_time_ms"] = chamar_ollama(prompt)
    elif backend == "openai":
        resposta, metricas["llm_time_ms"] = chamar_openai(prompt)
    else:
        resposta, metricas["llm_time_ms"] = None, 0.0

    metricas["total_time_ms"] = (time.time() - inicio_total) * 1000

    if resposta is None:
        registrar_metricas(pergunta, filtros, metricas)
        return "Erro ao consultar o backend LLM configurado."

    metricas["success"] = True
    registrar_metricas(pergunta, filtros, metricas)
    return resposta
