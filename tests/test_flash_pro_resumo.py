# tests/test_flash_pro_resumo.py
#
# Resumo reprodutível do experimento Flash × Pro pré-registrado
# (avaliacao/flash_pro/resumir_experimento_flash_pro.py): reprodução, integridade das fontes,
# critérios pré-registrados e robustez ao incidente de coleta. Só lê artefatos congelados.

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "avaliacao", "flash_pro")
SCRIPT = os.path.join(PASTA, "resumir_experimento_flash_pro.py")
SAIDA = os.path.join(PASTA, "resumo_experimento_flash_pro.json")


def carregar_modulo():
    spec = importlib.util.spec_from_file_location("resumir_experimento_flash_pro", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def hashes_da_pasta():
    out = {}
    for n in sorted(os.listdir(PASTA)):
        p = os.path.join(PASTA, n)
        if os.path.isfile(p):
            with open(p, "rb") as fh:
                out[n] = hashlib.sha256(fh.read()).hexdigest()
    return out


class ResumoFlashPro(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.R = carregar_modulo()
        cls.gerado = cls.R.calcular()
        with open(SAIDA, "rb") as fh:
            cls.versionado = fh.read()
        cls.r = json.loads(cls.versionado)

    def test_reproducao(self):
        self.assertEqual(self.R.lf(self.versionado), self.gerado)

    def test_fontes_conferem(self):
        self.R.conferir_fontes()
        self.assertEqual(self.r["proveniencia"]["fontes_sha256"], self.R.FONTES)

    def test_verificar_nao_grava_e_gerar_nao_sobrescreve(self):
        antes = hashes_da_pasta()
        p = subprocess.run([sys.executable, "-B", SCRIPT, "verificar", "--saida", PASTA],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(antes, hashes_da_pasta())
        p = subprocess.run([sys.executable, "-B", SCRIPT, "gerar", "--saida", PASTA],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("FileExistsError", p.stderr)

    def test_integridade_pre_registrada(self):
        i = self.r["integridade"]
        self.assertEqual(i["celulas"], 20)
        self.assertTrue(i["celulas_unicas_iguais_ao_desenho"])
        self.assertEqual(i["finish_reason"], ["STOP"])
        for k in ("hash_documento_igual_manifesto", "hash_contexto_unico_por_empresa", "hash_contexto_igual_manifesto",
                  "hash_prompt_unico_por_empresa_entre_bracos", "intercalacao_flash1_pro1_flash2_pro2"):
            self.assertTrue(i[k], k)
        self.assertEqual(i["inconsistencias_csv_json"], [])

    def test_denominadores_das_verificacoes(self):
        t = self.r["contagens_verificacoes"]["total"]
        self.assertEqual(t["entradas"], 564)
        self.assertEqual(t["por_veredito"], {"CONFERE": 541, "DIVERGENTE": 1, "NAO_ENCONTRADO": 1, "IGNORADO": 21})
        self.assertEqual(t["denominador_total_numeros"], 543)
        for b, n in (("flash", 325), ("pro", 218)):
            self.assertEqual(self.r["contagens_verificacoes"][b]["denominador_total_numeros"], n)
            self.assertEqual(self.r["resultado"]["fidelidade"]["agregado"][b]["total_numeros"], n)

    def test_auditor_e_estado_do_pipeline(self):
        self.assertTrue(self.r["desenho"]["auditor"].startswith("1.0"))
        self.assertIn("anterior às correções do TCC 2", self.r["desenho"]["estado_do_pipeline"])

    def test_criterios_e_veredito(self):
        f, c = self.r["resultado"]["fidelidade"], self.r["resultado"]["cobertura"]
        self.assertEqual((c["diferenca_relativa_sobre_maior"], c["diferenca_relativa_sobre_menor"]), (0.3846, 0.625))
        self.assertFalse(c["criterio_satisfeito_base_menor"])
        self.assertEqual((f["agregado"]["flash"]["conferem"], f["agregado"]["flash"]["total_numeros"]), (323, 325))
        self.assertEqual((f["agregado"]["pro"]["conferem"], f["agregado"]["pro"]["total_numeros"]), (218, 218))
        self.assertTrue(f["criterio_satisfeito"])
        self.assertEqual((f["pior_empresa"], f["pior_diferenca_pp"]), ("ZAMP3", 1.5625))
        self.assertEqual(c["mediana_total_numeros"], {"flash": 32.5, "pro": 20.0})
        self.assertFalse(c["criterio_satisfeito"])
        self.assertEqual(self.r["veredito"], "nao_equivalentes_pelo_criterio_pre_registrado")

    def test_veredito_robusto_ao_incidente(self):
        inc = self.r["incidente_de_coleta"]
        self.assertTrue(inc["versionadas_mais_descartadas_igual_bruto"])
        self.assertEqual(inc["selecoes_possiveis"], 256)
        self.assertEqual(inc["selecoes_equivalentes"], 0)
        self.assertEqual(inc["selecoes_com_cobertura_satisfeita"], 0)
        self.assertEqual(inc["selecoes_com_cobertura_satisfeita_base_menor"], 0)
        self.assertEqual(inc["selecoes_com_fidelidade_satisfeita"], 256)


if __name__ == "__main__":
    unittest.main()
