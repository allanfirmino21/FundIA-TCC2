# tests/test_cd_conta.py
#
# CD_CONTA preservado no .txt (FORMATO: CD_CONTA) e seleção hierárquica de
# "Aplicações Financeiras" em calcular_metricas(). Achado 1 da validação
# manual do TCC 2: na WEGE3 a liquidez somava 1.01.01.02 — componente do
# próprio caixa — em vez de 1.01.02.
#
# Os documentos reais em tests/fixtures/ foram gerados por baixar_documento()
# a partir do ZIP oficial itr_cia_aberta_2026.zip (ITR 2026-06-30, versão 1).
# As referências "antes" são os artefatos congelados da validação manual.
#
# Execução (na raiz do projeto):
#   python -m unittest tests.test_cd_conta -v

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from modulos import metricas  # noqa: E402
from modulos.auditoria import auditar_narrativa  # noqa: E402
from modulos.extracao import extrair_documento  # noqa: E402
from modulos.metricas import calcular_metricas, formatar_moeda  # noqa: E402

FIXTURES   = os.path.join(RAIZ, "tests", "fixtures")
VALIDACAO  = os.path.join(RAIZ, "avaliacao", "validacao_manual")
TICKERS    = ("WEGE3", "BBAS3", "ZAMP3")

# Únicos campos que a correção pode mudar (todos derivados da liquidez)
CAMPOS_LIQUIDEZ = {"aplicacoes_financeiras", "liquidez_total", "divida_liquida",
                   "divida_liquida_anterior", "divida_liquida_com_arrendamentos"}


def _chunking_real():
    """
    Carrega modulos/chunking.py de verdade, sem o custo de importar
    sentence_transformers/chromadb (só usados na indexação) e sem depender de
    outro teste ter trocado modulos.chunking por um stub em sys.modules.
    """
    pesados = {"sentence_transformers": mock.MagicMock(), "chromadb": mock.MagicMock()}
    with mock.patch.dict(sys.modules, pesados):
        spec = importlib.util.spec_from_file_location(
            "chunking_real", os.path.join(RAIZ, "modulos", "chunking.py"))
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
    return modulo


def _fixture(ticker):
    return os.path.join(FIXTURES, f"{ticker}_ITR_2026-06-30_cd_conta.txt")


def _congelado(ticker, arquivo=None):
    pasta = os.path.join(VALIDACAO, f"{ticker}_ITR_2026-06-30_v1")
    return os.path.join(pasta, arquivo or f"{ticker}_ITR_2026-06-30.txt")


def _dados_congelados(ticker):
    with open(_congelado(ticker, "resultado_analisar.json"), encoding="utf-8") as f:
        return json.load(f)["analise"]


def _json(obj):
    """Mesma forma do JSON gravado (tuplas viram listas etc.)."""
    return json.loads(json.dumps(obj, ensure_ascii=False, default=str))


def _preexistentes(metricas_calculadas):
    """Métricas sem os blocos acrescentados depois da validação
    (demonstracoes_resumidas, decomposicao_resultado), para comparar com os
    artefatos congelados."""
    d = _json(metricas_calculadas)
    d.pop("demonstracoes_resumidas", None)
    d.pop("decomposicao_resultado", None)
    return d


# Correção posterior à validação que também vale para documentos sem CD_CONTA
# (busca por nome): a captação no mercado aberto do BBAS3 deixou de ser
# nao_disponivel ("Captações", plural, na CVM). Ver tests/test_captacao.py.
CAPTACAO_BBAS3 = "R$ 845,41 bilhões"
DESTAQUE_CAPTACAO_BBAS3 = "Captação no mercado aberto: R$ 845,41 bilhões (variação +16,3%)"


def _sem_correcao_de_captacao(ticker, d):
    """Desfaz, para comparação, só o efeito da correção de captação no BBAS3."""
    if ticker != "BBAS3":
        return d
    assert d["endividamento"]["captacao_mercado_aberto"] == CAPTACAO_BBAS3
    assert DESTAQUE_CAPTACAO_BBAS3 in d["outros_destaques"]
    d["endividamento"]["captacao_mercado_aberto"] = "nao_disponivel"
    d["outros_destaques"].remove(DESTAQUE_CAPTACAO_BBAS3)
    return d


