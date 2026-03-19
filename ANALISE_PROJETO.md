# 📋 Análise do Projeto IA_leg — Revisor Fiscal Inteligente

**Data:** 21/02/2026  
**Autor:** Análise técnica automatizada  
**Versão:** 1.0

---

## 1. Visão Geral do Projeto

O **IA_leg** é um sistema de Retrieval-Augmented Generation (RAG) desenvolvido para a Secretaria de Estado de Finanças de Rondônia (SEFIN-RO). Seu objetivo é permitir consultas em linguagem natural sobre a legislação tributária estadual, retornando respostas fundamentadas com citações de dispositivos legais específicos.

### Arquitetura Atual

```
┌────────────────────────────────────────────────────────────┐
│                    Dashboard Streamlit                      │
│              (Chat IA + Painel + Timeline)                  │
├────────────────────────────────────────────────────────────┤
│                     Prompt Engine                           │
│              (Ollama / OpenAI backend)                      │
├────────────────────────────────────────────────────────────┤
│    Retriever (busca vetorial)  │  Embeddings (BGE-M3)      │
├────────────────────────────────────────────────────────────┤
│              ETL Pipeline (versionamento)                   │
│         (JSON → texto → dispositivos → versões)            │
├────────────────────────────────────────────────────────────┤
│         Crawler (API SEFIN legislação)                      │
├────────────────────────────────────────────────────────────┤
│              SQLite (metadata.db)                           │
│    normas │ versoes_norma │ dispositivos │ embeddings       │
└────────────────────────────────────────────────────────────┘
```

### Módulos e Responsabilidades

| Módulo | Arquivo Principal | O que faz |
|--------|-------------------|-----------|
| **Crawler** | `crawler/legislacao.py` | Conecta à API SEFIN e baixa JSONs com metadados e HTML de leis |
| **ETL** | `etl/versionamento_pipeline.py` | Extrai texto de HTML, segmenta em artigos, versiona normas |
| **RAG - Embeddings** | `-m ia_leg.rag.embedding_service` | Gera vetores densos com BGE-M3 e armazena no SQLite |
| **RAG - Retriever** | `rag/retriever.py` | Busca similaridade vetorial (brute-force com numpy) |
| **RAG - Prompt Engine** | `rag/prompt_engine.py` | Monta prompts estruturados e chama LLM |
| **Dashboard** | `dashboard/app.py` | Interface Streamlit com chat, estatísticas e timeline |
| **Config** | `config.py` | Centraliza caminhos e parâmetros |

### Base de Dados (estado atual)

| Métrica | Valor |
|---------|-------|
| Normas | **1.522** |
| Dispositivos (artigos) | **13.275** |
| Versões de norma | **1.624** |
| Embeddings gerados | **~1.000/13.275** (em progresso) |
| Tamanho do DB | ~150 MB |

---

## 2. Diagnóstico de Gargalos

### 🔴 Crítico: Velocidade de Geração de Embeddings

**Problema:** O modelo BGE-M3 (568M parâmetros) rodando em CPU processa apenas ~0.3 textos/segundo.

- ETA para indexar 13.275 dispositivos: **~12 horas**
- Cada novo lote de legislação requer reprocessamento demorado
- Impossibilita re-indexação rápida após atualização de dados

**Causa raiz:** O BGE-M3 é um modelo denso pesado, projetado para uso com GPU. Em CPU, cada forward pass com textos longos (artigos legislativos tipicamente têm 500-2000 tokens) consome segundos.

### 🟡 Moderado: Busca Vetorial Brute-Force

**Problema:** O `retriever.py` carrega **todos** os embeddings do SQLite na memória e calcula similaridade de coseno manualmente com numpy.

```python
# retriever.py — busca brute-force
cursor.execute('SELECT ... FROM embeddings e JOIN dispositivos d ...')
resultados = cursor.fetchall()  # Carrega TUDO na RAM

for row in resultados:
    vetor_doc = np.frombuffer(vetor_bytes, dtype=np.float32)
    score = np.dot(vetor_query, vetor_doc)  # O(n) para cada query
```

