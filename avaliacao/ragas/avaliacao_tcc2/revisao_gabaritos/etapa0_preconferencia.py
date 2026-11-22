# Etapa 0 — pré-conferência mecânica dos gabaritos (Claude Code; NÃO é revisão humana).
# Fontes: dataset congelado, contexto congelado da coleta (via executor) e pacote oficial CVM
# itr_cia_aberta_2026.zip (baixado com autorização do autor). Só lê; não grava no repositório.
# Não usa RAGAS, exatidão, respostas nem comportamento. Sem LLM.
import csv, io, json, os, re, subprocess, sys, unicodedata, zipfile, hashlib
from collections import Counter, defaultdict
from decimal import Decimal

RAIZ = r"C:\Users\allan\OneDrive\Desktop\TCC 2"
AQUI = os.path.dirname(os.path.abspath(__file__))
ZIP = os.path.join(AQUI, "cvm", "itr_cia_aberta_2026.zip")
sys.path.insert(0, os.path.join(RAIZ, "avaliacao", "ragas"))
import avaliar_respostas_tcc2 as A  # noqa: E402

assert not subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=RAIZ,
                          capture_output=True, text=True).stdout.strip()
SHA_ZIP = hashlib.sha256(open(ZIP, "rb").read()).hexdigest()
assert SHA_ZIP.startswith("0e1ef742")
ds = json.load(open(os.path.join(RAIZ, "avaliacao", "ragas", "dataset_tcc2.json"), encoding="utf-8"))
_, _, coleta = A.carregar_entradas()
CTX = {c["case_id"]: c["contextos"] for c in coleta}
EMP = ds["empresas"]
z = zipfile.ZipFile(ZIP)


def ler(n):
    return csv.DictReader(io.TextIOWrapper(z.open(n), encoding="latin-1"), delimiter=";")


codigos = {e["codigo_cvm"]: tk for tk, e in EMP.items()}
# índice de versões
IDX = defaultdict(list)
for r in ler("itr_cia_aberta_2026.csv"):
    if r["DT_REFER"] == "2026-06-30" and r["CD_CVM"].lstrip("0") in codigos:
        IDX[codigos[r["CD_CVM"].lstrip("0")]].append((int(r["VERSAO"]), r["ID_DOC"], r["DT_RECEB"]))
VERS = {}
for tk, e in EMP.items():
    vs = sorted(IDX[tk])
    VERS[tk] = {"versao_dataset": e["versao"], "versoes_no_indice": [v for v, _, _ in vs],
                "versao_mais_recente": vs[-1][0], "id_doc": next(i for v, i, _ in vs if v == e["versao"]),
                "dt_receb": next(d for v, _, d in vs if v == e["versao"]),
                "compativel": vs[-1][0] == e["versao"]}

# linhas oficiais (versão do dataset), por (ticker, arquivo, conta, ordem, dt_ini, dt_fim)
OF = {}
for arq in ("DRE", "BPA", "BPP"):
    nome = f"itr_cia_aberta_{arq}_con_2026.csv"
    for r in ler(nome):
        cd = r["CD_CVM"].lstrip("0")
        if r["DT_REFER"] != "2026-06-30" or cd not in codigos:
            continue
        tk = codigos[cd]
        if int(r["VERSAO"]) != EMP[tk]["versao"]:
            continue
        OF[(tk, nome, r["CD_CONTA"], r["ORDEM_EXERC"], r.get("DT_INI_EXERC"), r["DT_FIM_EXERC"])] = r


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()


def num_ctx(t):
    t = t.strip()
    if re.fullmatch(r"-?\d+\.\d{10}", t):
        return Decimal(t)
    return Decimal(t.replace(".", "").replace(",", "."))


def linhas_ctx(cid):
    out = []
    for t in CTX[cid]:
        ls = t.splitlines()
        cab = ls[0]
        for l in ls[1:]:
            m = re.match(r"^(.*?)\s{2,}(-?[\d.,]+)\s+\(anterior:\s*(-?[\d.,]+)\)\s*$", l)
            if m:
                out.append((cab, norm(m.group(1)), num_ctx(m.group(2)), num_ctx(m.group(3)), l.strip()))
    return out


TAB = {"itr_cia_aberta_DRE_con_2026.csv": "demonstracao de resultado", "itr_cia_aberta_BPA_con_2026.csv": "ativo",
       "itr_cia_aberta_BPP_con_2026.csv": "passivo"}
