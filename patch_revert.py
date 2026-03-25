import os

with open("scripts/ingerir_html_legislacao.py", "r") as f:
    content = f.read()

old_code = """    # 5. Chunking
    chunks = quebrar_pdf_em_chunks(texto_completo)
    if chunks:
        # Bolt ⚡: Replace N+1 queries with batch insert for performance
        dispositivos_para_inserir = [
            (nova_versao_id, ident, conteudo, calcular_hash_texto(conteudo))
            for ident, conteudo in chunks
        ]
        cursor.executemany(
            "INSERT INTO dispositivos (versao_id, identificador, texto, hash_dispositivo) VALUES (?, ?, ?, ?)",
            dispositivos_para_inserir,
        )"""

new_code = """    # 5. Chunking
    chunks = quebrar_pdf_em_chunks(texto_completo)
    for ident, conteudo in chunks:
        hash_disp = calcular_hash_texto(conteudo)
        cursor.execute(
            "INSERT INTO dispositivos (versao_id, identificador, texto, hash_dispositivo) VALUES (?, ?, ?, ?)",
            (nova_versao_id, ident, conteudo, hash_disp),
        )"""

content = content.replace(old_code, new_code)

with open("scripts/ingerir_html_legislacao.py", "w") as f:
    f.write(content)
