# avaliacao/analisar_cobertura.py
#
# Análise da COBERTURA do experimento Flash vs Pro: quais valores cada modelo
# efetivamente citou, não apenas quantos.
#
# A pergunta que este script responde é a que decide a interpretação do
# resultado: quando um modelo cita mais valores, ele está trazendo FATOS NOVOS
# (mais informação para o leitor) ou REPETINDO o mesmo número em seções
# diferentes (mais texto, mesma informação)? A contagem bruta de total_numeros
# não distingue os dois casos, e a diferença muda a conclusão.
#
# Identidade de um valor citado: o par (tipo, fato_mais_proximo) — isto é, o FATO
# da fonte que a auditoria casou com a citação, não a grafia do texto. Duas
# citações do mesmo fato ("R$ 1,58 bilhões" e "R$ 1,58 bilhão") são o MESMO
# valor, ainda que escritas diferente e em seções distintas. É essa a
# deduplicação pedida.
#
# Verificações IGNORADO (recurso didático "a cada R$ 100") ficam de fora, pelo
# mesmo motivo que não entram em total_numeros.
#
# Uso: python avaliacao/analisar_cobertura.py

import json
import os
import statistics
import sys
from collections import defaultdict

PASTA       = os.path.dirname(os.path.abspath(__file__))
ARQ_VERIFIC = os.path.join(PASTA, "experimento_flash_pro_verificacoes.json")
ARQ_SAIDA   = os.path.join(PASTA, "analise_cobertura.md")

MODELOS = ["flash", "pro"]


def chave_valor(v: dict) -> tuple:
    """
    Identidade do valor citado: o fato da fonte com que ele casou.
    Quando a auditoria não achou fato algum (NAO_ENCONTRADO), cai-se para o
    trecho literal — não há fato para deduplicar, e a citação é única por
    definição.
    """
    fato = v.get("fato_mais_proximo")
    if fato is None:
        return (v["tipo"], "SEM_FATO:" + v["trecho"].strip())
    return (v["tipo"], str(fato))


def coletar(registros: list) -> dict:
    """
    Para uma lista de execuções (mesmo ticker, mesmo modelo), devolve:
      distintos  -> {chave: {trecho(s), secoes, vezes, veredito(s)}}
      citacoes   -> total de citações contadas (sem IGNORADO)
    """
    distintos = {}
    citacoes  = 0
    for reg in registros:
        for v in reg["verificacoes"]:
            if v["veredito"] == "IGNORADO":
                continue
            citacoes += 1
            k = chave_valor(v)
            d = distintos.setdefault(k, {
                "tipo": v["tipo"], "fato": v.get("fato_mais_proximo"),
                "trechos": set(), "secoes": set(), "vezes": 0, "vereditos": set(),
                "origem": v.get("origem_fato"),
            })
            d["trechos"].add(v["trecho"].strip())
            d["secoes"].add(v["secao"])
            d["vezes"] += 1
            d["vereditos"].add(v["veredito"])
    return {"distintos": distintos, "citacoes": citacoes, "execucoes": len(registros)}


def rotular(d: dict) -> str:
    """Descrição legível de um valor distinto."""
    fato = d["fato"] if d["fato"] is not None else "(sem fato na fonte)"
    grafias = " / ".join(sorted(d["trechos"]))
    if grafias != str(fato):
        return f"{fato}  [citado como: {grafias}]"
    return str(fato)


