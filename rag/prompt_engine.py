"""
Constrói prompts estruturados para respostas fundamentadas.
Integra com Ollama (local) ou OpenAI-compatible APIs.
"""

import requests
import json
import os
from typing import List, Dict, Optional

# ─────────────────────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────────────────────

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")

try:
    from config import LLM_MODEL
except ImportError:
    LLM_MODEL = "llama3"

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
        # Foca nos tipos que ditam o *como fazer*
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
        
    return None  # Sem filtros, busca em tudo

def montar_prompt(pergunta: str, contextos: List[Dict]) -> str:
    """
    Monta o prompt completo com a pergunta e os trechos legislativos relevantes.
    """
    blocos = []
    for i, ctx in enumerate(contextos, 1):
        bloco = (
            f"### Trecho {i} — {ctx['norma']} ({ctx['identificador']})\n"
            f"Relevância: {ctx['score']:.2%}\n"
            f"```\n{ctx['texto']}\n```"
        )
        blocos.append(bloco)
    
    contexto_formatado = "\n\n".join(blocos) if blocos else "(Nenhum trecho normativo/manual encontrado na base.)"
    
    prompt_usuario = f"""## Contexto Recuperado (Manuais, Pareceres e Leis):
{contexto_formatado}

## Pergunta do Usuário:
{pergunta}

## Sua Resposta Especializada:"""
    
    return prompt_usuario


# ─────────────────────────────────────────────────────────
# CHAMADAS AO LLM
# ─────────────────────────────────────────────────────────

def chamar_ollama(prompt_usuario: str, modelo: str = None) -> Optional[str]:
    """Envia o prompt ao Ollama local e retorna a resposta."""
    modelo = modelo or OLLAMA_MODELO
    
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
                "options": {
                    "temperature": 0.1,  # Baixa para respostas mais factuais
                    "num_predict": 2048
                }
            },
            timeout=300
        )
        
        if resp.status_code == 200:
            return resp.json().get("message", {}).get("content", "")
        else:
            print(f"Erro Ollama ({resp.status_code}): {resp.text[:200]}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("Ollama não está rodando. Inicie com: ollama serve")
        return None
    except Exception as e:
        print(f"Erro ao chamar Ollama: {e}")
        return None


def chamar_openai(prompt_usuario: str, modelo: str = None) -> Optional[str]:
    """Envia o prompt a uma API OpenAI-compatible e retorna a resposta."""
    if not OPENAI_URL or not OPENAI_KEY:
        print("Configure OPENAI_URL e OPENAI_API_KEY nas variáveis de ambiente.")
        return None
    
    modelo = modelo or OPENAI_MODELO
    
    try:
        resp = requests.post(
            f"{OPENAI_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_KEY}",
                "Content-Type": "application/json"
            },
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
        
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        else:
            print(f"Erro OpenAI ({resp.status_code}): {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"Erro ao chamar OpenAI: {e}")
        return None


def consultar(pergunta: str, top_k: int = 5, backend: str = "ollama") -> str:
    """
    Pipeline completo: Recupera contexto → Monta prompt → Chama LLM.
    """
    from rag.retriever import recuperar_contexto
    
    print(f"🔍 Buscando legislação relevante para: \"{pergunta}\"")
    
    # Roteamento automático
    filtros = definir_filtros_por_pergunta(pergunta)
    if filtros:
        print(f"🚦 Roteamento de Query: Aplicando filtros de metadados: {filtros}")
        
    contextos = recuperar_contexto(pergunta, top_k=top_k * 2, filtro_tipos=filtros)
    
    if not contextos:
        return "Não foram encontrados dispositivos ou trechos de manuais na base vetorial que correspondam à sua busca."
    
    # Reranking com cross-encoder para melhorar precisão
    try:
        from rag.reranker import rerankar
        print(f"🔄 Reranking {len(contextos)} candidatos...")
        contextos = rerankar(pergunta, contextos, top_k=top_k)
    except Exception as e:
        print(f"⚠️ Reranker indisponível ({e}), usando scores originais.")
        contextos = contextos[:top_k]
    
    print(f"📋 {len(contextos)} trechos selecionados (melhor score: {contextos[0].get('score_rerank', contextos[0]['score']):.4f})")
    
    prompt = montar_prompt(pergunta, contextos)
    
    print(f"🤖 Consultando LLM ({backend})...")
    
    if backend == "ollama":
        resposta = chamar_ollama(prompt)
    elif backend == "openai":
        resposta = chamar_openai(prompt)
    else:
        resposta = None
        print(f"Backend '{backend}' não suportado. Use 'ollama' ou 'openai'.")
    
    if resposta is None:
        # Fallback: retorna o contexto raw se o LLM não estiver disponível
        print("⚠️ LLM indisponível. Retornando contexto interpretado bruto.\n")
        linhas = [f"**Contexto recuperado para:** {pergunta}\n"]
        for ctx in contextos:
            linhas.append(f"---\n**{ctx['norma']}** — {ctx['identificador']} (score: {ctx['score']:.4f})")
            linhas.append(f"{ctx['texto'][:500]}...\n")
        return "\n".join(linhas)
    
    return resposta


# ─────────────────────────────────────────────────────────
# CLI INTERATIVO
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("REVISOR FISCAL INTELIGENTE — SEFIN/RO")
    print("Sistema de Consulta à Legislação Tributária")
    print("=" * 60)
    print("Digite sua pergunta ou 'sair' para encerrar.\n")
    
    backend = "ollama"
    
    while True:
        try:
            pergunta = input("📝 Pergunta: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando.")
            break
            
        if not pergunta or pergunta.lower() in ("sair", "exit", "quit"):
            print("Encerrando.")
            break
        
        if pergunta.startswith("/backend "):
            backend = pergunta.split(" ", 1)[1].strip()
            print(f"Backend alterado para: {backend}")
            continue
            
        resposta = consultar(pergunta, top_k=5, backend=backend)
        print(f"\n{'─'*60}")
        print(resposta)
        print(f"{'─'*60}\n")

