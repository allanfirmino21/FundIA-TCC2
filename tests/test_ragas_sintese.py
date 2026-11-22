# tests/test_ragas_sintese.py
#
# Cruzamentos da síntese integrada do TCC 2
# (avaliacao/ragas/avaliacao_tcc2/sintese/sintetizar_resultados_tcc2.py): reprodução byte a
# byte, integridade das fontes, consistência dos denominadores e separação das dimensões.
# Só lê artefatos congelados; não chama LLM nem RAGAS.

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "avaliacao", "ragas", "avaliacao_tcc2", "sintese")
SCRIPT = os.path.join(PASTA, "sintetizar_resultados_tcc2.py")
SAIDA = os.path.join(PASTA, "sintese_resultados_tcc2.json")

spec = importlib.util.spec_from_file_location("sintetizar_resultados_tcc2", SCRIPT)
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)

DISP = ("presente", "parcial", "ausente")
VERSOES = ("original", "emenda5")


def hashes_da_pasta() -> dict:
    out = {}
    for n in sorted(os.listdir(PASTA)):
        p = os.path.join(PASTA, n)
        if os.path.isfile(p):
            with open(p, "rb") as fh:
                out[n] = hashlib.sha256(fh.read()).hexdigest()
    return out


class SinteseTCC2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bytes_gerados = S.calcular()
        with open(SAIDA, "rb") as fh:
            cls.bytes_versionados = fh.read()
        cls.r = json.loads(cls.bytes_versionados)

    # reprodução e fontes
    def test_reproducao_byte_a_byte(self):
        self.assertEqual(self.bytes_gerados, self.bytes_versionados)

    def test_fontes_conferem_com_os_hashes_fixados(self):
        S.conferir_fontes()
        self.assertEqual(self.r["proveniencia"]["fontes_sha256"], S.FONTES)

    def test_verificar_nao_grava_nada(self):
        antes = hashes_da_pasta()
        p = subprocess.run([sys.executable, "-B", SCRIPT, "verificar"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        depois = hashes_da_pasta()
        self.assertEqual(antes, depois)

    def test_gerar_nao_sobrescreve(self):
        p = subprocess.run([sys.executable, "-B", SCRIPT, "gerar"], capture_output=True, text=True, encoding="utf-8")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("FileExistsError", p.stderr)

    # denominadores
    def test_denominadores_globais(self):
        d = self.r["denominadores"]
        self.assertEqual(d["casos"], 96)
        self.assertEqual(sum(d["disponibilidade"].values()), 96)
        self.assertEqual(d["disponibilidade"], {"presente": 69, "parcial": 15, "ausente": 12})
        self.assertEqual(d["ragas_validos"], {"faithfulness": 96, "answer_relevancy": 96})
        self.assertEqual(d["comportamento"], {"classificaveis": 91, "pendentes_operacionais": 5})
        self.assertEqual(d["truncadas_max_tokens"], 36)
        for v in VERSOES:
            e = self.r["distribuicoes_globais"]["exatidao"][v]
            self.assertEqual(sum(e[k] for k in S.CLASSES_EXATIDAO), 96)
            self.assertEqual(e["aplicaveis"], e["CORRETO"] + e["PARCIALMENTE_CORRETO"] + e["INCORRETO"])
            self.assertEqual(e["NAO_APLICAVEL"], e["nao_aplicavel_n4"] + e["nao_aplicavel_sem_numero"])
            self.assertEqual((e["aplicaveis"], e["nao_aplicavel_n4"], e["nao_aplicavel_sem_numero"]), (43, 12, 41))
        self.assertEqual(self.r["distribuicoes_globais"]["exatidao"]["original"]["correto_sobre_aplicaveis"], "31/43")
        self.assertEqual(self.r["distribuicoes_globais"]["exatidao"]["emenda5"]["correto_sobre_aplicaveis"], "37/43")

    def test_comportamento_classes_e_registro(self):
        c = self.r["distribuicoes_globais"]["comportamento"]
        self.assertEqual(c["classificaveis"] + len(c["pendentes_operacionais"]), 96)
        self.assertEqual(sum(c["classes"].values()) + c["registro_sem_desvio_presente"], 91)
        self.assertEqual(c["registro_sem_desvio_presente"], 69)
        a = c["abstencao_em_caso_presente"]
        self.assertEqual(a["n_presente"], 69)
        self.assertEqual(a["marcados"], a["com_entrega_informacao_sustentada"] + a["sem_entrega"])
        self.assertEqual((a["marcados"], a["com_entrega_informacao_sustentada"]), (34, 12))

    def test_recortes_por_disponibilidade_somam_o_global(self):
        pd = self.r["por_disponibilidade"]
        self.assertEqual(sum(pd[d]["n"] for d in DISP), 96)
        self.assertEqual(sum(pd[d]["truncadas"] for d in DISP), 36)
        for v in VERSOES:
            g = self.r["distribuicoes_globais"]["exatidao"][v]
            for k in S.CLASSES_EXATIDAO + ("aplicaveis", "nao_aplicavel_n4", "nao_aplicavel_sem_numero"):
                self.assertEqual(sum(pd[d]["exatidao"][v][k] for d in DISP), g[k], (v, k))
        for d in DISP:
            self.assertEqual(pd[d]["ragas"]["faithfulness"]["n"], pd[d]["n"])
            self.assertEqual(pd[d]["ragas"]["answer_relevancy"]["n"], pd[d]["n"])

    def test_ragas_por_classe_de_exatidao_soma_cada_recorte(self):
        for v in VERSOES:
            for rec in DISP + ("todos",):
                n_rec = 96 if rec == "todos" else self.r["por_disponibilidade"][rec]["n"]
                bloco = self.r["ragas_por_classe_exatidao"][v][rec]
                self.assertEqual(sum(bloco[cl]["n"] for cl in S.CLASSES_EXATIDAO), n_rec, (v, rec))
                for cl in S.CLASSES_EXATIDAO:
                    self.assertEqual(bloco[cl]["n"], self.r["por_disponibilidade"][rec]["exatidao"][v][cl]
                                     if rec != "todos" else self.r["distribuicoes_globais"]["exatidao"][v][cl])

    def test_estruturas_somam_o_global(self):
        pe = self.r["por_estrutura"]
        self.assertEqual(sum(pe[e]["n"] for e in S.ESTRUTURAS), 96)
        self.assertEqual({e: pe[e]["n"] for e in S.ESTRUTURAS},
                         {"nao_financeira": 64, "banco": 16, "holding": 8, "resseguradora": 8})
        for v in VERSOES:
            self.assertEqual(sum(pe[e]["exatidao_presente"][v]["n"] for e in S.ESTRUTURAS), 69)

    # Q5 e divergência conceitual
    def test_q5_segue_a_definicao_e_a_tabela_por_caso(self):
        casos = {c["id"]: c for c in self.r["casos"]}
        for v in VERSOES:
            q = self.r["q5"][v]
            self.assertEqual(q["n"], q["geracao"] + q["recuperacao"])
            esperado = [c["id"] for c in self.r["casos"]
                        if c["exatidao"][v]["classe"] in ("INCORRETO", "PARCIALMENTE_CORRETO")
                        or c["comportamento"]["classe"] in ("EXTRAPOLACAO", "ALUCINACAO")]
            self.assertEqual([x["id"] for x in q["casos"]], esperado)
            for x in q["casos"]:
                self.assertEqual(x["atribuicao"], "geracao" if casos[x["id"]]["disponibilidade"] == "presente" else "recuperacao")
        self.assertEqual((self.r["q5"]["original"]["n"], self.r["q5"]["original"]["geracao"]), (12, 8))
        self.assertEqual((self.r["q5"]["emenda5"]["n"], self.r["q5"]["emenda5"]["geracao"]), (6, 2))

    def test_divergencia_conceitual_q5_registrada_sem_alterar_classes(self):
        dv = self.r["q5"]["divergencia_conceitual"]
        self.assertEqual(sorted(dv["resposta_parcial_adequada"]), ["CEAB3_E2", "WEGE3_E2"])
        self.assertEqual(dv["sem_classe_de_comportamento"], ["ITSA4_E2"])
        for x in dv["casos"]:
            self.assertEqual(x["classe_exatidao"], "PARCIALMENTE_CORRETO")
            self.assertTrue(x["encontrados"] and x["nao_encontrados"])

    def test_parcialmente_corretos_truncados_presente(self):
        pc = self.r["parcialmente_corretos_truncados_presente"]["casos"]
        self.assertEqual(sorted(x["id"] for x in pc), ["ITUB4_N3", "ZAMP3_N3"])
        for x in pc:
            self.assertEqual((x["finish_reason"], x["truncada_por_limite"]), ("MAX_TOKENS", True))
            self.assertTrue(any(v["conferido"] for v in x["valores_exigidos"]))
            self.assertTrue(any(not v["conferido"] for v in x["valores_exigidos"]))

    # separação das dimensões e equivalência dos pendentes
    def test_dimensoes_separadas_e_classes_existentes(self):
        for c in self.r["casos"]:
            self.assertEqual(set(c), {"id", "ticker", "estrutura", "categoria", "disponibilidade", "truncada_na_geracao",
                                      "comportamento", "exatidao", "ragas"})
            self.assertIn(c["comportamento"]["classe"], S.CLASSES_COMPORTAMENTO + (S.SEM_DESVIO, None))
            for v in VERSOES:
                self.assertIn(c["exatidao"][v]["classe"], S.CLASSES_EXATIDAO)
            if c["comportamento"]["classe"] == S.SEM_DESVIO:
                self.assertEqual(c["disponibilidade"], "presente")

    def test_equivalencia_dos_pendentes_de_comportamento(self):
        eq = self.r["equivalencia_pendentes_comportamento"]
        self.assertEqual(sorted(eq["ids"]), ["AURE3_E3", "AURE3_N2", "ITSA4_E2", "LAVV3_E2", "ZAMP3_E2"])
        pend = [c for c in self.r["casos"] if c["comportamento"]["situacao"] == S.PENDENTE]
        self.assertEqual(sorted(c["id"] for c in pend), sorted(eq["ids"]))
        self.assertTrue(all(c["comportamento"]["classe"] is None and c["truncada_na_geracao"] for c in pend))


if __name__ == "__main__":
    unittest.main()
