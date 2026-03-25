"""
Testes para a fábrica central `ia_leg.app.factory`.
Garante que as dependências corretas (engines e estratégias)
são injetadas de acordo com as variáveis de ambiente,
sem depender de monkey patches implícitos.
"""

import os
import importlib
import pytest
from unittest.mock import patch

from ia_leg.app import factory

@pytest.fixture(autouse=True)
def reset_env_vars():
    """Garante ambiente limpo antes de cada teste."""
    old_env = os.environ.get("IA_LEG_ENGINE_MODE")
    yield
    if old_env is not None:
        os.environ["IA_LEG_ENGINE_MODE"] = old_env
    elif "IA_LEG_ENGINE_MODE" in os.environ:
        del os.environ["IA_LEG_ENGINE_MODE"]
    # Reimportar para limpar cache do módulo
    importlib.reload(factory)

def test_get_answer_engine_standard():
    os.environ["IA_LEG_ENGINE_MODE"] = "standard"
    importlib.reload(factory)
    engine = factory.get_answer_engine()

    # A engine padrao é consultar do answer_engine
    assert engine.__name__ == "consultar"

def test_get_answer_engine_safe():
    os.environ["IA_LEG_ENGINE_MODE"] = "safe"
    importlib.reload(factory)
    engine = factory.get_answer_engine()

    assert engine.__name__ == "_consultar_safe"

def test_get_answer_engine_safe_audited():
    os.environ["IA_LEG_ENGINE_MODE"] = "safe_audited"
    importlib.reload(factory)
    engine = factory.get_answer_engine()

    assert engine.__name__ == "_consultar_safe_audited"

def test_get_chunking_strategy_standard():
    os.environ["IA_LEG_ENGINE_MODE"] = "standard"
    importlib.reload(factory)
    strategy = factory.get_chunking_strategy()

    assert strategy.__name__ == "quebrar_dispositivos_padrao"

def test_get_chunking_strategy_safe():
    os.environ["IA_LEG_ENGINE_MODE"] = "safe"
    importlib.reload(factory)
    strategy = factory.get_chunking_strategy()

    assert strategy.__name__ == "_quebrar_dispositivos_proxy"

def test_get_chunking_strategy_safe_audited():
    os.environ["IA_LEG_ENGINE_MODE"] = "safe_audited"
    importlib.reload(factory)
    strategy = factory.get_chunking_strategy()

    assert strategy.__name__ == "_quebrar_dispositivos_proxy"
