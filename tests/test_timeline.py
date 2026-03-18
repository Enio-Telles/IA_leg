from etl.timeline import consultar_norma_por_data

def test_consultar_norma_por_data():
    """
    Test that consultar_norma_por_data returns None when given stub inputs.
    """
    result = consultar_norma_por_data("id123", "2023-01-01")
    assert result is None
