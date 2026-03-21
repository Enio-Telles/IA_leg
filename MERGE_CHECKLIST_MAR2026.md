# Checklist de merge — março/2026

## 1. Validação funcional
- [ ] `python -m ia_leg setup`
- [ ] `python -m ia_leg ingest`
- [ ] `python -m ia_leg index`
- [ ] `streamlit run dashboard/app.py`
- [ ] `streamlit run dashboard/observability_audit_app_v2.py`
- [ ] `python scripts/benchmark_ia_leg_audited.py`

## 2. Validação técnica
- [ ] `pytest tests/`
- [ ] `python scripts/pre_merge_audit_check.py`
- [ ] benchmark auditado gera JSON sem erro
- [ ] `query_audit_logs` é criada automaticamente
- [ ] `usercustomize.py` sobrepõe a engine segura auditada

## 3. Validação de qualidade
- [ ] benchmark com `benchmark_queries_sefin_expanded.json`
- [ ] fallback rate em nível aceitável
- [ ] source anchor rate em nível aceitável
- [ ] tempos médios dentro do esperado
- [ ] painel auditado abre sem erro

## 4. Itens de revisão manual
- [ ] confirmar que a trilha auditada está ativa no ambiente alvo
- [ ] confirmar se o benchmark auditado deve virar padrão oficial
- [ ] decidir se os painéis antigos serão mantidos ou descontinuados
- [ ] decidir se `sitecustomize_safe_audit.py` ainda precisa ser mantido

## 5. Pós-merge recomendado
- [ ] atualizar README principal
- [ ] consolidar entrypoints paralelos que ficaram redundantes
- [ ] executar benchmark real com perguntas da SEFIN
- [ ] registrar baseline oficial de métricas
