# tests/test_deteccao_banco.py
#
# Detecção de instituição financeira (eh_banco) em calcular_metricas(). A regra
# anterior também aceitava qualquer linha "Depósitos" do passivo, o que no ITR
# 2026-06-30 classificou como banco duas empresas do plano comercial (CSU
# Digital e Rodobens, "Depósitos" em 2.01.05.02.04, dentro de Outras
# Obrigações). Agora a identificação vem só da receita de intermediação
# financeira; "Depósitos" continua sendo lido para a métrica bancária.
#
# Execução (na raiz do projeto):
#   python -m unittest tests.test_deteccao_banco -v

import os
import sys
import tempfile
import types
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from modulos.extracao import extrair_documento  # noqa: E402
from modulos.metricas import calcular_metricas, formatar_moeda  # noqa: E402

FIXTURES  = os.path.join(RAIZ, "tests", "fixtures")
VALIDACAO = os.path.join(RAIZ, "avaliacao", "validacao_manual")
SEP = "=" * 50

REGRA_NOVA   = 'eh_banco = "Intermediação Financeira" in desc_receita'
REGRA_ANTIGA = 'eh_banco = ("Intermediação Financeira" in desc_receita) or bool(dep_a)'


def _regra_antiga():
    """Cópia do módulo atual com a regra anterior, só para comparação."""
    with open(os.path.join(RAIZ, "modulos", "metricas.py"), encoding="utf-8") as f:
        fonte = f.read()
    assert fonte.count(REGRA_NOVA) == 1
    mod = types.ModuleType("metricas_regra_antiga")
    exec(compile(fonte.replace(REGRA_NOVA, REGRA_ANTIGA), "metricas_regra_antiga", "exec"),
         mod.__dict__)
    return mod


def _documento(secoes, com_codigo=True):
    def linha(cod, nome, a, b):
        return (f"[{cod}] " if com_codigo else "") + f"{nome:<55} {float(a):>20.10f}  (anterior: {float(b):.10f})"
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


def _comercial_com_depositos(com_codigo=True):
    """Plano comercial com "Depósitos" profundo, como CSU Digital e Rodobens."""
    return _documento([
        ("Demonstração de Resultado (Consolidado)", [
            ("3.01", "Receita de Venda de Bens e/ou Serviços", 1000, 900),
            ("3.02", "Custo dos Bens e/ou Serviços Vendidos", -600, -550),
            ("3.03", "Resultado Bruto", 400, 350),
            ("3.05", "Resultado Antes do Resultado Financeiro e dos Tributos", 200, 180),
            ("3.11", "Lucro/Prejuízo Consolidado do Período", 100, 90)]),
        ("Balanço Patrimonial — Ativo (Consolidado)", [
            ("1", "Ativo Total", 3000, 2800),
            ("1.01", "Ativo Circulante", 1500, 1400),
            ("1.01.01", "Caixa e Equivalentes de Caixa", 300, 250)]),
        ("Balanço Patrimonial — Passivo (Consolidado)", [
            ("2", "Passivo Total", 3000, 2800),
            ("2.01", "Passivo Circulante", 1000, 900),
            ("2.01.04", "Empréstimos e Financiamentos", 400, 350),
            ("2.01.05", "Outras Obrigações", 120, 100),
            ("2.01.05.02", "Outros", 120, 100),
            ("2.01.05.02.04", "Depósitos", 50, 40),
            ("2.02", "Passivo Não Circulante", 900, 850),
            ("2.02.01", "Empréstimos e Financiamentos", 600, 550),
            ("2.03", "Patrimônio Líquido Consolidado", 1100, 1050)]),
        ("Demonstração de Fluxo de Caixa (Consolidado)", [
            ("6.01", "Caixa Líquido Atividades Operacionais", 150, 140),
            ("6.01.01", "Caixa Gerado nas Operações", 160, 150),
            ("6.01.01.02", "Depreciação e amortização", 30, 25),
            ("6.02", "Caixa Líquido Atividades de Investimento", -50, -40)]),
    ], com_codigo)


def _banco(receita, depositos=(1000, 900), com_codigo=True):
    passivo = [("2", "Passivo Total", 3000, 2800),
               ("2.02", "Passivos Financeiros ao Custo Amortizado", 2000, 1800)]
    if depositos is not None:
        passivo.append(("2.02.01", "Depósitos", *depositos))
    passivo += [("2.02.02", "Captações no Mercado Aberto", 800, 700),
                ("2.07", "Patrimônio Líquido Consolidado", 200, 190)]
    return _documento([
        ("Demonstração de Resultado (Consolidado)", [
            ("3.01", receita, 500, 450),
            ("3.11", "Lucro ou Prejuízo Líquido Consolidado do Período", 60, 70)]),
        ("Balanço Patrimonial — Passivo (Consolidado)", passivo),
    ], com_codigo)


