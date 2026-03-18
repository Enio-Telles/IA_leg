import pytest
from etl.normalizador import extrair_metadados

def test_extrair_metadados_tipos_conhecidos():
    casos = [
        ("D 123/2023", "Decreto", "123"),
        ("L 456/2023", "Lei", "456"),
        ("LC 789/2023", "Lei Complementar", "789"),
        ("IN 12/2023", "Instrução Normativa", "12"),
        ("R 34/2023", "Resolução", "34"),
        ("P 56/2023", "Portaria", "56"),
        ("C 78/2023", "Convênio", "78")
    ]

    for identificador, tipo_esperado, numero_esperado in casos:
        dados = {"identificador": identificador}
        resultado = extrair_metadados(dados)
        assert resultado["tipo"] == tipo_esperado
        assert resultado["numero"] == numero_esperado

def test_extrair_metadados_tipo_desconhecido():
    dados = {"identificador": "X 999/2023"}
    resultado = extrair_metadados(dados)
    assert resultado["tipo"] == "X"
    assert resultado["numero"] == "999"

def test_extrair_metadados_sem_espaco():
    dados = {"identificador": "12345/2023"}
    resultado = extrair_metadados(dados)
    assert resultado["tipo"] == "Desconhecido"
    assert resultado["numero"] == "12345/2023"

def test_extrair_metadados_numero_sem_ano():
    dados = {"identificador": "D 12345"}
    resultado = extrair_metadados(dados)
    assert resultado["tipo"] == "Decreto"
    assert resultado["numero"] == "12345"

def test_extrair_metadados_conversao_data():
    dados = {"publicado_em": "19/02/2026"}
    resultado = extrair_metadados(dados)
    assert resultado["data_publicacao"] == "2026-02-19"
    assert resultado["vigencia_inicio"] == "2026-02-19"

def test_extrair_metadados_data_invalida_ou_diferente():
    dados1 = {"publicado_em": "02/2026"}
    assert extrair_metadados(dados1)["data_publicacao"] == "02/2026"

    dados2 = {"publicado_em": "2026-02-19"}
    assert extrair_metadados(dados2)["data_publicacao"] == "2026-02-19"

    dados3 = {"publicado_em": ""}
    assert extrair_metadados(dados3)["data_publicacao"] == ""

def test_extrair_metadados_dicionario_vazio():
    resultado = extrair_metadados({})
    assert resultado["tipo"] == "Desconhecido"
    assert resultado["numero"] == ""
    assert resultado["ano"] is None
    assert resultado["data_publicacao"] == ""
    assert resultado["vigencia_inicio"] == ""
    assert resultado["titulo"] == ""

def test_extrair_metadados_todos_campos():
    dados = {
        "identificador": "D 123/2023",
        "publicado_em": "01/02/2023",
        "ano": 2023,
        "titulo": "Decreto de Teste"
    }
    resultado = extrair_metadados(dados)
    assert resultado == {
        "tipo": "Decreto",
        "numero": "123",
        "ano": 2023,
        "data_publicacao": "2023-02-01",
        "vigencia_inicio": "2023-02-01",
        "titulo": "Decreto de Teste"
    }
