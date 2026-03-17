# SISTEMA RAG NORMATIVO FISCAL – PLANO MESTRE DE IMPLEMENTAÇÃO

## OBJETIVO DO PROJETO

Construir um sistema RAG jurídico-fiscal local capaz de:

* Realizar crawling automático de normas (ex.: SEFIN-RO)
* Versionar normas por vigência
* Permitir consulta por período histórico
* Gerar respostas fundamentadas com citação de artigos
* Incorporar feedback supervisionado
* Operar 100% local (Ollama + Python)

---

# PROMPT-MESTRE PARA IA NO VS CODE

Copie e utilize o texto abaixo como prompt inicial para a IA integrada ao VS Code.

---

Você é um engenheiro sênior especializado em:

* Python backend
* Processamento de documentos jurídicos
* Sistemas RAG com FAISS
* Embeddings locais
* Arquitetura modular escalável

Sua missão é construir um sistema RAG normativo fiscal completo, modular e pronto para ambiente institucional.

Requisitos obrigatórios:

1. Código modular e organizado por diretórios.
2. Sem dependência de serviços cloud.
3. Utilizar apenas bibliotecas Python estáveis.
4. Gerar documentação inline.
5. Estrutura preparada para expansão futura.

Arquitetura esperada:

crawler/
etl/
rag/
feedback/
dashboard/
documentos/

Nunca gere código monolítico.
Sempre entregue arquivos separados quando solicitado.
Sempre explique decisões arquitetônicas.
Nunca use dependências desnecessárias.

O sistema deve permitir:

* Atualização automática de normas
* Indexação incremental
* Consulta por data de vigência
* Comparação artigo a artigo
* Registro de avaliação das respostas

Sempre priorize robustez institucional.

---

# PLANO DETALHADO DE IMPLEMENTAÇÃO

## FASE 1 – CRAWLER NORMATIVO

Objetivo: baixar todas as normas disponíveis e evitar duplicidade.

### Tarefas:

* Mapear filtros dinâmicos da página
* Enumerar combinações de ano e categoria
* Extrair links PDF
* Calcular hash SHA256
* Salvar apenas arquivos novos
* Registrar metadados em JSON

Entrega esperada:

* crawler/legislacao.py
* crawler/hash_registry.json

---

## FASE 2 – EXTRAÇÃO E NORMALIZAÇÃO

Objetivo: converter PDF em texto limpo estruturado.

### Tarefas:

* Extrair texto com pdfplumber
* Remover cabeçalhos e rodapés
* Identificar tipo, número, data e ementa
* Gerar JSON estruturado

Formato esperado:
{
"tipo": "",
"numero": "",
"data_publicacao": "",
"ementa": "",
"texto": "",
"hash_pdf": ""
}

Entrega esperada:

* etl/pdf_to_text.py
* etl/normalizador.py

---

## FASE 3 – LINHA DO TEMPO NORMATIVA

Objetivo: organizar normas por vigência.

### Tarefas:

* Detectar vigência inicial
* Detectar revogações
* Criar estrutura temporal indexável
* Permitir consulta por data

Entrega esperada:

* etl/timeline.py

---

## FASE 4 – RAG LOCAL

Objetivo: indexar normas e responder consultas fundamentadas.

### Modelo sugerido:

* llama3:8b-instruct-q4
* mistral:7b-instruct-q4

### Embeddings:

* bge-m3
* nomic-embed-text

### Tarefas:

* Criar chunking jurídico
* Gerar embeddings
* Indexar no FAISS
* Implementar retriever com filtro temporal
* Criar prompt estruturado com citação obrigatória

Entrega esperada:

* rag/embeddings.py
* rag/index.py
* rag/retriever.py
* rag/prompt_engine.py

---

## FASE 5 – FEEDBACK SUPERVISIONADO

Objetivo: melhorar relevância com avaliação do usuário.

### Tarefas:

* Registrar pergunta/resposta/nota
* Ajustar pesos de relevância
* Permitir reindexação incremental

Entrega esperada:

* feedback/avaliacao_respostas.jsonl
* feedback/retrain.py

---

## FASE 6 – DASHBOARD

Objetivo: monitorar desempenho do sistema.

