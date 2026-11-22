# tests/test_demonstracoes_resumidas.py
#
# Bloco demonstracoes_resumidas de calcular_metricas(): resultado (DRE) e
# caixa (DFC) em primeiro nível, na base de base_dados, mais a abertura do
# "Resultado Financeiro". Substitui, para o Prompt 2, a tabela inteira que o
# canal narrativo entregava (achado 4 da validação manual do TCC 2: a ZAMP3
# teve um ajuste da DFC, 6.01.01.04, lido como despesa com juros).
#
# Execução (na raiz do projeto):
#   python -m unittest tests.test_demonstracoes_resumidas -v

import json
import os
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from modulos.extracao import extrair_documento  # noqa: E402
from modulos.metricas import (calcular_metricas, formatar_moeda,  # noqa: E402
                              formatar_pct, interpretar_variacao_factual,
                              rotular_periodos, variacao_pct)

FIXTURES   = os.path.join(RAIZ, "tests", "fixtures")
COMPARACAO = rotular_periodos("2026-06-30", "ITR")["comparacao_resultado"]
CAMPOS     = {"conta", "valor_atual", "valor_anterior", "variacao_pct",
              "interpretacao_variacao", "comparacao"}


# ── Documentos sintéticos ─────────────────────────────────────────────────────

def _secao(titulo, linhas, com_codigo=True):
    corpo = "\n".join(
        (f"[{c}] " if com_codigo else "") + f"{n:<55} {float(a):>20.10f}  (anterior: {float(b):.10f})"
        for c, n, a, b in linhas)
    return f"\n{'=' * 50}\n{titulo}\n{'=' * 50}\n{corpo}"


def _metricas(secoes, com_codigo=True):
    texto = "\n".join(["DOCUMENTO: ITR — 2026-06-30", "EMPRESA CVM: 9999", "VERSAO: 1",
                       "FORMATO: CD_CONTA", ""] +
                      [_secao(t, l, com_codigo) for t, l in secoes])
    with tempfile.TemporaryDirectory() as tmp:
        caminho = os.path.join(tmp, "doc.txt")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(texto)
        return calcular_metricas(extrair_documento(caminho))


DRE_CON = [
    ("3.01",       "Receita de Venda de Bens e/ou Serviços",                  1000000,  900000),
    ("3.02",       "Custo dos Bens e/ou Serviços Vendidos",                   -600000, -550000),
    ("3.03",       "Resultado Bruto",                                          400000,  350000),
    ("3.04",       "Despesas/Receitas Operacionais",                          -200000, -190000),
    ("3.04.01",    "Despesas com Vendas",                                     -100000,  -90000),
    ("3.05",       "Resultado Antes do Resultado Financeiro e dos Tributos",   200000,  160000),
    ("3.06",       "Resultado Financeiro",                                     -50000,  -40000),
    ("3.06.01",    "Receitas Financeiras",                                      30000,   20000),
    ("3.06.02",    "Despesas Financeiras",                                     -80000,  -60000),
    ("3.06.02.01", "Juros sobre empréstimos",                                  -70000,  -50000),
    ("3.07",       "Resultado Antes dos Tributos sobre o Lucro",               150000,  120000),
    ("3.08",       "Imposto de Renda e Contribuição Social sobre o Lucro",     -50000,  -40000),
    ("3.09",       "Resultado Líquido das Operações Continuadas",              100000,   80000),
    ("3.10",       "Resultado Líquido de Operações Descontinuadas",                 0,       0),
    ("3.11",       "Lucro/Prejuízo Consolidado do Período",                    100000,   80000),
    ("3.11.01",    "Atribuído a Sócios da Empresa Controladora",                90000,   70000),
    ("3.99",       "Lucro por Ação - (Reais / Ação)",                               1,       1),
]
DRE_IND = [
    ("3.01", "Receita de Venda de Bens e/ou Serviços",   11111, 22222),
    ("3.06", "Resultado Financeiro",                     33333, 44444),
    ("3.11", "Lucro/Prejuízo do Período",                55555, 66666),
]
DFC_CON = [
    ("6.01",       "Caixa Líquido Atividades Operacionais",                   300000,  250000),
    ("6.01.01",    "Caixa Gerado nas Operações",                              350000,  300000),
    ("6.01.01.04", "Juros, encargos, variação cambial, variação monetária e AVP sobre passivos de arrendamentos",
                                                                              162230,  103419),
    ("6.02",       "Caixa Líquido Atividades de Investimento",               -100000,  -80000),
    ("6.03",       "Caixa Líquido Atividades de Financiamento",               -50000,   60000),
    ("6.05",       "Aumento (Redução) de Caixa e Equivalentes",               150000,  230000),
]
DOC_CONSOLIDADO = [("Demonstração de Resultado (Consolidado)", DRE_CON),
                   ("Demonstração de Resultado (Individual)", DRE_IND),
                   ("Demonstração de Fluxo de Caixa (Consolidado)", DFC_CON)]


