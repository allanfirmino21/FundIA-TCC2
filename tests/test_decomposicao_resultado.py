# tests/test_decomposicao_resultado.py
#
# decomposicao_resultado em calcular_metricas(): a variação do resultado final
# da DRE decomposta em contribuições absolutas (valor atual − valor anterior),
# a partir do subtotal-âncora do plano de contas da CVM. Diagnóstico de
# causalidade da validação manual do TCC 2: a narrativa atribuía a variação a
# linhas internas que se compensam (ZAMP3) e lia ao contrário o efeito de um
# IR/CS positivo (BBAS3).
#
# Também cobre a correção de lucro_liquido nos bancos só-individuais: a conta
# final "Lucro ou Prejuízo Líquido do Período" vem depois das participações
# estatutárias; antes, a métrica parava em "Operações Continuadas".
#
# Execução (na raiz do projeto):
#   python -m unittest tests.test_decomposicao_resultado -v

import json
import os
import re
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from modulos import metricas as M  # noqa: E402
from modulos.extracao import extrair_documento  # noqa: E402
from modulos.metricas import calcular_metricas, formatar_moeda  # noqa: E402

FIXTURES  = os.path.join(RAIZ, "tests", "fixtures")
VALIDACAO = os.path.join(RAIZ, "avaliacao", "validacao_manual")
SEP = "=" * 50
EFEITOS = {f"{v} o {alvo}" for v in ("aumentou", "reduziu", "não alterou")
           for alvo in ("resultado", "subtotal")}
JULGAMENTO = re.compile(r"\b(bom|boa|ruim|positiv\w*|negativ\w*|melhor\w*|pior\w*|"
                        r"favor[aá]vel|desfavor[aá]vel)\b", re.IGNORECASE)


def _secoes(dre, com_codigo=True, titulo="Demonstração de Resultado (Consolidado)"):
    def linha(cod, nome, a, b):
        return (f"[{cod}] " if com_codigo else "") + f"{nome:<55} {float(a):>20.10f}  (anterior: {float(b):.10f})"
    texto = ["DOCUMENTO: ITR — 2026-06-30", "EMPRESA CVM: 9999", "VERSAO: 1"]
    texto += (["FORMATO: CD_CONTA"] if com_codigo else []) + ["", f"\n{SEP}", titulo, SEP]
    texto += [linha(*l) for l in dre]
    with tempfile.TemporaryDirectory() as tmp:
        caminho = os.path.join(tmp, "doc.txt")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write("\n".join(texto))
        return extrair_documento(caminho)


def _dec(dre, **kw):
    m = calcular_metricas(_secoes(dre, **kw))
    return m, json.loads(json.dumps(m["decomposicao_resultado"], ensure_ascii=False))


def _bruto(secoes, base="Consolidado"):
    """Decomposição em R$ mil, com o mesmo lucro que calcular_metricas usa."""
    dre = M._achar_secao(secoes, "Demonstração de Resultado", base)
    cadeia = M._cadeia_dre(M._parsear_linhas_com_codigo(dre.conteudo))
    final = [c for c in cadeia if c[3]][-1]
    return M._decompor_resultado(dre, final[1], final[2])


# Estruturas reais dos planos da CVM (valores em R$ mil)
COMERCIAL = [  # ZAMP3, ITR 2026-06-30
    ("3.01", "Receita de Venda de Bens e/ou Serviços", 2716534, 2442664),
    ("3.02", "Custo dos Bens e/ou Serviços Vendidos", -868253, -872713),
    ("3.03", "Resultado Bruto", 1848281, 1569951),
    ("3.04", "Despesas/Receitas Operacionais", -1821523, -1547418),
    ("3.05", "Resultado Antes do Resultado Financeiro e dos Tributos", 26758, 22533),
    ("3.06", "Resultado Financeiro", -169280, -144604),
    ("3.07", "Resultado Antes dos Tributos sobre o Lucro", -142522, -122071),
    ("3.08", "Imposto de Renda e Contribuição Social sobre o Lucro", -12157, 6060),
    ("3.09", "Resultado Líquido das Operações Continuadas", -154679, -116011),
    ("3.10", "Resultado Líquido de Operações Descontinuadas", 0, 0),
    ("3.11", "Lucro/Prejuízo Consolidado do Período", -154679, -116011),
    ("3.99", "Lucro por Ação - (Reais / Ação)", 0, 0)]

