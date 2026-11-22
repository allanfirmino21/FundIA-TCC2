# tests/test_recuperacao_regressao.py
#
# Regressão da base contábil única na recuperação, com o modelo de embeddings
# real e os documentos do ITR 2026-06-30 v1 (tests/fixtures/). Os contextos de
# referência em tests/fixtures/contextos/ foram gravados ANTES das correções, a
# partir do índice usado na validação manual (mesmos tamanhos do log:
# WEGE3 10.620/2.059, BBAS3 8.807/4.177, ZAMP3 8.541/4.241 caracteres).
#
# Lento (~1 min): carrega o sentence-transformers.
#
# Execução (na raiz do projeto):
#   python -m unittest tests.test_recuperacao_regressao -v

import importlib.util
import os
import sys
import unittest
from unittest import mock

import chromadb

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from modulos.extracao import extrair_documento  # noqa: E402
from modulos.metricas import calcular_metricas  # noqa: E402

FIXTURES = os.path.join(RAIZ, "tests", "fixtures")
TICKERS  = ("WEGE3", "BBAS3", "ZAMP3")
SEP      = "\n" + "-" * 40 + "\n"


def _carregar(nome, pesados):
    """Carrega um módulo de modulos/ de verdade, ignorando stubs em sys.modules."""
    with mock.patch.dict(sys.modules, pesados):
        spec = importlib.util.spec_from_file_location(
            f"{nome}_real", os.path.join(RAIZ, "modulos", f"{nome}.py"))
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
    return modulo


def _ler(caminho):
    with open(caminho, encoding="utf-8", newline="") as f:
        return f.read()


def _referencia(ticker, canal):
    return _ler(os.path.join(FIXTURES, "contextos", f"{ticker}_ITR_2026-06-30_ctx_{canal}.txt"))


def _trechos(ctx):
    """Conteúdo de cada [Trecho N], na ordem."""
    corpo = ctx.split(SEP, 1)[1].rsplit(SEP.rstrip("\n"), 1)[0]
    return [t.split("\n", 1)[1] for t in corpo.split(SEP)]


def _secao(trecho):
    return trecho.split("\n", 1)[0]


class TestRegressaoRecuperacao(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from sentence_transformers import SentenceTransformer
        from config import MODELO_EMBEDDINGS
        cls.chunking = _carregar("chunking", {"chromadb": mock.MagicMock()})
        cls.rec      = _carregar("recuperacao", {"modulos.chunking": cls.chunking})
        cls.modelo   = SentenceTransformer(MODELO_EMBEDDINGS)
        cls.cli      = chromadb.EphemeralClient()
        cls.ctx, cls.base = {}, {}
        for t in TICKERS:
            caminho = os.path.join(FIXTURES, f"{t}_ITR_2026-06-30_cd_conta.txt")
            secoes  = extrair_documento(caminho)
            chunks  = cls.chunking.criar_chunks(secoes)
            nome    = f"regressao_{t.lower()}"
            try:
                cls.cli.delete_collection(nome)
            except Exception:
                pass
            col = cls.cli.create_collection(nome)
            col.add(ids=[c["id"] for c in chunks],
                    documents=[c["texto"] for c in chunks],
                    metadatas=[c["metadata"] for c in chunks],
                    embeddings=cls.modelo.encode([c["texto"] for c in chunks],
                                                 show_progress_bar=False).tolist())
            cls.ctx[t]  = cls.rec._contextos(col, cls.modelo)
            cls.base[t] = calcular_metricas(secoes)["base_dados"]

    def test_narrativo_sem_nenhuma_tabela(self):
        for t in TICKERS:
            _, nar = self.ctx[t]
            with self.subTest(ticker=t):
                self.assertNotIn("[TABELA", nar)

    def test_numerico_identico_nas_tres(self):
        for t in TICKERS:
            num, _ = self.ctx[t]
            with self.subTest(ticker=t):
                self.assertEqual(num, _referencia(t, "num"))

    def test_narrativo_e_so_o_cabecalho_de_antes(self):
        # Documento estruturado: o canal narrativo fica só com o Cabeçalho que
        # já existia; nenhuma tabela (antes: DRE Individual na WEGE3, DFC na
        # BBAS3 e na ZAMP3)
        for t in TICKERS:
            _, nar = self.ctx[t]
            with self.subTest(ticker=t):
                antes = _trechos(_referencia(t, "nar"))
                self.assertTrue(antes[1].startswith("[TABELA"))
                self.assertEqual(nar, self.rec._formatar_contexto([antes[0]], "narrativo"))

    def test_toda_tabela_do_numerico_tem_a_base_das_metricas(self):
        for t in TICKERS:
            num, _ = self.ctx[t]
            with self.subTest(ticker=t):
                tabelas = [_secao(x) for x in _trechos(num) if x.startswith("[TABELA")]
                self.assertTrue(tabelas)
                for s in tabelas:
                    self.assertIn(f"({self.base[t]})", s)

if __name__ == "__main__":
    unittest.main()
