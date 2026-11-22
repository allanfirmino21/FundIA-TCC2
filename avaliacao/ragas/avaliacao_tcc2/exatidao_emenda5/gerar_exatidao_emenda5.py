# avaliacao/ragas/avaliacao_tcc2/exatidao_emenda5/gerar_exatidao_emenda5.py
#
# Emenda 5 do protocolo (PROTOCOLO_RAGAS_TCC2.md): classifica as 96 respostas congeladas com
# exatidao.classificar(..., regra_sinal="emenda5") e grava o resultado SEPARADO do resultado
# congelado da exatidão, que não é tocado e continua sendo o resultado reportado.
#
# Correção do instrumento de medida concebida depois da observação dos resultados; não é
# melhoria do sistema FundIA (as respostas são as mesmas). Sem LLM, sem RAGAS.
#
# Uso (na raiz do repositório):
#   python avaliacao/ragas/avaliacao_tcc2/exatidao_emenda5/gerar_exatidao_emenda5.py            # só confere
#   python avaliacao/ragas/avaliacao_tcc2/exatidao_emenda5/gerar_exatidao_emenda5.py --executar # grava (uma vez)
#
# Antes de gravar, exige: código, instrumentos, protocolo, dataset, coleta e este gerador
# commitados e limpos; resultado original íntegro (selo e SHA-256 fixados aqui); o modo padrão
# ("original") reproduzindo o resultado original em todos os campos; nenhuma pendência de sinal
# no modo "emenda5". Nunca sobrescreve.

import argparse
import os
import sys
from collections import Counter

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.normpath(os.path.join(AQUI, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "avaliacao", "ragas"))

import avaliar_respostas_tcc2 as A  # noqa: E402
import coletar_respostas_tcc2 as C  # noqa: E402  (selo, hash e gravação exclusiva)
import exatidao as X  # noqa: E402

REGRA = "emenda5"
ARQUIVO = "resultado_exatidao_emenda5.json"
ORIGINAL_REL = "avaliacao/ragas/avaliacao_tcc2/exatidao/resultado_exatidao.json"
SHA256_ORIGINAL = "3c3e28c080a9884f53f1197bd0c4106fd414105b2aa4de3ff2928f401a05a6db"
SHA256_REGISTRO_ORIGINAL = "8582e2e0352f93323629e7a28554ffa981577e7974e66fa6130ccf99a309c8f9"
SHA256_EXATIDAO_ORIGINAL = "2b4b11706841701ed6ffd551a4789431fa9102c65cf1302104cfa600ce432ff0"
COMMIT_EXATIDAO_ORIGINAL = "d49835d"
COMMIT_INSTRUMENTO_ORIGINAL = "a3f424f"
CAMPOS = ("numeros_lidos", "escala_implicita", "sinal_revisao_manual", "classe", "motivo", "encontrados",
          "nao_encontrados", "valores_nao_conciliados", "pendencias_sinal")
CLASSES = (X.CORRETO, X.PARCIALMENTE_CORRETO, X.INCORRETO, X.NAO_APLICAVEL)


def _rel(p: str) -> str:
    return os.path.relpath(p, RAIZ).replace(os.sep, "/")


def conferir_original(casos: list[dict]) -> dict:
    """Resultado congelado íntegro: selo, 96 respostas, classes finais, SHA-256 e proveniência fixados."""
    r = A.conferir_resultado_exatidao(A.SAIDA_PADRAO, casos)
    p = os.path.join(RAIZ, *ORIGINAL_REL.split("/"))
    if C.sha256_arquivo(p) != SHA256_ORIGINAL or r["sha256_registro"] != SHA256_REGISTRO_ORIGINAL:
        raise A.Bloqueio("resultado_exatidao.json não é o congelado (SHA-256 ou selo diferente)")
    if r["proveniencia"]["sha256_exatidao_py"] != SHA256_EXATIDAO_ORIGINAL:
        raise A.Bloqueio("o resultado original não foi produzido pelo instrumento congelado esperado")
    if r["sha256_decisoes_sinal"] is not None:
        raise A.Bloqueio("o original tem decisões manuais de sinal; a Emenda 5 não as prevê")
    return r


def classificar_emenda5(casos: list[dict], original: dict) -> tuple[list[dict], dict]:
    """Classifica os 96 casos com regra_sinal="emenda5" e confere o modo padrão contra o original."""
    orig = {x["case_id"]: x for x in original["resultados"]}
    resultados, regressao, pendentes, sinais = [], [], [], []
    for caso in casos:
        cid, resp, cd = caso["case_id"], caso["resposta"], caso["caso_dataset"]
        padrao = X.classificar(resp, cd, {})
        if any(padrao[k] != orig[cid][k] for k in CAMPOS):
            regressao.append(cid)
        r = X.classificar(resp, cd, {}, regra_sinal=REGRA)
        if r["classe"] not in CLASSES:
            pendentes.append(cid)
        lidos_o, lidos_e = X.extrair_numeros(resp), X.extrair_numeros(resp, REGRA)
        if [n.inicio for n in lidos_o] != [n.inicio for n in lidos_e]:
            raise A.Bloqueio(f"{cid}: a Emenda 5 alterou os números lidos (só o sinal pode mudar)")
        alterados = [{"numero": o.texto, "posicao": o.inicio, "sinal_original": o.sinal, "sinal_emenda5": e.sinal}
                     for o, e in zip(lidos_o, lidos_e) if o.sinal != e.sinal]
        sinais += [{"case_id": cid, "categoria": caso["categoria"], **s} for s in alterados]
        resultados.append({"case_id": cid, "ticker": caso["ticker"], "categoria": caso["categoria"],
                           "estrutura": caso["estrutura"], "disponibilidade": caso["disponibilidade"],
                           "sha256_resposta": caso["sha256_resposta"],
                           "truncada_na_geracao": caso["truncada_na_geracao"],
                           "decisoes_manuais_sinal": {}, "classe_original": orig[cid]["classe"],
                           "sinais_alterados": alterados, **r})
    if regressao:
        raise A.Bloqueio(f"o modo padrão não reproduz o resultado original: {regressao}")
    if pendentes:
        raise A.Bloqueio(f"pendência de sinal no modo emenda5 (não prevista): {pendentes}")
    resumo = {"original": _contagem(orig.values()), "emenda5": _contagem(resultados),
              "mudancas_de_classe": [{"case_id": x["case_id"], "de": x["classe_original"], "para": x["classe"],
                                      "disponibilidade": x["disponibilidade"]}
                                     for x in resultados if x["classe"] != x["classe_original"]],
              "sinais_alterados": sinais}
    return resultados, resumo


