# tests/test_ragas_exatidao.py
#
# Verificação determinística de exatidão do RAGAS do TCC 2
# (avaliacao/ragas/exatidao.py; PROTOCOLO_RAGAS_TCC2.md, Seção 11.1).
# Só respostas sintéticas: nenhuma resposta real é avaliada aqui.

import os
import sys
import unittest
from decimal import Decimal

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "avaliacao", "ragas"))

import exatidao as X  # noqa: E402


def mon(ident, reais, sinal=False, alternativas=None):
    return {"id": ident, "tipo": "monetario", "valor": str(reais), "sinal_exigido": sinal,
            "formas_alternativas": alternativas or []}


def pct(ident, valor):
    return {"id": ident, "tipo": "percentual", "valor": str(valor), "sinal_exigido": False,
            "formas_alternativas": []}


def caso(*itens, aplicavel=True):
    return {"verificacao_deterministica_aplicavel": aplicavel, "valores_esperados": list(itens)}


RECEITA = caso(mon("receita", Decimal("9468313") * 1000))   # g = 9.468.313 mil


class Escalas(unittest.TestCase):
    def valores(self, texto):
        return [n.valor for n in X.extrair_numeros(texto)]

    def test_equivalencias_de_um_bilhao(self):
        for t in ("R$ 1.000 milhões", "R$ 1 bilhão", "1.000.000", "R$ 1.000.000 mil", "R$ 1 bi", "R$ 1.000 MM"):
            self.assertEqual(self.valores(t), [Decimal("1e9")], t)

    def test_escala_implicita_so_sem_multiplicador(self):
        n = X.extrair_numeros("receita de 9.468.313")[0]
        self.assertTrue(n.escala_implicita)
        self.assertFalse(X.extrair_numeros("R$ 9,47 bilhões")[0].escala_implicita)

    def test_formato_nao_normalizado_do_contexto(self):
        n = X.extrair_numeros("Despesa de provisão: -34397820.0000000000")[0]
        self.assertEqual(n.valor, Decimal("-34397820") * 1000)
        self.assertEqual(n.casas, 10)

    def test_trilhao(self):
        self.assertEqual(self.valores("R$ 1,13 trilhão"), [Decimal("1.13e12")])


class Arredondamento(unittest.TestCase):
    """Exemplos congelados na regra 6 da Seção 11.1."""

    def classe(self, texto):
        return X.classificar(texto, RECEITA)["classe"]

    def test_exemplos_do_protocolo_conferem(self):
        for t in ("R$ 9,47 bilhões", "R$ 9,46 bilhões", "R$ 9.468,3 milhões", "9.468.313",
                  "R$ 9,5 bilhões", "R$ 9,4 bilhões"):
            self.assertEqual(self.classe(f"A receita foi {t}."), X.CORRETO, t)

    def test_exemplos_que_nao_conferem(self):
        for t in ("R$ 9,5 mil", "R$ 9,48 bilhões", "R$ 9,47 milhões", "9.468.312", "R$ 10 bilhões"):
            self.assertEqual(self.classe(f"A receita foi {t}."), X.INCORRETO, t)

    def test_percentual_arredondado_ou_truncado(self):
        c = caso(pct("margem", Decimal("16.44678")))
        for t, esperado in (("16,45%", X.CORRETO), ("16,44%", X.CORRETO), ("16,4 por cento", X.CORRETO),
                            ("16%", X.CORRETO), ("16,46%", X.INCORRETO), ("17%", X.INCORRETO)):
            self.assertEqual(X.classificar(f"Margem de {t}.", c)["classe"], esperado, t)

    def test_percentual_nao_confere_com_monetario(self):
        c = caso(pct("margem", Decimal("16")))
        self.assertEqual(X.classificar("Resultado de R$ 16 mil.", c)["classe"], X.INCORRETO)

    def test_percentual_comparado_em_valor_absoluto(self):
        c = caso(pct("variacao", Decimal("-33.33")))
        self.assertEqual(X.classificar("Queda de 33,33%.", c)["classe"], X.CORRETO)