BANCO_INDIVIDUAL = [  # Banco ABC Brasil, individual, ITR 2026-06-30
    ("3.01", "Receitas de Intermediação Financeira", 3869557, 4249726),
    ("3.02", "Despesas de Intermediação Financeira", -2961746, -3476913),
    ("3.03", "Resultado Bruto de Intermediação Financeira", 907811, 772813),
    ("3.04", "Outras Despesas e Receitas Operacionais", -295833, -213012),
    ("3.05", "Resultado antes dos Tributos sobre o Lucro", 611978, 559801),
    ("3.06", "Imposto de Renda e Contribuição Social sobre o Lucro", 12462, 12189),
    ("3.07", "Lucro ou Prejuízo das Operações Continuadas", 624440, 571990),
    ("3.08", "Resultado Líquido das Operações Descontinuadas", 0, 0),
    ("3.09", "Lucro ou Prejuízo antes das Participações e Contribuições Estatutárias", 624440, 571990),
    ("3.10", "Participações nos Lucros e Contribuições Estatutárias", -136906, -102323),
    ("3.11", "Lucro ou Prejuízo Líquido do Período", 487534, 469667)]

BANCO_IFRS = [  # Itaú Unibanco, consolidado: sem 3.10/3.11
    ("3.01", "Receitas da Intermediação Financeira", 199118000, 200251000),
    ("3.02", "Despesas da Intermediação Financeira", -127362000, -133262000),
    ("3.03", "Resultado Bruto Intermediação Financeira", 71756000, 66989000),
    ("3.04", "Outras Despesas/Receitas Operacionais", -44774000, -44446000),
    ("3.05", "Resultado Antes dos Tributos sobre o Lucro", 26982000, 22543000),
    ("3.06", "Imposto de Renda e Contribuição Social sobre o Lucro", -2783000, -438000),
    ("3.07", "Resultado Líquido das Operações Continuadas", 24199000, 22105000),
    ("3.08", "Resultado Líquido das Operações Descontinuadas", 0, 0),
    ("3.09", "Lucro/Prejuízo Consolidado do Período", 24199000, 22105000)]

SEGURADORA = [  # BB Seguridade, consolidado
    ("3.01", "Receitas das Atividades Seguradoras/Resseguradoras", 0, 0),
    ("3.02", "Despesas da Atividade Seguradora/Resseguradora", 0, 0),
    ("3.03", "Resultado Bruto", 0, 0),
    ("3.04", "Despesas Administrativas", 0, 0),
    ("3.05", "Outras Receitas e Despesas Operacionais", 2270999, 2293719),
    ("3.06", "Resultado de Equivalência Patrimonial", 2718613, 2587689),
    ("3.07", "Resultado Antes do Resultado Financeiro e dos Tributos", 4989612, 4881408),
    ("3.08", "Resultado Financeiro", 498579, 419751),
    ("3.09", "Resultado Antes dos Tributos sobre o Lucro", 5488191, 5301159),
    ("3.10", "Imposto de Renda e Contribuição Social sobre o Lucro", -936022, -920978),
    ("3.11", "Resultado Líquido das Operações Continuadas", 4552169, 4380181),
    ("3.12", "Resultado Líquido de Operações Descontinuadas", 0, 0),
    ("3.13", "Lucro/Prejuízo Consolidado do Período", 4552169, 4380181)]

