# Análise dos resultados RAGAS congelados do TCC 2 (commit d78d5a5): base analítica, estatísticas
# descritivas e tabelas mecânicas usadas na análise qualitativa diagnóstica.
#
# Só lê: resultados RAGAS brutos, coleta congelada (via executor), anotações de comportamento e
# pendências. Não lê a exatidão nem o gabarito, e não chama LLM/API.
#
#   python avaliacao/ragas/avaliacao_tcc2/analise/analisar_resultados_ragas.py gerar
#   python avaliacao/ragas/avaliacao_tcc2/analise/analisar_resultados_ragas.py verificar
#
# "gerar" cria as três saídas de forma exclusiva (recusa se já existirem). "verificar" recalcula
# tudo em memória e compara byte a byte com as saídas versionadas. Antes de qualquer cálculo,
# os 387 arquivos RAGAS brutos e as anotações são conferidos contra o commit dos resultados.
import csv, hashlib, io, json, math, os, re, statistics as st, subprocess, sys
from collections import Counter

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "avaliacao", "ragas"))
import avaliar_respostas_tcc2 as A  # noqa: E402

COMMIT_RESULTADOS = "d78d5a5ddfdbc29491377e28ac98d665183ea0ce"
DIR_BRUTOS = "avaliacao/ragas/avaliacao_tcc2/ragas"
N_BRUTOS = 387
METRICAS = ("faithfulness", "answer_relevancy")
SAIDAS = ("base_analitica_ragas.csv", "resultados_descritivos_ragas.json", "tabelas_mecanicas_ragas.json")

# Marcadores textuais EXPLORATÓRIOS, definidos depois da observação dos scores (não pré-registrados).
RE_IMPOSSIVEL = r"não (é|seria) possível|não pode(m)? ser determinad|impossibilitando"
RE_NAO_ESPECIFICA = r"não (especific|mencion|contê|contém|apresent|informa|há indicação|detalha)"
RE_PERIODO_NOMEADO = r"semestre de 202[56]|30 de junho de 2026"
# Varredura dos contextos: marcas de data/período e nome da empresa (limite de palavra).
RE_DATA_CONTEXTO = r"20\d\d|semestre|junho|trimestre|exercício|\b1S|\b6M"
NOMES_EMPRESA = {"AURE3": "Auren", "BBAS3": "Banco do Brasil", "CEAB3": "C&A", "IRBR3": "IRB", "ITSA4": "Itaúsa",
                 "ITUB4": "Itaú", "LAVV3": "Lavvi", "LWSA3": "Locaweb", "POMO4": "Marcopolo", "VALE3": "Vale",
                 "WEGE3": "WEG", "ZAMP3": "Zamp"}


def git(*args):
    return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")


