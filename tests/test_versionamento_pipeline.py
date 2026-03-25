import pytest
import hashlib
import sqlite3
from etl.versionamento_pipeline import calcular_hash_texto, conectar

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

def test_conectar_banco_de_dados(mocker):
    # Mock para usar banco em memória ao invés do arquivo real
    mocker.patch("etl.versionamento_pipeline.DB_PATH", ":memory:")

    conn = conectar()

    assert isinstance(conn, sqlite3.Connection)

    # Verifica se o PRAGMA foreign_keys foi ativado
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys;")
    resultado = cursor.fetchone()

    assert resultado is not None
    assert resultado[0] == 1, "PRAGMA foreign_keys deveria estar ativado (1)"

    conn.close()

def test_conectar_chama_connect_com_path_correto(mocker):
    # Verifica se sqlite3.connect é chamado com DB_PATH e se execute é chamado
    mock_connect = mocker.patch("etl.versionamento_pipeline.sqlite3.connect")
    mock_db_path = mocker.patch("etl.versionamento_pipeline.DB_PATH", "caminho_falso.db")

    mock_conn = mock_connect.return_value

    resultado = conectar()

    mock_connect.assert_called_once_with("caminho_falso.db")
    mock_conn.execute.assert_called_once_with("PRAGMA foreign_keys = ON;")
    assert resultado == mock_conn
