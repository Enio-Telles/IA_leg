# Próximos passos implementados — março/2026

Além do primeiro lote de hardening do RAG, este PR agora inclui **entrypoints operacionais** para colocar as melhorias em uso imediato.

## 1. Dashboard com trilha segura

Arquivo: `dashboard/app_safe.py`

### O que faz
- reaproveita o dashboard atual
- intercepta a chamada padrão de consulta
- força uso de `consultar_seguro()`
- aplica fallback quando a resposta não está ancorada nas fontes

### Como executar
```bash
streamlit run dashboard/app_safe.py
```

### Variáveis opcionais
```bash
IA_LEG_SAFE_TOP_K=5
IA_LEG_SAFE_MIN_SCORE=0.20
IA_LEG_SAFE_REQUIRE_ANCHORS=1
```

---

## 2. Pipeline ETL com parser hierárquico

Arquivo: `etl/versionamento_pipeline_safe.py`

### O que faz
- reutiliza o pipeline legado
- substitui a função simplista de quebra por parser jurídico hierárquico
- cai para chunking genérico quando não há estrutura normativa clássica
- adiciona `processar_tudo()` para compatibilidade com o novo CLI

### Como executar
```bash
python etl/versionamento_pipeline_safe.py
```

---

## 3. Testes de fumaça

Arquivo: `tests/test_safe_entrypoints.py`

Garante:
- import do dashboard seguro
- existência do `processar_tudo()` no pipeline seguro

---

## 4. Estratégia adotada

O conector disponível nesta sessão não permitiu editar diretamente os arquivos já existentes com segurança granular.
Por isso, a implementação foi feita por **entrypoints substitutos prontos para uso**, preservando o fluxo atual e evitando regressão.

O efeito prático é imediato:
- já existe dashboard seguro executável
- já existe pipeline ETL seguro executável

---

## 5. Próximo passo recomendado fora deste lote

Quando for conveniente, consolidar os entrypoints no fluxo principal:
1. `dashboard/app.py` -> usar engine segura por padrão
2. `etl/versionamento_pipeline.py` -> usar parser hierárquico como implementação nativa
3. atualizar o CLI para apontar diretamente para os entrypoints seguros
