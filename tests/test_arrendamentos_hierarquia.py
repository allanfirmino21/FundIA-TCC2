# tests/test_arrendamentos_hierarquia.py
#
# Deduplicação hierárquica dos passivos de arrendamento (IFRS 16) na visão
# ampliada do endividamento. Com CD_CONTA, só é arrendamento ADICIONAL à dívida
# bruta a conta com "arrendament" no nome que não descende de uma conta da
# dívida bruta nem de outro arrendamento já somado. No ITR 2026-06-30, 41
# companhias tinham o arrendamento dentro de "Empréstimos e Financiamentos"
# (ex.: LWSA3, "Passivo de arrendamento" 2.01.04.03.01) recontado por cima da
# dívida bruta, e a C&A lança "Financiamento por Arrendamento" em Outras
# Obrigações, que a exclusão pelo nome ignorava. Sem CD_CONTA a hierarquia não
# é recuperável: o comportamento anterior é mantido (limitação documentada).
#
# Execução (na raiz do projeto):
#   python -m unittest tests.test_arrendamentos_hierarquia -v

import os
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from modulos.extracao import extrair_documento  # noqa: E402
from modulos.metricas import (_eh_descendente, _emprestimos_por_bloco,  # noqa: E402
                              calcular_metricas, formatar_moeda)

FIXTURES = os.path.join(RAIZ, "tests", "fixtures")
SEP = "=" * 50
AMPLIADOS = ("passivos_arrendamento", "divida_bruta_com_arrendamentos",
             "divida_liquida_com_arrendamentos")


def _documento(passivo, com_codigo=True):
    """Plano comercial mínimo: DRE, ativo com caixa de 300 e o passivo dado."""
    def linha(cod, nome, a, b):
        return (f"[{cod}] " if com_codigo else "") + f"{nome:<55} {float(a):>20.10f}  (anterior: {float(b):.10f})"
    secoes = [
        ("Demonstração de Resultado (Consolidado)", [
            ("3.01", "Receita de Venda de Bens e/ou Serviços", 1000, 900),
            ("3.03", "Resultado Bruto", 400, 350),
            ("3.05", "Resultado Antes do Resultado Financeiro e dos Tributos", 200, 180),
            ("3.11", "Lucro/Prejuízo Consolidado do Período", 100, 90)]),
        ("Balanço Patrimonial — Ativo (Consolidado)", [
            ("1", "Ativo Total", 3000, 2800),
            ("1.01", "Ativo Circulante", 1500, 1400),
            ("1.01.01", "Caixa e Equivalentes de Caixa", 300, 250)]),
        ("Balanço Patrimonial — Passivo (Consolidado)",
         [("2", "Passivo Total", 3000, 2800)] + passivo),
    ]
    texto = ["DOCUMENTO: ITR — 2026-06-30", "EMPRESA CVM: 9999", "VERSAO: 1"]
    if com_codigo:
        texto.append("FORMATO: CD_CONTA")
    texto.append("")
    for titulo, linhas in secoes:
        texto += [f"\n{SEP}", titulo, SEP] + [linha(*l) for l in linhas]
    with tempfile.TemporaryDirectory() as tmp:
        caminho = os.path.join(tmp, "doc.txt")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write("\n".join(texto))
        return extrair_documento(caminho)


def _emprestimos(cod, total, emprestimo=0, arrendamento=0, filha="Passivo de arrendamento"):
    """Bloco "Empréstimos e Financiamentos" no formato fixo da CVM."""
    linhas = [(cod, "Empréstimos e Financiamentos", total, total),
              (f"{cod}.01", "Empréstimos e Financiamentos", emprestimo, emprestimo),
              (f"{cod}.02", "Debêntures", 0, 0),
              (f"{cod}.03", "Financiamento por Arrendamento", arrendamento, arrendamento)]
    if filha:
        linhas.append((f"{cod}.03.01", filha, arrendamento, arrendamento))
    return linhas


