"""
Constrói prompts estruturados para respostas fundamentadas.
Mede métricas de pipeline e integra com Ollama ou APIs OpenAI-compatible.
"""

import requests
import json
import os
import time
import sqlite3
from typing import List, Dict, Optional, Tuple

from ia_leg.core.config.settings import LLM_MODEL, DB_PATH

# ─────────────────────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────────────────────

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODELO = os.environ.get("OLLAMA_MODELO", LLM_MODEL)

OPENAI_URL = os.environ.get("OPENAI_URL", "")  # Ex: https://api.openai.com/v1
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODELO = os.environ.get("OPENAI_MODELO", "gpt-4o-mini")

SYSTEM_PROMPT = """Você é um Auditor Fiscal Especialista e Consultor Tributário Sênior do Estado de Rondônia (RO).

Sua função é responder a dúvidas fiscais, tributárias e de escrituração com base EXCLUSIVAMENTE nos documentos de contexto fornecidos.

## Regras de Formatação Obrigatórias:
1. **Didática:** Explique o conceito de forma clara antes de ir para as regras técnicas.
2. **Estrutura:** Use títulos (##), bullet points e negritos para facilitar a leitura.
3. **Fundamentação:** SEMPRE cite a origem da informação exata do contexto (ex: "Conforme o Guia_Pratico_EFD 3.1.9...", "Segundo o Parecer 443/2020...").
4. **Passo a Passo:** Se a pergunta envolver obrigações acessórias, escrituração (EFD, MOC), descreva os blocos e registros em sequência lógica (ex: 1. Registro E111, 2. Registro E110).
5. **Tabelas:** Se houver códigos específicos (como códigos de ajuste RO), apresente-os em formato de tabela para facilitar a visualização do usuário.
6. **Ausência de Dados:** Se a resposta não estiver no contexto fornecido, diga "Não possuo informações nos documentos consultados para responder a esta pergunta", JAMAIS invente regras, leis ou códigos.
"""

# ─────────────────────────────────────────────────────────
# ROTEAMENTO E MONTAGEM DO PROMPT
# ─────────────────────────────────────────────────────────

def definir_filtros_por_pergunta(pergunta: str) -> Optional[List[str]]:
    """
    Roteamento de Perguntas (Query Routing).
    Analisa a pergunta e decide se a busca deve ser restrita a Manuais e Pareceres ou Leis/Jurisprudências.
    """
    pergunta_min = pergunta.lower()
    
    # Palavras-chave de Obrigação Acessória/Prática
    keywords_escrituracao = ["escriturar", "efd", "sped", "registro", "bloco", "fecoep", "ajuste", "guia", "manual"]
    if any(kw in pergunta_min for kw in keywords_escrituracao):
        return ["Guia_Pratico_EFD", "Manual_MOC", "Parecer", "Despacho"]
    
    # Palavras-chave de súmulas/enunciados
    keywords_sumula = ["súmula", "sumula", "enunciado"]
    if any(kw in pergunta_min for kw in keywords_sumula):
        return ["Sumula_TATE", "Jurisprudencia_TATE", "Jurisprudencia_TATE_Camara_Plena"]
    
    # Palavras-chave de jurisprudência
    keywords_juris = ["stf", "tate", "entendimento", "decisão", "acórdão", "câmara plena", "camara plena"]
    if any(kw in pergunta_min for kw in keywords_juris):
        return ["Jurisprudencia_STF", "Jurisprudencia_TATE", "Jurisprudencia_TATE_Camara_Plena", "Sumula_TATE"]
    
    # Palavras-chave de ressarcimento/restituição
    keywords_ressarc = ["ressarcimento", "restituição", "restituicao"]
    if any(kw in pergunta_min for kw in keywords_ressarc):
        return ["Orientacao", "Orientacao_Fisconforme", "Parecer", "Despacho"]
    
    # Reforma tributária
    keywords_reforma = ["reforma tributária", "reforma tributaria", "ibs", "cbs", "lc 214", "lc 227", "emenda 132"]
    if any(kw in pergunta_min for kw in keywords_reforma):
        return ["Reforma_Tributaria", "Legislacao_Federal"]
    
    # Comércio exterior / ALCGM
    keywords_comex = ["importação", "importacao", "exportação", "exportacao", "glme", "alcgm", "guajará", "guajara", "pcce"]
    if any(kw in pergunta_min for kw in keywords_comex):
        return ["Comercio_Exterior", "Decreto", "Instrução Normativa"]
    
    # RICMS
    keywords_ricms = ["ricms", "regulamento icms", "anexo i", "anexo ii", "anexo iii", "anexo iv", "anexo v", "anexo vi"]
    if any(kw in pergunta_min for kw in keywords_ricms):
        return ["RICMS/RO", "Decreto"]
    
    # Fisconforme
    keywords_fisconf = ["fisconforme", "conformidade", "contribuinte legal"]
    if any(kw in pergunta_min for kw in keywords_fisconf):
        return ["Orientacao_Fisconforme", "Orientacao", "Despacho"]
        
    return None