def main() -> int:
    if not os.path.exists(ARQ_VERIFIC):
        print(f"Erro: {ARQ_VERIFIC} não encontrado.", file=sys.stderr)
        return 2

    with open(ARQ_VERIFIC, "r", encoding="utf-8") as f:
        bruto = json.load(f)

    # ticker -> modelo -> [execuções]
    porto = defaultdict(lambda: defaultdict(list))
    for reg in bruto.values():
        porto[reg["ticker"]][reg["modelo"]].append(reg)

    linhas = ["# Análise de cobertura — Flash vs Pro", ""]
    linhas += [
        "Um valor é identificado pelo **fato da fonte** com que a auditoria o casou, ",
        "não pela grafia: `R$ 1,58 bilhões` e `R$ 1,58 bilhão` são o mesmo valor. ",
        "Repetições do mesmo fato em seções diferentes contam uma vez. ",
        "Verificações `IGNORADO` ficam de fora.", "",
    ]

    totais_dist  = {m: [] for m in MODELOS}
    totais_cit   = {m: [] for m in MODELOS}
    soma_extras  = {m: {"repeticoes": 0, "novos": 0} for m in MODELOS}

    for ticker in sorted(porto):
        dados = {m: coletar(porto[ticker].get(m, [])) for m in MODELOS}
        conj  = {m: set(dados[m]["distintos"]) for m in MODELOS}

        linhas += [f"## {ticker}", ""]
        linhas += ["| | Flash | Pro |", "|---|---|---|"]
        linhas += [
            "| citações contadas (2 execuções) | {} | {} |".format(
                dados["flash"]["citacoes"], dados["pro"]["citacoes"]),
            "| **valores distintos** | **{}** | **{}** |".format(
                len(conj["flash"]), len(conj["pro"])),
            "| em comum | {} | |".format(len(conj["flash"] & conj["pro"])),
            "",
        ]

        for m in MODELOS:
            totais_dist[m].append(len(conj[m]))
            totais_cit[m].append(dados[m]["citacoes"])

        for m, outro in (("flash", "pro"), ("pro", "flash")):
            exclusivos = conj[m] - conj[outro]
            linhas += [f"**Só o {m.capitalize()} citou ({len(exclusivos)}):**", ""]
            if not exclusivos:
                linhas += ["_(nenhum)_", ""]
            else:
                for k in sorted(exclusivos, key=lambda x: (x[0], str(x[1]))):
                    d = dados[m]["distintos"][k]
                    linhas.append(
                        f"- `{d['tipo']}` {rotular(d)} — {d['vezes']}x, "
                        f"seções: {', '.join(sorted(d['secoes']))}"
                    )
                linhas.append("")

        # Repetição vs. informação nova: quanto do volume de citações de cada
        # modelo é o mesmo fato dito de novo?
        linhas += ["**Repetição interna** (mesmo fato citado mais de uma vez):", ""]
        for m in MODELOS:
            n_exec = dados[m]["execucoes"] or 1
            # Um fato citado n_exec vezes é o esperado: uma vez por execução.
            # Acima disso, o modelo repetiu o mesmo número em seções diferentes.
            rep = {k: d for k, d in dados[m]["distintos"].items() if d["vezes"] > n_exec}
            piso      = n_exec * len(conj[m])
            excedente = dados[m]["citacoes"] - piso
            soma_extras[m]["repeticoes"] += max(0, excedente)
            soma_extras[m]["novos"]      += len(conj[m])
            linhas.append(
                f"- **{m}** ({n_exec} exec.): {dados[m]['citacoes']} citações para "
                f"{len(conj[m])} valores distintos "
                f"(piso sem repetição: {piso}; excedente: {excedente:+d}); "
                f"{len(rep)} fato(s) repetido(s) dentro de uma mesma execução"
            )
        linhas.append("")

    # ── Agregado ──
    linhas += ["## Agregado", ""]
    linhas += ["| | Flash | Pro |", "|---|---|---|"]
    linhas += [
        "| valores distintos por empresa | {} | {} |".format(
            ", ".join(map(str, totais_dist["flash"])),
            ", ".join(map(str, totais_dist["pro"]))),
        "| **mediana de distintos** | **{}** | **{}** |".format(
            statistics.median(totais_dist["flash"]),
            statistics.median(totais_dist["pro"])),
        "| soma de distintos | {} | {} |".format(
            sum(totais_dist["flash"]), sum(totais_dist["pro"])),
        "| citações totais | {} | {} |".format(
            sum(totais_cit["flash"]), sum(totais_cit["pro"])),
        "",
    ]

    with open(ARQ_SAIDA, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")

    print("\n".join(linhas))
    print(f"\n[salvo em {ARQ_SAIDA}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
