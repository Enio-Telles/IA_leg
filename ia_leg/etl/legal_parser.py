"""
Parser jurídico hierárquico para segmentação normativa.

Objetivo:
- preservar a hierarquia Art. > § > inciso > alínea
- gerar chunks úteis para RAG sem depender apenas de split("Art.")
"""

import re
from typing import List, Tuple

ARTIGO_RE = re.compile(
    r"(?=^(Art\.\s*\d+[A-Za-zº°\-\/]*\.?))",
    flags=re.MULTILINE,
)

PARAGRAFO_RE = re.compile(
    r"(?=^(Parágrafo único|§\s*\d+[º°]?(?:-\w+)?\.?))",
    flags=re.MULTILINE,
)

INCISO_RE = re.compile(
    r"(?=^([IVXLCDM]+)\s*[-–—])",
    flags=re.MULTILINE,
)

ALINEA_RE = re.compile(
    r"(?=^([a-z])\))",
    flags=re.MULTILINE,
)


def _normalizar_texto(texto: str) -> str:
    texto = (texto or "").replace("\r\n", "\n").replace("\r", "\n")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def _split_by_pattern(texto: str, pattern: re.Pattern[str]) -> List[str]:
    texto = texto.strip()
    if not texto:
        return []
    partes = pattern.split(texto)
    blocos: List[str] = []
    i = 1
    while i < len(partes):
        cabecalho = partes[i].strip()
        corpo = partes[i + 1] if i + 1 < len(partes) else ""
        bloco = f"{cabecalho}{corpo}".strip()
        if bloco:
            blocos.append(bloco)
        i += 2
    return blocos


def _first_line(bloco: str) -> str:
    for linha in bloco.splitlines():
        linha = linha.strip()
        if linha:
            return linha
    return ""


def _identificador_artigo(bloco: str) -> str:
    linha = _first_line(bloco)
    m = re.match(r"(Art\.\s*\d+[A-Za-zº°\-\/]*\.?)", linha)
    return m.group(1).strip() if m else linha[:80].strip()


def _identificador_paragrafo(bloco: str) -> str:
    linha = _first_line(bloco)
    m = re.match(r"(Parágrafo único|§\s*\d+[º°]?(?:-\w+)?\.?)", linha)
    return m.group(1).strip() if m else linha[:80].strip()


def _identificador_inciso(bloco: str) -> str:
    linha = _first_line(bloco)
    m = re.match(r"([IVXLCDM]+)\s*[-–—]", linha)
    return f"Inciso {m.group(1)}" if m else linha[:80].strip()


def _identificador_alinea(bloco: str) -> str:
    linha = _first_line(bloco)
    m = re.match(r"([a-z])\)", linha)
    return f"Alínea {m.group(1)})" if m else linha[:80].strip()


def _adicionar_chunk(
    chunks: List[Tuple[str, str]], identificador: str, texto: str
) -> None:
    texto = texto.strip()
    identificador = identificador.strip()
    if not texto or not identificador:
        return
    if chunks and chunks[-1][0] == identificador and chunks[-1][1] == texto:
        return
    chunks.append((identificador, texto))


def _extrair_alineas(base_id: str, texto: str, chunks: List[Tuple[str, str]]) -> None:
    alineas = _split_by_pattern(texto, ALINEA_RE)
    for alinea in alineas:
        alinea_id = _identificador_alinea(alinea)
        _adicionar_chunk(chunks, f"{base_id} {alinea_id}", alinea)


def _extrair_incisos(base_id: str, texto: str, chunks: List[Tuple[str, str]]) -> None:
    incisos = _split_by_pattern(texto, INCISO_RE)
    for inciso in incisos:
        inciso_id = _identificador_inciso(inciso)
        inciso_ident = f"{base_id} {inciso_id}"
        _adicionar_chunk(chunks, inciso_ident, inciso)
        _extrair_alineas(inciso_ident, inciso, chunks)


def quebrar_dispositivos_hierarquicos(texto: str) -> List[Tuple[str, str]]:
    """
    Gera chunks jurídicos hierárquicos.

    Estratégia:
    - cada artigo completo vira um chunk
    - parágrafos viram chunks próprios
    - incisos e alíneas viram subchunks com caminho hierárquico

    Retorno:
        [("Art. 1º", "..."), ("Art. 1º § 1º", "..."), ...]
    """
    texto = _normalizar_texto(texto)
    if not texto:
        return []

    artigos = _split_by_pattern(texto, ARTIGO_RE)
    if not artigos:
        return []

    chunks: List[Tuple[str, str]] = []

    for artigo in artigos:
        artigo_id = _identificador_artigo(artigo)
        _adicionar_chunk(chunks, artigo_id, artigo)

        paragrafos = _split_by_pattern(artigo, PARAGRAFO_RE)
        if paragrafos:
            for paragrafo in paragrafos:
                paragrafo_id = _identificador_paragrafo(paragrafo)
                base_id = f"{artigo_id} {paragrafo_id}"
                _adicionar_chunk(chunks, base_id, paragrafo)
                _extrair_incisos(base_id, paragrafo, chunks)
        else:
            _extrair_incisos(artigo_id, artigo, chunks)

    return chunks


def quebrar_texto_generico_em_chunks(
    texto: str,
    tamanho_maximo: int = 1500,
    sobreposicao_palavras: int = 80,
) -> List[Tuple[str, str]]:
    """
    Divide documentos não normativos em chunks de leitura estável.
    Útil para manuais, orientações e pareceres.
    """
    texto = _normalizar_texto(texto)
    if not texto:
        return []

    paragrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
    if not paragrafos:
        return []

    chunks: List[Tuple[str, str]] = []
    atual: List[str] = []
    indice = 1

    for paragrafo in paragrafos:
        candidato = "\n\n".join(atual + [paragrafo]).strip()
        if len(candidato) <= tamanho_maximo:
            atual.append(paragrafo)
            continue

        if atual:
            texto_chunk = "\n\n".join(atual).strip()
            chunks.append((f"Trecho {indice}", texto_chunk))
            indice += 1

            palavras = texto_chunk.split()
            overlap = " ".join(palavras[-sobreposicao_palavras:]) if palavras else ""
            atual = [overlap, paragrafo] if overlap else [paragrafo]
        else:
            chunks.append((f"Trecho {indice}", paragrafo))
            indice += 1
            atual = []

    if atual:
        chunks.append((f"Trecho {indice}", "\n\n".join(atual).strip()))

    return chunks
