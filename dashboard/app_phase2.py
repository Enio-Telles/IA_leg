"""
Dashboard fase 2 — Revisor Fiscal Inteligente (SEFIN/RO).

Inclui:
- consulta com recorte temporal de vigência;
- painel de observabilidade com métricas do query_logs;
- comparador de versões baseado em diff_estrutural;
- páginas do painel institucional já existentes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
from datetime import date, datetime

import pandas as pd
import streamlit as st

from ia_leg.core.config.settings import DB_PATH

st.set_page_config(
    page_title="Revisor Fiscal Inteligente — Fase 2",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    .main-header h1 { margin: 0; font-size: 1.6rem; font-weight: 700; }
    .main-header p { margin: 0.3rem 0 0 0; opacity: 0.85; font-size: 0.95rem; }
    .card {
        background: white;
        border: 1px solid rgba(15, 52, 96, 0.08);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 12px;
        text-align: center;
    }
    .metric-card h3 { margin: 0; font-size: 1.8rem; }
    .metric-card p { margin: 0.2rem 0 0 0; font-size: 0.85rem; }
    .timeline-item {
        border-left: 3px solid #667eea;
        padding: 0.8rem 1.2rem;
        margin: 0.5rem 0;
        background: rgba(102, 126, 234, 0.05);
        border-radius: 0 8px 8px 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def get_db_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


@st.cache_data(ttl=60)
def carregar_estatisticas():
    conn = get_db_connection()
    stats = {}
    stats["normas"] = pd.read_sql("SELECT COUNT(*) AS total FROM normas", conn).iloc[0]["total"]
    stats["dispositivos"] = pd.read_sql("SELECT COUNT(*) AS total FROM dispositivos", conn).iloc[0]["total"]
    stats["embeddings"] = pd.read_sql("SELECT COUNT(*) AS total FROM embeddings", conn).iloc[0]["total"]
    stats["versoes"] = pd.read_sql("SELECT COUNT(*) AS total FROM versoes_norma", conn).iloc[0]["total"]
    return stats


@st.cache_data(ttl=60)
def carregar_normas_por_tipo():
    conn = get_db_connection()
    return pd.read_sql(
        """
        SELECT tipo, COUNT(*) as quantidade
        FROM normas
        GROUP BY tipo
        ORDER BY quantidade DESC
        """,
        conn,
    )


@st.cache_data(ttl=60)
def carregar_timeline(filtro_tipo=None, limite=50):
    conn = get_db_connection()
    query = """
        SELECT n.tipo, n.numero, n.ano, v.vigencia_inicio, v.vigencia_fim,
               LENGTH(v.texto_integral) AS tamanho_texto
        FROM versoes_norma v
        JOIN normas n ON v.norma_id = n.id
        WHERE v.vigencia_inicio IS NOT NULL
    """
    params = []
    if filtro_tipo and filtro_tipo != "Todos":
        query += " AND n.tipo = ?"
        params.append(filtro_tipo)
    query += " ORDER BY v.vigencia_inicio DESC LIMIT ?"
    params.append(limite)
    return pd.read_sql(query, conn, params=params)


@st.cache_data(ttl=60)
def pesquisar_normas(termo):
    conn = get_db_connection()
    return pd.read_sql(
        """
        SELECT n.id, n.tipo, n.numero, n.ano,
               COUNT(d.id) AS total_dispositivos
        FROM normas n
        LEFT JOIN versoes_norma v ON n.id = v.norma_id AND v.vigencia_fim IS NULL
        LEFT JOIN dispositivos d ON v.id = d.versao_id
        WHERE n.tipo LIKE ? OR n.numero LIKE ? OR CAST(n.ano AS TEXT) LIKE ?
        GROUP BY n.id
        ORDER BY n.ano DESC, n.tipo
        LIMIT 50
        """,
        conn,
        params=[f"%{termo}%", f"%{termo}%", f"%{termo}%"],
    )


@st.cache_data(ttl=60)
def buscar_norma_detalhes(norma_id):
    conn = get_db_connection()
    return pd.read_sql(
        """
        SELECT id, vigencia_inicio, vigencia_fim, hash_texto,
               LENGTH(texto_integral) AS tamanho
        FROM versoes_norma
        WHERE norma_id = ?
        ORDER BY vigencia_inicio DESC
        """,
        conn,
        params=[norma_id],
    )


@st.cache_data(ttl=30)
def carregar_observabilidade_resumo():
    conn = get_db_connection()
    total = pd.read_sql("SELECT COUNT(*) AS total FROM query_logs", conn).iloc[0]["total"]
    sucesso = pd.read_sql("SELECT COUNT(*) AS total FROM query_logs WHERE success = 1", conn).iloc[0]["total"]
    tempos = pd.read_sql(
        """
        SELECT
            ROUND(AVG(total_time_ms), 2) AS avg_total,
            ROUND(AVG(search_time_ms), 2) AS avg_search,
            ROUND(AVG(rerank_time_ms), 2) AS avg_rerank,
            ROUND(AVG(llm_time_ms), 2) AS avg_llm
        FROM query_logs
        """,
        conn,
    ).iloc[0].to_dict()
    return {
        "total": int(total),
        "sucesso": int(sucesso),
        "falha": int(total - sucesso),
        "taxa_sucesso": round((sucesso / total) * 100, 2) if total else 0.0,
        **tempos,
    }


@st.cache_data(ttl=30)
def carregar_observabilidade_diaria(limite=30):
    conn = get_db_connection()
    return pd.read_sql(
        """
        SELECT
            DATE(criado_em) AS dia,
            COUNT(*) AS consultas,
            ROUND(AVG(total_time_ms), 2) AS tempo_medio_ms,
            ROUND(AVG(llm_time_ms), 2) AS llm_medio_ms,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) AS sucessos
        FROM query_logs
        GROUP BY DATE(criado_em)
        ORDER BY dia DESC
        LIMIT ?
        """,
        conn,
        params=[limite],
    )


@st.cache_data(ttl=30)
def carregar_consultas_recentes(limite=50):
    conn = get_db_connection()
    return pd.read_sql(
        """
        SELECT criado_em, pergunta, backend, model, chunks_used,
               total_time_ms, search_time_ms, rerank_time_ms, llm_time_ms, success
        FROM query_logs
        ORDER BY criado_em DESC
        LIMIT ?
        """,
        conn,
        params=[limite],
    )


@st.cache_data(ttl=60)
def listar_normas_para_comparacao(busca=""):
    conn = get_db_connection()
    if busca.strip():
        return pd.read_sql(
            """
            SELECT id, tipo, numero, ano
            FROM normas
            WHERE tipo LIKE ? OR numero LIKE ? OR CAST(ano AS TEXT) LIKE ?
            ORDER BY ano DESC, tipo, numero
            LIMIT 100
            """,
            conn,
            params=[f"%{busca}%", f"%{busca}%", f"%{busca}%"],
        )
    return pd.read_sql(
        """
        SELECT id, tipo, numero, ano
        FROM normas
        ORDER BY ano DESC, tipo, numero
        LIMIT 100
        """,
        conn,
    )


@st.cache_data(ttl=60)
def carregar_versoes_norma(norma_id):
    conn = get_db_connection()
    return pd.read_sql(
        """
        SELECT id, vigencia_inicio, vigencia_fim, hash_texto
        FROM versoes_norma
        WHERE norma_id = ?
        ORDER BY vigencia_inicio DESC
        """,
        conn,
        params=[norma_id],
    )


@st.cache_data(ttl=60)
def comparar_versoes(versao_origem_id, versao_destino_id):
    conn = get_db_connection()
    diff = pd.read_sql(
        """
        SELECT identificador, tipo_alteracao, hash_anterior, hash_novo
        FROM diff_estrutural
        WHERE versao_origem_id = ? AND versao_destino_id = ?
        ORDER BY tipo_alteracao, identificador
        """,
        conn,
        params=[versao_origem_id, versao_destino_id],
    )
    if not diff.empty:
        return diff

    origem = pd.read_sql(
        "SELECT identificador, texto FROM dispositivos WHERE versao_id = ?",
        conn,
        params=[versao_origem_id],
    )
    destino = pd.read_sql(
        "SELECT identificador, texto FROM dispositivos WHERE versao_id = ?",
        conn,
        params=[versao_destino_id],
    )

    if origem.empty and destino.empty:
        return pd.DataFrame(columns=["identificador", "tipo_alteracao"])

    origem_map = {row["identificador"]: row["texto"] for _, row in origem.iterrows()}
    destino_map = {row["identificador"]: row["texto"] for _, row in destino.iterrows()}

    registros = []
    for identificador, texto in origem_map.items():
        if identificador not in destino_map:
            registros.append({"identificador": identificador, "tipo_alteracao": "revogado"})
        elif destino_map[identificador] != texto:
            registros.append({"identificador": identificador, "tipo_alteracao": "alterado"})
        else:
            registros.append({"identificador": identificador, "tipo_alteracao": "mantido"})

    for identificador in destino_map.keys():
        if identificador not in origem_map:
            registros.append({"identificador": identificador, "tipo_alteracao": "incluido"})

    return pd.DataFrame(registros)


st.markdown(
    """
