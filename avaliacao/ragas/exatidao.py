# avaliacao/ragas/exatidao.py
#
# Verificação determinística de exatidão numérica do RAGAS do TCC 2
# (PROTOCOLO_RAGAS_TCC2.md, Seção 11.1). Complementar ao RAGAS, sem LLM:
# lê os números de uma resposta, compara com os valores esperados do
# gabarito e devolve uma das classes CORRETO / PARCIALMENTE_CORRETO /
# INCORRETO / NAO_APLICAVEL.
#
# Isolado do pipeline de produção: não importa nada de modulos/.
#
# Regras do protocolo (numeração da Seção 11.1):
#   1. formato brasileiro (ponto = milhar, vírgula = decimal); exceção: ponto
#      seguido de exatamente 10 dígitos é separador decimal;
#   2. multiplicadores explícitos mil / milhão / bilhão / trilhão;
#   3. sem multiplicador, o número monetário está em R$ mil (escala da fonte)
#      e recebe a marca escala_implicita;
#   4. percentuais comparados só com percentuais, em valor absoluto;
#   5. sinal verificado só quando o gabarito exige; negativo por "-" ou "−"
#      ou pela palavra prejuízo/negativo/déficit na mesma oração;
#      inconclusivo -> decisão manual (sinal_revisao_manual);
#   6. confere se v == g arredondado (meio para cima) ou truncado em k casas,
#      na unidade em que v foi escrito;
#   7. conciliação um-para-um entre números da resposta e valores exigidos.
#
# Regras complementares (Emenda 1 do protocolo, antes da coleta):
#   A. não são números monetários: datas, anos isolados, códigos contábeis
#      (3.01), períodos (1S25/1S26), "Trecho N" e inteiros < 1000 sem R$,
#      multiplicador, % ou casas decimais;
#   B. o "-" de marcador de lista no início da linha não é sinal;
#   C. parênteses não tornam o número negativo por si: "(R$ 19,6 bilhões)" é
#      reapresentação; um número isolado entre parênteses tem sinal ambíguo e
#      vai para revisão manual, salvo se a oração o qualificar (regra 5);
#   D. número brasileiro seguido de pontuação ("R$ 9.468.313.") é lido inteiro.
#
# Emenda 5 do protocolo (depois da exatidão congelada; opcional, padrão "original"):
#   com regra_sinal="emenda5", um rótulo ambivalente — o termo negativo em par alternativo
#   com o antônimo positivo ("Lucro/Prejuízo", "Lucro ou Prejuízo", "Lucro (Prejuízo)",
#   "superávit/déficit", "positivo ou negativo"), em qualquer ordem — não indica sinal e é
#   desconsiderado na busca da palavra negativa da regra 5. Com regra_sinal="original"
#   (padrão), o comportamento é o do instrumento congelado antes da coleta.

import re
import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN
from itertools import product

CORRETO = "CORRETO"
PARCIALMENTE_CORRETO = "PARCIALMENTE_CORRETO"
INCORRETO = "INCORRETO"
NAO_APLICAVEL = "NAO_APLICAVEL"
PENDENTE_SINAL = "PENDENTE_REVISAO_SINAL"   # estado de trabalho, não é classe

MULTIPLICADORES = {
    "trilhao": Decimal("1e12"), "bilhao": Decimal("1e9"),
    "milhao": Decimal("1e6"), "mil": Decimal("1e3"),
}
_MULT_REGEX = [
    (r"trilh(?:ão|ao|ões|oes)|tri\b", "trilhao"),
    (r"bilh(?:ão|ao|ões|oes)|bi\b", "bilhao"),
    (r"milh(?:ão|ao|ões|oes)|mi\b|MM\b", "milhao"),
    (r"mil\b", "mil"),
]
_RE_MULT = re.compile(r"\s*(" + "|".join(p for p, _ in _MULT_REGEX) + r")", re.IGNORECASE)
_RE_PCT = re.compile(r"\s*(%|por\s+cento\b)", re.IGNORECASE)

# Número: não normalizado (ponto + 10 dígitos) | milhar pt-BR | simples
_RE_NUM = re.compile(
    r"(?P<num>\d+\.\d{10}(?!\d)|\d{1,3}(?:\.\d{3})+(?:,\d+)?(?!\d|\.\d)|\d+(?:,\d+)?)"
)
_RE_DATA = re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b")
_MESES = ("janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho",
          "agosto", "setembro", "outubro", "novembro", "dezembro")