### Funcionalidades:

* Perguntas recentes
* Avaliação média
* Normas mais citadas
* Alertas de baixa precisão

Tecnologia sugerida:

* Streamlit

Entrega esperada:

* dashboard/app.py

---

# BOAS PRÁTICAS INSTITUCIONAIS

* Nunca sobrescrever textos antigos
* Manter versionamento completo
* Registrar hash de todos os documentos
* Garantir reprodutibilidade
* Evitar inferência sem base normativa

---

# RESULTADO FINAL ESPERADO

Sistema capaz de:

* Atualizar legislação automaticamente
* Responder consultas fiscais fundamentadas
* Considerar período histórico da consulta
* Comparar versões normativas
* Aprender com feedback supervisionado

---

Se desejar, posso gerar agora:

* Estrutura inicial de código-base
* Modelo de banco SQLite para metadados
* Arquitetura de versionamento consolidado
* Estratégia de testes automatizados

Escolha o próximo passo e avançamos.

---

# ESTRUTURA BASE DO REPOSITÓRIO (CÓDIGO INICIAL)

Abaixo está a estrutura inicial com arquivos base e docstrings institucionais.

```
rag-normativo/
│
├── crawler/
│   ├── __init__.py
│   └── legislacao.py
│
├── etl/
│   ├── __init__.py
│   ├── pdf_to_text.py
│   ├── normalizador.py
│   └── timeline.py
│
├── rag/
│   ├── __init__.py
│   ├── embeddings.py
│   ├── index.py
│   ├── retriever.py
│   └── prompt_engine.py
│
├── feedback/
│   ├── __init__.py
│   └── retrain.py
│
├── dashboard/
│   ├── __init__.py
│   └── app.py
│
├── documentos/
│   ├── pdf/
│   ├── texto/
│   └── metadados.json
│
├── database/
│   └── metadata.db
│
├── tests/
│   └── test_pipeline.py
│
├── config.py
├── main.py
└── requirements.txt
```

---

# ARQUIVOS INICIAIS (ESQUELETO)

## config.py

```python
"""
Configurações globais do sistema RAG Normativo.
Centraliza caminhos, modelos e parâmetros institucionais.
"""

from pathlib import Path

BASE_DIR = Path(__file__).parent

PDF_DIR = BASE_DIR / "documentos" / "pdf"
TEXT_DIR = BASE_DIR / "documentos" / "texto"

EMBEDDING_MODEL = "bge-m3"
LLM_MODEL = "llama3:8b-instruct-q4"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
```

---

## crawler/legislacao.py

```python
"""
Módulo responsável pelo crawling de normas.
Realiza coleta incremental e controle por hash.
"""

import hashlib
from pathlib import Path


def calcular_hash(arquivo: Path) -> str:
    """Calcula SHA256 de um arquivo."""
    h = hashlib.sha256()
    with open(arquivo, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def executar_crawler():
    """Executa rotina principal de coleta."""
    pass
```

---

## etl/pdf_to_text.py

```python
"""
Converte PDFs normativos em texto bruto.
"""


def extrair_texto_pdf(caminho_pdf: str) -> str:
    """Extrai texto de um PDF."""
    pass
```

---

## etl/normalizador.py

```python
"""
Normaliza texto jurídico e extrai metadados.
"""


def extrair_metadados(texto: str) -> dict:
    """Identifica tipo, número, data e ementa."""
    pass
```

---

## etl/timeline.py

```python
"""
Organiza normas por vigência e cria linha do tempo normativa.
"""


def consultar_norma_por_data(id_norma: str, data: str):
    """Retorna versão válida em determinada data."""
    pass
```

---

## rag/embeddings.py

```python
"""
Geração de embeddings para documentos jurídicos.
"""


def gerar_embeddings(textos: list):
    """Gera vetores a partir de lista de textos."""
    pass
```

---

## rag/index.py

```python
"""
Indexação vetorial usando FAISS.
"""


def criar_indice(vetores):
    """Cria índice vetorial."""
    pass
```

---

## rag/retriever.py

```python
"""
Recupera trechos normativos com filtro temporal.
"""


def recuperar_contexto(pergunta: str, data_referencia: str):
    """Retorna documentos relevantes."""
    pass
```

