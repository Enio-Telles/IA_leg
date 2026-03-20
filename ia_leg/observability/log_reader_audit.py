"""Leitura da trilha auditada de consultas seguras."""

from __future__ import annotations

import sqlite3
from typing import Any, Dict

import pandas as pd

from ia_leg.core.config.settings import DB_PATH
from ia_leg.observability.audit_logger import ensure_audit_schema


def get_db_connection() -> sqlite3.Connection:
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)



def carregar_query_audit_logs(limit: int = 500) -> pd.DataFrame:
    ensure_audit_schema()
    conn = get_db_connection()
    try:
        query = """
            SELECT id, pergunta, backend, model, filtros, top_k, min_score,
                   exigir_ancoras, context_count, max_score, fallback_reason,
                   source_anchor_ok, source_identifiers, source_normas,
                   response_preview, prompt_chars, search_time_ms,
                   rerank_time_ms, llm_time_ms, total_time_ms, created_at
            FROM query_audit_logs
            ORDER BY id DESC
            LIMIT ?
        """
        return pd.read_sql(query, conn, params=[limit])
    finally:
        conn.close()



def carregar_stats_query_audit_logs() -> Dict[str, Any]:
    df = carregar_query_audit_logs(limit=5000)
    if df.empty:
        return {
            "total": 0,
            "fallback_rate": 0.0,
            "source_anchor_ok_rate": 0.0,
            "avg_total_ms": 0.0,
            "avg_max_score": 0.0,
            "avg_context_count": 0.0,
        }

    fallback_mask = df["fallback_reason"].fillna("") != ""
    anchor_mask = df["source_anchor_ok"].fillna(0).astype(float)

    return {
        "total": int(len(df)),
        "fallback_rate": float(fallback_mask.mean()),
        "source_anchor_ok_rate": float(anchor_mask.mean()),
        "avg_total_ms": float(df["total_time_ms"].fillna(0).mean()),
        "avg_max_score": float(df["max_score"].fillna(0).mean()),
        "avg_context_count": float(df["context_count"].fillna(0).mean()),
    }
