"""
Teste rápido do módulo de busca semântica (RAG Retriever).
"""
import sys
sys.path.insert(0, ".")

from ia_leg.rag.retriever import recuperar_contexto

print("=" * 60)
print("TESTE DO RETRIEVER - Busca Semantica")
print("=" * 60)

query = "prazo recolhimento ICMS"
print(f"\nQuery: '{query}'\n")

# Atualizado: recuperar_contexto agora retorna (resultados, tempo_ms)
results, tempo_ms = recuperar_contexto(query, top_k=5)

if not results:
    print("Nenhum resultado encontrado. Verifique se existem embeddings no banco.")
else:
    for i, r in enumerate(results, 1):
        print(f"--- Resultado {i} ---")
        print(f"Score: {r['score']:.4f}")
        print(f"Norma: {r['norma']}")
        print(f"Dispositivo: {r['identificador']}")
        print(f"Texto: {r['texto'][:150]}...")
        print()

print(f"Total de resultados retornados: {len(results)}")
print(f"Tempo de busca: {tempo_ms:.2f}ms")
