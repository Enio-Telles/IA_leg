"""
Pipeline automático de versionamento normativo.
Responsável por manter integridade histórica e consistência temporal.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
import hashlib

from ia_leg.core.config.settings import DB_PATH
import json
from etl.html_to_text import extrair_texto_html
from etl.normalizador import extrair_metadados

# -------------------------------------------------
# UTILITÁRIOS
# -------------------------------------------------


def calcular_hash_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# -------------------------------------------------
# COMPARADOR ESTRUTURAL
# -------------------------------------------------


def mapear_dispositivos_por_identificador(dispositivos):
    """
    Converte lista [(id, texto)] em dict estruturado
    { identificador: {texto, hash} }
    """
    estrutura = {}

    for identificador, texto in dispositivos:
        estrutura[identificador] = {
            "texto": texto,
            "hash": calcular_hash_texto(texto),
        }

    return estrutura


def comparar_estruturalmente(dispositivos_antigos, dispositivos_novos):
    """
    Compara versões artigo a artigo.

    Retorna dict com:
    - mantidos
    - alterados
    - revogados
    - incluidos
    """

    antigos = mapear_dispositivos_por_identificador(dispositivos_antigos)
    novos = mapear_dispositivos_por_identificador(dispositivos_novos)

    mantidos = []
    alterados = []
    revogados = []
    incluidos = []

    # Verificar antigos
    for ident, dados_antigos in antigos.items():
        if ident not in novos:
            revogados.append(ident)
        else:
            if dados_antigos["hash"] == novos[ident]["hash"]:
                mantidos.append(ident)
            else:
                alterados.append(ident)

    # Verificar novos
    for ident in novos.keys():
        if ident not in antigos:
            incluidos.append(ident)

    return {
        "mantidos": mantidos,
        "alterados": alterados,
        "revogados": revogados,
        "incluidos": incluidos,
    }


def persistir_diff(
    cursor,
    versao_origem_id,
    versao_destino_id,
    dispositivos_antigos,
    dispositivos_novos,
    resultado_diff,
):

    antigos_map = mapear_dispositivos_por_identificador(dispositivos_antigos)
    novos_map = mapear_dispositivos_por_identificador(dispositivos_novos)

    dados_insercao = []

    for ident in resultado_diff.get("mantidos", []):
        dados_insercao.append(
            (
                versao_origem_id,
                versao_destino_id,
                ident,
                "mantido",
                antigos_map[ident]["hash"],
                novos_map[ident]["hash"],
            )
        )

    for ident in resultado_diff.get("alterados", []):
        dados_insercao.append(
            (
                versao_origem_id,
                versao_destino_id,
                ident,
                "alterado",
                antigos_map[ident]["hash"],
                novos_map[ident]["hash"],
            )
        )

    for ident in resultado_diff.get("revogados", []):
        dados_insercao.append(
            (
                versao_origem_id,
                versao_destino_id,
                ident,
                "revogado",
                antigos_map[ident]["hash"],
                None,
            )
        )

    for ident in resultado_diff.get("incluidos", []):
        dados_insercao.append(
            (
                versao_origem_id,
                versao_destino_id,
                ident,
                "incluido",
                None,
                novos_map[ident]["hash"],
            )
        )

    if dados_insercao:
        cursor.executemany(
            """
            INSERT INTO diff_estrutural (
                versao_origem_id,
                versao_destino_id,
                identificador,
                tipo_alteracao,
                hash_anterior,
                hash_novo
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            dados_insercao,
        )


# -------------------------------------------------
# FUNÇÃO PRINCIPAL
# -------------------------------------------------


