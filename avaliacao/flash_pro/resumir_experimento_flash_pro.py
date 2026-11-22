# avaliacao/flash_pro/resumir_experimento_flash_pro.py   (local proposto)
#
# Resumo reprodutível do experimento Flash × Pro pré-registrado em
# avaliacao/PRE_REGISTRO_flash_vs_pro.md. Só lê os artefatos congelados no commit
# 75dbfc4 e agrega deterministicamente; não chama LLM, não reaudita narrativas e não
# altera nenhum arquivo de origem.
#
# Uso:
#   python resumir_experimento_flash_pro.py verificar [--saida DIR]   # recalcula e compara byte a byte
#   python resumir_experimento_flash_pro.py gerar     [--saida DIR]   # grava (recusa sobrescrever)

import argparse
import csv
import hashlib
import itertools
import json
import os
import statistics
import sys
from fractions import Fraction

RAIZ = os.environ.get("FUNDIA_RAIZ") or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AVAL = os.path.join(RAIZ, "avaliacao")
SAIDA_PADRAO = os.path.join(AVAL, "flash_pro")
NOME_SAIDA = "resumo_experimento_flash_pro.json"

# SHA-256 dos artefatos congelados (commit 75dbfc4; pré-registro em 6a9fee9), calculado sobre o
# conteúdo com CRLF normalizado para LF. Esses arquivos não têm "-text" no .gitattributes; com
# core.autocrlf a cópia de trabalho pode ter CRLF, e o hash normalizado coincide com o do blob.
FONTES = {
    "PRE_REGISTRO_flash_vs_pro.md": "eb1bab2a32ecf4f0e4e046167aec4f59ce5bb7de6313d4cb14003bfb45ced0c9",
    "experimento_flash_pro.csv": "a618a73b8aba3765bd637fcbcf7939609e87fed881af44dec0e4df67eaaddfda",
    "experimento_flash_pro_verificacoes.json": "694efac85f206ff6419b29d14a291cf004348dce375b7acf9b5b0ad47a007a56",
    "experimento_flash_pro_manifesto.json": "053ae7de68d8630844941c4e43d4211aac093a98d74e957658ed7e62d8b782c6",
    "experimento_flash_pro_bruto_28linhas.csv": "436315fe7ac7c687c6635c5f18e2b8554c100b3e509bd3b33e343ed5bf02be45",
    "experimento_flash_pro_descartadas.csv": "fe73b1ad317dc6984202d41631b72e69fa9176b8ca4874c1764a28a88e677805",
}

TICKERS = ["WEGE3", "VALE3", "ITSA4", "BBAS3", "ZAMP3"]
BRACOS = ["flash", "pro"]
LIMITE_AGREGADO_PP = 2.0
LIMITE_EMPRESA_PP = 5.0
LIMITE_COBERTURA = 0.10


def lf(dados):
    return dados.replace(b"\r\n", b"\n")


def sha256(caminho):
    with open(caminho, "rb") as fh:
        return hashlib.sha256(lf(fh.read())).hexdigest()


def conferir_fontes():
    for nome, esperado in FONTES.items():
        obtido = sha256(os.path.join(AVAL, nome))
        if obtido != esperado:
            raise RuntimeError(f"fonte alterada: {nome} ({obtido})")


