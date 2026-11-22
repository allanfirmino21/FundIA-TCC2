# tests/test_auditoria_conceito.py
#
# Verificação conceito + valor da auditoria (versão 2.0, só valores
# monetários). Achado da validação manual do TCC 2: a narrativa pós-Prompt 2
# da ZAMP3 atribuiu R$ 289,21 milhões (EBITDA) ao "Resultado Antes do
# Resultado Financeiro e dos Tributos" (EBIT, R$ 26,76 milhões), e a versão
# 1.0 do auditor deu CONFERE porque o valor existe na fonte.
#
# Execução (na raiz do projeto):
#   python -m unittest tests.test_auditoria_conceito -v

import json
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from modulos import auditoria as A  # noqa: E402
from modulos.auditoria import auditar_narrativa  # noqa: E402
from modulos.extracao import extrair_documento  # noqa: E402

VALIDACAO = os.path.join(RAIZ, "avaliacao", "validacao_manual")
PASTAS = [f"{t}_ITR_2026-06-30_v1{s}" for t in ("WEGE3", "BBAS3", "ZAMP3")
          for s in ("", "_pos_prompt2")]
EBIT = "O Resultado Antes do Resultado Financeiro e dos Tributos foi de {}."
EBITDA = "O EBITDA foi de {}."


def _artefatos(pasta):
    d = os.path.join(VALIDACAO, pasta)
    with open(os.path.join(d, "resultado_analisar.json"), encoding="utf-8") as f:
        analise = json.load(f)["analise"]
    with open(os.path.join(d, "auditoria.json"), encoding="utf-8") as f:
        congelada = json.load(f)
    ticker = pasta.split("_")[0]
    secoes = extrair_documento(os.path.join(d, f"{ticker}_ITR_2026-06-30.txt"))
    return analise, secoes, congelada


def _json(obj):
    return json.loads(json.dumps(obj, ensure_ascii=False))


class _Base(unittest.TestCase):
    PASTA = None

    @classmethod
    def setUpClass(cls):
        cls.analise, cls.secoes, cls.congelada = _artefatos(cls.PASTA)

    def moeda(self, frase, verificar_conceito=True):
        res = auditar_narrativa({"TESTE": frase}, self.secoes, self.analise["dados_extraidos"],
                                verificar_conceito=verificar_conceito)
        moedas = [v for v in res["verificacoes"] if v["tipo"] == "moeda"]
        self.assertEqual(len(moedas), 1, frase)
        return moedas[0]

    def assertConfere(self, frase, conceito):
        v = self.moeda(frase)
        self.assertEqual(v["veredito"], "CONFERE", v)
        self.assertEqual(v["conceito_reivindicado"], conceito)
        self.assertEqual(v["conceito_do_fato"], conceito)
        return v

    def assertDivergeConceito(self, frase, reivindicado, do_fato):
        v = self.moeda(frase)
        self.assertEqual(v["veredito"], "DIVERGENTE", v)
        self.assertEqual(v["conceito_reivindicado"], reivindicado)
        self.assertEqual(v["conceito_do_fato"], do_fato)
        self.assertIn(f'atribui o valor a "{reivindicado}"', v["motivo"])
        self.assertIn(f'corresponde a "{do_fato}"', v["motivo"])
        # a versão 1.0 aceitava o mesmo número
        self.assertEqual(self.moeda(frase, verificar_conceito=False)["veredito"], "CONFERE")
        return v


# ── Erro plantado da ZAMP3 ───────────────────────────────────────────────────

