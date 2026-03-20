"""
Painel de observabilidade do IA_leg.

Uso:
    streamlit run dashboard/observability_app.py
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from ia_leg.observability.log_reader import (
    carregar_benchmark,
    carregar_query_logs,
    carregar_stats_query_logs,
)

st.set_page_config(
    page_title="Observabilidade IA_leg",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Observabilidade do IA_leg")
st.caption("Painel de benchmark, query_logs e integridade operacional do RAG")

stats = carregar_stats_query_logs()

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Consultas registradas", f"{stats['total']:,}")
with c2:
    st.metric("Taxa de sucesso", f"{stats['success_rate']:.1%}")
with c3:
    st.metric("Tempo médio total", f"{stats['avg_total_ms']:.1f} ms")
with c4:
    st.metric("Chunks médios", f"{stats['avg_chunks']:.2f}")

st.markdown("---")

st.subheader("Benchmark do RAG")
benchmark_path = st.text_input(
    "Arquivo de benchmark",
    value="ia_leg/observability/benchmark_resultados.json",
)

payload = carregar_benchmark(benchmark_path)
if not payload.get("exists"):
    st.warning(f"Arquivo de benchmark não encontrado: {payload.get('path')}")
else:
    resumo = payload.get("summary", {})
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.metric("Queries", resumo.get("total_queries", 0))
    with r2:
        st.metric("Fallback rate", f"{resumo.get('fallback_rate', 0):.1%}")
    with r3:
        st.metric("Source anchor rate", f"{resumo.get('source_anchor_ok_rate', 0):.1%}")
    with r4:
        st.metric("Avg answer ms", f"{resumo.get('avg_answer_time_ms', 0):.1f} ms")

    resultados = pd.DataFrame(payload.get("results", []))
    if not resultados.empty:
        st.dataframe(resultados, use_container_width=True, hide_index=True)

st.markdown("---")

st.subheader("Query logs")
limite = st.slider("Quantidade de registros", 50, 1000, 200, step=50)
logs = carregar_query_logs(limit=limite)

if logs.empty:
    st.info("Nenhum registro encontrado em query_logs.")
else:
    col_a, col_b = st.columns(2)
    with col_a:
        st.bar_chart(logs[["search_time_ms", "llm_time_ms", "total_time_ms"]].fillna(0).head(30))
    with col_b:
        backend_counts = logs["backend"].fillna("N/D").value_counts()
        st.bar_chart(backend_counts)

    st.dataframe(logs, use_container_width=True, hide_index=True)
