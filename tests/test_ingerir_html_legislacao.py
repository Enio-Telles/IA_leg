import pytest
from scripts.ingerir_html_legislacao import extrair_numero_identificador

def test_extrair_numero_identificador_com_ano():
    """Testa identificadores com número e ano completos (4 dígitos)."""
    assert extrair_numero_identificador("D 31274/2026") == ("31274", 2026)
    assert extrair_numero_identificador("IN 15/2018") == ("15", 2018)
    assert extrair_numero_identificador("Portaria nº 42/2023") == ("42", 2023)

def test_extrair_numero_identificador_sem_ano():
    """Testa identificadores apenas com número, devendo retornar o ano padrão (2024)."""
    assert extrair_numero_identificador("Lei 12345") == ("12345", 2024)
    assert extrair_numero_identificador("12345") == ("12345", 2024)
    assert extrair_numero_identificador("Decreto nº 8") == ("8", 2024)

def test_extrair_numero_identificador_ano_incompleto():
    """Testa identificadores com ano de 2 dígitos, onde a regex falhará na primeira e pegará o número."""
    # O regex r"(\d+)[/](\d{4})" precisa de 4 dígitos pro ano.
    # Em "Decreto 123/20", ele não pega "123/20" com a primeira,
    # então cai no fallback e pega "123", retornando ano 2024.
    assert extrair_numero_identificador("Decreto 123/20") == ("123", 2024)

def test_extrair_numero_identificador_sem_numeros():
    """Testa identificadores sem qualquer número, devendo retornar o texto original e o ano padrão."""
    assert extrair_numero_identificador("Constituição Federal") == ("Constituição Federal", 2024)
    assert extrair_numero_identificador("Sem Numero") == ("Sem Numero", 2024)
    assert extrair_numero_identificador("") == ("", 2024)