class TestErroPlantadoZAMP3(_Base):
    PASTA = "ZAMP3_ITR_2026-06-30_v1_pos_prompt2"

    def test_ebit_com_valor_do_ebitda_diverge(self):
        v = self.assertDivergeConceito(EBIT.format("R$ 289,21 milhões"), "ebit", "ebitda")
        self.assertIn("R$ 26,76 milhões", v["motivo"])      # valor correto do EBIT

    def test_ebit_com_valor_do_ebit_confere(self):
        self.assertConfere(EBIT.format("R$ 26,76 milhões"), "ebit")

    def test_ebitda_com_valor_do_ebitda_confere(self):
        self.assertConfere(EBITDA.format("R$ 289,21 milhões"), "ebitda")

    def test_ebitda_com_valor_do_ebit_diverge(self):
        self.assertDivergeConceito(EBITDA.format("R$ 26,76 milhões"), "ebitda", "ebit")

    def test_frase_real_da_narrativa(self):
        # O parêntese explicativo cita "EBITDA", mas o sujeito é o EBIT.
        frase = ("O Resultado Antes do Resultado Financeiro e dos Tributos (EBITDA aproximado, "
                 "que é o lucro antes de descontar juros, impostos e depreciação e amortização) "
                 "foi de R$ 289,21 milhões, com uma margem de 10,65% sobre a receita.")
        self.assertIn(frase, self.analise["secoes"]["O QUE FOI POSITIVO"])
        self.assertDivergeConceito(frase, "ebit", "ebitda")

    def test_parentese_explicativo_nao_muda_o_sujeito(self):
        self.assertConfere("O EBITDA (lucro antes de juros, impostos, depreciação e amortização) "
                           "foi de R$ 289,21 milhões.", "ebitda")

    def test_reauditoria_da_narrativa_muda_so_esse_numero(self):
        novo = auditar_narrativa(self.analise["secoes"], self.secoes, self.analise["dados_extraidos"])
        mudancas = [(a["trecho"], a["veredito"], b["veredito"])
                    for a, b in zip(self.congelada["verificacoes"], novo["verificacoes"])
                    if a["veredito"] != b["veredito"]]
        self.assertEqual(mudancas, [("R$ 289,21 milhões", "CONFERE", "DIVERGENTE")])
        r = novo["resumo"]
        self.assertEqual((r["conferem"], r["divergentes"], r["total_numeros"]), (42, 1, 43))
        self.assertEqual(r["verificacao_conceitual"]["divergencias_de_conceito"], 1)


# ── Outras trocas da mesma classe (WEGE3, métricas pós-correção) ─────────────

class TestTrocasWEGE3(_Base):
    PASTA = "WEGE3_ITR_2026-06-30_v1_pos_prompt2"

    def test_divida_bruta_x_com_arrendamentos(self):
        self.assertConfere("A dívida bruta é de R$ 5,07 bilhões.", "divida_bruta")
        self.assertConfere("A dívida bruta com arrendamentos é de R$ 5,83 bilhões.",
                           "divida_bruta_com_arrendamentos")
        self.assertDivergeConceito("A dívida bruta é de R$ 5,83 bilhões.",
                                   "divida_bruta", "divida_bruta_com_arrendamentos")
        self.assertDivergeConceito("A dívida bruta com arrendamentos é de R$ 5,07 bilhões.",
                                   "divida_bruta_com_arrendamentos", "divida_bruta")

    def test_caixa_x_liquidez_total(self):
        self.assertConfere("O caixa e equivalentes somava R$ 7,75 bilhões.", "caixa")
        self.assertConfere("A liquidez total somava R$ 8,80 bilhões.", "liquidez_total")
        self.assertDivergeConceito("O caixa e equivalentes somava R$ 8,80 bilhões.",
                                   "caixa", "liquidez_total")
        self.assertDivergeConceito("A liquidez total somava R$ 7,75 bilhões.",
                                   "liquidez_total", "caixa")

    def test_divida_liquida_x_com_arrendamentos(self):
        self.assertConfere("A dívida líquida é negativa em R$ 3,73 bilhões.", "divida_liquida")
        self.assertConfere("A dívida líquida com arrendamentos é negativa em R$ 2,97 bilhões.",
                           "divida_liquida_com_arrendamentos")
        self.assertDivergeConceito("A dívida líquida é negativa em R$ 2,97 bilhões.",
                                   "divida_liquida", "divida_liquida_com_arrendamentos")
        self.assertDivergeConceito("A dívida líquida com arrendamentos é negativa em R$ 3,73 bilhões.",
                                   "divida_liquida_com_arrendamentos", "divida_liquida")

    def test_rotulo_depois_do_valor(self):
        self.assertConfere("A empresa tinha R$ 8,80 bilhões em liquidez total.", "liquidez_total")


# ── Limitações conhecidas (fixam o comportamento atual; não corrigidas) ──────

class TestLimitacoesDocumentadas(_Base):
    PASTA = "WEGE3_ITR_2026-06-30_v1_pos_prompt2"

    def test_periodo_valor_anterior_citado_como_atual_ainda_confere(self):
        # R$ 4,43 bilhões é o EBITDA do 1º semestre de 2025 (valor_anterior);
        # o texto o apresenta como de 2026. Conceito certo, período errado.
        dados = self.analise["dados_extraidos"]
        self.assertEqual(dados["ebitda"]["valor_anterior"], "R$ 4,43 bilhões")
        v = self.moeda("No 1º semestre de 2026, o EBITDA foi de R$ 4,43 bilhões.")
        self.assertEqual(v["veredito"], "CONFERE")
        self.assertIn("valor_anterior", v["origem_fato"])

    def test_base_valor_individual_citado_como_consolidado_ainda_confere(self):
        # Achado 2 da WEGE3: o resultado financeiro consolidado é R$ 65,82
        # milhões; R$ 10,55 milhões é o da demonstração individual.
        resumo = self.analise["dados_extraidos"]["demonstracoes_resumidas"]["resultado"]
        rf = next(i for i in resumo if i["conta"] == "Resultado Financeiro")
        self.assertEqual(rf["valor_atual"], "R$ 65,82 milhões")
        v = self.moeda("O resultado financeiro foi de R$ 10,55 milhões.")
        self.assertEqual(v["veredito"], "CONFERE")
        self.assertEqual(v["conceito_reivindicado"], "resultado_financeiro")
        self.assertIn("Resultado Financeiro", v["origem_fato"])


