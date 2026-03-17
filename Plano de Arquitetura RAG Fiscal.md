# **Plano Detalhado: Sistema de Consulta IA Fiscal/Tributário Local**

## **1\. Análise de Viabilidade e Hardware**

A sua máquina possui um **Processador (CPU) \+ RTX 3060 (presumivelmente 12GB de VRAM) \+ 36GB de RAM**.

* **VRAM (12GB):** É o gargalo principal para IA local, mas 12GB é perfeitamente adequado para rodar Modelos de Linguagem (LLMs) de até 8 a 9 bilhões de parâmetros (ex: Llama-3 8B, Gemma-2 9B, Mistral 7B) quantizados em 4-bit ou 8-bit (formato GGUF). Isso consumirá cerca de 5 a 7GB de VRAM, deixando espaço para o processamento de contexto (as páginas dos PDFs que a IA vai ler).  
* **RAM (36GB):** Excelente. Permite rodar o banco de dados vetorial na memória e processar a extração de PDFs pesados (como o Guia Prático da EFD de centenas de páginas) sem travamentos.

## **2\. Arquitetura do Sistema (Pipeline RAG)**

O sistema não treinará a IA com seus documentos (isso é caro e ineficiente). Ele usará a técnica **RAG**: O usuário faz a pergunta, o sistema "pesquisa" nos seus PDFs, extrai os trechos relevantes e entrega para a IA formular a resposta didática.

### **2.1. Separação e Metadados (Crucial para o seu caso)**

Como você possui origens distintas, cada documento inserido no sistema **deve** receber metadados (tags) antes de virar vetor.

* **Tipo de Documento:** Parecer, Jurisprudencia\_STF, Jurisprudencia\_TATE, Despacho\_Fisconforme, Manual\_MOC, Guia\_Pratico\_EFD, Metodologia.  
* **Estado/UF:** RO, Nacional (ex: STF, Lei Kandir).  
* **Assunto Principal:** ICMS, ST, DIFAL, Obrigacao\_Acessoria.

**Por que isso importa?** Se o usuário perguntar "Como escriturar o FECOEP?", o sistema deve filtrar a busca para procurar *apenas* em Guia\_Pratico\_EFD, Despacho\_Fisconforme e  Parecer, ignorando decisões criminais do STF que possam conter a mesma palavra.

### **2.2. O Stack de Software (Totalmente Local e Gratuito)**

* **Gerenciador do LLM:** Ollama ou LM Studio (Facilita rodar o modelo Llama-3 8B na RTX 3060).  
* **Orquestrador:** LangChain ou LlamaIndex (Python). Recomendado **LlamaIndex** por lidar melhor com hierarquia de documentos estruturados.  
* **Extração de Texto (PDFs):** PyMuPDF (rápido) \+ Camelot ou Tabula-py (ESSENCIAL para extrair as tabelas do Guia Prático e MOC).  
* **Modelo de Embeddings (Vetorização):** BGE-m3 ou paraphrase-multilingual-MiniLM-L12-v2 (modelos leves e excelentes para português jurídico).  
* **Banco de Dados Vetorial:** ChromaDB ou Qdrant (rodam localmente, rápido e suportam filtros por metadados).

## **3\. Propostas de Melhorias e Otimização do Projeto**

Ao analisar os documentos que você deseja inserir (Manuais, Guias Práticos, Jurisprudência), identifiquei desafios e proponho as seguintes soluções arquitetônicas:

### **Melhoria A: "Chunking" (Fatiamento) Semântico e Estrutural**

**O Problema:** Um RAG normal corta os PDFs a cada 500 palavras. Se ele cortar no meio de uma tabela do Guia Prático da EFD (ex: separando o código RO050010 da sua descrição), a IA nunca conseguirá responder sua pergunta de exemplo.

**A Solução:**

1. Para **Guias e MOCs**: Usar *Markdown parsing*. Converter o PDF para Markdown preservando tabelas, e usar fatiamento por Cabeçalho (Header Splitter). Assim, o "Registro E111" inteiro fica no mesmo bloco de contexto.  
2. Para **Pareceres e Jurisprudência**: Fatiamento semântico ou por parágrafos/artigos.

### **Melhoria B: Busca Híbrida (Hybrid Search)**

**O Problema:** A busca vetorial entende "semântica" (ex: entende que imposto e tributo são parecidos). Mas na área fiscal, códigos exatos importam (ex: "RO150002" ou "Registro C100"). A busca vetorial é ruim para códigos exatos.