class Sinal(unittest.TestCase):
    PREJ = caso(mon("resultado", Decimal("-154679") * 1000, sinal=True))
    LUCRO = caso(mon("resultado", Decimal("3226245") * 1000, sinal=True))

    def classe(self, texto, c, decisoes=None):
        return X.classificar(texto, c, decisoes)["classe"]

    def test_negativo_por_marca_explicita(self):
        # Parênteses deixaram de ser marca explícita (Emenda 1, regra C):
        # ver RegrasComplementares.test_c_*.
        for t in ("Resultado de -R$ 154,7 milhões.", "Resultado de R$ -154,7 milhões.",
                  "Resultado: −154.679.", "Resultado: (-154.679)."):
            self.assertEqual(self.classe(t, self.PREJ), X.CORRETO, t)

    def test_negativo_por_palavra_na_oracao(self):
        self.assertEqual(self.classe("A Zamp teve prejuízo de R$ 154,7 milhões.", self.PREJ), X.CORRETO)
        self.assertEqual(self.classe("O resultado foi negativo em R$ 154,68 milhões.", self.PREJ), X.CORRETO)

    def test_sinal_divergente_nao_confere(self):
        self.assertEqual(self.classe("O resultado foi de R$ 154,7 milhões.", self.PREJ), X.INCORRETO)
        self.assertEqual(self.classe("Houve prejuízo de R$ 3,23 bilhões.", self.LUCRO), X.INCORRETO)

    def test_palavra_em_outra_oracao_nao_contamina(self):
        t = "A WEG não teve prejuízo. O lucro foi de R$ 3,23 bilhões."
        self.assertEqual(self.classe(t, self.LUCRO), X.CORRETO)

    def test_oracao_com_dois_valores_fica_pendente_e_decisao_manual_resolve(self):
        c = caso(mon("r26", Decimal("-154679") * 1000, True), mon("r25", Decimal("-116011") * 1000, True))
        t = "O prejuízo foi de R$ 154,7 milhões no 1S26, ante R$ 116,0 milhões no 1S25."
        r = X.classificar(t, c)
        self.assertEqual(r["classe"], X.PENDENTE_SINAL)
        self.assertTrue(r["sinal_revisao_manual"])
        decisoes = {n.inicio: "-" for n in X.extrair_numeros(t)}
        self.assertEqual(self.classe(t, c, decisoes), X.CORRETO)

    def test_sinal_ignorado_quando_nao_exigido(self):
        c = caso(mon("despesa", Decimal("-111283805") * 1000, sinal=False))
        self.assertEqual(self.classe("Despesas de R$ 111,28 bilhões.", c), X.CORRETO)

    def test_marcador_de_lista_nao_e_sinal(self):
        self.assertEqual(self.classe("Lucro consolidado:\n- R$ 3,23 bilhões", self.LUCRO), X.CORRETO)

    def test_reapresentacao_entre_parenteses_nao_e_sinal(self):
        self.assertEqual(self.classe("Lucro de 3.226.245 (R$ 3,23 bilhões).", self.LUCRO), X.CORRETO)


class NaoNumeros(unittest.TestCase):
    def test_datas_anos_periodos_e_trechos_ignorados(self):
        t = ("Em 30 de junho de 2026 (30/06/2026), no 1S26 e no 2T26, segundo o Trecho 2 "
             "e a conta 3.01, com 3 componentes.")
        self.assertEqual(X.extrair_numeros(t), [])

    def test_abstencao_e_nao_aplicavel(self):
        r = X.classificar("Os trechos fornecidos não informam a receita do período.", RECEITA)
        self.assertEqual(r["classe"], X.NAO_APLICAVEL)
        self.assertEqual(r["nao_encontrados"], ["receita"])

    def test_n4_e_nao_aplicavel_mesmo_com_numeros(self):
        r = X.classificar("O resultado financeiro piorou R$ 24,7 milhões.", caso(aplicavel=False))
        self.assertEqual(r["classe"], X.NAO_APLICAVEL)


