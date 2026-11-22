# Integridade do registro temporário de decisões humanas. Só lê.
import json, os, re, sys
from collections import Counter
RAIZ = r"C:\Users\allan\OneDrive\Desktop\TCC 2"
AQUI = os.path.dirname(os.path.abspath(__file__))
ds = json.load(open(os.path.join(RAIZ, "avaliacao", "ragas", "dataset_tcc2.json"), encoding="utf-8"))
ids_ds = [c["id"] for c in ds["casos"]]
linhas = open(os.path.join(AQUI, "decisoes_revisao_humana.md"), encoding="utf-8").read().splitlines()
reg = []
for l in linhas:
    m = re.match(r"^\|\s*([A-Z0-9]{5}_(?:N[1-5]|E[1-3]))\s*\|\s*([^|]*)\|\s*([^|]*)\|", l)
    if m:
        reg.append((m.group(1), m.group(2).strip(), m.group(3).strip(), l))
cont = Counter(i for i, *_ in reg)
print("linhas de decisão:", len(reg), "| ids únicos:", len(cont), "| dataset:", len(ids_ds), len(set(ids_ds)))
print("duplicados:", [i for i, n in cont.items() if n > 1])
print("faltando:", sorted(set(ids_ds) - set(cont)), "| extras:", sorted(set(cont) - set(ids_ds)))
dec = Counter(re.sub(r"\s*\(.*\)$", "", d) for _, d, _, _ in reg)
print("decisões:", dict(dec))
print("correções não vazias:", [(i, c) for i, _, c, _ in reg if c not in ("—", "-", "")])
print("datas:", Counter(re.findall(r"\| (20\d\d-\d\d-\d\d) \|", l)[0] if re.findall(r"\| (20\d\d-\d\d-\d\d) \|", l) else "SEM DATA" for *_, l in reg))
print("colunas por linha:", Counter(l.count("|") for *_, l in reg))
print("pendências textuais:", [i for i, d, _, _ in reg if "PENDENTE" in d.upper()])
por_cat = Counter(i.split("_")[1] for i in cont)
print("por categoria:", dict(sorted(por_cat.items())))