def processar_norma_json(caminho_json: str):
    """
    Executa pipeline completo lendo de JSON:
    - Lê JSON e extrai metadados
    - Extrai texto do HTML
    - Versiona corretamente
    - Atualiza dispositivos
    - Reindexa embeddings
    """

    conn = conectar()
    cursor = conn.cursor()

    try:
        conn.execute("BEGIN TRANSACTION;")

        # 1️⃣ Ler JSON e extrair texto e metadados
        with open(caminho_json, "r", encoding="utf-8") as f:
            dados = json.load(f)

        texto = extrair_texto_html(dados.get("texto_html", ""))
        metadados = extrair_metadados(dados)

        tipo = metadados["tipo"]
        numero = metadados["numero"]
        ano = metadados["ano"]
        vigencia_inicio = metadados["vigencia_inicio"]

        hash_texto = calcular_hash_texto(texto)

        # 2️⃣ Verificar ou inserir norma
        cursor.execute(
            "SELECT id FROM normas WHERE tipo=? AND numero=? AND ano=?",
            (tipo, numero, ano),
        )
        resultado = cursor.fetchone()

        if resultado:
            norma_id = resultado[0]
        else:
            cursor.execute(
                "INSERT INTO normas (tipo, numero, ano) VALUES (?, ?, ?)",
                (tipo, numero, ano),
            )
            norma_id = cursor.lastrowid

        # 3️⃣ Verificar versão existente
        cursor.execute(
            """
            SELECT id, hash_texto
            FROM versoes_norma
            WHERE norma_id=? AND vigencia_fim IS NULL
            """,
            (norma_id,),
        )
        versao_atual = cursor.fetchone()

        if versao_atual and versao_atual[1] == hash_texto:
            print("Nenhuma alteração detectada.")
            conn.rollback()
            return

        dispositivos_antigos = []
        if versao_atual:
            # Buscar dispositivos da versão anterior para comparação estrutural
            cursor.execute(
                "SELECT identificador, texto FROM dispositivos WHERE versao_id=?",
                (versao_atual[0],),
            )
            dispositivos_antigos = cursor.fetchall()

        # 4️⃣ Encerrar vigência anterior
        if versao_atual:
            cursor.execute(
                """
                UPDATE versoes_norma
                SET vigencia_fim=?
                WHERE id=?
                """,
                (vigencia_inicio, versao_atual[0]),
            )

        # 5️⃣ Inserir nova versão
        cursor.execute(
            """
            INSERT INTO versoes_norma (
                norma_id,
                texto_integral,
                hash_texto,
                vigencia_inicio
            ) VALUES (?, ?, ?, ?)
            """,
            (norma_id, texto, hash_texto, vigencia_inicio),
        )

        nova_versao_id = cursor.lastrowid

        # 6️⃣ Reconstruir dispositivos
        dispositivos_novos_list = quebrar_dispositivos(texto)

        # Comparação estrutural:
        if versao_atual:
            resultado_diff = comparar_estruturalmente(
                dispositivos_antigos, dispositivos_novos_list
            )
            persistir_diff(
                cursor,
                versao_atual[0],
                nova_versao_id,
                dispositivos_antigos,
                dispositivos_novos_list,
                resultado_diff,
            )

        # Melhorador: Batch insert to prevent N+1 query latency
        dados_dispositivos = [
            (nova_versao_id, identificador, conteudo, calcular_hash_texto(conteudo))
            for identificador, conteudo in dispositivos_novos_list
        ]
        if dados_dispositivos:
            cursor.executemany(
                """
                INSERT INTO dispositivos (
                    versao_id,
                    identificador,
                    texto,
                    hash_dispositivo
                ) VALUES (?, ?, ?, ?)
                """,
                dados_dispositivos,
            )

        # 7️⃣ Gerar embeddings (Comentado para processamento em massa mais rápido)
        # Recomenda-se rodar -m ia_leg.rag.embedding_service separadamente após o ETL total.
        """
        cursor.execute(
            "SELECT id, texto FROM dispositivos WHERE versao_id=?",
            (nova_versao_id,),
        )
        novos_dispositivos_banco = cursor.fetchall()
        
        textos = [d[1] for d in novos_dispositivos_banco]
        if textos:
            vetores = gerar_embeddings(textos)
            if vetores:
                for (disp_id, _), vetor in zip(novos_dispositivos_banco, vetores):
                    cursor.execute(
                        \"\"\"
                        INSERT INTO embeddings (dispositivo_id, vetor, modelo)
                        VALUES (?, ?, ?)
                        \"\"\",
                        (disp_id, vetor.tobytes(), "bge-m3"),
                    )
        """

        conn.commit()
        print("Versionamento concluído com sucesso.")

    except Exception as e:
        conn.rollback()
        print("Erro no pipeline:", e)
        raise

    finally:
        conn.close()


# -------------------------------------------------
# QUEBRA DE DISPOSITIVOS
# -------------------------------------------------


def quebrar_pdf_em_chunks(
    texto: str, tamanho_maximo: int = 1500, sobreposicao: int = 200
):
    """
    Divide textos genéricos (Manuais, Pareceres) em chunks menores para vetorização.
    Tenta quebrar em parágrafos e agrupa até o tamanho máximo (+sobreposição).
    """
    paragrafos = texto.split("\n\n")
    chunks = []
    chunk_atual = ""
    contador = 1

    for p in paragrafos:
        p = p.strip()
        if not p:
            continue

        if len(chunk_atual) + len(p) < tamanho_maximo:
            chunk_atual += p + "\n\n"
        else:
            # Chunk atingiu o limite, salva
            if chunk_atual:
                chunks.append((f"Trecho {contador}", chunk_atual.strip()))
                contador += 1

            # Sobreposição puxa as palavras finais do chunk anterior
            palavras = chunk_atual.split()
            pedaco_sobreposicao = " ".join(palavras[-sobreposicao:]) if palavras else ""

            chunk_atual = pedaco_sobreposicao + "\n\n" + p + "\n\n"

    # Salvar o último
    if chunk_atual.strip():
        chunks.append((f"Trecho {contador}", chunk_atual.strip()))

    return chunks


def quebrar_dispositivos(texto: str):
    """
    Divide texto em dispositivos jurídicos básicos.
    Estratégia simples baseada em 'Art.'
    Pode evoluir para parser mais sofisticado.
    """
    partes = texto.split("Art.")
    dispositivos = []

    for parte in partes[1:]:
        identificador = "Art. " + parte.split("\n")[0].strip()
        conteudo = "Art." + parte
        dispositivos.append((identificador, conteudo.strip()))

    return dispositivos


if __name__ == "__main__":
    from ia_leg.core.config.settings import BASE_DIR

    text_dir = Path(BASE_DIR) / "documentos" / "texto"
    arquivos = list(text_dir.glob("*.json"))

    print(f"Iniciando processamento ETL de {len(arquivos)} arquivos JSON.")
    for arq in arquivos:
        try:
            print("----------------------------------------")
            print(f"Processando {arq.name}...")
            processar_norma_json(str(arq))
        except Exception as e:
            import traceback

            print(f"Falha ao processar {arq.name}: {e}")
            traceback.print_exc()