<div class="main-header">
    <h1>⚖️ Revisor Fiscal Inteligente — Fase 2</h1>
    <p>Consulta temporal, observabilidade operacional e comparação de versões normativas</p>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    pagina = st.radio(
        "Navegação",
        [
            "💬 Consulta IA",
            "📈 Observabilidade",
            "🧾 Comparar Versões",
            "📊 Painel Geral",
            "📜 Linha do Tempo",
            "🔍 Explorar Normas",
        ],
        label_visibility="collapsed",
    )

    stats = carregar_estatisticas()
    st.metric("Normas", f"{stats['normas']:,}")
    st.metric("Dispositivos", f"{stats['dispositivos']:,}")
    st.metric("Vetores RAG", f"{stats['embeddings']:,}")
    pct = (stats["embeddings"] / stats["dispositivos"] * 100) if stats["dispositivos"] else 0
    st.progress(min(pct / 100, 1.0), text=f"Indexação: {pct:.1f}%")
    st.caption(f"Última atualização da tela: {datetime.now().strftime('%d/%m/%Y %H:%M')}")


if pagina == "💬 Consulta IA":
    st.subheader("💬 Consulta à Legislação com IA")
    st.caption("Agora com recorte temporal opcional de vigência.")

    col_a, col_b = st.columns([2, 1])
    with col_a:
        usar_data = st.checkbox("Consultar por data de referência", value=False)
    with col_b:
        data_referencia = st.date_input(
            "Data de referência",
            value=date.today(),
            disabled=not usar_data,
            format="DD/MM/YYYY",
        )

    if "messages_phase2" not in st.session_state:
        st.session_state.messages_phase2 = []

    for msg in st.session_state.messages_phase2:
        with st.chat_message(msg["role"], avatar="⚖️" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Digite sua pergunta sobre legislação tributária..."):
        st.session_state.messages_phase2.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="⚖️"):
            with st.spinner("Consultando a base normativa..."):
                try:
                    from ia_leg.rag.answer_engine_temporal import consultar_temporal

                    data_ref_str = data_referencia.isoformat() if usar_data else None
                    resposta = consultar_temporal(
                        prompt,
                        top_k=5,
                        backend="ollama",
                        data_referencia=data_ref_str,
                    )
                except Exception as e:
                    resposta = f"❌ Erro ao consultar: {e}"

            st.markdown(resposta)
            st.session_state.messages_phase2.append({"role": "assistant", "content": resposta})