def _contas(itens):
    return [i["conta"] for i in itens]


def _item(itens, conta):
    return next(i for i in itens if i["conta"] == conta)


class TestSelecaoSintetica(unittest.TestCase):

    def setUp(self):
        self.bloco = _metricas(DOC_CONSOLIDADO)["demonstracoes_resumidas"]

    def test_dre_primeiro_nivel_e_filhas_do_resultado_financeiro_na_ordem(self):
        self.assertEqual(_contas(self.bloco["resultado"]), [
            "Receita de Venda de Bens e/ou Serviços",
            "Custo dos Bens e/ou Serviços Vendidos",
            "Resultado Bruto",
            "Despesas/Receitas Operacionais",
            "Resultado Antes do Resultado Financeiro e dos Tributos",
            "Resultado Financeiro",
            "Receitas Financeiras",
            "Despesas Financeiras",
            "Resultado Antes dos Tributos sobre o Lucro",
            "Imposto de Renda e Contribuição Social sobre o Lucro",
            "Resultado Líquido das Operações Continuadas",
            "Lucro/Prejuízo Consolidado do Período",
        ])

    def test_exclui_3_99_linhas_zeradas_e_niveis_mais_profundos(self):
        contas = _contas(self.bloco["resultado"])
        for fora in ("Lucro por Ação - (Reais / Ação)",           # 3.99
                     "Resultado Líquido de Operações Descontinuadas",  # zerada
                     "Despesas com Vendas",                        # 3.04.01
                     "Juros sobre empréstimos",                    # 3.06.02.01
                     "Atribuído a Sócios da Empresa Controladora"):  # 3.11.01
            self.assertNotIn(fora, contas)

    def test_dfc_so_primeiro_nivel_sem_ajustes_de_conciliacao(self):
        self.assertEqual(_contas(self.bloco["fluxo_de_caixa"]), [
            "Caixa Líquido Atividades Operacionais",
            "Caixa Líquido Atividades de Investimento",
            "Caixa Líquido Atividades de Financiamento",
            "Aumento (Redução) de Caixa e Equivalentes",
        ])
        self.assertNotIn(formatar_moeda(162230), json.dumps(self.bloco, ensure_ascii=False))

    def test_campos_formatacao_e_comparacao(self):
        rf = _item(self.bloco["resultado"], "Resultado Financeiro")
        self.assertEqual(set(rf), CAMPOS)
        self.assertEqual(rf["valor_atual"],    formatar_moeda(-50000))
        self.assertEqual(rf["valor_anterior"], formatar_moeda(-40000))
        self.assertEqual(rf["variacao_pct"],   formatar_pct(variacao_pct(-50000, -40000)))
        self.assertEqual(rf["variacao_pct"],   "-25,0%")   # piorou: sinal negativo
        self.assertEqual(rf["comparacao"],     COMPARACAO)
        fc = _item(self.bloco["fluxo_de_caixa"], "Caixa Líquido Atividades de Financiamento")
        self.assertEqual(fc["comparacao"], COMPARACAO)

    def test_usa_a_base_consolidada_e_ignora_a_individual(self):
        self.assertEqual(self.bloco["base"], "Consolidado")
        texto = json.dumps(self.bloco, ensure_ascii=False)
        for v in (11111, 33333, 55555):
            self.assertNotIn(formatar_moeda(v), texto)

    def test_resultado_financeiro_em_outro_codigo(self):
        # Plano com o resultado financeiro em 3.08 (4 empresas no ITR 2T26)
        dre = [("3.01", "Receita de Venda de Bens e/ou Serviços", 1000, 900),
               ("3.08", "Resultado Financeiro", -50, -40),
               ("3.08.01", "Receitas Financeiras", 30, 20),
               ("3.08.02", "Despesas Financeiras", -80, -60),
               ("3.11", "Lucro/Prejuízo Consolidado do Período", 100, 80)]
        bloco = _metricas([("Demonstração de Resultado (Consolidado)", dre)])["demonstracoes_resumidas"]
        self.assertEqual(_contas(bloco["resultado"]), [
            "Receita de Venda de Bens e/ou Serviços", "Resultado Financeiro",
            "Receitas Financeiras", "Despesas Financeiras",
            "Lucro/Prejuízo Consolidado do Período"])

    def test_banco_sem_resultado_financeiro(self):
        dre = [("3.01", "Receitas de Intermediação Financeira", 160747114, 149252571),
               ("3.02", "Despesas de Intermediação Financeira", -111283805, -101288276),
               ("3.03", "Resultado Bruto de Intermediação Financeira", 49463309, 47964295),
               ("3.05", "Resultado antes dos Tributos sobre o Lucro", 2725127, 1643370),
               ("3.06", "Imposto de Renda e Contribuição Social sobre o Lucro", 3637834, 6116746),
               ("3.11", "Lucro ou Prejuízo Líquido Consolidado do Período", 6362961, 7760116)]
        bloco = _metricas([("Demonstração de Resultado (Consolidado)", dre)])["demonstracoes_resumidas"]
        self.assertEqual(len(bloco["resultado"]), 6)
        self.assertEqual(_item(bloco["resultado"], "Imposto de Renda e Contribuição Social sobre o Lucro")
                         ["valor_atual"], formatar_moeda(3637834))
        self.assertEqual(bloco["fluxo_de_caixa"], [])

    def test_empresa_so_individual(self):
        m = _metricas([("Demonstração de Resultado (Individual)", DRE_CON)])
        bloco = m["demonstracoes_resumidas"]
        self.assertEqual((m["base_dados"], bloco["base"]), ("Individual", "Individual"))
        self.assertEqual(len(bloco["resultado"]), 12)
        self.assertEqual(bloco["fluxo_de_caixa"], [])   # DFC individual não é extraída

    def test_documento_sem_codigo_bloco_vazio_e_demais_campos_iguais(self):
        com = _metricas(DOC_CONSOLIDADO)
        sem = _metricas(DOC_CONSOLIDADO, com_codigo=False)
        self.assertEqual(sem["demonstracoes_resumidas"],
                         {"base": "Consolidado", "resultado": [], "fluxo_de_caixa": []})
        com.pop("demonstracoes_resumidas"); sem.pop("demonstracoes_resumidas")
        # A decomposição do resultado também depende do CD_CONTA
        # (tests/test_decomposicao_resultado.py); fora dela, nada muda.
        self.assertFalse(sem.pop("decomposicao_resultado")["fecha"])
        self.assertTrue(com.pop("decomposicao_resultado")["fecha"])
        self.assertEqual(com, sem)


