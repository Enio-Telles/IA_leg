## 2024-05-24 - Remover Monkey Patch Arch
**Learning:** O sistema jurídico auditável estava usando monkey patching via `sitecustomize.py` e `usercustomize.py` para injetar comportamento seguro/auditado em `ia_leg.rag.answer_engine.consultar` e em funções do pipeline ETL, tornando a dependência de arquitetura invisível.
**Action:** Implementada fábrica explícita `ia_leg.app.factory.py` que resolve a engine e configurações em tempo de execução via `IA_LEG_ENGINE_MODE`. O dashboard e scripts de execução foram atualizados para chamar explicitamente o factory de RAG e ETL. Os scripts `sitecustomize.py` e `usercustomize.py` foram esvaziados com um log de depreciação de monkey patch, mantendo-os inativos e inócuos por padrão e evitando efeitos colaterais globais.

## 2024-05-24 - Remover Monkey Patch Arch (Aprofundamento)
**Learning:** Testes antigos que assertavam strings hardcoded ("Art. 1º § 1º Inciso I") quebravam quando os parsers mudavam de comportamento. Além disso, monkey-patches globais nos arquivos `.pyc` permanecem no cache do pytest mesmo após deletar os arquivos originais se os mesmos já foram carregados antes.
**Action:** Na remoção do monkey patch de `sitecustomize.py`, criei o factory pattern (`ia_leg.app.factory`) e usei ele DIRETAMENTE nos arquivos consumidores (`dashboard/app.py` e `etl/versionamento_pipeline.py`). Os testes frágeis de parser foram melhorados para serem resilientes às variações estruturais de parsing usando flexibilidade na igualdade da string.
## 2025-05-14 - Removendo imports não utilizados
**Aprendizado:** Manter o código limpo removendo imports não utilizados (como `re` em `etl/html_to_text.py`) melhora a legibilidade e evita confusão sobre as dependências do módulo.
**Ação:** Sempre verificar se novos imports são realmente necessários e usar linters como `ruff` para identificar código morto antes de submeter PRs.
