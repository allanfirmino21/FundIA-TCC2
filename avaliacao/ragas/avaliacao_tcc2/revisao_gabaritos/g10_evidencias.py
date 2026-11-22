# Evidências G10 (E3 resultado financeiro). Só lê; sem LLM; não grava no repositório.
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
IDS = ["WEGE3_E3", "ZAMP3_E3", "LWSA3_E3", "LAVV3_E3", "POMO4_E3", "CEAB3_E3", "AURE3_E3", "ITSA4_E3"]
TKS = {i.split("_")[0] for i in IDS}
OF = defaultdict(list)
for arq in ("DRE", "DFC_MI"):
    for r in csv.DictReader(io.TextIOWrapper(z.open(f"itr_cia_aberta_{arq}_con_2026.csv"), encoding="latin-1"), delimiter=";"):
        tk = codigos.get(r["CD_CVM"].lstrip("0"))
        if tk in TKS and r["DT_REFER"] == "2026-06-30" and int(r["VERSAO"]) == EMP[tk]["versao"] and r["DT_INI_EXERC"][5:] == "01-01":
            OF[tk].append((arq, r["CD_CONTA"], r["DS_CONTA"], r["ORDEM_EXERC"], r["VL_CONTA"].replace(".0000000000", "")))
out = open(os.path.join(AQUI, "g10_evidencias.txt"), "w", encoding="utf-8")
P = lambda *a: print(*a, file=out)
casos = {c["id"]: c for c in ds["casos"]}
for cid in IDS:
    c = casos[cid]; tk = c["ticker"]
    P("=" * 30, cid, c["estrutura"], "v", c["versao"], c["disponibilidade"], "| estimada", c["disponibilidade_estimada_protocolo"])
    P("P:", c["pergunta"]); P("G:", c["gabarito"]); P("JD:", c["justificativa_disponibilidade"])
    P("DIV:", c["divergencia_da_estimativa"], c["justificativa_divergencia"])
    for f in c["fontes_gabarito"]:
        P("FG:", f.get("arquivo_cvm"), f.get("cd_conta"), f.get("ds_conta"), f.get("periodo"), f.get("ordem_exerc"))
    for v in c["valores_esperados"]:
        P("  VE", v["id"], v["valor"], v["fontes"], v["formula"], "sinal", v["sinal_exigido"], v.get("sinal_esperado"), v["tipo"], "alt:", [[p["id"] + "=" + p["valor"] for p in a["parcelas"]] for a in v["formas_alternativas"]])
    P("-- oficial DRE 3.06*, 3.05, 3.07 e DFC com financ/juros (acumulado):")
    lin = {}
    for arq, cd, d, ordem, vl in OF[tk]:
        lin.setdefault((arq, cd, d), {})[ordem] = vl
    for (arq, cd, d), v in lin.items():
        if (arq == "DRE" and (cd.startswith("3.06") or cd in ("3.05", "3.07"))) or (arq == "DFC_MI" and cd.startswith("6.01") and re.search(r"(?i)financ|juros|varia|cambi|rendim|encargo", d)):
            P(f"   {arq:6s} {cd:16s} {d[:70]:70s} 1S26 {v.get('ÚLTIMO'):>14} | 1S25 {v.get('PENÚLTIMO'):>14}")
    P("-- contexto congelado:")
    for t in CTX[cid]:
        ls = t.splitlines(); P("   [tabela]", ls[0][:120])
        for l in ls[1:]:
            if re.search(r"(?i)financ|juros|cambi|rendim|encargo|antes d|operacional", l):
                P("      ", l.strip()[:150])
out.close()
