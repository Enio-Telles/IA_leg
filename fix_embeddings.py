import re

with open('etl/versionamento_pipeline.py', 'r') as f:
    content = f.read()

pattern = re.compile(r'for \(disp_id, _\), vetor in zip\(novos_dispositivos_banco, vetores\):\s*cursor\.execute\(\s*"""\s*INSERT INTO embeddings \(dispositivo_id, vetor, modelo\)\s*VALUES \(\?, \?, \?\)\s*""",\s*\(disp_id, vetor\.tobytes\(\), "bge-m3"\),\s*\)', re.MULTILINE)

replacement = """dados_embeddings = [
                    (disp_id, vetor.tobytes(), "bge-m3")
                    for (disp_id, _), vetor in zip(novos_dispositivos_banco, vetores)
                ]
                cursor.executemany(
                    \"\"\"
                    INSERT INTO embeddings (dispositivo_id, vetor, modelo)
                    VALUES (?, ?, ?)
                    \"\"\",
                    dados_embeddings,
                )"""

new_content = pattern.sub(replacement, content)

with open('etl/versionamento_pipeline.py', 'w') as f:
    f.write(new_content)
