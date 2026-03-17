# Plano Revisado de Implementação do Crawler (SEFIN-RO)

## 1. Objetivo:
Criar um crawler robusto e automático para o portal legislacao.sefin.ro.gov.br.
O crawler irá listar as legislações disponíveis, gerenciar quais já foram baixadas (via controle de hash/banco SQLite) e salvar os PDFs localmente extraindo seus metadados.

## 2. Abordagem de Extração (Scraping/API):
- O site da SEFIN (legislacao.sefin.ro.gov.br) utiliza renderização dinâmica ou rotas de API para expor as leis e decretos.
- Precisaremos usar bibliotecas como `requests` + `BeautifulSoup` (se for HTML estático) ou `requests` consumindo os endpoints JSON da API (se for um SPA/React/Vue). Se houver bloqueios (WAF/Cloudflare) estruturaremos as requisições com headers simulando um navegador, ou se necessário futuramente, usaremos `playwright` (embora `requests` puro seja a prioridade para estabilidade e velocidade em backends).

## 3. Etapas Estruturadas:

### Etapa 1: Exploração e Mapeamento da Fonte
- [x] Construir um script de teste exploratório para entender a paginação e a estrutura de dados (ou rotas HTTP GET) do portal legislacao.sefin.ro.gov.br.
- [x] Identificar a URL correta da API de listagem de documentos reais e filtros (Ano, Tipo de Norma).

### Etapa 2: Crawler Base Integrado ao Banco SQLite
- [x] Modificar `crawler/legislacao.py` para buscar ativamente a lista de normativos do SEFIN.
- [x] Implementar lógica de paginação para recuperar o histórico completo.
- [x] Baixar cada PDF temporariamente e calcular o Hash SHA-256 (reaproveitando o que fizemos no `versionamento_pipeline.py`).
- [x] Verificar no banco (tabela `normas` e `versoes_norma`) se aquele hash ou Norma(Tipo, Número, Ano) já existe. Se existir, ignorar o download.

### Etapa 3: Persistência e Download Físico
- [x] Baixar e salvar PDFs não duplicados na respectiva pasta `documentos/pdf/`.
- [x] Gerar um JSON estruturado em `documentos/metadados.json` ou inserir o registro base da norma para processamento posterior pela pipeline ETL.

### Etapa 4: Teste Integrado (Crawler + Pipeline ETL)
- [x] Criar arquivo de teste `tests/test_crawler.py` ou rotina no `main.py` para acionar o Crawler.
- [x] Disparar a pipeline de versionamento (`versionamento_pipeline.py`) para os novos PDFs baixados.

---
## User Review Required
A abordagem principal focará em engenharia reversa das requisições de rede (API intercepting) do portal SEFIN. Se o portal tiver proteções contra bots complexas que impeçam o uso do Python Requests puro, você autorizaria o uso do `Selenium`/`Playwright`? (Por padrão tentarei `requests`).

## Verification Plan
1. **Automated Verification:** Vou rodar um pequeno script python `test_extracao.py` para comprovar que conseguimos obter a listagem de leis (JSON ou HTML) da Sefin via terminal.
2. **Manual Verification:** O usuário validará as tabelas do banco preenchidas e a existência real dos PDFs recém-baixados na pasta local `documentos/pdf`.
