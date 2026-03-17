"""
Converte PDFs normativos em texto bruto.
"""


import fitz  # PyMuPDF
import re

def extrair_texto_pdf(caminho_pdf: str) -> str:
    """Extrai texto de um PDF usando PyMuPDF (fitz), preservando parágrafos curtos."""
    try:
        doc = fitz.open(caminho_pdf)
        texto_completo = []
        
        for pagina in doc:
            texto_pagina = pagina.get_text("text")
            # Opcional: Aqui poderíamos aplicar Regex para remover rodapés comuns se necessário num futuro,
            # como "Secretaria de Estado de Finanças - Página X de Y". 
            
            # Limpa múltiplos espaços/quebras excessivas, mas tenta manter a estrutura de parágrafos/tabelas simples
            texto_pagina = re.sub(r'\n{3,}', '\n\n', texto_pagina)
            texto_completo.append(texto_pagina.strip())
            
        doc.close()
        return "\n\n".join(texto_completo)
    except Exception as e:
        print(f"Erro ao ler PDF {caminho_pdf}: {e}")
        return ""
