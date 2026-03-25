with open('etl/versionamento_pipeline.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'vetores = gerar_embeddings(textos)' in line:
        start_idx = i
        break

indent = lines[start_idx].split('vetores =')[0]

replacement = f"""{indent}vetores = gerar_embeddings(textos)
{indent}if vetores:
{indent}    dados_embeddings = [
{indent}        (disp_id, vetor.tobytes(), "bge-m3")
{indent}        for (disp_id, _), vetor in zip(novos_dispositivos_banco, vetores)
{indent}    ]
{indent}    cursor.executemany(
{indent}        \"\"\"
{indent}        INSERT INTO embeddings (dispositivo_id, vetor, modelo)
{indent}        VALUES (?, ?, ?)
{indent}        \"\"\",
{indent}        dados_embeddings,
{indent}    )
"""

for j in range(start_idx, len(lines)):
    if 'print("Versionamento concluído com sucesso.")' in lines[j]:
        end_idx = j
        break

lines = lines[:start_idx] + [replacement] + ['        """\n\n', '        conn.commit()\n', '        print("Versionamento concluído com sucesso.")\n'] + lines[end_idx+1:]

with open('etl/versionamento_pipeline.py', 'w') as f:
    f.writelines(lines)
