"""
iniciar.py — Bootstrap completo do sistema IA_leg (Revisor Fiscal Inteligente).

Executa todas as etapas necessárias para deixar o sistema pronto para uso:
  1. Cria o ambiente Conda 'leg_ia' (Python 3.11 + GPU)
  2. Instala todas as dependências (PyTorch, sentence-transformers, etc.)
  3. Cria o banco de dados SQLite com o schema completo
  4. Executa a ingestão de documentos (JSON, PDF, HTML)
  5. Gera os embeddings vetoriais (GPU se disponível)
  6. Inicia o dashboard Streamlit

Uso:
  python iniciar.py                  # Executa setup completo + abre dashboard
  python iniciar.py --etapa setup    # Só cria ambiente e instala dependências
  python iniciar.py --etapa ingerir  # Só executa ingestão de documentos
  python iniciar.py --etapa indexar  # Só gera embeddings
  python iniciar.py --etapa ui       # Só abre o dashboard
  python iniciar.py --pular-ingestao # Setup completo, mas pula ingestão (se já feita)
"""

import subprocess
import sys
import os
import sqlite3
import argparse
import shutil
import time
from pathlib import Path

# ─────────────────────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
ENV_NAME = "leg_ia"
PYTHON_VERSION = "3.11"
DB_PATH = BASE_DIR / "database" / "metadata.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"

# Modelo LLM (Ollama)
OLLAMA_MODEL = "qwen2.5:14b-instruct-q4_K_M"

# Cores para terminal
class Cor:
    VERDE  = "\033[92m"
    AMARELO = "\033[93m"
    VERMELHO = "\033[91m"
    AZUL   = "\033[94m"
    CIANO  = "\033[96m"
    BOLD   = "\033[1m"
    FIM    = "\033[0m"

def banner():
    print(f"""
{Cor.CIANO}{Cor.BOLD}
╔══════════════════════════════════════════════════════════╗
║       ⚖️  REVISOR FISCAL INTELIGENTE — IA_leg           ║
║       Secretaria de Estado de Finanças de Rondônia      ║
╚══════════════════════════════════════════════════════════╝
{Cor.FIM}""")

def log(msg, tipo="info"):
    icones = {"info": f"{Cor.AZUL}ℹ️ ", "ok": f"{Cor.VERDE}✅", "warn": f"{Cor.AMARELO}⚠️ ", "erro": f"{Cor.VERMELHO}❌", "etapa": f"{Cor.CIANO}{Cor.BOLD}▶ "}
    print(f"  {icones.get(tipo, '')} {msg}{Cor.FIM}")