**A Solução:** Implementar *Busca Híbrida*. O banco de dados (como Qdrant) fará duas buscas simultâneas: uma por palavras-chave exatas (BM25) para achar os códigos, e outra por similaridade de sentido. O resultado é combinado antes de ir para a IA.

### **Melhoria C: Roteamento de Perguntas (Query Routing)**

Criar um roteador IA antes da busca. Quando o usuário digita: *"Qual o entendimento do TATE sobre responsável solidário?"*

A IA roteadora percebe a palavra "TATE" e aplica automaticamente o filtro de metadados Origem \== TATE, garantindo que a resposta venha do arquivo Enunciado\_TATE\_007... e não do Guia Prático.

## **4\. Engenharia de Prompt para Respostas Didáticas e Detalhadas**

Para obter o nível de detalhe exigido no seu exemplo (tópicos, negritos, passos, referências a manuais), o *System Prompt* (a instrução raiz que a IA recebe em background) deve ser rigoroso.

**Exemplo de System Prompt Otimizado:**

"Você é um Auditor Fiscal Especialista e Consultor Tributário Sênior do Estado de Rondônia (RO).

Sua função é responder a dúvidas fiscais, tributárias e de escrituração com base EXCLUSIVAMENTE nos documentos de contexto fornecidos.

**Regras de Formatação Obrigatórias:**

1. **Didática:** Explique o conceito de forma clara antes de ir para as regras técnicas.  
2. **Estrutura:** Use títulos (\#\#), bullet points e negritos para facilitar a leitura.  
3. **Fundamentação:** Sempre cite a origem da informação (ex: 'Conforme o Guia Prático da EFD versão 3.1.9...', 'Segundo o Parecer 443/2020...').  
4. **Passo a Passo:** Se a pergunta envolver escrituração (EFD, MOC), descreva os blocos e registros em sequência lógica (ex: 1\. Registro E111, 2\. Registro E110).  
5. **Tabelas:** Se houver códigos específicos (como códigos de ajuste RO), apresente-os em formato de tabela para facilitar a visualização do usuário.  
6. **Ausência de Dados:** Se a resposta não estiver no contexto fornecido, diga 'Não possuo informações nos documentos consultados para responder a esta pergunta', JAMAIS invente regras ou códigos."

## **5\. Cronograma de Implementação (Passo a Passo Técnico)**

### **Fase 1: Configuração do Ambiente Local (Dias 1-2)**

* Instalar Python 3.10+.  
* Instalar Ollama e baixar o modelo llama3:8b-instruct-q4\_K\_M (ou gemma2:9b).  
* Instalar bibliotecas: langchain, llama-index, qdrant-client, pymupdf, sentence-transformers.

### **Fase 2: Pipeline de Ingestão de Dados (Dias 3-7) \- *A fase mais importante***

* Criar script de leitura dos PDFs.  
* Implementar extração especial para PDFs estruturados (Guia EFD, MOC).  
* Aplicar os Metadados:  
  * *Difal\_STF\_Lei\_Kandir.pdf* \-\> Origem: STF, Tipo: Jurisprudencia, Tema: DIFAL.  
  * *Guia Prático EFD.pdf* \-\> Origem: RFB/SEFIN, Tipo: Manual\_Escrituracao.  
  * *PARECER 443-2020 CIMENTO...* \-\> Origem: SEFIN-RO, Tipo: Parecer, Tema: Substituicao\_Tributaria.  
* Gerar os Embeddings e salvar no banco local (Qdrant).

### **Fase 3: Construção do RAG e Busca Híbrida (Dias 8-10)**

* Criar a interface de busca.  
* Implementar a integração com o Qdrant permitindo filtros de metadados via interface (ex: Checkboxes na tela para o usuário escolher "Buscar apenas em Jurisprudência").

### **Fase 4: Refinamento e Interface (Dias 11-14)**

* Integrar o modelo do Ollama no LangChain/LlamaIndex.  
* Aplicar o *System Prompt* desenhado acima.  
* Criar uma interface visual simples com Streamlit (Python) para você poder digitar as perguntas em formato de chat e visualizar as respostas renderizadas em Markdown.

## **Conclusão**

Com a sua RTX 3060, este projeto é 100% viável e não requer custos com nuvem (OpenAI/Google). O "segredo" do sucesso não estará no modelo de linguagem em si, mas em como você fará o *parsing* (leitura inteligente) das tabelas do Guia Prático e como você estruturará os metadados dos Pareceres para que o sistema saiba diferenciar uma regra de escrituração de uma decisão judicial.