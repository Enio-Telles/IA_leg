"""
Camada de proteção para respostas do RAG.

Força a exposição de fontes verificáveis e reduz respostas
com baixa sustentação contextual.
"""

from __future__ import annotations

from typing import Dict, List


def score_maximo(contextos: List[Dict]) -> float:
    if not contextos:
        return 0.0
    return max(float(ctx.get("score_rerank", ctx.get("score", 0.0))) for ctx in contextos)


def possui_ancoras_verificaveis(resposta: str, contextos: List[Dict]) -> bool:
    resposta_norm = (resposta or "").lower()
    for ctx in contextos:
        identificador = str(ctx.get("identificador", "")).lower()
        norma = str(ctx.get("norma", "")).lower()
        if identificador and identificador in resposta_norm:
            return True
        if norma and norma in resposta_norm:
            return True
    return False


def resumir_texto(texto: str, limite: int = 320) -> str:
    texto = " ".join((texto or "").split())
    if len(texto) <= limite:
        return texto
    return texto[: limite - 3].rstrip() + "..."


def montar_fontes_verificadas(contextos: List[Dict], limite_texto: int = 320) -> str:
    if not contextos:
        return ""

    linhas = ["\n\n## Fontes verificadas"]
    for i, ctx in enumerate(contextos, start=1):
        score = float(ctx.get("score_rerank", ctx.get("score", 0.0)))
        linhas.append(
            (
                f"{i}. **{ctx.get('norma', 'Norma não identificada')}** — "
                f"{ctx.get('identificador', 'Trecho sem identificador')} "
                f"(score: {score:.4f})"
            )
        )
        linhas.append(f"   > {resumir_texto(str(ctx.get('texto', '')), limite_texto)}")
    return "\n".join(linhas)


def resposta_fallback_contextual(
    pergunta: str,
    contextos: List[Dict],
    motivo: str,
) -> str:
    cabecalho = (
        "Não encontrei base suficiente para entregar uma resposta interpretativa "
        "segura. Abaixo estão os trechos mais relevantes localizados para análise direta."
    )
    if motivo:
        cabecalho += f"\n\nMotivo do fallback: {motivo}."

    return (
        f"## Consulta\n{pergunta}\n\n"
        f"## Resultado seguro\n{cabecalho}"
        f"{montar_fontes_verificadas(contextos)}"
    )
