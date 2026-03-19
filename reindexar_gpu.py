"""Re-indexar com diagnóstico completo."""
import sys
import os
import warnings

# Suprimir warnings do PyTorch/HF
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sqlite3
from ia_leg.core.config.settings import DB_PATH

# Verificar status atual
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
total_disp = c.execute("SELECT COUNT(*) FROM dispositivos").fetchone()[0]
total_emb = c.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
pendentes = c.execute("""
    SELECT COUNT(*) FROM dispositivos d
    LEFT JOIN embeddings e ON d.id = e.dispositivo_id
    WHERE e.id IS NULL
""").fetchone()[0]

print(f"Status atual: {total_emb}/{total_disp} embeddings ({total_emb/total_disp*100:.1f}%)")
print(f"Pendentes: {pendentes}")

if pendentes == 0:
    print("Nada a indexar!")
    conn.close()
    sys.exit(0)

# Carregar modelo
import torch
print(f"\nPyTorch: {torch.__version__} | CUDA: {torch.cuda.is_available()}")

from sentence_transformers import SentenceTransformer
import numpy as np
import time

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Carregando modelo no device: {device}")
modelo = SentenceTransformer("BAAI/bge-m3", device=device)
print(f"Modelo carregado!")

# Testar encoding
v = modelo.encode(["teste"], normalize_embeddings=True)
print(f"Teste encoding OK: shape={v.shape}\n")

# Buscar pendentes
cursor = conn.cursor()
cursor.execute("""
    SELECT d.id, d.texto
    FROM dispositivos d
    LEFT JOIN embeddings e ON d.id = e.dispositivo_id
    WHERE e.id IS NULL
""")
resultados = cursor.fetchall()

MODELO_NOME = "BAAI/bge-m3"
LOTE = 16
total = len(resultados)
total_lotes = (total + LOTE - 1) // LOTE
processados = 0
erros = 0
inicio = time.time()

print(f"Indexando {total} dispositivos em {total_lotes} lotes...")

for i in range(0, total, LOTE):
    lote = resultados[i:i + LOTE]
    ids = [r[0] for r in lote]
    textos = [r[1] for r in lote]
    lote_num = i // LOTE + 1

    try:
        t0 = time.time()
        vetores = modelo.encode(textos, show_progress_bar=False, normalize_embeddings=True)
        dt = time.time() - t0

        conn.execute("BEGIN TRANSACTION;")
        for id_disp, vetor in zip(ids, vetores):
            cursor.execute(
                "INSERT INTO embeddings (dispositivo_id, vetor, modelo) VALUES (?, ?, ?)",
                (id_disp, vetor.astype(np.float32).tobytes(), MODELO_NOME)
            )
        conn.commit()

        processados += len(lote)
        vel = processados / (time.time() - inicio)
        restantes = total - processados
        eta = restantes / vel if vel > 0 else 0
        print(f"[Lote {lote_num}/{total_lotes}] {processados}/{total} | {dt:.1f}s | {vel:.1f} txt/s | ETA: {eta/60:.0f}min")

    except Exception as e:
        conn.rollback()
        erros += 1
        print(f"[Lote {lote_num}/{total_lotes}] ERRO: {type(e).__name__}: {e}")

conn.close()
tempo_total = time.time() - inicio
print(f"\nFINALIZADO: {processados}/{total} processados | {erros} erros | {tempo_total/60:.1f} min")
