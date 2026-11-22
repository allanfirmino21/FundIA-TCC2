# Evidências G9 (E2 bancos: depósitos). Só lê; sem LLM; não grava no repositório.
import csv, io, json, os, re, subprocess, sys, zipfile, hashlib
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
out = open(os.path.join(AQUI, "g9_evidencias.txt"), "w", encoding="utf-8")
P = lambda *a: print(*a, file=out)
for tk, pref in (("BBAS3", "2.02"), ("ITUB4", "2.03")):
    P("=" * 20, tk, "v", EMP[tk]["versao"])
    for r in csv.DictReader(io.TextIOWrapper(z.open("itr_cia_aberta_BPP_con_2026.csv"), encoding="latin-1"), delimiter=";"):
        if codigos.get(r["CD_CVM"].lstrip("0")) != tk or r["DT_REFER"] != "2026-06-30" or int(r["VERSAO"]) != EMP[tk]["versao"]:
            continue
        cd = r["CD_CONTA"]
        if cd.count(".") == 1 or cd.startswith(pref) or re.search(r"(?i)dep[oó]sito|capta", r["DS_CONTA"]):
            P(f"   {r['ORDEM_EXERC']:9s} {r['DT_FIM_EXERC']} {cd:16s} {r['DS_CONTA'][:75]:75s} {r['VL_CONTA']}")
    P("-- contexto", tk + "_E2")
    for t in CTX[tk + "_E2"]:
        ls = t.splitlines(); P("   [tabela]", ls[0][:120], "| linhas:", len(ls) - 1)
        for l in ls[1:]:
            if re.search(r"(?i)dep[oó]sito|capta|passivo|total", l):
                P("      ", l.strip()[:150])
out.close()