def executar(cmd, cwd=None, shell=True, check=True, capturar=False):
    """Executa um comando no shell."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd or str(BASE_DIR), shell=shell, check=check,
            capture_output=capturar, text=True, encoding="utf-8", errors="replace"
        )
        return result
    except subprocess.CalledProcessError as e:
        log(f"Comando falhou: {cmd}", "erro")
        if capturar and e.stderr:
            log(f"  Detalhe: {e.stderr[:200]}", "erro")
        return None

def verificar_conda():
    """Verifica se o Conda está instalado."""
    if shutil.which("conda") is None:
        log("Conda não encontrado. Instale o Miniconda ou Anaconda:", "erro")
        log("  https://docs.conda.io/en/latest/miniconda.html", "info")
        sys.exit(1)
    log("Conda encontrado", "ok")

def verificar_ollama():
    """Verifica se o Ollama está instalado e rodando."""
    if shutil.which("ollama") is None:
        log("Ollama não encontrado. Instale em: https://ollama.com/download", "warn")
        return False
    
    # Verificar se está rodando
    try:
        import urllib.request
        req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        log("Ollama está rodando", "ok")
        return True
    except Exception:
        log("Ollama instalado mas não está em execução", "warn")
        log("  Inicie manualmente com: ollama serve", "info")
        return False

# ─────────────────────────────────────────────────────────
# ETAPA 1: CRIAR AMBIENTE CONDA
# ─────────────────────────────────────────────────────────

def etapa_criar_ambiente():
    log("ETAPA 1 — Criando ambiente Conda", "etapa")
    
    # Verificar se ambiente já existe
    result = executar("conda env list", capturar=True)
    if result and ENV_NAME in result.stdout:
        log(f"Ambiente '{ENV_NAME}' já existe. Pulando criação.", "ok")
        return True
    
    log(f"Criando ambiente '{ENV_NAME}' com Python {PYTHON_VERSION}...", "info")
    
    # Usar environment.yml se existir
    env_yml = BASE_DIR / "environment.yml"
    if env_yml.exists():
        log("Usando environment.yml para criar ambiente...", "info")
        cmd = f"conda env create -f \"{env_yml}\" --name {ENV_NAME}"
    else:
        cmd = f"conda create -n {ENV_NAME} python={PYTHON_VERSION} -y"
    
    result = executar(cmd)
    if result is None:
        log("Falha ao criar ambiente Conda", "erro")
        return False
    
    log(f"Ambiente '{ENV_NAME}' criado com sucesso!", "ok")
    return True

# ─────────────────────────────────────────────────────────
# ETAPA 2: INSTALAR DEPENDÊNCIAS
# ─────────────────────────────────────────────────────────

def etapa_instalar_dependencias():
    log("ETAPA 2 — Instalando dependências", "etapa")
    
    # Determinar o executável pip/python do ambiente conda
    conda_prefix = executar(
        f"conda run -n {ENV_NAME} python -c \"import sys; print(sys.prefix)\"",
        capturar=True
    )
    
    if not conda_prefix or not conda_prefix.stdout.strip():
        log("Não foi possível localizar o ambiente Conda", "erro")
        return False
    
    run = f"conda run -n {ENV_NAME}"
    
    # Pacotes conda (core)
    log("Instalando pacotes conda (numpy, pandas, streamlit, PyTorch)...", "info")
    pacotes_conda = [
        "numpy", "pandas", "polars", "pyarrow", "requests", "streamlit",
    ]
    executar(f"{run} conda install -y -c conda-forge {' '.join(pacotes_conda)}")
    
    # PyTorch com CUDA
    log("Instalando PyTorch com suporte a GPU (CUDA 12.1)...", "info")
    executar(f"{run} conda install -y pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia")
    
    # Pacotes pip
    log("Instalando pacotes pip (sentence-transformers, PyMuPDF, etc.)...", "info")
    pacotes_pip = [
        "sentence-transformers",
        "python-dotenv",
        "PyMuPDF",
        "beautifulsoup4",
    ]
    executar(f"{run} pip install {' '.join(pacotes_pip)}")
    
    log("Todas as dependências instaladas!", "ok")
    return True

# ─────────────────────────────────────────────────────────
# ETAPA 3: CRIAR BANCO DE DADOS
# ─────────────────────────────────────────────────────────

def etapa_criar_banco():
    log("ETAPA 3 — Configurando banco de dados SQLite", "etapa")
    
    # Criar diretório se necessário
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    if DB_PATH.exists():
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        n_tabelas = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM normas" if n_tabelas > 0 else "SELECT 0")
        n_normas = cur.fetchone()[0]
        conn.close()
        
        if n_tabelas >= 5:
            log(f"Banco já existe com {n_tabelas} tabelas e {n_normas} normas. Pulando.", "ok")
            return True
    
    if not SCHEMA_PATH.exists():
        log(f"Schema não encontrado em {SCHEMA_PATH}", "erro")
        return False
    
    log("Criando tabelas a partir do schema.sql...", "info")
    conn = sqlite3.connect(str(DB_PATH))
    with open(str(SCHEMA_PATH), "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.close()
    
    log("Banco de dados criado com sucesso!", "ok")
    return True

# ─────────────────────────────────────────────────────────
# ETAPA 4: INGESTÃO DE DOCUMENTOS
# ─────────────────────────────────────────────────────────

def etapa_ingerir_documentos():
    log("ETAPA 4 — Ingestão de documentos na base RAG", "etapa")
    
    run = f"conda run -n {ENV_NAME} python"
    
    # 4a. Pipeline de versionamento (JSON → normas)
    texto_dir = BASE_DIR / "documentos" / "texto"
    if texto_dir.exists() and any(texto_dir.glob("*.json")):
        log("4a. Processando documentos JSON (versionamento)...", "info")
        executar(f"{run} -c \"from etl.versionamento_pipeline import processar_tudo; processar_tudo()\"")
        log("Documentos JSON processados!", "ok")
    else:
        log("4a. Nenhum JSON encontrado em documentos/texto/. Pulando.", "warn")
    
    # 4b. Ingestão de PDFs locais
    pdf_dir = BASE_DIR / "documentos" / "pdf"
    if pdf_dir.exists() and any(pdf_dir.rglob("*.pdf")):
        log("4b. Ingerindo PDFs locais (documentos/pdf/)...", "info")
        executar(f"{run} scripts/ingerir_pdfs.py")
        log("PDFs locais processados!", "ok")
    else:
        log("4b. Nenhum PDF local encontrado. Pulando.", "warn")
    
    # 4c. Ingestão de PDFs da Legislacao_SEFIN
    script_sefin_pdf = BASE_DIR / "scripts" / "ingerir_legislacao_sefin_pdfs.py"
    if script_sefin_pdf.exists():
        log("4c. Ingerindo PDFs da base Legislacao_SEFIN...", "info")
        executar(f"{run} scripts/ingerir_legislacao_sefin_pdfs.py")
        log("PDFs SEFIN processados!", "ok")
    else:
        log("4c. Script ingerir_legislacao_sefin_pdfs.py não encontrado. Pulando.", "warn")
    
    # 4d. Ingestão de HTMLs da Legislacao_SEFIN
    script_sefin_html = BASE_DIR / "scripts" / "ingerir_html_legislacao.py"
    if script_sefin_html.exists():
        log("4d. Ingerindo HTMLs da base Legislacao_atual (1.609 docs)...", "info")
        executar(f"{run} scripts/ingerir_html_legislacao.py")
        log("HTMLs SEFIN processados!", "ok")
    else:
        log("4d. Script ingerir_html_legislacao.py não encontrado. Pulando.", "warn")
    
    # Relatório
    if DB_PATH.exists():
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM normas")
        n_normas = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM dispositivos")
        n_disp = cur.fetchone()[0]
        conn.close()
        log(f"Base de dados: {n_normas} normas | {n_disp} dispositivos", "ok")
    
    return True

# ─────────────────────────────────────────────────────────
# ETAPA 5: GERAÇÃO DE EMBEDDINGS
# ─────────────────────────────────────────────────────────

def etapa_gerar_embeddings():
    log("ETAPA 5 — Geração de embeddings vetoriais (GPU)", "etapa")
    
    # Verificar se há dispositivos pendentes
    if DB_PATH.exists():
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(d.id) FROM dispositivos d 
            LEFT JOIN embeddings e ON d.id = e.dispositivo_id 
            WHERE e.id IS NULL
        """)
        pendentes = cur.fetchone()[0]
        conn.close()
        
        if pendentes == 0:
            log("Todos os dispositivos já estão vetorizados!", "ok")
            return True
        
        log(f"{pendentes} dispositivos pendentes de vetorização...", "info")
        log("Isso pode levar vários minutos dependendo da GPU disponível.", "info")
    
    run = f"conda run -n {ENV_NAME} python"
    executar(f"{run} rag/embeddings.py")
    
    log("Embeddings gerados com sucesso!", "ok")
    return True

