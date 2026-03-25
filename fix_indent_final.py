with open('etl/versionamento_pipeline.py', 'r') as f:
    lines = f.readlines()

import re
with open('etl/versionamento_pipeline.py', 'w') as f:
    for line in lines:
        if "                    \"\"\"" in line and "INSERT INTO" not in line and "VALUES" not in line:
            # Flake8 doesn't like multiline strings inside docstrings to be further indented.
            pass
        f.write(line.replace("                    \"\"\"", "                    '''").replace("                    INSERT INTO", "                    INSERT INTO").replace("                    VALUES", "                    VALUES"))
