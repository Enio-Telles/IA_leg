from ia_leg.observability.log_reader import carregar_benchmark


def test_carregar_benchmark_inexistente(tmp_path):
    alvo = tmp_path / "nao_existe.json"
    payload = carregar_benchmark(alvo)
    assert payload["exists"] is False
    assert payload["results"] == []
