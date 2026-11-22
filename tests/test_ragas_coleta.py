# tests/test_ragas_coleta.py
#
# Executor da coleta do RAGAS do TCC 2 (avaliacao/ragas/coletar_respostas_tcc2.py).
# Sem rede e sem API: o socket é bloqueado durante todo o módulo; recuperador,
# gerador e git são falsos; toda saída vai para diretórios temporários. Nenhuma
# resposta experimental real é criada.

import ast
import copy
import hashlib
import importlib.util
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "avaliacao", "ragas")
sys.path.insert(0, PASTA)

import coletar_respostas_tcc2 as C  # noqa: E402

CONGELADOS = ("dataset_tcc2.json", "dataset_tcc2_revisao.csv", "revisao_tecnica_tcc2.json",
              "PROTOCOLO_RAGAS_TCC2.md", "RUBRICA_COMPORTAMENTO_TCC2.md", "RELATORIO_fechamento_dataset.md",
              "exatidao.py", "comportamento.py", "validar_dataset.py", "construir_dataset.py")
# Chaves falsas montadas em tempo de execução (o fonte não contém nada com formato de chave)
CHAVE_FALSA = "chave-falsa-de-teste-" + "0123456789abcdef" * 2
SEP = "-" * 40


class RedeProibida(AssertionError):
    pass


def _sem_rede(*a, **k):
    raise RedeProibida("acesso à rede durante os testes da coleta")


_patches = [mock.patch.object(socket.socket, "connect", _sem_rede),
            mock.patch.object(socket, "create_connection", _sem_rede),
            mock.patch.object(socket, "getaddrinfo", _sem_rede)]

# Depois da coleta, o protocolo recebeu a Emenda 2 (operacional, commit a83a78c). O executor
# congelado (fb13ba8) continua exigindo, byte a byte, a versão com que a coleta foi feita
# (SHA256_PROTOCOLO_CONGELADO, o hash registrado no dataset). Como o protocolo só recebe
# acréscimos, essa versão é exatamente o trecho do arquivo atual antes da Emenda 2: os testes
# do executor usam esse trecho, conferido pelo hash. Que o executor recusa o protocolo
# emendado está em ProtocoloEmendado.
PROTOCOLO_EMENDADO = C.PROTOCOLO
_dir_protocolo = None


def protocolo_da_coleta() -> bytes:
    with open(PROTOCOLO_EMENDADO, "rb") as f:
        b = f.read()
    return b[:b.index(b"\n### Emenda 2")]


def setUpModule():
    global _dir_protocolo
    congelado = protocolo_da_coleta()
    if sha(congelado) != C.SHA256_PROTOCOLO_CONGELADO:
        raise AssertionError("o protocolo antes da Emenda 2 não é a versão congelada da coleta")
    _dir_protocolo = tempfile.TemporaryDirectory()
    caminho = os.path.join(_dir_protocolo.name, "PROTOCOLO_RAGAS_TCC2.md")
    with open(caminho, "wb") as f:
        f.write(congelado)
    _patches.append(mock.patch.object(C, "PROTOCOLO", caminho))
    for p in _patches:
        p.start()


def tearDownModule():
    for p in _patches:
        p.stop()
    _dir_protocolo.cleanup()


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def hashes_congelados() -> dict:
    out = {}
    for n in CONGELADOS:
        with open(os.path.join(PASTA, n), "rb") as f:
            out[n] = sha(f.read())
    return out


def contexto_falso(tk: str) -> str:
    """Mesmo formato de recuperacao._formatar_contexto; linhas neutras, sem valores do gabarito."""
    trechos = [f"[TABELA | Tabela Fictícia {i} (Consolidado)]\nConta Fictícia {tk} {i}   {i}1.111  (anterior: {i}2.222)"
               for i in (1, 2, 3)]
    blocos = [f"[Trecho {i + 1}]\n{c}" for i, c in enumerate(trechos)]
    return f"=== CONTEXTO TABELA ===\n{SEP}\n" + f"\n{SEP}\n".join(blocos) + f"\n{SEP}"


class RecuperadorFalso:
    def __init__(self, ctxs, versoes_ok=True):
        self.ctxs, self.versoes_ok = dict(ctxs), versoes_ok
        self.preparados, self.recuperacoes = [], 0

    def verificar_versoes(self, empresas):
        return [] if self.versoes_ok else ["WEGE3: versão mais recente 2, registrada 1"]

    def preparar(self, emp):
        self.preparados.append(emp["ticker"])
        return emp["sha256_documento"]

    def recuperar(self, emp):
        self.recuperacoes += 1
        return {"ctx_num": self.ctxs[emp["ticker"]], "ids": [f"p0_tab_{i}" for i in range(3)]}


