"""
Ponto de entrada do sistema IA_leg.
Permite iniciar o dashboard ou o pipeline de indexação via CLI.
"""

import sys
import subprocess
import argparse

def iniciar_dashboard():
    """Inicia a interface Streamlit."""
    print("Iniciando Dashboard IA_leg...")
    try:
        subprocess.run(["streamlit", "run", "dashboard/app.py"], check=True)
    except KeyboardInterrupt:
        print("\nSistema encerrado pelo usuário.")
    except Exception as e:
        print(f"Erro ao iniciar dashboard: {e}")

def iniciar_indexacao():
    """Inicia o pipeline de embeddings."""
    print("Iniciando Pipeline de Indexação (GPU)...")
    try:
        subprocess.run(["python", "rag/embeddings.py"], check=True)
    except Exception as e:
        print(f"Erro na indexação: {e}")

def main():
    parser = argparse.ArgumentParser(description="IA_leg — Revisor Fiscal Inteligente")
    parser.add_argument("comando", nargs="?", default="ui", choices=["ui", "index"], 
                        help="Comando para executar: 'ui' (dashboard) ou 'index' (embeddings)")
    
    args = parser.parse_args()

    if args.comando == "ui":
        iniciar_dashboard()
    elif args.comando == "index":
        iniciar_indexacao()

if __name__ == "__main__":
    main()
