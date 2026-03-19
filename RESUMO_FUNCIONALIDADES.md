# Resumo das Funcionalidades: IA_leg (Revisor Fiscal Inteligente - SEFIN-RO)

Com base na exploração do código-fonte, o projeto **IA_leg** é um sistema avançado de **Retrieval-Augmented Generation (RAG)** focado na legislação tributária de Rondônia. Aqui estão as principais funcionalidades mapeadas:

### 1. Coleta e Ingestão de Dados (Crawler)
*   **Módulo:** `crawler/legislacao.py`
*   **Funcionalidade:** Conecta-se à API oficial da SEFIN-RO (`https://legislacao.sefin.ro.gov.br`) para baixar automaticamente normas jurídicas (JSONs com metadados/HTML e PDFs).
*   **Controle:** Verifica o sistema de arquivos para evitar o download duplicado e reprocessamento de leis já baixadas.

### 2. Processamento e Estruturação (ETL & Versionamento)
*   **Módulos (`etl/`):** `html_to_text.py`, `normalizador.py`, `versionamento_pipeline.py`.
*   **Funcionalidades:**
    *   **Limpeza:** Remove tags HTML transformando o conteúdo em texto limpo.
    *   **Normalização:** Extrai metadados padronizados (ex: "D 22721/2018" -> Tipo: "Decreto", Número: "22721", Ano: "2018") e formata datas.
    *   **Segmentação e Versionamento:** Divide o texto completo em dispositivos menores (Artigos, Parágrafos, etc.). Registra o histórico e as versões das leis, calculando hashes de texto para identificar o que foi incluído, alterado ou revogado (`diff_estrutural`).

### 3. Armazenamento de Conhecimento (Banco de Dados)
*   **Módulo:** `database/schema.sql` (banco `metadata.db` em SQLite).
*   **Funcionalidade:** Armazena toda a estrutura jurídica:
    *   Tabelas de `normas`, `versoes_norma`, e `dispositivos`.
    *   `relacoes_normativas`: Identifica se uma norma altera, revoga ou regulamenta outra.
    *   `embeddings`: Guarda as representações vetoriais dos textos para busca semântica.
    *   `feedback_respostas`: Coleta notas sobre a qualidade das respostas geradas.

### 4. Motor de Busca e Geração (Pipeline RAG)
*   **Módulos (`rag/`):** `embeddings.py`, `retriever.py`, `reranker.py`, `prompt_engine.py`.
*   **Funcionalidades:**
    *   **Vetorização:** O `embeddings.py` converte os textos em vetores matemáticos usando o modelo `BAAI/bge-m3`.
    *   **Busca Semântica (Retriever):** Recupera os dispositivos legais mais similares à pergunta do usuário usando cálculo de similaridade de cosseno.
    *   **Refinamento (Reranker):** Um modelo Cross-Encoder reordena os resultados do Retriever para maximizar a precisão do contexto jurídico recuperado.
    *   **Geração de Resposta (Prompt Engine):** Constrói prompts instruindo o LLM (ex: `Ollama` com `qwen2.5:14b-instruct-q4_K_M`) a atuar como Auditor Fiscal, forçando a fundamentação das respostas nas fontes recuperadas, sem alucinar leis.

### 5. Interfaces de Interação (Frontend)
*   **Aplicação Principal (`frontend/`):** Um SPA construído com React, TypeScript, Vite e Tailwind CSS.
    *   **Painel Geral (`PainelGeral.tsx`):** Dashboard com estatísticas da base legislativa (quantidade de normas, dispositivos, vetores).
    *   **Consulta à IA (`ConsultaIA.tsx`):** Interface de chat interativa para o usuário fazer perguntas e receber respostas fundamentadas da IA.
    *   **Linha do Tempo (`LinhaDoTempo.tsx`):** Visualização cronológica do histórico de publicações e alterações legislativas (status de Vigente/Revogado).
    *   **Explorador (`ExplorarNormas.tsx`):** Ferramenta de busca manual e visualização da estrutura e versões das normas.
*   **Dashboard Legado (`dashboard/app.py`):** Interface inicial desenvolvida em Streamlit.

### 6. Orquestração e Configuração
*   **Módulos:** `main.py`, `config.py`, `iniciar.py`.
*   **Funcionalidades:**
    *   Centralização de configurações (modelos, caminhos, parâmetros de chunking).
    *   CLI (`main.py`) para iniciar o processo de indexação vetorial ou levantar as interfaces web.
    *   Script de bootstrap (`iniciar.py`) para configurar o ambiente Conda, banco de dados e iniciar os serviços.
