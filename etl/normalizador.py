"""
Normaliza texto jurídico e extrai metadados.
"""


def extrair_metadados(dados: dict) -> dict:
    """Extrai e padroniza metadados oriundos do JSON da API."""
    identificador = dados.get("identificador", "")
    
    # identificador costuma vir como "D 31266/2026"
    partes = identificador.split(" ", 1)
    tipo = "Desconhecido"
    numero = identificador
    
    if len(partes) >= 2:
        tipo_abreviado = partes[0].upper()
        numero_ano = partes[1].split("/")
        numero = numero_ano[0] if len(numero_ano) > 0 else partes[1]
        
        tipo_map = {
            "D": "Decreto", 
            "L": "Lei", 
            "LC": "Lei Complementar", 
            "IN": "Instrução Normativa", 
            "R": "Resolução", 
            "P": "Portaria",
            "C": "Convênio"
        }
        tipo = tipo_map.get(tipo_abreviado, tipo_abreviado)

    # Converter data_publicacao de DD/MM/YYYY para YYYY-MM-DD
    # A API retorna "publicado_em": "19/02/2026"
    data_pub_original = dados.get("publicado_em", "")
    data_pub_iso = data_pub_original
    if "/" in data_pub_original:
        partes_data = data_pub_original.split("/")
        if len(partes_data) == 3:
            data_pub_iso = f"{partes_data[2]}-{partes_data[1]}-{partes_data[0]}"

    return {
        "tipo": tipo,
        "numero": numero,
        "ano": dados.get("ano"),
        "data_publicacao": data_pub_iso,
        "vigencia_inicio": data_pub_iso, # Sem dados explícitos de vigência, usamos pub
        "titulo": dados.get("titulo", "")
    }
