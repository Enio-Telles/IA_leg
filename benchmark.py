import pandas as pd
import time
import numpy as np

# Create a dummy dataframe for df_resultado and versoes
np.random.seed(42)
num_normas = 100
num_versoes = 1000

df_resultado = pd.DataFrame({
    'id': range(num_normas),
    'tipo': ['Decreto'] * num_normas,
    'numero': np.random.randint(1000, 9999, size=num_normas),
    'ano': np.random.randint(2000, 2024, size=num_normas),
    'total_dispositivos': np.random.randint(1, 100, size=num_normas)
})

todas_versoes = pd.DataFrame({
    'id': range(num_versoes),
    'norma_id': np.random.randint(0, num_normas, size=num_versoes),
    'vigencia_inicio': ['2023-01-01'] * num_versoes,
    'vigencia_fim': [np.nan if np.random.rand() > 0.5 else '2024-01-01' for _ in range(num_versoes)],
    'tamanho': np.random.randint(1000, 10000, size=num_versoes),
    'hash_texto': ['abcdef1234567890'] * num_versoes
})

def method_iterrows():
    count = 0
    for _, row in df_resultado.iterrows():
        versoes = todas_versoes[todas_versoes["norma_id"] == row["id"]]
        if not versoes.empty:
            for _, v in versoes.iterrows():
                vigente = "🟢 Vigente" if pd.isna(v["vigencia_fim"]) else f"🔴 Encerrada em {v['vigencia_fim']}"
                count += 1
    return count

def method_itertuples():
    count = 0
    for row in df_resultado.itertuples():
        versoes = todas_versoes[todas_versoes["norma_id"] == row.id]
        if not versoes.empty:
            for v in versoes.itertuples():
                vigente = "🟢 Vigente" if pd.isna(v.vigencia_fim) else f"🔴 Encerrada em {v.vigencia_fim}"
                count += 1
    return count

start = time.time()
method_iterrows()
t_iterrows = time.time() - start

start = time.time()
method_itertuples()
t_itertuples = time.time() - start

print(f"iterrows(): {t_iterrows:.4f}s")
print(f"itertuples(): {t_itertuples:.4f}s")
