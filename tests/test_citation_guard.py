from ia_leg.rag.citation_guard import (
    montar_fontes_verificadas,
    possui_ancoras_verificaveis,
    resposta_fallback_contextual,
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
