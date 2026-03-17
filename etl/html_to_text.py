"""
Converte HTML bruto em texto simples.
"""
import re

try:
    from bs4 import BeautifulSoup
except ImportError:
    pass

def extrair_texto_html(html_content: str) -> str:
    """Extrai texto limpo de um conteúdo HTML."""
    if not html_content:
        return ""
    
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        texto = soup.get_text(separator="\n")
    except NameError:
        # Fallback caso bs4 não esteja instalado
        texto = re.sub(r'<[^>]+>', '\n', html_content)
    
    # Limpeza básica
    linhas = [linha.strip() for linha in texto.split('\n') if linha.strip()]
    return "\n".join(linhas)
