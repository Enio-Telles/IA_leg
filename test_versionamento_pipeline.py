import sqlite3
import os
import sys

sys.path.insert(0, ".")

import etl.versionamento_pipeline
from etl.versionamento_pipeline import processar_norma_json, conectar

# Setup a test DB and try processing a test json
def setup_test_db():
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN TRANSACTION;")
    except:
        pass

    # Check if table already exists
    cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='normas'")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            CREATE TABLE sefin_tributos (
                id INTEGER PRIMARY KEY
            )
        ''')
        cursor.execute('''
            CREATE TABLE normas (
                id INTEGER PRIMARY KEY,
                tipo TEXT,
                numero TEXT,
                ano TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE versoes_norma (
                id INTEGER PRIMARY KEY,
                norma_id INTEGER,
                texto_integral TEXT,
                hash_texto TEXT,
                vigencia_inicio TEXT,
                vigencia_fim TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE dispositivos (
                id INTEGER PRIMARY KEY,
                versao_id INTEGER,
                identificador TEXT,
                texto TEXT,
                hash_dispositivo TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE embeddings (
                id INTEGER PRIMARY KEY,
                dispositivo_id INTEGER,
                vetor BLOB,
                modelo TEXT
            )
        ''')
    conn.commit()
    conn.close()

import json
def create_test_json():
    test_json = {
        "texto_html": "<html><body><p>Art. 1º Este é um teste.</p><p>Art. 2º Outro artigo.</p></body></html>",
        "tipo": "Lei",
        "numero": "123",
        "ano": "2026",
        "vigencia_inicio": "2026-01-01"
    }
    with open("test_norma.json", "w") as f:
        json.dump(test_json, f)

# Mock out the vector generation
class MockVetor:
    def tobytes(self):
        return b"mock_vector"

def mock_gerar_embeddings(textos):
    return [MockVetor() for _ in textos]

# Monkeypatch
etl.versionamento_pipeline.gerar_embeddings = mock_gerar_embeddings

setup_test_db()
create_test_json()
processar_norma_json("test_norma.json")

# verify results
conn = conectar()
cursor = conn.cursor()
cursor.execute("SELECT * FROM embeddings")
results = cursor.fetchall()
print(f"Number of embeddings inserted: {len(results)}")
print(results)
conn.close()
