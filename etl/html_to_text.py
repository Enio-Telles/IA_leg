"""
Converte HTML bruto em texto simples.
"""

from html.parser import HTMLParser

try:
    from bs4 import BeautifulSoup
except ImportError:
    pass


class _FallbackHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []

    def handle_data(self, data):
        self.text_parts.append(data)

    def get_text(self):
        return "\n".join(self.text_parts)


def extrair_texto_html(html_content: str) -> str:
    """Extrai texto limpo de um conteúdo HTML."""
    if not html_content:
        return ""

    try:
        soup = BeautifulSoup(html_content, "html.parser")
        texto = soup.get_text(separator="\n")
    except NameError:
        # Fallback caso bs4 não esteja instalado
        parser = _FallbackHTMLParser()
        parser.feed(html_content)
        texto = parser.get_text()

    # Limpeza básica
    linhas = [linha.strip() for linha in texto.split("\n") if linha.strip()]
    return "\n".join(linhas)