# ─────────────────────────────────────────────────────────
# ETAPA 6: VERIFICAR OLLAMA + MODELO LLM
# ─────────────────────────────────────────────────────────

def etapa_verificar_llm():
    log("ETAPA 6 — Verificando LLM (Ollama)", "etapa")
    
    if not verificar_ollama():
        log("O Ollama é necessário para respostas com IA.", "warn")
        log(f"Após instalar, execute: ollama pull {OLLAMA_MODEL}", "info")
        return False
    
    # Verificar se o modelo está baixado
    result = executar("ollama list", capturar=True)
    if result and OLLAMA_MODEL.split(":")[0] in result.stdout:
        log(f"Modelo '{OLLAMA_MODEL}' encontrado!", "ok")
        return True
    
    log(f"Baixando modelo '{OLLAMA_MODEL}'... (pode levar alguns minutos)", "info")
    executar(f"ollama pull {OLLAMA_MODEL}")
    log("Modelo LLM pronto!", "ok")
    return True

# ─────────────────────────────────────────────────────────
# ETAPA 7: INICIAR DASHBOARD
# ─────────────────────────────────────────────────────────

def etapa_iniciar_dashboard():
    log("ETAPA 7 — Iniciando Dashboard", "etapa")
    
    # Relatório final antes de abrir
    if DB_PATH.exists():
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM normas")
        n_normas = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM dispositivos")
        n_disp = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM embeddings")
        n_emb = cur.fetchone()[0]
        conn.close()
        
        pct = (n_emb / n_disp * 100) if n_disp > 0 else 0
        print(f"""
{Cor.VERDE}{Cor.BOLD}
╔══════════════════════════════════════════════════════════╗
║                    SISTEMA PRONTO!                       ║
╠══════════════════════════════════════════════════════════╣
║  Normas:            {n_normas:>6}                                ║
║  Dispositivos:      {n_disp:>6}                                ║
║  Vetores RAG:       {n_emb:>6}  ({pct:.1f}%)                     ║
╚══════════════════════════════════════════════════════════╝
{Cor.FIM}""")
    
    log("Abrindo Dashboard Streamlit em http://localhost:8501", "info")
    log("Pressione Ctrl+C para encerrar.", "info")
    
    run = f"conda run -n {ENV_NAME}"
    try:
        executar(f"{run} streamlit run dashboard/app.py")
    except KeyboardInterrupt:
        print(f"\n{Cor.AMARELO}Sistema encerrado pelo usuário.{Cor.FIM}")

