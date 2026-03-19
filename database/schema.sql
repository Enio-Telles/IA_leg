CREATE TABLE normas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    numero TEXT NOT NULL,
    ano INTEGER NOT NULL,
    orgao TEXT,
    tema TEXT,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tipo, numero, ano)
);
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
CREATE TABLE dispositivos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    versao_id INTEGER NOT NULL,
    identificador TEXT NOT NULL,
    -- Ex: Art. 53, §1º, Inciso II
    texto TEXT NOT NULL,
    hash_dispositivo TEXT NOT NULL,
    FOREIGN KEY (versao_id) REFERENCES versoes_norma(id)
);
CREATE TABLE relacoes_normativas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    norma_origem_id INTEGER NOT NULL,
    norma_destino_id INTEGER NOT NULL,
    tipo_relacao TEXT NOT NULL,
    -- ALTERA, REVOGA, REGULAMENTA
    FOREIGN KEY (norma_origem_id) REFERENCES normas(id),
    FOREIGN KEY (norma_destino_id) REFERENCES normas(id)
);
CREATE TABLE embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dispositivo_id INTEGER NOT NULL,
    vetor BLOB NOT NULL,
    modelo TEXT NOT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dispositivo_id) REFERENCES dispositivos(id)
);
CREATE TABLE feedback_respostas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pergunta TEXT NOT NULL,
    resposta TEXT NOT NULL,
    nota INTEGER CHECK(
        nota BETWEEN 1 AND 5
    ),
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE diff_estrutural (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    versao_origem_id INTEGER,
    versao_destino_id INTEGER NOT NULL,
    identificador TEXT NOT NULL,
    tipo_alteracao TEXT NOT NULL,
    -- 'mantido', 'alterado', 'revogado', 'incluido'
    hash_anterior TEXT,
    hash_novo TEXT,
    data_registro TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (versao_origem_id) REFERENCES versoes_norma(id),
    FOREIGN KEY (versao_destino_id) REFERENCES versoes_norma(id)
);
CREATE INDEX idx_normas_identidade ON normas(tipo, numero, ano);
CREATE INDEX idx_versoes_vigencia ON versoes_norma(norma_id, vigencia_inicio, vigencia_fim);
CREATE INDEX idx_dispositivos_identificador ON dispositivos(identificador);
CREATE INDEX idx_diff_versao_destino ON diff_estrutural (versao_destino_id);
CREATE TABLE query_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pergunta TEXT NOT NULL,
    filtros TEXT,
    embedding_time_ms REAL,
    search_time_ms REAL,
    rerank_time_ms REAL,
    llm_time_ms REAL,
    total_time_ms REAL,
    chunks_used INTEGER,
    backend TEXT,
    model TEXT,
    success BOOLEAN,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
);