---

## rag/prompt_engine.py

```python
"""
Constrói prompts estruturados para respostas fundamentadas.
"""


def montar_prompt(pergunta: str, contexto: str, data: str) -> str:
    """Monta prompt jurídico estruturado."""
    pass
```

---

## feedback/retrain.py

```python
"""
Módulo de aprendizado supervisionado via feedback.
"""


def registrar_feedback(pergunta: str, resposta: str, nota: int):
    """Armazena avaliação do usuário."""
    pass
```

---

## dashboard/app.py

```python
"""
Dashboard institucional para monitoramento do sistema.
"""


def iniciar_dashboard():
    """Inicializa aplicação Streamlit."""
    pass
```

---

## main.py

```python
"""
Ponto de entrada do sistema.
"""


def main():
    """Executa pipeline completo ou modo interativo."""
    pass


if __name__ == "__main__":
    main()
```

---

# MODELO SQLITE – VERSIONAMENTO NORMATIVO CONSOLIDADO

## OBJETIVO

Garantir:

* Histórico completo das normas
* Controle de vigência temporal
* Versionamento por alteração
* Rastreabilidade por hash
* Consulta por data válida

---

# PRINCÍPIOS DE MODELAGEM

1. Nunca sobrescrever texto antigo.
2. Cada alteração gera nova versão.
3. Vigência é tratada como intervalo fechado-aberto.
4. Revogação encerra vigência anterior.
5. Todo documento possui hash imutável.

---

# ESTRUTURA DE TABELAS

## 1️⃣ TABELA: normas

Representa a identidade lógica da norma.

```sql
CREATE TABLE normas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    numero TEXT NOT NULL,
    ano INTEGER NOT NULL,
    orgao TEXT,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tipo, numero, ano)
);
```

---

## 2️⃣ TABELA: versoes_norma

Cada alteração gera um novo registro.

```sql
CREATE TABLE versoes_norma (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    norma_id INTEGER NOT NULL,
    texto_integral TEXT NOT NULL,
    hash_texto TEXT NOT NULL,
    vigencia_inicio DATE NOT NULL,
    vigencia_fim DATE,
    ato_alterador TEXT,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (norma_id) REFERENCES normas(id)
);
```

Regra:

* vigencia_fim NULL = versão vigente atual

---

## 3️⃣ TABELA: dispositivos

Permite comparação artigo a artigo.

```sql
CREATE TABLE dispositivos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    versao_id INTEGER NOT NULL,
    identificador TEXT NOT NULL,  -- Ex: Art. 53, §1º, Inciso II
    texto TEXT NOT NULL,
    hash_dispositivo TEXT NOT NULL,
    FOREIGN KEY (versao_id) REFERENCES versoes_norma(id)
);
```

---

## 4️⃣ TABELA: relacoes_normativas

Controla revogações e alterações.

```sql
CREATE TABLE relacoes_normativas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    norma_origem_id INTEGER NOT NULL,
    norma_destino_id INTEGER NOT NULL,
    tipo_relacao TEXT NOT NULL, -- ALTERA, REVOGA, REGULAMENTA
    FOREIGN KEY (norma_origem_id) REFERENCES normas(id),
    FOREIGN KEY (norma_destino_id) REFERENCES normas(id)
);
```

---

## 5️⃣ TABELA: embeddings

Permite reindexação incremental.

```sql
CREATE TABLE embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dispositivo_id INTEGER NOT NULL,
    vetor BLOB NOT NULL,
    modelo TEXT NOT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dispositivo_id) REFERENCES dispositivos(id)
);
```

---

## 6️⃣ TABELA: feedback_respostas

Aprendizado supervisionado.

```sql
CREATE TABLE feedback_respostas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pergunta TEXT NOT NULL,
    resposta TEXT NOT NULL,
    nota INTEGER CHECK(nota BETWEEN 1 AND 5),
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

# ÍNDICES IMPORTANTES

```sql
CREATE INDEX idx_normas_identidade
ON normas(tipo, numero, ano);

CREATE INDEX idx_versoes_vigencia
ON versoes_norma(norma_id, vigencia_inicio, vigencia_fim);

