"""Diagnóstico detalhado do erro de encoding com GPU."""
import traceback
import sys
import os

# Suppress the CVE warning by acknowledging it
os.environ["TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD_CHECK"] = "1"

import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0)}")

print("\n--- Testando import do modelo ---")
try:
    from sentence_transformers import SentenceTransformer
    print("SentenceTransformer importado OK")
except Exception as e:
    print(f"ERRO no import: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n--- Carregando modelo na GPU ---")
try:
    m = SentenceTransformer("BAAI/bge-m3", device="cuda")
    print(f"Modelo carregado! Device: {m.device}")
except Exception as e:
    print(f"ERRO ao carregar modelo: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n--- Testando encoding ---")
try:
    v = m.encode(["Teste de encoding na GPU"], normalize_embeddings=True, show_progress_bar=False)
    print(f"Encoding OK! Shape: {v.shape}, dtype: {v.dtype}")
except Exception as e:
    print(f"ERRO no encoding: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n--- Testando encoding em lote ---")
try:
    textos = [f"Texto de teste número {i}" for i in range(10)]
    v = m.encode(textos, normalize_embeddings=True, show_progress_bar=True)
    print(f"Encoding em lote OK! Shape: {v.shape}")
except Exception as e:
    print(f"ERRO no encoding em lote: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n✅ TODOS OS TESTES PASSARAM!")
