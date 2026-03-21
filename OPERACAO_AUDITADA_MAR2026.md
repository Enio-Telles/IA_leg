# Operação auditada do IA_leg — março/2026

Este documento descreve **o estado operacional consolidado** da trilha segura/auditada nesta branch.

---

## 1. Fluxo recomendado

### Setup inicial
```bash
python -m ia_leg setup
```

### Ingestão da base
```bash
python -m ia_leg ingest
```

### Indexação vetorial
```bash
python -m ia_leg index
```

---

## 2. Execução do sistema

### Dashboard principal
```bash
streamlit run dashboard/app.py
```

Observação:
- `sitecustomize.py` ativa a trilha segura no fluxo principal;
- `usercustomize.py` sobrepõe para a trilha segura auditada.

### Painel recomendado de observabilidade
```bash
streamlit run dashboard/observability_audit_app_v2.py
```

Este é o **painel canônico** desta branch.

---

## 3. Benchmark auditado

### Benchmark padrão
```bash
python scripts/benchmark_ia_leg_audited.py
```

### Benchmark com arquivo expandido da SEFIN
```bash
python scripts/benchmark_ia_leg_audited.py \
  --query-file ia_leg/observability/benchmark_queries_sefin_expanded.json
```

### Saída esperada
Arquivo gerado:
- `ia_leg/observability/benchmark_resultados_auditados.json`

---

## 4. Logs e auditoria

### Trilha auditada principal
Tabela:
- `query_audit_logs`

Campos mais importantes:
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
Tabela:
- `query_logs`

Uso recomendado:
- tratar `query_logs` como compatibilidade histórica;
- tratar `query_audit_logs` como fonte principal de auditoria operacional.

---

## 5. Variáveis úteis

```bash
IA_LEG_ENABLE_SAFE_PATCHES=1
IA_LEG_SAFE_TOP_K=5
IA_LEG_SAFE_MIN_SCORE=0.20
IA_LEG_SAFE_REQUIRE_ANCHORS=1
```

---

## 6. Fluxo recomendado para evolução do sistema

1. rodar ingestão e indexação;
2. rodar benchmark auditado;
3. abrir o painel auditado v2;
4. analisar fallback rate, source anchor rate, max_score e tempos;
5. ajustar parser, retriever, reranker ou threshold;
6. repetir benchmark.

---

## 7. Comandos úteis de validação

```bash
pytest tests/
python scripts/pre_merge_audit_check.py
python scripts/benchmark_ia_leg_audited.py
```