# ── Documento sintético ───────────────────────────────────────────────────────

def _linha(cod, nome, atual, anterior, com_codigo=True):
    prefixo = f"[{cod}] " if com_codigo and cod else ""
    return f"{prefixo}{nome:<55} {float(atual):>20.10f}  (anterior: {float(anterior):.10f})"


def _secao(titulo, linhas, com_codigo=True):
    corpo = "\n".join(_linha(*l, com_codigo=com_codigo) for l in linhas)
    return f"\n{'=' * 50}\n{titulo}\n{'=' * 50}\n{corpo}"


DRE = [("3.01", "Receita de Venda de Bens e/ou Serviços", 1000000, 900000),
       ("3.11", "Lucro/Prejuízo Consolidado do Período", 150000, 140000)]

PASSIVO = [("2", "Passivo Total", 20000000, 19000000),
           ("2.01", "Passivo Circulante", 4000000, 3900000),
           ("2.01.04", "Empréstimos e Financiamentos", 1000000, 900000),
           ("2.02", "Passivo Não Circulante", 5000000, 4800000),
           ("2.02.01", "Empréstimos e Financiamentos", 2000000, 1800000),
           ("2.03", "Patrimônio Líquido Consolidado", 11000000, 10300000)]
DIVIDA_BRUTA, DIVIDA_BRUTA_ANT = 3000000, 2700000

# Estrutura da WEGE3 no ITR 2026-06-30: a primeira "Aplicações Financeiras"
# do circulante é 1.01.01.02, filha do caixa.
ATIVO_WEGE3 = [("1", "Ativo Total", 46670000, 42640000),
               ("1.01", "Ativo Circulante", 30055127, 26910845),
               ("1.01.01", "Caixa e Equivalentes de Caixa", 7750256, 6296498),
               ("1.01.01.01", "Caixa e Bancos", 2273211, 2040959),
               ("1.01.01.02", "Aplicações Financeiras", 5477045, 4255539),
               ("1.01.02", "Aplicações Financeiras", 1050886, 983367),
               ("1.01.02.01", "Aplicações Financeiras Avaliadas a Valor Justo através do Resultado", 0, 0),
               ("1.01.03", "Contas a Receber", 8105685, 7000000),
               ("1.02", "Ativo Não Circulante", 16611304, 15734185),
               ("1.02.01.01", "Aplicações Financeiras Avaliadas a Valor Justo através do Resultado", 11821, 14263)]


def _metricas_sinteticas(ativo, com_codigo=True):
    texto = "\n".join([
        "DOCUMENTO: ITR — 2026-06-30", "EMPRESA CVM: 9999", "VERSAO: 1",
        f"FORMATO: {'CD_CONTA' if com_codigo else ''}", "",
        _secao("Demonstração de Resultado (Consolidado)", DRE, com_codigo),
        _secao("Balanço Patrimonial — Ativo (Consolidado)", ativo, com_codigo),
        _secao("Balanço Patrimonial — Passivo (Consolidado)", PASSIVO, com_codigo),
    ])
    with tempfile.TemporaryDirectory() as tmp:
        caminho = os.path.join(tmp, "doc.txt")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(texto)
        return calcular_metricas(extrair_documento(caminho))["endividamento"]


def _sem(ativo, *codigos):
    return [l for l in ativo if l[0] not in codigos]


# ── Parsing ───────────────────────────────────────────────────────────────────

class TestParsing(unittest.TestCase):

    COM = "[1.01.02] Aplicações Financeiras                                    1050886.0000000000  (anterior: 983367.0000000000)"
    SEM = "Aplicações Financeiras                                    1050886.0000000000  (anterior: 983367.0000000000)"

    def test_linha_com_codigo_separa_codigo_e_nome(self):
        self.assertEqual(metricas._parsear_linhas_com_codigo(self.COM),
                         [("1.01.02", "Aplicações Financeiras", 1050886.0, 983367.0)])

    def test_linha_sem_codigo_tem_codigo_none(self):
        self.assertEqual(metricas._parsear_linhas_com_codigo(self.SEM),
                         [(None, "Aplicações Financeiras", 1050886.0, 983367.0)])

    def test_parsear_linhas_retrocompativel(self):
        # Mesma saída (nome sem código) para os dois formatos
        esperado = [("Aplicações Financeiras", 1050886.0, 983367.0)]
        self.assertEqual(metricas._parsear_linhas(self.COM), esperado)
        self.assertEqual(metricas._parsear_linhas(self.SEM), esperado)

    def test_nome_longo_com_codigo(self):
        # Nome acima de 55 caracteres: sobra um único espaço antes do valor
        linha = ("[6.01.01.03] Juros, encargos, variação cambial, variação monetária "
                 "e AVP sobre passivos de arrendamentos    162230.0000000000  "
                 "(anterior: 103419.0000000000)")
        cod, nome, atual, ant = metricas._parsear_linhas_com_codigo(linha)[0]
        self.assertEqual(cod, "6.01.01.03")
        self.assertTrue(nome.startswith("Juros, encargos"))
        self.assertEqual((atual, ant), (162230.0, 103419.0))


