from ia_leg.etl.legal_parser import quebrar_dispositivos_hierarquicos


def test_quebra_hierarquica_basica():
    texto = """
Art. 1º Esta lei dispõe sobre algo.
§ 1º O contribuinte deverá:
I - apresentar documento;
II - recolher o imposto;
a) no prazo regular;
b) com memória de cálculo.

Art. 2º Fica revogado o dispositivo anterior.
""".strip()

    chunks = quebrar_dispositivos_hierarquicos(texto)
    ids = [ident for ident, _ in chunks]

    assert "Art. 1º" in ids
    assert "Art. 1º § 1º" in ids
    assert "Art. 1º § 1º Inciso I" in ids
    assert "Art. 1º § 1º Inciso II" in ids
    assert "Art. 1º § 1º Inciso II Alínea a)" in ids
    assert "Art. 1º § 1º Inciso II Alínea b)" in ids
    assert "Art. 2º" in ids
