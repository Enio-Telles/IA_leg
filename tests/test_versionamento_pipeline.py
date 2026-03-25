import pytest
import hashlib
from etl.versionamento_pipeline import calcular_hash_texto

def test_calcular_hash_texto_padrao():
    texto = "Este é um texto padrão"
    resultado_esperado = hashlib.sha256(texto.encode("utf-8")).hexdigest()
    assert calcular_hash_texto(texto) == resultado_esperado

def test_calcular_hash_texto_vazio():
    texto = ""
    resultado_esperado = hashlib.sha256(texto.encode("utf-8")).hexdigest()
    assert calcular_hash_texto(texto) == resultado_esperado

def test_calcular_hash_texto_caracteres_especiais():
    texto = "Texto com caracteres especiais: áéíóú ç ~ ^ !@#$%^&*()"
    resultado_esperado = hashlib.sha256(texto.encode("utf-8")).hexdigest()
    assert calcular_hash_texto(texto) == resultado_esperado

def test_calcular_hash_texto_quebra_de_linha():
    texto = "Texto com\nquebra de linha\ne\ttabulação"
    resultado_esperado = hashlib.sha256(texto.encode("utf-8")).hexdigest()
    assert calcular_hash_texto(texto) == resultado_esperado

def test_calcular_hash_texto_conhecido():
    # Verifica contra um hash conhecido previamente calculado
    texto = "hello world"
    # echo -n "hello world" | sha256sum
    hash_esperado = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    assert calcular_hash_texto(texto) == hash_esperado
