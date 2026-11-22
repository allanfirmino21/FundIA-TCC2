# Evidências G8 (E2 caixa x dívida). Só lê; sem LLM; não grava no repositório.
import csv, io, json, os, re, subprocess, sys, zipfile, hashlib
from collections import defaultdict
RAIZ = r"C:\Users\allan\OneDrive\Desktop\TCC 2"
AQUI = os.path.dirname(os.path.abspath(__file__))
ZIP = os.path.join(AQUI, "cvm", "itr_cia_aberta_2026.zip")
sys.path.insert(0, os.path.join(RAIZ, "avaliacao", "ragas"))
import avaliar_respostas_tcc2 as A  # noqa: E402
assert not subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
assert hashlib.sha256(open(ZIP, "rb").read()).hexdigest().startswith("0e1ef742")
ds = json.load(open(os.path.join(RAIZ, "avaliacao", "ragas", "dataset_tcc2.json"), encoding="utf-8"))
_, _, coleta = A.carregar_entradas()
CTX = {c["case_id"]: c["contextos"] for c in coleta}
EMP = ds["empresas"]; codigos = {e["codigo_cvm"]: tk for tk, e in EMP.items()}
z = zipfile.ZipFile(ZIP)
IDS = ["WEGE3_E2", "ZAMP3_E2", "LAVV3_E2", "CEAB3_E2", "AURE3_E2", "POMO4_E2", "ITSA4_E2"]
TKS = {i.split("_")[0] for i in IDS}
OF = defaultdict(list)
for arq in ("BPA", "BPP", "DFC_MI"):
    for r in csv.DictReader(io.TextIOWrapper(z.open(f"itr_cia_aberta_{arq}_con_2026.csv"), encoding="latin-1"), delimiter=";"):
        tk = codigos.get(r["CD_CVM"].lstrip("0"))
        if tk in TKS and r["DT_REFER"] == "2026-06-30" and int(r["VERSAO"]) == EMP[tk]["versao"]:
            OF[tk].append((arq, r["CD_CONTA"], r["DS_CONTA"], r["ORDEM_EXERC"], r.get("DT_INI_EXERC", ""), r["DT_FIM_EXERC"], r["VL_CONTA"]))
out = open(os.path.join(AQUI, "g8_evidencias.txt"), "w", encoding="utf-8")
P = lambda *a: print(*a, file=out)
casos = {c["id"]: c for c in ds["casos"]}
for cid in IDS:
    c = casos[cid]; tk = c["ticker"]
    P("=" * 30, cid, c["estrutura"], "v", c["versao"], c["disponibilidade"], "| estimada", c["disponibilidade_estimada_protocolo"])
    P("P:", c["pergunta"]); P("G:", c["gabarito"]); P("JD:", c["justificativa_disponibilidade"])
    P("DIV:", c["divergencia_da_estimativa"], c["justificativa_divergencia"])
    P("FG:", json.dumps(c["fontes_gabarito"], ensure_ascii=False))
    for v in c["valores_esperados"]:
        P("  VE", v["id"], v["valor"], v["fontes"], v["formula"], "alt:", [[p["id"] + "=" + p["valor"] for p in a["parcelas"]] for a in v["formas_alternativas"]])
    P("RT:", json.dumps(c["revisao_tecnica"], ensure_ascii=False))
    P("-- oficial (ÚLTIMO; BPA/BPP 1.01*, 2.01.04*, 2.02.01*, e rótulos de empréstimo/arrendamento/debênture):")
    for arq, cd, ds_, ordem, ini, fim, vl in OF[tk]:
        if ordem != "ÚLTIMO" and ordem != "PENÚLTIMO":
            continue
        rel = (arq in ("BPA", "BPP") and (cd in ("1.01", "1.01.01", "1.01.02", "2.01", "2.02") or cd.startswith("2.01.04") or cd.startswith("2.02.01"))) \
            or re.search(r"(?i)arrend|deb[eê]nt|empr[eé]st|financiam|leas", ds_)
        if rel:
            P(f"   {arq:6s} {ordem:9s} {ini:10s} {fim} {cd:16s} {ds_[:70]:70s} {vl}")
    P("-- contexto congelado (linhas relevantes):")
    for t in CTX[cid]:
        ls = t.splitlines(); P("   [tabela]", ls[0][:120])
        for l in ls[1:]:
            if re.search(r"(?i)caixa|empr[eé]st|financiam|arrend|deb[eê]nt|aplica", l):
                P("      ", l.strip()[:150])
out.close()