PLANO_ANTIGO = [  # Dibens Leasing, individual: sem o subtotal-âncora do plano atual
    ("3.01", "Receitas da Intermediação Financeira", 53401, 58952),
    ("3.02", "Despesas da Intermediação Financeira", -89, -79),
    ("3.03", "Resultado Bruto Intermediação Financeira", 53312, 58873),
    ("3.04", "Outras Despesas/Receitas Operacionais", -1852, -2188),
    ("3.05", "Resultado Operacional", 51460, 56685),
    ("3.06", "Resultado Não Operacional", 0, 0),
    ("3.07", "Resultado Antes Tributação/Participações", 51460, 56685),
    ("3.08", "Provisão para IR e Contribuição Social", -19068, -21155),
    ("3.09", "IR Diferido", 0, 0),
    ("3.10", "Participações/Contribuições Estatutárias", 0, 0),
    ("3.11", "Reversão dos Juros sobre Capital Próprio", 0, 0),
    ("3.13", "Lucro/Prejuízo do Período", 32392, 35530)]


def _contas(itens):
    return [i["conta"] for i in itens]


# ── Estrutura por plano ──────────────────────────────────────────────────────

class TestEstrutura(unittest.TestCase):

    def test_comercial(self):
        _, d = _dec(COMERCIAL)
        self.assertTrue(d["fecha"])
        self.assertEqual(_contas(d["ponte"]), ["Resultado Antes do Resultado Financeiro e dos Tributos",
                                               "Resultado Financeiro",
                                               "Imposto de Renda e Contribuição Social sobre o Lucro"])
        self.assertEqual(_contas(d["subtotais_intermediarios"]),
                         ["Resultado Antes dos Tributos sobre o Lucro"])
        self.assertEqual(d["abertura_da_ancora"]["conta"],
                         "Resultado Antes do Resultado Financeiro e dos Tributos")
        self.assertEqual(_contas(d["abertura_da_ancora"]["itens"]),
                         ["Resultado Bruto", "Despesas/Receitas Operacionais"])
        self.assertEqual(d["resultado"]["conta"], "Lucro/Prejuízo Consolidado do Período")

    def test_banco_com_participacoes(self):
        m, d = _dec(BANCO_INDIVIDUAL, titulo="Demonstração de Resultado (Individual)")
        self.assertTrue(d["fecha"])
        self.assertNotIn("Resultado Financeiro", _contas(d["ponte"]))   # não existe no plano
        self.assertEqual(_contas(d["ponte"]), ["Resultado antes dos Tributos sobre o Lucro",
                                               "Imposto de Renda e Contribuição Social sobre o Lucro",
                                               "Participações nos Lucros e Contribuições Estatutárias"])
        self.assertEqual(_contas(d["abertura_da_ancora"]["itens"]),
                         ["Resultado Bruto de Intermediação Financeira",
                          "Outras Despesas e Receitas Operacionais"])
        # 3.07 e 3.09 têm o mesmo valor: aparecem uma vez só
        self.assertEqual(_contas(d["subtotais_intermediarios"]),
                         ["Lucro ou Prejuízo das Operações Continuadas"])
        self.assertEqual(d["resultado"]["valor_atual"], formatar_moeda(487534))

    def test_banco_ifrs_sem_3_10_e_3_11(self):
        _, d = _dec(BANCO_IFRS)
        self.assertTrue(d["fecha"])
        self.assertEqual(d["resultado"]["conta"], "Lucro/Prejuízo Consolidado do Período")
        self.assertEqual(_contas(d["ponte"]), ["Resultado Antes dos Tributos sobre o Lucro",
                                               "Imposto de Renda e Contribuição Social sobre o Lucro"])
        self.assertNotIn("subtotais_intermediarios", d)

    def test_seguradora(self):
        _, d = _dec(SEGURADORA)
        self.assertTrue(d["fecha"])
        self.assertEqual(_contas(d["ponte"]), ["Resultado Antes do Resultado Financeiro e dos Tributos",
                                               "Resultado Financeiro",
                                               "Imposto de Renda e Contribuição Social sobre o Lucro"])
        # sem subtotal antes da âncora: a abertura são as linhas com valor
        self.assertEqual(_contas(d["abertura_da_ancora"]["itens"]),
                         ["Outras Receitas e Despesas Operacionais",
                          "Resultado de Equivalência Patrimonial"])

    def test_plano_antigo_sem_ancora(self):
        _, d = _dec(PLANO_ANTIGO, titulo="Demonstração de Resultado (Individual)")
        self.assertFalse(d["fecha"])
        self.assertIn("subtotal-âncora", d["motivo"])
        self.assertNotIn("ponte", d)

    def test_dre_zerada(self):
        zerada = [(c, n, 0, 0) for c, n, _, _ in COMERCIAL]
        _, d = _dec(zerada)
        self.assertFalse(d["fecha"])
        self.assertIn("zerados", d["motivo"])

    def test_sem_a_primeira_ancora_usa_resultado_antes_dos_tributos(self):
        dre = [(c, "Lucro Operacional Ajustado" if c == "3.05" else n, a, b)
               for c, n, a, b in COMERCIAL]
        _, d = _dec(dre)
        self.assertTrue(d["fecha"])
        self.assertEqual(_contas(d["ponte"]), ["Resultado Antes dos Tributos sobre o Lucro",
                                               "Imposto de Renda e Contribuição Social sobre o Lucro"])

    def test_sem_nenhuma_ancora(self):
        novos = {"3.05": "Lucro Operacional Ajustado", "3.07": "Lucro Antes do IR Ajustado"}
        dre = [(c, novos.get(c, n), a, b) for c, n, a, b in COMERCIAL]
        _, d = _dec(dre)
        self.assertFalse(d["fecha"])
        self.assertIn("subtotal-âncora", d["motivo"])

    def test_sem_cd_conta(self):
        _, d = _dec(COMERCIAL, com_codigo=False)
        self.assertEqual(d["fecha"], False)
        self.assertIn("CD_CONTA", d["motivo"])
        self.assertEqual(set(d), {"base", "comparacao", "fecha", "motivo"})

    def test_tolerancia_de_arredondamento(self):
        # subtotal publicado com 1 mil de diferença: fecha
        dre = [(c, n, a + (1 if c == "3.07" else 0), b) for c, n, a, b in COMERCIAL]
        _, d = _dec(dre)
        self.assertTrue(d["fecha"])
        # diferença acima da tolerância: não fecha e não inventa parcela
        dre = [(c, n, a + 50 if c == "3.07" else a, b) for c, n, a, b in COMERCIAL]
        _, d = _dec(dre)
        self.assertFalse(d["fecha"])
        self.assertNotIn("ponte", d)

    def test_resultado_final_diferente_do_lucro_nao_fecha(self):
        # Conta final fora dos nomes de lucro: lucro_liquido cai em
        # "Operações Continuadas" (3.09), que difere do final por causa de 3.10.
        dre = [(c, "Resultado Ajustado do Período" if c == "3.11" else n,
                a - 1000 if c == "3.11" else a, b) for c, n, a, b in COMERCIAL]
        dre = [(c, n, -1000 if c == "3.10" else a, b) for c, n, a, b in dre]
        m, d = _dec(dre)
        self.assertFalse(d["fecha"])
        self.assertIn("lucro_liquido", d["motivo"])