# ── Documentos reais do ITR 2026-06-30 v1 ─────────────────────────────────────

class TestDocumentosReais(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.bloco = {}
        for t in ("WEGE3", "BBAS3", "ZAMP3"):
            m = calcular_metricas(extrair_documento(
                os.path.join(FIXTURES, f"{t}_ITR_2026-06-30_cd_conta.txt")))
            cls.bloco[t] = m["demonstracoes_resumidas"]

    def _texto(self, t):
        return json.dumps(self.bloco[t], ensure_ascii=False)

    def test_wege3_resultado_financeiro_consolidado(self):
        rf = _item(self.bloco["WEGE3"]["resultado"], "Resultado Financeiro")
        self.assertEqual((rf["valor_atual"], rf["valor_anterior"]),
                         (formatar_moeda(65819), formatar_moeda(47595)))
        self.assertEqual(self.bloco["WEGE3"]["base"], "Consolidado")

    def test_wege3_nenhum_valor_da_dre_individual(self):
        texto = self._texto("WEGE3")
        # Resultado Financeiro individual (achado 2) e Outras Despesas
        # Operacionais individuais
        for v in (10552, 3924, -6457, -2788):
            self.assertNotIn(formatar_moeda(v), texto)
        self.assertNotIn("Outras Despesas Operacionais", _contas(self.bloco["WEGE3"]["resultado"]))

    def test_zamp3_resultado_e_despesas_financeiras_da_dre_consolidada(self):
        res = self.bloco["ZAMP3"]["resultado"]
        rf = _item(res, "Resultado Financeiro")
        df = _item(res, "Despesas Financeiras")
        self.assertEqual((rf["valor_atual"], rf["valor_anterior"]),
                         (formatar_moeda(-169280), formatar_moeda(-144604)))
        self.assertEqual((df["valor_atual"], df["valor_anterior"]),
                         (formatar_moeda(-209602), formatar_moeda(-177818)))

    def test_zamp3_sem_o_ajuste_de_arrendamentos_da_dfc(self):
        texto = self._texto("ZAMP3")
        for v in (162230, 103419):
            self.assertNotIn(formatar_moeda(v), texto)
        self.assertFalse(any("arrendamento" in c.lower()
                             for c in _contas(self.bloco["ZAMP3"]["resultado"]) +
                             _contas(self.bloco["ZAMP3"]["fluxo_de_caixa"])))

    def test_bbas3_plano_de_banco_com_ir_cs(self):
        res = self.bloco["BBAS3"]["resultado"]
        self.assertEqual(res[0]["conta"], "Receitas de Intermediação Financeira")
        ir = _item(res, "Imposto de Renda e Contribuição Social sobre o Lucro")
        self.assertEqual((ir["valor_atual"], ir["valor_anterior"]),
                         (formatar_moeda(3637834), formatar_moeda(6116746)))
        self.assertNotIn("Resultado Financeiro", _contas(res))
        self.assertIn("Caixa Líquido das Atividades Operacionais",
                      _contas(self.bloco["BBAS3"]["fluxo_de_caixa"]))

    def test_auditoria_das_narrativas_congeladas_mantem_os_vereditos(self):
        # O auditor varre todas as métricas: os valores do bloco passam a ser
        # fatos "métrica calculada". Nenhum veredito da validação pode mudar.
        from modulos.auditoria import auditar_narrativa
        for t in ("WEGE3", "BBAS3", "ZAMP3"):
            with self.subTest(ticker=t):
                pasta = os.path.join(RAIZ, "avaliacao", "validacao_manual", f"{t}_ITR_2026-06-30_v1")
                with open(os.path.join(pasta, "resultado_analisar.json"), encoding="utf-8") as f:
                    a = json.load(f)["analise"]
                secoes = extrair_documento(os.path.join(FIXTURES, f"{t}_ITR_2026-06-30_cd_conta.txt"))
                dados = dict(a["dados_extraidos"])
                dados["demonstracoes_resumidas"] = calcular_metricas(secoes)["demonstracoes_resumidas"]
                novo = auditar_narrativa(a["secoes"], secoes, dados)
                chave = lambda v: (v["secao"], v["trecho"], v["tipo"], v["veredito"])
                self.assertEqual([chave(v) for v in novo["verificacoes"]],
                                 [chave(v) for v in a["auditoria"]["verificacoes"]])

    def test_tres_empresas_consolidadas_com_dre_e_dfc(self):
        for t in ("WEGE3", "BBAS3", "ZAMP3"):
            with self.subTest(ticker=t):
                b = self.bloco[t]
                self.assertEqual(b["base"], "Consolidado")
                self.assertTrue(b["resultado"])
                self.assertTrue(b["fluxo_de_caixa"])
                for item in b["resultado"] + b["fluxo_de_caixa"]:
                    self.assertEqual(set(item), CAMPOS)
                    self.assertEqual(item["comparacao"], COMPARACAO)


# ── interpretacao_variacao ────────────────────────────────────────────────────

class TestInterpretacaoVariacao(unittest.TestCase):
    """Descrição factual da mudança, sem juízo de bom/ruim."""

    INVERSAO = "(inversão de sinal: a variação percentual não é comparável)"

    def test_casos(self):
        casos = [
            # (atual, anterior, esperado)
            (110, 100,  "aumentou 10,0%"),                                        # positivo que aumenta
            (90, 100,   "diminuiu 10,0%"),                                        # positivo que diminui
            (-120, -100, "ficou mais negativo (em valor absoluto, 20,0% maior)"),  # negativo que piora em módulo
            (-80, -100,  "ficou menos negativo (em valor absoluto, 20,0% menor)"), # negativo que melhora em módulo
            (-50, 100,  f"passou de positivo para negativo {self.INVERSAO}"),
            (50, -100,  f"passou de negativo para positivo {self.INVERSAO}"),
            (50, 0,     "passou de zero para um valor positivo (sem base para variação percentual)"),
            (-50, 0,    "passou de zero para um valor negativo (sem base para variação percentual)"),
            (0, 100,    "passou de positivo para zero"),
            (0, -100,   "passou de negativo para zero"),
            (100, 100,  "não variou"),
            (-100, -100, "não variou"),
        ]
        for atual, anterior, esperado in casos:
            with self.subTest(atual=atual, anterior=anterior):
                self.assertEqual(interpretar_variacao_factual(atual, anterior), esperado)

    def test_nao_classifica_como_bom_ou_ruim(self):
        for atual, anterior in ((110, 100), (90, 100), (-120, -100), (-80, -100),
                                (-50, 100), (50, -100), (50, 0), (0, 100)):
            texto = interpretar_variacao_factual(atual, anterior)
            for juizo in ("melhor", "pior", "bom", "ruim", "positivo para o", "negativo para o"):
                self.assertNotIn(juizo, texto)

    def test_inversao_de_sinal_no_bloco_sintetico(self):
        dre = [("3.01", "Receita de Venda de Bens e/ou Serviços", 1000, 900),
               ("3.06", "Resultado Financeiro", -30, 20),
               ("3.08", "Imposto de Renda e Contribuição Social sobre o Lucro", 15, -40),
               ("3.11", "Lucro/Prejuízo Consolidado do Período", 100, 0)]
        res = _metricas([("Demonstração de Resultado (Consolidado)", dre)])["demonstracoes_resumidas"]["resultado"]
        rf, ir, lucro = (_item(res, c) for c in ("Resultado Financeiro",
                         "Imposto de Renda e Contribuição Social sobre o Lucro",
                         "Lucro/Prejuízo Consolidado do Período"))
        self.assertEqual(rf["interpretacao_variacao"], f"passou de positivo para negativo {self.INVERSAO}")
        self.assertEqual(rf["variacao_pct"], "-250,0%")        # preservado, mas não comparável
        self.assertEqual(ir["interpretacao_variacao"], f"passou de negativo para positivo {self.INVERSAO}")
        self.assertEqual(ir["variacao_pct"], "+137,5%")
        self.assertTrue(lucro["interpretacao_variacao"].startswith("passou de zero para um valor positivo"))
        self.assertEqual(lucro["variacao_pct"], "nao_disponivel")


class TestInterpretacaoDocumentosReais(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.b = {t: calcular_metricas(extrair_documento(os.path.join(
                     FIXTURES, f"{t}_ITR_2026-06-30_cd_conta.txt")))["demonstracoes_resumidas"]
                 for t in ("WEGE3", "BBAS3", "ZAMP3")}

    def _i(self, t, grupo, conta):
        return _item(self.b[t][grupo], conta)

    def test_zamp3_despesas_financeiras_ficaram_mais_negativas(self):
        df = self._i("ZAMP3", "resultado", "Despesas Financeiras")
        # variacao_pct "-17,9%" preservado; a interpretação diz o que aconteceu:
        # a despesa cresceu (de -177,8 para -209,6 mi)
        self.assertEqual(df["variacao_pct"], "-17,9%")
        self.assertEqual(df["interpretacao_variacao"],
                         "ficou mais negativo (em valor absoluto, 17,9% maior)")

    def test_zamp3_resultado_financeiro_e_ir_cs(self):
        self.assertEqual(self._i("ZAMP3", "resultado", "Resultado Financeiro")["interpretacao_variacao"],
                         "ficou mais negativo (em valor absoluto, 17,1% maior)")
        ir = self._i("ZAMP3", "resultado", "Imposto de Renda e Contribuição Social sobre o Lucro")
        self.assertEqual(ir["variacao_pct"], "-300,6%")
        self.assertTrue(ir["interpretacao_variacao"].startswith("passou de positivo para negativo"))

    def test_wege3_custo_ficou_menos_negativo(self):
        custo = self._i("WEGE3", "resultado", "Custo dos Bens e/ou Serviços Vendidos")
        self.assertEqual(custo["variacao_pct"], "+2,1%")
        self.assertEqual(custo["interpretacao_variacao"],
                         "ficou menos negativo (em valor absoluto, 2,1% menor)")

    def test_wege3_financiamento_inverteu_de_sinal(self):
        fin = self._i("WEGE3", "fluxo_de_caixa", "Caixa Líquido Atividades de Financiamento")
        self.assertEqual(fin["variacao_pct"], "+123,0%")
        self.assertTrue(fin["interpretacao_variacao"].startswith("passou de negativo para positivo"))

    def test_positivos_que_aumentam_e_diminuem(self):
        self.assertEqual(self._i("ZAMP3", "resultado", "Receita de Venda de Bens e/ou Serviços")
                         ["interpretacao_variacao"], "aumentou 11,2%")
        self.assertEqual(self._i("BBAS3", "resultado", "Imposto de Renda e Contribuição Social sobre o Lucro")
                         ["interpretacao_variacao"], "diminuiu 40,5%")

    def test_todo_item_tem_interpretacao(self):
        for t, b in self.b.items():
            for item in b["resultado"] + b["fluxo_de_caixa"]:
                with self.subTest(ticker=t, conta=item["conta"]):
                    self.assertTrue(item["interpretacao_variacao"])


if __name__ == "__main__":
    unittest.main()