# ─────────────────────────────────────────────────────────
# ORQUESTRADOR PRINCIPAL
# ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="IA_leg — Inicialização completa do Revisor Fiscal Inteligente",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python iniciar.py                    Setup completo + dashboard
  python iniciar.py --etapa setup      Só cria ambiente e instala deps
  python iniciar.py --etapa ingerir    Só executa ingestão de documentos
  python iniciar.py --etapa indexar    Só gera embeddings
  python iniciar.py --etapa ui         Só abre o dashboard
  python iniciar.py --pular-ingestao   Setup sem re-ingerir docs
        """
    )
    parser.add_argument(
        "--etapa", choices=["setup", "ingerir", "indexar", "ui"],
        help="Executar apenas uma etapa específica"
    )
    parser.add_argument(
        "--pular-ingestao", action="store_true",
        help="Pular a etapa de ingestão de documentos (use se já foi feita antes)"
    )
    
    args = parser.parse_args()
    
    banner()
    
    inicio = time.time()
    
    if args.etapa == "setup":
        verificar_conda()
        etapa_criar_ambiente()
        etapa_instalar_dependencias()
        etapa_criar_banco()
        
    elif args.etapa == "ingerir":
        etapa_ingerir_documentos()
        
    elif args.etapa == "indexar":
        etapa_gerar_embeddings()
        
    elif args.etapa == "ui":
        etapa_iniciar_dashboard()
        
    else:
        # Fluxo completo
        verificar_conda()
        
        if not etapa_criar_ambiente():
            sys.exit(1)
        
        if not etapa_instalar_dependencias():
            log("Falha na instalação de dependências. Verifique os logs acima.", "erro")
            sys.exit(1)
        
        if not etapa_criar_banco():
            sys.exit(1)
        
        if not args.pular_ingestao:
            etapa_ingerir_documentos()
        else:
            log("Ingestão de documentos pulada (--pular-ingestao)", "warn")
        
        etapa_gerar_embeddings()
        
        etapa_verificar_llm()
        
        duracao = time.time() - inicio
        log(f"Setup completo em {duracao/60:.1f} minutos", "ok")
        
        etapa_iniciar_dashboard()


if __name__ == "__main__":
    main()
