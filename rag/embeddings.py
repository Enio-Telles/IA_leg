"""
Geração de embeddings para documentos jurídicos.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
import numpy as np
import warnings
from typing import List

# Suprimir FutureWarning do PyTorch sobre CVE-2025-32434
# (modelo BGE-M3 é confiável e já foi verificado)
warnings.filterwarnings("ignore", message=".*CVE-2025-32434.*")
warnings.filterwarnings("ignore", category=FutureWarning, module="torch")

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from config import DB_PATH

# Inicialização Lazy do modelo para não pesar memória se não for chamado
_MODELO = None
MODELO_NOME = "BAAI/bge-m3"


def carregar_modelo():
    """Carrega o modelo BGE-M3 (multilíngue forte para contextos longos).
    Usa GPU automaticamente se CUDA estiver disponível."""
    global _MODELO
    if _MODELO is None:
        if SentenceTransformer is None:
            raise ImportError(
                "Instale 'sentence-transformers' para usar gerar_embeddings()"
            )

        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Carregando modelo {MODELO_NOME} no dispositivo: {device}")
        if device == "cuda":
            print(
                f"  GPU: {torch.cuda.get_device_name(0)} ({torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB VRAM)"
            )
        _MODELO = SentenceTransformer(MODELO_NOME, device=device)
    return _MODELO


def gerar_embeddings(textos: List[str]) -> List[np.ndarray]:
    """Gera vetores a partir de uma lista de textos."""
    if not textos:
        return []

    modelo = carregar_modelo()
    # Para o bge-m3, usamos o encoder básico
    print(f"Gerando embeddings para {len(textos)} textos...")
    vetores = modelo.encode(textos, show_progress_bar=True, normalize_embeddings=True)
    return vetores


def indexar_dispositivos_sem_vetor(tamanho_lote: int = 16):
    """
    Busca no banco de dados dispositivos que ainda não possuem embeddings,
    gera seus vetores e os persiste no SQLite.
    Otimizado para processamento massivo com progresso e ETA.
    """
    import time

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Busca IDs e textos de dispositivos que não existam na tabela embeddings
    cursor.execute("""
        SELECT d.id, d.texto 
        FROM dispositivos d
        LEFT JOIN embeddings e ON d.id = e.dispositivo_id
        WHERE e.id IS NULL
    """)
    resultados = cursor.fetchall()

    if not resultados:
        print("Nenhum dispositivo novo precisando de indexação vetorial.")
        conn.close()
        return

    total = len(resultados)
    total_lotes = (total + tamanho_lote - 1) // tamanho_lote
    print(f"{'='*60}")
    print(f"INDEXAÇÃO VETORIAL MASSIVA")
    print(f"Dispositivos pendentes: {total}")
    print(f"Tamanho do lote: {tamanho_lote}")
    print(f"Total de lotes: {total_lotes}")
    print(f"{'='*60}")

    processados = 0
    erros = 0
    inicio_geral = time.time()

    for i in range(0, total, tamanho_lote):
        lote = resultados[i : i + tamanho_lote]
        ids_lote = [row[0] for row in lote]
        textos_lote = [row[1] for row in lote]
        lote_num = i // tamanho_lote + 1

        try:
            inicio_lote = time.time()
            vetores = gerar_embeddings(textos_lote)
            tempo_lote = time.time() - inicio_lote

            # Persistir
            # Melhorador: Batch insert to prevent N+1 query latency
            dados_embeddings = [
                (id_disp, vetor.astype(np.float32).tobytes(), MODELO_NOME)
                for id_disp, vetor in zip(ids_lote, vetores)
            ]
            conn.execute("BEGIN TRANSACTION;")
            if dados_embeddings:
                cursor.executemany(
                    """
                    INSERT INTO embeddings (dispositivo_id, vetor, modelo)
                    VALUES (?, ?, ?)
                    """,
                    dados_embeddings,
                )
            conn.commit()

            processados += len(lote)
            tempo_total = time.time() - inicio_geral
            velocidade = processados / tempo_total  # textos/seg
            restantes = total - processados - (erros * tamanho_lote)
            eta_seg = restantes / velocidade if velocidade > 0 else 0
            eta_min = eta_seg / 60

            print(
                f"[Lote {lote_num}/{total_lotes}] {processados}/{total} vetores | "
                f"{tempo_lote:.1f}s/lote | "
                f"ETA: {eta_min:.0f}min | "
                f"Vel: {velocidade:.1f} txt/s"
            )

        except Exception as e:
            conn.rollback()
            erros += 1
            print(f"[Lote {lote_num}/{total_lotes}] ERRO: {e} (continuando...)")
            continue  # Pular lote com erro em vez de abortar tudo

    conn.close()
    tempo_final = time.time() - inicio_geral
    print(f"\n{'='*60}")
    print(f"VETORIZAÇÃO FINALIZADA")
    print(f"Processados: {processados}/{total}")
    print(f"Erros: {erros} lotes")
    print(f"Tempo total: {tempo_final/60:.1f} minutos")
    print(f"{'='*60}")


if __name__ == "__main__":
    indexar_dispositivos_sem_vetor()
