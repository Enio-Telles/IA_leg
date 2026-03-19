import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ia_leg.rag.answer_engine import consultar

pergunta = "Qual o entendimento do TATE sobre a decadência do crédito tributário?"
resposta = consultar(pergunta, top_k=3)

print("--- RESPOSTA ---")
print(resposta)
