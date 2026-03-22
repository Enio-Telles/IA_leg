import sys

with open("scripts/ingerir_html_legislacao.py", "r", encoding="utf-8") as f:
    content = f.read()

old_code = """    # 5. Chunking
    chunks = quebrar_pdf_em_chunks(texto_completo)
    for ident, conteudo in chunks:
        hash_disp = calcular_hash_texto(conteudo)
        cursor.execute(
            "INSERT INTO dispositivos (versao_id, identificador, texto, hash_dispositivo) VALUES (?, ?, ?, ?)",
            (nova_versao_id, ident, conteudo, hash_disp),
        )"""

new_code = """    # 5. Chunking
    chunks = quebrar_pdf_em_chunks(texto_completo)
    dados_dispositivos = [
        (nova_versao_id, ident, conteudo, calcular_hash_texto(conteudo))
        for ident, conteudo in chunks
    ]
    if dados_dispositivos:
        cursor.executemany(
            "INSERT INTO dispositivos (versao_id, identificador, texto, hash_dispositivo) VALUES (?, ?, ?, ?)",
            dados_dispositivos,
        )"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open("scripts/ingerir_html_legislacao.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Patched successfully")
else:
    print("Code not found")
