# Evidências POMO4_E1. Só lê; sem LLM; não grava no repositório.
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
out = open(os.path.join(AQUI, "pomo4_e1_evidencias.txt"), "w", encoding="utf-8")
P = lambda *a: print(*a, file=out)
casos = {c["id"]: c for c in ds["casos"]}
c = casos["POMO4_E1"]
for k in ("estrutura", "versao", "pergunta", "gabarito", "disponibilidade", "disponibilidade_estimada_protocolo", "justificativa_disponibilidade",
          "divergencia_da_estimativa", "justificativa_divergencia", "verificacao_deterministica_aplicavel"):
    P(k, ":", c[k])
P("fontes_gabarito:", json.dumps(c["fontes_gabarito"], ensure_ascii=False, indent=1))
P("valores_esperados:", json.dumps(c["valores_esperados"], ensure_ascii=False, indent=1))
P("revisao_tecnica:", json.dumps(c["revisao_tecnica"], ensure_ascii=False))
for arq in ("DRE", "DFC_MI"):
    for r in csv.DictReader(io.TextIOWrapper(z.open(f"itr_cia_aberta_{arq}_con_2026.csv"), encoding="latin-1"), delimiter=";"):
        if codigos.get(r["CD_CVM"].lstrip("0")) == "POMO4" and r["DT_REFER"] == "2026-06-30" and int(r["VERSAO"]) == 1 and r["DT_INI_EXERC"][5:] == "01-01":
            if (arq == "DRE" and r["CD_CONTA"] in ("3.01", "3.02", "3.03", "3.09", "3.10", "3.11", "3.11.01", "3.11.02")) or (arq == "DFC_MI" and r["CD_CONTA"] in ("6.01", "6.01.01", "6.01.01.01")):
                P(f"OF {arq:6s} {r['ORDEM_EXERC']:9s} {r['DT_INI_EXERC']}..{r['DT_FIM_EXERC']} {r['CD_CONTA']:10s} {r['DS_CONTA'][:60]:60s} {r['VL_CONTA'].replace('.0000000000','')}")
P("-- contexto POMO4_E1:")
for t in CTX["POMO4_E1"]:
    ls = t.splitlines(); P("   [tabela]", ls[0][:120], "| linhas:", len(ls) - 1)
    for l in ls[1:]:
        if re.search(r"(?i)resultado|lucro|preju|receita|venda", l):
            P("      ", l.strip()[:150])
out.close()
