with open('etl/versionamento_pipeline.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'dados_embeddings = [' in line:
        start_idx = i
        break

indent = lines[start_idx].split('dados_embeddings')[0]

# remove extra indentation
for i in range(start_idx, start_idx + 12):
    lines[i] = lines[i].replace(indent + "    ", indent)

with open('etl/versionamento_pipeline.py', 'w') as f:
    f.writelines(lines)
