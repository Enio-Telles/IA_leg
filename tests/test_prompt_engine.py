"""
Teste do Prompt Engine com fallback (sem Ollama rodando).
"""
import sys
sys.path.insert(0, ".")

from ia_leg.rag.answer_engine import consultar

print("=" * 60)
print("TESTE DO PROMPT ENGINE")
print("=" * 60)

query = "prazo recolhimento ICMS"
print(f"\nQuery: '{query}'\n")

resposta = consultar(query, top_k=3, backend="ollama")

print("\n" + "=" * 60)
print("RESPOSTA:")
print("=" * 60)
print(resposta)
