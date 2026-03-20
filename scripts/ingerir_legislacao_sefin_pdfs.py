"""
Ingestão de PDFs temáticos da pasta Legislacao_SEFIN.
Mapeia automaticamente metadados com base na pasta-pai de cada arquivo.
"""

import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from ia_leg.core.config.settings import LEGISLACAO_SEFIN_DIR
from etl.pdf_to_text import extrair_texto_pdf
from etl.versionamento_pipeline import (
    conectar,
    calcular_hash_texto,
    quebrar_pdf_em_chunks,
)

# ─────────────────────────────────────────────────────────
# MAPEAMENTO AUTOMÁTICO DE METADADOS POR PASTA
# ─────────────────────────────────────────────────────────

MAPA_PASTAS = {
    "ricmsro": {"tipo": "RICMS/RO", "tema": "Regulamento_ICMS"},
    "efd": {"tipo": "Manual_EFD", "tema": "Obrigacao_Acessoria"},
    "fisconforme": {"tipo": "Orientacao_Fisconforme", "tema": "Fisconforme"},
    "comercio_exterior": {"tipo": "Comercio_Exterior", "tema": "Importacao_Exportacao"},
    "decisoes_stf": {"tipo": "Jurisprudencia_STF", "tema": "Jurisprudencia"},
    "reforma_tributaria": {"tipo": "Reforma_Tributaria", "tema": "Reforma_Tributaria"},
    "nfe": {"tipo": "Manual_NFe", "tema": "Nota_Fiscal"},
    "nf3e": {"tipo": "Manual_NF3e", "tema": "Nota_Fiscal"},
    "nota_fiscal": {"tipo": "Manual_NFe", "tema": "Nota_Fiscal"},
    "simples": {"tipo": "Simples_Nacional", "tema": "Simples_Nacional"},
    "estoque": {"tipo": "Metodologia", "tema": "ICMS_ST"},
    "refaz": {"tipo": "REFAZ", "tema": "Programa_Fiscal"},
    "creditos_acum": {"tipo": "Orientacao", "tema": "Creditos_Acumulados"},
    "agencia_virtual": {"tipo": "Orientacao", "tema": "Agencia_Virtual"},
    "in_instrucao_normativa": {
        "tipo": "Instrucao_Normativa_PDF",
        "tema": "Instrucao_Normativa",
    },
    "imposto de renda": {"tipo": "Imposto_Renda", "tema": "Imposto_Renda"},
    "tate": None,  # Já ingerido pelo script anterior
    "curso": None,  # Material de curso, pular
    "nova pasta": None,  # Pasta vazia/genérica
}