class GeradorFalso:
    def __init__(self, falhar_em=(), sem_texto_em=(), excecao=None):
        self.reqs, self.falhar_em, self.sem_texto_em = [], set(falhar_em), set(sem_texto_em)
        self.excecao = excecao or RuntimeError("503 UNAVAILABLE")

    def __call__(self, req):
        self.reqs.append(req)
        n = len(self.reqs)
        if n in self.falhar_em:
            raise self.excecao
        if n in self.sem_texto_em:
            return {"texto": None, "modelo_retornado": "fake", "finish_reason": "MAX_TOKENS", "uso_tokens": None}
        return {"texto": f"  Resposta sintética {n}.  ", "modelo_retornado": "gemini-2.5-flash-fake",
                "finish_reason": "STOP", "uso_tokens": {"prompt_token_count": 10, "candidates_token_count": 5,
                                                        "thoughts_token_count": 0, "total_token_count": 15}}


class GitFalso:
    def __init__(self, head="f" * 40, pendencias=(), descende=True, alterados=()):
        self._head, self._pend, self._desc, self._alt = head, list(pendencias), descende, list(alterados)

    def head(self):
        return self._head

    def pendencias(self):
        return self._pend

    def descende_de(self, commit):
        return self._desc

    def alterados_desde(self, commit):
        return self._alt


