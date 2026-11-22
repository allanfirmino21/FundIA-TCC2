# tests/test_ragas_dataset.py
#
# Integridade do dataset experimental do RAGAS do TCC 2
# (avaliacao/ragas/dataset_tcc2.json) contra o protocolo pré-registrado
# (avaliacao/ragas/PROTOCOLO_RAGAS_TCC2.md). Não chama LLM nem RAGAS.

import hashlib
import json
import os
import re
import sys
import unittest
from collections import Counter
from decimal import Decimal

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "avaliacao", "ragas")
sys.path.insert(0, PASTA)

import exatidao as X  # noqa: E402
from construir_dataset import ler_protocolo, CATEGORIAS  # noqa: E402
from validar_dataset import verificar, itens_atomicos, CHAVES_PROIBIDAS, chaves  # noqa: E402

DATASET = os.path.join(PASTA, "dataset_tcc2.json")
ESTRUTURAS = {"nao_financeira", "banco", "holding", "resseguradora"}
DISPONIBILIDADES = {"presente", "parcial", "ausente"}

# Cópias do documento já versionadas no repositório (mesmo formato CD_CONTA)
COPIAS = {
    "WEGE3": "avaliacao/validacao_manual/WEGE3_ITR_2026-06-30_v1_final/WEGE3_ITR_2026-06-30.txt",
    "BBAS3": "avaliacao/validacao_manual/BBAS3_ITR_2026-06-30_v1_final/BBAS3_ITR_2026-06-30.txt",
    "ZAMP3": "avaliacao/validacao_manual/ZAMP3_ITR_2026-06-30_v1_final/ZAMP3_ITR_2026-06-30.txt",
    "LWSA3": "tests/fixtures/LWSA3_ITR_2026-06-30_cd_conta.txt",
}


