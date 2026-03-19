"""
Configurações globais do sistema RAG Normativo.
Centraliza caminhos, modelos e parâmetros institucionais, suportando
diferentes perfis de ambiente (dev, local_gpu, server).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
load_dotenv()

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

# --- Perfis de Ambiente ---
# Opções: "dev", "local_gpu", "server"
ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev").lower()

# --- Definição de Caminhos Base ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Validar/criar caminhos principais
PDF_DIR = Path(os.environ.get("PDF_DIR", str(BASE_DIR / "documentos" / "pdf")))
TEXT_DIR = Path(os.environ.get("TEXT_DIR", str(BASE_DIR / "documentos" / "texto")))
DB_PATH = Path(os.environ.get("DB_PATH", str(BASE_DIR / "database" / "metadata.db")))

# Caminho do OneDrive não é mais hardcoded. Deve vir do .env
# Exemplo no .env: LEGISLACAO_SEFIN_DIR="C:\\Users\\...\\Legislacao_SEFIN"
_leg_sefin_env = os.environ.get("LEGISLACAO_SEFIN_DIR")
if _leg_sefin_env:
    LEGISLACAO_SEFIN_DIR = Path(_leg_sefin_env)
else:
    # Fallback seguro para evitar quebras se a variável não estiver definida
    LEGISLACAO_SEFIN_DIR = BASE_DIR / "documentos" / "legislacao_sefin_mock"


def validate_paths():
    """Garante que os diretórios necessários existam (ou tenta criá-los)."""
    for directory in [PDF_DIR, TEXT_DIR, DB_PATH.parent]:
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Aviso: Não foi possível criar/validar diretório {directory}: {e}")


# Executar validação de paths na importação
validate_paths()

# --- Modelos de Embeddings e LLM ---
if ENVIRONMENT == "local_gpu":
    EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-m3")
    LLM_MODEL = os.environ.get("LLM_MODEL", "qwen2.5:14b-instruct-q4_K_M")
elif ENVIRONMENT == "server":
    # Modelos potencialmente diferentes para servidor de produção
    EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-m3")
    LLM_MODEL = os.environ.get("LLM_MODEL", "qwen2.5:14b-instruct-q4_K_M")
else: # dev (default)
    # Modelos mais leves para desenvolvimento rápido
    EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-m3") # Mantém bge-m3, mas pode mudar
    LLM_MODEL = os.environ.get("LLM_MODEL", "qwen2.5:14b-instruct-q4_K_M")

# --- Parâmetros de Chunking ---
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", 800))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", 100))
