from etl.timeline import consultar_norma_por_data
import pytest

def test_consultar_norma_por_data_valid_inputs():
    """Testa o caminho feliz com entradas válidas."""
    result = consultar_norma_por_data("id123", "2023-01-01")
    assert result is None

def test_consultar_norma_por_data_empty_strings():
    """Testa o comportamento com strings vazias."""
    result = consultar_norma_por_data("", "")
    assert result is None

def test_consultar_norma_por_data_invalid_date_format():
    """Testa o comportamento com formato de data inválido."""
    result = consultar_norma_por_data("id123", "01/01/2023")
    assert result is None

def test_consultar_norma_por_data_future_date():
    """Testa o comportamento com uma data no futuro."""
    result = consultar_norma_por_data("id123", "2050-12-31")
    assert result is None

def test_consultar_norma_por_data_none_values():
    """Testa o comportamento quando os valores são None."""
    result = consultar_norma_por_data(None, None)
    assert result is None

def test_consultar_norma_por_data_missing_args():
    """Testa o comportamento quando argumentos obrigatórios estão faltando."""
    with pytest.raises(TypeError):
        consultar_norma_por_data()

def test_consultar_norma_por_data_invalid_types():
    """Testa o comportamento com tipos de dados inválidos."""
    result = consultar_norma_por_data(123, 20230101)
    assert result is None
