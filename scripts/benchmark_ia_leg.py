"""Atalho para executar benchmark do IA_leg.

Uso:
    python scripts/benchmark_ia_leg.py
    python scripts/benchmark_ia_leg.py --backend ollama --top-k 5
"""

from ia_leg.observability.benchmark_runner import main


if __name__ == "__main__":
    main()