class RegrasComplementares(unittest.TestCase):
    """Regras A–D da Emenda 1 do protocolo (antes da coleta)."""
    PREJ = caso(mon("resultado", Decimal("-154679") * 1000, sinal=True))
    LUCRO = caso(mon("resultado", Decimal("3226245") * 1000, sinal=True))

    def lidos(self, t):
        return [n.texto for n in X.extrair_numeros(t)]

    # A — o que não é número monetário
    def test_a_datas_anos_codigos_periodos_e_trechos(self):
        for t in ("30/06/2026", "31/12/2025", "em 2025", "no ano de 2026", "conta 3.01", "conta 1.01.02",
                  "no 1S25", "no 1S26", "Trecho 1", "trecho 3", "30 de junho", "31 de dezembro"):
            self.assertEqual(self.lidos(t), [], t)

    def test_a_inteiro_pequeno_so_com_marca_monetaria(self):
        self.assertEqual(self.lidos("foram 3 componentes e 12 empresas"), [])
        self.assertEqual(self.lidos("R$ 500"), ["500"])
        self.assertEqual(self.lidos("500 mil"), ["500 mil"])
        self.assertEqual(self.lidos("0,72"), ["0,72"])

    # B — marcador de lista
    def test_b_traco_de_lista_nao_e_sinal(self):
        for t in ("- R$ 10 milhões", "  - R$ 10 milhões", "* - R$ 10 milhões", "Itens:\n- 10.000"):
            self.assertEqual(X.extrair_numeros(t)[0].sinal, "+", t)
        self.assertEqual(X.extrair_numeros("-R$ 10 milhões")[0].sinal, "-")
        self.assertEqual(X.extrair_numeros("Saldo: - 10.000")[0].sinal, "-")

    # C — parênteses
    def test_c_reapresentacao_entre_parenteses_nao_e_negativa(self):
        for t in ("(R$ 19,6 bilhões)", "(19,6 bilhões)", "(16,4%)"):
            self.assertEqual(X.extrair_numeros(t)[0].sinal, "+", t)

    def test_c_numero_isolado_entre_parenteses_vai_para_revisao_manual(self):
        t = "Resultado consolidado: (154.679)."
        r = X.classificar(t, self.PREJ)
        self.assertEqual(r["classe"], X.PENDENTE_SINAL)
        self.assertTrue(r["sinal_revisao_manual"])
        pos = X.extrair_numeros(t)[0].inicio
        self.assertEqual(X.classificar(t, self.PREJ, {pos: "-"})["classe"], X.CORRETO)
        self.assertEqual(X.classificar(t, self.PREJ, {pos: "+"})["classe"], X.INCORRETO)

    def test_c_parenteses_com_palavra_negativa_na_oracao(self):
        self.assertEqual(X.classificar("Houve prejuízo de (154.679).", self.PREJ)["classe"], X.CORRETO)

    def test_c_reapresentacao_bruta_nao_impede_acerto(self):
        r = X.classificar("Lucro de R$ 3,23 bilhões (3.226.245).", self.LUCRO)
        self.assertEqual(r["classe"], X.CORRETO)

    def test_c_sinal_ambiguo_irrelevante_quando_nao_exigido(self):
        c = caso(mon("caixa", Decimal("7750256") * 1000))
        self.assertEqual(X.classificar("Caixa: (7.750.256).", c)["classe"], X.CORRETO)

    # D — pontuação
    def test_d_numero_brasileiro_seguido_de_pontuacao(self):
        for t in ("R$ 9.468.313.", "R$ 9.468.313,", "R$ 9.468.313;", "R$ 9.468.313!", "R$ 9.468.313)"):
            self.assertEqual(X.extrair_numeros(t)[0].valor, Decimal("9468313") * 1000, t)
        self.assertEqual(X.classificar("A receita foi R$ 9.468.313.", RECEITA)["classe"], X.CORRETO)


