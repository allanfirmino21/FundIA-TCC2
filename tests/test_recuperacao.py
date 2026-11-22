# tests/test_recuperacao.py
#
# Base contábil única na recuperação (recuperacao._base_principal). Achado 2
# da validação manual do TCC 2: o complemento do canal narrativo aceitava
# tabelas de qualquer base e entregou ao Prompt 2 a DRE Individual da WEGE3,
# empresa consolidada. Desde o achado 4 (ZAMP3), documentos estruturados não
# recebem mais nenhuma tabela no canal narrativo; PDFs mantêm o complemento.
#
# Unitário e rápido: ChromaDB em memória com vetores escolhidos à mão para
# forçar o ranking; sem modelo de embeddings.
#
# Execução (na raiz do projeto):
#   python -m unittest tests.test_recuperacao -v

import importlib.util
import os
import sys
import unittest
from unittest import mock

import chromadb

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)


def _recuperacao_real():
    """
    Carrega modulos/recuperacao.py de verdade, sem importar
    sentence_transformers e sem depender de outro teste ter trocado
    modulos.recuperacao por um stub em sys.modules.
    """
    def carregar(nome):
        spec = importlib.util.spec_from_file_location(
            f"{nome}_real", os.path.join(RAIZ, "modulos", f"{nome}.py"))
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo

    with mock.patch.dict(sys.modules, {"sentence_transformers": mock.MagicMock(),
                                       "chromadb": mock.MagicMock()}):
        chunking = carregar("chunking")
    with mock.patch.dict(sys.modules, {"sentence_transformers": mock.MagicMock(),
                                       "modulos.chunking": chunking}):
        return carregar("recuperacao")


rec = _recuperacao_real()

CONSULTA = [1.0, 0.0, 0.0]


class _Modelo:
    """Toda consulta vira o mesmo vetor; o ranking vem dos vetores dos chunks."""
    def encode(self, _texto):
        return mock.MagicMock(tolist=lambda: list(CONSULTA))


# Ranking pela distância à CONSULTA: a DRE Individual é a MAIS próxima —
# exatamente a situação da WEGE3 — e o Cabeçalho, o mais distante.
CHUNKS_CONSOLIDADO = [
    # (id, secao, tipo, base, vetor)
    ("cab",     "Cabeçalho",                                    "narrativo", None,          [0.0, 0.0, 1.0]),
    ("dre_ind", "Demonstração de Resultado (Individual)",       "tabela",    "Individual",  [1.0, 0.0, 0.0]),
    ("dfc",     "Demonstração de Fluxo de Caixa (Consolidado)", "tabela",    "Consolidado", [0.9, 0.1, 0.0]),
    ("bpa",     "Balanço Patrimonial — Ativo (Consolidado)",    "tabela",    "Consolidado", [0.5, 0.5, 0.0]),
    ("bpp",     "Balanço Patrimonial — Passivo (Consolidado)",  "tabela",    "Consolidado", [0.0, 0.9, 0.1]),
    ("dre_con", "Demonstração de Resultado (Consolidado)",      "tabela",    "Consolidado", [0.0, 1.0, 0.0]),
]


def _collection(chunks, nome):
    cli = chromadb.EphemeralClient()
    try:
        cli.delete_collection(nome)
    except Exception:
        pass
    col = cli.create_collection(nome)
    metas = []
    for _, secao, tipo, base, _ in chunks:
        m = {"tipo": tipo, "secao": secao, "pagina": 1}
        if base is not None:
            m["base"] = base
        metas.append(m)
    col.add(ids=[c[0] for c in chunks],
            documents=[f"[{c[2].upper()} | {c[1]}]" for c in chunks],
            metadatas=metas,
            embeddings=[c[4] for c in chunks])
    return col


def _secoes(ctx):
    """Seções dos trechos, na ordem em que aparecem no contexto."""
    return [l.split(" | ", 1)[1].rstrip("]") for l in ctx.split("\n") if " | " in l]


def _canais(col):
    return rec._contextos(col, _Modelo())


