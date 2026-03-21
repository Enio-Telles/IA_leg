"""Leitura de métricas operacionais do IA_leg."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from ia_leg.core.config.settings import DB_PATH


DEFAULT_BENCHMARK_FILE = Path(__file__).resolve().parent / "benchmark_resultados.json"


def get_db_connection() -> sqlite3.Connection:
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)


def carregar_query_logs(limit: int = 500) -> pd.DataFrame:
    conn = get_db_connection()
    try:
        query = """
            SELECT id, pergunta, filtros, embedding_time_ms, search_time_ms,
                   rerank_time_ms, llm_time_ms, total_time_ms, chunks_used,
                   backend, model, success, criado_em
            FROM query_logs
            ORDER BY id DESC
            LIMIT ?
        """
        return pd.read_sql(query, conn, params=[limit])
    finally:
        conn.close()



def carregar_stats_query_logs() -> Dict[str, Any]:
    df = carregar_query_logs(limit=5000)
    if df.empty:
        return {
            "total": 0,
            "success_rate": 0.0,
            "avg_total_ms": 0.0,
            "avg_llm_ms": 0.0,
            "avg_search_ms": 0.0,
            "avg_chunks": 0.0,
        }

    return {
        "total": int(len(df)),
        "success_rate": float(df["success"].fillna(0).astype(float).mean()),
        "avg_total_ms": float(df["total_time_ms"].fillna(0).mean()),
        "avg_llm_ms": float(df["llm_time_ms"].fillna(0).mean()),
        "avg_search_ms": float(df["search_time_ms"].fillna(0).mean()),
        "avg_chunks": float(df["chunks_used"].fillna(0).mean()),
    }



def carregar_benchmark(path: str | Path | None = None) -> Dict[str, Any]:
    alvo = Path(path) if path else DEFAULT_BENCHMARK_FILE
    if not alvo.exists():
        return {"exists": False, "path": str(alvo), "summary": {}, "results": []}

    with open(alvo, "r", encoding="utf-8") as f:
        payload = json.load(f)

    payload["exists"] = True
    payload["path"] = str(alvo)
    return payload
