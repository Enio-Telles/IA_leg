"""
Teste de melhoria de relevancia - Retriever vs Retriever + Reranker.

Compara os resultados da busca vetorial pura (cosine similarity) com
os resultados apos reranking por cross-encoder (ms-marco-MiniLM-L-6-v2).

Execucao:
    conda activate leg_ia
    python tests/test_reranker_relevancia.py
"""
import sys
import time
import copy

sys.path.insert(0, ".")

from rag.retriever import recuperar_contexto
from rag.reranker import rerankar

# ---------------------------------------------------------
# QUERIES DE TESTE
# ---------------------------------------------------------
QUERIES = [
    "Qual a aliquota do ICMS sobre combustiveis em Rondonia?",
    "Prazo para recolhimento do ICMS substituicao tributaria",
    "Isencao de ICMS para produtos da cesta basica",
    "Base de calculo do ICMS sobre energia eletrica",
    "Obrigacoes acessorias do contribuinte do ICMS",
]

TOP_K_RETRIEVER = 10
TOP_K_FINAL = 5
OUTPUT_FILE = "tests/resultado_reranker.txt"


def log(msg, f):
    """Escreve no arquivo de saida."""
    f.write(msg + "\n")


def formatar_resultado(i, r, score_key="score"):
    score = r.get(score_key, r.get("score", 0))
    texto_limpo = r['texto'][:120].replace('\n', ' ').replace('\r', ' ')
    return (
        f"  {i}. [{score:.4f}] {r['norma']} - {r['identificador']}\n"
        f"     {texto_limpo}..."
    )


def testar_query(pergunta, f):
    log(f"\n{'=' * 70}", f)
    log(f"  QUERY: {pergunta}", f)
    log(f"{'=' * 70}", f)

    # Retriever puro (cosine similarity)
    t0 = time.perf_counter()
    candidatos = recuperar_contexto(pergunta, top_k=TOP_K_RETRIEVER)
    t_retriever = time.perf_counter() - t0

    if not candidatos:
        log("  [!] Nenhum resultado do retriever.", f)
        return None

    top_retriever = candidatos[:TOP_K_FINAL]

    log(f"\n  -- RETRIEVER (cosine sim) -- [{t_retriever:.3f}s]", f)
    for i, r in enumerate(top_retriever, 1):
        log(formatar_resultado(i, r, "score"), f)

    # Reranker (cross-encoder)
    candidatos_copia = copy.deepcopy(candidatos)
    t0 = time.perf_counter()
    reranked = rerankar(pergunta, candidatos_copia, top_k=TOP_K_FINAL)
    t_reranker = time.perf_counter() - t0

    log(f"\n  -- RERANKER (cross-encoder) -- [{t_reranker:.3f}s]", f)
    for i, r in enumerate(reranked, 1):
        log(formatar_resultado(i, r, "score_rerank"), f)

    # Comparacao
    ids_retriever = [r["id"] for r in top_retriever]
    ids_reranked = [r["id"] for r in reranked]

    mudancas = sum(1 for a, b in zip(ids_retriever, ids_reranked) if a != b)
    novos = [rid for rid in ids_reranked if rid not in ids_retriever]

    log(f"\n  -- ANALISE --", f)
    log(f"  Posicoes alteradas:     {mudancas}/{TOP_K_FINAL}", f)
    log(f"  Novos no top-{TOP_K_FINAL} (promovidos): {len(novos)}", f)
    log(f"  Tempo retriever:        {t_retriever:.3f}s", f)
    log(f"  Tempo reranker:         {t_reranker:.3f}s", f)
    log(f"  Overhead total:         +{t_reranker:.3f}s ({t_reranker / max(t_retriever, 0.001):.1f}x)", f)

    return {
        "mudancas": mudancas,
        "novos": len(novos),
        "t_retriever": t_retriever,
        "t_reranker": t_reranker,
    }


if __name__ == "__main__":
    print(f"Executando teste de relevancia... Resultados em: {OUTPUT_FILE}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        log("=" * 70, f)
        log("  TESTE DE RELEVANCIA - Retriever vs Retriever + Reranker", f)
        log(f"  Candidatos iniciais: {TOP_K_RETRIEVER} | Top final: {TOP_K_FINAL}", f)
        log("=" * 70, f)

        resultados = []
        for q in QUERIES:
            r = testar_query(q, f)
            if r:
                resultados.append(r)

        if resultados:
            log(f"\n\n{'=' * 70}", f)
            log("  RESUMO GERAL", f)
            log(f"{'=' * 70}", f)

            total_mudancas = sum(r["mudancas"] for r in resultados)
            total_novos = sum(r["novos"] for r in resultados)
            avg_t_ret = sum(r["t_retriever"] for r in resultados) / len(resultados)
            avg_t_rer = sum(r["t_reranker"] for r in resultados) / len(resultados)

            log(f"  Queries testadas:          {len(resultados)}", f)
            log(f"  Total posicoes alteradas:  {total_mudancas}/{len(resultados) * TOP_K_FINAL}", f)
            log(f"  Total promovidos ao top-{TOP_K_FINAL}: {total_novos}", f)
            log(f"  Tempo medio retriever:     {avg_t_ret:.3f}s", f)
            log(f"  Tempo medio reranker:      {avg_t_rer:.3f}s", f)
            log(f"  Overhead medio:            +{avg_t_rer:.3f}s", f)

            pct_mudanca = (total_mudancas / (len(resultados) * TOP_K_FINAL)) * 100
            if pct_mudanca > 30:
                log(f"\n  [OK] Reranker ALTEROU {pct_mudanca:.0f}% das posicoes - impacto significativo!", f)
            elif pct_mudanca > 0:
                log(f"\n  [**] Reranker alterou {pct_mudanca:.0f}% das posicoes - impacto moderado.", f)
            else:
                log(f"\n  [--] Reranker manteve a mesma ordem em todas as queries.", f)

        log(f"\n{'=' * 70}", f)
        log("  Teste concluido.", f)
        log(f"{'=' * 70}", f)

    print("Teste concluido. Verifique o arquivo de resultados.")
