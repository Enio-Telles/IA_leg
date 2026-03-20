"""Atalho para executar benchmark auditado do IA_leg.

Uso:
    python scripts/benchmark_ia_leg_audited.py
    python scripts/benchmark_ia_leg_audited.py --query-file ia_leg/observability/benchmark_queries_sefin_expanded.json
"""

from ia_leg.observability.benchmark_runner_audited import main


if __name__ == "__main__":
    main()
