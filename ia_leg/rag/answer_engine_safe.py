"""
Pipeline de resposta com trilho de segurança.

Diferenças em relação ao answer_engine padrão:
- threshold mínimo de relevância
- instrução forte de citação literal
- fallback quando a resposta não ancora nas fontes
- anexa fontes verificadas ao final da resposta
"""

from __future__ import annotations

import os
import time
from typing import Dict, List, Optional, Tuple

from ia_leg.rag.reranker import rerankar

import requests

from ia_leg.core.config.settings import LLM_MODEL
from ia_leg.rag.citation_guard import (
    montar_fontes_verificadas,
    possui_ancoras_verificaveis,
    resposta_fallback_contextual,
    score_maximo,
)

from urllib.parse import urlparse


def validar_url_http(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ["http", "https"] and bool(parsed.netloc)
    except Exception:
        return False


OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODELO = os.environ.get("OLLAMA_MODELO", LLM_MODEL)

OPENAI_URL = os.environ.get("OPENAI_URL", "")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODELO = os.environ.get("OPENAI_MODELO", "gpt-4o-mini")

SYSTEM_PROMPT_SEGURO = """Você é um auditor fiscal especialista em legislação tributária de Rondônia.

Responda somente com base nos trechos fornecidos.
Regras obrigatórias:
1. Não invente normas, artigos, parágrafos, incisos ou exceções.
2. Cite literalmente pelo menos um identificador e uma norma do contexto.
3. Quando houver incerteza, diga que a base recuperada não é suficiente.
4. Não trate orientação inferida como regra obrigatória sem apoio textual.
5. Feche a resposta com linguagem técnica, objetiva e verificável.
"""


def _montar_prompt_seguro(pergunta: str, contextos: List[Dict]) -> str:
    if not contextos:
        return f"Pergunta do usuário: {pergunta}"

    blocos: List[str] = []
    for i, ctx in enumerate(contextos, start=1):
        bloco = (
            f"### Fonte {i}\n"
            f"Norma: {ctx.get('norma', 'N/D')}\n"
            f"Identificador: {ctx.get('identificador', 'N/D')}\n"
            f"Relevância: {float(ctx.get('score_rerank', ctx.get('score', 0.0))):.4f}\n"
            f"Texto:\n{ctx.get('texto', '')}"
        )
        blocos.append(bloco)

    contexto = "\n\n".join(blocos)
    return (
        "## Contexto normativo\n"
        f"{contexto}\n\n"
        "## Instrução de resposta\n"
        "Responda com base exclusiva nas fontes acima e cite norma + identificador exatamente como aparecem.\n\n"
        f"## Pergunta\n{pergunta}\n"
    )


def _chamar_ollama(
    prompt_usuario: str, modelo: Optional[str] = None
) -> Tuple[Optional[str], float]:
    modelo = modelo or OLLAMA_MODELO
    inicio = time.time()
    if not validar_url_http(OLLAMA_URL):
        print(f"Erro Ollama: URL configurada é inválida ({OLLAMA_URL})")
        return None, (time.time() - inicio) * 1000
    try:
        resposta = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": modelo,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT_SEGURO},
                    {"role": "user", "content": prompt_usuario},
                ],
                "stream": False,
                "options": {"temperature": 0.0, "num_predict": 1400},
            },
            timeout=300,
        )
        tempo_ms = (time.time() - inicio) * 1000
        if resposta.status_code == 200:
            return resposta.json().get("message", {}).get("content", ""), tempo_ms
        return None, tempo_ms
    except Exception:
        return None, (time.time() - inicio) * 1000


def _chamar_openai(
    prompt_usuario: str, modelo: Optional[str] = None
) -> Tuple[Optional[str], float]:
    if not OPENAI_URL or not OPENAI_KEY:
        raise ValueError(
            "Configure OPENAI_URL e OPENAI_API_KEY nas variaveis de ambiente."
        )

    modelo = modelo or OPENAI_MODELO
    inicio = time.time()
    if not validar_url_http(OPENAI_URL):
        print(f"Erro OpenAI: URL configurada é inválida ({OPENAI_URL})")
        return None, (time.time() - inicio) * 1000
    try:
        resposta = requests.post(
            f"{OPENAI_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": modelo,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT_SEGURO},
                    {"role": "user", "content": prompt_usuario},
                ],
                "temperature": 0.0,
                "max_tokens": 1400,
            },
            timeout=60,
        )
        tempo_ms = (time.time() - inicio) * 1000
        if resposta.status_code == 200:
            return resposta.json()["choices"][0]["message"]["content"], tempo_ms
        return None, tempo_ms
    except Exception:
        return None, (time.time() - inicio) * 1000


def consultar_seguro(
    pergunta: str,
    top_k: int = 5,
    backend: str = "ollama",
    min_score: float = 0.20,
    exigir_ancoras: bool = True,
) -> str:
    from ia_leg.rag.answer_engine import definir_filtros_por_pergunta
    from ia_leg.rag.retriever import recuperar_contexto

    filtros = definir_filtros_por_pergunta(pergunta)
    contextos, _tempo_busca_ms = recuperar_contexto(
        pergunta,
        top_k=top_k * 2,
        filtro_tipos=filtros,
    )

    if not contextos:
        return "Não localizei trechos suficientes na base vetorial para responder com segurança."
    try:
        contextos = rerankar(pergunta, contextos, top_k=top_k)
    except Exception as e:
        print(f"⚠️ Reranker indisponível ({e}), usando scores originais.")
        contextos = contextos[:top_k]

    if score_maximo(contextos) < min_score:
        return resposta_fallback_contextual(
            pergunta,
            contextos,
            motivo=f"score máximo abaixo do limiar configurado ({min_score:.2f})",
        )

    prompt = _montar_prompt_seguro(pergunta, contextos)
    if backend == "openai":
        resposta, _tempo_llm_ms = _chamar_openai(prompt)
    else:
        resposta, _tempo_llm_ms = _chamar_ollama(prompt)

    if not resposta:
        return resposta_fallback_contextual(
            pergunta,
            contextos,
            motivo="backend indisponível ou sem resposta",
        )

    if exigir_ancoras and not possui_ancoras_verificaveis(resposta, contextos):
        return resposta_fallback_contextual(
            pergunta,
            contextos,
            motivo="a resposta do LLM não trouxe âncoras verificáveis nas fontes recuperadas",
        )

    return resposta.strip() + montar_fontes_verificadas(contextos)
