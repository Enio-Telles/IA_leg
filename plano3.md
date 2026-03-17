# Plano de Melhorias — IA_leg (Revisor Fiscal Inteligente)

**Hardware de Referência:** Intel i7 13ª Geração · 32 GB RAM · NVIDIA RTX 3060 12 GB VRAM  
**Data:** 21/02/2026  
**Status atual da base:** 7.624 / 13.275 embeddings indexados (~57%)

---

## Diagnóstico do Ambiente Atual

| Item | Estado Atual | Problema |
|------|-------------|----------|
| **PyTorch + CUDA** | ❌ CUDA não detectado (`torch.cuda.is_available() = False`) | PyTorch instalado sem suporte CUDA no env `base` |
| **Modelo de Embedding** | BGE-M3 (2.2 GB, 1024 dims) rodando em **CPU** | ~0.3 txt/s — 18h+ para indexar 13k docs |
| **Busca Vetorial** | Brute-force com numpy (carrega TUDO na RAM) | O(n) por query, aceitável para 13k mas não escala |
| **LLM (Ollama)** | `llama3:latest` (8B, ~8 GB) | Funcional, mas modelo genérico — pode melhorar em PT-BR |
| **Cache** | Nenhum cache de queries ou modelo pré-carregado no dashboard | Latência de ~30s no primeiro uso + reprocessamento de queries repetidas |

> [!IMPORTANT]
> A RTX 3060 com 12 GB de VRAM é capaz de rodar **simultaneamente** embeddings com GPU (~50x mais rápido) e modelos LLM quantizados. Essa placa muda completamente a estratégia ideal.

---

## Fase 1 — Ativação da GPU (Impacto Imediato)

### 1.1 Instalar PyTorch com CUDA

O ambiente conda `base` não possui PyTorch compilado com suporte à GPU. É necessário reinstalar:

```bash
# Criar ambiente dedicado para o projeto
conda create -n ia_leg python=3.11 -y
conda activate ia_leg

# Instalar PyTorch com CUDA 12.1 (compatível com RTX 3060)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Instalar dependências do projeto
pip install streamlit pandas sentence-transformers requests numpy
```

**Verificação:**
```bash
python -c "import torch; print('CUDA:', torch.cuda.is_available(), '| GPU:', torch.cuda.get_device_name(0))"
# Esperado: CUDA: True | GPU: NVIDIA GeForce RTX 3060
```

**Ganho esperado:** Embeddings passam de ~0.3 txt/s para **15-50 txt/s** (50-150x mais rápido). A indexação dos 13k dispositivos levaria **~5 minutos** em vez de 18 horas.

### 1.2 Mover Modelo de Embedding para GPU

#### [MODIFY] `rag/embeddings.py`
Alterar `carregar_modelo()` para usar GPU automaticamente:

```python
def carregar_modelo():
    global _MODELO
    if _MODELO is None:
        if SentenceTransformer is None:
            raise ImportError("Instale 'sentence-transformers'")
        
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Carregando modelo {MODELO_NOME} no dispositivo: {device}")
        _MODELO = SentenceTransformer(MODELO_NOME, device=device)
    return _MODELO
```

**Nenhuma outra alteração necessária** — o `sentence-transformers` roteia automaticamente os tensores para a GPU.

---

## Fase 2 — Otimização do LLM

### 2.1 Modelo Ollama Otimizado para Português

Com 12 GB de VRAM e 32 GB de RAM, é possível rodar modelos maiores e mais precisos:

| Modelo | VRAM | Velocidade | Qualidade PT-BR | Recomendação |
|--------|------|------------|-----------------|--------------|
| **qwen2.5:14b-instruct-q4_K_M** | ~10 GB | ~12 tok/s (GPU) | ⭐⭐⭐⭐⭐ | 🥇 **Melhor opção** — cabe na RTX 3060 |
| **llama3:8b-instruct-q5_K_M** | ~6 GB | ~25 tok/s (GPU) | ⭐⭐⭐⭐ | Rápido e preciso |
| **deepseek-r1:14b** | ~10 GB | ~10 tok/s (GPU) | ⭐⭐⭐⭐⭐ | Raciocínio jurídico forte |
| **gemma2:9b-instruct-q5_K_M** | ~7 GB | ~20 tok/s (GPU) | ⭐⭐⭐⭐ | Boa alternativa |

```bash
# Instalar modelo recomendado
ollama pull qwen2.5:14b-instruct-q4_K_M

# Testar
ollama run qwen2.5:14b-instruct-q4_K_M "Explique a alíquota do ICMS sobre combustíveis em Rondônia"
```

### 2.2 Configurar Modelo no Sistema

#### [MODIFY] `config.py`
Adicionar configuração centralizada de modelos:

```python
# Modelos
EMBEDDING_MODEL = "BAAI/bge-m3"
LLM_MODEL = "qwen2.5:14b-instruct-q4_K_M"  # Atualizado
```

#### [MODIFY] `rag/prompt_engine.py`
Atualizar o modelo padrão para usar `config.py`:

```python
from config import LLM_MODEL
OLLAMA_MODELO = os.environ.get("OLLAMA_MODELO", LLM_MODEL)
```

---

## Fase 3 — Performance da Busca Vetorial

### 3.1 Cache de Queries no Retriever

#### [MODIFY] `rag/retriever.py`
Adicionar cache LRU para queries frequentes e pré-carregar vetores na memória:

```python
import hashlib
from functools import lru_cache

# Carregar vetores uma vez na memória
_VETORES_CACHE = None

def _carregar_vetores():
    global _VETORES_CACHE
    if _VETORES_CACHE is not None:
        return _VETORES_CACHE
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT e.dispositivo_id, d.identificador, d.texto,
               n.tipo, n.numero, n.ano, e.vetor
        FROM embeddings e
        JOIN dispositivos d ON e.dispositivo_id = d.id
        JOIN versoes_norma v ON d.versao_id = v.id
        JOIN normas n ON v.norma_id = n.id
        WHERE v.vigencia_fim IS NULL
    ''')
    _VETORES_CACHE = cursor.fetchall()
    conn.close()
    return _VETORES_CACHE
```

### 3.2 Pré-carregar Modelo no Dashboard

#### [MODIFY] `dashboard/app.py`
Adicionar cache do modelo de embedding para eliminar o delay de ~30s na primeira consulta:

```python
@st.cache_resource
def carregar_modelo_rag():
    from rag.embeddings import carregar_modelo
    return carregar_modelo()

# Chamar no início do app (lazy, carrega quando necessário)
```

---

## Fase 4 — Qualidade das Respostas (Reranking)

### 4.1 Reranker Cross-Encoder

#### [NEW] `rag/reranker.py`
Adicionar segunda passada de relevância para refinar os resultados do retriever:

```python
"""
Reranker cross-encoder para refinar resultados da busca vetorial.
"""
from sentence_transformers import CrossEncoder

_RERANKER = None

def carregar_reranker():
    global _RERANKER
    if _RERANKER is None:
        _RERANKER = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", device="cuda")
    return _RERANKER

def rerankar(pergunta, candidatos, top_k=3):
    reranker = carregar_reranker()
    pares = [(pergunta, c["texto"]) for c in candidatos]
    scores = reranker.predict(pares)
    for i, c in enumerate(candidatos):
        c["score_rerank"] = float(scores[i])
    candidatos.sort(key=lambda x: x["score_rerank"], reverse=True)
    return candidatos[:top_k]
```

#### [MODIFY] `rag/prompt_engine.py`
Integrar o reranker no pipeline `consultar()`:

```python
def consultar(pergunta, top_k=5, backend="ollama"):
    from rag.retriever import recuperar_contexto
    from rag.reranker import rerankar
    
    contextos = recuperar_contexto(pergunta, top_k=top_k * 2)  # Buscar 2x mais
    contextos = rerankar(pergunta, contextos, top_k=top_k)      # Refinar com reranker
    # ... restante do pipeline
```

**Instalação:** `pip install sentence-transformers` (já instalado)  
**Modelo do reranker:** ~80 MB, roda na GPU junto com o embedding.

---

## Fase 5 — Melhorias Futuras (Médio Prazo)

### 5.1 FAISS para Busca Vetorial (quando base > 50k)

#### [NEW] `rag/index.py`
Substituir busca brute-force por índice FAISS:

```python
import faiss
import numpy as np

def criar_indice(vetores: np.ndarray):
    dim = vetores.shape[1]
    index = faiss.IndexFlatIP(dim)  # Cosine sim com vetores normalizados
    index.add(vetores)
    return index
```

**Quando implementar:** Apenas quando a base ultrapassar 50k dispositivos. Com 13k, o numpy brute-force leva < 50ms por query.

### 5.2 Chunking Avançado (§, Incisos, Alíneas)

Atualmente o ETL segmenta apenas por `"Art."`. Proposta de expansão para capturar hierarquia jurídica completa (§, incisos, alíneas), conforme descrito na seção 3.5 do `ANALISE_PROJETO.md`.

### 5.3 Filtros Temporais na Busca

Permitir consultas como "legislação vigente em 2020" adicionando parâmetro `data_referencia` ao retriever.

### 5.4 Exportação de Pareceres em PDF

Gerar documentos formais a partir das respostas do LLM usando `reportlab` ou `weasyprint`.

---

## Resumo de Impacto por Fase

| Fase | Esforço | Impacto | Tempo |
|------|---------|---------|-------|
| **1. Ativação GPU** | Baixo | 🔴 Crítico — Indexação de 18h → 5min | 30 min |
| **2. LLM Otimizado** | Baixo | 🟡 Alto — Respostas mais rápidas e precisas em PT-BR | 15 min |
| **3. Cache + Pré-carga** | Médio | 🟡 Alto — Elimina latência de 30s no dashboard | 1-2 horas |
| **4. Reranking** | Médio | 🟢 Moderado — Melhora precisão das respostas | 1-2 horas |
| **5. FAISS/Chunking/PDF** | Alto | 🟢 Incremental — Escalabilidade futura | Dias/Semanas |

---

## Checklist de Implementação

### Fase 1 — GPU ✅
- [x] Criar ambiente conda `leg_ia` com Python 3.11
- [x] Instalar PyTorch com CUDA 12.4 (`2.5.1+cu124`)
- [x] Instalar dependências do projeto (mamba + pip)
- [x] Verificar CUDA disponível (`True` — RTX 3060 12 GB)
- [x] Alterar `rag/embeddings.py` para usar GPU
- [/] Re-indexar toda a base com GPU (~2h30, em progresso: 63.2%)

### Fase 2 — LLM
- [x] Baixar `qwen2.5:14b-instruct-q4_K_M` via Ollama (~9 GB)
- [x] Atualizar `config.py` com novo modelo
- [x] Atualizar `prompt_engine.py` para ler modelo de `config.py`
- [ ] Testar consultas no dashboard

### Fase 3 — Cache ✅
- [x] Implementar cache de vetores em `retriever.py`
- [x] Pré-carregar modelo no `dashboard/app.py`
- [x] Busca vetorizada com `np.argpartition` (Top-K eficiente)

### Fase 4 — Reranking ✅
- [x] Criar `rag/reranker.py` (cross-encoder `ms-marco-MiniLM-L-6-v2`)
- [x] Integrar reranker no pipeline `consultar()`
- [x] Testar melhoria de relevância

