"""
Ingestão de documentos HTML da pasta Legislacao_SEFIN/Legislacao_atual.
Usa indice_geral.json como fonte de metadados estruturados.
"""

import sys
import re
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from ia_leg.core.config.settings import LEGISLACAO_SEFIN_DIR
from etl.html_to_text import extrair_texto_html
from etl.versionamento_pipeline import (
    conectar,
    calcular_hash_texto,
    quebrar_pdf_em_chunks,
)

# ─────────────────────────────────────────────────────────
# MAPEAMENTO DE CATEGORIAS DO JSON → TIPOS NO RAG
# ─────────────────────────────────────────────────────────

MAPA_CATEGORIAS = {
    "Ato Conjunto": "AC",
    "Ato Normativo": "AN",
    "Código Tributário Nacional": "CTN",
    "Decretos": "Decreto",
    "Informações Fiscais": "IF",
    "Instrução Normativa": "Instrução Normativa",
    "Legislação outras": "OUTRAS",
    "Leis Complementares": "Lei Complementar",
    "Leis Ordinárias": "LO",
    "Pareceres": "Parecer",
    "Pareceres Normativos": "PN",
    "Regulamento do ICMS e ANEXOS (Novo)": "RICMS/RO",
    "Regulamento do ICMS e ANEXOS (Antigo)": "RICMS/RO_Antigo",
    "Regulamento do IPVA": "RIPVA",
    "Regulamento do ITCD": "RITCD",
    "Resoluções": "Resolução",
    "Resoluções Conjuntas": "RC",
    "Simples Nacional": "SN",
}


def extrair_numero_identificador(identificador: str) -> tuple:
    """Extrai número e ano de um identificador como 'D 31274/2026' ou 'IN 15/2018'."""
    match = re.search(r"(\d+)[/](\d{4})", identificador)
    if match:
        return match.group(1), int(match.group(2))
    # Fallback: tentar só o número
    match = re.search(r"(\d+)", identificador)
    if match:
        return match.group(1), 2024
    return identificador, 2024


def ler_e_processar_html(html_path, identificador, titulo, categoria):
    """
    Lê o arquivo HTML, extrai texto, gera hash e tema.
    Retorna (texto_completo, hash_texto, tema_auto) ou (None, None, None) se falhar.
    """
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        html_content = f.read()

    texto = extrair_texto_html(html_content)
    if not texto or len(texto.strip()) < 30:
        return None, None, None

    # Prefixar com título/ementa para contexto semântico

    texto_completo = f"{identificador} - {titulo}\n\n{texto}"
    hash_texto = calcular_hash_texto(texto_completo)

    # Tema baseado no título (primeiras palavras)
    tema_auto = titulo[:50].replace(" ", "_") if titulo else categoria

    return texto_completo, hash_texto, tema_auto


def salvar_documento_bd(
    cursor, tipo, numero, ano, tema_auto, texto_completo, hash_texto
):
    """
    Verifica se a norma existe, atualiza/insere, faz chunking e salva dispositivos.
    Retorna uma string: 'inserido', 'atualizado' ou 'pulado'.
    """
    # 2. Verificar/inserir norma
    cursor.execute(
        "SELECT id FROM normas WHERE tipo=? AND numero=? AND ano=?", (tipo, numero, ano)
    )
    resultado = cursor.fetchone()

    if resultado:
        norma_id = resultado[0]
        cursor.execute("UPDATE normas SET tema=? WHERE id=?", (tema_auto, norma_id))
    else:
        cursor.execute(
            "INSERT INTO normas (tipo, numero, ano, tema) VALUES (?, ?, ?, ?)",
            (tipo, numero, ano, tema_auto),
        )
        norma_id = cursor.lastrowid

    # 3. Verificar versão (dedup)
    cursor.execute(
        "SELECT id, hash_texto FROM versoes_norma WHERE norma_id=? AND vigencia_fim IS NULL",
        (norma_id,),
    )
    versao_atual = cursor.fetchone()

    if versao_atual and versao_atual[1] == hash_texto:
        return "pulado"

    status = "inserido"
    if versao_atual:
        cursor.execute(
            "UPDATE versoes_norma SET vigencia_fim=CURRENT_DATE WHERE id=?",
            (versao_atual[0],),
        )
        status = "atualizado"

    # 4. Inserir nova versão
    cursor.execute(
        "INSERT INTO versoes_norma (norma_id, texto_integral, hash_texto, vigencia_inicio) VALUES (?, ?, ?, CURRENT_DATE)",
        (norma_id, texto_completo, hash_texto),
    )
    nova_versao_id = cursor.lastrowid

    # 5. Chunking
    chunks = quebrar_pdf_em_chunks(texto_completo)
    dados_dispositivos = [
        (nova_versao_id, ident, conteudo, calcular_hash_texto(conteudo))
        for ident, conteudo in chunks
    ]
    if dados_dispositivos:
        cursor.executemany(
            "INSERT INTO dispositivos (versao_id, identificador, texto, hash_dispositivo) VALUES (?, ?, ?, ?)",
            dados_dispositivos,
        )

    return status


