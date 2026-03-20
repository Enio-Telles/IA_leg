# Implementação inicial do plano de melhorias — março/2026

Este lote implementa a parte mais crítica do plano: **confiabilidade jurídica do RAG**.

## Entregas deste lote

### 1. Parser jurídico hierárquico
Arquivo: `ia_leg/etl/legal_parser.py`

Inclui:
- segmentação por artigo
- extração de parágrafos
- extração de incisos
- extração de alíneas
- função para chunking de documentos genéricos

Uso sugerido:
```python
from ia_leg.etl.legal_parser import quebrar_dispositivos_hierarquicos
chunks = quebrar_dispositivos_hierarquicos(texto_normativo)
```

### 2. Camada de proteção de citações
Arquivo: `ia_leg/rag/citation_guard.py`

Inclui:
- detecção de âncoras verificáveis
- montagem de bloco de fontes verificadas
- fallback contextual seguro

### 3. Engine de resposta segura
Arquivo: `ia_leg/rag/answer_engine_safe.py`

Inclui:
- threshold mínimo de relevância
- prompt mais restritivo
- fallback quando o LLM não ancora nas fontes
- anexação obrigatória das fontes verificadas

Uso sugerido:
```python
from ia_leg.rag.answer_engine_safe import consultar_seguro
resposta = consultar_seguro("Qual a alíquota interna do ICMS?", top_k=5)
```

### 4. Testes unitários
Arquivos:
- `tests/test_legal_parser.py`
- `tests/test_citation_guard.py`

## O que ainda não ficou integrado automaticamente

Esta implementação foi entregue sem refatorar os arquivos já em produção da interface atual.
Ou seja:
- o `dashboard/app.py` continua usando o fluxo padrão
- a nova trilha segura pode ser adotada imediatamente nos pontos de integração
- o próximo passo natural é trocar a chamada atual de consulta para `consultar_seguro(...)`

## Próximo passo recomendado

1. ligar o `consultar_seguro()` à interface atual
2. trocar o parser antigo do ETL pelo `quebrar_dispositivos_hierarquicos()`
3. criar benchmark comparando recuperação antiga vs. nova
