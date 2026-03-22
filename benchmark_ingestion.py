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

    ihl.salvar_documento_bd(
        cursor, "tipo_teste", "123", 2024, "tema_teste", "texto "*10, "hash_texto"
    )

    end_time = time.time()
    print(f"Time taken (N+1 query): {end_time - start_time:.4f} seconds")

    conn.close()
    ihl.quebrar_pdf_em_chunks = original_chunking

if __name__ == "__main__":
    run_benchmark()
