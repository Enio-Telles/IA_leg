# IA_leg — Revisor Fiscal Inteligente (SEFIN-RO)

Sistema de consulta jurídica com **RAG auditável** para legislação tributária de Rondônia.

Esta branch consolida um núcleo de melhoria focado em quatro frentes:
- **segmentação jurídica hierárquica** para artigos, parágrafos, incisos e alíneas;
- **resposta segura com citações verificáveis**;
- **trilha auditada de consultas** com registro de fallback, score e fontes usadas;
- **benchmark auditado** e painel de observabilidade operacional.

---

## Estado operacional desta branch

O caminho operacional recomendado nesta branch é:
1. ingestão e indexação da base;
2. consulta pelo dashboard Streamlit principal;
3. observabilidade pelo painel auditado;
4. benchmark pelo runner auditado.

### Interfaces recomendadas

**Consulta principal**
```bash
streamlit run dashboard/app.py
```

**Observabilidade auditada**
```bash
streamlit run dashboard/observability_audit_app_v2.py
```

### Benchmark recomendado

```bash
python scripts/benchmark_ia_leg_audited.py
```

Saída padrão:
- `ia_leg/observability/benchmark_resultados_auditados.json`

---

## Arquitetura consolidada

```mermaid
graph TD
    A[Base normativa] --> B[ETL / Parser jurídico hierárquico]
    B --> C[Dispositivos + metadados]
    C --> D[Embeddings]
    D --> E[Retriever]
    E --> F[Reranker]
    F --> G[Engine segura]
    G --> H[Engine segura auditada]
    H --> I[Dashboard principal]
    H --> J[Query audit logs]
    H --> K[Benchmark auditado]
    K --> L[Painel de observabilidade auditada]
```

### Componentes principais

- `ia_leg/etl/legal_parser.py`  
  Parser jurídico hierárquico.

- `ia_leg/rag/citation_guard.py`  
  Validação de âncoras verificáveis e fallback seguro.

- `ia_leg/rag/answer_engine_safe.py`  
  Trilha segura base.

- `ia_leg/rag/answer_engine_safe_audited.py`  
  Trilha segura com auditoria detalhada.

- `sitecustomize.py` e `usercustomize.py`  
  Consolidação do comportamento seguro/auditado no fluxo principal sem alterar diretamente todos os pontos antigos do projeto.

- `ia_leg/observability/audit_logger.py`  
  Persistência de auditoria em tabela própria.

- `ia_leg/observability/benchmark_runner_audited.py`  
  Benchmark auditado com campos alinhados à trilha de auditoria.

- `dashboard/observability_audit_app_v2.py`  
  Painel consolidado de observabilidade.

---

## Tabelas e logs relevantes

### Tabela principal da trilha auditada
- `query_audit_logs`

Campos relevantes:
- `fallback_reason`
- `max_score`
- `source_anchor_ok`
- `source_identifiers`
- `source_normas`
- `search_time_ms`
- `rerank_time_ms`
- `llm_time_ms`
- `total_time_ms`

### Tabela legada de compatibilidade
- `query_logs`

Nesta branch, `query_logs` continua existindo por compatibilidade histórica, mas o **foco operacional** da auditoria está em `query_audit_logs`.

---

## Como operar

### 1. Setup
```bash
python -m ia_leg setup
```

### 2. Ingestão
```bash
python -m ia_leg ingest
```

### 3. Indexação
```bash
python -m ia_leg index
```

### 4. Consulta
```bash
streamlit run dashboard/app.py
```

### 5. Benchmark auditado
```bash
python scripts/benchmark_ia_leg_audited.py \
  --query-file ia_leg/observability/benchmark_queries_sefin_expanded.json
```

### 6. Observabilidade auditada
```bash
streamlit run dashboard/observability_audit_app_v2.py
```

---

## Variáveis úteis

```bash
IA_LEG_ENABLE_SAFE_PATCHES=1
IA_LEG_SAFE_TOP_K=5
IA_LEG_SAFE_MIN_SCORE=0.20
IA_LEG_SAFE_REQUIRE_ANCHORS=1
```

---

## Validação antes de merge

```bash
pytest tests/
python scripts/pre_merge_audit_check.py
python scripts/benchmark_ia_leg_audited.py
```

---

## Observações importantes

- O frontend React continua existindo no repositório, mas **não é o caminho operacional principal desta branch**.
- A consolidação do fluxo principal foi feita por `sitecustomize.py` e `usercustomize.py`. Isso entrega efeito operacional imediato, mas ainda pode ser refatorado depois para integração direta nos módulos principais.
- O painel auditado v2 é o **painel recomendado** para leitura de benchmark e auditoria nesta branch.

---

## Documentação complementar

- `OPERACAO_AUDITADA_MAR2026.md`
- `MERGE_CHECKLIST_MAR2026.md`

---
**SEFIN-RO** | Desenvolvimento Interno | 2026