class Conciliacao(unittest.TestCase):
    N3 = caso(mon("r26", Decimal("3226245") * 1000, True), mon("r25", Decimal("3329842") * 1000, True),
              pct("var", Decimal("-3.111")))

    def test_correto_parcial_incorreto(self):
        self.assertEqual(X.classificar("Lucro de R$ 3,23 bi no 1S26 e R$ 3,33 bi no 1S25, queda de 3,1%.", self.N3)["classe"], X.CORRETO)
        r = X.classificar("Lucro de R$ 3,23 bi no 1S26 e R$ 3,33 bi no 1S25.", self.N3)
        self.assertEqual(r["classe"], X.PARCIALMENTE_CORRETO)
        self.assertEqual(r["nao_encontrados"], ["var"])
        self.assertEqual(X.classificar("Lucro de R$ 4,1 bi.", self.N3)["classe"], X.INCORRETO)

    def test_valores_nao_conciliados_listados_sem_mudar_classe(self):
        r = X.classificar("A receita foi R$ 9,47 bilhões e o custo R$ 6,2 bilhões.", RECEITA)
        self.assertEqual(r["classe"], X.CORRETO)
        self.assertEqual(r["valores_nao_conciliados"], ["6,2 bilhões"])

    def test_forma_alternativa_por_parcelas(self):
        p1, p2 = mon("circ", Decimal("3163058") * 1000), mon("ncirc", Decimal("1903288") * 1000)
        c = caso(mon("caixa", Decimal("7750256") * 1000),
                 mon("divida", Decimal("5066346") * 1000, alternativas=[{"parcelas": [p1, p2]}]))
        self.assertEqual(X.classificar("Caixa de R$ 7,75 bi; dívida total de R$ 5,07 bi.", c)["classe"], X.CORRETO)
        self.assertEqual(X.classificar("Caixa de R$ 7,75 bi; empréstimos de R$ 3,16 bi (circulante) e R$ 1,9 bi.", c)["classe"], X.CORRETO)
        self.assertEqual(X.classificar("Caixa de R$ 7,75 bi; empréstimos circulantes de R$ 3,16 bi.", c)["classe"], X.PARCIALMENTE_CORRETO)

    def test_um_numero_concilia_no_maximo_um_valor(self):
        c = caso(mon("a", Decimal("1000") * 1000), mon("b", Decimal("1000") * 1000))
        self.assertEqual(X.classificar("O valor foi R$ 1 milhão.", c)["classe"], X.PARCIALMENTE_CORRETO)
        self.assertEqual(X.classificar("R$ 1 milhão e R$ 1 milhão.", c)["classe"], X.CORRETO)