# ── Posição dos subtotais intermediários ─────────────────────────────────────

class TestPosicaoSubtotais(unittest.TestCase):
    """Cada subtotal intermediário diz entre quais parcelas da ponte fica
    ("apos"/"antes"); é informativo e não entra na soma."""

    @classmethod
    def setUpClass(cls):
        cls.m = {t: calcular_metricas(extrair_documento(
                     os.path.join(FIXTURES, f"{t}_ITR_2026-06-30_cd_conta.txt")))
                 for t in ("WEGE3", "BBAS3", "ZAMP3")}

    def _ordem(self, d):
        """Cadeia reconstruída: parcelas da ponte com os subtotais na posição."""
        ordem = _contas(d["ponte"])
        for s in d.get("subtotais_intermediarios", []):
            i = ordem.index(s["apos"])
            self.assertEqual(ordem[i + 1] if i + 1 < len(ordem) else d["resultado"]["conta"],
                             s["antes"])
            ordem.insert(i + 1, s["conta"])
        return ordem + [d["resultado"]["conta"]]

    def test_wege3_e_zamp3_resultado_antes_dos_tributos_entre_financeiro_e_ir(self):
        for t in ("WEGE3", "ZAMP3"):
            with self.subTest(ticker=t):
                d = self.m[t]["decomposicao_resultado"]
                self.assertTrue(d["fecha"])
                (s,) = d["subtotais_intermediarios"]
                self.assertEqual((s["conta"], s["apos"], s["antes"]),
                                 ("Resultado Antes dos Tributos sobre o Lucro", "Resultado Financeiro",
                                  "Imposto de Renda e Contribuição Social sobre o Lucro"))
                self.assertEqual(self._ordem(d), [
                    "Resultado Antes do Resultado Financeiro e dos Tributos",
                    "Resultado Financeiro",
                    "Resultado Antes dos Tributos sobre o Lucro",
                    "Imposto de Renda e Contribuição Social sobre o Lucro",
                    "Lucro/Prejuízo Consolidado do Período"])

    def test_bbas3_estrutura_bancaria(self):
        d = self.m["BBAS3"]["decomposicao_resultado"]
        self.assertTrue(d["fecha"])
        # 3.07 e 3.09 repetem o resultado final: nenhum subtotal intermediário
        self.assertNotIn("subtotais_intermediarios", d)
        self.assertEqual(self._ordem(d), [
            "Resultado antes dos Tributos sobre o Lucro",
            "Imposto de Renda e Contribuição Social sobre o Lucro",
            "Lucro ou Prejuízo Líquido Consolidado do Período"])

    def test_banco_com_participacoes(self):
        _, d = _dec(BANCO_INDIVIDUAL, titulo="Demonstração de Resultado (Individual)")
        (s,) = d["subtotais_intermediarios"]
        self.assertEqual((s["apos"], s["antes"]),
                         ("Imposto de Renda e Contribuição Social sobre o Lucro",
                          "Participações nos Lucros e Contribuições Estatutárias"))

    def test_subtotal_informativo_e_o_acumulado_ate_a_parcela_anterior(self):
        for t in ("WEGE3", "ZAMP3"):
            with self.subTest(ticker=t):
                b = _bruto(extrair_documento(os.path.join(FIXTURES, f"{t}_ITR_2026-06-30_cd_conta.txt")))
                nomes = [n for n, _, _ in b["ponte"]]
                contrib = [a - ant for _, a, ant in b["ponte"]]
                _, fim_a, fim_ant = b["resultado"]
                self.assertEqual(sum(contrib), fim_a - fim_ant)       # a soma não muda
                for nome, a, ant, apos, antes in b["subtotais"]:
                    self.assertNotIn(nome, nomes)                     # não é parcela
                    i = nomes.index(apos)
                    # variação do subtotal = parcelas até "apos" (acumulado)
                    self.assertEqual(a - ant, sum(contrib[:i + 1]))


