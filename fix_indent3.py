with open('etl/versionamento_pipeline.py', 'r') as f:
    lines = f.readlines()

start_idx = -1
for i, line in enumerate(lines):
    if 'dados_embeddings = [' in line:
        start_idx = i
        break

end_idx = start_idx
for i in range(start_idx, len(lines)):
    if 'dados_embeddings,' in lines[i]:
        end_idx = i + 1
        break

indent = lines[start_idx].split('dados_embeddings')[0]

replacement = f"""{indent}dados_embeddings = [
{indent}    (disp_id, vetor.tobytes(), "bge-m3")
{indent}    for (disp_id, _), vetor in zip(novos_dispositivos_banco, vetores)
{indent}]
{indent}cursor.executemany(
{indent}    \"\"\"
{indent}    INSERT INTO embeddings (dispositivo_id, vetor, modelo)
{indent}    VALUES (?, ?, ?)
{indent}    \"\"\",
{indent}    dados_embeddings,
{indent})
"""

lines = lines[:start_idx] + [replacement] + lines[end_idx+1:]

with open('etl/versionamento_pipeline.py', 'w') as f:
    f.writelines(lines)
