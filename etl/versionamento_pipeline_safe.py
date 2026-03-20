"""
Entry-point seguro para o pipeline de versionamento.

Uso:
    python etl/versionamento_pipeline_safe.py

Objetivo:
- reutilizar o pipeline legado
- trocar a quebra simplista por parser jurídico hierárquico
- adicionar `processar_tudo()` para compatibilidade com o CLI novo
"""

from __future__ import annotations

from pathlib import Path

import etl.versionamento_pipeline as legacy_pipeline
from ia_leg.etl.legal_parser import (
    quebrar_dispositivos_hierarquicos,
    quebrar_texto_generico_em_chunks,
)
from ia_leg.core.config.settings import BASE_DIR


def quebrar_dispositivos(texto: str):
    """
    Heurística segura:
    - se houver artigo, usa parser jurídico hierárquico
    - senão, usa chunking genérico
    """
    texto = (texto or "").strip()
    if not texto:
        return []

    if "Art." in texto or "ART." in texto:
        chunks = quebrar_dispositivos_hierarquicos(texto)
        if chunks:
            return chunks

    return quebrar_texto_generico_em_chunks(texto)


def processar_norma_json(caminho_json: str):
    legacy_pipeline.quebrar_dispositivos = quebrar_dispositivos
    return legacy_pipeline.processar_norma_json(caminho_json)


def processar_tudo():
    text_dir = Path(BASE_DIR) / "documentos" / "texto"
    arquivos = sorted(text_dir.glob("*.json"))

    print(f"Iniciando processamento ETL seguro de {len(arquivos)} arquivos JSON.")
    for arq in arquivos:
        try:
            print("----------------------------------------")
            print(f"Processando {arq.name}...")
            processar_norma_json(str(arq))
        except Exception as exc:
            import traceback

            print(f"Falha ao processar {arq.name}: {exc}")
            traceback.print_exc()


if __name__ == "__main__":
    processar_tudo()
