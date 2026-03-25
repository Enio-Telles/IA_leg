"""Verificação leve de pré-merge para a trilha auditada do IA_leg.

Uso:
    python scripts/pre_merge_audit_check.py
"""

from __future__ import annotations

from pathlib import Path

REQUIRED_FILES = [
    "sitecustomize.py",
    "usercustomize.py",
    "ia_leg/rag/answer_engine_safe.py",
    "ia_leg/rag/answer_engine_safe_audited.py",
    "ia_leg/observability/audit_logger.py",
    "ia_leg/observability/benchmark_runner_audited.py",
    "ia_leg/observability/log_reader_audit.py",
    "dashboard/observability_audit_app_v2.py",
    "scripts/benchmark_ia_leg_audited.py",
]


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    missing = []

    for rel in REQUIRED_FILES:
        path = root / rel
        if not path.exists():
            missing.append(rel)

    print("=" * 60)
    print("PRE-MERGE AUDIT CHECK")
    print("=" * 60)

    if missing:
        print("Arquivos ausentes:")
        for item in missing:
            print(f"- {item}")
        return 1

    print("Todos os arquivos essenciais da trilha auditada estão presentes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
