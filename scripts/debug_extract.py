import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from etl.pdf_to_text import extrair_texto_pdf

data = {}

try:
    pdf_camara = r"c:\Users\eniot\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\IA_leg\documentos\pdf\Camara_Plena_tate\2024\Decisoes_02_2024\PAT_20133000200064.pdf"
    texto_camara = extrair_texto_pdf(pdf_camara)
    data["camara"] = texto_camara[:1500]
except Exception as e:
    data["camara_error"] = str(e)

try:
    pdf_sumula = r"c:\Users\eniot\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\IA_leg\documentos\pdf\Sumulas_tate\Sumula_01_TATE_RO.pdf"
    texto_sumula = extrair_texto_pdf(pdf_sumula)
    data["sumula"] = texto_sumula[:1500]
except Exception as e:
    data["sumula_error"] = str(e)

with open('debug_extract.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