class TestComercialComDepositosProfundos(unittest.TestCase):

    def test_nao_e_banco(self):
        for com_codigo in (True, False):
            with self.subTest(com_codigo=com_codigo):
                m = calcular_metricas(_comercial_com_depositos(com_codigo))
                e = m["endividamento"]
                self.assertEqual(m["ebitda"]["valor_atual"], formatar_moeda(230))
                self.assertEqual(e["divida_bruta"], formatar_moeda(1000))
                self.assertEqual(e["divida_liquida"], formatar_moeda(700))
                self.assertNotIn("depositos", e)
                self.assertFalse(any(d.startswith("Depósitos") for d in m["outros_destaques"]))

    def test_regra_antiga_classificava_como_banco(self):
        # Garante que o documento sintético reproduz o defeito corrigido.
        antiga = _regra_antiga()
        for com_codigo in (True, False):
            with self.subTest(com_codigo=com_codigo):
                m = antiga.calcular_metricas(_comercial_com_depositos(com_codigo))
                self.assertEqual(m["ebitda"]["valor_atual"], "nao_aplicavel")
                self.assertEqual(m["endividamento"]["divida_liquida"], "nao_aplicavel")


class TestBancos(unittest.TestCase):

    def _assert_banco(self, m):
        self.assertEqual(m["ebitda"]["valor_atual"], "nao_aplicavel")
        self.assertEqual(m["endividamento"]["divida_bruta"], "nao_aplicavel")
        self.assertEqual(m["endividamento"]["divida_liquida"], "nao_aplicavel")
        self.assertEqual(m["endividamento"]["captacao_mercado_aberto"], formatar_moeda(800))

    def test_receitas_de_e_da_intermediacao(self):
        for receita in ("Receitas de Intermediação Financeira",    # BB, Bradesco...
                        "Receitas da Intermediação Financeira"):   # Itaú, BTG...
            for com_codigo in (True, False):
                with self.subTest(receita=receita, com_codigo=com_codigo):
                    m = calcular_metricas(_banco(receita, com_codigo=com_codigo))
                    self._assert_banco(m)
                    self.assertEqual(m["endividamento"]["depositos"], formatar_moeda(1000))
                    self.assertEqual(m["receita_principal"]["valor_atual"], formatar_moeda(500))

    def test_banco_sem_conta_depositos(self):
        # Caso dos bancos só com base individual, cujo documento não traz passivo.
        for com_codigo in (True, False):
            with self.subTest(com_codigo=com_codigo):
                m = calcular_metricas(_banco("Receitas de Intermediação Financeira",
                                             depositos=None, com_codigo=com_codigo))
                self._assert_banco(m)
                self.assertEqual(m["endividamento"]["depositos"], "nao_disponivel")

    def test_banco_com_depositos_zero(self):
        # Caso Santander: a conta existe, zerada.
        for com_codigo in (True, False):
            with self.subTest(com_codigo=com_codigo):
                m = calcular_metricas(_banco("Receitas da Intermediação Financeira",
                                             depositos=(0, 0), com_codigo=com_codigo))
                self._assert_banco(m)
                self.assertEqual(m["endividamento"]["depositos"], formatar_moeda(0))


class TestRegressaoFixtures(unittest.TestCase):
    """BBAS3, WEGE3 e ZAMP3 (ITR 2026-06-30 v1): saída idêntica à da regra
    anterior, no documento com CD_CONTA e no congelado sem código."""

    @classmethod
    def setUpClass(cls):
        cls.antiga = _regra_antiga()

    def _documentos(self, ticker):
        return (os.path.join(FIXTURES, f"{ticker}_ITR_2026-06-30_cd_conta.txt"),
                os.path.join(VALIDACAO, f"{ticker}_ITR_2026-06-30_v1", f"{ticker}_ITR_2026-06-30.txt"))

    def test_saida_identica(self):
        for ticker, banco in (("BBAS3", True), ("WEGE3", False), ("ZAMP3", False)):
            for caminho in self._documentos(ticker):
                with self.subTest(documento=os.path.basename(caminho)):
                    secoes = extrair_documento(caminho)
                    novo = calcular_metricas(secoes)
                    self.assertEqual(novo, self.antiga.calcular_metricas(secoes))
                    self.assertEqual(novo["ebitda"]["valor_atual"] == "nao_aplicavel", banco)
                    self.assertEqual("depositos" in novo["endividamento"], banco)

    def test_bbas3_continua_com_depositos_e_captacao(self):
        e = calcular_metricas(extrair_documento(self._documentos("BBAS3")[0]))["endividamento"]
        self.assertEqual(e["depositos"], "R$ 954,02 bilhões")
        self.assertEqual(e["captacao_mercado_aberto"], "R$ 845,41 bilhões")


if __name__ == "__main__":
    unittest.main()