def _contagem(regs) -> dict:
    regs = list(regs)
    c = Counter(x["classe"] for x in regs)
    ap = c[X.CORRETO] + c[X.PARCIALMENTE_CORRETO] + c[X.INCORRETO]
    por_disp = {}
    for d in ("presente", "parcial", "ausente"):
        cd = Counter(x["classe"] for x in regs if x["disponibilidade"] == d)
        por_disp[d] = {k: cd[k] for k in CLASSES}
    return {"classes": {k: c[k] for k in CLASSES}, "aplicaveis": ap, "correto_sobre_aplicaveis": f"{c[X.CORRETO]}/{ap}",
            "por_disponibilidade": por_disp}


def gerar(*, executar: bool = False, saida: str = A.SAIDA_PADRAO, git=None, exigir_git: bool = True,
          log=print) -> dict:
    """
    Sem executar: confere tudo e mostra o resumo, sem gravar. Com executar: exige o repositório
    commitado e limpo e grava saida/exatidao_emenda5/resultado_exatidao_emenda5.json uma única vez.
    """
    git = git or A.Git()
    extras = (_rel(os.path.abspath(__file__)), ORIGINAL_REL)
    if executar and exigir_git:
        head = A.verificar_git(git, extras)
    else:
        head = git.head()
        pend = git.pendencias(list(A.ARQUIVOS_VERSIONADOS) + list(extras))
        if pend:
            log("aviso: alterações não commitadas (impediriam --executar): " + "; ".join(pend))
    ds, sha_ds, casos = A.carregar_entradas()
    original = conferir_original(casos)
    resultados, resumo = classificar_emenda5(casos, original)
    log(f"original : {resumo['original']['classes']} | CORRETO/aplicáveis {resumo['original']['correto_sobre_aplicaveis']}")
    log(f"emenda5  : {resumo['emenda5']['classes']} | CORRETO/aplicáveis {resumo['emenda5']['correto_sobre_aplicaveis']}")
    for m in resumo["mudancas_de_classe"]:
        log(f"  classe: {m['case_id']} {m['de']} -> {m['para']} ({m['disponibilidade']})")
    for s in resumo["sinais_alterados"]:
        log(f"  sinal:  {s['case_id']} {s['numero']} {s['sinal_original']} -> {s['sinal_emenda5']} ({s['categoria']})")
    if not executar:
        log("conferência concluída; nada foi gravado (use --executar para gravar)")
        return {"status": "conferido", "resumo": resumo}
    pasta = os.path.join(saida, "exatidao_emenda5")
    destino = os.path.join(pasta, ARQUIVO)
    if os.path.exists(destino):
        raise A.Bloqueio(f"{ARQUIVO} já existe: o resultado da Emenda 5 não é recalculado nem sobrescrito")
    os.makedirs(pasta, exist_ok=True)
    registro = {
        "esquema": A.ESQUEMA, "etapa": "exatidao_emenda5", "regra_sinal": REGRA,
        "emenda": "PROTOCOLO_RAGAS_TCC2.md, Emenda 5",
        "nota": ("Resultado adicional, reportado ao lado do original congelado. Correção do instrumento de "
                 "verificação concebida depois da observação dos resultados; não representa melhoria do "
                 "sistema FundIA (as 96 respostas são as mesmas)."),
        "gerado_em": A.agora_utc(),
        "proveniencia": {**A.proveniencia(sha_ds, head),
                         "sha256_gerador": C.sha256_arquivo(os.path.abspath(__file__))},
        "resultado_original": {"caminho": ORIGINAL_REL, "sha256": SHA256_ORIGINAL,
                               "sha256_registro": SHA256_REGISTRO_ORIGINAL,
                               "sha256_exatidao_py": SHA256_EXATIDAO_ORIGINAL,
                               "commit_resultado": COMMIT_EXATIDAO_ORIGINAL,
                               "commit_instrumento": COMMIT_INSTRUMENTO_ORIGINAL},
        "sha256_decisoes_sinal": None,
        "n_casos": len(resultados), "resumo": resumo, "resultados": resultados,
    }
    with A.trava(saida):
        C.gravar_exclusivo(destino, C.selar(registro))
    log(f"exatidão (Emenda 5): {len(resultados)} casos gravados em {destino}")
    return {"status": "gravado", "arquivo": destino, "resumo": resumo}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Exatidão com a Emenda 5 (resultado separado do original).")
    ap.add_argument("--executar", action="store_true", help="grava o resultado (uma única vez)")
    a = ap.parse_args(argv)
    try:
        gerar(executar=a.executar)
    except A.Bloqueio as e:
        print(f"BLOQUEADO: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