# ── Seleção de "Aplicações Financeiras" ──────────────────────────────────────

class TestAplicacoesCirculante(unittest.TestCase):

    def test_wege3_usa_1_01_02_e_nao_a_filha_do_caixa(self):
        e = _metricas_sinteticas(ATIVO_WEGE3)
        liquidez     = 7750256 + 1050886
        liquidez_ant = 6296498 + 983367
        self.assertEqual(e["aplicacoes_financeiras"], formatar_moeda(1050886))
        self.assertEqual(e["liquidez_total"],         formatar_moeda(liquidez))
        self.assertEqual(e["divida_liquida"],          formatar_moeda(DIVIDA_BRUTA - liquidez))
        self.assertEqual(e["divida_liquida_anterior"], formatar_moeda(DIVIDA_BRUTA_ANT - liquidez_ant))

    def test_sem_aplicacoes_liquidez_e_so_o_caixa(self):
        ativo = _sem(ATIVO_WEGE3, "1.01.01.02", "1.01.02", "1.01.02.01")
        e = _metricas_sinteticas(ativo)
        self.assertEqual(e["aplicacoes_financeiras"], "nao_disponivel")
        self.assertEqual(e["liquidez_total"], formatar_moeda(7750256))

    def test_so_a_filha_do_caixa_nao_e_escolhida(self):
        # Sem 1.01.02, a 1.01.01.02 continua fora: já está dentro do caixa
        ativo = _sem(ATIVO_WEGE3, "1.01.02", "1.01.02.01")
        e = _metricas_sinteticas(ativo)
        self.assertEqual(e["aplicacoes_financeiras"], "nao_disponivel")
        self.assertEqual(e["liquidez_total"], formatar_moeda(7750256))

    def test_aplicacao_zerada(self):
        ativo = [l if l[0] != "1.01.02" else ("1.01.02", "Aplicações Financeiras", 0, 0)
                 for l in ATIVO_WEGE3]
        e = _metricas_sinteticas(ativo)
        self.assertEqual(e["liquidez_total"], formatar_moeda(7750256))

    def test_banco_sem_ativo_circulante_nada_e_escolhido(self):
        linhas = [("1", "Ativo Total", 2588103740, 2455143253),
                  ("1.01", "Caixa e Equivalentes de Caixa", 65017849, 59635525),
                  ("1.01.02", "Aplicações de Liquidez", 100, 90),
                  ("1.02.01", "Aplicações Financeiras", 200, 180)]
        self.assertEqual(metricas._aplicacoes_circulante(
            [(c, n, a, b) for c, n, a, b in linhas]), (None, None))

    def test_documento_sem_codigo_mantem_regra_original(self):
        # Artefatos antigos continuam reproduzíveis — inclusive o defeito
        e = _metricas_sinteticas(ATIVO_WEGE3, com_codigo=False)
        self.assertEqual(e["aplicacoes_financeiras"], formatar_moeda(5477045))
        self.assertEqual(e["liquidez_total"], formatar_moeda(7750256 + 5477045))


# ── Regressão com os documentos reais do ITR 2026-06-30 v1 ───────────────────