class Base(unittest.TestCase):
    """Dataset temporário: cópia do congelado com os SHA-256 do contexto falso."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.tmp = self._tmp.name
        with open(C.DATASET, encoding="utf-8") as f:
            ds = json.load(f)
        self.ctxs = {tk: contexto_falso(tk) for tk in ds["empresas"]}
        for tk, e in ds["empresas"].items():
            e["contexto_recuperado"]["sha256_ctx_num"] = C.sha256_texto(self.ctxs[tk])
            e["contexto_recuperado"]["sha256_trechos"] = [C.sha256_texto(t) for t in C.extrair_chunks(self.ctxs[tk])]
        self.ds_obj = ds
        self.ds_path = os.path.join(self.tmp, "dataset.json")
        self._gravar_ds(ds)
        self.saida = os.path.join(self.tmp, "coleta")

    def tearDown(self):
        self._tmp.cleanup()

    def _gravar_ds(self, ds):
        with open(self.ds_path, "w", encoding="utf-8") as f:
            json.dump(ds, f, ensure_ascii=False, indent=1)
        with open(self.ds_path, "rb") as f:
            self.ds_sha = sha(f.read())

    def coletar(self, gerador=None, rec=None, git=None, **kw):
        kw.setdefault("sha_dataset_esperado", self.ds_sha)
        kw.setdefault("log", lambda *a: None)
        return C.coletar(recuperador=rec or RecuperadorFalso(self.ctxs), gerador=gerador or GeradorFalso(),
                         git=git or GitFalso(), dataset_path=self.ds_path, saida=self.saida, **kw)

    def ler(self, nome):
        with open(os.path.join(self.saida, nome), encoding="utf-8") as f:
            return json.load(f)

    def texto_de_tudo(self):
        partes = []
        for raiz, _, arqs in os.walk(self.saida):
            for a in arqs:
                with open(os.path.join(raiz, a), encoding="utf-8", errors="replace") as f:
                    partes.append(f.read())
        return "\n".join(partes)

    def cfg(self):
        ds, s = C.carregar_dataset(self.ds_path)
        return C.sha_config(C.configuracao(ds, s))


# 1–2 ──────────────────────────────────────────────────────────────────────────
class DatasetEOrdem(unittest.TestCase):
    def test_carrega_exatamente_os_96_casos_congelados(self):
        ds, s = C.carregar_dataset(C.DATASET)
        self.assertEqual(s, C.SHA256_DATASET_CONGELADO)
        self.assertEqual(len(ds["casos"]), 96)
        self.assertEqual(len(ds["empresas"]), 12)
        self.assertEqual(dict(C.Counter(c["disponibilidade"] for c in ds["casos"])), C.DISTRIBUICAO_ESPERADA)

    def test_ordem_deterministica_e_congelada(self):
        ds, s = C.carregar_dataset(C.DATASET)
        o1, o2 = C.ordem_execucao(ds), C.ordem_execucao(copy.deepcopy(ds))
        self.assertEqual(o1, o2)
        self.assertEqual(o1, [c["id"] for c in ds["casos"]])
        self.assertEqual((o1[0], o1[-1], len(set(o1))), ("WEGE3_N1", "AURE3_E3", 96))
        self.assertEqual(C.configuracao(ds, s)["ordem_casos"], o1)

    def test_dataset_invalido_e_recusado(self):
        with open(C.DATASET, encoding="utf-8") as f:
            ds = json.load(f)
        ds["casos"] = ds["casos"][:95]
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "d.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump(ds, f)
            with self.assertRaises(C.Bloqueio):
                C.carregar_dataset(p)


# 3–4 ──────────────────────────────────────────────────────────────────────────
class ProtecaoContraChamadaReal(Base):
    def _boom(self, *a, **k):
        raise AssertionError("fábrica do gerador real chamada")

    def test_dry_run_nao_chama_gemini_nem_grava(self):
        zipf = os.path.join(self.tmp, "falso.zip")
        with open(zipf, "wb") as f:
            f.write(b"zip falso")
        rec = RecuperadorFalso(self.ctxs)
        with mock.patch("google.genai.Client", side_effect=AssertionError("cliente real")) as cli, \
                mock.patch("builtins.print") as pr:
            rc = C.main(["--dry-run", "--zip", zipf, "--saida", self.saida],
                        fabrica_recuperador=lambda z, t: rec, fabrica_gerador=self._boom, git=GitFalso(),
                        dataset_path=self.ds_path, sha_dataset_esperado=self.ds_sha)
        self.assertEqual(rc, 0)
        cli.assert_not_called()
        self.assertEqual(len(rec.preparados), 12)
        self.assertIn("96 casos prontos", " ".join(str(c) for c in pr.call_args_list))
        self.assertFalse(os.path.exists(self.saida))
        self.assertFalse(C._EXECUCAO_REAL_AUTORIZADA)

    def test_dry_run_valida_96_casos(self):
        r = C.dry_run(recuperador=RecuperadorFalso(self.ctxs), git=GitFalso(), dataset_path=self.ds_path,
                      sha_dataset_esperado=self.ds_sha, log=lambda *a: None)
        self.assertEqual(len(r["prontos"]), 96)
        self.assertEqual(r["prontos"], C.ordem_execucao(self.ds_obj))
        self.assertFalse(os.path.exists(self.saida))

    def test_dry_run_detecta_recuperacao_instavel(self):
        class Instavel(RecuperadorFalso):
            def recuperar(self, emp):
                r = super().recuperar(emp)
                if self.recuperacoes == 2:
                    r = dict(r, ctx_num=r["ctx_num"].replace("1.111", "9.999"))
                return r

        with self.assertRaisesRegex(C.Bloqueio, "contexto recuperado difere"):
            C.dry_run(recuperador=Instavel(self.ctxs), dataset_path=self.ds_path,
                      sha_dataset_esperado=self.ds_sha, log=lambda *a: None)

    def test_sem_execute_nada_e_chamado(self):
        with mock.patch("builtins.print"):
            self.assertEqual(C.main([], fabrica_gerador=self._boom, fabrica_recuperador=self._boom), 2)
            self.assertEqual(C.main(["--zip", "x.zip", "--limit", "1"], fabrica_gerador=self._boom,
                                    fabrica_recuperador=self._boom), 2)
        with mock.patch("sys.stderr"), self.assertRaises(SystemExit):
            C.main(["--dry-run", "--execute"], fabrica_gerador=self._boom)

    def test_cliente_real_proibido_fora_de_execute(self):
        self.assertFalse(C._EXECUCAO_REAL_AUTORIZADA)
        with mock.patch("google.genai.Client") as cli:
            with self.assertRaises(C.ChamadaRealProibida):
                C.GeradorGemini(os.path.join(self.tmp, "nao_existe.txt"))
            cli.assert_not_called()
        with self.assertRaises(C.ChamadaRealProibida):
            C.gerador_proibido({})

    def test_gerador_proibido_interrompe_a_coleta(self):
        with self.assertRaises(C.ChamadaRealProibida):
            self.coletar(gerador=C.gerador_proibido)
        self.assertEqual(os.listdir(os.path.join(self.saida, "respostas")), [])
        self.assertEqual(self.ler("estado_coleta.json")["execucoes"][0]["encerramento"], "proibida")


# 5–7 ──────────────────────────────────────────────────────────────────────────
class Payload(Base):
    def test_gerador_recebe_pergunta_e_contexto_corretos(self):
        g = GeradorFalso()
        self.coletar(gerador=g)
        casos = {c["id"]: c for c in self.ds_obj["casos"]}
        self.assertEqual(len(g.reqs), 96)
        for req, cid in zip(g.reqs, C.ordem_execucao(self.ds_obj)):
            c = casos[cid]
            self.assertEqual(req["contents"], C.montar_prompt(self.ctxs[c["ticker"]], c["pergunta"]))
            self.assertEqual(req, C.montar_requisicao(c, self.ctxs[c["ticker"]]))

    def test_payload_contem_somente_o_permitido(self):
        c = self.ds_obj["casos"][0]
        req = C.montar_requisicao(c, self.ctxs["WEGE3"])
        self.assertEqual(set(req), {"model", "contents", "config"})
        self.assertEqual(req["model"], "gemini-2.5-flash")
        self.assertEqual(req["config"], {"temperature": 0.1, "max_output_tokens": 1024})
        resto = req["contents"].replace(self.ctxs["WEGE3"], "").replace(c["pergunta"], "")
        self.assertEqual(resto, C.PROMPT_MODELO.format(contexto="", pergunta=""))

    def test_gabarito_nao_vaza_para_o_prompt(self):
        for c in self.ds_obj["casos"]:
            p = C.montar_requisicao(c, self.ctxs[c["ticker"]])["contents"]
            for t in (c["gabarito"], c["justificativa_disponibilidade"], c["revisao_tecnica"].get("observacao"),
                      c["revisao_tecnica"].get("atencao_humana"), json.dumps(c.get("decisao_metodologica"))):
                if t and t != "null":
                    self.assertNotIn(t, p, c["id"])
            for v in c["valores_esperados"]:
                self.assertNotIn(v["apresentacao_referencia"], p, c["id"])
                if v["tipo"] == "monetario":
                    self.assertNotIn(f"{abs(int(v['valor_origem'])):,}".replace(",", "."), p, c["id"])
            C.verificar_requisicao(C.montar_requisicao(c, self.ctxs[c["ticker"]]), c, self.ctxs[c["ticker"]])
        c = next(x for x in self.ds_obj["casos"] if x["id"] == "IRBR3_E3")
        adulterada = C.montar_requisicao(c, self.ctxs["IRBR3"])
        adulterada["contents"] += "\n" + c["gabarito"]
        with self.assertRaises(C.Bloqueio):
            C.verificar_requisicao(adulterada, c, self.ctxs["IRBR3"])

    def test_disponibilidade_nao_vaza_para_o_prompt(self):
        for c in self.ds_obj["casos"]:
            p = C.montar_requisicao(c, self.ctxs[c["ticker"]])["contents"].lower()
            self.assertNotIn("disponibilidade", p)
            self.assertNotIn(c["disponibilidade"], p, c["id"])
        c = next(x for x in self.ds_obj["casos"] if x["disponibilidade"] == "ausente")
        adulterada = C.montar_requisicao(c, self.ctxs[c["ticker"]])
        adulterada["contents"] = adulterada["contents"].replace("## PERGUNTA", "Disponibilidade: ausente\n## PERGUNTA")
        with self.assertRaises(C.Bloqueio):
            C.verificar_requisicao(adulterada, c, self.ctxs[c["ticker"]])
        # a disponibilidade existe no artefato só como metadado
        self.coletar(case_ids=[c["id"]])
        r = self.ler(f"respostas/{c['id']}.json")
        self.assertEqual(r["disponibilidade_congelada"], "ausente")
        self.assertNotIn("ausente", r["requisicao"]["prompt"].lower())

    def test_prompt_identico_ao_do_tcc1(self):
        """Mesmos model, contents, temperature e max_output_tokens que perguntar() do TCC 1 enviaria."""
        spec = importlib.util.spec_from_file_location("_tcc1_teste", C.COLETOR_TCC1)
        tcc1 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tcc1)
        capturado = {}

        class Cliente:
            class models:
                @staticmethod
                def generate_content(**kw):
                    capturado.update(kw)
                    return type("R", (), {"text": " ok "})()

        c = self.ds_obj["casos"][10]
        tcc1.perguntar(self.ctxs[c["ticker"]], c["pergunta"], Cliente())
        req = C.montar_requisicao(c, self.ctxs[c["ticker"]])
        self.assertEqual(capturado["model"], req["model"])
        self.assertEqual(capturado["contents"], req["contents"])
        self.assertEqual((capturado["config"].temperature, capturado["config"].max_output_tokens),
                         (req["config"]["temperature"], req["config"]["max_output_tokens"]))

        # e o cliente real deste executor envia exatamente o mesmo (cliente do SDK substituído)
        chave = os.path.join(self.tmp, "chave.txt")
        with open(chave, "w") as f:
            f.write(CHAVE_FALSA)
        enviado = {}

        class ClienteSDK:
            def __init__(self, api_key):
                self.models = self

            def generate_content(self, **kw):
                enviado.update(kw)
                return type("R", (), {"text": "ok", "model_version": "v", "candidates": [], "usage_metadata": None})()

        with mock.patch.object(C, "_EXECUCAO_REAL_AUTORIZADA", True), mock.patch("google.genai.Client", ClienteSDK):
            g = C.GeradorGemini(chave)
            self.assertNotIn(CHAVE_FALSA, repr(g))
            g(req)
        self.assertEqual((enviado["model"], enviado["contents"]), (capturado["model"], capturado["contents"]))
        self.assertEqual(enviado["config"].model_dump(exclude_none=True), capturado["config"].model_dump(exclude_none=True))

    def test_prompt_igual_ao_citado_no_protocolo(self):
        with open(C.PROTOCOLO, encoding="utf-8") as f:
            t = f.read()
        bloco = re.search(r"^  > Você é um analista.*?^  > \{pergunta\}$", t, re.M | re.S).group(0)
        citado = " ".join(re.sub(r"^  >", "", l).strip() for l in bloco.splitlines()).split()
        modelo = C.PROMPT_MODELO.format(contexto="{contexto numérico}", pergunta="{pergunta}").split()
        self.assertEqual(citado, modelo)


class ProtocoloEmendado(unittest.TestCase):
    """Com o protocolo emendado após a coleta, o executor congelado não valida nem gera nada."""

    def test_executor_recusa_o_protocolo_emendado(self):
        ds, _ = C.carregar_dataset(C.DATASET)
        C.verificar_protocolo(ds)                                   # versão da coleta: aceita
        self.assertEqual(sha(protocolo_da_coleta()), ds["metadados"]["sha256_protocolo"])
        with mock.patch.object(C, "PROTOCOLO", PROTOCOLO_EMENDADO), \
                self.assertRaisesRegex(C.Bloqueio, "difere do congelado"):
            C.verificar_protocolo(ds)                               # arquivo emendado: recusado


# 8–12 ─────────────────────────────────────────────────────────────────────────
class ArquivosERetomada(Base):
    CAMPOS = ("case_id", "empresa", "categoria", "pergunta", "disponibilidade_congelada", "documento", "contexto",
              "resposta", "requisicao", "recuperacao", "inicio_utc", "fim_utc", "duracao_s", "status", "erro",
              "tentativa", "commit", "sha256_dataset", "sha256_configuracao", "geracao", "sha256_registro")

    def test_resposta_salva_pelo_case_id(self):
        self.coletar(limit=3)
        for cid in C.ordem_execucao(self.ds_obj)[:3]:
            r = self.ler(f"respostas/{cid}.json")
            self.assertEqual(r["case_id"], cid)
            self.assertTrue(C.selo_confere(r))
            for k in self.CAMPOS:
                self.assertIn(k, r, k)
            self.assertEqual((r["documento"]["versao"], r["documento"]["sha256_documento"]),
                             (self.ds_obj["empresas"][r["ticker"]]["versao"],
                              self.ds_obj["empresas"][r["ticker"]]["sha256_documento"]))
            self.assertEqual([t["ordem"] for t in r["contexto"]["trechos"]], [1, 2, 3])
            self.assertEqual(r["contexto"]["trechos"][0]["chroma_id"], "p0_tab_0")
            self.assertEqual((r["requisicao"]["modelo"], r["requisicao"]["temperatura"],
                              r["requisicao"]["max_output_tokens"]), ("gemini-2.5-flash", 0.1, 1024))
            self.assertEqual(r["recuperacao"]["top_k"], 3)
            self.assertEqual(r["resposta"], r["resposta_bruta"].strip())
            for proibido in ("gabarito", "valores_esperados", "fontes_gabarito", "revisao_tecnica",
                             "justificativa_disponibilidade", "faithfulness", "answer_relevancy", "classe"):
                self.assertNotIn(proibido, r)

    def test_resposta_existente_nao_e_sobrescrita(self):
        self.coletar(limit=2)
        p = os.path.join(self.saida, "respostas", "WEGE3_N1.json")
        with open(p, "rb") as f:
            antes = f.read()
        g = GeradorFalso()
        r = self.coletar(gerador=g, case_ids=["WEGE3_N1"])
        self.assertEqual((r["encerramento"], g.reqs), ("nada_a_fazer", []))
        with open(p, "rb") as f:
            self.assertEqual(f.read(), antes)
        with self.assertRaises(FileExistsError):
            C.gravar_exclusivo(p, {"x": 1})
        with self.assertRaises(C.Bloqueio):
            self.coletar(case_ids=["WEGE3_N1"], reexecutar_concluido=True)          # sem motivo
        self.coletar(case_ids=["WEGE3_N1"], reexecutar_concluido=True, motivo="teste técnico")
        with open(p, "rb") as f:
            self.assertEqual(f.read(), antes)                                       # original intacto
        rx = self.ler("respostas/WEGE3_N1.reexecucao_01.json")
        self.assertEqual((rx["status"], rx["motivo_reexecucao"]), ("REEXECUCAO", "teste técnico"))

    def test_retomada_ignora_concluidos(self):
        self.coletar(limit=10)
        g = GeradorFalso()
        r = self.coletar(gerador=g)
        feitos = [x["case_id"] for x in r["executados"]]
        self.assertEqual(feitos, C.ordem_execucao(self.ds_obj)[10:])
        self.assertEqual(len(g.reqs), 86)
        self.assertEqual(r["estados"], {"CONCLUIDO": 96})

    def test_interrupcao_e_retomada(self):
        class Interrompe(GeradorFalso):
            def __call__(self, req):
                if len(self.reqs) == 72:
                    raise KeyboardInterrupt
                return super().__call__(req)

        with self.assertRaises(KeyboardInterrupt):
            self.coletar(gerador=Interrompe())
        est = self.ler("estado_coleta.json")
        self.assertEqual(est["execucoes"][0]["encerramento"], "interrompida")
        self.assertEqual(est["resumo"], {"CONCLUIDO": 72, "PENDENTE": 24})
        self.assertFalse(os.path.exists(os.path.join(self.saida, ".trava")))
        g = GeradorFalso()
        self.coletar(gerador=g)
        self.assertEqual(len(g.reqs), 24)
        self.assertEqual(self.ler("estado_coleta.json")["resumo"], {"CONCLUIDO": 96})

    def test_registro_incompleto_nao_conta_como_concluido(self):
        self.coletar(limit=2)
        p = os.path.join(self.saida, "respostas", "WEGE3_N2.json")
        with open(p, "rb") as f:
            original = f.read()
        with open(p, "wb") as f:
            f.write(original[: len(original) // 2])                                # gravação interrompida
        self.assertEqual(C.estado_caso(self.saida, "WEGE3_N2", self.cfg()), C.ESTADO_CORROMPIDO)
        g = GeradorFalso()
        r = self.coletar(gerador=g, case_ids=["WEGE3_N2"])
        self.assertEqual((g.reqs, r["pulados"]), ([], {"WEGE3_N2": "CORROMPIDO"}))
        r = self.coletar(gerador=g, case_ids=["WEGE3_N2"], retentar_erros=True)
        self.assertEqual(len(g.reqs), 1)
        invalidos = os.listdir(os.path.join(self.saida, "respostas", "_invalidos"))
        self.assertEqual(len(invalidos), 1)                                       # preservado
        self.assertEqual(C.estado_caso(self.saida, "WEGE3_N2", self.cfg()), C.STATUS_CONCLUIDO)

    def test_registro_adulterado_nao_conta_como_concluido(self):
        self.coletar(limit=1)
        p = os.path.join(self.saida, "respostas", "WEGE3_N1.json")
        with open(p, encoding="utf-8") as f:
            r = json.load(f)
        r["resposta"] = "outra coisa"
        with open(p, "w", encoding="utf-8") as f:
            json.dump(r, f)
        self.assertEqual(C.estado_caso(self.saida, "WEGE3_N1", self.cfg()), C.ESTADO_CORROMPIDO)

    def test_erro_de_api_nao_vira_resposta(self):
        g = GeradorFalso(falhar_em={3})
        r = self.coletar(gerador=g)
        self.assertEqual(r["encerramento"], "erro")
        self.assertEqual(len(g.reqs), 3)                                          # interrompe na falha
        cid = C.ordem_execucao(self.ds_obj)[2]
        self.assertFalse(os.path.exists(os.path.join(self.saida, "respostas", f"{cid}.json")))
        e = self.ler(f"respostas/{cid}.erro_01.json")
        self.assertEqual((e["status"], e["erro"]["tipo"]), ("ERRO", "RuntimeError"))
        self.assertNotIn("resposta", e)
        self.assertEqual(C.estado_caso(self.saida, cid, self.cfg()), C.STATUS_ERRO)
        # sem --retentar-erros o caso com erro fica de fora; os pendentes seguem
        g2 = GeradorFalso()
        r = self.coletar(gerador=g2)
        self.assertEqual(len(g2.reqs), 93)
        self.assertEqual(r["pulados"][cid], "ERRO")
        g3 = GeradorFalso()
        self.coletar(gerador=g3, retentar_erros=True)
        self.assertEqual(len(g3.reqs), 1)
        self.assertEqual(self.ler(f"respostas/{cid}.json")["tentativa"], 2)
        self.assertTrue(os.path.exists(os.path.join(self.saida, "respostas", f"{cid}.erro_01.json")))

    def test_resposta_sem_texto_e_erro_e_nao_resposta(self):
        g = GeradorFalso(sem_texto_em={1})
        self.coletar(gerador=g)
        e = self.ler("respostas/WEGE3_N1.erro_01.json")
        self.assertEqual((e["erro"]["tipo"], e["geracao"]["finish_reason"]), ("RESPOSTA_SEM_TEXTO", "MAX_TOKENS"))
        self.assertFalse(os.path.exists(os.path.join(self.saida, "respostas", "WEGE3_N1.json")))


# 13–17 ────────────────────────────────────────────────────────────────────────
class SegredosEManifesto(Base):
    def test_segredo_nao_aparece_nos_artefatos(self):
        exc = PermissionError(f"401 API key not valid: key={CHAVE_FALSA} ({CHAVE_FALSA})")
        with mock.patch("builtins.print") as pr:
            self.coletar(gerador=GeradorFalso(falhar_em={2}, excecao=exc), segredos=(CHAVE_FALSA,), log=print)
        tudo = self.texto_de_tudo()
        self.assertNotIn(CHAVE_FALSA, tudo)
        self.assertNotIn(CHAVE_FALSA[:20], tudo)
        self.assertIn("***", self.ler("respostas/WEGE3_N2.erro_01.json")["erro"]["mensagem"])
        self.assertNotIn(CHAVE_FALSA, " ".join(str(c) for c in pr.call_args_list))
        self.assertNotIn("Q" * 35, C.sanitizar(f"x {'AI' + 'za' + 'Q' * 35} y {CHAVE_FALSA}"))

    def test_manifesto_nao_contem_gabarito(self):
        self.coletar(limit=1)
        m = self.ler("manifesto_config.json")
        texto = json.dumps(m, ensure_ascii=False)
        for c in self.ds_obj["casos"]:
            self.assertNotIn(c["gabarito"], texto)
            for v in c["valores_esperados"]:
                self.assertNotIn(v["apresentacao_referencia"], texto)
        for k in ("gabarito", "valores_esperados", "fontes_gabarito", "revisao_tecnica", "resposta"):
            self.assertNotIn(f'"{k}"', texto)
        self.assertNotIn(CHAVE_FALSA, texto)

    def test_manifesto_registra_commit_hash_e_configuracao(self):
        self.coletar(limit=1, git=GitFalso(head="a" * 40))
        m = self.ler("manifesto_config.json")
        cfg = m["configuracao"]
        self.assertEqual(m["commit_inicio"], "a" * 40)
        self.assertEqual(m["commit_congelamento_dataset"], C.COMMIT_CONGELAMENTO)
        self.assertEqual(m["sha256_configuracao"], C.sha_config(cfg))
        self.assertEqual(cfg["dataset"]["sha256"], self.ds_sha)
        self.assertEqual(cfg["sha256_protocolo_no_dataset"], C.SHA256_PROTOCOLO_CONGELADO)
        self.assertEqual((cfg["n_casos"], len(cfg["empresas"]), cfg["categorias"]), (96, 12, list(C.CATEGORIAS)))
        self.assertEqual(cfg["distribuicao_disponibilidade"], {"ausente": 12, "parcial": 15, "presente": 69})
        self.assertEqual(cfg["ordem_casos"], C.ordem_execucao(self.ds_obj))
        self.assertEqual((cfg["geracao"]["modelo"], cfg["geracao"]["temperatura"], cfg["geracao"]["max_output_tokens"]),
                         ("gemini-2.5-flash", 0.1, 1024))
        with open(os.path.join(RAIZ, "modulos", "recuperacao.py"), encoding="utf-8") as f:
            self.assertIn(f'QUERY_NUMERICO = "{cfg["recuperacao"]["query_numerico"]}"', f.read())
        self.assertEqual((cfg["recuperacao"]["top_k"], cfg["recuperacao"]["embeddings"]),
                         (3, "paraphrase-multilingual-mpnet-base-v2"))
        self.assertTrue(cfg["ambiente"]["python"] and cfg["ambiente"]["dependencias"]["google-genai"])
        self.assertIn("criado_em_utc", m)
        # imutável: a retomada não reescreve o manifesto
        with open(os.path.join(self.saida, "manifesto_config.json"), "rb") as f:
            antes = f.read()
        self.coletar(limit=2)
        with open(os.path.join(self.saida, "manifesto_config.json"), "rb") as f:
            self.assertEqual(f.read(), antes)

    def test_dataset_alterado_bloqueia_retomada(self):
        self.coletar(limit=5)
        ds = copy.deepcopy(self.ds_obj)
        ds["casos"][0]["gabarito"] += " "
        self._gravar_ds(ds)
        g = GeradorFalso()
        with self.assertRaisesRegex(C.Bloqueio, "dataset mudou"):
            self.coletar(gerador=g)
        self.assertEqual(g.reqs, [])
        with self.assertRaisesRegex(C.Bloqueio, "difere do congelado"):
            self.coletar(gerador=g, sha_dataset_esperado="0" * 64)
        self.assertEqual(g.reqs, [])

    def test_configuracao_alterada_bloqueia_retomada(self):
        self.coletar(limit=5)
        g = GeradorFalso()
        with self.assertRaisesRegex(C.Bloqueio, "configuração mudou: ambiente"):
            self.coletar(gerador=g, cfg_extra={"dependencias": {"google-genai": "9.9.9"}})
        rec = C.parametros_recuperacao()
        rec["top_k"] = 4
        with self.assertRaisesRegex(C.Bloqueio, "configuração mudou: recuperacao"):
            self.coletar(gerador=g, cfg_extra={"recuperacao": rec})
        with self.assertRaisesRegex(C.Bloqueio, "commits posteriores"):
            self.coletar(gerador=g, git=GitFalso(alterados=["modulos/recuperacao.py"]))
        self.assertEqual(g.reqs, [])
        # commit que só acrescenta respostas não bloqueia
        saida_rel = os.path.relpath(self.saida, C.RAIZ).replace(os.sep, "/")
        self.coletar(gerador=g, limit=1, git=GitFalso(alterados=[saida_rel + "/respostas/WEGE3_N1.json"]))
        self.assertEqual(len(g.reqs), 1)

    def test_bloqueios_antes_de_qualquer_chamada(self):
        g = GeradorFalso()
        outro = dict(self.ctxs, BBAS3=self.ctxs["BBAS3"].replace("1.111", "1.112"))
        for kw, padrao in (({"rec": RecuperadorFalso(outro)}, "contexto recuperado difere"),
                           ({"rec": RecuperadorFalso(self.ctxs, versoes_ok=False)}, "Regra de versão"),
                           ({"git": GitFalso(pendencias=["?? avaliacao/ragas/novo.py"])}, "não commitadas"),
                           ({"git": GitFalso(descende=False)}, "não descende")):
            with self.assertRaisesRegex(C.Bloqueio, padrao):
                self.coletar(gerador=g, **kw)
        self.assertEqual(g.reqs, [])
        self.assertFalse(os.path.exists(os.path.join(self.saida, "manifesto_config.json")))
        os.makedirs(self.saida, exist_ok=True)
        open(os.path.join(self.saida, ".trava"), "w").close()
        with self.assertRaisesRegex(C.Bloqueio, "Outra execução"):
            self.coletar(gerador=g)


# 18–20 ────────────────────────────────────────────────────────────────────────
class SeparacaoEIntegridade(Base):
    def test_coleta_nao_depende_de_ragas_nem_avalia(self):
        with open(C.__file__, encoding="utf-8") as f:
            arvore = ast.parse(f.read())
        importados = set()
        for n in ast.walk(arvore):
            if isinstance(n, ast.Import):
                importados |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom) and n.module:
                importados.add(n.module.split(".")[0])
        self.assertFalse(importados & {"ragas", "langchain", "langchain_google_genai", "langchain_community",
                                       "exatidao", "comportamento", "datasets"}, importados)
        codigo = ("import sys; sys.modules['ragas']=None; sys.modules['exatidao']=None; "
                  "sys.modules['comportamento']=None; sys.path.insert(0, r'%s'); "
                  "import coletar_respostas_tcc2 as C; ds, s = C.carregar_dataset(); print(len(ds['casos']))" % PASTA)
        r = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, cwd=RAIZ)
        self.assertEqual(r.stdout.strip(), "96", r.stderr)

    def test_dataset_congelado_nao_e_modificado(self):
        antes = hashes_congelados()
        coleta_oficial = os.path.join(PASTA, "coleta_tcc2")    # existe desde o início da coleta real

        def conteudo_coleta():
            if not os.path.isdir(coleta_oficial):
                return {}
            out = {}
            for raiz, _, arqs in os.walk(coleta_oficial):
                for a in arqs:
                    with open(os.path.join(raiz, a), "rb") as f:
                        out[os.path.relpath(os.path.join(raiz, a), coleta_oficial)] = sha(f.read())
            return out

        coleta_antes = conteudo_coleta()
        self.coletar()
        with self.assertRaises(C.Bloqueio):          # contexto falso ≠ congelado: bloqueia na leitura
            C.dry_run(recuperador=RecuperadorFalso(self.ctxs), dataset_path=C.DATASET, log=lambda *a: None)
        C.carregar_dataset(C.DATASET)
        self.assertEqual(hashes_congelados(), antes)
        self.assertEqual(conteudo_coleta(), coleta_antes)       # os testes não escrevem na coleta oficial

    def test_ponta_a_ponta_falsa_sem_rede(self):
        with self.assertRaises(RedeProibida):
            socket.create_connection(("generativelanguage.googleapis.com", 443))
        g = GeradorFalso()
        r = self.coletar(gerador=g)
        self.assertEqual((r["encerramento"], r["estados"]), ("completa", {"CONCLUIDO": 96}))
        arquivos = sorted(os.listdir(os.path.join(self.saida, "respostas")))
        self.assertEqual(arquivos, sorted(f"{i}.json" for i in C.ordem_execucao(self.ds_obj)))
        est = self.ler("estado_coleta.json")
        self.assertEqual((len(est["execucoes"]), est["execucoes"][0]["encerramento"]), (1, "completa"))
        self.assertEqual([x["case_id"] for x in est["execucoes"][0]["casos"]], C.ordem_execucao(self.ds_obj))
        self.assertFalse(os.path.exists(os.path.join(self.saida, ".trava")))


if __name__ == "__main__":
    unittest.main()