# PDFs na raiz mapeados estaticamente
MAPA_RAIZ = {
    "CF_1988.pdf": {
        "tipo": "Legislacao_Federal",
        "tema": "Constituicao_Federal",
        "numero": "CF/1988",
        "ano": 1988,
    },
    "LC_87_1996_Lei_Kandir.pdf": {
        "tipo": "Legislacao_Federal",
        "tema": "Lei_Kandir",
        "numero": "LC87/1996",
        "ano": 1996,
    },
    "LO_688_1996.pdf": {"tipo": "LO", "tema": "ICMS", "numero": "688", "ano": 1996},
    "Lcp225_Cod_defesa_contribuinte.pdf": {
        "tipo": "Lei Complementar",
        "tema": "Defesa_Contribuinte",
        "numero": "225",
        "ano": 2010,
    },
    "CFOP.pdf": {
        "tipo": "Tabela_Referencia",
        "tema": "CFOP",
        "numero": "CFOP",
        "ano": 2024,
    },
    "CFOP_incluidos_estoque.pdf": {
        "tipo": "Tabela_Referencia",
        "tema": "CFOP_Estoque",
        "numero": "CFOP_EST",
        "ano": 2024,
    },
    "NCM_nesh-2022.pdf": {
        "tipo": "Tabela_Referencia",
        "tema": "NCM",
        "numero": "NESH",
        "ano": 2022,
    },
    "tabela_ncm.pdf": {
        "tipo": "Tabela_Referencia",
        "tema": "NCM",
        "numero": "NCM_TAB",
        "ano": 2024,
    },
    "tipi.pdf": {
        "tipo": "Tabela_Referencia",
        "tema": "TIPI",
        "numero": "TIPI",
        "ano": 2024,
    },
    "CONVENIO ICMS 23_08_ALC_INTERNAMENTO.pdf": {
        "tipo": "Convenio_ICMS",
        "tema": "ALC_Internamento",
        "numero": "23/08",
        "ano": 2008,
    },
    "convenio_ICMS_142_2018.pdf": {
        "tipo": "Convenio_ICMS",
        "tema": "Substituicao_Tributaria",
        "numero": "142/2018",
        "ano": 2018,
    },
    "comercio_exterior_importacao_lei_1473.pdf": {
        "tipo": "Legislacao_Estadual",
        "tema": "Comercio_Exterior",
        "numero": "1473",
        "ano": 2005,
    },
    "manual_arrecadacao.pdf": {
        "tipo": "Manual",
        "tema": "Arrecadacao",
        "numero": "S/N",
        "ano": 2024,
    },
    "Ressarcimento_apresentacao.pdf": {
        "tipo": "Orientacao",
        "tema": "Ressarcimento_ICMS_ST",
        "numero": "APRES",
        "ano": 2024,
    },
    "PAINEL EXPORTACAO.pdf": {
        "tipo": "Orientacao",
        "tema": "Exportacao",
        "numero": "PAINEL",
        "ano": 2024,
    },
    "Guia Prático EFD - Versão 3.1.8 (1).pdf": {
        "tipo": "Guia_Pratico_EFD",
        "tema": "Obrigacao_Acessoria",
        "numero": "3.1.8",
        "ano": 2023,
    },
    "IN_15_2018_PREENCHIMENTO_NFE_GUAJARA.pdf": {
        "tipo": "Instrucao_Normativa_PDF",
        "tema": "NFe_Guajara",
        "numero": "15/2018",
        "ano": 2018,
    },
    "IN_34_2020_produtor_rural.pdf": {
        "tipo": "Instrucao_Normativa_PDF",
        "tema": "Produtor_Rural",
        "numero": "34/2020",
        "ano": 2020,
    },
    "Codigo_Civil_L10406compilada.pdf": {
        "tipo": "Legislacao_Federal",
        "tema": "Codigo_Civil",
        "numero": "10406",
        "ano": 2002,
    },
}


def extrair_metadados_sefin(arq_path: Path) -> dict:
    """Extrai metadados com base na pasta-pai e no nome do arquivo."""
    nome = arq_path.name

    # PDFs na raiz
    if arq_path.parent == LEGISLACAO_SEFIN_DIR:
        meta = MAPA_RAIZ.get(nome)
        if meta:
            return meta
        # Fallback para PDFs raiz não mapeados
        base = nome.rsplit(".", 1)[0]
        return {
            "tipo": "Legislacao_Geral",
            "tema": base.replace(" ", "_")[:50],
            "numero": "S/N",
            "ano": 2024,
        }

    # Verificar cada pasta ancestral
    for part in arq_path.relative_to(LEGISLACAO_SEFIN_DIR).parts[:-1]:
        chave = part.lower()
        if chave in MAPA_PASTAS:
            mapa = MAPA_PASTAS[chave]
            if mapa is None:
                return None  # Pular esta pasta

            base = nome.rsplit(".", 1)[0]

            # Tentar extrair número e ano do nome do arquivo
            match_num = re.search(r"(\d+)[_/](\d{4})", base)
            if match_num:
                numero = match_num.group(1)
                ano = int(match_num.group(2))
            else:
                numero = base.replace(" ", "_")[:30]
                # Tentar extrair ano isolado
                match_ano = re.search(r"(\d{4})", base)
                ano = int(match_ano.group(1)) if match_ano else 2024

            return {
                "tipo": mapa["tipo"],
                "tema": mapa["tema"],
                "numero": numero,
                "ano": ano,
            }

    # Fallback genérico
    base = nome.rsplit(".", 1)[0]
    return {
        "tipo": "Legislacao_Geral",
        "tema": base.replace(" ", "_")[:50],
        "numero": "S/N",
        "ano": 2024,
    }


