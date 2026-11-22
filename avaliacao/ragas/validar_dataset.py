# avaliacao/ragas/validar_dataset.py
#
# Validação automática do dataset do RAGAS do TCC 2 e material de revisão.
# Lê apenas dataset_tcc2.json (fonte canônica) e o protocolo; gera:
#   - RELATORIO_validacao_dataset.md
#   - dataset_tcc2_revisao.csv (derivado, para inspeção humana; não editar)
#
# Uso: python avaliacao/ragas/validar_dataset.py

import csv
import json
import os
import sys
from collections import Counter
from decimal import Decimal, InvalidOperation

PASTA = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PASTA)
from construir_dataset import ler_protocolo, CATEGORIAS, SAIDA  # noqa: E402

RELATORIO = os.path.join(PASTA, "RELATORIO_validacao_dataset.md")
CSV = os.path.join(PASTA, "dataset_tcc2_revisao.csv")

CAMPOS_OBRIGATORIOS = (
    "id", "ticker", "codigo_cvm", "empresa", "estrutura", "categoria", "pergunta", "documento",
    "periodo", "versao", "sha256_documento", "disponibilidade", "justificativa_disponibilidade",
    "gabarito", "fontes_gabarito", "valores_esperados", "verificacao_deterministica_aplicavel",
    "disponibilidade_estimada_protocolo", "divergencia_da_estimativa", "revisao_tecnica",
)
CHAVES_PROIBIDAS = {"resposta", "respostas", "answer", "response", "output", "faithfulness",
                    "answer_relevancy", "relevancy", "score", "scores", "comportamento",
                    "classe_exatidao", "resultado_exatidao", "exatidao"}


