# Proposta Técnica: Arquitetura-Alvo e Plano de Evolução do IA_leg

## 1. Visão Geral e Contexto
O IA_leg já se mostra uma ferramenta fundamental, estruturada sobre um pipeline maduro de Recuperação da Informação e Geração Aumentada (RAG) voltado à legislação fiscal de Rondônia. O projeto alcançou resultados expressivos com:
*   Modelagem robusta em PyTorch/SentenceTransformers (BGE-M3 e MS-MARCO).
*   Segmentação hierárquica inovadora de normas.
*   Trilha de auditoria (Citation Guard) visando segurança e minimização de alucinações.
*   Painéis operacionais no Streamlit, além de um backend pronto para consumo de uma SPA em React.

Contudo, para escalar este projeto rumo à alta disponibilidade, baixa latência e total confiabilidade sistêmica como produto, o sistema demanda refatorações que mitigam acoplamentos técnicos, afunilamentos computacionais (O(N) search) e tratamento de documentos genéricos ou mal formatados.

---

## 2. Análise Profunda: Diagnóstico por Área (Os 14 Aspectos)

### 2.1. Organização geral do repositório
**Situação atual:** O repositório está logicamente organizado nas pastas `crawler`, `etl`, `ia_leg` (core, config, rag, observability), `dashboard` e `frontend` (React). Porém, existe duplicação de responsabilidades, particularmente nos `answer_engine.py`, `answer_engine_safe.py` e `answer_engine_safe_audited.py`.
**Recomendação:** Consolidar os pipelines de resposta em um motor unificado parametrizado por _Feature Flags_ ou _Strategy Pattern_. Isso centraliza regras de fallback, auditoria e prompt genérico.

### 2.2. Separação entre coleta, parsing, indexação, busca e apresentação
**Situação atual:** Excelente no conceito. O `__main__.py` como CLI comprova o desacoplamento (`setup`, `ingest`, `index`, `serve`).
**Recomendação:** Avançar em orquestração. Hoje dependemos de scripts encadeados, propensos a falhas em massa. Evoluir a coleta e o indexador para uma ferramenta como **Apache Airflow** ou **Prefect** garantirá tolerância a falhas na ingestão contínua.

### 2.3. Qualidade do tratamento de PDFs e documentos normativos
**Situação atual:** O `pdf_to_text.py` utiliza PyMuPDF (`fitz`), o que é muito veloz, mas lida de modo rústico com layouts complexos, cabeçalhos, rodapés e, principalmente, tabelas (frequentes em legislação tributária - ICMS).
**Recomendação:** Introduzir um módulo especializado de Visão Computacional / OCR para tabelas, como `Unstructured.io` ou `LlamaParse`, isolando rodapés/cabeçalhos padrão da SEFIN-RO para não poluírem a busca semântica.

### 2.4. Estrutura de metadados dos documentos
**Situação atual:** Sólida e relacional via SQLite (`normas`, `versoes_norma`, `dispositivos`, `relacoes_normativas`). Captura o essencial (tipo, número, ano, órgão, tema, vigência).
**Recomendação:** Enriquecer o modelo para abraçar categorização semântica (tags automáticas por tema via LLM) e melhorar a modelagem de revogações e vigências retroativas (linha do tempo).

### 2.5. Rastreabilidade da origem e versão dos textos
**Situação atual:** Coberta pelo `versionamento_pipeline.py` e a tabela `diff_estrutural` baseada em hashes criptográficos, o que garante a trilha histórica.
**Recomendação:** Criar endpoints que permitam ao usuário navegar pelo histórico visual do normativo (diff view no React frontend), exibindo visualmente o que mudou de uma versão para outra, ativando a real "Máquina do Tempo" legislativa.

### 2.6. Estratégia de chunking de documentos jurídicos
**Situação atual:** Excepcional. O `legal_parser.py` respeita a hierarquia jurídica (Art. > § > Inciso > Alínea), evitando cortes arbitrários de caracteres.
**Recomendação:** Tratar a interdependência dos chunks. Quando o RAG extrai a "Alínea a", ele precisa, nativamente no vetor ou metadado, saber de qual Inciso, Parágrafo e Artigo ela vem, anexando esse contexto "pai" ao chunk final para não perder sentido semântico isoladamente.

### 2.7. Indexação e recuperação da informação
**Situação atual:** Indexação vetorizada via `bge-m3`. A recuperação é `brute-force` na RAM usando multiplicação de matrizes Numpy (`matrix @ vetor_query`), o que é O(N).
**Recomendação Crítica:** Esta é a mudança de maior impacto a curto/médio prazo. Substituir o brute-force in-memory por um índice **FAISS** (com IndexIVFFlat para alta escala) ou migrar para um VectorDB profissional como **Qdrant** / **Milvus** / **pgvector** se decidirmos migrar todo o SQLite para PostgreSQL.

### 2.8. Qualidade da busca semântica e/ou lexical
**Situação atual:** Usa Busca Semântica Densa (Dense Retrieval) + Reranking (Cross-Encoder). O fluxo garante altíssima relevância semântica.
**Recomendação:** Falta busca Lexical/BM25 (Sparse Retrieval). Leis tributárias têm jargões e códigos exatos (ex: NCM, CFOP). Uma estratégia **Híbrida** (Semantic + Keyword BM25) combinada com Reciprocal Rank Fusion (RRF) trará o ápice da qualidade.

### 2.9. Forma de armazenamento dos dados e índices
**Situação atual:** Banco SQLite (`metadata.db`), com os vetores armazenados em BLOB.
**Recomendação:** Migrar de SQLite para **PostgreSQL**. O SQLite atende protótipos e desktops, mas trava sob forte concorrência (locks de escrita no ETL enquanto há leituras no Serve). A adoção do PostgreSQL + extensão `pgvector` unificaria metadados e vetores num banco robusto e pronto para escala.

