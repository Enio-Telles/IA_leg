import pytest
from unittest.mock import patch
from etl.html_to_text import extrair_texto_html

def test_extrair_texto_html_happy_path():
    """Testa a extração básica de texto HTML."""
    html = "<html><body><h1>Título</h1><p>Parágrafo 1.</p><div><p>Parágrafo 2.</p></div></body></html>"
    resultado = extrair_texto_html(html)

    assert "Título" in resultado
    assert "Parágrafo 1." in resultado
    assert "Parágrafo 2." in resultado
    assert "<html>" not in resultado
    assert resultado.count("\n") >= 2

def test_extrair_texto_html_empty_and_none():
    """Testa os edge cases de string vazia e None."""
    assert extrair_texto_html("") == ""
    assert extrair_texto_html(None) == ""

def test_extrair_texto_html_fallback():
    """Testa o fallback (sem bs4) simulando NameError no BeautifulSoup."""
    html = "<html><body><h1>Título</h1><p>Parágrafo 1.</p></body></html>"

    # Mock para forçar a exceção NameError quando BeautifulSoup for chamado
    with patch("etl.html_to_text.BeautifulSoup", side_effect=NameError("name 'BeautifulSoup' is not defined")):
        resultado = extrair_texto_html(html)

        assert "Título" in resultado
        assert "Parágrafo 1." in resultado
        assert "<html>" not in resultado
        assert "<body>" not in resultado
        assert "<h1>" not in resultado

def test_extrair_texto_html_only_tags():
    """Testa o comportamento com HTML que só tem tags e não texto."""
    html = "<div><span><br></span></div>"
    assert extrair_texto_html(html) == ""

def test_extrair_texto_html_whitespace_handling():
    """Testa o manuseio de espaços em branco extras."""
    html = "<p>  Texto   com   espaços  </p>\n\n<p>\tMais texto\n\n</p>"
    resultado = extrair_texto_html(html)
    assert "Texto   com   espaços" in resultado
    assert "Mais texto" in resultado