SIG = {"[DRE]": "demonstracao de resultado", "[BPA]": "ativo", "[BPP]": "passivo", "[DFC]": "fluxo de caixa"}
SINAL_TABELA = {("N1", None): False, ("N2", None): True, ("N3", None): True, ("N5", None): False,
                ("E1", "nao_financeira"): False, ("E2", "nao_financeira"): False, ("E3", "nao_financeira"): True,
                ("E2", "holding"): False, ("E3", "holding"): True, ("E1", "holding"): False,
                ("E1", "banco"): False, ("E2", "banco"): False, ("E3", "banco"): False,
                ("E1", "resseguradora"): True, ("E2", "resseguradora"): True, ("E3", "resseguradora"): False}


def fmt_mil(v):  # Decimal em R$ mil -> "1.234.567"
    s = f"{abs(int(v)):,}".replace(",", ".")
    return s


rel = {}
for c in ds["casos"]:
    cid, tk, cat = c["id"], c["ticker"], c["categoria"]
    probs, avisos, ev = [], [], {}
    # 1. versão
    if not VERS[tk]["compativel"]:
        probs.append(f"versão: dataset v{VERS[tk]['versao_dataset']}, mais recente no índice v{VERS[tk]['versao_mais_recente']}")
    # 2. linhas-fonte
    fonte_val = {}
    for f in c["fontes_gabarito"]:
        k = (tk, f["arquivo_cvm"], f["cd_conta"], f["ordem_exerc"], f.get("dt_ini_exerc"), f["dt_fim_exerc"])
        r = OF.get(k)
        if r is None:
            probs.append(f"linha-fonte não encontrada no pacote oficial: {k[1:]}")
            continue
        if Decimal(r["VL_CONTA"]) != Decimal(f["vl_conta_cvm"]):
            probs.append(f"valor diverge {f['cd_conta']} {f['ordem_exerc']}: dataset {f['vl_conta_cvm']} x oficial {r['VL_CONTA']}")
        if norm(r["DS_CONTA"]) != norm(f["ds_conta"]):
            probs.append(f"descrição diverge {f['cd_conta']}: {f['ds_conta']!r} x {r['DS_CONTA']!r}")
        if (r["ESCALA_MOEDA"], r["MOEDA"]) != ("MIL", "REAL"):
            probs.append(f"escala/moeda {r['ESCALA_MOEDA']}/{r['MOEDA']}")
        if f["arquivo_cvm"].endswith("DRE_con_2026.csv"):
            esperado = ("2026-01-01", "2026-06-30") if f["ordem_exerc"] == "ÚLTIMO" else ("2025-01-01", "2025-06-30")
            if (f["dt_ini_exerc"], f["dt_fim_exerc"]) != esperado:
                probs.append(f"período DRE não acumulado: {f['cd_conta']} {f['dt_ini_exerc']}–{f['dt_fim_exerc']}")
        else:
            if (f["ordem_exerc"], f["dt_fim_exerc"]) != ("ÚLTIMO", "2026-06-30"):
                probs.append(f"período BP inesperado: {f['cd_conta']} {f['ordem_exerc']} {f['dt_fim_exerc']}")
        fonte_val[(f["cd_conta"], f["ordem_exerc"])] = Decimal(f["vl_conta_cvm"])
        ev.setdefault("fontes", []).append({"conta": f["cd_conta"], "ds": r["DS_CONTA"], "ordem": f["ordem_exerc"],
                                            "periodo": f"{f.get('dt_ini_exerc') or ''}..{f['dt_fim_exerc']}",
                                            "oficial": str(Decimal(r["VL_CONTA"]).normalize()), "dataset": str(Decimal(f["vl_conta_cvm"]).normalize())})
    # 3. valores exigidos, sinais e derivados
    U = lambda k: fonte_val.get(k)  # noqa: E731
    for v in c["valores_esperados"]:
        val = Decimal(v["valor"])
        if v["tipo"] == "monetario":
            if v.get("formula") == "2.01.04 + 2.02.01":
                calc = (U(("2.01.04", "ÚLTIMO")) + U(("2.02.01", "ÚLTIMO"))) * 1000
                parc = [Decimal(p["valor"]) for a in v.get("formas_alternativas") or [] for p in a["parcelas"]]
                if parc != [U(("2.01.04", "ÚLTIMO")) * 1000, U(("2.02.01", "ÚLTIMO")) * 1000]:
                    probs.append(f"parcelas da dívida não conferem: {parc}")
            elif v.get("formula"):
                calc = None; avisos.append(f"fórmula monetária não tratada: {v['formula']}")
            else:
                ks = [k for k in fonte_val if k[0] in v["fontes"]]
                per = "PENÚLTIMO" if "1s25" in v["id"] else "ÚLTIMO"
                calc = U((v["fontes"][0], per)) * 1000 if U((v["fontes"][0], per)) is not None else None
            if calc is None or calc != val:
                probs.append(f"valor exigido {v['id']}={val} x recalculado {calc}")
            esp = "-" if val < 0 else "+"
            if v.get("sinal_esperado") and v["sinal_esperado"] != esp:
                probs.append(f"sinal_esperado {v['sinal_esperado']} incoerente com valor {val}")
            regra = SINAL_TABELA.get((cat, c["estrutura"]), SINAL_TABELA.get((cat, None)))
            if regra is not None and v["sinal_exigido"] != regra:
                probs.append(f"sinal_exigido={v['sinal_exigido']} difere da tabela do §11.1 ({regra}) em {v['id']}")
        else:  # percentual
            f_ = v.get("formula") or ""
            if f_.startswith("resultado consolidado 1S26 / receita"):
                calc = U(("3.11", "ÚLTIMO")) / U(("3.01", "ÚLTIMO")) * 100
            elif f_.startswith("(|resultado"):
                a1, a0 = abs(U((v["fontes"][0], "ÚLTIMO"))), abs(U((v["fontes"][0], "PENÚLTIMO")))
                calc = (a1 - a0) / a0 * 100
            elif f_.startswith("(resultado 1S26"):
                a1, a0 = U((v["fontes"][0], "ÚLTIMO")), U((v["fontes"][0], "PENÚLTIMO"))
                calc = (a1 - a0) / a0 * 100
            else:
                calc = None
            if calc is None or abs(calc - val) > Decimal("1e-15"):
                probs.append(f"percentual {v['id']}={val} x recalculado {calc}")
            if v["sinal_exigido"]:
                probs.append(f"percentual com sinal exigido ({v['id']})")
    # N3: aplicabilidade do percentual
    if cat == "N3":
        k0 = [k for k in fonte_val if k[1] == "PENÚLTIMO"]
        r1 = next((fonte_val[k] for k in fonte_val if k[1] == "ÚLTIMO"), None)
        r0 = fonte_val[k0[0]] if k0 else None
        tem_pct = any(v["tipo"] == "percentual" for v in c["valores_esperados"])
        deve = r1 is not None and r0 is not None and r0 != 0 and (r1 > 0) == (r0 > 0)
        if tem_pct != deve:
            probs.append(f"aplicabilidade do % N3: exigido={tem_pct}, regra={deve} ({r1} vs {r0})")
        ev["n3"] = {"r1": str(r1), "r0": str(r0), "regra": c.get("regra_percentual_n3")}
    # 4. texto do gabarito
    txt = c["gabarito"]
    for v in c["valores_esperados"]:
        val = Decimal(v["valor"])
        if v["tipo"] == "monetario":
            s = fmt_mil(val / 1000)
            m = re.search(r"([-−]?)\s*" + re.escape(s) + r"(?![\d.])", txt)
            if not m:
                probs.append(f"texto do gabarito não contém {s} ({v['id']})")
            elif val < 0 and not m.group(1) and v.get("formula") is None:
                probs.append(f"texto do gabarito sem sinal negativo para {s}")
        else:
            s = f"{abs(val):.2f}".replace(".", ",") + "%"
            if s not in txt:
                probs.append(f"texto do gabarito não contém {s}")
    if cat == "E2" and c["estrutura"] in ("nao_financeira", "holding"):
        caixa, divida = U(("1.01.01", "ÚLTIMO")), U(("2.01.04", "ÚLTIMO")) + U(("2.02.01", "ÚLTIMO"))
        concl = "mais caixa" if caixa > divida else "mais empréstimos e financiamentos"
        if concl not in txt:
            probs.append(f"conclusão E2 do texto difere de '{concl}'")
        ev["e2"] = {"caixa": str(caixa), "divida": str(divida), "conclusao": concl}
    if cat == "N3":
        r1, r0 = Decimal(ev["n3"]["r1"]), Decimal(ev["n3"]["r0"])
        if r1 > 0 and r0 > 0:
            kw = "aumento" if r1 > r0 else "redução"
        elif r1 < 0 and r0 < 0:
            kw = "prejuízo maior" if abs(r1) > abs(r0) else "prejuízo menor"
        else:
            kw = None
        if kw and kw not in txt:
            avisos.append(f"palavra de direção esperada '{kw}' ausente no texto")
        ev["n3"]["direcao"] = kw
    # 5. N4: cadeia
    if cat == "N4":
        cad = c["cadeia_n4"]
        nos = {n["cd_conta"]: n for n in cad["nos"]}
        for n in cad["nos"]:
            for per, campo in (("ÚLTIMO", "valor_1s26_mil"), ("PENÚLTIMO", "valor_1s25_mil")):
                if fonte_val.get((n["cd_conta"], per)) != Decimal(n[campo]):
                    probs.append(f"nó {n['cd_conta']} {per} difere da fonte")
        comp = cad["componentes_por_magnitude"]
        for cm in comp:
            s1 = sum(fonte_val[(k, "ÚLTIMO")] for k in cm["cd_contas"]); s0 = sum(fonte_val[(k, "PENÚLTIMO")] for k in cm["cd_contas"])
            if (Decimal(cm["valor_1s26_mil"]), Decimal(cm["valor_1s25_mil"]), Decimal(cm["variacao_mil"])) != (s1, s0, s1 - s0):
                probs.append(f"componente {cm['componente']} não confere")
        res = [n for n in cad["nos"] if n["no"] == "resultado"][0]
        dres = Decimal(res["valor_1s26_mil"]) - Decimal(res["valor_1s25_mil"])
        if sum(Decimal(cm["variacao_mil"]) for cm in comp) != dres or Decimal(cad["variacao_resultado_mil"]) != dres:
            probs.append("fechamento das variações não confere")
        for per in ("valor_1s26_mil", "valor_1s25_mil"):
            if sum(Decimal(cm[per]) for cm in comp) != Decimal(res[per]):
                avisos.append(f"soma dos níveis dos componentes ≠ resultado em {per} (componentes omitidos ou nulos)")
        mags = [abs(Decimal(cm["variacao_mil"])) for cm in comp]
        if mags != sorted(mags, reverse=True):
            probs.append("componentes fora da ordem de magnitude")
        for cm in comp:
            for campo in ("valor_1s26_mil", "valor_1s25_mil", "variacao_mil"):
                if fmt_mil(Decimal(cm[campo])) not in txt:
                    probs.append(f"texto N4 sem {cm[campo]} ({cm['componente']})")
        ev["n4"] = {"variacao": str(dres), "componentes": [(cm["descricao"], cm["variacao_mil"]) for cm in comp]}
    # 6. disponibilidade x contexto congelado
    L = linhas_ctx(cid)
    cabs = [t.splitlines()[0] for t in CTX[cid]]
    if not all("(Consolidado)" in x for x in cabs):
        probs.append(f"contexto com tabela não consolidada: {cabs}")
    tem_dre = any("Demonstração de Resultado" in x for x in cabs)
    # 6a. linhas citadas na justificativa existem literalmente (rótulo, atual, anterior) na tabela certa
    citadas = re.findall(r"(\[(?:DRE|BPA|BPP|DFC)\])\s+(.+?)\s{2,}(-?[\d.,]+)\s+\(anterior:\s*(-?[\d.,]+)\)", c["justificativa_disponibilidade"])
    for sig, lab, a1, a0 in citadas:
        ok = any(SIG[sig] in norm(cab) and l == norm(lab) and v1 == num_ctx(a1) and v0 == num_ctx(a0) for cab, l, v1, v0, _ in L)
        if not ok:
            probs.append(f"linha citada na justificativa não encontrada no contexto: {sig} {lab.strip()}")
    # 6b. conceito exigido no contexto: mesma tabela, mesmo rótulo, mesmo valor e mesmo período
    necessarios = [f for f in c["fontes_gabarito"]] if cat != "N4" else []
    achados, faltam = [], []
    for f in necessarios:
        alvo = Decimal(f["vl_conta_cvm"]); col = 2 if f["ordem_exerc"] == "ÚLTIMO" else 3
        hit = [x for x in L if TAB[f["arquivo_cvm"]] in norm(x[0]) and x[1] == norm(f["ds_conta"]) and x[col] == alvo]
        (achados if hit else faltam).append(f"{f['cd_conta']}/{f['ordem_exerc']}")
    # regra 2 (N2/N3 pela DFC): linha da DFC "resultado do período" com o mesmo valor
    via_dfc = False
    if cat in ("N2", "N3") and faltam:
        r1 = next(Decimal(f["vl_conta_cvm"]) for f in c["fontes_gabarito"] if f["ordem_exerc"] == "ÚLTIMO")
        r0 = next((Decimal(f["vl_conta_cvm"]) for f in c["fontes_gabarito"] if f["ordem_exerc"] == "PENÚLTIMO"), None)
        dfc = [x for x in L if "fluxo de caixa" in norm(x[0]) and re.search(r"(lucro|resultado).*(do periodo|liquido do periodo)", x[1])
               and "antes" not in x[1] and x[2] == r1 and (r0 is None or x[3] == r0)]
        via_dfc = bool(dfc)
    valor_em_qualquer_lugar = []
    for f in necessarios:
        alvo = Decimal(f["vl_conta_cvm"]); col = 2 if f["ordem_exerc"] == "ÚLTIMO" else 3
        valor_em_qualquer_lugar += [f"{f['cd_conta']}/{f['ordem_exerc']} em '{x[4][:60]}'" for x in L if x[col] == alvo
                                    and not (TAB[f["arquivo_cvm"]] in norm(x[0]) and x[1] == norm(f["ds_conta"]))]
    disp = c["disponibilidade"]
    if cat == "N4":
        nos_fora = c["justificativa_disponibilidade"]
        esperado = "presente" if tem_dre else None
        if tem_dre and disp != "presente":
            probs.append("N4 com DRE no contexto mas não presente")
        if not tem_dre and disp == "presente":
            probs.append("N4 presente sem DRE no contexto")
        ev["disp"] = {"dre_no_contexto": tem_dre, "justificativa": c["justificativa_disponibilidade"][:200]}
    else:
        todos = not faltam or via_dfc
        if disp == "presente" and not todos:
            probs.append(f"presente, mas faltam no contexto: {faltam}")
        if disp in ("parcial", "ausente") and not faltam:
            probs.append("parcial/ausente, mas todos os conceitos exigidos estão no contexto")
        if disp == "ausente" and achados:
            probs.append(f"ausente, mas há insumo no contexto: {achados}")
        if disp == "parcial" and cat in ("E1", "E2") and not achados:
            avisos.append("parcial sem nenhum insumo exato no contexto (verificar regra de disponibilidade)")
        if via_dfc:
            avisos.append("presente pela regra 2 (DFC 'resultado do período')")
        if valor_em_qualquer_lugar and disp != "presente":
            avisos.append(f"valor exigido aparece no contexto em outra linha: {valor_em_qualquer_lugar}")
        ev["disp"] = {"achados": achados, "faltam": faltam, "via_dfc": via_dfc, "tem_dre": tem_dre}
    rel[cid] = {"id": cid, "ticker": tk, "categoria": cat, "estrutura": c["estrutura"], "disponibilidade": disp,
                "atencao_humana": bool(c["revisao_tecnica"].get("atencao_humana")), "problemas": probs, "avisos": avisos,
                "evidencia": ev, "gabarito": txt, "justificativa_disponibilidade": c["justificativa_disponibilidade"]}

json.dump({"sha256_zip": SHA_ZIP, "versoes": VERS, "casos": rel}, open(os.path.join(AQUI, "etapa0_resultado.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1, default=str)
for grupo, sel in (("78 restantes", lambda r: not r["atencao_humana"]), ("18 atencao_humana", lambda r: r["atencao_humana"])):
    rs = [r for r in rel.values() if sel(r)]
    print(f"\n== {grupo}: {len(rs)} | com problema: {sum(bool(r['problemas']) for r in rs)} | com aviso: {sum(bool(r['avisos']) for r in rs)}")
    for r in rs:
        if r["problemas"] or r["avisos"]:
            print(f"  {r['id']:9s} [{r['disponibilidade']}] P={r['problemas']} | A={r['avisos']}")
print("\nversões:", {tk: (v["versao_dataset"], v["versoes_no_indice"], v["compativel"]) for tk, v in VERS.items()})