def ingerir_html_legislacao():
    """Ingere documentos HTML da Legislacao_atual usando indice_geral.json."""
    pasta_base = LEGISLACAO_SEFIN_DIR / "Legislacao_atual"
    indice_path = pasta_base / "indice_geral.json"

    if not indice_path.exists():
        print(f"ERRO: Índice não encontrado: {indice_path}")
        return

    # Carregar índice
    with open(indice_path, "r", encoding="utf-8") as f:
        indice = json.load(f)

    documentos = indice.get("documentos", {})
    total = len(documentos)

    conn = conectar()
    cursor = conn.cursor()

    inseridos = 0
    atualizados = 0
    pulados = 0
    erros = 0

    print(f"{'=' * 60}")
    print("INGESTÃO HTML — Legislacao_atual")
    print(f"Documentos no índice: {total}")
    print(f"Última atualização:   {indice.get('ultima_atualizacao', 'N/A')}")
    print(f"{'='*60}\n")

    for i, (doc_id, meta) in enumerate(documentos.items(), 1):
        categoria = meta.get("categoria", "Outros")
        identificador = meta.get("identificador", "S/N")
        titulo = meta.get("titulo", "")
        ano = meta.get("ano", 2024)
        arquivo_rel = meta.get("arquivo", "")

        # Mapear categoria → tipo RAG
        tipo = MAPA_CATEGORIAS.get(categoria, categoria)

        # Extrair número
        numero, ano_id = extrair_numero_identificador(identificador)
        if ano == 0:
            ano = ano_id

        # Caminho do HTML
        html_path = pasta_base / arquivo_rel.replace("\\\\", "\\")
        if not html_path.exists():
            if i <= 5 or erros < 3:
                print(f"[{i}/{total}] SKIP {arquivo_rel}: arquivo não encontrado")
            erros += 1
            continue

        # Progresso a cada 100 docs
        if i % 100 == 0 or i == 1:
            print(f"[{i}/{total}] Processando {categoria}...")

        try:
            conn.execute("BEGIN TRANSACTION;")

            texto_completo, hash_texto, tema_auto = ler_e_processar_html(
                html_path, identificador, titulo, categoria
            )

            if not texto_completo:
                conn.rollback()
                pulados += 1
                continue

            status = salvar_documento_bd(
                cursor, tipo, numero, ano, tema_auto, texto_completo, hash_texto
            )

            if status == "pulado":
                conn.rollback()
                pulados += 1
                continue

            conn.commit()
            if status == "inserido":
                inseridos += 1
            elif status == "atualizado":
                atualizados += 1

        except Exception as e:
            conn.rollback()
            erros += 1
            if erros <= 10:
                print(f"  ERRO em {arquivo_rel}: {e}")

    conn.close()

    print(f"\n{'=' * 60}")
    print("RESULTADO FINAL")
    print(f"  Inseridos novos: {inseridos}")
    print(f"  Atualizados:     {atualizados}")
    print(f"  Pulados (dedup): {pulados}")
    print(f"  Erros:           {erros}")
    print(f"{'=' * 60}")
    print("\nPróximo passo: python -m ia_leg.rag.embedding_service")


if __name__ == "__main__":
    ingerir_html_legislacao()
