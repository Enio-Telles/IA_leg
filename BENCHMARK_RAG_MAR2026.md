# Benchmark do RAG — março/2026

Este lote adiciona benchmark repetível para o IA_leg.

## Arquivos
- `ia_leg/observability/benchmark_queries.json`
- `ia_leg/observability/benchmark_runner.py`
- `scripts/benchmark_ia_leg.py`
- `tests/test_benchmark_runner.py`

## O que mede
- taxa de fallback
- taxa de presença de palavras esperadas
- taxa de presença de termos de âncora esperados
- taxa de âncoras verificáveis nas fontes recuperadas
- tempo médio de recuperação
- tempo médio de resposta
- score máximo médio do contexto recuperado

## Como executar
```bash
python scripts/benchmark_ia_leg.py
```

Ou:
```bash
python -m ia_leg.observability.benchmark_runner --backend ollama --top-k 5 --min-score 0.20
```

## Saída
O benchmark gera um arquivo JSON com:
- resumo agregado
- resultado detalhado por query
- preview da resposta
- normas e identificadores recuperados

## Uso recomendado
Rodar sempre que houver mudança em:
- parser jurídico
- retriever
- reranker
- prompt
- threshold de segurança