# ── lucro_liquido dos bancos só-individuais ──────────────────────────────────

class TestLucroBancoIndividual(unittest.TestCase):

    def test_lucro_e_a_conta_final_depois_das_participacoes(self):
        for com_codigo in (True, False):
            with self.subTest(com_codigo=com_codigo):
                m = calcular_metricas(_secoes(BANCO_INDIVIDUAL, com_codigo=com_codigo,
                                              titulo="Demonstração de Resultado (Individual)"))
                l = m["lucro_liquido"]
                self.assertEqual(l["valor_atual"], formatar_moeda(487534))       # não 624.440
                self.assertEqual(l["valor_anterior"], formatar_moeda(469667))    # não 571.990

    def test_sem_conta_final_usa_operacoes_continuadas(self):
        dre = [l for l in BANCO_INDIVIDUAL if l[0] not in ("3.10", "3.11")]
        m = calcular_metricas(_secoes(dre, titulo="Demonstração de Resultado (Individual)"))
        self.assertEqual(m["lucro_liquido"]["valor_atual"], formatar_moeda(624440))


# ── Propriedades ─────────────────────────────────────────────────────────────

class TestPropriedades(unittest.TestCase):

    CASOS = [(COMERCIAL, {}), (BANCO_INDIVIDUAL, {"titulo": "Demonstração de Resultado (Individual)"}),
             (BANCO_IFRS, {}), (SEGURADORA, {})]

    def _todos(self):
        for dre, kw in self.CASOS:
            secoes = _secoes(dre, **kw)
            base = "Individual" if "Individual" in kw.get("titulo", "") else "Consolidado"
            yield dre, secoes, calcular_metricas(secoes), _bruto(secoes, base)
        for t in ("WEGE3", "BBAS3", "ZAMP3"):
            secoes = extrair_documento(os.path.join(FIXTURES, f"{t}_ITR_2026-06-30_cd_conta.txt"))
            yield t, secoes, calcular_metricas(secoes), _bruto(secoes)

    def test_soma_das_contribuicoes_e_a_variacao_do_resultado(self):
        for caso, _, m, b in self._todos():
            with self.subTest(caso=str(caso)[:20]):
                self.assertTrue(b["fecha"])
                _, a, ant = b["resultado"]
                self.assertAlmostEqual(sum(x - y for _, x, y in b["ponte"]), a - ant,
                                       delta=M._TOLERANCIA_DRE)
                _, anc_a, anc_ant = b["ponte"][0]
                if b["abertura"]:
                    self.assertAlmostEqual(sum(x - y for _, x, y in b["abertura"]),
                                           anc_a - anc_ant, delta=M._TOLERANCIA_DRE)

    def test_resultado_final_e_o_lucro_liquido(self):
        for caso, _, m, _ in self._todos():
            with self.subTest(caso=str(caso)[:20]):
                d = m["decomposicao_resultado"]
                self.assertEqual(d["resultado"]["valor_atual"], m["lucro_liquido"]["valor_atual"])
                self.assertEqual(d["resultado"]["valor_anterior"], m["lucro_liquido"]["valor_anterior"])

    def test_contribuicao_e_diferenca_absoluta_sem_percentual(self):
        for caso, _, m, b in self._todos():
            with self.subTest(caso=str(caso)[:20]):
                d = m["decomposicao_resultado"]
                self.assertNotIn("%", json.dumps(d, ensure_ascii=False))
                for item, (_, a, ant) in zip(d["ponte"], b["ponte"]):
                    self.assertEqual(item["contribuicao"], M._formatar_contribuicao(a - ant))

    def test_efeito_so_aritmetico(self):
        for caso, _, m, _ in self._todos():
            with self.subTest(caso=str(caso)[:20]):
                d = m["decomposicao_resultado"]
                itens = d["ponte"] + d.get("abertura_da_ancora", {}).get("itens", [])
                for item in itens:
                    self.assertIn(item["efeito"], EFEITOS)
                for texto in [item["efeito"] for item in itens] + [d["criterio"]]:
                    self.assertIsNone(JULGAMENTO.search(texto), texto)
                self.assertNotIn("maior_contribuicao", d)
                self.assertNotIn("principal_fator", d)

    def test_efeito_segue_o_sinal_da_contribuicao(self):
        self.assertEqual(M.efeito_no_resultado(10), "aumentou o resultado")
        self.assertEqual(M.efeito_no_resultado(-10), "reduziu o resultado")
        self.assertEqual(M.efeito_no_resultado(0), "não alterou o resultado")
        self.assertEqual(M.efeito_no_resultado(-10, "subtotal"), "reduziu o subtotal")