class DatasetRagas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(DATASET, encoding="utf-8") as f:
            cls.ds = json.load(f)
        cls.casos = cls.ds["casos"]
        cls.prot = ler_protocolo()
        cls.pe = {e["ticker"]: e for e in cls.prot["empresas"]}

    # 1–4
    def test_96_casos_12_empresas_8_categorias_ids_unicos(self):
        self.assertEqual(len(self.casos), 96)
        self.assertEqual(set(c["ticker"] for c in self.casos), set(self.pe))
        por_emp = Counter(c["ticker"] for c in self.casos)
        self.assertTrue(all(n == 8 for n in por_emp.values()), por_emp)
        for tk in self.pe:
            self.assertEqual(sorted(c["categoria"] for c in self.casos if c["ticker"] == tk), sorted(CATEGORIAS))
        ids = [c["id"] for c in self.casos]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(c["id"] == f"{c['ticker']}_{c['categoria']}" for c in self.casos))

    # 5
    def test_perguntas_nao_vazias_e_unicas(self):
        self.assertTrue(all(c["pergunta"].strip() for c in self.casos))
        self.assertEqual(len({c["pergunta"] for c in self.casos}), 96)

    def test_perguntas_padronizadas_por_categoria_e_estrutura(self):
        modelos = {}
        for c in self.casos:
            m = c["pergunta"].replace(c["nome_na_pergunta"], "{EMPRESA}")
            m = re.sub(r"\b(da|do|a|o) \{EMPRESA\}", "{ART} {EMPRESA}", m)
            modelos.setdefault((c["categoria"], c["estrutura"]), set()).add(m)
        for k, v in modelos.items():
            self.assertEqual(len(v), 1, (k, v))

    def test_pergunta_nao_contem_valor_esperado(self):
        for c in self.casos:
            for v in itens_atomicos(c):
                if v["tipo"] == "monetario":
                    bruto = f"{abs(Decimal(v['valor_origem'])):,.0f}".replace(",", ".")
                    self.assertNotIn(bruto, c["pergunta"], c["id"])
                    self.assertNotIn(v["apresentacao_referencia"].replace("-", ""), c["pergunta"], c["id"])

    # 6
    def test_gabaritos_estruturalmente_validos(self):
        falhas = {k: v for k, v in verificar(self.ds).items() if v}
        self.assertEqual(falhas, {})
        for c in self.casos:
            self.assertTrue(c["gabarito"].strip(), c["id"])
            for f in c["fontes_gabarito"]:
                for campo in ("demonstracao", "base", "cd_conta", "ds_conta", "periodo", "vl_conta_cvm",
                              "unidade", "escala_moeda", "arquivo_cvm"):
                    self.assertTrue(f.get(campo), (c["id"], campo))
                self.assertEqual(f["base"], "Consolidado")
                self.assertEqual(f["escala_moeda"], "MIL")
            for v in itens_atomicos(c):
                self.assertIn(v["tipo"], ("monetario", "percentual"))
                self.assertIsInstance(v["sinal_exigido"], bool)
                if v["tipo"] == "monetario":
                    self.assertEqual(Decimal(v["valor"]), Decimal(v["valor_origem"]) * 1000, (c["id"], v["id"]))

    def test_fontes_rastreaveis_aos_valores(self):
        """Todo valor monetário de uma só conta coincide com o VL_CONTA da fonte citada."""
        for c in self.casos:
            fontes = {(f["cd_conta"], f["periodo"][:4]): Decimal(f["vl_conta_cvm"]) for f in c["fontes_gabarito"]}
            for v in itens_atomicos(c):
                if v["tipo"] == "monetario" and len(v["fontes"]) == 1:
                    chave = (v["fontes"][0], v["periodo"][:4])
                    self.assertIn(chave, fontes, (c["id"], v["id"]))
                    self.assertEqual(fontes[chave], Decimal(v["valor_origem"]), (c["id"], v["id"]))

    def test_n4_cadeia_fecha_a_variacao_do_resultado(self):
        for c in self.casos:
            if c["categoria"] != "N4":
                continue
            cad = c["cadeia_n4"]
            soma = sum(Decimal(x["variacao_mil"]) for x in cad["componentes_por_magnitude"])
            self.assertEqual(soma, Decimal(cad["variacao_resultado_mil"]), c["id"])
            mags = [abs(Decimal(x["variacao_mil"])) for x in cad["componentes_por_magnitude"]]
            self.assertEqual(mags, sorted(mags, reverse=True), c["id"])

    # 7–8
    def test_documento_periodo_versao_e_hash_do_protocolo(self):
        for c in self.casos:
            e = self.pe[c["ticker"]]
            self.assertEqual((c["documento"], c["periodo"]), ("ITR", "2026-06-30"))
            self.assertEqual(c["versao"], e["versao"], c["id"])
            self.assertEqual(c["codigo_cvm"], e["codigo_cvm"], c["id"])
            self.assertEqual(c["sha256_documento"], e["sha256_documento"], c["id"])
        for tk, e in self.ds["empresas"].items():
            self.assertEqual(e["sha256_documento"], self.pe[tk]["sha256_documento"])

    def test_hash_recalculado_das_copias_versionadas(self):
        for tk, rel in COPIAS.items():
            with open(os.path.join(RAIZ, rel), "rb") as f:
                sha = hashlib.sha256(f.read()).hexdigest()
            self.assertEqual(sha, self.pe[tk]["sha256_documento"], tk)

    def test_protocolo_nao_mudou(self):
        """O protocolo só recebe acréscimos. A versão com que o dataset foi congelado e a coleta
        feita (texto pré-registrado + Emenda 1) é tudo antes da Emenda 2, e o seu hash é o
        registrado no dataset. Depois dela só podem vir, na ordem e byte a byte, as emendas
        pós-congelamento autorizadas; qualquer outro acréscimo ou alteração falha."""
        with open(os.path.join(PASTA, "PROTOCOLO_RAGAS_TCC2.md"), "rb") as f:
            b = f.read()
        i = b.index(b"\n### Emenda 2")
        self.assertEqual(hashlib.sha256(b[:i]).hexdigest(), self.ds["metadados"]["sha256_protocolo"])
        self.assertEqual(hashlib.sha256(b[:i]).hexdigest(),
                         "e0b374608a1e4f5b4cae530931e4626f6f67c145d215212ea7ecd55b08da2490")
        blocos = [b"\n### Emenda " + x for x in b[i:].split(b"\n### Emenda ")[1:]]
        self.assertEqual(b"".join(blocos), b[i:])
        self.assertEqual([hashlib.sha256(x).hexdigest() for x in blocos], [
            # Emenda 2 (2026-09-28, operacional: uma empresa por processo; commit a83a78c)
            "71ec8fe82394fdd12a7f92870b05df4860df6ae959cdf8c9af2d7f967d3f6597",
            # Emenda 3 (2026-09-29, avaliação: temperatura efetiva, ambiente, uma métrica por chamada)
            "48631b58ecacc8f1d77bc4270e33df729713b086e855996b93e6732cc0878fb6",
            # Emenda 4 (2026-10-03, comportamento: apoio de LLM na anotação e PENDENTE_OPERACIONAL)
            "28265171c621fbfe9a93f301ae2de9c435c148d5f5cd7f73ceb1d357584f8beb",
            # Emenda 5 (2026-10-09, exatidão: rótulo ambivalente na regra de sinal, regra_sinal="emenda5")
            "49d133c2cf6b08d67e24f74847f90ae12db976cdf1dedd742d5f8b850d9d568d",
        ])

    def test_texto_pre_registrado_intacto(self):
        """Tudo antes de '## Emendas' é o texto do commit b17ea73; emendas só são acrescentadas."""
        with open(os.path.join(PASTA, "PROTOCOLO_RAGAS_TCC2.md"), "rb") as f:
            b = f.read()
        prefixo = b[:b.index("## Emendas".encode())]
        self.assertEqual(hashlib.sha256(prefixo).hexdigest(),
                         "32e6fef3df1f29ed3d479d0b5ae5f378a3fac78f39d3ce35384371c70000575a")

    def test_irbr3_e3_usa_so_a_conta_aplicacoes_financeiras(self):
        c = next(x for x in self.casos if x["id"] == "IRBR3_E3")
        self.assertEqual(len(c["valores_esperados"]), 1)
        v = c["valores_esperados"][0]
        self.assertEqual((v["fontes"], v["formas_alternativas"], v["valor_origem"]), (["1.01.02"], [], "4414934"))
        self.assertEqual([f["cd_conta"] for f in c["fontes_gabarito"]], ["1.01.02"])
        self.assertEqual(c["fontes_gabarito"][0]["ds_conta"], "Aplicações Financeiras")
        self.assertIn("ativo circulante", c["pergunta"])
        self.assertIn("Emenda 1", c["decisao_metodologica"]["referencia"])

    def test_nenhum_valor_monetario_exigido_abaixo_de_mil(self):
        """Regra A: inteiros < 1000 sem marca monetária são ignorados; nenhum valor exigido cai nessa faixa."""
        for c in self.casos:
            for v in itens_atomicos(c):
                if v["tipo"] == "monetario":
                    self.assertGreaterEqual(abs(Decimal(v["valor_origem"])), 1000, (c["id"], v["id"]))

    # 9–11
    def test_categorias_estruturas_e_disponibilidade_validas(self):
        for c in self.casos:
            self.assertIn(c["categoria"], CATEGORIAS)
            self.assertIn(c["estrutura"], ESTRUTURAS)
            self.assertEqual(c["estrutura"], self.pe[c["ticker"]]["estrutura"])
            self.assertIn(c["disponibilidade"], DISPONIBILIDADES)
            self.assertTrue(c["justificativa_disponibilidade"].strip(), c["id"])

    def test_estimativa_do_protocolo_registrada_e_divergencias_justificadas(self):
        for c in self.casos:
            est = self.prot["estimada"][c["ticker"]][c["categoria"]]
            self.assertEqual(c["disponibilidade_estimada_protocolo"], est, c["id"])
            self.assertEqual(c["divergencia_da_estimativa"], c["disponibilidade"] != est, c["id"])
            if c["divergencia_da_estimativa"]:
                self.assertTrue(c.get("justificativa_divergencia"), c["id"])

    # 12 — parseável e verificável sem LLM
    def test_valores_esperados_conferem_consigo_mesmos(self):
        """Uma resposta sintética com a apresentação de referência é CORRETO: o gabarito é verificável."""
        for c in self.casos:
            if not c["verificacao_deterministica_aplicavel"]:
                continue
            resp = "; ".join(v["apresentacao_referencia"] for v in c["valores_esperados"]) + "."
            self.assertEqual(X.classificar(resp, c)["classe"], X.CORRETO, (c["id"], resp))

    # 13
    def test_n4_nao_aplicavel_mas_presente_nos_96(self):
        n4 = [c for c in self.casos if c["categoria"] == "N4"]
        self.assertEqual(len(n4), 12)
        for c in n4:
            self.assertFalse(c["verificacao_deterministica_aplicavel"])
            self.assertEqual(c["valores_esperados"], [])
            self.assertEqual(X.classificar("R$ 1 bilhão", c)["classe"], X.NAO_APLICAVEL)
        self.assertTrue(all(c["verificacao_deterministica_aplicavel"] for c in self.casos if c["categoria"] != "N4"))

    # 14–16
    def test_sem_respostas_scores_ou_resultados(self):
        proibidas = [f"{cam}.{k}" for k, cam in chaves(self.ds) if k.lower() in CHAVES_PROIBIDAS]
        self.assertEqual(proibidas, [])
        texto = json.dumps(self.ds, ensure_ascii=False).lower()
        for termo in ('"faithfulness"', '"answer_relevancy"', '"resposta"', '"classe_exatidao"'):
            self.assertNotIn(termo, texto)

    def test_revisao_registrada_sem_resultado_experimental(self):
        for c in self.casos:
            r = c["revisao_tecnica"]
            self.assertIn("revisado", r)
            self.assertFalse(set(r) & CHAVES_PROIBIDAS)


if __name__ == "__main__":
    unittest.main()
