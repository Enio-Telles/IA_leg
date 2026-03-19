import pytest
from etl.normalizador import extrair_metadados

def test_extrair_metadados_basico():
    dados = {
        "identificador": "D 12345/2026",
        "publicado_em": "19/02/2026",
        "ano": "2026",
        "titulo": "Decreto Teste"
    }
    resultado = extrair_metadados(dados)
    assert resultado["tipo"] == "Decreto"
    assert resultado["numero"] == "12345"
    assert resultado["ano"] == "2026"
    assert resultado["data_publicacao"] == "2026-02-19"
    assert resultado["vigencia_inicio"] == "2026-02-19"
    assert resultado["titulo"] == "Decreto Teste"

def test_extrair_metadados_tipos_conhecidos():
    tipos = {
        "D": "Decreto",
        "L": "Lei",
        "LC": "Lei Complementar",
        "IN": "Instrução Normativa",
        "R": "Resolução",
        "P": "Portaria",
        "C": "Convênio"
    }
    for abrev, nome_completo in tipos.items():
        dados = {"identificador": f"{abrev} 123/2026"}
        resultado = extrair_metadados(dados)
        assert resultado["tipo"] == nome_completo

def test_extrair_metadados_tipo_desconhecido():
    dados = {"identificador": "X 999/2026"}
    resultado = extrair_metadados(dados)
    assert resultado["tipo"] == "X"
    assert resultado["numero"] == "999"

def test_extrair_metadados_sem_identificador():
    dados = {"publicado_em": "01/01/2026"}
    resultado = extrair_metadados(dados)
    assert resultado["tipo"] == "Desconhecido"
    assert resultado["numero"] == ""
    assert resultado["data_publicacao"] == "2026-01-01"

    dados_vazio = {"identificador": ""}
    resultado_vazio = extrair_metadados(dados_vazio)
    assert resultado_vazio["tipo"] == "Desconhecido"
    assert resultado_vazio["numero"] == ""

def test_extrair_metadados_sem_barra_no_numero():
    dados = {"identificador": "L 12345"}
    resultado = extrair_metadados(dados)
    assert resultado["tipo"] == "Lei"
    assert resultado["numero"] == "12345"

def test_extrair_metadados_data_invalida():
    # Invalid formats should be returned as is
    dados1 = {"identificador": "D 1/2026", "publicado_em": "19-02-2026"}
    resultado1 = extrair_metadados(dados1)
    assert resultado1["data_publicacao"] == "19-02-2026"

    dados2 = {"identificador": "D 1/2026", "publicado_em": "19/02"}
    resultado2 = extrair_metadados(dados2)
    assert resultado2["data_publicacao"] == "19/02"

    dados3 = {"identificador": "D 1/2026", "publicado_em": ""}
    resultado3 = extrair_metadados(dados3)
    assert resultado3["data_publicacao"] == ""
