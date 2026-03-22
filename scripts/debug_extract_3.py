import sys
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from etl.pdf_to_text import extrair_texto_pdf

data = {}

def extract_sumula(texto, num_sumula):
    padrao = rf"(SÚMULA\s*0?{num_sumula}.*?Presidente do TATE/SEFIN)"
    match = re.search(padrao, texto, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return "NAO ENCONTRADO"

def extract_ementa(texto):
    padrao = r"(EMENTA:?.*?(?:ACÓRDÃO|Vistos, relatados e discutidos|DECISÃO))"
    match = re.search(padrao, texto, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return "NAO ENCONTRADO"

try:
    pdf_camara1 = r"c:\Users\eniot\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\IA_leg\documentos\pdf\Camara_Plena_tate\2024\Decisoes_02_2024\PAT_20133000200064.pdf"
    texto_camara = extrair_texto_pdf(pdf_camara1)
    data["camara_pat20133000200064"] = extract_ementa(texto_camara)
except Exception:
    pass

try:
    with open('debug_extract.json', 'r', encoding='utf-8') as f:
        d1 = json.load(f)
        texto_sumula1 = d1.get("sumula", "")
        data["sumula_1"] = extract_sumula(texto_sumula1, "1")
except Exception:
    pass

try:
    with open('debug_extract_2.json', 'r', encoding='utf-8') as f:
        d2 = json.load(f)
        texto_sumula2 = d2.get("sumula_2", "")
        data["sumula_2"] = extract_sumula(texto_sumula2, "2")
        texto_sumula3 = d2.get("sumula_3", "")
        data["sumula_3"] = extract_sumula(texto_sumula3, "3")
except Exception:
    pass


with open('debug_extract_3.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
