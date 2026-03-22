from ia_leg.rag.citation_guard import (
    montar_fontes_verificadas,
    possui_ancoras_verificaveis,
    resposta_fallback_contextual,
    score_maximo,
)


def _ctx():
    return [
        {
            "norma": "Decreto 22721/2018",
            "identificador": "Art. 12",
            "texto": "A alíquota interna do ICMS é de 17%.",
            "score": 0.91,
        }
    ]


def test_detecta_ancora_valida():
    resposta = "Conforme o Decreto 22721/2018, no Art. 12, a alíquota é de 17%."
    assert possui_ancoras_verificaveis(resposta, _ctx()) is True


def test_fallback_inclui_fontes():
    texto = resposta_fallback_contextual("Qual a alíquota?", _ctx(), "sem âncoras")
    assert "Fontes verificadas" in texto
    assert "Decreto 22721/2018" in texto
    assert "Art. 12" in texto


def test_fontes_verificadas_formatadas():
    bloco = montar_fontes_verificadas(_ctx())
    assert "score: 0.9100" in bloco

def test_score_maximo():
    # Contexto vazio
    assert score_maximo([]) == 0.0

    # Apenas score
    assert score_maximo([{"score": 0.5}, {"score": 0.8}]) == 0.8

    # Apenas score_rerank
    assert score_maximo([{"score_rerank": 0.4}, {"score_rerank": 0.7}]) == 0.7

    # Precedência (score_rerank deve ser usado se existir)
    # Mesmo que o score base seja maior
    assert score_maximo([{"score": 0.9, "score_rerank": 0.5}]) == 0.5

    # Valores em string (deve converter para float)
    assert score_maximo([{"score": "0.7"}, {"score_rerank": "0.85"}]) == 0.85

    # Mix de chaves em diferentes dicionários
    assert score_maximo([{"score": 0.9}, {"score_rerank": 0.6}]) == 0.9
