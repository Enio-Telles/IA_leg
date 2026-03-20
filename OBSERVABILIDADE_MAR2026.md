# Observabilidade e benchmark expandido — março/2026

Este lote adiciona duas frentes:

## 1. Base ampliada de queries fiscais
Arquivo:
- `ia_leg/observability/benchmark_queries_sefin_expanded.json`

Contém um conjunto maior de perguntas com foco em:
- ICMS próprio
- ICMS-ST
- EFD ICMS/IPI
- TATE
- benefícios fiscais
- energia elétrica
- combustíveis
- obrigações acessórias

## 2. Painel de observabilidade
Arquivos:
- `ia_leg/observability/log_reader.py`
- `dashboard/observability_app.py`
- `tests/test_log_reader.py`

### O que o painel mostra
- quantidade de consultas registradas
- taxa de sucesso
- tempo médio total
- chunks médios
- resumo do benchmark
- tabela detalhada do benchmark
- tabela e gráficos de `query_logs`

### Como executar
```bash
streamlit run dashboard/observability_app.py
```

## 3. Arquivo de benchmark
Você pode apontar no painel para:
- `ia_leg/observability/benchmark_resultados.json`
- ou outro JSON gerado pelo benchmark runner

## 4. Fluxo recomendado
1. rodar benchmark
2. abrir painel de observabilidade
3. comparar fallback rate, source anchor rate e tempos médios
4. ajustar threshold, prompt, parser ou retriever
