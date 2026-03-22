import sys
from pathlib import Path

# Adiciona o diretório principal para encontrar o módulo 'ia_leg'
sys.path.insert(0, str(Path(__file__).resolve().parent))

import time
import sqlite3
import hashlib

def mock_calcular_hash_texto(texto):
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()

# Substituir calcular_hash_texto do mock
import scripts.ingerir_html_legislacao as ihl
ihl.calcular_hash_texto = mock_calcular_hash_texto

def setup_db():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE normas (
        id INTEGER PRIMARY KEY, tipo TEXT, numero TEXT, ano INTEGER, tema TEXT
    )''')
    cursor.execute('''
    CREATE TABLE versoes_norma (
        id INTEGER PRIMARY KEY, norma_id INTEGER, texto_integral TEXT, hash_texto TEXT, vigencia_inicio TEXT, vigencia_fim TEXT
    )''')
    cursor.execute('''
    CREATE TABLE dispositivos (
        id INTEGER PRIMARY KEY, versao_id INTEGER, identificador TEXT, texto TEXT, hash_dispositivo TEXT
    )''')
    conn.commit()
    return conn

# Mock quebrar_pdf_em_chunks
def mock_quebrar_pdf_em_chunks(texto):
    return [(f"ident_{i}", f"conteudo_{i}" * 10) for i in range(10000)]

def run_benchmark():
    # Override chunking for the test
    original_chunking = ihl.quebrar_pdf_em_chunks
    ihl.quebrar_pdf_em_chunks = mock_quebrar_pdf_em_chunks

    conn = setup_db()
    cursor = conn.cursor()

    start_time = time.time()

    # 2. Verificar/inserir norma
    tipo, numero, ano, tema_auto, texto_completo, hash_texto = "tipo_teste", "123", 2024, "tema_teste", "texto "*10, "hash_texto"

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
        status = "pulado"
    else:
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

        # 5. Chunking (Optimized Batch Insert)
        chunks = ihl.quebrar_pdf_em_chunks(texto_completo)

        dados_dispositivos = [
            (nova_versao_id, ident, conteudo, mock_calcular_hash_texto(conteudo))
            for ident, conteudo in chunks
        ]

        if dados_dispositivos:
            cursor.executemany(
                "INSERT INTO dispositivos (versao_id, identificador, texto, hash_dispositivo) VALUES (?, ?, ?, ?)",
                dados_dispositivos,
            )

    end_time = time.time()
    print(f"Time taken (Batch Query): {end_time - start_time:.4f} seconds")

    conn.close()
    ihl.quebrar_pdf_em_chunks = original_chunking

if __name__ == "__main__":
    run_benchmark()
