"""
Configurações globais do sistema RAG Normativo.
Centraliza caminhos, modelos e parâmetros institucionais.
"""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from pathlib import Path

BASE_DIR = Path(__file__).parent

PDF_DIR = BASE_DIR / "documentos" / "pdf"
TEXT_DIR = BASE_DIR / "documentos" / "texto"
DB_PATH = BASE_DIR / "database" / "metadata.db"

# Base legislativa externa (OneDrive SEFIN)
LEGISLACAO_SEFIN_DIR = Path(r"C:\Users\eniot\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Legislacao_SEFIN")

EMBEDDING_MODEL = "BAAI/bge-m3"
LLM_MODEL = "qwen2.5:14b-instruct-q4_K_M"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