- **Para 13k vetores × 1024 dims:** ~50 MB na RAM + O(13k) por query = OK por agora
- **Se escalar para 100k+:** Latência sensível + consumo de RAM ~400 MB

### 🟡 Moderado: Modelo de Embedding Excessivo

**Problema:** O BGE-M3 gera vetores de **1024 dimensões**. Para uma base de ~13k documentos, isso é:
- Total em disco: ~52 MB de vetores puros
- Overhead de query: multiplicação de vetor 1024-d contra 13k itens

Para o caso de uso jurídico em português com ~15k documentos, um modelo menor seria suficiente.

### 🟢 Menor: Cache e Serialização

- O modelo BGE-M3 é recarregado a cada execução do prompt engine (~30s de startup)
- Não há cache de queries frequentes
- O Dashboard faz novas conexões ao SQLite a cada refresh

---

## 3. Propostas de Melhoria

### 3.1 Modelos de Embedding Alternativos (Mais Rápidos)

| Modelo | Dimensão | Tamanho | Velocidade CPU | Qualidade PT-BR |
|--------|----------|---------|----------------|-----------------|
| **BAAI/bge-m3** (atual) | 1024 | 2.2 GB | ~0.3 txt/s | ⭐⭐⭐⭐⭐ |
| **intfloat/multilingual-e5-small** | 384 | 470 MB | ~5 txt/s | ⭐⭐⭐⭐ |
| **sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2** | 384 | 470 MB | ~8 txt/s | ⭐⭐⭐⭐ |
| **sentence-transformers/all-MiniLM-L6-v2** | 384 | 90 MB | ~20 txt/s | ⭐⭐⭐ |
| **BAAI/bge-m3** (ONNX quantizado) | 1024 | 600 MB | ~2 txt/s | ⭐⭐⭐⭐⭐ |

> **Recomendação:** Usar `intfloat/multilingual-e5-small` como modelo padrão rápido. Mantém excelente qualidade em português e é **15x mais rápido** que o BGE-M3 em CPU. A indexação dos 13k dispositivos passaria de ~12h para ~45 minutos.

#### Como implementar a troca:

```python
# config.py — adicionar configuração flexível
EMBEDDING_MODELS = {
    "rapido": {
        "nome": "intfloat/multilingual-e5-small",
        "dimensao": 384,
        "prefixo_query": "query: ",   # E5 exige prefixo
        "prefixo_doc": "passage: ",
    },
    "preciso": {
        "nome": "BAAI/bge-m3",
        "dimensao": 1024,
        "prefixo_query": "",
        "prefixo_doc": "",
    }
}
EMBEDDING_ATIVO = "rapido"  # Trocar para "preciso" quando tiver GPU
```

### 3.2 Substituir Busca Brute-Force por Índice Vetorial

**Opção A — FAISS (Facebook AI Similarity Search)**

```python
# rag/index.py — criar índice FAISS
import faiss
import numpy as np

def criar_indice_faiss(vetores: np.ndarray) -> faiss.IndexFlatIP:
    dim = vetores.shape[1]
    index = faiss.IndexFlatIP(dim)  # Inner Product = cosine sim (vetores normalizados)
    index.add(vetores)
    return index

# Para bases maiores (>50k), usar IVF para busca aproximada:
# nlist = int(np.sqrt(len(vetores)))
# quantizer = faiss.IndexFlatIP(dim)
# index = faiss.IndexIVFFlat(quantizer, dim, nlist)
```

- Pros: Extremamente rápido (milhões de vetores em milissegundos), instalação simples
- Cons: Precisa reconstruir o índice ao adicionar novos vetores

**Opção B — ChromaDB (banco vetorial nativo)**