def montar_prompt(pergunta: str, contextos: List[Dict]) -> str:
    """Monta o prompt completo com a pergunta e os trechos legislativos relevantes."""
    blocos = []
    for i, ctx in enumerate(contextos, 1):
        bloco = (
            f"### Trecho {i} — {ctx['norma']} ({ctx['identificador']})\n"
            f"Relevância: {ctx['score']:.2%}\n"
            f"```\n{ctx['texto']}\n```"
        )
        blocos.append(bloco)
    
    contexto_formatado = "\n\n".join(blocos) if blocos else "(Nenhum trecho normativo/manual encontrado na base.)"
    
    return f"""## Contexto Recuperado (Manuais, Pareceres e Leis):
{contexto_formatado}

## Pergunta do Usuário:
{pergunta}

## Sua Resposta Especializada:"""


# ─────────────────────────────────────────────────────────
# CHAMADAS AO LLM
# ─────────────────────────────────────────────────────────

def chamar_ollama(prompt_usuario: str, modelo: str = None) -> Tuple[Optional[str], float]:
    modelo = modelo or OLLAMA_MODELO
    inicio = time.time()
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": modelo,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_usuario}
                ],
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 2048}
            },
            timeout=300
        )
        tempo = (time.time() - inicio) * 1000
        if resp.status_code == 200:
            return resp.json().get("message", {}).get("content", ""), tempo
        print(f"Erro Ollama ({resp.status_code}): {resp.text[:200]}")
        return None, tempo
    except Exception as e:
        print(f"Erro ao chamar Ollama: {e}")
        return None, (time.time() - inicio) * 1000


def chamar_openai(prompt_usuario: str, modelo: str = None) -> Tuple[Optional[str], float]:
    if not OPENAI_URL or not OPENAI_KEY:
        raise ValueError("Configure OPENAI_URL e OPENAI_API_KEY nas variaveis de ambiente.")
    
    modelo = modelo or OPENAI_MODELO
    inicio = time.time()
    try:
        resp = requests.post(
            f"{OPENAI_URL}/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"},
            json={
                "model": modelo,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_usuario}
                ],
                "temperature": 0.1,
                "max_tokens": 2048
            },
            timeout=60
        )
        tempo = (time.time() - inicio) * 1000
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"], tempo
        print(f"Erro OpenAI ({resp.status_code}): {resp.text[:200]}")
        return None, tempo
    except Exception as e:
        print(f"Erro ao chamar OpenAI: {e}")
        return None, (time.time() - inicio) * 1000

def registrar_metricas(pergunta: str, filtros: List[str], metadados: Dict):
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO query_logs
               (pergunta, filtros, embedding_time_ms, search_time_ms, rerank_time_ms, llm_time_ms, total_time_ms, chunks_used, backend, model, success)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                pergunta,
                str(filtros) if filtros else None,
                metadados.get("embedding_time_ms"),
                metadados.get("search_time_ms"),
                metadados.get("rerank_time_ms"),
                metadados.get("llm_time_ms"),
                metadados.get("total_time_ms"),
                metadados.get("chunks_used"),
                metadados.get("backend"),
                metadados.get("model"),
                metadados.get("success")
            )
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Aviso: Erro ao registrar métricas - {e}")

def consultar(pergunta: str, top_k: int = 5, backend: str = "ollama") -> str:
    from ia_leg.rag.retriever import recuperar_contexto

    inicio_total = time.time()
    metricas = {"backend": backend, "model": OLLAMA_MODELO if backend == "ollama" else OPENAI_MODELO, "success": False}
    
    print(f"🔍 Buscando legislação relevante para: \"{pergunta}\"")
    
    filtros = definir_filtros_por_pergunta(pergunta)
    if filtros:
        print(f"🚦 Roteamento de Query: Aplicando filtros: {filtros}")
        
    contextos, metricas["search_time_ms"] = recuperar_contexto(pergunta, top_k=top_k * 2, filtro_tipos=filtros)
    
    if not contextos:
        metricas["total_time_ms"] = (time.time() - inicio_total) * 1000
        registrar_metricas(pergunta, filtros, metricas)
        return "Não foram encontrados dispositivos ou trechos de manuais na base vetorial que correspondam à sua busca."
    
    try:
        # TODO: Refatorar reranker futuramente, por enquanto isolamos o timing
        inicio_rerank = time.time()
        from ia_leg.rag.reranker import rerankar # Temporary, to be fixed in next phase if not refactored yet
        contextos = rerankar(pergunta, contextos, top_k=top_k)
        metricas["rerank_time_ms"] = (time.time() - inicio_rerank) * 1000
    except Exception as e:
        print(f"⚠️ Reranker indisponível ({e}), usando scores originais.")
        contextos = contextos[:top_k]
        metricas["rerank_time_ms"] = 0.0
    
    metricas["chunks_used"] = len(contextos)
    prompt = montar_prompt(pergunta, contextos)
    
    print(f"🤖 Consultando LLM ({backend})...")
    
    if backend == "ollama":
        resposta, metricas["llm_time_ms"] = chamar_ollama(prompt)
    elif backend == "openai":
        resposta, metricas["llm_time_ms"] = chamar_openai(prompt)
    else:
        resposta, metricas["llm_time_ms"] = None, 0.0

    metricas["total_time_ms"] = (time.time() - inicio_total) * 1000
    
    if resposta is None:
        metricas["success"] = False
        registrar_metricas(pergunta, filtros, metricas)
        return "Erro ao consultar LLM. Use fallbacks de contexto."
    
    metricas["success"] = True
    registrar_metricas(pergunta, filtros, metricas)
    return resposta
