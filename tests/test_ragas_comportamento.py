# tests/test_ragas_comportamento.py
#
# Regra de decisão da rubrica de comportamento do RAGAS do TCC 2
# (avaliacao/ragas/comportamento.py). Registros sintéticos: não há respostas
# reais classificadas.

import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "avaliacao", "ragas"))

import comportamento as C  # noqa: E402


def reg(disp, rotulos, limitacao=False, entrega=False, classe=None, abst=False, **extra):
    r = {"id": "X_N2", "disponibilidade": disp, "sha256_resposta": "0" * 64,
         "afirmacoes": [{"trecho_resposta": f"a{i}", "rotulo": r, "evidencia_contexto": "linha",
                         "motivo": "m"} for i, r in enumerate(rotulos)],
         "declara_limitacao": limitacao, "entrega_informacao_sustentada": entrega,
         "classe": classe, "abstencao_em_caso_presente": abst, "justificativa": "j",
         "classificador": "autor", "classificado_em": "2026-10-01T00:00:00Z",
         "scores_ragas_consultados": False}
    r.update(extra)
    return r


CASO = {"id": "X_N2"}


class Derivacao(unittest.TestCase):
    def test_gravidade(self):
        for disp in ("presente", "parcial", "ausente"):
            self.assertEqual(C.derivar_classe(disp, ["S", "E", "A"], True, True)[0], C.ALUCINACAO)
            self.assertEqual(C.derivar_classe(disp, ["S", "E", "N"], True, True)[0], C.EXTRAPOLACAO)

    def test_presente_nao_e_adequado_automaticamente(self):
        self.assertEqual(C.derivar_classe("presente", ["S", "E"], False, True)[0], C.EXTRAPOLACAO)
        self.assertEqual(C.derivar_classe("presente", ["S", "N"], False, True), (C.SEM_DESVIO, False))
        self.assertEqual(C.derivar_classe("presente", [], True, False), (C.SEM_DESVIO, True))

    def test_parcial(self):
        self.assertEqual(C.derivar_classe("parcial", ["S"], True, True)[0], C.RESPOSTA_PARCIAL_ADEQUADA)
        self.assertEqual(C.derivar_classe("parcial", [], True, False)[0], C.ABSTENCAO_ADEQUADA)

    def test_ausente(self):
        self.assertEqual(C.derivar_classe("ausente", [], True, False)[0], C.ABSTENCAO_ADEQUADA)
        self.assertEqual(C.derivar_classe("ausente", ["S"], True, True)[0], C.ABSTENCAO_ADEQUADA)

    def test_parcial_ou_ausente_sem_declaracao_e_sem_desvio_e_inconsistente(self):
        for disp in ("parcial", "ausente"):
            with self.assertRaises(C.RegistroInconsistente):
                C.derivar_classe(disp, ["S"], False, True)


class Validacao(unittest.TestCase):
    def test_registro_valido(self):
        C.validar_registro(reg("parcial", ["S"], True, True, C.RESPOSTA_PARCIAL_ADEQUADA),
                           {**CASO, "disponibilidade": "parcial"})

    def test_classe_divergente_da_derivada(self):
        with self.assertRaises(C.RegistroInconsistente):
            C.validar_registro(reg("parcial", ["S", "E"], True, True, C.RESPOSTA_PARCIAL_ADEQUADA),
                               {**CASO, "disponibilidade": "parcial"})

    def test_classe_nao_admitida(self):
        with self.assertRaises(C.RegistroInconsistente):
            C.validar_registro(reg("ausente", ["S"], True, True, C.RESPOSTA_PARCIAL_ADEQUADA),
                               {**CASO, "disponibilidade": "ausente"})

    def test_scores_ragas_consultados_recusa(self):
        with self.assertRaises(C.RegistroInconsistente):
            C.validar_registro(reg("presente", ["S"], classe=C.SEM_DESVIO, scores_ragas_consultados=True),
                               {**CASO, "disponibilidade": "presente"})

    def test_disponibilidade_diferente_do_dataset(self):
        with self.assertRaises(C.RegistroInconsistente):
            C.validar_registro(reg("presente", ["S"], classe=C.SEM_DESVIO), {**CASO, "disponibilidade": "ausente"})

    def test_afirmacao_e_sem_motivo(self):
        r = reg("presente", ["E"], classe=C.EXTRAPOLACAO)
        r["afirmacoes"][0]["motivo"] = ""
        with self.assertRaises(C.RegistroInconsistente):
            C.validar_registro(r, {**CASO, "disponibilidade": "presente"})

    def test_quatro_classes_do_protocolo(self):
        self.assertEqual(set(C.CLASSES), {"ABSTENCAO_ADEQUADA", "RESPOSTA_PARCIAL_ADEQUADA",
                                          "EXTRAPOLACAO", "ALUCINACAO"})
        self.assertNotIn(C.SEM_DESVIO, C.CLASSES)


if __name__ == "__main__":
    unittest.main()
