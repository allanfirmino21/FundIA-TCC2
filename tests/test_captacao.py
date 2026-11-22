# tests/test_captacao.py
#
# Captação no mercado aberto (métrica bancária). Achado 3 da validação manual
# do TCC 2: a conta existe no documento do BBAS3 ("Captações no Mercado
# Aberto", 2.02.02), mas calcular_metricas() procurava "Captação no Mercado
# Aberto" e a métrica ficava nao_disponivel. Das 10 companhias com essa conta
# no ITR 2026-06-30, só o Itaú usa o singular.
#
# Execução (na raiz do projeto):
#   python -m unittest tests.test_captacao -v

import json
import os
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from modulos import metricas  # noqa: E402
from modulos.extracao import extrair_documento  # noqa: E402
from modulos.metricas import calcular_metricas, formatar_moeda  # noqa: E402

FIXTURES  = os.path.join(RAIZ, "tests", "fixtures")
VALIDACAO = os.path.join(RAIZ, "avaliacao", "validacao_manual", "BBAS3_ITR_2026-06-30_v1")


def _metricas_banco(nome_captacao, com_codigo=True, filha=None):
    def linha(cod, nome, a, b):
        return (f"[{cod}] " if com_codigo else "") + f"{nome:<55} {float(a):>20.10f}  (anterior: {float(b):.10f})"
    passivo = [("2", "Passivo Total", 3000, 2800),
               ("2.02", "Passivos Financeiros ao Custo Amortizado", 2000, 1800),
               ("2.02.01", "Depósitos", 1000, 900),
               ("2.02.02", nome_captacao, 800, 700)]
    if filha:
        passivo.append(("2.02.02.01", filha, 300, 250))
    passivo.append(("2.07", "Patrimônio Líquido Consolidado", 200, 190))
    dre = [("3.01", "Receitas de Intermediação Financeira", 500, 450),
           ("3.11", "Lucro ou Prejuízo Líquido Consolidado do Período", 60, 70)]
    sep = "=" * 50
    texto = "\n".join(
        ["DOCUMENTO: ITR — 2026-06-30", "EMPRESA CVM: 9999", "VERSAO: 1", "FORMATO: CD_CONTA", "",
         f"\n{sep}", "Demonstração de Resultado (Consolidado)", sep] + [linha(*l) for l in dre] +
        [f"\n{sep}", "Balanço Patrimonial — Passivo (Consolidado)", sep] + [linha(*l) for l in passivo])
    with tempfile.TemporaryDirectory() as tmp:
        caminho = os.path.join(tmp, "doc.txt")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(texto)
        return calcular_metricas(extrair_documento(caminho))["endividamento"]


class TestNomenclatura(unittest.TestCase):

    def test_tres_grafias_da_cvm(self):
        for nome in ("Captações no Mercado Aberto",   # conta fixa 2.02.02 (BB, Bradesco...)
                     "Captações no mercado aberto",   # BTG
                     "Captação no Mercado Aberto"):   # Itaú
            with self.subTest(nome=nome):
                self.assertTrue(metricas._RE_CAPTACAO_MERCADO_ABERTO.match(nome))

    def test_nao_casa_com_outras_contas(self):
        for nome in ("Captação de passivos de longo prazo",
                     "Operações de Captação no Mercado",
                     "Outras Captações",
                     "Captações no Mercado Aberto e Interfinanceiro",
                     "Depósitos"):
            with self.subTest(nome=nome):
                self.assertIsNone(metricas._RE_CAPTACAO_MERCADO_ABERTO.match(nome))

    def test_conta_pai_antes_da_subconta_homonima(self):
        linhas = [("Captações no Mercado Aberto", 800.0, 700.0),
                  ("Captação no Mercado Aberto", 300.0, 250.0)]
        self.assertEqual(metricas._primeira_por_padrao(linhas, metricas._RE_CAPTACAO_MERCADO_ABERTO),
                         (800.0, 700.0))


class TestMetricaBancaria(unittest.TestCase):

    def test_cada_grafia_produz_a_metrica(self):
        for nome in ("Captações no Mercado Aberto", "Captações no mercado aberto",
                     "Captação no Mercado Aberto"):
            with self.subTest(nome=nome):
                e = _metricas_banco(nome)
                self.assertEqual(e["captacao_mercado_aberto"], formatar_moeda(800))
                self.assertEqual(e["depositos"], formatar_moeda(1000))

    def test_subconta_homonima_nao_substitui_o_total(self):
        e = _metricas_banco("Captações no Mercado Aberto", filha="Captação no Mercado Aberto")
        self.assertEqual(e["captacao_mercado_aberto"], formatar_moeda(800))

    def test_documento_sem_codigo(self):
        e = _metricas_banco("Captações no Mercado Aberto", com_codigo=False)
        self.assertEqual(e["captacao_mercado_aberto"], formatar_moeda(800))


class TestBBAS3(unittest.TestCase):
    """ITR 2026-06-30 v1: 845.408.764 (anterior 727.039.247), em R$ mil."""

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(VALIDACAO, "resultado_analisar.json"), encoding="utf-8") as f:
            cls.antes = json.load(f)["analise"]["dados_extraidos"]
        cls.novo = json.loads(json.dumps(calcular_metricas(extrair_documento(
            os.path.join(FIXTURES, "BBAS3_ITR_2026-06-30_cd_conta.txt"))), ensure_ascii=False))
        cls.congelado = calcular_metricas(extrair_documento(
            os.path.join(VALIDACAO, "BBAS3_ITR_2026-06-30.txt")))

    def test_captacao_encontrada(self):
        e = self.novo["endividamento"]
        self.assertEqual(self.antes["endividamento"]["captacao_mercado_aberto"], "nao_disponivel")
        self.assertEqual(e["captacao_mercado_aberto"], formatar_moeda(845408764))
        self.assertEqual(e["captacao_mercado_aberto"], "R$ 845,41 bilhões")
        self.assertIn("Captação no mercado aberto: R$ 845,41 bilhões (variação +16,3%)",
                      self.novo["outros_destaques"])

    def test_documento_congelado_sem_codigo_tambem(self):
        self.assertEqual(self.congelado["endividamento"]["captacao_mercado_aberto"],
                         "R$ 845,41 bilhões")

    def test_depositos_e_demais_metricas_bancarias_iguais(self):
        e_antes, e_novo = self.antes["endividamento"], self.novo["endividamento"]
        for campo in set(e_antes) | set(e_novo):
            if campo != "captacao_mercado_aberto":
                self.assertEqual(e_novo.get(campo), e_antes.get(campo), campo)
        self.assertEqual(e_novo["depositos"], "R$ 954,02 bilhões")
        self.assertEqual(e_novo["divida_liquida"], "nao_aplicavel")
        for chave in ("receita_principal", "lucro_liquido", "ebitda", "periodos", "base_dados",
                      "dados_ausentes", "advertencias"):
            self.assertEqual(self.novo[chave], self.antes[chave], chave)


if __name__ == "__main__":
    unittest.main()