elif pagina == "📈 Observabilidade":
    st.subheader("📈 Observabilidade Operacional")
    st.caption("Métricas capturadas a partir da tabela query_logs.")

    resumo = carregar_observabilidade_resumo()
    c1, c2, c3, c4 = st.columns(4)
    for col, valor, rotulo in [
        (c1, resumo["total"], "Consultas registradas"),
        (c2, f"{resumo['taxa_sucesso']}%", "Taxa de sucesso"),
        (c3, f"{resumo.get('avg_total') or 0} ms", "Tempo médio total"),
        (c4, f"{resumo.get('avg_llm') or 0} ms", "Tempo médio LLM"),
    ]:
        with col:
            st.markdown(f"<div class='metric-card'><h3>{valor}</h3><p>{rotulo}</p></div>", unsafe_allow_html=True)

    st.markdown("### Latência média por etapa")
    df_lat = pd.DataFrame(
        {
            "etapa": ["busca", "rerank", "llm", "total"],
            "tempo_ms": [
                resumo.get("avg_search") or 0,
                resumo.get("avg_rerank") or 0,
                resumo.get("avg_llm") or 0,
                resumo.get("avg_total") or 0,
            ],
        }
    )
    st.bar_chart(df_lat.set_index("etapa"))

    st.markdown("### Evolução diária")
    df_obs = carregar_observabilidade_diaria()
    if df_obs.empty:
        st.info("Ainda não há registros em query_logs.")
    else:
        st.line_chart(df_obs.sort_values("dia").set_index("dia")[["consultas", "tempo_medio_ms"]])
        st.dataframe(df_obs, use_container_width=True, hide_index=True)

    st.markdown("### Consultas recentes")
    df_recentes = carregar_consultas_recentes()
    st.dataframe(df_recentes, use_container_width=True, hide_index=True)