class TestRegressaoDocumentosReais(unittest.TestCase):

    def test_bbas3_e_zamp3_metricas_identicas_as_da_validacao(self):
        for t in ("BBAS3", "ZAMP3"):
            with self.subTest(ticker=t):
                novo = _preexistentes(calcular_metricas(extrair_documento(_fixture(t))))
                self.assertEqual(_sem_correcao_de_captacao(t, novo),
                                 _dados_congelados(t)["dados_extraidos"])

    def test_wege3_muda_so_a_liquidez_e_derivados(self):
        antes = _dados_congelados("WEGE3")["dados_extraidos"]
        depois = _preexistentes(calcular_metricas(extrair_documento(_fixture("WEGE3"))))

        e_antes, e_depois = antes.pop("endividamento"), depois.pop("endividamento")
        self.assertEqual(depois, antes, "métricas fora do endividamento mudaram")
        for campo in set(e_antes) | set(e_depois):
            if campo not in CAMPOS_LIQUIDEZ:
                self.assertEqual(e_depois.get(campo), e_antes.get(campo), campo)

        self.assertEqual(e_depois["aplicacoes_financeiras"], "R$ 1,05 bilhões")
        self.assertEqual(e_depois["liquidez_total"],         "R$ 8,80 bilhões")
        self.assertEqual(e_depois["divida_liquida"],          "-R$ 3,73 bilhões")
        self.assertEqual(e_depois["divida_liquida_anterior"], "-R$ 2,69 bilhões")
        self.assertEqual(e_depois["divida_liquida_com_arrendamentos"], "-R$ 2,97 bilhões")

    def test_artefatos_congelados_continuam_reproduziveis(self):
        # O .txt da validação (sem CD_CONTA) reproduz as métricas avaliadas,
        # exceto a correção de captação do BBAS3, que também vale para ele
        for t in TICKERS:
            with self.subTest(ticker=t):
                antigo = _preexistentes(calcular_metricas(extrair_documento(_congelado(t))))
                self.assertEqual(_sem_correcao_de_captacao(t, antigo),
                                 _dados_congelados(t)["dados_extraidos"])
        self.assertEqual(_dados_congelados("WEGE3")["dados_extraidos"]
                         ["endividamento"]["liquidez_total"], "R$ 13,23 bilhões")

    def test_contexto_do_llm_identico(self):
        chunking = _chunking_real()
        for t in TICKERS:
            with self.subTest(ticker=t):
                novo   = chunking.criar_chunks(extrair_documento(_fixture(t)))
                antigo = chunking.criar_chunks(extrair_documento(_congelado(t)))
                self.assertEqual(novo, antigo)

    def test_auditoria_da_narrativa_congelada_inalterada(self):
        # Mesmos vereditos e fatos; só o texto da origem ganha o [CD_CONTA]
        chaves = ("secao", "trecho", "tipo", "veredito", "fato_mais_proximo")
        for t in TICKERS:
            with self.subTest(ticker=t):
                a = _dados_congelados(t)
                novo = auditar_narrativa(a["secoes"],
                                         extrair_documento(_fixture(t)),
                                         a["dados_extraidos"])
                self.assertEqual(
                    [{k: v[k] for k in chaves} for v in _json(novo)["verificacoes"]],
                    [{k: v[k] for k in chaves} for v in a["auditoria"]["verificacoes"]])


# ── Formato gravado por baixar_documento ─────────────────────────────────────

class TestFormatoDocumento(unittest.TestCase):

    def test_fixtures_tem_marcador_e_codigo_em_todas_as_linhas_de_valor(self):
        for t in TICKERS:
            with self.subTest(ticker=t):
                with open(_fixture(t), encoding="utf-8") as f:
                    linhas = f.read().split("\n")
                self.assertIn("FORMATO: CD_CONTA", linhas[:5])
                valores = [l for l in linhas if "(anterior:" in l]
                self.assertTrue(valores)
                self.assertTrue(all(l.startswith("[") for l in valores))

    def test_fixture_sem_prefixo_e_identica_ao_documento_congelado(self):
        import re
        for t in TICKERS:
            with self.subTest(ticker=t):
                with open(_fixture(t), encoding="utf-8") as f:
                    novo = f.read().split("\n")
                with open(_congelado(t), encoding="utf-8") as f:
                    antigo = f.read()
                sem = "\n".join(re.sub(r"^\[\d+(?:\.\d+)*\] ", "", l)
                                for l in novo if not l.startswith("FORMATO:"))
                self.assertEqual(sem, antigo)


if __name__ == "__main__":
    unittest.main()