# ── Casos reais do ITR 2026-06-30 (R$ mil) ───────────────────────────────────

class TestCasosReais(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.b = {t: _bruto(extrair_documento(os.path.join(FIXTURES, f"{t}_ITR_2026-06-30_cd_conta.txt")))
                 for t in ("WEGE3", "BBAS3", "ZAMP3")}

    def _contribuicoes(self, itens):
        return [(n, a - b) for n, a, b in itens]

    def test_wege3(self):
        b = self.b["WEGE3"]
        _, a, ant = b["resultado"]
        self.assertEqual(a - ant, -103597)
        self.assertEqual(self._contribuicoes(b["ponte"]), [
            ("Resultado Antes do Resultado Financeiro e dos Tributos", -159934),
            ("Resultado Financeiro", 18224),
            ("Imposto de Renda e Contribuição Social sobre o Lucro", 38113)])
        self.assertEqual(sum(c for _, c in self._contribuicoes(b["ponte"])), a - ant)

    def test_bbas3(self):
        b = self.b["BBAS3"]
        _, a, ant = b["resultado"]
        self.assertEqual(a - ant, -1397155)
        self.assertEqual(self._contribuicoes(b["ponte"]), [
            ("Resultado antes dos Tributos sobre o Lucro", 1081757),
            ("Imposto de Renda e Contribuição Social sobre o Lucro", -2478912)])
        self.assertEqual(self._contribuicoes(b["abertura"]), [
            ("Resultado Bruto de Intermediação Financeira", 1499014),
            ("Outras Despesas e Receitas Operacionais", -417257)])
        self.assertEqual(sum(c for _, c in self._contribuicoes(b["ponte"])), a - ant)

    def test_bbas3_ir_positivo_em_queda_reduz_o_resultado(self):
        m = calcular_metricas(extrair_documento(
            os.path.join(FIXTURES, "BBAS3_ITR_2026-06-30_cd_conta.txt")))
        ir = m["decomposicao_resultado"]["ponte"][1]
        self.assertEqual((ir["valor_anterior"], ir["valor_atual"]),
                         ("R$ 6,12 bilhões", "R$ 3,64 bilhões"))
        self.assertEqual(ir["efeito"], "reduziu o resultado")

    def test_zamp3(self):
        b = self.b["ZAMP3"]
        _, a, ant = b["resultado"]
        self.assertEqual(a - ant, -38668)
        self.assertEqual(self._contribuicoes(b["ponte"]), [
            ("Resultado Antes do Resultado Financeiro e dos Tributos", 4225),
            ("Resultado Financeiro", -24676),
            ("Imposto de Renda e Contribuição Social sobre o Lucro", -18217)])
        self.assertEqual(self._contribuicoes(b["abertura"]), [
            ("Resultado Bruto", 278330), ("Despesas/Receitas Operacionais", -274105)])
        self.assertEqual(sum(c for _, c in self._contribuicoes(b["ponte"])), a - ant)

    def test_zamp3_operacional_aumentou_o_resultado_mesmo_com_despesas(self):
        d = calcular_metricas(extrair_documento(
            os.path.join(FIXTURES, "ZAMP3_ITR_2026-06-30_cd_conta.txt")))["decomposicao_resultado"]
        self.assertEqual(d["ponte"][0]["efeito"], "aumentou o resultado")
        despesas = d["abertura_da_ancora"]["itens"][1]
        self.assertEqual(despesas["efeito"], "reduziu o subtotal")   # não "o resultado"

    def test_documentos_congelados_sem_codigo_nao_fecham(self):
        for t in ("WEGE3", "BBAS3", "ZAMP3"):
            with self.subTest(ticker=t):
                d = calcular_metricas(extrair_documento(os.path.join(
                    VALIDACAO, f"{t}_ITR_2026-06-30_v1", f"{t}_ITR_2026-06-30.txt")))["decomposicao_resultado"]
                self.assertFalse(d["fecha"])
                self.assertIn("CD_CONTA", d["motivo"])


if __name__ == "__main__":
    unittest.main()