def _outras(cod, *filhas):
    """Bloco "Outras Obrigações" > "Outros" com as contas dadas (código, nome, valor)."""
    total = sum(v for c, _, v in filhas if c.count(".") == cod.count(".") + 2)
    return ([(cod, "Outras Obrigações", total, total), (f"{cod}.02", "Outros", total, total)]
            + [(c, n, v, v) for c, n, v in filhas])


def _passivo(circ, ncirc):
    return ([("2.01", "Passivo Circulante", 1000, 900)] + circ
            + [("2.02", "Passivo Não Circulante", 900, 850)] + ncirc
            + [("2.03", "Patrimônio Líquido Consolidado", 1100, 1050)])


def _endividamento(doc):
    m = calcular_metricas(doc)
    return m["endividamento"], m["outros_destaques"]


def _tem_destaque_arrendamento(destaques):
    return any(d.startswith("Além dos empréstimos") for d in destaques)


class TestAncestralidade(unittest.TestCase):

    def test_descendentes(self):
        self.assertTrue(_eh_descendente("2.01.04.03", "2.01.04"))
        self.assertTrue(_eh_descendente("2.01.04.03.01", "2.01.04"))
        self.assertTrue(_eh_descendente("2.01.04.03.01", "2.01.04.03"))

    def test_nao_descendentes(self):
        self.assertFalse(_eh_descendente("2.01.040.03", "2.01.04"))   # só textualmente parecido
        self.assertFalse(_eh_descendente("2.01.041", "2.01.04"))
        self.assertFalse(_eh_descendente("2.01.05.02.07", "2.01.04"))
        self.assertFalse(_eh_descendente("2.01.04", "2.01.04"))       # a própria conta
        self.assertFalse(_eh_descendente("2.01.04", "2.01.04.03"))    # ancestral, não descendente

    def test_emprestimos_por_bloco_devolve_os_codigos(self):
        linhas = [("2.01", "Passivo Circulante", 1, 1),
                  ("2.01.04", "Empréstimos e Financiamentos", 10, 9),
                  ("2.01.04.01", "Empréstimos e Financiamentos", 10, 9),
                  ("2.02", "Passivo Não Circulante", 1, 1),
                  ("2.02.01", "Empréstimos e Financiamentos", 20, 19)]
        self.assertEqual(_emprestimos_por_bloco(linhas), ((10, 9), (20, 19), ["2.01.04", "2.02.01"]))
        sem_codigo = [(None, n, a, b) for _, n, a, b in linhas]
        self.assertEqual(_emprestimos_por_bloco(sem_codigo), ((10, 9), (20, 19), []))