def ingerir_pdfs_sefin():
    """Ingere todos os PDFs da pasta Legislacao_SEFIN."""
    if not LEGISLACAO_SEFIN_DIR.exists():
        print(f"ERRO: Diretório não encontrado: {LEGISLACAO_SEFIN_DIR}")
        return

    # Excluir Legislacao_atual (processado separadamente como HTML)
    arquivos = [
        f
        for f in LEGISLACAO_SEFIN_DIR.rglob("*.pdf")
        if "Legislacao_atual" not in str(f)
        and "Tabela_NCM_Texto_Puro" not in f.name  # xlsx renomeado
    ]

    conn = conectar()
    cursor = conn.cursor()

    total = len(arquivos)
    inseridos = 0
    pulados = 0
    erros = 0

    print(f"{'=' * 60}")
    print("INGESTÃO DE PDFs — Legislacao_SEFIN")
    print(f"Arquivos encontrados: {total}")
    print(f"{'=' * 60}\n")

    for i, arq in enumerate(arquivos, 1):
        rel_path = arq.relative_to(LEGISLACAO_SEFIN_DIR)

        metadados = extrair_metadados_sefin(arq)

        if not metadados:
            print(f"[{i}/{total}] SKIP {rel_path} (pasta ignorada)")
            pulados += 1
            continue

        print(f"[{i}/{total}] {rel_path}")
        print(
            f"         Tipo={metadados['tipo']} | Tema={metadados['tema']} | {metadados['numero']}/{metadados['ano']}"
        )

        try:
            conn.execute("BEGIN TRANSACTION;")

            # 1. Extrair texto
            texto = extrair_texto_pdf(str(arq))
            if not texto or len(texto.strip()) < 50:
                print("         SKIP: texto muito curto ou vazio")
                conn.rollback()
                pulados += 1
                continue

            hash_texto = calcular_hash_texto(texto)

            # 2. Verificar/inserir norma
            cursor.execute(
                "SELECT id FROM normas WHERE tipo=? AND numero=? AND ano=?",
                (metadados["tipo"], metadados["numero"], metadados["ano"]),
            )
            resultado = cursor.fetchone()

            if resultado:
                norma_id = resultado[0]
                cursor.execute(
                    "UPDATE normas SET tema=? WHERE id=?", (metadados["tema"], norma_id)
                )
            else:
                cursor.execute(
                    "INSERT INTO normas (tipo, numero, ano, tema) VALUES (?, ?, ?, ?)",
                    (
                        metadados["tipo"],
                        metadados["numero"],
                        metadados["ano"],
                        metadados["tema"],
                    ),
                )
                norma_id = cursor.lastrowid

            # 3. Verificar versão (dedup por hash)
            cursor.execute(
                "SELECT id, hash_texto FROM versoes_norma WHERE norma_id=? AND vigencia_fim IS NULL",
                (norma_id,),
            )
            versao_atual = cursor.fetchone()

            if versao_atual and versao_atual[1] == hash_texto:
                print("         DEDUP: já existe, pulando")
                conn.rollback()
                pulados += 1
                continue

            if versao_atual:
                cursor.execute(
                    "UPDATE versoes_norma SET vigencia_fim=CURRENT_DATE WHERE id=?",
                    (versao_atual[0],),
                )

            # 4. Inserir nova versão
            cursor.execute(
                "INSERT INTO versoes_norma (norma_id, texto_integral, hash_texto, vigencia_inicio) VALUES (?, ?, ?, CURRENT_DATE)",
                (norma_id, texto, hash_texto),
            )
            nova_versao_id = cursor.lastrowid

            # 5. Chunking & dispositivos
            chunks = quebrar_pdf_em_chunks(texto)
            for identificador, conteudo in chunks:
                hash_disp = calcular_hash_texto(conteudo)
                cursor.execute(
                    "INSERT INTO dispositivos (versao_id, identificador, texto, hash_dispositivo) VALUES (?, ?, ?, ?)",
                    (nova_versao_id, identificador, conteudo, hash_disp),
                )

            conn.commit()
            inseridos += 1
            print(f"         OK: {len(chunks)} chunks inseridos")

        except Exception as e:
            conn.rollback()
            erros += 1
            print(f"         ERRO: {e}")

    conn.close()

    print(f"\n{'=' * 60}")
    print("RESULTADO FINAL")
    print(f"  Inseridos: {inseridos}")
    print(f"  Pulados:   {pulados}")
    print(f"  Erros:     {erros}")
    print(f"{'=' * 60}")
    print("\nPróximo passo: python -m ia_leg.rag.embedding_service")


if __name__ == "__main__":
    ingerir_pdfs_sefin()