### 2.10. Possíveis duplicidades, documentos quebrados ou inconsistentes
**Situação atual:** Hashes nos dispositivos ajudam a detectar mudanças. O pipeline de versão tenta mitigar duplicação.
**Recomendação:** Inserir testes sistemáticos de integridade na camada de ETL e rodar verificações noturnas de "links quebrados" e dispositivos orfãos. O Crawler precisa ter tratamento defensivo de timeouts e arquivos corrompidos para garantir a estabilidade da base primária.

### 2.11. Tratamento de documentos consolidados e não consolidados
**Situação atual:** A base armazena `vigencia_inicio` e `vigencia_fim` e calcula diff estrutural.
**Recomendação:** Institucionalizar um processo de consolidação automática. Quando a Lei B altera a Lei A, o sistema deve ser capaz de gerar e exibir o texto consolidado da Lei A instantaneamente, guardando ambos os estados no tempo.

### 2.12. Suporte a hierarquia normativa e referências internas
**Situação atual:** A tabela `relacoes_normativas` mapeia ORIGEM -> DESTINO (ALTERA, REVOGA).
**Recomendação:** Expandir isso para Graph RAG ou Multi-Hop RAG. Quando um usuário perguntar algo e o Retriever puxar um artigo, o Retriever deve verificar no Grafo se aquele artigo cita outro dispositivo, trazendo ambos como contexto enriquecido ao LLM.

### 2.13. Testes, logs, observabilidade e tolerância a falhas
**Situação atual:** O projeto evoluiu bem com `audit_logger.py`, `query_audit_logs`, fallback methods (Citation Guard) e o painel `observability_audit_app_v2.py`.
**Recomendação:** Integrar com APMs de mercado como **OpenTelemetry**, **Prometheus/Grafana** e **LangSmith** (para trace profundo das respostas do LLM e do Reranker). Aumentar a cobertura de testes de integração na pipeline do ETL e RAG.

### 2.14. Facilidade de manutenção e expansão
**Situação atual:** Código coeso, mas acoplado a rodar na máquina local via scripts Python ou Streamlit.
**Recomendação:** Containerização total. Adotar **Docker** e **Docker Compose** separando os serviços: Frontend (React), API Server (FastAPI), Banco (PostgreSQL/VectorDB), Motor LLM (Ollama Server) e Worker ETL.

---

## 3. Arquitetura-Alvo (Target State)

A nova arquitetura moverá o sistema do estágio "Local/Monolítico" para o "Distribuído/Nuvem":

*   **Ingestão e ETL:** Orquestrados via Apache Airflow. Extração PDF rica (tabelas preservadas). Hashes para dedup e versionamento.
*   **Armazenamento Unificado:** PostgreSQL atuando com metadados relacionais e `pgvector` indexando os embeddings, dispensando o gerenciamento do FAISS in-memory manual.
*   **Retrieval Híbrido:** Motor de busca combinando BM25 (palavras-chave via Elasticsearch ou Postgres FTS) com Busca Densa Vetorial (BGE-M3/E5) unidos via Reciprocal Rank Fusion (RRF), seguido do Reranker (Cross-Encoder) para precisão fina.
*   **Core API (RAG):** Backend unificado em FastAPI (assíncrono), parametrizado para modelos locais (Ollama) ou nuvem. Implementação de Multi-Hop para referências cruzadas.
*   **Frontend:** Transição definitiva do Streamlit para o Single Page Application (SPA) React com Tailwind.
*   **Observabilidade:** Logs centralizados via ELK Stack ou DataDog e tracing do LLM via OpenTelemetry/LangSmith.

---

## 4. Plano Realista de Evolução (Roadmap Trimestral)

### Fase 1: Estabilização e Performance (Semanas 1 a 4)
*   **Troca de Motor Vetorial:** Implantar FAISS temporário no Python ou trocar o modelo de embedding local do gigantesco BGE-M3 para `intfloat/multilingual-e5-small`, reduzindo em 15x o tempo de indexação mantendo alta acurácia em Português.
*   **Refatoração de Código:** Consolidar os 3 scripts de `answer_engine` num único módulo coeso usando features flags.
*   **Melhoria de Chunking Pai-Filho:** Anexar o texto ou o título dos Artigos "pais" nos metadados de seus respectivos Parágrafos, Incisos e Alíneas "filhos".

### Fase 2: Infraestrutura e Backend (Meses 2 e 3)
*   **Migração Banco de Dados:** Substituir SQLite por PostgreSQL + `pgvector`. Adequação das queries.
*   **Containerização:** Dockerizar todo o repositório (`docker-compose.yml` abrangendo API FastAPI, React UI, Postgres, etc).
*   **Busca Lexical (BM25):** Implementar e fundir a busca híbrida (Sparse + Dense Retrieval).
*   **Refinamento PDF:** Substituir PyMuPDF por parser especializado para preservação de tabelas de anexos do ICMS.

### Fase 3: RAG Avançado e Escala (Meses 4 a 6)
*   **RAG Multi-Hop:** Capacitar o Retriever a caminhar nas `relacoes_normativas` injetando leis conectadas ao contexto do prompt.
*   **Painel Admin Definitivo:** Integrar os fluxos operacionais de Auditoria (Audit App V2) para o Frontend React.
*   **Deploy Produtivo:** CI/CD robusto com GitHub Actions, hospedagem gerenciada, Autenticação de Usuários, e rotinas Cron/Airflow para o Crawler noturno dos diários oficiais.