class Emenda5RotuloAmbivalente(unittest.TestCase):
    """Emenda 5 do protocolo: rótulo com termos opostos ("Lucro/Prejuízo") não indica sinal
    com regra_sinal="emenda5"; o padrão continua sendo o instrumento original."""
    LUCRO = caso(mon("resultado", Decimal("184619") * 1000, sinal=True))
    PREJ = caso(mon("resultado", Decimal("-154679") * 1000, sinal=True))

    def classe(self, texto, c, regra="emenda5"):
        return X.classificar(texto, c, None, regra_sinal=regra)["classe"]

    # rótulos ambivalentes não tornam o número negativo
    def test_rotulo_com_barra(self):
        self.assertEqual(self.classe('O "Lucro/Prejuízo Consolidado do Período" é de 184.619.', self.LUCRO), X.CORRETO)

    def test_rotulo_com_ou(self):
        self.assertEqual(self.classe("O Lucro ou Prejuízo Líquido Consolidado do Período foi de 184.619.", self.LUCRO),
                         X.CORRETO)

    def test_rotulo_com_parenteses_fechados(self):
        self.assertEqual(self.classe("O Lucro (Prejuízo) do período foi de 184.619.", self.LUCRO), X.CORRETO)

    def test_rotulo_em_ordem_inversa(self):
        self.assertEqual(self.classe("Prejuízo/Lucro do período: 184.619.", self.LUCRO), X.CORRETO)

    def test_alternativa_da_pergunta_repetida(self):
        self.assertEqual(self.classe("O resultado líquido (lucro ou prejuízo) foi de 184.619.", self.LUCRO), X.CORRETO)

    def test_superavit_deficit_e_rotulo(self):
        self.assertEqual(self.classe("O superávit/déficit do período foi de 184.619.", self.LUCRO), X.CORRETO)

    # sinais negativos reais continuam valendo
    def test_rotulo_com_palavra_negativa_fora_do_par(self):
        self.assertEqual(self.classe("O Lucro/Prejuízo do período foi um prejuízo de 154.679.", self.PREJ), X.CORRETO)

    def test_rotulo_com_traco_explicito(self):
        self.assertEqual(self.classe("O Lucro/Prejuízo do período é de -154.679.", self.PREJ), X.CORRETO)

    def test_rotulo_sem_marca_negativa_nao_confere_com_prejuizo(self):
        self.assertEqual(self.classe("O Lucro/Prejuízo do período é de 154.679.", self.PREJ), X.INCORRETO)

    def test_palavra_prejuizo_isolada(self):
        self.assertEqual(self.classe("A Zamp teve prejuízo de R$ 154,7 milhões.", self.PREJ), X.CORRETO)

    def test_palavra_negativo_isolada(self):
        self.assertEqual(self.classe("O resultado foi negativo em 154.679.", self.PREJ), X.CORRETO)

    def test_palavra_prejuizos_isolada(self):
        self.assertEqual(self.classe("Os prejuízos somaram 154.679.", self.PREJ), X.CORRETO)

    # regra C (parênteses) com rótulo
    def test_parenteses_com_rotulo_sem_palavra_fora_do_par_vai_para_revisao(self):
        self.assertEqual(self.classe("O Lucro/Prejuízo foi de (154.679).", self.PREJ), X.PENDENTE_SINAL)

    def test_parenteses_com_palavra_negativa_fora_do_par(self):
        self.assertEqual(self.classe("Lucro/Prejuízo: houve prejuízo de (154.679).", self.PREJ), X.CORRETO)

    # complementares
    def test_padrao_e_o_instrumento_original(self):
        t = 'O "Lucro/Prejuízo Consolidado do Período" é de 184.619.'
        self.assertEqual(X.classificar(t, self.LUCRO)["classe"], X.INCORRETO)
        self.assertEqual(self.classe(t, self.LUCRO, "original"), X.INCORRETO)
        self.assertEqual([n.sinal for n in X.extrair_numeros(t)], ["-"])
        self.assertEqual([n.sinal for n in X.extrair_numeros(t, "emenda5")], ["+"])

    def test_regra_desconhecida_e_rejeitada(self):
        for regra in ("emenda", "EMENDA5", "", None):
            with self.assertRaises(ValueError, msg=regra):
                X.classificar("R$ 1 bilhão", self.LUCRO, None, regra_sinal=regra)
            with self.assertRaises(ValueError, msg=regra):
                X.extrair_numeros("R$ 1 bilhão", regra)

    def test_parentese_explicativo_nao_e_rotulo(self):
        self.assertEqual(self.classe("Teve prejuízo (lucro operacional foi positivo) de 154.679.", self.PREJ),
                         X.CORRETO)
        self.assertEqual(self.classe("Teve prejuízo (lucro de 2025 foi maior) de 154.679.", self.PREJ), X.CORRETO)


if __name__ == "__main__":
    unittest.main()
