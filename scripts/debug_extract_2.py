import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from etl.pdf_to_text import extrair_texto_pdf

data = {}

try:
    pdf_camara1 = r"c:\Users\eniot\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\IA_leg\documentos\pdf\Camara_Plena_tate\2024\Decisoes_02_2024\PAT_20133000200064.pdf"
    texto_camara = extrair_texto_pdf(pdf_camara1)
    data["camara_pat20133000200064"] = texto_camara
except Exception:
    pass

try:
    pdf_sumula2 = r"c:\Users\eniot\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\IA_leg\documentos\pdf\Sumulas_tate\Sumula_02_TATE_RO.pdf"
    texto_sumula = extrair_texto_pdf(pdf_sumula2)
    data["sumula_2"] = texto_sumula
except Exception:
    pass

try:
    pdf_sumula3 = r"c:\Users\eniot\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\IA_leg\documentos\pdf\Sumulas_tate\Sumula_03_TATE_RO.pdf"
    texto_sumula = extrair_texto_pdf(pdf_sumula3)
    data["sumula_3"] = texto_sumula
except Exception:
    pass


with open('debug_extract_2.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