```python
import chromadb
client = chromadb.PersistentClient(path="database/chroma")
collection = client.get_or_create_collection("legislacao")

# Inserir
collection.add(
    ids=[str(id) for id in ids],
    embeddings=vetores.tolist(),
    metadatas=[{"norma": n, "artigo": a} for n, a in zip(normas, artigos)]
)

# Buscar
results = collection.query(query_embeddings=[vetor_query], n_results=5)
```

- Pros: Persistente, API simples, suporte a filtros de metadados
- Cons: Dependência adicional, pode ser overkill para 13k docs

> **Recomendação:** Para a escala atual (~13k docs), manter o SQLite com numpy e adicionar FAISS como camada de aceleração quando a base crescer acima de 50k.

### 3.3 LLMs Quantizados e Menores

#### Modelos Recomendados para Ollama (uso local)

| Modelo | RAM | Velocidade | Qualidade PT-BR | Caso de Uso |
|--------|-----|------------|-----------------|-------------|
| **llama3:8b-instruct-q4_K_M** | 5 GB | ~15 tok/s | ⭐⭐⭐⭐ | Melhor equilíbrio geral |
| **llama3:8b-instruct-q5_K_M** | 6 GB | ~12 tok/s | ⭐⭐⭐⭐⭐ | Maior precisão |
| **mistral:7b-instruct-q4_K_M** | 4.5 GB | ~18 tok/s | ⭐⭐⭐⭐ | Rápido, bom em instruções |
| **gemma2:9b-instruct-q4_K_M** | 6 GB | ~12 tok/s | ⭐⭐⭐⭐ | Bom follow de instruções |
| **phi3:mini-128k-instruct-q4** | 2.5 GB | ~25 tok/s | ⭐⭐⭐ | Ultra-leve, contexto enorme |
| **qwen2.5:7b-instruct-q4_K_M** | 5 GB | ~15 tok/s | ⭐⭐⭐⭐⭐ | Excelente multilíngue |
| **deepseek-r1:8b** | 5 GB | ~10 tok/s | ⭐⭐⭐⭐ | Raciocínio jurídico forte |

> **Recomendação primária:** `qwen2.5:7b-instruct-q4_K_M` — excelente em português, bom em seguir instruções estruturadas, e rápido em CPU.

> **Para máquinas com ≤8 GB RAM:** `phi3:mini-128k-instruct-q4` — aceita contextos enormes (ideal para artigos legislativos longos) com apenas 2.5 GB de RAM.

#### Instalação e teste rápido:

```bash
# Instalar o modelo recomendado
ollama pull qwen2.5:7b-instruct-q4_K_M

# Configurar no prompt_engine
# Alterar a variável de ambiente ou editar config.py:
set OLLAMA_MODELO=qwen2.5:7b-instruct-q4_K_M

# Ou para o phi3 ultra-leve:
ollama pull phi3:mini-128k-instruct
set OLLAMA_MODELO=phi3:mini-128k-instruct
```

### 3.4 Otimizações de Performance

#### A) Cache de Queries

```python
# rag/retriever.py — adicionar cache LRU
from functools import lru_cache
import hashlib

@lru_cache(maxsize=128)
def _buscar_cached(query_hash: str, top_k: int):
    # ... busca vetorial
    pass

def recuperar_contexto(pergunta, top_k=5):
    h = hashlib.md5(pergunta.encode()).hexdigest()
    return _buscar_cached(h, top_k)
```

#### B) Pré-carregar Modelo no Dashboard

```python
# dashboard/app.py — carregar modelo uma vez
@st.cache_resource
def carregar_modelo_rag():
    from ia_leg.rag.embedding_service import carregar_modelo
    return carregar_modelo()
```

Elimina o delay de ~30s na primeira query do chat.

#### C) Reranking (Segunda Passada de Relevância)

Após a busca vetorial, aplicar um reranker cross-encoder para refinar os top resultados:

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerankar(pergunta, candidatos, top_k=3):
    pares = [(pergunta, c["texto"]) for c in candidatos]
    scores = reranker.predict(pares)
    for i, c in enumerate(candidatos):
        c["score_rerank"] = float(scores[i])
    candidatos.sort(key=lambda x: x["score_rerank"], reverse=True)
    return candidatos[:top_k]
