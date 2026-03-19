"""
Serviço parametrizável de geração de embeddings para documentos jurídicos.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import sqlite3
import numpy as np
import warnings
from typing import List, Optional

# Suprimir FutureWarning do PyTorch sobre CVE-2025-32434
# (modelo BGE-M3 é confiável e já foi verificado)
warnings.filterwarnings("ignore", message=".*CVE-2025-32434.*")
warnings.filterwarnings("ignore", category=FutureWarning, module="torch")

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from ia_leg.core.config.settings import DB_PATH, EMBEDDING_MODEL

# Modelos Predefinidos
MODELO_FAST = "sentence-transformers/all-MiniLM-L6-v2"
MODELO_PRECISE = "BAAI/bge-m3"

# Inicialização Lazy do modelo para não pesar memória se não for chamado
_MODELO = None
_MODELO_NOME_ATUAL = None

def get_device(device_param: Optional[str] = None) -> str:
    """Retorna o device (cpu/cuda) explícito ou inferido."""
    if device_param:
        return device_param
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"

def carregar_modelo(model_name: Optional[str] = None, device: Optional[str] = None, force_reload: bool = False):
    """Carrega o modelo de embeddings (parametrizável)."""
    global _MODELO, _MODELO_NOME_ATUAL

    # Resolver o modelo alvo
    target_model = model_name or EMBEDDING_MODEL

    if force_reload or _MODELO is None or _MODELO_NOME_ATUAL != target_model:
        if SentenceTransformer is None:
            raise ImportError(
                "Instale 'sentence-transformers' para usar gerar_embeddings()"
            )

        target_device = get_device(device)
        print(f"Carregando modelo {target_model} no dispositivo: {target_device}")

        if target_device == "cuda":
            import torch
            try:
                print(f"  GPU: {torch.cuda.get_device_name(0)} ({torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB VRAM)")
            except Exception:
                pass

        _MODELO = SentenceTransformer(target_model, device=target_device)
        _MODELO_NOME_ATUAL = target_model

    return _MODELO


def gerar_embeddings(textos: List[str], model_name: Optional[str] = None, device: Optional[str] = None, batch_size: int = 32) -> List[np.ndarray]:
    """Gera vetores a partir de uma lista de textos."""
    if not textos:
        return []

    modelo = carregar_modelo(model_name=model_name, device=device)
    print(f"Gerando embeddings para {len(textos)} textos (batch_size={batch_size})...")

    vetores = modelo.encode(
        textos,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True
    )
    return vetores


def indexar_dispositivos_sem_vetor(tamanho_lote: int = 16, model_name: Optional[str] = None, device: Optional[str] = None):
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

    target_model = model_name or EMBEDDING_MODEL
    total = len(resultados)
    total_lotes = (total + tamanho_lote - 1) // tamanho_lote
    print(f"{'='*60}")
    print(f"INDEXAÇÃO VETORIAL MASSIVA")
    print(f"Modelo: {target_model}")
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
            # Usamos gerar_embeddings passando as configurações parametrizadas
            vetores = gerar_embeddings(textos_lote, model_name=target_model, device=device, batch_size=tamanho_lote)
            tempo_lote = time.time() - inicio_lote

            # Persistir
            # Melhorador: Batch insert to prevent N+1 query latency
            dados_embeddings = [
                (id_disp, vetor.astype(np.float32).tobytes(), target_model)
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