# ── Extração do conceito e mapeamento dos fatos ──────────────────────────────

class TestLexico(unittest.TestCase):

    def _reivindicado(self, frase, trecho):
        i = frase.index(trecho)
        return A._conceito_reivindicado(frase, i, i + len(trecho))

    def test_correspondencia_mais_longa(self):
        self.assertEqual(A._achar_conceitos("Resultado Antes do Resultado Financeiro e dos Tributos"),
                         [(0, "ebit")])
        self.assertEqual(A._achar_conceitos("dívida líquida com arrendamentos"),
                         [(0, "divida_liquida_com_arrendamentos")])
        self.assertEqual(A._achar_conceitos("Caixa Líquido Atividades Operacionais"),
                         [(0, "fluxo_operacional")])

    def test_mais_proximo_antes_do_valor_na_mesma_frase(self):
        f = "A receita caiu, mas o lucro líquido somou R$ 3,23 bilhões."
        self.assertEqual(self._reivindicado(f, "R$ 3,23 bilhões"), "lucro_liquido")

    def test_nao_atravessa_frase(self):
        f = "O EBITDA caiu 2,9%. Chegou a R$ 289,21 milhões."
        self.assertIsNone(self._reivindicado(f, "R$ 289,21 milhões"))

    def test_parentese_fechado_e_ignorado(self):
        f = "O EBIT (diferente do EBITDA) foi de R$ 26,76 milhões."
        self.assertEqual(self._reivindicado(f, "R$ 26,76 milhões"), "ebit")

    def test_valor_em_parentese_aberto_usa_so_o_parentese(self):
        f = "A dívida líquida é negativa em R$ 3,73 bilhões (ou -R$ 2,97 bilhões se incluirmos..."
        self.assertIsNone(self._reivindicado(f, "-R$ 2,97 bilhões"))
        f = "O resultado financeiro (receitas financeiras de R$ 40,32 milhões menos..."
        self.assertEqual(self._reivindicado(f, "R$ 40,32 milhões"), "receitas_financeiras")

    def test_rotulo_depois_do_valor(self):
        f = "A empresa tinha R$ 13,23 bilhões em liquidez total."
        self.assertEqual(self._reivindicado(f, "R$ 13,23 bilhões"), "liquidez_total")

    def test_sem_rotulo(self):
        f = "O montante registrado foi de R$ 1,00 bilhão."
        self.assertIsNone(self._reivindicado(f, "R$ 1,00 bilhão"))

    def test_nome_de_conta_com_e_sem_codigo(self):
        for nome, conceito in (("Resultado Antes do Resultado Financeiro e dos Tributos", "ebit"),
                               ("Prejuízo antes do imposto de renda e contribuição social",
                                "resultado_antes_tributos"),
                               ("Lucro/Prejuízo Consolidado do Período", "lucro_liquido"),
                               ("Captações no Mercado Aberto", "captacao_mercado_aberto"),
                               ("Custo dos Bens e/ou Serviços Vendidos", "custo_vendas")):
            with self.subTest(nome=nome):
                self.assertEqual(A._conceito_do_nome(nome), conceito)
                self.assertEqual(A._conceito_do_nome(f"[3.05] {nome}"), conceito)

    def test_fatos_das_metricas(self):
        analise, _, _ = _artefatos("ZAMP3_ITR_2026-06-30_v1_pos_prompt2")
        moedas, *_ = A._fatos_dos_dados_com_conceito(analise["dados_extraidos"])
        conceito = {(o, round(v)): c for v, o, c in moedas}
        self.assertEqual(conceito[("métrica calculada: ebitda.valor_atual", 289210)], "ebitda")
        self.assertEqual(conceito[("métrica calculada: outros_destaques", 26760)], "ebit")
        self.assertEqual(conceito[("métrica calculada: endividamento.divida_liquida_com_arrendamentos",
                                   2060000)], "divida_liquida_com_arrendamentos")
        self.assertEqual(conceito[("métrica calculada: demonstracoes_resumidas.resultado.valor_atual",
                                   -169280)], "resultado_financeiro")

    def test_fatos_do_documento_sem_mudanca_na_interface_antiga(self):
        _, secoes, _ = _artefatos("ZAMP3_ITR_2026-06-30_v1_pos_prompt2")
        antigos, pcts = A._fatos_do_documento(secoes)
        novos, pcts2 = A._fatos_do_documento_com_conceito(secoes)
        self.assertEqual(antigos, [(v, o) for v, o, _ in novos])
        self.assertEqual(pcts, pcts2)


