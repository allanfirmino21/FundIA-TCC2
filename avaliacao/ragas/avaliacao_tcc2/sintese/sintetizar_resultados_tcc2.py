# Cruzamentos da síntese integrada do TCC 2: RAGAS × comportamento × exatidão (original e
# Emenda 5) × disponibilidade. Só lê artefatos versionados e congelados; não recalcula nem
# substitui nenhuma avaliação, não cria classes e não chama LLM/API.
#
#   python avaliacao/ragas/avaliacao_tcc2/sintese/sintetizar_resultados_tcc2.py gerar
#   python avaliacao/ragas/avaliacao_tcc2/sintese/sintetizar_resultados_tcc2.py verificar
#
# "gerar" grava sintese_resultados_tcc2.json de forma exclusiva (recusa se já existir).
# "verificar" recalcula em memória e compara byte a byte com o arquivo versionado; não grava nada.
# Antes de qualquer cálculo, cada fonte é conferida pelo SHA-256 fixado abaixo.
#
# Fontes das quatro dimensões, mantidas separadas:
#   - métricas RAGAS (F, AR): base_analitica_ragas.csv da análise congelada (que o script
#     analisar_resultados_ragas.py reconstrói e confere a partir dos 387 brutos);
#   - comportamento: anotacoes_comportamento.json e pendencias_comportamento.json;
#   - exatidão: resultado_exatidao.json (original) e resultado_exatidao_emenda5.json;
#   - disponibilidade e truncamento: dataset congelado e coleta congelada (via executor).
import csv, hashlib, json, os, statistics as st, sys
from collections import Counter

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "avaliacao", "ragas"))
import avaliar_respostas_tcc2 as A  # noqa: E402
import coletar_respostas_tcc2 as C  # noqa: E402

SAIDA = "sintese_resultados_tcc2.json"
FONTES = {
    "avaliacao/ragas/dataset_tcc2.json": "313bdf359fdeabb063ceec3bcca12ebfe3b52caae346b3ff1d9f3dc23196bc5e",
    "avaliacao/ragas/avaliacao_tcc2/analise/base_analitica_ragas.csv": "8dd85190d7bae9283d26cecfc08136ee47a6b3efb334c256db57a0d284a2a1a4",
    "avaliacao/ragas/avaliacao_tcc2/comportamento/anotacoes_comportamento.json": "c83cf6cef724f88ab35ac439978d13f0ad812c0ce25859ab7155eef97627b18f",
    "avaliacao/ragas/avaliacao_tcc2/comportamento/pendencias_comportamento.json": "d20f736187f69cd441a53795b4425ff212d54d7ee9274d79c894e02825976b71",
    "avaliacao/ragas/avaliacao_tcc2/exatidao/resultado_exatidao.json": "3c3e28c080a9884f53f1197bd0c4106fd414105b2aa4de3ff2928f401a05a6db",
    "avaliacao/ragas/avaliacao_tcc2/exatidao_emenda5/resultado_exatidao_emenda5.json": "22af220e529edd04ba97f5a6fc4c841188edc02f9bdb6e46ad4daba7e1cef04f",
}
DISP = ("presente", "parcial", "ausente")
ESTRUTURAS = ("nao_financeira", "banco", "holding", "resseguradora")
CLASSES_EXATIDAO = ("CORRETO", "PARCIALMENTE_CORRETO", "INCORRETO", "NAO_APLICAVEL")
CLASSES_COMPORTAMENTO = ("ABSTENCAO_ADEQUADA", "RESPOSTA_PARCIAL_ADEQUADA", "EXTRAPOLACAO", "ALUCINACAO")
SEM_DESVIO = "SEM_DESVIO"            # registro dos casos presente (comportamento.py: "não é classe")
PENDENTE = "PENDENTE_OPERACIONAL"   # Emenda 4: estado técnico, não é classe
TRUNCADOS_PARCIAIS = ("ITUB4_N3", "ZAMP3_N3")   # PARCIALMENTE_CORRETO em presente com resposta truncada


def caminho(rel):
    return os.path.join(RAIZ, *rel.split("/"))