elif pagina == "🧾 Comparar Versões":
    st.subheader("🧾 Comparador de Versões Normativas")
    st.caption("Compara duas versões da mesma norma usando diff_estrutural ou fallback estrutural.")

    busca_norma = st.text_input("Pesquisar norma para comparação", placeholder="Ex: Decreto 22121 2024")
    df_normas = listar_normas_para_comparacao(busca_norma)

    if df_normas.empty:
        st.info("Nenhuma norma encontrada para comparação.")
    else:
        opcoes = {
            f"{row['tipo']} {row['numero']}/{row['ano']}": row['id']
            for _, row in df_normas.iterrows()
        }
        norma_escolhida = st.selectbox("Selecione a norma", list(opcoes.keys()))
        norma_id = opcoes[norma_escolhida]

        versoes = carregar_versoes_norma(norma_id)
        if len(versoes) < 2:
            st.warning("A norma selecionada não possui ao menos duas versões para comparação.")
        else:
            labels_versoes = {
                f"ID {row['id']} | início {row['vigencia_inicio']} | fim {row['vigencia_fim'] if pd.notna(row['vigencia_fim']) else 'Atual'}": row['id']
                for _, row in versoes.iterrows()
            }
            col1, col2 = st.columns(2)
            with col1:
                origem_label = st.selectbox("Versão origem", list(labels_versoes.keys()), index=min(1, len(labels_versoes)-1))
            with col2:
                destino_label = st.selectbox("Versão destino", list(labels_versoes.keys()), index=0)

            origem_id = labels_versoes[origem_label]
            destino_id = labels_versoes[destino_label]

            if origem_id == destino_id:
                st.info("Selecione versões diferentes para comparar.")
            else:
                diff = comparar_versoes(origem_id, destino_id)
                if diff.empty:
                    st.info("Nenhuma diferença encontrada entre as versões selecionadas.")
                else:
                    resumo = diff.groupby("tipo_alteracao").size().reset_index(name="quantidade")
                    st.markdown("### Resumo das alterações")
                    st.dataframe(resumo, use_container_width=True, hide_index=True)
                    st.markdown("### Diferenças por dispositivo")
                    st.dataframe(diff, use_container_width=True, hide_index=True)

elif pagina == "📊 Painel Geral":
    st.subheader("📊 Painel Geral da Base Legislativa")
    stats = carregar_estatisticas()
    cols = st.columns(4)
    dados = [
        (stats["normas"], "Normas"),
        (stats["dispositivos"], "Dispositivos"),
        (stats["versoes"], "Versões"),
        (stats["embeddings"], "Vetores RAG"),
    ]
    for col, (valor, rotulo) in zip(cols, dados):
        with col:
            st.markdown(f"<div class='metric-card'><h3>{valor:,}</h3><p>{rotulo}</p></div>", unsafe_allow_html=True)

    df_tipos = carregar_normas_por_tipo()
    st.markdown("### Distribuição por tipo")
    if not df_tipos.empty:
        st.bar_chart(df_tipos.set_index("tipo")["quantidade"])
        st.dataframe(df_tipos, use_container_width=True, hide_index=True)

elif pagina == "📜 Linha do Tempo":
    st.subheader("📜 Linha do Tempo Normativa")
    df_tipos = carregar_normas_por_tipo()
    opcoes_tipo = ["Todos"] + df_tipos["tipo"].tolist() if not df_tipos.empty else ["Todos"]
    col1, col2 = st.columns([2, 1])
    with col1:
        filtro_tipo = st.selectbox("Filtrar por tipo", opcoes_tipo)
    with col2:
        limite = st.slider("Registros", 10, 200, 50)

    df_timeline = carregar_timeline(filtro_tipo, limite)
    if df_timeline.empty:
        st.info("Nenhum registro encontrado com os filtros selecionados.")
    else:
        for _, row in df_timeline.iterrows():
            vigente = "🟢" if pd.isna(row["vigencia_fim"]) else "🔴"
            status_txt = "Vigente" if pd.isna(row["vigencia_fim"]) else f"Revogada em {row['vigencia_fim']}"
            tamanho_kb = (row["tamanho_texto"] or 0) / 1024
            st.markdown(
                f"<div class='timeline-item'><strong>{vigente} {row['tipo']} {row['numero']}/{row['ano']}</strong><br><small>📅 Publicação: {row['vigencia_inicio']} | {status_txt} | 📄 {tamanho_kb:.1f} KB</small></div>",
                unsafe_allow_html=True,
            )

elif pagina == "🔍 Explorar Normas":
    st.subheader("🔍 Explorar Normas")
    termo = st.text_input("Pesquisar por tipo, número ou ano", placeholder="Ex: Decreto, 22721, 2024...")
    if termo:
        df_resultado = pesquisar_normas(termo)
        if df_resultado.empty:
            st.warning("Nenhuma norma encontrada.")
        else:
            st.success(f"{len(df_resultado)} norma(s) encontrada(s)")
            for _, row in df_resultado.iterrows():
                with st.expander(f"📋 {row['tipo']} {row['numero']}/{row['ano']} — {row['total_dispositivos']} dispositivos"):
                    versoes = buscar_norma_detalhes(row["id"])
                    st.dataframe(versoes, use_container_width=True, hide_index=True)
    else:
        st.info("Digite um termo para pesquisar na base legislativa.")
