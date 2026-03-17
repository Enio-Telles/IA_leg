import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from etl.pdf_to_text import extrair_texto_pdf

try:
    pdf_camara = r"c:\Users\eniot\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\IA_leg\documentos\pdf\Camara_Plena_tate\2024\Decisoes_02_2024\PAT_20133000200064.pdf"
    texto_camara = extrair_texto_pdf(pdf_camara)
    print("--- CAMARA PLENA ---")
    print(repr(texto_camara[:1000]))
except Exception as e:
    print(f"Error on Camara: {e}")

try:
    pdf_sumula = r"c:\Users\eniot\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\IA_leg\documentos\pdf\Sumulas_tate\Sumula_01_TATE_RO.pdf"
    texto_sumula = extrair_texto_pdf(pdf_sumula)
    print("--- SUMULA ---")
    print(repr(texto_sumula[:1000]))
except Exception as e:
    print(f"Error on Sumula: {e}")