def sha256_arquivo(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def ler_json(rel):
    with open(caminho(rel), encoding="utf-8") as fh:
        return json.load(fh)


def r6(x):
    return None if x is None else round(float(x), 6)


def resumo(valores, ids=None):
    """n, média, mediana, dp amostral (n-1), mín, máx; com menos de 5 casos, lista os casos."""
    v = [float(x) for x in valores]
    if not v:
        return {"n": 0}
    out = {"n": len(v), "media": r6(st.mean(v)), "mediana": r6(st.median(v)),
           "dp": r6(st.stdev(v)) if len(v) > 1 else None, "min": r6(min(v)), "max": r6(max(v))}
    if ids is not None and len(v) < 5:
        out["casos"] = [{"id": i, "valor": r6(x)} for i, x in zip(ids, v)]
    return out


def contagem_exatidao(regs):
    c = Counter(x["classe"] for x in regs)
    na_n4 = sum(1 for x in regs if x["classe"] == "NAO_APLICAVEL" and x["motivo"].startswith("categoria"))
    ap = c["CORRETO"] + c["PARCIALMENTE_CORRETO"] + c["INCORRETO"]
    return {"n": len(regs), **{k: c[k] for k in CLASSES_EXATIDAO},
            "nao_aplicavel_n4": na_n4, "nao_aplicavel_sem_numero": c["NAO_APLICAVEL"] - na_n4,
            "aplicaveis": ap, "correto_sobre_aplicaveis": f"{c['CORRETO']}/{ap}" if ap else None,
            "taxa_correto": r6(c["CORRETO"] / ap) if ap else None}


def conferir_fontes():
    for rel, h in FONTES.items():
        s = sha256_arquivo(caminho(rel))
        assert s == h, f"fonte diferente da congelada: {rel} ({s})"


def carregar():
    conferir_fontes()
    _, sha_ds, casos = A.carregar_entradas()
    assert sha_ds == FONTES["avaliacao/ragas/dataset_tcc2.json"]
    original = A.conferir_resultado_exatidao(A.SAIDA_PADRAO, casos)      # selo, 96 respostas, classes finais
    e5 = ler_json("avaliacao/ragas/avaliacao_tcc2/exatidao_emenda5/resultado_exatidao_emenda5.json")
    assert C.selo_confere(e5), "selo do resultado da Emenda 5 não confere"
    assert e5["resultado_original"]["sha256"] == FONTES["avaliacao/ragas/avaliacao_tcc2/exatidao/resultado_exatidao.json"]
    with open(caminho("avaliacao/ragas/avaliacao_tcc2/analise/base_analitica_ragas.csv"), encoding="utf-8") as fh:
        base = {r["id"]: r for r in csv.DictReader(fh)}
    anot = {a["id"]: a for a in ler_json("avaliacao/ragas/avaliacao_tcc2/comportamento/anotacoes_comportamento.json")["registros"]}
    pend = ler_json("avaliacao/ragas/avaliacao_tcc2/comportamento/pendencias_comportamento.json")
    return casos, original, e5, base, anot, pend


def conferir_consistencia(casos, original, e5, base, anot, pend):
    """Integridade entre as fontes; devolve os ids dos 5 pendentes de comportamento."""
    por = {c["case_id"]: c for c in casos}
    eo = {x["case_id"]: x for x in original["resultados"]}
    e5r = {x["case_id"]: x for x in e5["resultados"]}
    ids = set(por)
    assert len(casos) == A.N_CASOS == 96 and ids == set(eo) == set(e5r) == set(base) == set(anot), "ids divergem"
    for i in ids:
        d = por[i]["disponibilidade"]
        assert d == eo[i]["disponibilidade"] == e5r[i]["disponibilidade"] == base[i]["disponibilidade"] == anot[i]["disponibilidade"], i
        t = por[i]["truncada_na_geracao"]
        assert t == eo[i]["truncada_na_geracao"] == e5r[i]["truncada_na_geracao"] and base[i]["truncada_por_limite"] == str(t), i
        assert por[i]["sha256_resposta"] == eo[i]["sha256_resposta"] == e5r[i]["sha256_resposta"] == anot[i]["sha256_resposta"], i
        assert e5r[i]["classe_original"] == eo[i]["classe"], i
        assert eo[i]["classe"] in CLASSES_EXATIDAO and e5r[i]["classe"] in CLASSES_EXATIDAO, i
        assert anot[i]["classe"] in CLASSES_COMPORTAMENTO + (SEM_DESVIO, None), i
    # equivalência dos rótulos dos casos sem classe de comportamento (sem alterar as anotações)
    sem_classe = {i for i in ids if anot[i]["classe"] is None}
    na_base = {i for i in ids if base[i]["classe_comportamento"] == "SEM_CLASSE_PENDENTE_OPERACIONAL"
               and base[i]["status_comportamento"] == PENDENTE}
    na_pend = {p["id"] for p in pend["pendencias"] if p["estado"] == "PENDENTE_POR_TRUNCAMENTO_E_REGRA_DO_VALIDADOR"}
    assert sem_classe == na_base == na_pend and len(sem_classe) == pend["denominador"]["pendentes_por_truncamento_e_regra_do_validador"] == 5
    assert pend["denominador"]["classificaveis"] == 96 - len(sem_classe) == 91
    for i in ids - sem_classe:
        assert base[i]["classe_comportamento"] == anot[i]["classe"] and base[i]["status_comportamento"] == "VALIDO", i
        assert str(anot[i]["abstencao_em_caso_presente"]) == base[i]["abstencao_em_caso_presente"], i
    for i in sem_classe:
        assert por[i]["truncada_na_geracao"] and anot[i]["abstencao_em_caso_presente"] is None, i
    return sorted(sem_classe)


def calcular() -> bytes:
    casos, original, e5, base, anot, pend = carregar()
    pendentes = conferir_consistencia(casos, original, e5, base, anot, pend)
    ordem = [c["case_id"] for c in casos]
    por = {c["case_id"]: c for c in casos}
    EX = {"original": {x["case_id"]: x for x in original["resultados"]},
          "emenda5": {x["case_id"]: x for x in e5["resultados"]}}
    F = {i: float(base[i]["faithfulness"]) for i in ordem}
    AR = {i: float(base[i]["answer_relevancy"]) for i in ordem}

    def disp(i):
        return por[i]["disponibilidade"]

    def situacao(i):
        return PENDENTE if i in pendentes else "classificado"

    def ids(cond, conjunto=None):
        return [i for i in (conjunto or ordem) if cond(i)]

    def comportamento_resumo(conj):
        cl = Counter(anot[i]["classe"] for i in conj if i not in pendentes)
        pres = [i for i in conj if disp(i) == "presente"]
        abst = [i for i in pres if anot[i]["abstencao_em_caso_presente"] is True]
        return {"n": len(conj), "classificaveis": len(conj) - sum(i in pendentes for i in conj),
                "pendentes_operacionais": [i for i in conj if i in pendentes],
                "classes": {k: cl[k] for k in CLASSES_COMPORTAMENTO},
                "registro_sem_desvio_presente": cl[SEM_DESVIO],
                "abstencao_em_caso_presente": {"n_presente": len(pres), "marcados": len(abst),
                                               "com_entrega_informacao_sustentada": sum(anot[i]["entrega_informacao_sustentada"] is True for i in abst),
                                               "sem_entrega": sum(anot[i]["entrega_informacao_sustentada"] is not True for i in abst)}}

    def ragas_resumo(conj):
        return {"faithfulness": resumo([F[i] for i in conj], conj), "answer_relevancy": resumo([AR[i] for i in conj], conj)}

    res = {
        "descricao": ("Cruzamentos da síntese integrada do TCC 2. Dimensões mantidas separadas: disponibilidade "
                      "(classificação prévia do dataset), comportamento (rubrica; SEM_DESVIO é registro dos casos "
                      "presente, não classe), exatidão numérica (original e Emenda 5, lado a lado) e métricas RAGAS "
                      "(Faithfulness e Answer Relevancy finais). Nenhuma medida é combinada em índice único. Estatísticas "
                      "descritivas, sem teste inferencial; células com menos de 5 casos listam os casos."),
        "convencoes": {
            "estatistica": "média, mediana, desvio-padrão amostral (n-1), mínimo e máximo; valores arredondados a 6 casas",
            "taxa_exatidao": "CORRETO / aplicáveis (CORRETO + PARCIALMENTE_CORRETO + INCORRETO); NAO_APLICAVEL à parte, separado em N4 e sem número",
            "exatidao_emenda5": "resultado adicional, concebido depois da observação dos resultados; reportar sempre ao lado do original",
            "ragas": "F e AR finais da base analítica congelada (tentativa final conforme a análise RAGAS); sem reinterpretação",
        },
        "proveniencia": {"fontes_sha256": FONTES, "sha256_SHA256_COLETA": A.SHA256_SHA256_COLETA,
                         "sha256_registro_exatidao_original": original["sha256_registro"],
                         "sha256_registro_exatidao_emenda5": e5["sha256_registro"]},
        "equivalencia_pendentes_comportamento": {
            "ids": pendentes,
            "rotulos_nas_fontes": {
                "anotacoes_comportamento.json": "classe = null, abstencao_em_caso_presente = null",
                "pendencias_comportamento.json": "estado = PENDENTE_POR_TRUNCAMENTO_E_REGRA_DO_VALIDADOR",
                "base_analitica_ragas.csv": "classe_comportamento = SEM_CLASSE_PENDENTE_OPERACIONAL; status_comportamento = PENDENTE_OPERACIONAL",
                "PROTOCOLO_RAGAS_TCC2.md, Emenda 4": "PENDENTE_OPERACIONAL",
            },
            "nesta_sintese": "situacao_comportamento = PENDENTE_OPERACIONAL e classe_comportamento = null; não é classe da rubrica",
            "conferido": "os três conjuntos de ids são idênticos; as anotações não foram alteradas",
        },
    }

    # denominadores e distribuições globais
    res["denominadores"] = {
        "casos": len(ordem),
        "ragas_validos": {"faithfulness": len(F), "answer_relevancy": len(AR)},
        "comportamento": {"classificaveis": len(ordem) - len(pendentes), "pendentes_operacionais": len(pendentes)},
        "exatidao": {v: {k: contagem_exatidao(list(EX[v].values()))[k] for k in ("aplicaveis", "NAO_APLICAVEL", "nao_aplicavel_n4", "nao_aplicavel_sem_numero")}
                     for v in EX},
        "disponibilidade": {d: len(ids(lambda i, d=d: disp(i) == d)) for d in DISP},
        "truncadas_max_tokens": len(ids(lambda i: por[i]["truncada_na_geracao"])),
    }
    res["distribuicoes_globais"] = {
        "disponibilidade": res["denominadores"]["disponibilidade"],
        "comportamento": comportamento_resumo(ordem),
        "exatidao": {v: contagem_exatidao(list(EX[v].values())) for v in EX},
        "ragas": ragas_resumo(ordem),
    }

    # por disponibilidade
    res["por_disponibilidade"] = {}
    for d in DISP:
        conj = ids(lambda i, d=d: disp(i) == d)
        res["por_disponibilidade"][d] = {
            "n": len(conj), "truncadas": sum(por[i]["truncada_na_geracao"] for i in conj),
            "comportamento": comportamento_resumo(conj),
            "exatidao": {v: contagem_exatidao([EX[v][i] for i in conj]) for v in EX},
            "ragas": ragas_resumo(conj)}

    # RAGAS por classe de exatidão (Protocolo, Seção 12, item 2), por disponibilidade e no total
    res["ragas_por_classe_exatidao"] = {}
    for v in EX:
        bloco = {}
        for recorte in DISP + ("todos",):
            conj_r = ordem if recorte == "todos" else ids(lambda i, d=recorte: disp(i) == d)
            bloco[recorte] = {}
            for cl in CLASSES_EXATIDAO:
                conj = [i for i in conj_r if EX[v][i]["classe"] == cl]
                bloco[recorte][cl] = {"n": len(conj), **ragas_resumo(conj),
                                      "f_zero": [i for i in conj if F[i] == 0], "ar_zero_n": sum(AR[i] == 0 for i in conj)}
        res["ragas_por_classe_exatidao"][v] = bloco

    # por estrutura contábil (Q4)
    res["por_estrutura"] = {}
    for est in ESTRUTURAS:
        conj = ids(lambda i, e=est: por[i]["estrutura"] == e)
        pres = [i for i in conj if disp(i) == "presente"]
        res["por_estrutura"][est] = {
            "n": len(conj), "disponibilidade": {d: sum(disp(i) == d for i in conj) for d in DISP},
            "empresas": sorted({por[i]["ticker"] for i in conj}),
            "comportamento": comportamento_resumo(conj),
            "exatidao_presente": {v: contagem_exatidao([EX[v][i] for i in pres]) for v in EX},
            "exatidao_todos": {v: contagem_exatidao([EX[v][i] for i in conj]) for v in EX},
            "ragas_todos": ragas_resumo(conj), "ragas_presente": ragas_resumo(pres)}

    # Q5 (Seção 12, item 5): inadequada = exatidão INCORRETO ou PARCIALMENTE_CORRETO, ou comportamento
    # EXTRAPOLACAO ou ALUCINACAO; atribuição pela classificação prévia (presente -> geração;
    # parcial/ausente -> recuperação).
    def q5(v):
        lista = []
        for i in ordem:
            crit = []
            if EX[v][i]["classe"] in ("INCORRETO", "PARCIALMENTE_CORRETO"):
                crit.append("exatidao_" + EX[v][i]["classe"])
            if anot[i]["classe"] in ("EXTRAPOLACAO", "ALUCINACAO"):
                crit.append("comportamento_" + anot[i]["classe"])
            if crit:
                lista.append({"id": i, "disponibilidade": disp(i),
                              "atribuicao": "geracao" if disp(i) == "presente" else "recuperacao",
                              "criterios": crit, "classe_exatidao": EX[v][i]["classe"],
                              "classe_comportamento": anot[i]["classe"], "situacao_comportamento": situacao(i),
                              "truncada_na_geracao": por[i]["truncada_na_geracao"]})
        return {"n": len(lista), "geracao": sum(x["atribuicao"] == "geracao" for x in lista),
                "recuperacao": sum(x["atribuicao"] == "recuperacao" for x in lista), "casos": lista}

    q5o, q5e = q5("original"), q5("emenda5")
    diverg = [x for x in q5e["casos"] if x["criterios"] == ["exatidao_PARCIALMENTE_CORRETO"]
              and x["disponibilidade"] != "presente"]
    res["q5"] = {
        "definicao": ("Protocolo, Seção 12, item 5: resposta inadequada se a exatidão for INCORRETO ou "
                      "PARCIALMENTE_CORRETO, ou se o comportamento for extrapolação ou alucinação; atribuição a "
                      "geração (caso presente) ou recuperação (caso parcial ou ausente), pela classificação prévia."),
        "original": q5o, "emenda5": q5e,
        "divergencia_conceitual": {
            "descricao": ("Pela definição mecânica, casos parcial com exatidão PARCIALMENTE_CORRETO contam como "
                          "inadequados, embora a parte que falta não esteja no contexto. Nenhuma classificação é "
                          "alterada; as duas leituras são reportadas."),
            "casos": [{"id": x["id"], "classe_exatidao": x["classe_exatidao"],
                       "classe_comportamento": x["classe_comportamento"], "situacao_comportamento": x["situacao_comportamento"],
                       "encontrados": EX["emenda5"][x["id"]]["encontrados"],
                       "nao_encontrados": EX["emenda5"][x["id"]]["nao_encontrados"]} for x in diverg],
            "resposta_parcial_adequada": [x["id"] for x in diverg if x["classe_comportamento"] == "RESPOSTA_PARCIAL_ADEQUADA"],
            "sem_classe_de_comportamento": [x["id"] for x in diverg if x["situacao_comportamento"] == PENDENTE],
        },
    }

    # PARCIALMENTE_CORRETO em presente associados a respostas truncadas
    trunc_p = []
    for i in TRUNCADOS_PARCIAIS:
        reg = ler_json(f"avaliacao/ragas/coleta_tcc2/respostas/{i}.json")
        assert reg["resposta"] == por[i]["resposta"] and EX["original"][i]["classe"] == EX["emenda5"][i]["classe"] == "PARCIALMENTE_CORRETO"
        esperados = por[i]["caso_dataset"]["valores_esperados"]
        trunc_p.append({
            "id": i, "disponibilidade": disp(i), "sha256_resposta": por[i]["sha256_resposta"],
            "sha256_registro_coleta": sha256_arquivo(caminho(f"avaliacao/ragas/coleta_tcc2/respostas/{i}.json")),
            "finish_reason": reg["geracao"]["finish_reason"], "truncada_por_limite": reg["geracao"]["truncada_por_limite"],
            "uso_tokens": reg["geracao"]["uso_tokens"],
            "valores_exigidos": [{"id": v["id"], "valor": v["valor"], "sinal_exigido": v["sinal_exigido"],
                                  "conferido": v["id"] in EX["original"][i]["encontrados"]} for v in esperados],
            "numeros_lidos": EX["original"][i]["numeros_lidos"],
            "valores_nao_conciliados": EX["original"][i]["valores_nao_conciliados"],
            "fim_da_resposta": por[i]["resposta"][-160:]})
    res["parcialmente_corretos_truncados_presente"] = {
        "descricao": ("Os dois PARCIALMENTE_CORRETO de casos presente (iguais no original e na Emenda 5) vêm de "
                      "respostas encerradas por MAX_TOKENS; os valores conferidos aparecem antes do corte e os "
                      "valores não conferidos não aparecem na resposta."),
        "casos": trunc_p}
    assert sorted(i for i in ordem if disp(i) == "presente" and EX["emenda5"][i]["classe"] == "PARCIALMENTE_CORRETO") == sorted(TRUNCADOS_PARCIAIS)

    # casos individuais (auditoria): as quatro dimensões em blocos separados
    res["casos"] = [{
        "id": i, "ticker": por[i]["ticker"], "estrutura": por[i]["estrutura"], "categoria": por[i]["categoria"],
        "disponibilidade": disp(i), "truncada_na_geracao": por[i]["truncada_na_geracao"],
        "comportamento": {"situacao": situacao(i), "classe": anot[i]["classe"],
                          "abstencao_em_caso_presente": anot[i]["abstencao_em_caso_presente"],
                          "declara_limitacao": anot[i]["declara_limitacao"],
                          "entrega_informacao_sustentada": anot[i]["entrega_informacao_sustentada"]},
        "exatidao": {v: {"classe": EX[v][i]["classe"], "encontrados": EX[v][i]["encontrados"],
                         "nao_encontrados": EX[v][i]["nao_encontrados"]} for v in EX},
        "ragas": {"faithfulness": r6(F[i]), "answer_relevancy": r6(AR[i])},
    } for i in ordem]

    return (json.dumps(res, ensure_ascii=False, indent=1) + "\n").encode("utf-8")


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else ""
    if modo not in ("gerar", "verificar"):
        sys.exit("uso: sintetizar_resultados_tcc2.py gerar|verificar")
    conteudo = calcular()
    destino = os.path.join(AQUI, SAIDA)
    if modo == "gerar":
        with open(destino, "xb") as fh:   # exclusivo: nunca sobrescreve
            fh.write(conteudo)
        print(f"gravado {SAIDA}  sha256={hashlib.sha256(conteudo).hexdigest()}")
    else:
        with open(destino, "rb") as fh:
            igual = fh.read() == conteudo
        print(f"{'OK    ' if igual else 'DIFERE'} {SAIDA}  sha256={hashlib.sha256(conteudo).hexdigest()}")
        sys.exit(0 if igual else 1)


if __name__ == "__main__":
    main()