def sha256_arquivo(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def conferir_congelados():
    """Brutos e anotações idênticos ao commit dos resultados; devolve o hash do inventário dos brutos."""
    rastreados = git("ls-tree", "-r", "--name-only", COMMIT_RESULTADOS, "--", DIR_BRUTOS).stdout.split()
    assert len(rastreados) == N_BRUTOS, f"esperados {N_BRUTOS} brutos no commit, há {len(rastreados)}"
    comport = "avaliacao/ragas/avaliacao_tcc2/comportamento"
    d = git("diff", "--quiet", COMMIT_RESULTADOS, "--", DIR_BRUTOS, comport)
    assert d.returncode == 0, "brutos RAGAS ou anotações diferem do commit dos resultados"
    s = git("status", "--porcelain", "--untracked-files=all", "--", DIR_BRUTOS, comport).stdout.strip()
    assert not s, f"alterações ou arquivos extras nos congelados:\n{s}"
    em_disco = sorted(os.path.relpath(os.path.join(r, f), RAIZ).replace(os.sep, "/")
                      for r, _, fs in os.walk(os.path.join(RAIZ, *DIR_BRUTOS.split("/"))) for f in fs)
    assert em_disco == sorted(rastreados), "arquivos em disco diferem dos rastreados"
    linhas = "".join(f"{sha256_arquivo(os.path.join(RAIZ, *p.split('/')))}  {p}\n" for p in em_disco)
    return hashlib.sha256(linhas.encode("utf-8")).hexdigest()


def ler_json(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def calcular():
    sha_inventario = conferir_congelados()
    ds, sha_ds, casos = A.carregar_entradas()
    base_dir = os.path.join(A.SAIDA_PADRAO, "ragas")
    anot = {r["id"]: r for r in ler_json(A.arquivo_anotacoes(A.SAIDA_PADRAO))["registros"]}
    val = A.validar_anotacoes(casos, A.SAIDA_PADRAO)
    assert val["contagem"] == {"VALIDO": 91, "PENDENTE_OPERACIONAL": 5, "INCOMPLETO": 0, "INVALIDO": 0}
    falhas, configs = [], {m: set() for m in METRICAS}

    def final(metrica, cid):
        """Tentativa 2 válida, se existir; senão tentativa 1 válida. Inválidas nunca entram."""
        for t in (2, 1):
            p = os.path.join(base_dir, metrica, f"{cid}.tentativa_0{t}.json")
            if os.path.exists(p):
                r = ler_json(p)
                configs[metrica].add(json.dumps(r["avaliador"], sort_keys=True, ensure_ascii=False))
                if r["valido"]:
                    return r["score"], t
                if t == 2:
                    falhas.append(f"{metrica}/{cid}: tentativa 2 inválida")
                    return None, t
        falhas.append(f"{metrica}/{cid}: sem resultado válido")
        return None, None

    linhas = []
    for c in casos:
        cid = c["case_id"]
        f, tf = final("faithfulness", cid)
        ar, ta = final("answer_relevancy", cid)
        st_c = val["casos"][cid]["status"]
        reg = anot[cid]
        linhas.append({
            "id": cid, "ticker": c["ticker"], "estrutura": c["estrutura"], "categoria": c["categoria"],
            "disponibilidade": c["disponibilidade"], "truncada_por_limite": c["truncada_na_geracao"],
            "classe_comportamento": reg["classe"] if st_c == "VALIDO" else "SEM_CLASSE_PENDENTE_OPERACIONAL",
            "status_comportamento": st_c,
            "abstencao_em_caso_presente": reg["abstencao_em_caso_presente"] if st_c == "VALIDO" else None,
            "faithfulness": f, "faithfulness_tentativa_final": tf, "faithfulness_reavaliado": tf == 2,
            "answer_relevancy": ar, "answer_relevancy_tentativa_final": ta})

    ids = [l["id"] for l in linhas]
    aud = {
        "96 ids, únicos, iguais à coleta": len(ids) == 96 == len(set(ids)) and set(ids) == {c["case_id"] for c in casos},
        "96 Faithfulness finais": sum(l["faithfulness"] is not None for l in linhas) == 96,
        "96 Answer Relevancy finais": sum(l["answer_relevancy"] is not None for l in linhas) == 96,
        "nenhum NaN": all(isinstance(l[m], (int, float)) and math.isfinite(l[m]) for l in linhas for m in METRICAS),
        "domínio [0, 1]": all(0.0 <= l[m] <= 1.0 for l in linhas for m in METRICAS),
        "tentativa final F = 2 só em POMO4_N2 e ITSA4_E1": sorted(l["id"] for l in linhas if l["faithfulness_tentativa_final"] == 2) == ["ITSA4_E1", "POMO4_N2"],
        "tentativa final AR = 1 nos 96": all(l["answer_relevancy_tentativa_final"] == 1 for l in linhas),
        "sem falhas de seleção": not falhas,
    }
    assert all(aud.values()), (aud, falhas)
    assert all(len(v) == 1 for v in configs.values()), "configuração do avaliador varia entre resultados"

    # ---------------- base analítica (CSV) ----------------
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=list(linhas[0]), lineterminator="\r\n")
    w.writeheader()
    w.writerows(linhas)
    csv_txt = buf.getvalue()

    # ---------------- estatísticas descritivas ----------------
    def resumo(x, completo=False):
        x = list(x)
        if not x:
            return {"n": 0}
        r = {"n": len(x), "media": st.fmean(x), "mediana": st.median(x),
             "dp": st.stdev(x) if len(x) > 1 else None, "min": min(x), "max": max(x)}
        if completo:
            q = st.quantiles(x, n=4, method="inclusive")   # interpolação linear
            r["q1"], r["q3"] = q[0], q[2]
        return r

    def faixas(x):
        x = list(x)
        def cont(f):
            return sum(1 for v in x if f(v))
        return {"=0": cont(lambda v: v == 0), "(0;0,25]": cont(lambda v: 0 < v <= 0.25),
                "(0,25;0,50]": cont(lambda v: 0.25 < v <= 0.5), "(0,50;0,75]": cont(lambda v: 0.5 < v <= 0.75),
                "(0,75;1)": cont(lambda v: 0.75 < v < 1), "=1": cont(lambda v: v == 1)}

    def ranks(x):
        ordem = sorted(range(len(x)), key=lambda i: x[i])
        r = [0.0] * len(x)
        i = 0
        while i < len(x):
            j = i
            while j + 1 < len(x) and x[ordem[j + 1]] == x[ordem[i]]:
                j += 1
            for k in range(i, j + 1):
                r[ordem[k]] = (i + j) / 2 + 1
            i = j + 1
        return r

    def pearson(a, b):
        ma, mb = st.fmean(a), st.fmean(b)
        num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
        return num / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))

    avaliador = {m: json.loads(next(iter(configs[m]))) for m in METRICAS}
    res = {"commit_resultados": COMMIT_RESULTADOS,
           "regra_tentativa_final": "tentativa 2 válida se existir; senão tentativa 1 válida",
           "auditoria": aud, "global": {}, "faixas": {}, "recortes": {}}
    for m in METRICAS:
        v = [l[m] for l in linhas]
        res["global"][m] = resumo(v, completo=True)
        res["faixas"][m] = faixas(v)

    def recorte(nome, chave, filtro=lambda l: True):
        grupos = {}
        for l in linhas:
            if filtro(l):
                grupos.setdefault(chave(l), []).append(l)
        res["recortes"][nome] = {g: {m: resumo(l[m] for l in ls) for m in METRICAS}
                                 for g, ls in sorted(grupos.items(), key=lambda kv: str(kv[0]))}

    valido = lambda l: l["status_comportamento"] == "VALIDO"  # noqa: E731
    recorte("disponibilidade", lambda l: l["disponibilidade"])
    recorte("truncamento", lambda l: "truncado" if l["truncada_por_limite"] else "nao_truncado")
    recorte("classe_91", lambda l: l["classe_comportamento"], valido)
    recorte("classe_91_por_disponibilidade", lambda l: f'{l["disponibilidade"]}|{l["classe_comportamento"]}', valido)
    recorte("abstencao_presente_69", lambda l: l["abstencao_em_caso_presente"],
            lambda l: valido(l) and l["disponibilidade"] == "presente")
    res["pendentes_operacionais"] = [{k: l[k] for k in ("id", "disponibilidade", "faithfulness", "faithfulness_tentativa_final", "answer_relevancy")}
                                     for l in linhas if not valido(l)]
    f = [l["faithfulness"] for l in linhas]
    a = [l["answer_relevancy"] for l in linhas]
    res["correlacao"] = {"n": 96, "pearson": pearson(f, a), "spearman": pearson(ranks(f), ranks(a))}
    cols = ("id", "disponibilidade", "classe_comportamento", "faithfulness", "answer_relevancy")
    res["menores_faithfulness"] = [{k: l[k] for k in cols} for l in sorted(linhas, key=lambda l: (l["faithfulness"], l["id"]))[:10]]
    res["menores_answer_relevancy"] = [{k: l[k] for k in cols} for l in sorted(linhas, key=lambda l: (l["answer_relevancy"], l["id"]))[:10]]
    res["maiores_diferencas"] = [{**{k: l[k] for k in cols}, "dif_abs": abs(l["faithfulness"] - l["answer_relevancy"])}
                                 for l in sorted(linhas, key=lambda l: (-abs(l["faithfulness"] - l["answer_relevancy"]), l["id"]))[:10]]
    res["nota_empates"] = ("menores_answer_relevancy e maiores_diferencas são decididas por desempate alfabético: "
                           "75 casos empatam em AR = 0 e 47 em |F - AR| = 1.")
    res["proveniencia"] = {
        "commit_resultados": COMMIT_RESULTADOS, "denominador_global": 96, "denominador_classe": 91,
        "arquivos_ragas_brutos": N_BRUTOS,
        "sha256_inventario_ragas_brutos": sha_inventario,
        "formato_inventario": "sha256 de linhas '<sha256>  <caminho relativo com />\\n', ordenadas por caminho",
        "sha256_anotacoes_comportamento": sha256_arquivo(A.arquivo_anotacoes(A.SAIDA_PADRAO)),
        "sha256_pendencias_comportamento": sha256_arquivo(A.arquivo_pendencias(A.SAIDA_PADRAO)),
        "sha256_dataset": sha_ds,
        "avaliador": avaliador,
        "estatistica": "dp amostral (n-1); quartis por interpolação linear (statistics.quantiles, method='inclusive'); "
                       "Spearman = Pearson sobre postos médios",
    }

    # ---------------- tabelas mecânicas (análise qualitativa) ----------------
    resp = {c["case_id"]: c["resposta"] for c in casos}
    ctxs = {c["case_id"]: c["contextos"] for c in casos}
    P = []
    for l in linhas:
        an = anot[l["id"]]
        r = resp[l["id"]]
        imp = bool(re.search(RE_IMPOSSIVEL, r, re.I))
        nesp = bool(re.search(RE_NAO_ESPECIFICA, r, re.I))
        P.append({"id": l["id"], "disponibilidade": l["disponibilidade"], "truncada": l["truncada_por_limite"],
                  "grupo": ("PENDENTE_OPERACIONAL" if not valido(l) else
                            ("SEM_DESVIO|abstencao" if l["abstencao_em_caso_presente"] else "SEM_DESVIO|sem_abstencao")
                            if l["classe_comportamento"] == "SEM_DESVIO" else l["classe_comportamento"]),
                  "F": l["faithfulness"], "AR": l["answer_relevancy"],
                  "rotulos": "".join(x["rotulo"] for x in an["afirmacoes"]),
                  "n_afirmacoes": len(an["afirmacoes"]),
                  "declara_limitacao": an["declara_limitacao"],
                  "entrega_informacao_sustentada": an["entrega_informacao_sustentada"],
                  "abstencao_em_caso_presente": l["abstencao_em_caso_presente"],
                  "m_impossivel": imp, "m_nao_especifica": nesp, "m_ressalva": imp or nesp,
                  "m_periodo_nomeado": bool(re.search(RE_PERIODO_NOMEADO, r, re.I))})
    por = {p["id"]: p for p in P}

    def ids(cond):
        return sorted(p["id"] for p in P if cond(p))

    def media(cond, k="F"):
        v = [p[k] for p in P if cond(p)]
        return st.fmean(v) if v else None

    T = {"definicoes": {
        "marcadores_exploratorios": {"m_impossivel": RE_IMPOSSIVEL, "m_nao_especifica": RE_NAO_ESPECIFICA,
                                     "m_ressalva": "m_impossivel OU m_nao_especifica",
                                     "m_periodo_nomeado": RE_PERIODO_NOMEADO,
                                     "aplicacao": "re.search(..., resposta congelada, re.IGNORECASE)",
                                     "status": "exploratórios, definidos após a observação dos scores; não pré-registrados"},
        "fragmento_sem_conteudo": "truncada E 0 afirmações anotadas E declara_limitacao = false",
        "so_declaracao_truncada": "truncada E 0 afirmações anotadas E declara_limitacao = true",
        "grupo": "classe de comportamento; SEM_DESVIO separado por abstencao_em_caso_presente; 5 pendentes à parte"}}

    # varredura dos contextos
    assert set(NOMES_EMPRESA) == {c["ticker"] for c in casos}
    com_data = ids(lambda p: re.search(RE_DATA_CONTEXTO, "\n".join(ctxs[p["id"]]), re.I))
    com_nome = ids(lambda p: re.search(r"\b" + re.escape(NOMES_EMPRESA[p["id"].split("_")[0]]) + r"\b", "\n".join(ctxs[p["id"]])))
    cabecalhos = sorted({t.splitlines()[0] for c in casos for t in c["contextos"]})
    T["contextos"] = {"n": 96, "com_marca_de_data_ou_periodo": com_data, "com_nome_da_empresa": com_nome,
                      "cabecalhos_de_trecho": cabecalhos}

    # Faithfulness = 0
    T["faithfulness_zero"] = [{k: por[i][k] for k in ("id", "disponibilidade", "truncada", "grupo", "rotulos", "F", "AR",
                                                       "m_ressalva", "m_periodo_nomeado")} for i in ids(lambda p: p["F"] == 0)]

    # Answer Relevancy
    ar_pos = [p["AR"] for p in P if p["AR"] > 0]
    T["answer_relevancy_zero"] = {"n_zero_exato": sum(p["AR"] == 0.0 for p in P), "menor_positivo": min(ar_pos),
                                  "algum_negativo": any(p["AR"] < 0 for p in P)}
    grupos = sorted({p["grupo"] for p in P})
    T["decomposicao_ar_por_grupo"] = {g: {"total": len(ids(lambda p: p["grupo"] == g)),
                                          "ar_zero": len(ids(lambda p: p["grupo"] == g and p["AR"] == 0)),
                                          "ar_positivo": len(ids(lambda p: p["grupo"] == g and p["AR"] > 0)),
                                          "ar_zero_truncado": len(ids(lambda p: p["grupo"] == g and p["AR"] == 0 and p["truncada"])),
                                          "ar_zero_nao_truncado": len(ids(lambda p: p["grupo"] == g and p["AR"] == 0 and not p["truncada"]))}
                                      for g in grupos}
    T["ar_zero_por_truncamento"] = {t: {"ar_zero": len(ids(lambda p: p["truncada"] == v and p["AR"] == 0)),
                                        "n": len(ids(lambda p: p["truncada"] == v))}
                                    for t, v in (("truncado", True), ("nao_truncado", False))}
    T["ressalva_x_ar"] = {k: {"n": len(ids(lambda p: p["m_ressalva"] == v)),
                              "ar_zero": len(ids(lambda p: p["m_ressalva"] == v and p["AR"] == 0)),
                              "ar_positivo": len(ids(lambda p: p["m_ressalva"] == v and p["AR"] > 0)),
                              "ids_ar_positivo": ids(lambda p: p["m_ressalva"] == v and p["AR"] > 0),
                              "ids_ar_zero": ids(lambda p: p["m_ressalva"] == v and p["AR"] == 0) if not v else None}
                          for k, v in (("com_ressalva", True), ("sem_ressalva", False))}
    T["sem_ressalva_ar_zero_detalhe"] = [{k: por[i][k] for k in ("id", "truncada", "grupo", "n_afirmacoes", "rotulos", "declara_limitacao")}
                                         for i in T["ressalva_x_ar"]["sem_ressalva"]["ids_ar_zero"]]
    sdsa = lambda p: p["grupo"] == "SEM_DESVIO|sem_abstencao"  # noqa: E731
    T["sem_desvio_sem_abstencao"] = {
        "entrega_com_ressalva": {"ar_zero": ids(lambda p: sdsa(p) and p["entrega_informacao_sustentada"] and p["m_ressalva"] and p["AR"] == 0),
                                 "ar_positivo": ids(lambda p: sdsa(p) and p["entrega_informacao_sustentada"] and p["m_ressalva"] and p["AR"] > 0)},
        "entrega_sem_ressalva": {"ar_zero": ids(lambda p: sdsa(p) and p["entrega_informacao_sustentada"] and not p["m_ressalva"] and p["AR"] == 0),
                                 "ar_positivo": ids(lambda p: sdsa(p) and p["entrega_informacao_sustentada"] and not p["m_ressalva"] and p["AR"] > 0)},
        "sem_entrega": {"ar_zero": ids(lambda p: sdsa(p) and not p["entrega_informacao_sustentada"] and p["AR"] == 0),
                        "ar_positivo": ids(lambda p: sdsa(p) and not p["entrega_informacao_sustentada"] and p["AR"] > 0)},
        "f_media": media(sdsa)}
    T["periodo_nomeado_sem_ressalva"] = [{k: por[i][k] for k in ("id", "truncada", "disponibilidade", "rotulos", "F", "AR")}
                                         for i in ids(lambda p: p["m_periodo_nomeado"] and not p["m_ressalva"])]

    # abstenções em caso presente
    ab = lambda p: p["abstencao_em_caso_presente"] is True  # noqa: E731
    T["abstencao_presente"] = {
        "n": len(ids(ab)), "f_media": media(ab), "f_igual_1": len(ids(lambda p: ab(p) and p["F"] == 1)),
        "f_menor_1": [{k: por[i][k] for k in ("id", "F", "rotulos", "truncada")} for i in ids(lambda p: ab(p) and p["F"] < 1)],
        "ar_zero": len(ids(lambda p: ab(p) and p["AR"] == 0)),
        "entrega_informacao_sustentada": ids(lambda p: ab(p) and p["entrega_informacao_sustentada"]),
        "f_media_com_entrega": media(lambda p: ab(p) and p["entrega_informacao_sustentada"]),
        "f_media_sem_entrega": media(lambda p: ab(p) and not p["entrega_informacao_sustentada"]),
        "comparacao_presente_sem_marca": {"n": len(ids(sdsa)), "f_media": media(sdsa),
                                          "ar_positivo": len(ids(lambda p: sdsa(p) and p["AR"] > 0))}}
    T["classes_nao_sem_desvio"] = [{k: por[i][k] for k in ("id", "grupo", "disponibilidade", "truncada", "rotulos", "F", "AR")}
                                   for i in ids(lambda p: p["grupo"] in ("ABSTENCAO_ADEQUADA", "RESPOSTA_PARCIAL_ADEQUADA", "EXTRAPOLACAO"))]
    T["f_um_ar_zero_por_grupo"] = dict(sorted(Counter(p["grupo"] for p in P if p["F"] == 1 and p["AR"] == 0).items()))

    # truncamento
    tr = lambda p: p["truncada"]  # noqa: E731
    frag = lambda p: tr(p) and p["n_afirmacoes"] == 0 and not p["declara_limitacao"]  # noqa: E731
    so_decl = lambda p: tr(p) and p["n_afirmacoes"] == 0 and p["declara_limitacao"]  # noqa: E731
    T["truncamento_2x2"] = {t: {"n": len(ids(lambda p: tr(p) == v)), "f_zero": len(ids(lambda p: tr(p) == v and p["F"] == 0)),
                                "f_positivo": len(ids(lambda p: tr(p) == v and p["F"] > 0))}
                            for t, v in (("truncado", True), ("nao_truncado", False))}
    T["truncamento_subgrupos"] = {
        "fragmento_sem_conteudo": {"ids": ids(frag), "f_media": media(frag), "f_zero": ids(lambda p: frag(p) and p["F"] == 0),
                                   "detalhe": [{k: por[i][k] for k in ("id", "F", "AR")} for i in ids(frag)]},
        "truncado_com_afirmacao_ou_declaracao": {"n": len(ids(lambda p: tr(p) and not frag(p))),
                                                 "f_media": media(lambda p: tr(p) and not frag(p)),
                                                 "f_zero": ids(lambda p: tr(p) and not frag(p) and p["F"] == 0)},
        "so_declaracao_truncada": [{k: por[i][k] for k in ("id", "F", "AR")} for i in ids(so_decl)],
        "nao_truncado": {"n": len(ids(lambda p: not tr(p))), "f_media": media(lambda p: not tr(p))}}
    T["por_caso"] = P

    j1 = json.dumps(res, ensure_ascii=False, indent=1) + "\n"
    j2 = json.dumps(T, ensure_ascii=False, indent=1) + "\n"
    return {SAIDAS[0]: csv_txt.encode("utf-8"), SAIDAS[1]: j1.encode("utf-8"), SAIDAS[2]: j2.encode("utf-8")}


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else ""
    if modo not in ("gerar", "verificar"):
        sys.exit("uso: analisar_resultados_ragas.py gerar|verificar")
    saidas = calcular()
    if modo == "gerar":
        for nome, conteudo in saidas.items():
            with open(os.path.join(AQUI, nome), "xb") as fh:   # exclusivo: nunca sobrescreve
                fh.write(conteudo)
            print(f"gravado {nome}  sha256={hashlib.sha256(conteudo).hexdigest()}")
    else:
        ok = True
        for nome, conteudo in saidas.items():
            with open(os.path.join(AQUI, nome), "rb") as fh:
                igual = fh.read() == conteudo
            ok &= igual
            print(f"{'OK    ' if igual else 'DIFERE'} {nome}  sha256={hashlib.sha256(conteudo).hexdigest()}")
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
