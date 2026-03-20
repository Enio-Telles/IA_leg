"""Auditoria detalhada para consultas da trilha segura do IA_leg."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict

from ia_leg.core.config.settings import DB_PATH


CREATE_QUERY_AUDIT_LOGS_SQL = """
CREATE TABLE IF NOT EXISTS query_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pergunta TEXT NOT NULL,
    backend TEXT,
    model TEXT,
    filtros TEXT,
    top_k INTEGER,
    min_score REAL,
    exigir_ancoras BOOLEAN,
    context_count INTEGER,
    max_score REAL,
    fallback_reason TEXT,
    source_anchor_ok BOOLEAN,
    source_identifiers TEXT,
    source_normas TEXT,
    response_preview TEXT,
    prompt_chars INTEGER,
    search_time_ms REAL,
    rerank_time_ms REAL,
    llm_time_ms REAL,
    total_time_ms REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""


def ensure_audit_schema() -> None:
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute(CREATE_QUERY_AUDIT_LOGS_SQL)
        conn.commit()
    finally:
        conn.close()



def registrar_query_audit(payload: Dict[str, Any]) -> None:
    ensure_audit_schema()
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute(
            """
            INSERT INTO query_audit_logs (
                pergunta, backend, model, filtros, top_k, min_score, exigir_ancoras,
                context_count, max_score, fallback_reason, source_anchor_ok,
                source_identifiers, source_normas, response_preview, prompt_chars,
                search_time_ms, rerank_time_ms, llm_time_ms, total_time_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.get("pergunta"),
                payload.get("backend"),
                payload.get("model"),
                json.dumps(payload.get("filtros"), ensure_ascii=False),
                payload.get("top_k"),
                payload.get("min_score"),
                payload.get("exigir_ancoras"),
                payload.get("context_count"),
                payload.get("max_score"),
                payload.get("fallback_reason"),
                payload.get("source_anchor_ok"),
                json.dumps(payload.get("source_identifiers"), ensure_ascii=False),
                json.dumps(payload.get("source_normas"), ensure_ascii=False),
                payload.get("response_preview"),
                payload.get("prompt_chars"),
                payload.get("search_time_ms"),
                payload.get("rerank_time_ms"),
                payload.get("llm_time_ms"),
                payload.get("total_time_ms"),
            ),
        )
        conn.commit()
    finally:
        conn.close()