CREATE INDEX idx_dispositivos_identificador
ON dispositivos(identificador);
```

---

# CONSULTA TEMPORAL PADRÃO

Buscar versão válida em determinada data:

```sql
SELECT * FROM versoes_norma
WHERE norma_id = ?
AND vigencia_inicio <= ?
AND (vigencia_fim IS NULL OR vigencia_fim > ?);
```

---

# LÓGICA DE VERSIONAMENTO (PROCESSO DE ALTERAÇÃO)

1. Nova norma alteradora é detectada.
2. Localiza versão vigente anterior.
3. Define vigencia_fim da versão anterior.
4. Insere nova versão com vigencia_inicio.
5. Registra relação em relacoes_normativas.
6. Recalcula dispositivos e embeddings.

---

# VANTAGENS DO MODELO

* Histórico completo auditável
* Comparação artigo a artigo
* Consulta temporal precisa
* Suporte a aprendizado supervisionado
* Reindexação incremental controlada

---

# PIPELINE AUTOMÁTICO DE VERSIONAMENTO NORMATIVO

## OBJETIVO

Automatizar o processo de:

* Detectar norma nova ou alteradora
* Encerrar vigência anterior
* Criar nova versão consolidada
* Atualizar dispositivos
* Reindexar embeddings incrementalmente

Esse pipeline deve ser executado sempre que:

* Novo PDF for baixado
* Texto for reprocessado
* Norma alteradora for identificada

---

# FLUXO GERAL DO PIPELINE

```
1. Novo PDF detectado
2. Extrair texto
3. Extrair metadados
4. Identificar norma base
5. Verificar se já existe no banco
6. Detectar se é alteração ou norma inédita
7. Encerrar vigência anterior (se aplicável)
8. Inserir nova versão
9. Reconstruir dispositivos
10. Atualizar embeddings
```

---

# ETAPA 1 – IDENTIFICAR NORMA

Regra:

* Se (tipo, número, ano) não existir → inserir em `normas`
* Se existir → tratar como possível nova versão

Consulta:

```sql
SELECT id FROM normas
WHERE tipo = ? AND numero = ? AND ano = ?;
```

---

# ETAPA 2 – VERIFICAR ALTERAÇÃO

Critério:

* Comparar hash do texto integral
* Se hash diferente → nova versão
* Se hash igual → ignorar

---

# ETAPA 3 – ENCERRAR VIGÊNCIA ANTERIOR

```sql
UPDATE versoes_norma
SET vigencia_fim = ?
WHERE norma_id = ?
AND vigencia_fim IS NULL;
```

A data usada deve ser:

* Data de vigência da nova versão

---

# ETAPA 4 – INSERIR NOVA VERSÃO

```sql
INSERT INTO versoes_norma (
    norma_id,
    texto_integral,
    hash_texto,
    vigencia_inicio,
    ato_alterador
) VALUES (?, ?, ?, ?, ?);
```

---

# ETAPA 5 – RECONSTRUIR DISPOSITIVOS

Processo:

1. Quebrar texto por padrões jurídicos:

   * Art.\n   - §\n   - Inciso\n
2. Inserir cada dispositivo com hash próprio.

Isso permite:

* Comparação artigo a artigo
* Reindexação parcial

---

# ETAPA 6 – REINDEXAÇÃO INCREMENTAL

Regra estratégica:

* Apenas dispositivos com hash novo geram novo embedding
* Embeddings antigos são preservados

Fluxo:

```
Para cada dispositivo novo:
    gerar embedding
    salvar em tabela embeddings
```

---

# SCRIPT CENTRAL DO PIPELINE

Arquivo sugerido:

```
etl/versionamento_pipeline.py
```

Função principal:

```python

def processar_norma(caminho_pdf: str):
    """
    Executa pipeline completo de versionamento normativo.
    """
    pass