# ── Comparabilidade com a versão 1.0 e resumo ────────────────────────────────

class TestComparabilidade(unittest.TestCase):

    def test_versao_1_reproduz_as_auditorias_congeladas(self):
        for pasta in PASTAS:
            with self.subTest(pasta=pasta):
                analise, secoes, congelada = _artefatos(pasta)
                v1 = auditar_narrativa(analise["secoes"], secoes, analise["dados_extraidos"],
                                       verificar_conceito=False)
                self.assertEqual(_json(v1["verificacoes"]), congelada["verificacoes"])
                resumo = dict(v1["resumo"])
                self.assertEqual(resumo.pop("auditor"),
                                 {"versao": "1.0", "verificar_conceito": False,
                                  "metodologia": A.AUDITOR_METODOLOGIA[False]})
                self.assertEqual(resumo, congelada["resumo"])

    def test_sem_conceito_verificado_o_veredito_e_o_da_versao_1(self):
        for pasta in PASTAS:
            analise, secoes, _ = _artefatos(pasta)
            args = (analise["secoes"], secoes, analise["dados_extraidos"])
            v1, v2 = auditar_narrativa(*args, verificar_conceito=False), auditar_narrativa(*args)
            self.assertEqual(len(v1["verificacoes"]), len(v2["verificacoes"]))
            for a, b in zip(v1["verificacoes"], v2["verificacoes"]):
                if b["tipo"] != "moeda" or b["verificacao_conceitual"] != "verificado":
                    with self.subTest(pasta=pasta, trecho=b["trecho"]):
                        self.assertEqual({k: b[k] for k in a}, a)

    def test_so_o_erro_da_zamp3_muda_nas_seis_narrativas(self):
        mudancas = []
        for pasta in PASTAS:
            analise, secoes, congelada = _artefatos(pasta)
            v2 = auditar_narrativa(analise["secoes"], secoes, analise["dados_extraidos"])
            mudancas += [(pasta, b["trecho"]) for a, b in zip(congelada["verificacoes"], v2["verificacoes"])
                         if a["veredito"] != b["veredito"]]
        self.assertEqual(mudancas, [("ZAMP3_ITR_2026-06-30_v1_pos_prompt2", "R$ 289,21 milhões")])

    def test_resumo_registra_versao_e_cobertura(self):
        analise, secoes, _ = _artefatos("ZAMP3_ITR_2026-06-30_v1_pos_prompt2")
        r = auditar_narrativa(analise["secoes"], secoes, analise["dados_extraidos"])["resumo"]
        self.assertEqual(r["auditor"]["versao"], "2.0")
        self.assertTrue(r["auditor"]["verificar_conceito"])
        c = r["verificacao_conceitual"]
        self.assertEqual(c["moedas"], c["verificadas"] + c["conceito_nao_identificado"]
                         + c["conceito_sem_fato_na_fonte"])
        self.assertEqual(c["cobertura_pct"], round(c["verificadas"] / c["moedas"] * 100, 1))
        self.assertIn("período", c["nao_verifica"])
        self.assertIn("base contábil", c["nao_verifica"])
        r1 = auditar_narrativa(analise["secoes"], secoes, analise["dados_extraidos"],
                               verificar_conceito=False)["resumo"]
        self.assertNotIn("verificacao_conceitual", r1)

    def test_conceito_sem_fato_na_fonte_mantem_versao_1(self):
        # Banco: EBITDA é nao_aplicavel, não há fato de EBITDA na fonte.
        analise, secoes, _ = _artefatos("BBAS3_ITR_2026-06-30_v1_pos_prompt2")
        frase = {"T": "O EBITDA foi de R$ 6,36 bilhões."}
        v2 = auditar_narrativa(frase, secoes, analise["dados_extraidos"])["verificacoes"][0]
        v1 = auditar_narrativa(frase, secoes, analise["dados_extraidos"],
                               verificar_conceito=False)["verificacoes"][0]
        self.assertEqual(v2["verificacao_conceitual"], "conceito_sem_fato_na_fonte")
        self.assertEqual(v2["veredito"], v1["veredito"])


if __name__ == "__main__":
    unittest.main()