```

Melhora significativamente a precisão sem trocar o modelo de embedding.

### 3.5 Melhorias Funcionais

#### A) Chunking Inteligente por Dispositivo

O sistema atual segmenta texto apenas por `"Art."`. Proposta de melhoria:

```python
import re

PATTERNS_DISPOSITIVOS = [
    r'(Art\.\s*\d+)',
    r'(§\s*\d+[°º]?)',
    r'(Parágrafo único)',
    r'(Inciso\s+[IVXLCDM]+)',
    r'(Alínea\s+[a-z]\))',
]

def segmentar_avancado(texto: str) -> list:
    """Segmenta preservando hierarquia: Art > § > Inciso > Alínea"""
    # ... implementação com regex combinada
```

#### B) Filtros Temporais na Busca

Permitir ao usuário buscar legislação vigente em uma data específica:

```python
def recuperar_contexto(pergunta, top_k=5, data_referencia=None):
    filtro = "v.vigencia_fim IS NULL"
    if data_referencia:
        filtro = f"v.vigencia_inicio <= '{data_referencia}' AND (v.vigencia_fim IS NULL OR v.vigencia_fim > '{data_referencia}')"
```

#### C) Exportar Respostas em PDF

Gerar pareceres formais a partir das respostas do LLM usando `reportlab` ou `weasyprint`.

---

## 4. Roadmap Sugerido (Próximas Etapas)

### Curto Prazo (1-2 semanas)
- [ ] Trocar modelo de embedding para `multilingual-e5-small` (indexação 15x mais rápida)
- [ ] Instalar e configurar modelo Ollama otimizado (`qwen2.5:7b-instruct-q4`)
- [ ] Pré-carregar modelo no Dashboard (`@st.cache_resource`)
- [ ] Adicionar cache de queries frequentes

### Médio Prazo (1-2 meses)
- [ ] Implementar reranking com cross-encoder
- [ ] Migrar busca vetorial para FAISS
- [ ] Melhorar segmentação de dispositivos (§, incisos, alíneas)
- [ ] Adicionar filtros temporais na busca
- [ ] Implementar modo de exportação em PDF para pareceres

### Longo Prazo (3-6 meses)
- [ ] Fine-tuning de modelo LLM com dados legislativos de RO
- [ ] RAG multi-hop (encadeamento de consultas automáticas)
- [ ] Integração com fontes externas (CONFAZ, STF, STJ)
- [ ] Deploy em servidor institucional com autenticação
- [ ] Monitoramento de novas publicações legislativas (crawler agendado)

---

## 5. Comparativo de Custos Computacionais

| Cenário | RAM Necessária | Tempo de Indexação (13k docs) | Latência por Query |
|---------|---------------|-------------------------------|-------------------|
| **Atual** (BGE-M3 + Llama3 CPU) | ~12 GB | ~12 horas | ~30-60s |
| **Otimizado** (E5-small + Qwen2.5 q4) | ~8 GB | ~45 min | ~10-20s |
| **Ultra-leve** (MiniLM + Phi3 q4) | ~4 GB | ~12 min | ~5-10s |
| **Com GPU** (BGE-M3 + Llama3 q4) | ~14 GB VRAM | ~8 min | ~3-5s |

---

## 6. Conclusão

O projeto está **muito bem estruturado** para um sistema RAG em estágio inicial. A arquitetura modular (crawler → ETL → embeddings → retriever → prompt → dashboard) permite otimizações incrementais sem reescritas. 

As maiores oportunidades de ganho imediato são:

1. **Trocar o modelo de embedding** para um mais leve (ganho de 15x em velocidade)
2. **Configurar um LLM quantizado menor** (melhor experiência no chat)
3. **Adicionar cache e pré-carregamento** (eliminar latência de startup)

Essas 3 mudanças, juntas, transformariam a experiência de uso de "demo funcional" para "ferramenta de produção" sem custo adicional de infraestrutura.