```

---

# REGRAS DE SEGURANÇA INSTITUCIONAL

* Nunca deletar versão antiga
* Nunca atualizar texto antigo
* Sempre registrar hash
* Todas operações devem estar dentro de transação SQLite
* Em caso de erro → rollback automático

---

# VALIDAÇÕES AUTOMÁTICAS

O pipeline deve verificar:

* Não pode existir duas versões com vigencia_fim NULL
* vigencia_inicio da nova versão deve ser posterior à anterior
* hash_texto não pode ser duplicado para mesma norma

---

# RESULTADO FINAL

Ao final do processo, o sistema terá:

* Histórico completo da norma
* Linha do tempo consistente
* Dispositivos organizados
* Embeddings atualizados
* Sistema pronto para consulta temporal

---

# IMPLEMENTAÇÃO REAL – versionamento_pipeline.py

## OBJETIVO

Implementar o pipeline automático completo de versionamento normativo com:

* Controle transacional
* Detecção de nova versão por hash
* Encerramento correto de vigência
* Reconstrução de dispositivos
* Reindexação incremental

Este documento contém o código base funcional.

---

# ARQUIVO: etl/versionamento_pipeline.py

```python
"""
Pipeline automático de versionamento normativo.
Responsável por manter integridade histórica e consistência temporal.
"""

import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path

from etl.pdf_to_text import extrair_texto_pdf
from etl.normalizador import extrair_metadados
from rag.embeddings import gerar_embeddings

DB_PATH = "database/metadata.db"


# -------------------------------------------------
# UTILITÁRIOS
# -------------------------------------------------


def calcular_hash_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# -------------------------------------------------
# FUNÇÃO PRINCIPAL
# -------------------------------------------------


def processar_norma(caminho_pdf: str):
    """
    Executa pipeline completo:
    - Extrai texto
    - Identifica norma
    - Versiona corretamente
    - Atualiza dispositivos
    - Reindexa embeddings
    """

    conn = conectar()
    cursor = conn.cursor()

    try:
        conn.execute("BEGIN TRANSACTION;")

        # 1️⃣ Extrair texto
        texto = extrair_texto_pdf(caminho_pdf)
        metadados = extrair_metadados(texto)

        tipo = metadados["tipo"]
        numero = metadados["numero"]
        ano = int(metadados["data_publicacao"][:4])
        vigencia_inicio = metadados.get("vigencia_inicio") or metadados["data_publicacao"]

        hash_texto = calcular_hash_texto(texto)

        # 2️⃣ Verificar ou inserir norma
        cursor.execute(
            "SELECT id FROM normas WHERE tipo=? AND numero=? AND ano=?",
            (tipo, numero, ano),
        )
        resultado = cursor.fetchone()

        if resultado:
            norma_id = resultado[0]
        else:
            cursor.execute(
                "INSERT INTO normas (tipo, numero, ano) VALUES (?, ?, ?)",
                (tipo, numero, ano),
            )
            norma_id = cursor.lastrowid

        # 3️⃣ Verificar versão existente
        cursor.execute(
            """
            SELECT id, hash_texto
            FROM versoes_norma
            WHERE norma_id=? AND vigencia_fim IS NULL
            """,
            (norma_id,),
        )
        versao_atual = cursor.fetchone()

        if versao_atual and versao_atual[1] == hash_texto:
            print("Nenhuma alteração detectada.")
            conn.rollback()
            return

        # 4️⃣ Encerrar vigência anterior
        if versao_atual:
            cursor.execute(
                """
                UPDATE versoes_norma
                SET vigencia_fim=?
                WHERE id=?
                """,
                (vigencia_inicio, versao_atual[0]),
            )

        # 5️⃣ Inserir nova versão
        cursor.execute(
            """
            INSERT INTO versoes_norma (
                norma_id,
                texto_integral,
                hash_texto,
                vigencia_inicio
            ) VALUES (?, ?, ?, ?)
            """,
            (norma_id, texto, hash_texto, vigencia_inicio),
        )

        nova_versao_id = cursor.lastrowid

        # 6️⃣ Reconstruir dispositivos
        dispositivos = quebrar_dispositivos(texto)

        for identificador, conteudo in dispositivos:
            hash_disp = calcular_hash_texto(conteudo)
            cursor.execute(
                """
                INSERT INTO dispositivos (
                    versao_id,
                    identificador,
                    texto,
                    hash_dispositivo
                ) VALUES (?, ?, ?, ?)
                """,
                (nova_versao_id, identificador, conteudo, hash_disp),
            )

        # 7️⃣ Gerar embeddings apenas para novos dispositivos
        cursor.execute(
            "SELECT id, texto FROM dispositivos WHERE versao_id=?",
            (nova_versao_id,),
        )
        novos_dispositivos = cursor.fetchall()

        textos = [d[1] for d in novos_dispositivos]
        vetores = gerar_embeddings(textos)

        for (disp_id, _), vetor in zip(novos_dispositivos, vetores):
            cursor.execute(
                """
                INSERT INTO embeddings (dispositivo_id, vetor, modelo)
                VALUES (?, ?, ?)
                """,
                (disp_id, vetor.tobytes(), "bge-m3"),
            )

        conn.commit()
        print("Versionamento concluído com sucesso.")

    except Exception as e:
        conn.rollback()
        print("Erro no pipeline:", e)
        raise

    finally:
        conn.close()


