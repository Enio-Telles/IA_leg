"""
Ponto de entrada do sistema IA_leg (Revisor Fiscal Inteligente).
Fornece comandos independentes para reduzir o acoplamento.

Uso:
  python -m ia_leg setup
  python -m ia_leg ingest
  python -m ia_leg index
  python -m ia_leg serve
  python -m ia_leg validate
"""

import sys
import subprocess
import argparse
import shutil
import sqlite3
import urllib.request
import shlex
from pathlib import Path

# Adiciona o diretório base ao sys.path para garantir que os módulos internos sejam encontrados
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ia_leg.core.config.settings import DB_PATH, BASE_DIR

# ─────────────────────────────────────────────────────────
# UTILITÁRIOS E CORES
# ─────────────────────────────────────────────────────────

class Cor:
    VERDE = "\033[92m"
    AMARELO = "\033[93m"
    VERMELHO = "\033[91m"
    AZUL = "\033[94m"
    CIANO = "\033[96m"
    BOLD = "\033[1m"
    FIM = "\033[0m"

def banner():
    print(f"""
{Cor.CIANO}{Cor.BOLD}
╔══════════════════════════════════════════════════════════╗
║       ⚖️  REVISOR FISCAL INTELIGENTE — IA_leg           ║
║       Secretaria de Estado de Finanças de Rondônia      ║
╚══════════════════════════════════════════════════════════╝
{Cor.FIM}""")

def log(msg, tipo="info"):
    icones = {
        "info": f"{Cor.AZUL}ℹ️ ",
        "ok": f"{Cor.VERDE}✅",
        "warn": f"{Cor.AMARELO}⚠️ ",
        "erro": f"{Cor.VERMELHO}❌",
        "etapa": f"{Cor.CIANO}{Cor.BOLD}▶ ",
    }
    print(f"  {icones.get(tipo, '')} {msg}{Cor.FIM}")

def executar(cmd, cwd=None, shell=False, check=True, capturar=False):
    """Executa um comando de forma segura."""
    if not shell and isinstance(cmd, str):
        cmd = shlex.split(cmd)

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or str(BASE_DIR),
            shell=shell,
            check=check,
            capture_output=capturar,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return result
    except subprocess.CalledProcessError as e:
        log(f"Comando falhou: {cmd}", "erro")
        if capturar and e.stderr:
            log(f"  Detalhe: {e.stderr[:200]}", "erro")
        return None

# ─────────────────────────────────────────────────────────
# COMANDOS
# ─────────────────────────────────────────────────────────

def command_setup():
    """Setup de banco de dados e verificações básicas."""
    log("ETAPA — Configurando banco de dados SQLite", "etapa")

    schema_path = BASE_DIR / "database" / "schema.sql"

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        n_tabelas = cur.fetchone()[0]
        conn.close()

        if n_tabelas >= 5:
            log(f"Banco já existe em {DB_PATH} com {n_tabelas} tabelas. Pulando criação.", "ok")
            return

    if not schema_path.exists():
        log(f"Schema não encontrado em {schema_path}", "erro")
        sys.exit(1)

    log("Criando tabelas a partir do schema.sql...", "info")
    conn = sqlite3.connect(str(DB_PATH))
    with open(str(schema_path), "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.close()

    log("Banco de dados criado com sucesso!", "ok")

def command_ingest():
    """Ingere documentos na base RAG."""
    log("ETAPA — Ingestão de documentos na base RAG", "etapa")

    # 4a. Pipeline de versionamento
    texto_dir = BASE_DIR / "documentos" / "texto"
    if texto_dir.exists() and any(texto_dir.glob("*.json")):
        log("Processando documentos JSON (versionamento)...", "info")
        executar(["python", "-c", "from etl.versionamento_pipeline import processar_tudo; processar_tudo()"])
        log("Documentos JSON processados!", "ok")
    else:
        log("Nenhum JSON encontrado em documentos/texto/. Pulando.", "warn")

    # 4b. PDFs
    pdf_dir = BASE_DIR / "documentos" / "pdf"
    if pdf_dir.exists() and any(pdf_dir.rglob("*.pdf")):
        log("Ingerindo PDFs locais (documentos/pdf/)...", "info")
        executar(["python", "scripts/ingerir_pdfs.py"])
        log("PDFs locais processados!", "ok")
    else:
        log("Nenhum PDF local encontrado. Pulando.", "warn")

    # 4c. HTMLs e Outros (dependem da SEFIN)
    script_sefin_html = BASE_DIR / "scripts" / "ingerir_html_legislacao.py"
    if script_sefin_html.exists():
        log("Ingerindo HTMLs da base Legislacao_atual...", "info")
        executar(["python", "scripts/ingerir_html_legislacao.py"])
        log("HTMLs SEFIN processados!", "ok")

    log("Ingestão finalizada.", "ok")

def command_index():
    """Gera embeddings vetoriais."""
    log("ETAPA — Geração de embeddings vetoriais", "etapa")
    executar(["python", "-m", "ia_leg.rag.embedding_service"])
    log("Embeddings gerados com sucesso!", "ok")

def command_serve():
    """Inicia os serviços (Ollama check e UI)."""
    log("ETAPA — Verificando LLM (Ollama)", "etapa")

    if shutil.which("ollama") is None:
        log("Ollama não encontrado. Instale em: https://ollama.com/download", "warn")
    else:
        try:
            urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
            log("Ollama está rodando", "ok")
        except Exception:
            log("Ollama instalado mas não está em execução", "warn")
            log("  Inicie manualmente com: ollama serve", "info")

    log("ETAPA — Iniciando Dashboard", "etapa")
    log("Abrindo Dashboard Streamlit em http://localhost:8501", "info")
    try:
        executar(["streamlit", "run", "dashboard/app.py"])
    except KeyboardInterrupt:
        print(f"\n{Cor.AMARELO}Sistema encerrado pelo usuário.{Cor.FIM}")

def command_validate():
    """Executa validação (Testes de relevância e pipeline)."""
    log("ETAPA — Validando sistema (Testes)", "etapa")
    executar(["pytest", "tests/"])
    log("Validação finalizada.", "ok")

# ─────────────────────────────────────────────────────────
# ORQUESTRADOR PRINCIPAL
# ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="IA_leg — Inicialização completa do Revisor Fiscal Inteligente"
    )
    parser.add_argument(
        "comando",
        choices=["setup", "ingest", "index", "serve", "validate"],
        help="Comando para executar",
    )

    args = parser.parse_args()
    banner()

    if args.comando == "setup":
        command_setup()
    elif args.comando == "ingest":
        command_ingest()
    elif args.comando == "index":
        command_index()
    elif args.comando == "serve":
        command_serve()
    elif args.comando == "validate":
        command_validate()

if __name__ == "__main__":
    main()