def ler_csv(nome):
    with open(os.path.join(AVAL, nome), encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def ler_texto(nome):
    with open(os.path.join(AVAL, nome), encoding="utf-8") as fh:
        return fh.read()


def r4(x):
    return round(x, 4)


def criterios(celulas):
    """celulas: {(ticker, braco, execucao): {'conferem', 'total_numeros'}} com as 20 células."""
    # Diferenças e critérios usam frações exatas; o arredondamento (4 casas) só ocorre na saída.
    def taxa(filtro):
        c = sum(v["conferem"] for k, v in celulas.items() if filtro(k))
        t = sum(v["total_numeros"] for k, v in celulas.items() if filtro(k))
        return c, t, Fraction(100 * c, t)

    agg, exato = {}, {}
    for b in BRACOS:
        c, t, x = taxa(lambda k, b=b: k[1] == b)
        agg[b] = {"conferem": c, "total_numeros": t, "taxa_pct": r4(float(x))}
        exato[b] = x
    por_empresa, dif_emp = {}, {}
    for tk in TICKERS:
        linha, ex = {}, {}
        for b in BRACOS:
            c, t, x = taxa(lambda k, b=b, tk=tk: k[0] == tk and k[1] == b)
            linha[b] = {"conferem": c, "total_numeros": t, "taxa_pct": r4(float(x))}
            ex[b] = x
        dif_emp[tk] = abs(ex["flash"] - ex["pro"])
        linha["diferenca_pp"] = r4(float(dif_emp[tk]))
        por_empresa[tk] = linha
    dif_agg = abs(exato["flash"] - exato["pro"])
    pior = max(TICKERS, key=lambda tk: (dif_emp[tk], tk))
    fid_ok = dif_agg <= LIMITE_AGREGADO_PP and dif_emp[pior] <= LIMITE_EMPRESA_PP
    dif_agg = r4(float(dif_agg))
    med = {b: statistics.median(v["total_numeros"] for k, v in celulas.items() if k[1] == b) for b in BRACOS}
    maior, menor = Fraction(max(med.values())), Fraction(min(med.values()))
    cob = {
        "mediana_total_numeros": med,
        "diferenca_relativa_sobre_maior": r4(float((maior - menor) / maior)),
        "diferenca_relativa_sobre_menor": r4(float((maior - menor) / menor)),
    }
    # Base adotada: a mediana maior (a leitura da mensagem do commit 75dbfc4). O pré-registro não
    # fixa a base; a mediana menor é reportada como interpretação alternativa.
    cob_ok = (maior - menor) / maior <= Fraction(LIMITE_COBERTURA).limit_denominator()
    cob["criterio_satisfeito_base_menor"] = (maior - menor) / menor <= Fraction(LIMITE_COBERTURA).limit_denominator()
    return {
        "fidelidade": {
            "agregado": agg, "diferenca_agregada_pp": dif_agg, "por_empresa": por_empresa,
            "pior_empresa": pior, "pior_diferenca_pp": por_empresa[pior]["diferenca_pp"],
            "criterio_satisfeito": fid_ok,
        },
        "cobertura": dict(cob, criterio_satisfeito=cob_ok),
        "equivalentes": fid_ok and cob_ok,
    }


def calcular():
    conferir_fontes()
    pre = ler_texto("PRE_REGISTRO_flash_vs_pro.md")
    linhas = ler_csv("experimento_flash_pro.csv")
    verif = json.loads(ler_texto("experimento_flash_pro_verificacoes.json"))
    manif = json.loads(ler_texto("experimento_flash_pro_manifesto.json"))
    bruto = ler_csv("experimento_flash_pro_bruto_28linhas.csv")
    descart = ler_csv("experimento_flash_pro_descartadas.csv")

    # 1. integridade e condições de aborto do pré-registro (Seção 6)
    chaves = [(x["ticker"], x["modelo"], int(x["execucao"])) for x in linhas]
    esperadas = [(t, b, e) for t in TICKERS for b in BRACOS for e in (1, 2)]
    integ = {
        "celulas": len(linhas),
        "celulas_unicas_iguais_ao_desenho": sorted(chaves) == sorted(esperadas),
        "finish_reason": sorted({x["finish_reason"] for x in linhas}),
        "hash_documento_igual_manifesto": all(x["hash_documento"] == manif["documentos"][x["ticker"]]["hash_documento"] for x in linhas),
        "hash_contexto_unico_por_empresa": all(len({x["hash_contexto"] for x in linhas if x["ticker"] == t}) == 1 for t in TICKERS),
        "hash_contexto_igual_manifesto": all(x["hash_contexto"] == manif["contextos"][x["ticker"]] for x in linhas),
        "hash_prompt_unico_por_empresa_entre_bracos": all(len({x["hash_prompt"] for x in linhas if x["ticker"] == t}) == 1 for t in TICKERS),
        "modelo_efetivo": sorted({v["telemetria"]["modelo_efetivo"] for v in verif.values()}),
    }
    ordem = {}
    for t in TICKERS:
        seq = sorted((int(x["ordem_global"]), x["modelo"], int(x["execucao"])) for x in linhas if x["ticker"] == t)
        ordem[t] = [f"{m}-exec{e}" for _, m, e in seq]
    integ["intercalacao_flash1_pro1_flash2_pro2"] = all(v == ["flash-exec1", "pro-exec1", "flash-exec2", "pro-exec2"] for v in ordem.values())

    # 2. consistência CSV × JSON de verificações (recontagem a partir das verificações individuais)
    incons = []
    celulas = {}
    nao_confere = []
    for x in linhas:
        k = (x["ticker"], x["modelo"], int(x["execucao"]))
        j = verif[f"{k[0]}_{k[1]}_exec{k[2]}"]
        vs = [v for v in j["verificacoes"] if v["veredito"] != "IGNORADO"]
        cont = {
            "total_numeros": len(vs),
            "conferem": sum(v["veredito"] == "CONFERE" for v in vs),
            "divergentes": sum(v["veredito"] == "DIVERGENTE" for v in vs),
            "nao_encontrados": sum(v["veredito"] == "NAO_ENCONTRADO" for v in vs),
        }
        for campo, valor in cont.items():
            if int(x[campo]) != valor or j["resumo"][campo] != valor:
                incons.append(f"{k}: {campo} csv={x[campo]} resumo={j['resumo'][campo]} recontado={valor}")
        celulas[k] = {"conferem": int(x["conferem"]), "total_numeros": int(x["total_numeros"])}
        for v in vs:
            if v["veredito"] != "CONFERE":
                nao_confere.append({"celula": f"{k[0]}_{k[1]}_exec{k[2]}", "secao": v.get("secao"), "trecho": v.get("trecho"),
                                    "veredito": v["veredito"], "motivo": v.get("motivo")})
    integ["inconsistencias_csv_json"] = incons
    integ["ignorados_fora_do_denominador"] = sum(
        sum(v["veredito"] == "IGNORADO" for v in j["verificacoes"]) for j in verif.values())

    # contagens das verificações individuais do JSON, por veredito e por braço
    contagens = {}
    for b in BRACOS + ["total"]:
        vs = [x for j in verif.values() if b == "total" or j["modelo"] == b for x in j["verificacoes"]]
        por_veredito = {ver: sum(x["veredito"] == ver for x in vs)
                        for ver in ("CONFERE", "DIVERGENTE", "NAO_ENCONTRADO", "IGNORADO")}
        contagens[b] = {"entradas": len(vs), "por_veredito": por_veredito,
                        "denominador_total_numeros": len(vs) - por_veredito["IGNORADO"]}

    # 3. critérios pré-registrados (Seção 5) na seleção versionada
    res = criterios(celulas)

    # 4. variabilidade dentro do braço × diferença entre braços (Seção 8), descritiva
    var = {}
    for t in TICKERS:
        f = [celulas[(t, "flash", e)]["total_numeros"] for e in (1, 2)]
        p = [celulas[(t, "pro", e)]["total_numeros"] for e in (1, 2)]
        var[t] = {"flash": f, "pro": p,
                  "amplitude_dentro_flash": abs(f[0] - f[1]), "amplitude_dentro_pro": abs(p[0] - p[1]),
                  "diferenca_entre_medias": r4(abs(statistics.mean(f) - statistics.mean(p)))}
        var[t]["entre_maior_que_dentro"] = var[t]["diferenca_entre_medias"] > max(var[t]["amplitude_dentro_flash"], var[t]["amplitude_dentro_pro"])

    # 5. secundárias descritivas (Seção 4), sem critério
    sec = {}
    for b in BRACOS:
        xs = [x for x in linhas if x["modelo"] == b]
        sec[b] = {campo: {"mediana": r4(statistics.median(float(x[campo]) for x in xs)),
                          "min": r4(min(float(x[campo]) for x in xs)), "max": r4(max(float(x[campo]) for x in xs))}
                  for campo in ("latencia_s", "tokens_saida", "tokens_raciocinio", "tokens_total")}

    # 6. incidente: robustez do veredito sobre todas as seleções possíveis de duplicatas
    grupos = {}
    for x in bruto:
        k = (x["ticker"], x["modelo"], int(x["execucao"]))
        grupos.setdefault(k, []).append({"conferem": int(x["conferem"]), "total_numeros": int(x["total_numeros"]),
                                         "finish_reason": x["finish_reason"]})
    duplicadas = sorted(k for k, v in grupos.items() if len(v) > 1)
    combos = []
    for escolha in itertools.product(*[range(len(grupos[k])) for k in duplicadas]):
        cel = {k: grupos[k][0] for k in grupos if len(grupos[k]) == 1}
        cel.update({k: grupos[k][i] for k, i in zip(duplicadas, escolha)})
        r = criterios(cel)
        combos.append((r["fidelidade"]["criterio_satisfeito"], r["cobertura"]["criterio_satisfeito"], r["equivalentes"],
                       r["fidelidade"]["diferenca_agregada_pp"], r["fidelidade"]["pior_diferenca_pp"],
                       r["cobertura"]["diferenca_relativa_sobre_maior"], r["cobertura"]["criterio_satisfeito_base_menor"]))
    chaves_desc = {(x["ticker"], x["modelo"], int(x["execucao"]), x["timestamp"]) for x in descart}
    chaves_bruto = {(x["ticker"], x["modelo"], int(x["execucao"]), x["timestamp"]) for x in bruto}
    chaves_vers = {(x["ticker"], x["modelo"], int(x["execucao"]), x["timestamp"]) for x in linhas}
    incidente = {
        "linhas_brutas": len(bruto),
        "celulas_duplicadas": [f"{k[0]}_{k[1]}_exec{k[2]}" for k in duplicadas],
        "versionadas_mais_descartadas_igual_bruto": chaves_vers | chaves_desc == chaves_bruto and not (chaves_vers & chaves_desc),
        "selecoes_possiveis": len(combos),
        "selecoes_equivalentes": sum(c[2] for c in combos),
        "selecoes_com_fidelidade_satisfeita": sum(c[0] for c in combos),
        "selecoes_com_cobertura_satisfeita": sum(c[1] for c in combos),
        "selecoes_com_cobertura_satisfeita_base_menor": sum(c[6] for c in combos),
        "faixa_diferenca_agregada_pp": [min(c[3] for c in combos), max(c[3] for c in combos)],
        "faixa_pior_empresa_pp": [min(c[4] for c in combos), max(c[4] for c in combos)],
        "faixa_diferenca_cobertura_sobre_maior": [min(c[5] for c in combos), max(c[5] for c in combos)],
        "secao_emendas_do_pre_registro_vazia": "Nenhuma até o momento" in pre,
        "classificacao": "desvio de procedimento não emendado: gerações além das 20 previstas e seleção das "
                         "linhas feita depois da coleta, registrados só na mensagem do commit 75dbfc4; "
                         "o veredito não depende da seleção",
    }

    resumo = {
        "descricao": "Resumo reprodutível do experimento Flash × Pro (pré-registro 6a9fee9; coleta 75dbfc4). "
                     "Agregação determinística dos artefatos congelados; nenhuma reauditoria nem chamada a LLM.",
        "proveniencia": {"fontes_sha256": {n: sha256(os.path.join(AVAL, n)) for n in FONTES}},
        "desenho": {"empresas": TICKERS, "bracos": {"flash": "gemini-2.5-flash", "pro": "gemini-2.5-pro"},
                    "execucoes_por_celula": 2, "documento": "ITR 2026-03-31",
                    "denominador": "resumo.total_numeros = verificações com veredito diferente de IGNORADO",
                    "auditor": "1.0 (modulos/auditoria.py no commit 75dbfc4: existência do valor, sinal e direção; "
                               "sem verificação de conceito, introduzida em 27dfdd5)",
                    "estado_do_pipeline": "anterior às correções do TCC 2 (commits 183e69f a 777b256 em modulos/)"},
        "formulas": {
            "fidelidade_braco": "100 × Σ conferem / Σ total_numeros nas 10 execuções do braço",
            "fidelidade_empresa": "100 × Σ conferem / Σ total_numeros nas 2 execuções da empresa no braço",
            "diferenca_fidelidade_pp": "|taxa_flash − taxa_pro|",
            "diferenca_cobertura_base_adotada": "(mediana_maior − mediana_menor) / mediana_maior",
            "diferenca_cobertura_base_alternativa": "(mediana_maior − mediana_menor) / mediana_menor",
            "nota_base": "o pré-registro (Seção 5) não especifica a base da diferença relativa; o limite de 10% "
                         "é ultrapassado nas duas interpretações",
        },
        "contagens_verificacoes": contagens,
        "limites_pre_registrados": {"fidelidade_agregada_pp": LIMITE_AGREGADO_PP, "fidelidade_por_empresa_pp": LIMITE_EMPRESA_PP,
                                    "cobertura_diferenca_relativa_mediana": LIMITE_COBERTURA},
        "integridade": integ,
        "ordem_por_empresa": ordem,
        "resultado": res,
        "veredito": "equivalentes" if res["equivalentes"] else "nao_equivalentes_pelo_criterio_pre_registrado",
        "verificacoes_nao_confere": nao_confere,
        "variabilidade_total_numeros": var,
        "secundarias_descritivas": sec,
        "incidente_de_coleta": incidente,
    }
    return (json.dumps(resumo, ensure_ascii=False, indent=2, sort_keys=False) + "\n").encode("utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["gerar", "verificar"])
    ap.add_argument("--saida", default=SAIDA_PADRAO)
    a = ap.parse_args()
    destino = os.path.join(a.saida, NOME_SAIDA)
    dados = calcular()
    if a.modo == "gerar":
        os.makedirs(a.saida, exist_ok=True)
        with open(destino, "xb") as fh:
            fh.write(dados)
        print(f"gravado {destino} sha256={hashlib.sha256(dados).hexdigest()}")
    else:
        with open(destino, "rb") as fh:
            atual = fh.read()
        if lf(atual) != dados:
            print(f"DIVERGE {destino}")
            sys.exit(1)
        print(f"OK     {NOME_SAIDA}  sha256={hashlib.sha256(dados).hexdigest()}")


if __name__ == "__main__":
    main()