# -------------------------------------------------
# QUEBRA DE DISPOSITIVOS
# -------------------------------------------------


def quebrar_dispositivos(texto: str):
    """
    Divide texto em dispositivos jurídicos básicos.
    Estratégia simples baseada em 'Art.'
    Pode evoluir para parser mais sofisticado.
    """
    partes = texto.split("Art.")
    dispositivos = []

    for parte in partes[1:]:
        identificador = "Art. " + parte.split("\n")[0].strip()
        conteudo = "Art." + parte
        dispositivos.append((identificador, conteudo.strip()))

    return dispositivos
```

---

# CARACTERÍSTICAS IMPORTANTES

* Transação completa com rollback automático
* Nunca sobrescreve versões antigas
* Atualização incremental
* Hash garante integridade
* Pronto para evolução com parser mais sofisticado

---

# COMPARADOR ARTIGO-A-ARTIGO COM HASH ESTRUTURAL

## OBJETIVO

Detectar exatamente quais dispositivos:

* Permaneceram iguais
* Foram alterados
* Foram revogados
* Foram incluídos

Sem depender apenas do hash global da norma.

Isso permite versionamento inteligente e reuso de embeddings.

---

# IMPLEMENTAÇÃO

Adicionar ao arquivo:

```python
# -------------------------------------------------
# COMPARADOR ESTRUTURAL
# -------------------------------------------------


def mapear_dispositivos_por_identificador(dispositivos):
    """
    Converte lista [(id, texto)] em dict estruturado
    { identificador: {texto, hash} }
    """
    estrutura = {}

    for identificador, texto in dispositivos:
        estrutura[identificador] = {
            "texto": texto,
            "hash": calcular_hash_texto(texto),
        }

    return estrutura


def comparar_estruturalmente(dispositivos_antigos, dispositivos_novos):
    """
    Compara versões artigo a artigo.

    Retorna dict com:
    - mantidos
    - alterados
    - revogados
    - incluidos
    """

    antigos = mapear_dispositivos_por_identificador(dispositivos_antigos)
    novos = mapear_dispositivos_por_identificador(dispositivos_novos)

    mantidos = []
    alterados = []
    revogados = []
    incluidos = []

    # Verificar antigos
    for ident, dados_antigos in antigos.items():
        if ident not in novos:
            revogados.append(ident)
        else:
            if dados_antigos["hash"] == novos[ident]["hash"]:
                mantidos.append(ident)
            else:
                alterados.append(ident)

    # Verificar novos
    for ident in novos.keys():
        if ident not in antigos:
            incluidos.append(ident)

    return {
        "mantidos": mantidos,
        "alterados": alterados,
        "revogados": revogados,
        "incluidos": incluidos,
    }