class TestBasePrincipal(unittest.TestCase):

    def test_dre_consolidada_define_consolidado(self):
        self.assertEqual(rec._base_principal(_collection(CHUNKS_CONSOLIDADO, "base_cons")), "Consolidado")

    def test_so_individual_define_individual(self):
        so_ind = [c for c in CHUNKS_CONSOLIDADO if c[3] != "Consolidado"]
        self.assertEqual(rec._base_principal(_collection(so_ind, "base_ind")), "Individual")

    def test_base_desconhecida_retorna_none(self):
        pdf = [("t1", "Tabela — tabela", "tabela", "desconhecido", [1.0, 0.0, 0.0]),
               ("n1", "Introdução", "narrativo", None, [0.0, 0.0, 1.0])]
        self.assertIsNone(rec._base_principal(_collection(pdf, "base_pdf")))

    def test_sem_tabelas_retorna_none(self):
        so_cab = [c for c in CHUNKS_CONSOLIDADO if c[2] == "narrativo"]
        self.assertIsNone(rec._base_principal(_collection(so_cab, "base_cab")))


class TestEmpresaConsolidada(unittest.TestCase):

    def setUp(self):
        self.ctx_num, self.ctx_nar = _canais(_collection(CHUNKS_CONSOLIDADO, "cons"))

    def test_narrativo_nao_recebe_individual_mesmo_sendo_a_mais_proxima(self):
        self.assertNotIn("Demonstração de Resultado (Individual)", _secoes(self.ctx_nar))

    def test_narrativo_so_com_o_cabecalho(self):
        # Documento estruturado: nenhuma tabela completa o canal narrativo
        self.assertEqual(_secoes(self.ctx_nar), ["Cabeçalho"])

    def test_numerico_igual_a_regra_anterior(self):
        # A regra anterior já filtrava Consolidado: as 3 consolidadas mais próximas
        self.assertEqual(_secoes(self.ctx_num), [
            "Demonstração de Fluxo de Caixa (Consolidado)",
            "Balanço Patrimonial — Ativo (Consolidado)",
            "Balanço Patrimonial — Passivo (Consolidado)",
        ])

    def test_formato_e_tamanho_dos_canais_preservados(self):
        self.assertTrue(self.ctx_nar.startswith("=== CONTEXTO NARRATIVO ==="))
        self.assertTrue(self.ctx_num.startswith("=== CONTEXTO TABELA ==="))
        self.assertEqual(self.ctx_nar.count("[Trecho "), 1)
        self.assertEqual(self.ctx_num.count("[Trecho "), 3)


class TestEmpresaSoIndividual(unittest.TestCase):

    def setUp(self):
        so_ind = [c for c in CHUNKS_CONSOLIDADO if c[3] != "Consolidado"]
        self.ctx_num, self.ctx_nar = _canais(_collection(so_ind, "ind"))

    def test_narrativo_so_com_o_cabecalho(self):
        # A DRE Individual chega ao Prompt 2 pelas métricas
        # (demonstracoes_resumidas), não mais como tabela no canal narrativo
        self.assertEqual(_secoes(self.ctx_nar), ["Cabeçalho"])

    def test_numerico_recebe_a_dre_individual_e_completa_com_o_cabecalho(self):
        # Mesmo resultado do antigo fallback "sem filtro de base"
        self.assertEqual(_secoes(self.ctx_num),
                         ["Demonstração de Resultado (Individual)", "Cabeçalho"])


class TestBaseDesconhecida(unittest.TestCase):
    """PDF: chunks com base "desconhecido" — comportamento anterior preservado."""

    PDF = [("n1",  "Introdução",        "narrativo", None,           [0.0, 0.0, 1.0]),
           ("t1",  "Tabela A — tabela", "tabela",    "desconhecido", [1.0, 0.0, 0.0]),
           ("t2",  "Tabela B — tabela", "tabela",    "desconhecido", [0.9, 0.1, 0.0]),
           ("t3",  "Tabela C — tabela", "tabela",    "desconhecido", [0.0, 1.0, 0.0])]

    def test_sem_filtro_de_base_e_narrativo_completado_com_tabela(self):
        ctx_num, ctx_nar = _canais(_collection(self.PDF, "pdf"))
        self.assertEqual(_secoes(ctx_num), ["Tabela A — tabela", "Tabela B — tabela",
                                            "Tabela C — tabela"])
        self.assertEqual(_secoes(ctx_nar), ["Introdução", "Tabela A — tabela"])


if __name__ == "__main__":
    unittest.main()
