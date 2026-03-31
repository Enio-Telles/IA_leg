"""
Dashboard institucional — Revisor Fiscal Inteligente (SEFIN/RO).
Streamlit app com chat interativo e linha do tempo normativa.
"""

import sys
import html
from pathlib import Path

# Garantir que o root do projeto está no path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

from ia_leg.core.config.settings import DB_PATH

# ─────────────────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Revisor Fiscal Inteligente — SEFIN/RO",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────
# CSS CUSTOMIZADO
# ─────────────────────────────────────────────────────────

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * { font-family: 'Inter', sans-serif; }

    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    .main-header h1 { margin: 0; font-size: 1.6rem; font-weight: 700; }
    .main-header p { margin: 0.3rem 0 0 0; opacity: 0.8; font-size: 0.9rem; }

    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.2rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 3px 12px rgba(102, 126, 234, 0.3);
    }
    .stat-card.green { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); box-shadow: 0 3px 12px rgba(17,153,142,0.3); }
    .stat-card.orange { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); box-shadow: 0 3px 12px rgba(245,87,108,0.3); }
    .stat-card.blue { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); box-shadow: 0 3px 12px rgba(79,172,254,0.3); }
    .stat-card h3 { margin: 0; font-size: 2rem; font-weight: 700; }
    .stat-card p { margin: 0.2rem 0 0 0; font-size: 0.8rem; opacity: 0.9; }

    .timeline-item {
        border-left: 3px solid #667eea;
        padding: 0.8rem 1.2rem;
        margin: 0.5rem 0;
        background: rgba(102, 126, 234, 0.05);
        border-radius: 0 8px 8px 0;
        transition: background 0.2s;
    }
    .timeline-item:hover { background: rgba(102, 126, 234, 0.12); }

    .score-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .score-high { background: #d4edda; color: #155724; }
    .score-mid  { background: #fff3cd; color: #856404; }
    .score-low  { background: #f8d7da; color: #721c24; }

    div[data-testid="stChatMessage"] { border-radius: 12px; }

    .juris-card {
        background: linear-gradient(135deg, #2d1b69 0%, #11998e 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 3px 12px rgba(45, 27, 105, 0.3);
    }
    .juris-card h3 { margin: 0; font-size: 1.8rem; font-weight: 700; }
    .juris-card p { margin: 0.2rem 0 0 0; font-size: 0.75rem; opacity: 0.9; }
    .juris-card.sumula { background: linear-gradient(135deg, #0f3460 0%, #533483 100%); box-shadow: 0 3px 12px rgba(83, 52, 131, 0.3); }
    .juris-card.enunciado { background: linear-gradient(135deg, #1a1a2e 0%, #e94560 100%); box-shadow: 0 3px 12px rgba(233, 69, 96, 0.3); }
    .juris-card.orientacao { background: linear-gradient(135deg, #0d7377 0%, #14ffec 100%); color: #1a1a2e; box-shadow: 0 3px 12px rgba(13, 115, 119, 0.3); }

    .category-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #667eea;
        margin: 1.2rem 0 0.5rem 0;
        padding-bottom: 0.3rem;
        border-bottom: 2px solid rgba(102, 126, 234, 0.2);
    }
</style>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────
# FUNÇÕES AUXILIARES
# ─────────────────────────────────────────────────────────


@st.cache_resource
def get_db_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


@st.cache_data(ttl=60)
def carregar_estatisticas():
    conn = get_db_connection()
    # ⚡ Bolt: Replace multiple pd.read_sql calls with a single batched query to avoid N+1 latency
    query = """
        SELECT
            (SELECT COUNT(*) FROM normas) as normas,
            (SELECT COUNT(*) FROM dispositivos) as dispositivos,
            (SELECT COUNT(*) FROM embeddings) as embeddings,
            (SELECT COUNT(*) FROM versoes_norma) as versoes
    """
    df = pd.read_sql(query, conn)
    return {
        "normas": int(df.iloc[0]["normas"]),
        "dispositivos": int(df.iloc[0]["dispositivos"]),
        "embeddings": int(df.iloc[0]["embeddings"]),
        "versoes": int(df.iloc[0]["versoes"]),
    }


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
def carregar_detalhamento_rag():
    conn = get_db_connection()
    return pd.read_sql(
        """
        SELECT n.tipo as "Tipo de Documento", 
               n.tema as "Tema/Assunto", 
               COUNT(e.id) as "Trechos (Vetores RAG)"
        FROM embeddings e
        JOIN dispositivos d ON e.dispositivo_id = d.id
        JOIN versoes_norma v ON d.versao_id = v.id
        JOIN normas n ON v.norma_id = n.id
        WHERE v.vigencia_fim IS NULL
        GROUP BY n.tipo, n.tema
        ORDER BY "Trechos (Vetores RAG)" DESC
    """,
        conn,
    )


@st.cache_data(ttl=60)
def carregar_stats_jurisprudencia():
    """Carrega estatísticas detalhadas sobre a base jurisprudencial TATE."""
    conn = get_db_connection()
    # ⚡ Bolt: Replace O(N) loop of pd.read_sql queries with a single batched GROUP BY query
    query = """
        SELECT n.tipo,
               COUNT(DISTINCT n.id) as normas,
               COUNT(d.id) as chunks
        FROM normas n
        LEFT JOIN versoes_norma v ON n.id = v.norma_id AND v.vigencia_fim IS NULL
        LEFT JOIN dispositivos d ON v.id = d.versao_id
        WHERE n.tipo IN ('Jurisprudencia_TATE_Camara_Plena', 'Sumula_TATE', 'Jurisprudencia_TATE', 'Orientacao')
        GROUP BY n.tipo
    """
    df = pd.read_sql(query, conn)

    mapping = {
        "Jurisprudencia_TATE_Camara_Plena": "camara_plena",
        "Sumula_TATE": "sumulas",
        "Jurisprudencia_TATE": "enunciados",
        "Orientacao": "orientacoes",
    }

    stats = {
        "camara_plena": 0,
        "camara_plena_chunks": 0,
        "sumulas": 0,
        "sumulas_chunks": 0,
        "enunciados": 0,
        "enunciados_chunks": 0,
        "orientacoes": 0,
        "orientacoes_chunks": 0,
    }

    for _, row in df.iterrows():
        tipo = row["tipo"]
        if tipo in mapping:
            key = mapping[tipo]
            stats[key] = int(row["normas"])
            stats[key + "_chunks"] = int(row["chunks"])

    return stats


def agrupar_categorias(df_tipos):
    """Agrupa tipos de normas em categorias maiores para visualização."""
    categorias = {
        "Legislação": ["Decreto", "LO", "Lei Complementar", "RICMS/RO", "CTN", "RIPVA"],
        "Atos Normativos": ["Instrução Normativa", "Portaria", "Resolução"],
        "Jurisprudência TATE": [
            "Jurisprudencia_TATE_Camara_Plena",
            "Sumula_TATE",
            "Jurisprudencia_TATE",
        ],
        "Manuais e Orientações": [
            "Guia_Pratico_EFD",
            "Manual_MOC",
            "Orientacao",
            "Metodologia",
        ],
        "Pareceres e Despachos": ["Parecer", "Despacho"],
        "Outros": [
            "Jurisprudencia_STF",
            "RC",
            "AN",
            "IF",
            "PN",
            "AC",
            "RI",
            "SN",
            "OUTRAS",
        ],
    }
    result = []
    for cat, tipos in categorias.items():
        total = df_tipos[df_tipos["tipo"].isin(tipos)]["quantidade"].sum()
        if total > 0:
            result.append({"Categoria": cat, "Quantidade": int(total)})
    return pd.DataFrame(result)


@st.cache_data(ttl=60)
def carregar_timeline(filtro_tipo=None, limite=50):
    conn = get_db_connection()
    query = """
        SELECT n.tipo, n.numero, n.ano, v.vigencia_inicio, v.vigencia_fim,
               LENGTH(v.texto_integral) as tamanho_texto
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
def buscar_norma_detalhes_em_lote(norma_ids):
    if not norma_ids:
        import pandas as pd

        return pd.DataFrame()
    conn = get_db_connection()
    # ⚡ Bolt: Use IN clause to fetch details for all search results at once, avoiding N+1 query problem
    placeholders = ",".join("?" * len(norma_ids))
    versoes = pd.read_sql(
        f"""
        SELECT id, norma_id, vigencia_inicio, vigencia_fim, hash_texto,
               LENGTH(texto_integral) as tamanho
        FROM versoes_norma
        WHERE norma_id IN ({placeholders})
        ORDER BY vigencia_inicio DESC
    """,
        conn,
        params=norma_ids,
    )
    return versoes


@st.cache_data(ttl=60)
def buscar_norma_detalhes(norma_id):
    conn = get_db_connection()
    versoes = pd.read_sql(
        """
        SELECT id, vigencia_inicio, vigencia_fim, hash_texto,
               LENGTH(texto_integral) as tamanho
        FROM versoes_norma
        WHERE norma_id = ?
        ORDER BY vigencia_inicio DESC
    """,
        conn,
        params=[norma_id],
    )
    return versoes


@st.dialog("Texto Integral da Norma", width="large")
def modal_ler_texto(versao_id):
    conn = get_db_connection()
    df = pd.read_sql(
        "SELECT texto_integral FROM versoes_norma WHERE id = ?",
        conn,
        params=[versao_id],
    )
    if not df.empty:
        texto = html.escape(str(df.iloc[0]["texto_integral"]))
        st.markdown(
            f"<div style='white-space: pre-wrap; font-family: monospace; font-size: 14px; background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px;'>{texto}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.error("Texto não encontrado.")


@st.cache_data(ttl=60)
def pesquisar_normas(termo):
    conn = get_db_connection()
    termo_escaped = termo.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return pd.read_sql(
        """
        SELECT n.id, n.tipo, n.numero, n.ano,
               COUNT(d.id) as total_dispositivos
        FROM normas n
        LEFT JOIN versoes_norma v ON n.id = v.norma_id AND v.vigencia_fim IS NULL
        LEFT JOIN dispositivos d ON v.id = d.versao_id
        WHERE n.tipo LIKE ? ESCAPE '\\' OR n.numero LIKE ? ESCAPE '\\' OR CAST(n.ano AS TEXT) LIKE ? ESCAPE '\\'
        GROUP BY n.id
        ORDER BY n.ano DESC, n.tipo
        LIMIT 50
    """,
        conn,
        params=[f"%{termo_escaped}%", f"%{termo_escaped}%", f"%{termo_escaped}%"],
    )


# ─────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────

st.markdown(
    """
<div class="main-header">
    <h1>⚖️ Revisor Fiscal Inteligente</h1>
    <p>Secretaria de Estado de Finanças de Rondônia — Sistema de Consulta à Legislação Tributária</p>
</div>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### ⚙️ Configurações")

    pagina = st.radio(
        "Navegação",
        [
            "💬 Consulta IA",
            "📊 Painel Geral",
            "📜 Linha do Tempo",
            "🔍 Explorar Normas",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    stats = carregar_estatisticas()
    st.markdown("### 📈 Base de Dados")
    st.metric("Normas", f"{stats['normas']:,}")
    st.metric("Dispositivos", f"{stats['dispositivos']:,}")
    st.metric("Vetores RAG", f"{stats['embeddings']:,}")
    pct = (
        (stats["embeddings"] / stats["dispositivos"] * 100)
        if stats["dispositivos"] > 0
        else 0
    )
    st.progress(min(pct / 100, 1.0), text=f"Indexação: {pct:.1f}%")

    st.divider()

    if st.button(
        "🔄 Atualizar Base (RAG)",
        help="Recarrega os vetores e metadados mais recentes do banco.",
    ):
        with st.spinner("Limpando cache e recarregando vetores..."):
            from ia_leg.rag.retriever import invalidar_cache

            invalidar_cache()
            st.cache_data.clear()
            st.cache_resource.clear()
            st.rerun()

    st.caption(f"Última verificação: {datetime.now().strftime('%d/%m/%Y %H:%M')}")


# ─────────────────────────────────────────────────────────
# PÁGINA: CONSULTA IA
# ─────────────────────────────────────────────────────────

if pagina == "💬 Consulta IA":

    st.markdown("### 💬 Consulta à Legislação com IA")
    st.caption(
        "Faça perguntas em linguagem natural sobre a legislação tributária de Rondônia."
    )

    # Estado do chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Exibir histórico
    for msg in st.session_state.messages:
        with st.chat_message(
            msg["role"], avatar="⚖️" if msg["role"] == "assistant" else "👤"
        ):
            st.markdown(msg["content"])

    # Input
    if prompt := st.chat_input("Digite sua pergunta sobre legislação tributária..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="⚖️"):
            with st.spinner("Buscando na legislação e consultando IA..."):
                try:
                    from ia_leg.app.factory import get_answer_engine

                    engine = get_answer_engine()
                    resposta = engine(prompt, top_k=5, backend="ollama")
                except Exception as e:
                    resposta = f"❌ Erro ao consultar: {e}"

            st.markdown(resposta)
            st.session_state.messages.append({"role": "assistant", "content": resposta})


# ─────────────────────────────────────────────────────────
# PÁGINA: PAINEL GERAL
# ─────────────────────────────────────────────────────────

elif pagina == "📊 Painel Geral":

    st.markdown("### 📊 Painel Geral da Base Legislativa")

    # Cards de estatísticas
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
        <div class="stat-card">
            <h3>{stats['normas']:,}</h3>
            <p>Normas Cadastradas</p>
        </div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
        <div class="stat-card green">
            <h3>{stats['dispositivos']:,}</h3>
            <p>Dispositivos (Artigos)</p>
        </div>""",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
        <div class="stat-card orange">
            <h3>{stats['versoes']:,}</h3>
            <p>Versões Registradas</p>
        </div>""",
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
        <div class="stat-card blue">
            <h3>{stats['embeddings']:,}</h3>
            <p>Vetores RAG Indexados</p>
        </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Gráficos — Categorias agrupadas + Detalhamento individual
    col_chart, col_table = st.columns([2, 1])

    with col_chart:
        st.markdown("#### Distribuição por Categoria")
        df_tipos = carregar_normas_por_tipo()
        if not df_tipos.empty:
            df_cat = agrupar_categorias(df_tipos)
            if not df_cat.empty:
                st.bar_chart(
                    df_cat.set_index("Categoria")["Quantidade"], color="#667eea"
                )

    with col_table:
        st.markdown("#### Detalhamento por Tipo")
        if not df_tipos.empty:
            st.dataframe(
                df_tipos, use_container_width=True, hide_index=True, height=300
            )

    st.markdown("---")

    # Seção: Base Jurisprudencial TATE
    st.markdown("### ⚖️ Base Jurisprudencial — TATE/RO")
    st.caption(
        "Decisões da Câmara Plena, Súmulas e Enunciados do Tribunal Administrativo de Tributos Estaduais."
    )

    juris_stats = carregar_stats_jurisprudencia()

    j1, j2, j3, j4 = st.columns(4)
    with j1:
        st.markdown(
            f"""
        <div class="juris-card">
            <h3>{juris_stats['camara_plena']}</h3>
            <p>Decisões Câmara Plena</p>
            <p style="font-size:0.65rem; opacity:0.7;">{juris_stats['camara_plena_chunks']} trechos semânticos</p>
        </div>""",
            unsafe_allow_html=True,
        )
    with j2:
        st.markdown(
            f"""
        <div class="juris-card sumula">
            <h3>{juris_stats['sumulas']}</h3>
            <p>Súmulas TATE</p>
            <p style="font-size:0.65rem; opacity:0.7;">{juris_stats['sumulas_chunks']} trechos semânticos</p>
        </div>""",
            unsafe_allow_html=True,
        )
    with j3:
        st.markdown(
            f"""
        <div class="juris-card enunciado">
            <h3>{juris_stats['enunciados']}</h3>
            <p>Enunciados TATE</p>
            <p style="font-size:0.65rem; opacity:0.7;">{juris_stats['enunciados_chunks']} trechos semânticos</p>
        </div>""",
            unsafe_allow_html=True,
        )
    with j4:
        st.markdown(
            f"""
        <div class="juris-card orientacao">
            <h3>{juris_stats['orientacoes']}</h3>
            <p>Orientações</p>
            <p style="font-size:0.65rem; opacity:0.7;">{juris_stats['orientacoes_chunks']} trechos semânticos</p>
        </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### 🧠 Composição da Memória da IA (Base RAG)")
    st.caption(
        "Detalhamento explícito de todos os trechos semânticos (chunks) que a IA utiliza para gerar respostas contextuais."
    )

    df_rag = carregar_detalhamento_rag()
    if not df_rag.empty:
        st.dataframe(df_rag, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma base RAG carregada no momento.")


# ─────────────────────────────────────────────────────────
# PÁGINA: LINHA DO TEMPO
# ─────────────────────────────────────────────────────────

elif pagina == "📜 Linha do Tempo":

    st.markdown("### 📜 Linha do Tempo Normativa")
    st.caption("Histórico cronológico das publicações e alterações legislativas.")

    col_filtro, col_limite = st.columns([2, 1])
    with col_filtro:
        df_tipos = carregar_normas_por_tipo()
        opcoes_tipo = (
            ["Todos"] + df_tipos["tipo"].tolist() if not df_tipos.empty else ["Todos"]
        )
        filtro_tipo = st.selectbox("Filtrar por tipo", opcoes_tipo)
    with col_limite:
        limite = st.slider("Registros", 10, 200, 50)

    df_timeline = carregar_timeline(filtro_tipo, limite)

    if df_timeline.empty:
        st.info("Nenhum registro encontrado com os filtros selecionados.")
    else:
        for _, row in df_timeline.iterrows():
            vigente = "🟢" if pd.isna(row["vigencia_fim"]) else "🔴"
            status_txt = (
                "Vigente"
                if pd.isna(row["vigencia_fim"])
                else f"Revogada em {row['vigencia_fim']}"
            )
            tamanho_kb = row["tamanho_texto"] / 1024 if row["tamanho_texto"] else 0

            tipo_escaped = html.escape(str(row["tipo"]))
            num_escaped = html.escape(str(row["numero"]))
            ano_escaped = html.escape(str(row["ano"]))
            vigencia_escaped = html.escape(str(row["vigencia_inicio"]))
            status_escaped = html.escape(str(status_txt))

            st.markdown(
                f"""
            <div class="timeline-item">
                <strong>{vigente} {tipo_escaped} {num_escaped}/{ano_escaped}</strong>
                <br><small>📅 Publicação: {vigencia_escaped} | {status_escaped} | 📄 {tamanho_kb:.1f} KB</small>
            </div>
            """,
                unsafe_allow_html=True,
            )


# ─────────────────────────────────────────────────────────
# PÁGINA: EXPLORAR NORMAS
# ─────────────────────────────────────────────────────────

elif pagina == "🔍 Explorar Normas":

    st.markdown("### 🔍 Explorar Normas")

    termo = st.text_input(
        "Pesquisar por tipo, número ou ano", placeholder="Ex: Decreto, 22721, 2024..."
    )

    if termo:
        df_resultado = pesquisar_normas(termo)
        if df_resultado.empty:
            st.warning("Nenhuma norma encontrada.")
        else:
            st.success(f"{len(df_resultado)} norma(s) encontrada(s)")

            norma_ids = df_resultado["id"].tolist()
            todas_versoes = buscar_norma_detalhes_em_lote(norma_ids)

            for _, row in df_resultado.iterrows():
                with st.expander(
                    f"📋 {row['tipo']} {row['numero']}/{row['ano']} — {row['total_dispositivos']} dispositivos"
                ):
                    versoes = todas_versoes[todas_versoes["norma_id"] == row["id"]]
                    if not versoes.empty:
                        st.markdown("**Histórico de Versões:**")
                        for _, v in versoes.iterrows():
                            vigente = (
                                "🟢 Vigente"
                                if pd.isna(v["vigencia_fim"])
                                else f"🔴 Encerrada em {v['vigencia_fim']}"
                            )

                            col_info, col_btn = st.columns([4, 1])
                            with col_info:
                                st.markdown(
                                    f"- **{v['vigencia_inicio']}** → {vigente} "
                                    f"({v['tamanho']/1024:.1f} KB | Hash: `{v['hash_texto'][:12]}...`)"
                                )
                            with col_btn:
                                if st.button("📖 Ler Texto", key=f"btn_ler_{v['id']}"):
                                    modal_ler_texto(v["id"])
                    else:
                        st.info("Sem versões registradas.")
    else:
        st.info("Digite um termo para pesquisar na base legislativa.")
