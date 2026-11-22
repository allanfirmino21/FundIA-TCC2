# tests/test_ragas_avaliacao_ambiente.py
#
# Adaptador RAGAS real do executor da avaliação (AvaliadorRagas), no ambiente da Emenda 3
# (venv com requirements_avaliacao.txt). Usa um modelo de chat FALSO do langchain no lugar
# do Gemini: sem rede, sem API e sem respostas reais. No ambiente principal, onde o ragas
# não está instalado, estes testes são pulados.

import importlib.util
import itertools
import json
import math
import os
import socket
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "avaliacao", "ragas"))

import avaliar_respostas_tcc2 as A  # noqa: E402

TEM_RAGAS = importlib.util.find_spec("ragas") is not None
CHAVE_FALSA = "chave-falsa-de-teste-" + "0123456789abcdef" * 2
_connect = socket.socket.connect


def _so_loopback(self, addr, *a, **k):          # o asyncio do Windows usa socketpair em 127.0.0.1
    if isinstance(addr, tuple) and addr[0] in ("127.0.0.1", "::1"):
        return _connect(self, addr, *a, **k)
    raise AssertionError("acesso à rede durante os testes do ambiente de avaliação")


def _sem_rede(*a, **k):
    raise AssertionError("acesso à rede durante os testes do ambiente de avaliação")


_originais = (socket.socket.connect, socket.create_connection, socket.getaddrinfo)


def setUpModule():
    socket.socket.connect, socket.create_connection, socket.getaddrinfo = _so_loopback, _sem_rede, _sem_rede


def tearDownModule():
    socket.socket.connect, socket.create_connection, socket.getaddrinfo = _originais


@unittest.skipUnless(TEM_RAGAS, "ragas não instalado: rodar no venv da Emenda 3")
class AdaptadorRagas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
        from langchain_core.messages import AIMessage

        class GeminiFalso(GenericFakeChatModel):
            temperature: float = 0.0
            n: int = 1
            chamadas: list = []
            falhar: bool = False

            def _generate(self, messages, stop=None, run_manager=None, **kw):
                self.chamadas.append((self.temperature, self.n))
                if self.falhar:
                    raise RuntimeError(f"503 UNAVAILABLE key={CHAVE_FALSA}")
                return super()._generate(messages, stop=stop, run_manager=run_manager, **kw)

        cls.GeminiFalso, cls.AIMessage = GeminiFalso, AIMessage
        cls.amostra = {"user_input": "Qual foi a receita?", "response": "A receita foi R$ 1 mil.",
                       "retrieved_contexts": ["Trecho A", "Trecho B", "Trecho C"], "reference": "gabarito"}

    def avaliador(self, saidas, falhar=False):
        chat = self.GeminiFalso(messages=iter([self.AIMessage(content=s) for s in saidas]) if isinstance(saidas, list)
                                else itertools.repeat(self.AIMessage(content=saidas)), temperature=0.0, falhar=falhar)
        chat.chamadas = []
        return A.AvaliadorRagas(CHAVE_FALSA, chat=chat), chat

    def test_ambiente_da_emenda_3(self):
        amb = A.verificar_ambiente()
        self.assertEqual(amb["problemas"], [])
        self.assertEqual(amb["revisoes_embeddings"], [A.REVISAO_EMBEDDINGS])

    def test_faithfulness_temperatura_efetiva_001(self):
        av, chat = self.avaliador([json.dumps({"statements": ["A receita foi R$ 1 mil."]}),
                                   json.dumps({"statements": [{"statement": "A receita foi R$ 1 mil.",
                                                               "reason": "ok", "verdict": 1}]})])
        self.assertEqual(os.environ["RAGAS_DO_NOT_TRACK"], "true")
        r = av.avaliar("faithfulness", self.amostra)
        self.assertEqual((r["score"], r["erros"]), (1.0, []))
        self.assertEqual(set(chat.chamadas), {(0.01, 1)})
        self.assertEqual(chat.temperature, 0.0)

    def test_answer_relevancy_temperatura_efetiva_03_com_3_perguntas(self):
        av, chat = self.avaliador(json.dumps({"question": "Qual foi a receita?", "noncommittal": 0}))
        r = av.avaliar("answer_relevancy", self.amostra)
        self.assertAlmostEqual(r["score"], 1.0, places=6)
        self.assertEqual(set(chat.chamadas), {(0.3, 3)})
        self.assertEqual(av.descricao()["strictness"], 3)

    def test_resposta_evasiva_recebe_zero(self):
        av, _ = self.avaliador(json.dumps({"question": "Qual foi a receita?", "noncommittal": 1}))
        self.assertEqual(av.avaliar("answer_relevancy", self.amostra)["score"], 0.0)

    def test_erro_da_api_vira_nan_registrado_sem_chave(self):
        av, _ = self.avaliador("x", falhar=True)
        r = av.avaliar("faithfulness", self.amostra)
        self.assertTrue(math.isnan(r["score"]))
        self.assertTrue(r["erros"])
        self.assertNotIn(CHAVE_FALSA, json.dumps(r["erros"]))

    def test_descricao_registra_versoes_e_parametros(self):
        av, _ = self.avaliador("x")
        d = av.descricao()
        self.assertEqual((d["modelo"], d["temperatura_cliente"], d["run_config"]),
                         ("gemini-2.5-flash", 0.0, {"timeout": 120, "max_retries": 3, "max_workers": 1}))
        self.assertEqual({p: d["dependencias"][p] for p in A.VERSOES_FIXADAS}, A.VERSOES_FIXADAS)


if __name__ == "__main__":
    unittest.main()