class TestArrendamentoHierarquico(unittest.TestCase):

    def test_a_arrendamento_fora_da_divida(self):
        # Como WEGE3/ZAMP3: arrendamento em Outras Obrigações, somado à dívida.
        e, dest = _endividamento(_documento(_passivo(
            _emprestimos("2.01.04", 400, emprestimo=400) + _outras("2.01.05", ("2.01.05.02.07", "Arrendamentos", 80)),
            _emprestimos("2.02.01", 600, emprestimo=600) + _outras("2.02.02", ("2.02.02.02.05", "Arrendamentos", 120)))))
        self.assertEqual(e["divida_bruta"], formatar_moeda(1000))
        self.assertEqual(e["passivos_arrendamento"], formatar_moeda(200))
        self.assertEqual(e["divida_bruta_com_arrendamentos"], formatar_moeda(1200))
        self.assertEqual(e["divida_liquida_com_arrendamentos"], formatar_moeda(900))
        self.assertTrue(_tem_destaque_arrendamento(dest))

    def test_b_arrendamento_inteiramente_dentro_da_divida(self):
        # Como LWSA3: todo o grupo "Empréstimos e Financiamentos" é arrendamento,
        # lançado em 2.0x.0x.03.01 — circulante e não circulante.
        e, dest = _endividamento(_documento(_passivo(
            _emprestimos("2.01.04", 19361, arrendamento=19361),
            _emprestimos("2.02.01", 52554, arrendamento=52554))))
        self.assertEqual(e["divida_bruta"], formatar_moeda(71915))
        self.assertEqual(e["divida_liquida"], formatar_moeda(71915 - 300))
        for campo in AMPLIADOS:
            self.assertNotIn(campo, e)            # nunca "R$ 0": os arrendamentos existem, já na dívida
        self.assertFalse(_tem_destaque_arrendamento(dest))

    def test_c_divida_mista(self):
        # 70 de empréstimo + 30 de arrendamento dentro de 2.01.04.
        e, dest = _endividamento(_documento(_passivo(
            _emprestimos("2.01.04", 100, emprestimo=70, arrendamento=30),
            _emprestimos("2.02.01", 0))))
        self.assertEqual(e["divida_bruta"], formatar_moeda(100))
        for campo in AMPLIADOS:
            self.assertNotIn(campo, e)
        self.assertFalse(_tem_destaque_arrendamento(dest))

    def test_d_arrendamento_dentro_e_fora_da_divida(self):
        e, _ = _endividamento(_documento(_passivo(
            _emprestimos("2.01.04", 100, emprestimo=70, arrendamento=30)
            + _outras("2.01.05", ("2.01.05.02.08", "Passivos de arrendamento", 20)),
            _emprestimos("2.02.01", 0))))
        self.assertEqual(e["divida_bruta"], formatar_moeda(100))
        self.assertEqual(e["passivos_arrendamento"], formatar_moeda(20))
        self.assertEqual(e["divida_bruta_com_arrendamentos"], formatar_moeda(120))
        self.assertEqual(e["divida_liquida_com_arrendamentos"], formatar_moeda(120 - 300))

    def test_e_pai_e_filha_fora_da_divida(self):
        # "Passivos de arrendamento" (50) aberto em duas filhas (30 + 20) com o
        # mesmo radical: conta só o pai.
        e, _ = _endividamento(_documento(_passivo(
            _emprestimos("2.01.04", 400, emprestimo=400)
            + _outras("2.01.05", ("2.01.05.02.07", "Passivos de arrendamento", 50),
                      ("2.01.05.02.07.01", "Passivos de arrendamento - terceiros", 30),
                      ("2.01.05.02.07.02", "Passivos de arrendamento - partes relacionadas", 20)),
            _emprestimos("2.02.01", 0))))
        self.assertEqual(e["passivos_arrendamento"], formatar_moeda(50))
        self.assertEqual(e["divida_bruta_com_arrendamentos"], formatar_moeda(450))

    def test_f_financiamento_por_arrendamento_fora_da_divida(self):
        # Como C&A: a conta se chama "Financiamento por Arrendamento", mas está
        # em Outras Obrigações — é arrendamento adicional. A conta homônima
        # dentro da dívida (zerada) continua fora da soma pela hierarquia.
        e, _ = _endividamento(_documento(_passivo(
            _emprestimos("2.01.04", 400, emprestimo=400, filha=None)
            + _outras("2.01.05", ("2.01.05.02.06", "Financiamento por Arrendamento", 366)),
            _emprestimos("2.02.01", 600, emprestimo=600, filha=None)
            + _outras("2.02.02", ("2.02.02.02.06", "Financiamento por Arrendamento", 1410)))))
        self.assertEqual(e["divida_bruta"], formatar_moeda(1000))
        self.assertEqual(e["passivos_arrendamento"], formatar_moeda(1776))
        self.assertEqual(e["divida_bruta_com_arrendamentos"], formatar_moeda(2776))

    def test_f_financiamento_por_arrendamento_dentro_da_divida_nao_soma(self):
        # A mesma conta com valor, mas dentro de "Empréstimos e Financiamentos".
        e, _ = _endividamento(_documento(_passivo(
            _emprestimos("2.01.04", 100, emprestimo=70, arrendamento=30, filha=None),
            _emprestimos("2.02.01", 0))))
        self.assertEqual(e["divida_bruta"], formatar_moeda(100))
        self.assertNotIn("passivos_arrendamento", e)