def chaves(obj, caminho=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k, caminho
            yield from chaves(v, f"{caminho}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from chaves(v, f"{caminho}[{i}]")


def itens_atomicos(c):
    for v in c["valores_esperados"]:
        yield v
        for alt in v.get("formas_alternativas") or []:
            yield from alt["parcelas"]


def verificar(ds: dict) -> dict:
    prot = ler_protocolo()
    pe = {e["ticker"]: e for e in prot["empresas"]}
    casos = ds["casos"]
    ids = Counter(c["id"] for c in casos)
    perguntas = Counter(c["pergunta"] for c in casos)
    p = {
        "ids_duplicados": [i for i, n in ids.items() if n > 1],
        "perguntas_duplicadas": [q for q, n in perguntas.items() if n > 1],
        "campos_ausentes": [(c.get("id"), f) for c in casos for f in CAMPOS_OBRIGATORIOS if f not in c],
        "documentos_divergentes": [c["id"] for c in casos if c["documento"] != "ITR" or c["periodo"] != "2026-06-30"],
        "versoes_divergentes": [c["id"] for c in casos if c["versao"] != pe[c["ticker"]]["versao"]],
        "hashes_divergentes": [c["id"] for c in casos if c["sha256_documento"] != pe[c["ticker"]]["sha256_documento"]],
        "codigos_divergentes": [c["id"] for c in casos if c["codigo_cvm"] != pe[c["ticker"]]["codigo_cvm"]],
        "estruturas_divergentes": [c["id"] for c in casos if c["estrutura"] != pe[c["ticker"]]["estrutura"]],
        "gabaritos_sem_fonte": [c["id"] for c in casos if not c["fontes_gabarito"]
                                or any(not v.get("fontes") for v in itens_atomicos(c))],
        "derivados_sem_formula": [f"{c['id']}:{v['id']}" for c in casos for v in itens_atomicos(c)
                                  if (len(v.get("fontes", [])) > 1 or v["tipo"] == "percentual") and not v.get("formula")],
        "valores_nao_parseaveis": [],
        "chaves_proibidas": sorted({f"{cam}.{k}" for k, cam in chaves(ds) if k.lower() in CHAVES_PROIBIDAS}),
        "divergencias_sem_justificativa": [c["id"] for c in casos if c["divergencia_da_estimativa"]
                                           and not c.get("justificativa_divergencia")],
    }
    for c in casos:
        for v in itens_atomicos(c):
            try:
                Decimal(v["valor"])
            except (InvalidOperation, KeyError, TypeError):
                p["valores_nao_parseaveis"].append(f"{c['id']}:{v.get('id')}")
    return p


def gerar(ds: dict):
    casos = ds["casos"]
    prob = verificar(ds)
    disp = Counter(c["disponibilidade"] for c in casos)
    est = Counter(c["disponibilidade_estimada_protocolo"] for c in casos)
    atom = [v for c in casos for v in itens_atomicos(c)]
    principais = [v for c in casos for v in c["valores_esperados"]]
    temporais = [c["id"] for c in casos
                 if {v["periodo"][:4] for v in c["valores_esperados"] if v["tipo"] == "monetario"} >= {"1S26", "1S25"}]
    rev = [c for c in casos if c["revisao_tecnica"].get("revisado")]
    obs = [c for c in casos if c["revisao_tecnica"].get("atencao_humana")]

    L = ["# Relatório de validação do dataset — RAGAS do TCC 2", "",
         f"Gerado por `validar_dataset.py` a partir de `dataset_tcc2.json` (fonte canônica). "
         f"Protocolo: `{ds['metadados']['protocolo']}` (SHA-256 `{ds['metadados']['sha256_protocolo'][:16]}…`). "
         f"Construído em {ds['metadados']['construido_em']} no commit `{ds['metadados']['commit_construcao'][:7]}`.", "",
         "Nenhuma resposta foi gerada, nenhum LLM foi chamado e nenhum score RAGAS ou resultado de exatidão existe neste dataset.", "",
         "## 1. Totais", "",
         f"- Empresas: **{len({c['ticker'] for c in casos})}**; casos: **{len(casos)}**",
         "- Casos por categoria: " + ", ".join(f"{k} {v}" for k, v in sorted(Counter(c['categoria'] for c in casos).items())),
         "- Casos por estrutura: " + ", ".join(f"{k} {v}" for k, v in sorted(Counter(c['estrutura'] for c in casos).items())),
         f"- Disponibilidade: presente **{disp['presente']}**, parcial **{disp['parcial']}**, ausente **{disp['ausente']}** "
         f"(estimativa pré-registrada: {est['presente']}/{est['parcial']}/{est['ausente']})",
         f"- Divergências em relação à estimativa: **{sum(c['divergencia_da_estimativa'] for c in casos)}**",
         f"- Verificação determinística aplicável: **{sum(c['verificacao_deterministica_aplicavel'] for c in casos)}** "
         f"casos; N4 (não aplicável por definição): **{sum(c['categoria'] == 'N4' for c in casos)}**",
         f"- Casos `presente` com exatidão aplicável: **{sum(c['disponibilidade'] == 'presente' and c['verificacao_deterministica_aplicavel'] for c in casos)}**",
         "", "## 2. Gabaritos", "",
         f"- Valores esperados (nível principal): **{len(principais)}**; incluindo parcelas alternativas: {len(atom)}",
         f"- Valores simples (uma conta CVM): **{sum(len(v['fontes']) == 1 and v['tipo'] == 'monetario' for v in principais)}**",
         f"- Valores derivados (fórmula sobre contas CVM): **{sum(bool(v.get('formula')) for v in principais)}**",
         f"- Percentuais: **{sum(v['tipo'] == 'percentual' for v in principais)}**",
         f"- Casos com comparação temporal (1S26 e 1S25): **{len(temporais)}**",
         f"- Casos com múltiplos valores esperados: **{sum(len(c['valores_esperados']) > 1 for c in casos)}**",
         f"- Casos com formas alternativas aceitas (total ou parcelas): **{sum(any(v.get('formas_alternativas') for v in c['valores_esperados']) for c in casos)}**",
         f"- Valores que exigem sinal: **{sum(v['sinal_exigido'] for v in principais)}**",
         "", "## 3. Integridade", "", "| Verificação | Resultado |", "|---|---|"]
    for k, v in prob.items():
        L.append(f"| {k.replace('_', ' ')} | {'OK (0)' if not v else f'**{len(v)}**: ' + ', '.join(map(str, v[:10]))} |")
    L += ["", "## 4. Contexto recuperado por empresa", "",
          "| Ticker | Versão | SHA-256 documento | Tabelas recuperadas (ordem) | Caracteres | SHA-256 contexto |",
          "|---|---|---|---|---|---|"]
    for tk, e in ds["empresas"].items():
        r = e["contexto_recuperado"]
        tabs = " → ".join(t.replace("[TABELA | ", "").replace(" (Consolidado)]", "") for t in r["tabelas_recuperadas"])
        L.append(f"| {tk} | {e['versao']} | `{e['sha256_documento'][:12]}…` | {tabs} | {r['caracteres_ctx_num']:,} | `{r['sha256_ctx_num'][:12]}…` |")
    L += ["", "## 5. Disponibilidade por caso", "", "| Ticker | " + " | ".join(CATEGORIAS) + " | P | Pa | A |",
          "|---|" + "---|" * 11]
    ab = {"presente": "P", "parcial": "Pa", "ausente": "A"}
    for tk in ds["empresas"]:
        cs = {c["categoria"]: c for c in casos if c["ticker"] == tk}
        cel = [ab[cs[k]["disponibilidade"]] + ("*" if cs[k]["divergencia_da_estimativa"] else "") for k in CATEGORIAS]
        n = Counter(cs[k]["disponibilidade"] for k in CATEGORIAS)
        L.append(f"| {tk} | " + " | ".join(cel) + f" | {n['presente']} | {n['parcial']} | {n['ausente']} |")
    L += ["", "`*` = diverge da estimativa pré-registrada.", "",
          "## 6. Revisão técnica pré-coleta", "",
          f"- Casos revisados: **{len(rev)}/{len(casos)}** "
          f"(revisor: {', '.join(sorted({c['revisao_tecnica'].get('revisor') or '—' for c in rev})) or '—'})",
          "- A revisão técnica **não** substitui a revisão humana de 100% exigida pela Seção 13 do protocolo; "
          "o dataset não está congelado.", ""]
    if obs:
        L += ["### Casos que merecem atenção na revisão humana", "", "| Caso | Motivo |", "|---|---|"]
        L += [f"| {c['id']} | {c['revisao_tecnica']['atencao_humana']} |" for c in obs]
        L.append("")
    L += ["## 7. Perguntas e gabaritos", "",
          "A lista completa (pergunta, gabarito, fontes, disponibilidade e justificativa) está em "
          "`dataset_tcc2_revisao.csv`, derivado deste dataset.", ""]
    with open(RELATORIO, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))
    with open(CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id", "ticker", "estrutura", "categoria", "pergunta", "disponibilidade", "estimada_protocolo",
                    "justificativa_disponibilidade", "gabarito", "valores_esperados", "contas_cvm",
                    "exatidao_aplicavel", "revisado", "observacao_revisao"])
        for c in casos:
            vals = "; ".join(f"{v['id']}={v['valor']}{' (sinal)' if v['sinal_exigido'] else ''}" for v in c["valores_esperados"])
            contas = ", ".join(sorted({f"{x['cd_conta']} {x['ds_conta']} [{x['periodo'][:4]}]" for x in c["fontes_gabarito"]}))
            w.writerow([c["id"], c["ticker"], c["estrutura"], c["categoria"], c["pergunta"], c["disponibilidade"],
                        c["disponibilidade_estimada_protocolo"], c["justificativa_disponibilidade"], c["gabarito"], vals,
                        contas, c["verificacao_deterministica_aplicavel"], c["revisao_tecnica"].get("revisado"),
                        c["revisao_tecnica"].get("observacao") or ""])
    return prob


if __name__ == "__main__":
    with open(SAIDA, encoding="utf-8") as f:
        ds = json.load(f)
    prob = gerar(ds)
    falhas = {k: v for k, v in prob.items() if v}
    print("Integridade:", "OK" if not falhas else falhas)
    print("Relatório:", RELATORIO)