```

---

# COMO INTEGRAR NO PIPELINE

Antes de inserir nova versão:

1. Buscar dispositivos da versão vigente
2. Gerar nova estrutura com parser
3. Executar comparar_estruturalmente
4. Reaproveitar embeddings dos "mantidos"
5. Gerar embeddings apenas para "alterados" e "incluidos"

---

# GANHO ARQUITETURAL

Com esse comparador:

* Evita reindexação desnecessária
* Permite histórico granular
* Abre caminho para diff explicável
* Possibilita auditoria jurídica automatizada

---

# PERSISTÊNCIA DO HISTÓRICO DE ALTERAÇÕES (DIFF ESTRUTURAL)

## OBJETIVO

Registrar no banco cada alteração estrutural entre versões:

* Inclusão de dispositivo
* Alteração de dispositivo
* Revogação de dispositivo
* Manutenção (opcional para auditoria)

Isso cria trilha histórica auditável.

---

# MODELAGEM DA TABELA

Adicionar ao schema SQLite:

```sql
CREATE TABLE diff_estrutural (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    versao_origem_id INTEGER,
    versao_destino_id INTEGER NOT NULL,
    identificador TEXT NOT NULL,
    tipo_alteracao TEXT NOT NULL, -- 'mantido', 'alterado', 'revogado', 'incluido'
    hash_anterior TEXT,
    hash_novo TEXT,
    data_registro TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (versao_origem_id) REFERENCES versoes_norma(id),
    FOREIGN KEY (versao_destino_id) REFERENCES versoes_norma(id)
);

CREATE INDEX idx_diff_versao_destino
ON diff_estrutural (versao_destino_id);
```

---

# INTEGRAÇÃO NO PIPELINE

Após executar `comparar_estruturalmente`, persistir o resultado:

```python

def persistir_diff(
    cursor,
    versao_origem_id,
    versao_destino_id,
    dispositivos_antigos,
    dispositivos_novos,
    resultado_diff,
):

    antigos_map = mapear_dispositivos_por_identificador(dispositivos_antigos)
    novos_map = mapear_dispositivos_por_identificador(dispositivos_novos)

    # Mantidos
    for ident in resultado_diff["mantidos"]:
        cursor.execute(
            """
            INSERT INTO diff_estrutural (
                versao_origem_id,
                versao_destino_id,
                identificador,
                tipo_alteracao,
                hash_anterior,
                hash_novo
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                versao_origem_id,
                versao_destino_id,
                ident,
                "mantido",
                antigos_map[ident]["hash"],
                novos_map[ident]["hash"],
            ),
        )

    # Alterados
    for ident in resultado_diff["alterados"]:
        cursor.execute(
            """
            INSERT INTO diff_estrutural (
                versao_origem_id,
                versao_destino_id,
                identificador,
                tipo_alteracao,
                hash_anterior,
                hash_novo
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                versao_origem_id,
                versao_destino_id,
                ident,
                "alterado",
                antigos_map[ident]["hash"],
                novos_map[ident]["hash"],
            ),
        )

    # Revogados
    for ident in resultado_diff["revogados"]:
        cursor.execute(
            """
            INSERT INTO diff_estrutural (
                versao_origem_id,
                versao_destino_id,
                identificador,
                tipo_alteracao,
                hash_anterior,
                hash_novo
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                versao_origem_id,
                versao_destino_id,
                ident,
                "revogado",
                antigos_map[ident]["hash"],
                None,
            ),
        )

    # Incluídos
    for ident in resultado_diff["incluidos"]:
        cursor.execute(
            """
            INSERT INTO diff_estrutural (
                versao_origem_id,
                versao_destino_id,
                identificador,
                tipo_alteracao,
                hash_anterior,
                hash_novo
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                versao_origem_id,
                versao_destino_id,
                ident,
                "incluido",
                None,
                novos_map[ident]["hash"],
            ),
        )
```

---

# ONDE CHAMAR

Dentro de `processar_norma`, após inserir `nova_versao_id` e antes de commit:

1. Buscar dispositivos da versão anterior
2. Gerar dispositivos novos com parser
3. Rodar `comparar_estruturalmente`
4. Chamar `persistir_diff(...)`

---

# RESULTADO ARQUITETURAL

Agora o sistema passa a ter:

* Histórico completo de mutações normativas
* Base para explicar "o que mudou" entre datas
* Base para linha do tempo jurídica
* Base para auditoria automatizada

---

# PRÓXIMO NÍVEL

Se você quer transformar isso em sistema realmente avançado:

1. Armazenar também diff textual (ex: unified diff)
2. Criar API que retorne explicação automática das mudanças
3. Implementar reconstrução automática do texto consolidado por data
4. Implementar versionamento semântico (tipo MAJOR/MINOR jurídico)

Qual desses você quer elevar agora?

