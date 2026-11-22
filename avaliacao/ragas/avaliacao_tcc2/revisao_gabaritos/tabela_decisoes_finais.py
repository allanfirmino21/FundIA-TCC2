# Preservação da revisão humana dos gabaritos (passo 1, 2026-10-08). Script criado para a
# preservação no repositório; NÃO foi usado durante a revisão. Só lê.
# Lê o registro cronológico (decisoes_revisao_humana.md) e o dataset congelado, separa as
# decisões finais das provisórias substituídas e confere a integridade. Com --markdown imprime
# a tabela das decisões finais; com --verificar confere que REVISAO_HUMANA_GABARITOS.md contém
# exatamente essa tabela entre os marcadores.
import json, os, re, sys
from collections import Counter

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.normpath(os.path.join(AQUI, "..", "..", "..", ".."))
REGISTRO = os.path.join(AQUI, "decisoes_revisao_humana.md")
DOC = os.path.join(AQUI, "REVISAO_HUMANA_GABARITOS.md")
INI, FIM = "<!-- INICIO_TABELA_DECISOES_FINAIS -->", "<!-- FIM_TABELA_DECISOES_FINAIS -->"
LINHA = re.compile(r"^\|\s*([A-Z0-9]{5}_(?:N[1-5]|E[1-3]))\s*\|(.*)\|\s*$")


def ler_registro():
    secao, finais, provisorias = "", [], []
    for l in open(REGISTRO, encoding="utf-8").read().splitlines():
        if l.startswith("#"):
            secao = l.lstrip("#").strip()
            continue
        m = LINHA.match(l)
        if not m:
            continue
        cel = [c.strip() for c in m.group(2).split("|")]
        assert len(cel) == 5, (m.group(1), len(cel))
        decisao, correcao, justif, data, evid = cel
        if "Bloco 5" in secao:
            etapa = "atenção humana, bloco 5"
        elif secao.startswith("Revisão humana dos gabaritos"):
            etapa = "atenção humana, blocos 1–4"
        else:
            g = re.search(r"\(grupo (G\d+[ab]?)\)", decisao)
            etapa = g.group(1) if g else ("revisão individual" if "individual" in decisao else secao)
        r = {"id": m.group(1), "decisao": decisao, "correcao": correcao, "justificativa": justif,
             "data": data, "evidencia": evid, "etapa": etapa}
        (provisorias if decisao.startswith("~~") else finais).append(r)
    return finais, provisorias


def conferir(finais, provisorias, ids_ds):
    cont = Counter(r["id"] for r in finais)
    erros = []
    if len(finais) != 96 or len(cont) != 96:
        erros.append(f"decisões finais: {len(finais)} linhas, {len(cont)} ids únicos")
    if [i for i, n in cont.items() if n > 1]:
        erros.append(f"duplicadas: {[i for i, n in cont.items() if n > 1]}")
    if set(cont) != set(ids_ds):
        erros.append(f"faltando {sorted(set(ids_ds) - set(cont))}, extras {sorted(set(cont) - set(ids_ds))}")
    if any(r["correcao"] not in ("—", "") for r in finais):
        erros.append("há correções registradas")
    if any(not re.fullmatch(r"20\d\d-\d\d-\d\d", r["data"]) for r in finais):
        erros.append("data ausente ou inválida")
    if any(not r["decisao"].upper().startswith("CONFIRMAR") for r in finais):
        erros.append("decisão final diferente de CONFIRMAR")
    if any(p["id"] not in cont for p in provisorias):
        erros.append("provisória sem decisão final")
    return erros


def tabela(finais, ids_ds):
    por = {r["id"]: r for r in finais}
    out = ["| nº | id | etapa | decisão humana final | data | justificativa (do autor) |", "|---:|---|---|---|---|---|"]
    for n, i in enumerate(ids_ds, 1):
        r = por[i]
        out.append(f"| {n} | {i} | {r['etapa']} | {r['decisao']} | {r['data']} | {r['justificativa']} |")
    return "\n".join(out)


if __name__ == "__main__":
    ds = json.load(open(os.path.join(RAIZ, "avaliacao", "ragas", "dataset_tcc2.json"), encoding="utf-8"))
    ids_ds = [c["id"] for c in ds["casos"]]
    finais, provisorias = ler_registro()
    if "--markdown" in sys.argv:
        print(tabela(finais, ids_ds))
        sys.exit(0)
    erros = conferir(finais, provisorias, ids_ds)
    print("linhas de decisão no registro:", len(finais) + len(provisorias), "| finais:", len(finais),
          "| provisórias substituídas:", [p["id"] for p in provisorias])
    print("ids finais únicos:", len({r["id"] for r in finais}), "| ids do dataset:", len(ids_ds), len(set(ids_ds)),
          "| iguais:", {r["id"] for r in finais} == set(ids_ds))
    print("por categoria:", dict(sorted(Counter(r["id"].split("_")[1] for r in finais).items())))
    print("decisões:", dict(Counter(re.sub(r"\s*\(.*\)$", "", r["decisao"]) for r in finais)))
    print("datas:", dict(Counter(r["data"] for r in finais)), "| etapas:", dict(Counter(r["etapa"] for r in finais)))
    if "--verificar" in sys.argv:
        doc = open(DOC, encoding="utf-8").read()
        bloco = doc.split(INI, 1)[1].split(FIM, 1)[0].strip()
        if bloco != tabela(finais, ids_ds):
            erros.append("tabela do documento difere da gerada a partir do registro")
        else:
            print("tabela do documento = tabela gerada a partir do registro")
    print("ERROS:", erros if erros else "nenhum")
    sys.exit(1 if erros else 0)
