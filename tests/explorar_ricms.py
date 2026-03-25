"""
Script de exploracao - salva resultados em JSON puro para leitura.
"""
import requests
import json

BASE_URL = "https://legislacao.sefin.ro.gov.br"

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

resultados_completos = {}

# 1. Total geral
r = session.get(f"{BASE_URL}/pesquisar_lei", params={"por_pagina": 1})
d = r.json()
resultados_completos["total_geral"] = d.get("total", 0)
resultados_completos["chaves_json"] = list(d.keys())

# 2. Busca RICMS
r2 = session.get(f"{BASE_URL}/pesquisar_lei", params={"q": "RICMS", "por_pagina": 100})
d2 = r2.json()
resultados_completos["ricms_total"] = d2.get("total", 0)
resultados_completos["ricms_resultados"] = [
    {"id": x.get("lei"), "identificador": x.get("identificador", ""), "titulo": x.get("titulo", "")}
    for x in d2.get("resultados", [])
]

# 3. Busca Decreto 22721 (RICMS/RO original)
r3 = session.get(f"{BASE_URL}/pesquisar_lei", params={"q": "22721", "por_pagina": 50})
d3 = r3.json()
resultados_completos["decreto_22721_total"] = d3.get("total", 0)
resultados_completos["decreto_22721_resultados"] = [
    {"id": x.get("lei"), "identificador": x.get("identificador", ""), "titulo": x.get("titulo", "")}
    for x in d3.get("resultados", [])
]

# 4. Busca Anexo
r4 = session.get(f"{BASE_URL}/pesquisar_lei", params={"q": "Anexo", "por_pagina": 100})
d4 = r4.json()
resultados_completos["anexo_total"] = d4.get("total", 0)
resultados_completos["anexo_primeiros"] = [
    {"id": x.get("lei"), "identificador": x.get("identificador", ""), "titulo": x.get("titulo", "")}
    for x in d4.get("resultados", [])[:20]
]

with open("ricms_exploracao.json", "w", encoding="utf-8") as f:
    json.dump(resultados_completos, f, indent=2, ensure_ascii=False)

print("Salvo em ricms_exploracao.json")