class TestSemCdConta(unittest.TestCase):
    """Sem CD_CONTA a hierarquia não é recuperável: mantém a regra anterior.
    Estes testes documentam a limitação — os valores abaixo são os do legado."""

    def test_g_estrutura_lwsa3_sem_codigo_mantem_legado(self):
        e, dest = _endividamento(_documento(_passivo(
            _emprestimos("2.01.04", 19361, arrendamento=19361),
            _emprestimos("2.02.01", 52554, arrendamento=52554)), com_codigo=False))
        self.assertEqual(e["divida_bruta"], formatar_moeda(71915))
        self.assertEqual(e["passivos_arrendamento"], formatar_moeda(71915))          # recontagem legada
        self.assertEqual(e["divida_bruta_com_arrendamentos"], formatar_moeda(143830))
        self.assertTrue(_tem_destaque_arrendamento(dest))

    def test_g_financiamento_por_arrendamento_sem_codigo_mantem_exclusao_por_nome(self):
        e, _ = _endividamento(_documento(_passivo(
            _emprestimos("2.01.04", 400, emprestimo=400, filha=None)
            + _outras("2.01.05", ("2.01.05.02.06", "Financiamento por Arrendamento", 366)),
            _emprestimos("2.02.01", 600, emprestimo=600, filha=None)), com_codigo=False))
        self.assertNotIn("passivos_arrendamento", e)


class TestFixturesReais(unittest.TestCase):
    """ITR 2026-06-30, v1, com CD_CONTA (formato do pipeline)."""

    def _metricas(self, ticker):
        return calcular_metricas(extrair_documento(
            os.path.join(FIXTURES, f"{ticker}_ITR_2026-06-30_cd_conta.txt")))

    def test_wege3_arrendamento_fora_da_divida_preservado(self):
        e = self._metricas("WEGE3")["endividamento"]
        self.assertEqual(e["divida_bruta"], formatar_moeda(3163058 + 1903288))
        self.assertEqual(e["passivos_arrendamento"], formatar_moeda(183672 + 584717))
        self.assertEqual(e["divida_bruta_com_arrendamentos"],
                         formatar_moeda(3163058 + 1903288 + 183672 + 584717))
        self.assertEqual(e["divida_liquida"], "-R$ 3,73 bilhões")
        self.assertEqual(e["divida_liquida_com_arrendamentos"], "-R$ 2,97 bilhões")

    def test_zamp3_arrendamento_fora_da_divida_preservado(self):
        e = self._metricas("ZAMP3")["endividamento"]
        self.assertEqual(e["divida_bruta"], formatar_moeda(266761 + 1278313))
        self.assertEqual(e["passivos_arrendamento"], formatar_moeda(209956 + 674338))
        self.assertEqual(e["divida_bruta_com_arrendamentos"],
                         formatar_moeda(266761 + 1278313 + 209956 + 674338))
        self.assertEqual(e["divida_liquida"], "R$ 1,18 bilhões")

    def test_lwsa3_arrendamento_nao_e_recontado(self):
        m = self._metricas("LWSA3")
        e = m["endividamento"]
        self.assertEqual(e["divida_bruta"], formatar_moeda(19361 + 52554))        # R$ 71,92 milhões
        self.assertEqual(e["liquidez_total"], formatar_moeda(314495 + 90069))
        self.assertEqual(e["divida_liquida"], formatar_moeda(19361 + 52554 - 314495 - 90069))
        for campo in AMPLIADOS:
            self.assertNotIn(campo, e)
        self.assertFalse(_tem_destaque_arrendamento(m["outros_destaques"]))


if __name__ == "__main__":
    unittest.main()