_PALAVRAS_NEGATIVAS = ("prejuizo", "negativo", "negativa", "deficit")

REGRAS_SINAL = ("original", "emenda5")
# Emenda 5: par alternativo positivo/negativo, em qualquer ordem, separado por "/", "ou" ou
# "e/ou", ou com o segundo termo sozinho entre parênteses ("lucro (prejuízo)"); aplicado ao
# texto sem acento e em minúsculas.
_POS = r"(?:lucros?|superavit|positiv[oa]s?)"
_NEG = r"(?:prejuizos?|deficit|negativ[oa]s?)"
_SEP = r"\s*(?:e/ou\b|/|\bou\b)\s*"
_RE_ROTULO_AMBIVALENTE = re.compile(rf"\b{_POS}{_SEP}{_NEG}\b|\b{_NEG}{_SEP}{_POS}\b"
                                    rf"|\b{_POS}\s*\(\s*{_NEG}\s*\)|\b{_NEG}\s*\(\s*{_POS}\s*\)")


def _sem_acento(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def _validar_regra(regra_sinal: str) -> None:
    if regra_sinal not in REGRAS_SINAL:
        raise ValueError(f"regra_sinal inválida: {regra_sinal!r} (aceitas: {REGRAS_SINAL})")


def _tem_palavra_negativa(trecho: str, regra_sinal: str) -> bool:
    """Regra 5: palavra negativa no trecho; com a Emenda 5, fora de rótulo ambivalente."""
    s = _sem_acento(trecho)
    if regra_sinal == "emenda5":
        s = _RE_ROTULO_AMBIVALENTE.sub(" ", s)
    return any(p in s for p in _PALAVRAS_NEGATIVAS)


@dataclass
class Numero:
    """Um número lido da resposta."""
    texto: str                 # trecho original
    inicio: int                # posição na resposta
    tipo: str                  # "monetario" | "percentual"
    exibido: Decimal           # valor como escrito, na unidade em que foi escrito
    casas: int                 # k: casas decimais exibidas
    multiplicador: Decimal     # reais por unidade exibida (percentual: 1)
    escala_implicita: bool
    sinal: str                 # "-" | "+" | "?" (inconclusivo)
    oracao: int
    parenteses: bool = False   # número isolado entre parênteses (regra C)

    @property
    def valor(self) -> Decimal:
        """Valor em reais (monetário) ou em pontos percentuais."""
        v = self.exibido * self.multiplicador
        return -v if self.sinal == "-" else v


def _para_decimal(bruto: str) -> tuple[Decimal, int]:
    """Converte o texto do número (regra 1) e devolve (valor, casas exibidas)."""
    if re.fullmatch(r"\d+\.\d{10}", bruto):
        return Decimal(bruto), 10
    if "," in bruto:
        inteiro, dec = bruto.split(",")
        return Decimal(inteiro.replace(".", "") + "." + dec), len(dec)
    return Decimal(bruto.replace(".", "")), 0


def _oracoes(texto: str) -> list[tuple[int, int]]:
    """Intervalos das orações: separadas por . ! ? ; seguidos de espaço, ou quebra de linha."""
    limites, inicio = [], 0
    for m in re.finditer(r"[.!?;](?=\s|$)|\n", texto):
        limites.append((inicio, m.end()))
        inicio = m.end()
    limites.append((inicio, len(texto)))
    return [(a, b) for a, b in limites if b > a]


def extrair_numeros(texto: str, regra_sinal: str = "original") -> list[Numero]:
    """
    Lê os números monetários e percentuais da resposta (regras 1–5).

    regra_sinal: "original" (padrão; instrumento congelado) ou "emenda5" (Emenda 5).

    Não são considerados números monetários ou percentuais:
    - datas (30/06/2026) e o dia em "30 de junho";
    - anos (1900–2100) sem R$, multiplicador ou %;
    - códigos de período colados a letras (1S26, 2T26) e códigos de conta (3.01);
    - números precedidos de "Trecho";
    - inteiros menores que 1000 sem R$, multiplicador, % ou casas decimais.
    """
    _validar_regra(regra_sinal)
    ocultos = [(m.start(), m.end()) for m in _RE_DATA.finditer(texto)]
    oracoes = _oracoes(texto)
    numeros = []
    for m in _RE_NUM.finditer(texto):
        a, b = m.start("num"), m.end("num")
        if any(x <= a < y for x, y in ocultos):
            continue
        antes, depois = texto[max(0, a - 12):a], texto[b:b + 20]
        # colado a letras/dígitos/pontos (1S26, 3.01, T2) -> código, não número
        if (a > 0 and (texto[a - 1].isalpha() or texto[a - 1] in "._/")) or \
           (b < len(texto) and (texto[b].isalpha() or (texto[b] == "." and b + 1 < len(texto) and texto[b + 1].isdigit()))):
            continue
        if re.search(r"trecho\s*$", _sem_acento(antes)):
            continue
        bruto = m.group("num")
        exibido, casas = _para_decimal(bruto)
        pct = _RE_PCT.match(depois)
        mult = None if pct else _RE_MULT.match(depois)
        tem_rs = bool(re.search(r"R\$\s*[-−]?\s*\(?\s*$", antes))
        if pct:
            tipo, fator, implicita, fim = "percentual", Decimal(1), False, b + pct.end()
        else:
            tipo = "monetario"
            if mult:
                chave = next(k for p, k in _MULT_REGEX if re.fullmatch(p, mult.group(1), re.IGNORECASE))
                fator, implicita, fim = MULTIPLICADORES[chave], False, b + mult.end()
            else:
                fator, implicita, fim = Decimal(1000), True, b
            if not tem_rs and not mult:
                seguinte = _sem_acento(texto[b:b + 15]).strip()
                if seguinte.startswith("de ") and any(seguinte[3:].startswith(mes) for mes in _MESES):
                    continue          # "30 de junho"
                if casas == 0 and "." not in bruto:
                    if 1900 <= exibido <= 2100:
                        continue      # ano
                    if exibido < 1000:
                        continue      # inteiro pequeno sem marca monetária
        # sinal explícito (regra 5): "-" ou "−" imediatamente antes (admite
        # "R$" e "**" entre eles), exceto marcador de lista no início da linha
        # (regra B). Parênteses (regra C): só o número isolado, sem
        # multiplicador nem %, fica marcado como ambíguo.
        traco = re.search(r"([-−])[\s*]*(R\$\s*)?\(?[\s*]*$", antes)
        explicito_neg = False
        if traco:
            pos = a - len(antes) + traco.start(1)
            inicio_linha = texto.rfind("\n", 0, pos) + 1
            marcador = texto[inicio_linha:pos].strip(" \t*") == "" and \
                pos + 1 < len(texto) and texto[pos + 1] in " \t"
            explicito_neg = not marcador
        parenteses = not explicito_neg and bool(re.search(r"\(\s*(R\$\s*)?$", antes)) \
            and bool(re.match(r"\s*\)", texto[b:])) and not mult and not pct
        idx = next(i for i, (x, y) in enumerate(oracoes) if x <= a < y)
        numeros.append(Numero(texto[a:fim], a, tipo, exibido, casas, fator, implicita,
                              "-" if explicito_neg else "+", idx, parenteses))
    # regra 5: palavra negativa na oração; regra C: parênteses ambíguos
    for n in numeros:
        if n.sinal == "-" or n.tipo != "monetario":
            continue
        if n.parenteses and not _tem_palavra_negativa(texto[slice(*oracoes[n.oracao])], regra_sinal):
            n.sinal = "?"
            continue
        x, y = oracoes[n.oracao]
        if _tem_palavra_negativa(texto[x:y], regra_sinal):
            na_oracao = [o for o in numeros if o.oracao == n.oracao and o.tipo == "monetario"]
            n.sinal = "-" if len(na_oracao) == 1 else "?"
    return numeros


def _arredondar(v: Decimal, casas: int, modo) -> Decimal:
    return v.quantize(Decimal(1).scaleb(-casas), rounding=modo)


def confere(n: Numero, esperado: Decimal, tipo: str) -> bool:
    """Regras 4 e 6: compara |v| com |g| na unidade e precisão em que v foi escrito."""
    if n.tipo != tipo:
        return False
    g = abs(esperado) / n.multiplicador
    v = abs(n.exibido)
    return v in (_arredondar(g, n.casas, ROUND_HALF_UP), _arredondar(g, n.casas, ROUND_DOWN))


def _alvos(item: dict) -> list[list[dict]]:
    """Formas aceitas de um valor exigido: o próprio valor ou uma lista de parcelas."""
    formas = [[item]]
    for alt in item.get("formas_alternativas") or []:
        formas.append(alt["parcelas"])
    return formas


def _sinal_ok(n: Numero, alvo: dict, decisoes: dict) -> str:
    """'ok' | 'erro' | 'pendente' para um número que já confere em módulo."""
    if not alvo.get("sinal_exigido"):
        return "ok"
    sinal = n.sinal
    if sinal == "?":
        sinal = decisoes.get(n.inicio, "?")
    if sinal == "?":
        return "pendente"
    esperado = "-" if Decimal(alvo["valor"]) < 0 else "+"
    return "ok" if sinal == esperado else "erro"


def classificar(resposta: str, caso: dict, decisoes_sinal: dict | None = None,
                regra_sinal: str = "original") -> dict:
    """
    Classifica uma resposta contra os valores esperados de um caso do dataset.

    decisoes_sinal: {posição do número na resposta: "+"|"-"} para os números
    cujo sinal a regra 5 não resolveu (decisão manual registrada).
    regra_sinal: "original" (padrão; instrumento congelado) ou "emenda5" (Emenda 5).
    """
    decisoes = decisoes_sinal or {}
    numeros = extrair_numeros(resposta or "", regra_sinal)
    base = {
        "numeros_lidos": [n.texto for n in numeros],
        "escala_implicita": any(n.escala_implicita for n in numeros),
        "sinal_revisao_manual": any(n.sinal == "?" for n in numeros),
    }
    if not caso.get("verificacao_deterministica_aplicavel"):
        return {**base, "classe": NAO_APLICAVEL, "motivo": "categoria sem valores exigidos (N4)",
                "encontrados": [], "nao_encontrados": [], "valores_nao_conciliados": [n.texto for n in numeros],
                "pendencias_sinal": []}
    if not numeros:
        return {**base, "classe": NAO_APLICAVEL, "motivo": "resposta sem número monetário ou percentual",
                "encontrados": [], "nao_encontrados": [v["id"] for v in caso["valores_esperados"]],
                "valores_nao_conciliados": [], "pendencias_sinal": []}

    itens = caso["valores_esperados"]
    melhor = None
    # escolhe, por força bruta (poucos itens), a combinação de formas e de
    # números que concilia o maior número de itens, um número por alvo
    for formas in product(*[_alvos(i) for i in itens]):
        usados, achados, pend = set(), [], []
        for item, forma in zip(itens, formas):
            ok_item, usados_item, pend_item = True, [], []
            for alvo in forma:
                cand = None
                for n in numeros:
                    if n.inicio in usados or n.inicio in usados_item:
                        continue
                    if not confere(n, Decimal(alvo["valor"]), alvo["tipo"]):
                        continue
                    s = _sinal_ok(n, alvo, decisoes)
                    if s == "erro":
                        continue
                    cand = n
                    if s == "pendente":
                        pend_item.append(n.texto)
                    break
                if cand is None:
                    ok_item = False
                    break
                usados_item.append(cand.inicio)
            if ok_item:
                usados.update(usados_item)
                achados.append(item["id"])
                pend.extend(pend_item)
        chave = (len(achados), -len(pend))
        if melhor is None or chave > melhor[0]:
            melhor = (chave, achados, usados, pend)
    _, achados, usados, pend = melhor
    nao = [i["id"] for i in itens if i["id"] not in achados]
    if pend:
        classe = PENDENTE_SINAL
    elif not nao:
        classe = CORRETO
    elif achados:
        classe = PARCIALMENTE_CORRETO
    else:
        classe = INCORRETO
    return {**base, "classe": classe, "motivo": "",
            "encontrados": achados, "nao_encontrados": nao,
            "valores_nao_conciliados": [n.texto for n in numeros if n.inicio not in usados],
            "pendencias_sinal": pend}
