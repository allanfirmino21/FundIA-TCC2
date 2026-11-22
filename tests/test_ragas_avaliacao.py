# tests/test_ragas_avaliacao.py
#
# Executor da avaliação do RAGAS do TCC 2 (avaliacao/ragas/avaliar_respostas_tcc2.py).
# Sem rede e sem API. Toda avaliação roda sobre uma COLETA SINTÉTICA montada em diretório
# temporário: mesmos contextos congelados, respostas artificiais escritas aqui. Nenhuma
# resposta experimental real é classificada ou pontuada; a coleta real só é conferida
# mecanicamente (hashes), em modo de leitura.

import copy
import hashlib
import json
import math
import os
import shutil
import socket
import sys
import tempfile
import unittest
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "avaliacao", "ragas")
sys.path.insert(0, PASTA)

import avaliar_respostas_tcc2 as A  # noqa: E402
import coletar_respostas_tcc2 as C  # noqa: E402

COLETA_REAL = os.path.join(PASTA, "coleta_tcc2")
CHAVE_FALSA = "chave-falsa-de-teste-" + "0123456789abcdef" * 2


def _sem_rede(*a, **k):
    raise AssertionError("acesso à rede durante os testes da avaliação")


_patches = [mock.patch.object(socket.socket, "connect", _sem_rede),
            mock.patch.object(socket, "create_connection", _sem_rede),
            mock.patch.object(socket, "getaddrinfo", _sem_rede)]


def setUpModule():
    for p in _patches:
        p.start()


def tearDownModule():
    for p in _patches:
        p.stop()


def sha_arquivos(pasta: str) -> dict:
    out = {}
    for raiz, _, arqs in os.walk(pasta):
        for a in arqs:
            with open(os.path.join(raiz, a), "rb") as f:
                out[os.path.relpath(os.path.join(raiz, a), pasta)] = hashlib.sha256(f.read()).hexdigest()
    return out


def br(d: Decimal, k: int) -> str:
    s = f"{d:,.{k}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def valor(ds, cid, item=0) -> Decimal:
    caso = next(c for c in ds["casos"] if c["id"] == cid)
    return Decimal(caso["valores_esperados"][item]["valor"])


def resposta_truncada(ds) -> tuple[str, str]:
    """Um caso N1 escrito com o valor TRUNCADO numa precisão em que o arredondamento daria outro número."""
    for cid in ("ZAMP3_N1", "CEAB3_N1", "ITSA4_N1", "IRBR3_N1", "WEGE3_N5"):
        for divisor, nome in ((Decimal("1e9"), "bi"), (Decimal("1e6"), "mi")):
            g = valor(ds, cid) / divisor
            for k in range(1, 7):
                t = g.quantize(Decimal(1).scaleb(-k), rounding=ROUND_DOWN)
                if t != g.quantize(Decimal(1).scaleb(-k), rounding=ROUND_HALF_UP) and t > 0:
                    return cid, f"O valor foi de R$ {br(t, k)} {nome}."
    raise AssertionError("sem caso com truncamento distinto do arredondamento")


def respostas_sinteticas(ds) -> tuple[dict, dict]:
    """Respostas artificiais e a classe de exatidão esperada de cada uma."""
    r, esperado = {}, {}
    v = valor(ds, "WEGE3_N1")                                   # formato brasileiro + "mil"
    r["WEGE3_N1"], esperado["WEGE3_N1"] = f"A receita foi de R$ {br(v / 1000, 0)} mil.", "CORRETO"
    v = valor(ds, "BBAS3_N1")                                   # escala implícita (sem R$ nem multiplicador)
    r["BBAS3_N1"], esperado["BBAS3_N1"] = f"O valor foi {br(v / 1000, 0)}.", "CORRETO"
    v = valor(ds, "ITUB4_N1")                                   # bilhões, arredondado (meio para cima)
    r["ITUB4_N1"] = f"Receita de R$ {br((v / Decimal('1e9')).quantize(Decimal('0.01'), ROUND_HALF_UP), 2)} bilhões."
    esperado["ITUB4_N1"] = "CORRETO"
    cid, texto = resposta_truncada(ds)                          # truncado (não arredondado), "bi"/"mi"
    r[cid], esperado[cid] = texto, "CORRETO"
    v = valor(ds, "LAVV3_N1")                                   # trilhões
    r["LAVV3_N1"] = f"Receita de R$ {br((v / Decimal('1e12')).quantize(Decimal('0.0001'), ROUND_DOWN), 4)} tri."
    esperado["LAVV3_N1"] = "CORRETO"
    a, b = valor(ds, "WEGE3_N3", 0), valor(ds, "WEGE3_N3", 1)  # múltiplos valores + percentual
    p = abs(valor(ds, "WEGE3_N3", 2)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    r["WEGE3_N3"] = (f"Lucro de R$ {br(a / 1000, 0)} mil no 1S26 e de R$ {br(b / 1000, 0)} mil no 1S25, "
                     f"queda de {br(p, 2)}%.")
    esperado["WEGE3_N3"] = "CORRETO"
    a, b = valor(ds, "ZAMP3_E3", 0), valor(ds, "ZAMP3_E3", 1)  # sinais explícitos negativos
    r["ZAMP3_E3"] = (f"Resultado financeiro de -R$ {br(abs(a) / 1000, 0)} mil no 1S26 "
                     f"e de −R$ {br(abs(b) / 1000, 0)} mil no 1S25.")
    esperado["ZAMP3_E3"] = "CORRETO"
    a = valor(ds, "WEGE3_E3", 0)                                # só um de dois valores exigidos
    r["WEGE3_E3"], esperado["WEGE3_E3"] = f"Resultado financeiro de R$ {br(a / 1000, 0)} mil.", "PARCIALMENTE_CORRETO"
    a = valor(ds, "ZAMP3_N2", 0)                                # sinal divergente do gabarito
    r["ZAMP3_N2"], esperado["ZAMP3_N2"] = f"Lucro de R$ {br(abs(a) / 1000, 0)} mil.", "INCORRETO"
    r["LWSA3_N5"], esperado["LWSA3_N5"] = "O caixa foi de R$ 1,00 bilhão.", "INCORRETO"
    a = valor(ds, "ZAMP3_N3", 0)                                # parênteses: sinal ambíguo -> decisão manual
    r["ZAMP3_N3"] = f"Resultado: ({br(abs(a) / 1000, 0)}) no 1S26."
    esperado["ZAMP3_N3"] = "PARCIALMENTE_CORRETO"               # depois da decisão "-"
    r["WEGE3_N4"], esperado["WEGE3_N4"] = "Lucro de R$ 3,2 bilhões e receita de R$ 19,6 bilhões.", "NAO_APLICAVEL"
    r["AURE3_N1"], esperado["AURE3_N1"] = "Os trechos não trazem essa informação.", "NAO_APLICAVEL"
    for c in ds["casos"]:
        if c["id"] not in r:
            r[c["id"]] = f"Resposta sintética de {c['id']}."
            esperado[c["id"]] = "NAO_APLICAVEL"
    return r, esperado


def construir_coleta(dest: str, respostas: dict, truncadas=(), config=None) -> str:
    """Coleta sintética com o mesmo esquema da real; devolve o SHA-256 do SHA256_COLETA.txt."""
    os.makedirs(os.path.join(dest, "respostas"))
    shutil.copyfile(os.path.join(COLETA_REAL, "manifesto_config.json"), os.path.join(dest, "manifesto_config.json"))
    for cid, texto in respostas.items():
        with open(os.path.join(COLETA_REAL, "respostas", f"{cid}.json"), encoding="utf-8") as f:
            real = json.load(f)
        reg = {k: v for k, v in real.items() if k not in ("resposta", "resposta_bruta", "geracao", "sha256_registro")}
        reg["geracao"] = {"modelo_retornado": "gemini-2.5-flash",
                          "finish_reason": "MAX_TOKENS" if cid in truncadas else "STOP",
                          "truncada_por_limite": cid in truncadas, "uso_tokens": None}
        if config:
            reg["sha256_configuracao"] = config
        reg["resposta"], reg["resposta_bruta"] = texto, texto
        C.gravar_exclusivo(os.path.join(dest, "respostas", f"{cid}.json"), C.selar(reg))
    return regerar_hashes(dest)


def regerar_hashes(dest: str) -> str:
    p = os.path.join(dest, "SHA256_COLETA.txt")
    if os.path.exists(p):
        os.remove(p)
    rel = sorted((os.path.relpath(os.path.join(r, a), dest).replace(os.sep, "/")
                  for r, _, arqs in os.walk(dest) for a in arqs), key=lambda s: s.encode())
    linhas = "".join(f"{hashlib.sha256(open(os.path.join(dest, *x.split('/')), 'rb').read()).hexdigest()}  {x}\n"
                     for x in rel)
    with open(p, "wb") as f:
        f.write(linhas.encode())
    return hashlib.sha256(linhas.encode()).hexdigest()


class GitFalso:
    def __init__(self, pendencias=(), rastreado=True):
        self.pend, self.rast = list(pendencias), rastreado

    def head(self):
        return "f" * 40

    def pendencias(self, caminhos):
        return list(self.pend)

    def rastreado(self, caminho):
        return self.rast


class AvaliadorFalso:
    """Devolve scores fixos; registra cada chamada (uma métrica por vez)."""
    segredos = (CHAVE_FALSA,)

    def __init__(self, resp_para_id, scores=None, falhar_em=None, erros_em=None):
        self.resp_para_id, self.scores = resp_para_id, scores or {}
        self.falhar_em, self.erros_em, self.chamadas = falhar_em, erros_em or {}, []

    def descricao(self):
        return {"modelo": "falso", "dependencias": {}}

    def avaliar(self, metrica, amostra):
        cid = self.resp_para_id[amostra["response"]]
        self.chamadas.append((cid, metrica, copy.deepcopy(amostra)))
        if cid == self.falhar_em:
            raise RuntimeError(f"falha inesperada com a chave {CHAVE_FALSA}")
        return {"score": self.scores.get((cid, metrica), 0.5), "erros": self.erros_em.get(cid, []),
                "modelos_retornados": ["gemini-2.5-flash"]}


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ds, cls.sha_ds = C.carregar_dataset(C.DATASET)
        cls.respostas, cls.esperado = respostas_sinteticas(cls.ds)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.coleta = os.path.join(self.tmp.name, "coleta")
        self.saida = os.path.join(self.tmp.name, "saida")
        self.truncadas = {"WEGE3_N1", "LWSA3_N5"}
        self.sha_hashes = construir_coleta(self.coleta, self.respostas, self.truncadas)
        self.real_antes = sha_arquivos(COLETA_REAL)

    def tearDown(self):
        self.assertEqual(sha_arquivos(COLETA_REAL), self.real_antes)      # a coleta real nunca é tocada
        self.tmp.cleanup()

    def carregar(self, coleta=None, sha=None, **kw):
        return A.carregar_entradas(C.DATASET, coleta or self.coleta,
                                   sha_manifesto_hashes=sha or self.sha_hashes, **kw)[2]

    def exatidao(self, casos, git=None):
        return A.exatidao(casos=casos, sha_dataset=self.sha_ds, saida=self.saida, git=git or GitFalso(),
                          log=lambda *a: None)

    def decidir_sinal(self, casos, sinal="-"):
        caso = next(c for c in casos if c["case_id"] == "ZAMP3_N3")
        pend = json.load(open(os.path.join(self.saida, "exatidao", "pendencias_sinal_01.json"), encoding="utf-8"))
        num = pend["casos"]["ZAMP3_N3"]["numeros"][0]
        dec = {"decidido_por": "teste", "decidido_em": "2026-09-29",
               "casos": {"ZAMP3_N3": {"sha256_resposta": caso["sha256_resposta"], "decisoes": [
                   {"inicio": num["inicio"], "texto": num["texto"], "sinal": sinal,
                    "justificativa": "a oração trata de prejuízo registrado no contexto"}]}}}
        with open(os.path.join(self.saida, "exatidao", "decisoes_sinal.json"), "w", encoding="utf-8") as f:
            json.dump(dec, f, ensure_ascii=False)
        return dec

    def anotar_tudo(self, casos):
        A.gerar_modelo_anotacao(casos, self.saida)
        p = A.arquivo_anotacoes(self.saida)
        doc = json.load(open(p, encoding="utf-8"))
        for reg in doc["registros"]:
            if reg["disponibilidade"] == "presente":
                reg.update(afirmacoes=[{"trecho_resposta": "Resposta", "rotulo": "S", "evidencia_contexto": "linha"}],
                           declara_limitacao=False, entrega_informacao_sustentada=True, classe="SEM_DESVIO",
                           abstencao_em_caso_presente=False)
            else:
                reg.update(afirmacoes=[{"trecho_resposta": "Resposta", "rotulo": "N"}], declara_limitacao=True,
                           entrega_informacao_sustentada=False, classe="ABSTENCAO_ADEQUADA",
                           abstencao_em_caso_presente=False)
            reg.update(justificativa="teste", classificador="teste", classificado_em="2026-09-29")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False)

    def documentar_comportamento(self):
        """Convenções e ratificação: documentos exigidos em commit antes do RAGAS (Emenda 4)."""
        for p in A.documentos_comportamento(self.saida):
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(f"# {os.path.basename(p)} (teste)\n")

    def preparar_ragas(self):
        casos = self.carregar()
        self.exatidao(casos)
        self.decidir_sinal(casos)
        self.exatidao(casos)
        self.anotar_tudo(casos)
        self.documentar_comportamento()
        return casos

    def ragas(self, casos, avaliador, **kw):
        kw.setdefault("git", GitFalso())
        return A.avaliar_ragas(casos=casos, sha_dataset=self.sha_ds, avaliador=avaliador, saida=self.saida,
                               pausa=0, log=lambda *a: None, **kw)

    def avaliador(self, **kw):
        return AvaliadorFalso({v: k for k, v in self.respostas.items()}, **kw)


# ── integridade das entradas ───────────────────────────────────────────────────

def config_com_protocolo_atual() -> str:
    """Configuração histórica com o hash do protocolo trocado pelo do arquivo atual (emendado)."""
    with open(os.path.join(COLETA_REAL, "manifesto_config.json"), encoding="utf-8") as f:
        cfg = json.load(f)["configuracao"]
    cfg["instrumentos_congelados"]["avaliacao/ragas/PROTOCOLO_RAGAS_TCC2.md"] = \
        C.sha256_arquivo(os.path.join(PASTA, "PROTOCOLO_RAGAS_TCC2.md"))
    return C.sha_config(cfg)


class ColetaReal(unittest.TestCase):
    def test_coleta_real_confere_pela_configuracao_historica(self):
        antes = sha_arquivos(COLETA_REAL)
        ds, sha, casos = A.carregar_entradas()
        self.assertEqual(len(casos), 96)
        self.assertEqual(sum(c["truncada_na_geracao"] for c in casos), 36)
        self.assertEqual(sha_arquivos(COLETA_REAL), antes)

    def test_protocolo_emendado_nao_invalida_a_coleta(self):
        """A configuração recalculada hoje difere da histórica (protocolo emendado), e a coleta vale."""
        ds, sha = C.carregar_dataset(C.DATASET)
        self.assertNotEqual(config_com_protocolo_atual(), A.SHA256_CONFIG_HISTORICA)
        self.assertEqual(len(A.carregar_coleta(ds, sha)), 96)


class Integridade(Base):
    def test_coleta_sintetica_confere(self):
        casos = self.carregar()
        self.assertEqual([c["case_id"] for c in casos], [c["id"] for c in self.ds["casos"]])
        self.assertEqual(len(casos[0]["contextos"]), 3)

    def test_manifesto_de_hashes_diferente_do_congelado_bloqueia(self):
        with self.assertRaisesRegex(A.Bloqueio, "SHA256_COLETA.txt difere"):
            A.carregar_entradas(C.DATASET, self.coleta)            # hash congelado da coleta REAL

    def test_arquivo_extra_na_coleta_bloqueia(self):
        open(os.path.join(self.coleta, "respostas", "intruso.json"), "w").close()
        with self.assertRaisesRegex(A.Bloqueio, "sobrando"):
            self.carregar()

    def test_resposta_adulterada_bloqueia(self):
        p = os.path.join(self.coleta, "respostas", "WEGE3_N1.json")
        reg = json.load(open(p, encoding="utf-8"))
        reg["resposta"] = reg["resposta"].replace("receita", "RECEITA")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(reg, f, ensure_ascii=False, indent=2)
        with self.assertRaisesRegex(A.Bloqueio, "alterado após o congelamento"):
            self.carregar()
        novo = regerar_hashes(self.coleta)                      # mesmo refazendo a lista de hashes:
        with self.assertRaisesRegex(A.Bloqueio, "adulterado"):  # o selo do registro não confere
            self.carregar(sha=novo)

    def test_dataset_adulterado_bloqueia(self):
        copia = os.path.join(self.tmp.name, "dataset.json")
        with open(C.DATASET, encoding="utf-8") as f:
            d = json.load(f)
        d["casos"][0]["pergunta"] += " "
        with open(copia, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
        with self.assertRaisesRegex(A.Bloqueio, "dataset"):
            A.carregar_entradas(copia, self.coleta, sha_manifesto_hashes=self.sha_hashes)

    def test_case_id_faltante_bloqueia(self):
        os.remove(os.path.join(self.coleta, "respostas", "AURE3_E3.json"))
        with self.assertRaisesRegex(A.Bloqueio, "faltando \\['AURE3_E3'\\]"):
            self.carregar(sha=regerar_hashes(self.coleta))

    def test_case_id_duplicado_bloqueia(self):
        p = os.path.join(self.coleta, "respostas", "WEGE3_N2.json")
        reg = json.load(open(os.path.join(self.coleta, "respostas", "WEGE3_N1.json"), encoding="utf-8"))
        os.remove(p)
        C.gravar_exclusivo(p, C.selar(reg))                    # WEGE3_N2.json com o registro de WEGE3_N1
        with self.assertRaisesRegex(A.Bloqueio, "duplicado ou trocado"):
            self.carregar(sha=regerar_hashes(self.coleta))

    def test_registro_com_configuracao_atual_e_recusado(self):
        outra = os.path.join(self.tmp.name, "outra")
        sha_h = construir_coleta(outra, self.respostas, config=config_com_protocolo_atual())
        with self.assertRaisesRegex(A.Bloqueio, "configuração histórica"):
            self.carregar(coleta=outra, sha=sha_h)

    def test_resposta_truncada_preservada_e_marcada(self):
        casos = {c["case_id"]: c for c in self.carregar()}
        self.assertTrue(casos["WEGE3_N1"]["truncada_na_geracao"])
        self.assertFalse(casos["WEGE3_N3"]["truncada_na_geracao"])
        self.assertEqual(casos["WEGE3_N1"]["resposta"], self.respostas["WEGE3_N1"])


# ── A. exatidão ───────────────────────────────────────────────────────────────

class Exatidao(Base):
    def test_sinal_ambiguo_fica_pendente_sem_resultado(self):
        casos = self.carregar()
        r = self.exatidao(casos)
        self.assertEqual((r["status"], r["pendencias"]), ("pendente_sinal", ["ZAMP3_N3"]))
        self.assertFalse(os.path.exists(os.path.join(self.saida, "exatidao", "resultado_exatidao.json")))
        pend = json.load(open(r["arquivo"], encoding="utf-8"))
        num = pend["casos"]["ZAMP3_N3"]["numeros"]
        self.assertEqual(len(num), 1)
        self.assertEqual(self.respostas["ZAMP3_N3"][num[0]["inicio"]:].split(")")[0], num[0]["texto"])
        r2 = self.exatidao(casos)                               # sem decisão nova: não duplica
        self.assertEqual(r2["arquivo"], r["arquivo"])

    def test_classes_depois_da_decisao_manual(self):
        casos = self.carregar()
        self.exatidao(casos)
        self.decidir_sinal(casos)
        r = self.exatidao(casos)
        self.assertEqual(r["status"], "concluida")
        res = json.load(open(r["arquivo"], encoding="utf-8"))
        self.assertTrue(C.selo_confere(res))
        classes = {x["case_id"]: x["classe"] for x in res["resultados"]}
        self.assertEqual(classes, self.esperado)
        por_id = {x["case_id"]: x for x in res["resultados"]}
        self.assertTrue(por_id["BBAS3_N1"]["escala_implicita"])
        self.assertFalse(por_id["WEGE3_N1"]["escala_implicita"])
        self.assertTrue(por_id["ZAMP3_N3"]["sinal_revisao_manual"])
        self.assertEqual(list(por_id["ZAMP3_N3"]["decisoes_manuais_sinal"].values()), ["-"])
        self.assertTrue(por_id["LWSA3_N5"]["truncada_na_geracao"])
        self.assertEqual(res["sha256_decisoes_sinal"],
                         C.sha256_arquivo(os.path.join(self.saida, "exatidao", "decisoes_sinal.json")))

    def test_decisao_contraria_ao_gabarito_nao_confere(self):
        casos = self.carregar()
        self.exatidao(casos)
        self.decidir_sinal(casos, sinal="+")
        res = json.load(open(self.exatidao(casos)["arquivo"], encoding="utf-8"))
        self.assertEqual(next(x for x in res["resultados"] if x["case_id"] == "ZAMP3_N3")["classe"], "INCORRETO")

    def test_resultado_nao_e_sobrescrito(self):
        casos = self.carregar()
        self.exatidao(casos)
        self.decidir_sinal(casos)
        p = self.exatidao(casos)["arquivo"]
        antes = C.sha256_arquivo(p)
        with self.assertRaisesRegex(A.Bloqueio, "já existe"):
            self.exatidao(casos)
        self.assertEqual(C.sha256_arquivo(p), antes)

    def test_decisoes_invalidas_sao_recusadas(self):
        casos = self.carregar()
        self.exatidao(casos)
        dec = self.decidir_sinal(casos)
        p = os.path.join(self.saida, "exatidao", "decisoes_sinal.json")
        for mudar in (lambda d: d["casos"]["ZAMP3_N3"]["decisoes"][0].update(inicio=0),
                      lambda d: d["casos"]["ZAMP3_N3"]["decisoes"][0].update(justificativa=""),
                      lambda d: d["casos"]["ZAMP3_N3"]["decisoes"][0].update(sinal="?"),
                      lambda d: d["casos"]["ZAMP3_N3"].update(sha256_resposta="0" * 64),
                      lambda d: d.update(decidido_por="")):
            d = copy.deepcopy(dec)
            mudar(d)
            with open(p, "w", encoding="utf-8") as f:
                json.dump(d, f)
            with self.assertRaises(A.Bloqueio):
                self.exatidao(casos)
        self.assertFalse(os.path.exists(os.path.join(self.saida, "exatidao", "resultado_exatidao.json")))

    def test_exige_codigo_commitado(self):
        with self.assertRaisesRegex(A.Bloqueio, "não commitadas"):
            self.exatidao(self.carregar(), git=GitFalso(pendencias=[" M avaliacao/ragas/exatidao.py"]))


# ── B. comportamento ──────────────────────────────────────────────────────────

class Comportamento(Base):
    def test_sem_anotacao_tudo_incompleto(self):
        casos = self.carregar()
        A.gerar_modelo_anotacao(casos, self.saida)
        v = A.validar_anotacoes(casos, self.saida)
        self.assertEqual(v["contagem"], {"VALIDO": 0, "INCOMPLETO": 96, "INVALIDO": 0})
        self.assertFalse(v["completo"])

    def test_modelo_nao_e_sobrescrito(self):
        casos = self.carregar()
        p = A.gerar_modelo_anotacao(casos, self.saida)
        with self.assertRaises(FileExistsError):
            A.gerar_modelo_anotacao(casos, self.saida)
        self.assertTrue(os.path.exists(p))

    def test_anotacao_valida_completa(self):
        casos = self.carregar()
        self.anotar_tudo(casos)
        v = A.validar_anotacoes(casos, self.saida)
        self.assertTrue(v["completo"], v["contagem"])

    def test_classe_derivada_informada_para_registro_sem_classe(self):
        casos = self.carregar()
        self.anotar_tudo(casos)
        p = A.arquivo_anotacoes(self.saida)
        doc = json.load(open(p, encoding="utf-8"))
        reg = next(r for r in doc["registros"] if r["disponibilidade"] == "parcial")
        reg["classe"] = None
        reg["afirmacoes"] = [{"trecho_resposta": "x", "rotulo": "E", "motivo": "conceito vizinho"}]
        json.dump(doc, open(p, "w", encoding="utf-8"))
        s = A.validar_anotacoes(casos, self.saida)["casos"][reg["id"]]
        self.assertEqual((s["status"], s["classe_derivada"]), ("INCOMPLETO", "EXTRAPOLACAO"))

    def test_anotacoes_inconsistentes_rejeitadas(self):
        casos = self.carregar()
        self.anotar_tudo(casos)
        p = A.arquivo_anotacoes(self.saida)
        base = json.load(open(p, encoding="utf-8"))
        mudancas = {
            "classe escolhida diferente da derivada": lambda r: r.update(classe="ALUCINACAO"),
            "resposta de outra versão": lambda r: r.update(sha256_resposta="0" * 64),
            "scores RAGAS consultados": lambda r: r.update(scores_ragas_consultados=True),
            "E sem motivo": lambda r: r.update(afirmacoes=[{"trecho_resposta": "x", "rotulo": "E"}], classe="EXTRAPOLACAO"),
            "rótulo inválido": lambda r: r.update(afirmacoes=[{"trecho_resposta": "x", "rotulo": "Z"}]),
        }
        for nome, mudar in mudancas.items():
            doc = copy.deepcopy(base)
            mudar(doc["registros"][0])
            json.dump(doc, open(p, "w", encoding="utf-8"))
            s = A.validar_anotacoes(casos, self.saida)
            self.assertEqual(s["casos"][doc["registros"][0]["id"]]["status"], "INVALIDO", nome)
            self.assertFalse(s["completo"], nome)
        doc = copy.deepcopy(base)
        doc["registros"].append(copy.deepcopy(doc["registros"][0]))
        json.dump(doc, open(p, "w", encoding="utf-8"))
        with self.assertRaisesRegex(A.Bloqueio, "duplicado"):
            A.validar_anotacoes(casos, self.saida)


# ── C/D. RAGAS ────────────────────────────────────────────────────────────────

class OrdemDasEtapas(Base):
    def test_ragas_bloqueado_sem_exatidao(self):
        with self.assertRaisesRegex(A.Bloqueio, "exatidão ainda não concluída"):
            self.ragas(self.carregar(), self.avaliador(), metrica="faithfulness")

    def test_ragas_bloqueado_sem_comportamento_completo(self):
        casos = self.carregar()
        self.exatidao(casos)
        self.decidir_sinal(casos)
        self.exatidao(casos)
        A.gerar_modelo_anotacao(casos, self.saida)
        with self.assertRaisesRegex(A.Bloqueio, "comportamento incompleta"):
            self.ragas(casos, self.avaliador(), metrica="faithfulness")

    def test_ragas_bloqueado_sem_commit_das_etapas_anteriores(self):
        casos = self.preparar_ragas()
        av = self.avaliador()
        with self.assertRaisesRegex(A.Bloqueio, "congelados em commit"):
            self.ragas(casos, av, metrica="faithfulness", git=GitFalso(rastreado=False))
        self.assertEqual(av.chamadas, [])

    def test_decisoes_alteradas_depois_da_exatidao_bloqueiam(self):
        casos = self.preparar_ragas()
        p = os.path.join(self.saida, "exatidao", "decisoes_sinal.json")
        with open(p, "a", encoding="utf-8") as f:
            f.write(" ")
        with self.assertRaisesRegex(A.Bloqueio, "decisoes_sinal.json mudou"):
            self.ragas(casos, self.avaliador(), metrica="faithfulness")


class Ragas(Base):
    def test_uma_metrica_por_chamada_com_entradas_do_protocolo(self):
        casos = self.preparar_ragas()
        av = self.avaliador()
        r = self.ragas(casos, av, metrica="faithfulness")
        self.assertEqual((r["encerramento"], len(r["executados"])), ("completa", 96))
        self.assertEqual({m for _, m, _ in av.chamadas}, {"faithfulness"})
        por_id = {c["case_id"]: c for c in casos}
        for cid, _, amostra in av.chamadas:
            c = por_id[cid]
            self.assertEqual(amostra, {"user_input": c["caso_dataset"]["pergunta"], "response": self.respostas[cid],
                                       "retrieved_contexts": c["contextos"], "reference": c["caso_dataset"]["gabarito"]})
        res = json.load(open(os.path.join(self.saida, "ragas", "faithfulness", "WEGE3_N1.tentativa_01.json"),
                             encoding="utf-8"))
        self.assertTrue(C.selo_confere(res))
        self.assertEqual((res["score"], res["valido"], res["tentativa"]), (0.5, True, 1))
        self.assertTrue(res["entrada"]["truncada_na_geracao"])
        self.assertEqual(res["avaliador"]["temperatura_efetiva"], 0.01)
        self.assertEqual(res["sha256_resposta"], C.sha256_texto(self.respostas["WEGE3_N1"]))
        self.assertEqual(res["proveniencia"]["sha256_configuracao_historica_coleta"], A.SHA256_CONFIG_HISTORICA)
        self.assertIn("sha256_anotacoes_comportamento", res["etapas_anteriores_congeladas"])
        self.assertFalse(os.path.exists(os.path.join(self.saida, "ragas", "answer_relevancy", "WEGE3_N1.tentativa_01.json")))

    def test_retomada_nao_reavalia_nem_sobrescreve(self):
        casos = self.preparar_ragas()
        self.ragas(casos, self.avaliador(), metrica="answer_relevancy", case_ids=["WEGE3_N1", "WEGE3_N2"])
        pasta = os.path.join(self.saida, "ragas", "answer_relevancy")
        antes = sha_arquivos(pasta)
        av = self.avaliador()
        r = self.ragas(casos, av, metrica="answer_relevancy")
        self.assertEqual(len(r["executados"]), 94)
        self.assertNotIn("WEGE3_N1", {c for c, _, _ in av.chamadas})
        for k, v in antes.items():
            self.assertEqual(sha_arquivos(pasta)[k], v)
        self.assertEqual(self.ragas(casos, self.avaliador(), metrica="answer_relevancy")["executados"], [])

    def test_nan_so_uma_reavaliacao_e_primeira_preservada(self):
        casos = self.preparar_ragas()
        av = self.avaliador(scores={("ITSA4_N2", "faithfulness"): float("nan")})
        self.ragas(casos, av, metrica="faithfulness")
        p1 = os.path.join(self.saida, "ragas", "faithfulness", "ITSA4_N2.tentativa_01.json")
        r1 = json.load(open(p1, encoding="utf-8"))
        self.assertEqual((r1["score"], r1["valido"], r1["nan"]), (None, False, True))
        sha1 = C.sha256_arquivo(p1)
        self.assertEqual(self.ragas(casos, self.avaliador(), metrica="faithfulness")["executados"], [])
        av2 = self.avaliador(scores={("ITSA4_N2", "faithfulness"): 0.25})
        r = self.ragas(casos, av2, metrica="faithfulness", reavaliar_nan=True)
        self.assertEqual(r["executados"], [{"case_id": "ITSA4_N2", "tentativa": 2, "valido": True}])
        r2 = json.load(open(p1.replace("_01", "_02"), encoding="utf-8"))
        self.assertEqual((r2["passada"], r2["score"]), ("reavaliacao_nan", 0.25))
        self.assertEqual(C.sha256_arquivo(p1), sha1)
        self.assertEqual(self.ragas(casos, self.avaliador(), metrica="faithfulness", reavaliar_nan=True)["executados"], [])

    def test_reavaliacao_persistente_fica_invalida(self):
        casos = self.preparar_ragas()
        nan = {("ITSA4_N2", "answer_relevancy"): float("nan")}
        self.ragas(casos, self.avaliador(scores=nan), metrica="answer_relevancy")
        self.ragas(casos, self.avaliador(scores=nan), metrica="answer_relevancy", reavaliar_nan=True)
        e = A.estado_ragas(self.saida, "answer_relevancy", next(c for c in casos if c["case_id"] == "ITSA4_N2"))
        self.assertEqual(e["estado"], "FINAL")

    def test_erro_da_api_registrado_sem_interromper(self):
        casos = self.preparar_ragas()
        erro = ["Exception raised in Job[0]: ServerError(503 UNAVAILABLE)"]
        av = self.avaliador(scores={("POMO4_E1", "faithfulness"): float("nan")}, erros_em={"POMO4_E1": erro})
        r = self.ragas(casos, av, metrica="faithfulness")
        self.assertEqual((r["encerramento"], len(r["executados"])), ("completa", 96))
        res = json.load(open(os.path.join(self.saida, "ragas", "faithfulness", "POMO4_E1.tentativa_01.json"),
                             encoding="utf-8"))
        self.assertEqual((res["erros"], res["valido"]), (erro, False))

    def test_falha_do_avaliador_registra_interrompe_e_nao_vaza_chave(self):
        casos = self.preparar_ragas()
        r = self.ragas(casos, self.avaliador(falhar_em="WEGE3_N3"), metrica="faithfulness")
        self.assertEqual(r["encerramento"], "erro")
        p = os.path.join(self.saida, "ragas", "faithfulness", "WEGE3_N3.tentativa_01.json")
        texto = open(p, encoding="utf-8").read()
        self.assertNotIn(CHAVE_FALSA, texto)
        self.assertFalse(json.loads(texto)["valido"])
        av = self.avaliador()
        self.ragas(casos, av, metrica="faithfulness")           # retoma o resto sem refazer WEGE3_N3
        self.assertNotIn("WEGE3_N3", {c for c, _, _ in av.chamadas})
        self.assertEqual(len(av.chamadas), 96 - 3)

    def test_tentativa_interrompida_conta_como_invalida(self):
        casos = self.preparar_ragas()
        os.makedirs(os.path.join(self.saida, "ragas", "faithfulness"))
        ini, _ = A._arquivos_ragas(self.saida, "faithfulness", "CEAB3_N1", 1)
        C.gravar_exclusivo(ini, C.selar({"case_id": "CEAB3_N1"}))
        av = self.avaliador()
        self.ragas(casos, av, metrica="faithfulness")
        self.assertNotIn("CEAB3_N1", {c for c, _, _ in av.chamadas})
        r = self.ragas(casos, self.avaliador(), metrica="faithfulness", reavaliar_nan=True)
        self.assertEqual(r["executados"], [{"case_id": "CEAB3_N1", "tentativa": 2, "valido": True}])

    def test_resultado_adulterado_bloqueia(self):
        casos = self.preparar_ragas()
        self.ragas(casos, self.avaliador(), metrica="faithfulness", case_ids=["WEGE3_N1"])
        p = os.path.join(self.saida, "ragas", "faithfulness", "WEGE3_N1.tentativa_01.json")
        r = json.load(open(p, encoding="utf-8"))
        r["score"] = 0.99
        json.dump(r, open(p, "w", encoding="utf-8"))
        with self.assertRaisesRegex(A.Bloqueio, "adulterado"):
            self.ragas(casos, self.avaliador(), metrica="faithfulness")

    def test_selecao_e_metrica_invalidas(self):
        casos = self.preparar_ragas()
        with self.assertRaisesRegex(A.Bloqueio, "case_id inexistente"):
            self.ragas(casos, self.avaliador(), metrica="faithfulness", case_ids=["XXXX3_N1"])
        with self.assertRaisesRegex(A.Bloqueio, "métrica desconhecida"):
            self.ragas(casos, self.avaliador(), metrica="context_precision")

    def test_trava_impede_execucao_concorrente(self):
        casos = self.preparar_ragas()
        with A.trava(self.saida), self.assertRaisesRegex(A.Bloqueio, "em andamento"):
            self.ragas(casos, self.avaliador(), metrica="faithfulness")


# ── dry-run e CLI ─────────────────────────────────────────────────────────────

# ── Emenda 4: PENDENTE_OPERACIONAL ─────────────────────────────────────────────

class GitSeletivo(GitFalso):
    """Marca como não rastreado ou com alterações só os caminhos que terminam com um nome dado."""

    def __init__(self, nao_rastreado=None, alterado=None):
        super().__init__()
        self.nao_rastreado, self.alterado = nao_rastreado, alterado

    def pendencias(self, caminhos):
        return [f" M {c}" for c in caminhos if self.alterado and c.endswith(self.alterado)]

    def rastreado(self, caminho):
        return not (self.nao_rastreado and caminho.endswith(self.nao_rastreado))


class PendenteOperacional(Base):
    """
    Casos truncados, anotados e ratificados, que comportamento.derivar_classe recusa pela regra
    estrutural (rubrica, Seção 4, item 4): só ficam PENDENTE_OPERACIONAL se listados em
    pendencias_comportamento.json e se cumprirem todas as condições da Emenda 4.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        por_disp = {d: [c["id"] for c in cls.ds["casos"] if c["disponibilidade"] == d]
                    for d in ("presente", "parcial", "ausente")}
        cls.parcial_trunc, cls.parcial_inteira = por_disp["parcial"][0], por_disp["parcial"][1]
        cls.ausente_trunc = por_disp["ausente"][0]
        cls.presente_trunc = next(i for i in por_disp["presente"] if i not in ("WEGE3_N1", "LWSA3_N5"))
        cls.pendentes = [cls.parcial_trunc, cls.ausente_trunc]

    def setUp(self):
        super().setUp()
        self.truncadas = self.truncadas | {self.parcial_trunc, self.ausente_trunc, self.presente_trunc}
        self.coleta = os.path.join(self.tmp.name, "coleta_emenda4")
        self.sha_hashes = construir_coleta(self.coleta, self.respostas, self.truncadas)

    # helpers
    def doc_anotacoes(self):
        return json.load(open(A.arquivo_anotacoes(self.saida), encoding="utf-8"))

    def gravar_anotacoes(self, doc):
        with open(A.arquivo_anotacoes(self.saida), "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False)

    def deixar_sem_classe(self, ids, **campos):
        """Anotação ratificada de caso truncado que a regra congelada não classifica."""
        doc = self.doc_anotacoes()
        for reg in doc["registros"]:
            if reg["id"] in ids:
                reg.update(afirmacoes=[], declara_limitacao=False, entrega_informacao_sustentada=False,
                           classe=None, abstencao_em_caso_presente=None)
                reg.update(campos)
        self.gravar_anotacoes(doc)

    def escrever_pendencias(self, casos, ids, **sobrescrever):
        por_id = {c["case_id"]: c for c in casos}
        lista = [{"id": i, "disponibilidade": por_id[i]["disponibilidade"],
                  "truncada_na_geracao": por_id[i]["truncada_na_geracao"], "estado": A.ESTADO_PENDENCIA,
                  **sobrescrever} for i in ids]
        p = A.arquivo_pendencias(self.saida)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"pendencias": lista}, f, ensure_ascii=False)

    def preparar(self, ids=None, **campos):
        """Anota tudo como válido, deixa os ids sem classe e os lista nas pendências."""
        casos = self.carregar()
        ids = self.pendentes if ids is None else ids
        if os.path.exists(A.arquivo_anotacoes(self.saida)):      # permite repetir dentro do mesmo teste
            os.remove(A.arquivo_anotacoes(self.saida))
        self.anotar_tudo(casos)
        self.deixar_sem_classe(ids, **campos)
        self.escrever_pendencias(casos, ids)
        return casos

    def status(self, casos, cid):
        return A.validar_anotacoes(casos, self.saida)["casos"][cid]

    def assertInvalido(self, casos, cid, trecho_motivo=None):
        s = self.status(casos, cid)
        self.assertEqual(s["status"], "INVALIDO", s)
        if trecho_motivo:
            self.assertIn(trecho_motivo, s["motivo"])
        self.assertFalse(A.validar_anotacoes(casos, self.saida)["completo"])

    # condições
    def test_listado_e_conforme_fica_pendente_operacional(self):
        casos = self.preparar()
        v = A.validar_anotacoes(casos, self.saida)
        for cid in self.pendentes:
            self.assertEqual(v["casos"][cid]["status"], A.PENDENTE_OPERACIONAL)
        self.assertEqual(v["contagem"], {"VALIDO": 94, "PENDENTE_OPERACIONAL": 2, "INCOMPLETO": 0, "INVALIDO": 0})
        self.assertTrue(v["completo"])

    def test_pendente_com_afirmacao_s_e_informacao_entregue(self):
        casos = self.preparar(afirmacoes=[{"trecho_resposta": "Resposta", "rotulo": "S"}],
                              entrega_informacao_sustentada=True)
        self.assertEqual(self.status(casos, self.parcial_trunc)["status"], A.PENDENTE_OPERACIONAL)

    def test_pendente_nao_e_classe_de_comportamento(self):
        self.assertNotIn(A.PENDENTE_OPERACIONAL, A.B.CLASSES)
        for admitidas in A.B.ADMITIDAS.values():
            self.assertNotIn(A.PENDENTE_OPERACIONAL, admitidas)

    def test_nao_listado_continua_invalido(self):
        casos = self.carregar()
        self.anotar_tudo(casos)
        self.deixar_sem_classe(self.pendentes)
        v = A.validar_anotacoes(casos, self.saida)               # sem arquivo de pendências
        self.assertEqual(v["contagem"], {"VALIDO": 94, "INCOMPLETO": 0, "INVALIDO": 2})
        self.escrever_pendencias(casos, [self.parcial_trunc])    # com arquivo, mas sem o caso ausente
        self.assertInvalido(casos, self.ausente_trunc, "sem afirmação E/A")

    def test_sem_arquivo_de_pendencias_comportamento_anterior(self):
        casos = self.carregar()
        self.anotar_tudo(casos)
        v = A.validar_anotacoes(casos, self.saida)
        self.assertEqual(v["contagem"], {"VALIDO": 96, "INCOMPLETO": 0, "INVALIDO": 0})
        self.assertTrue(v["completo"])

    def test_listado_mas_nao_truncado(self):
        casos = self.carregar()
        self.anotar_tudo(casos)
        self.deixar_sem_classe([self.parcial_inteira])
        self.escrever_pendencias(casos, [self.parcial_inteira])
        self.assertInvalido(casos, self.parcial_inteira, "não truncada")
        self.escrever_pendencias(casos, [self.parcial_inteira], truncada_na_geracao=True)
        self.assertInvalido(casos, self.parcial_inteira, "difere da coleta")

    def test_listado_mas_presente(self):
        casos = self.preparar([self.presente_trunc])
        self.assertInvalido(casos, self.presente_trunc, "parcial ou ausente")

    def test_listado_com_e_ou_a(self):
        for rotulo in ("E", "A"):
            casos = self.preparar(afirmacoes=[{"trecho_resposta": "Resposta", "rotulo": rotulo, "motivo": "teste"}])
            self.assertInvalido(casos, self.parcial_trunc, "E ou A")

    def test_listado_com_declaracao_de_limitacao(self):
        casos = self.preparar(declara_limitacao=True)
        self.assertInvalido(casos, self.parcial_trunc, "declara_limitacao")

    def test_listado_classificavel_nunca_vira_pendente(self):
        casos = self.preparar(afirmacoes=[{"trecho_resposta": "Resposta", "rotulo": "N"}], declara_limitacao=True)
        for cid in self.pendentes:
            self.assertNotEqual(self.status(casos, cid)["status"], A.PENDENTE_OPERACIONAL)

    def test_listado_com_classe_ou_marca_preenchida(self):
        casos = self.preparar(classe="ABSTENCAO_ADEQUADA")
        self.assertInvalido(casos, self.parcial_trunc, "classe ou abstencao")
        for marca in (False, True):
            casos = self.preparar(abstencao_em_caso_presente=marca)
            self.assertInvalido(casos, self.parcial_trunc, "classe ou abstencao")

    def test_registro_vazio_ou_malformado(self):
        casos = self.carregar()
        A.gerar_modelo_anotacao(casos, self.saida)                # nunca anotado
        self.escrever_pendencias(casos, self.pendentes)
        self.assertInvalido(casos, self.parcial_trunc)
        casos = self.preparar()
        doc = self.doc_anotacoes()
        reg = next(r for r in doc["registros"] if r["id"] == self.parcial_trunc)
        del reg["classificado_em"]
        self.gravar_anotacoes(doc)
        self.assertInvalido(casos, self.parcial_trunc, "campos ausentes")
        casos = self.preparar(entrega_informacao_sustentada=None)
        self.assertInvalido(casos, self.parcial_trunc, "entrega_informacao_sustentada")

    def test_scores_justificativa_classificador_e_rotulos(self):
        mudancas = {
            "scores RAGAS": ({"scores_ragas_consultados": True}, "scores RAGAS"),
            "justificativa vazia": ({"justificativa": " "}, "justificativa"),
            "classificador vazio": ({"classificador": ""}, "classificador"),
            "rótulo inválido": ({"afirmacoes": [{"trecho_resposta": "Resposta", "rotulo": "Z"}]}, "afirmação inválida"),
            "trecho vazio": ({"afirmacoes": [{"trecho_resposta": " ", "rotulo": "S"}]}, "afirmação inválida"),
        }
        for nome, (campos, motivo) in mudancas.items():
            with self.subTest(nome):
                casos = self.preparar(**campos)
                self.assertInvalido(casos, self.parcial_trunc, motivo)

    def test_sha_da_resposta_divergente(self):
        casos = self.preparar(sha256_resposta="0" * 64)
        self.assertInvalido(casos, self.parcial_trunc, "sha256_resposta")

    def test_pendencias_incoerentes_com_a_coleta(self):
        casos = self.preparar()
        self.escrever_pendencias(casos, self.pendentes, disponibilidade="presente")
        self.assertInvalido(casos, self.parcial_trunc, "difere da coleta")
        self.escrever_pendencias(casos, self.pendentes, estado="OUTRO")
        self.assertInvalido(casos, self.parcial_trunc, "estado diferente")

    def test_derivar_classe_precisa_recusar_pela_regra_estrutural(self):
        casos = self.preparar()
        with mock.patch.object(A.B, "derivar_classe", return_value=("ABSTENCAO_ADEQUADA", False)):
            self.assertInvalido(casos, self.parcial_trunc, "não recusa")
        with mock.patch.object(A.B, "derivar_classe", side_effect=A.B.RegistroInconsistente("outra recusa")):
            self.assertInvalido(casos, self.parcial_trunc, "recusa diferente")

    def test_lista_com_id_inexistente_repetido_ou_malformada_bloqueia(self):
        casos = self.preparar()
        p = A.arquivo_pendencias(self.saida)
        for conteudo, erro in (({"pendencias": [{"id": "XXXX3_N9", "estado": A.ESTADO_PENDENCIA}]}, "inexistente"),
                               ({"pendencias": [{"id": self.parcial_trunc}, {"id": self.parcial_trunc}]}, "duplicado"),
                               ({"pendencias": {"id": self.parcial_trunc}}, "lista"),
                               ([], "lista")):
            with open(p, "w", encoding="utf-8") as f:
                json.dump(conteudo, f)
            with self.assertRaisesRegex(A.Bloqueio, erro):
                A.validar_anotacoes(casos, self.saida)

    # gate e congelamento
    def preparar_gate(self):
        casos = self.preparar_ragas()
        self.deixar_sem_classe(self.pendentes)
        self.escrever_pendencias(casos, self.pendentes)
        return casos

    def test_gate_liberado_com_validos_e_pendentes_somando_96(self):
        casos = self.preparar_gate()
        av = self.avaliador()
        r = self.ragas(casos, av, metrica="faithfulness")
        self.assertEqual((r["encerramento"], len(r["executados"])), ("completa", 96))   # RAGAS sobre os 96
        res = json.load(open(os.path.join(self.saida, "ragas", "faithfulness", f"{self.parcial_trunc}.tentativa_01.json"),
                             encoding="utf-8"))
        cong = res["etapas_anteriores_congeladas"]
        self.assertEqual(cong["sha256_anotacoes_comportamento"], C.sha256_arquivo(A.arquivo_anotacoes(self.saida)))
        self.assertEqual(cong["sha256_pendencias_comportamento"], C.sha256_arquivo(A.arquivo_pendencias(self.saida)))
        conv, ratif = A.documentos_comportamento(self.saida)
        self.assertEqual(cong["sha256_convencoes_comportamento"], C.sha256_arquivo(conv))
        self.assertEqual(cong["sha256_ratificacao_comportamento"], C.sha256_arquivo(ratif))

    def test_gate_bloqueado_com_incompleto(self):
        casos = self.preparar_gate()
        doc = self.doc_anotacoes()
        outro = next(r for r in doc["registros"] if r["id"] not in self.pendentes)
        outro["classe"] = None                                    # INCOMPLETO
        self.gravar_anotacoes(doc)
        av = self.avaliador()
        with self.assertRaisesRegex(A.Bloqueio, "comportamento incompleta"):
            self.ragas(casos, av, metrica="faithfulness")
        self.assertEqual(av.chamadas, [])

    def test_gate_bloqueado_com_invalido(self):
        casos = self.preparar_gate()
        self.escrever_pendencias(casos, [self.parcial_trunc])     # o ausente fica INVALIDO
        av = self.avaliador()
        with self.assertRaisesRegex(A.Bloqueio, "comportamento incompleta"):
            self.ragas(casos, av, metrica="faithfulness")
        self.assertEqual(av.chamadas, [])

    def test_gate_exige_documentos_de_comportamento_congelados(self):
        casos = self.preparar_gate()
        nomes = ["anotacoes_comportamento.json", "pendencias_comportamento.json",
                 "CONVENCOES_ANOTACAO_COMPORTAMENTO.md", "RATIFICACAO_COMPORTAMENTO.md"]
        for nome in nomes:
            for git in (GitSeletivo(nao_rastreado=nome), GitSeletivo(alterado=nome)):
                with self.subTest(nome=nome, git=vars(git)):
                    av = self.avaliador()
                    with self.assertRaisesRegex(A.Bloqueio, "congelados em commit"):
                        self.ragas(casos, av, metrica="faithfulness", git=git)
                    self.assertEqual(av.chamadas, [])

    def test_gate_exige_convencoes_e_ratificacao(self):
        casos = self.preparar_gate()
        for p in A.documentos_comportamento(self.saida):
            with self.subTest(os.path.basename(p)):
                os.rename(p, p + ".fora")
                av = self.avaliador()
                with self.assertRaisesRegex(A.Bloqueio, "documentos da anotação de comportamento ausentes"):
                    self.ragas(casos, av, metrica="faithfulness")
                self.assertEqual(av.chamadas, [])
                os.rename(p + ".fora", p)

    def test_executor_nao_contem_ids_nem_tickers(self):
        fonte = open(os.path.join(PASTA, "avaliar_respostas_tcc2.py"), encoding="utf-8").read()
        for c in self.ds["casos"]:
            self.assertNotIn(c["id"], fonte)
            self.assertNotIn(c["ticker"], fonte)
        self.assertNotRegex(fonte, r"\b[A-Z]{4}\d{1,2}_[NE]\d\b")


class DryRunECli(Base):
    def test_dry_run_sintetico_nao_escreve_nem_avalia(self):
        antes = sha_arquivos(self.coleta)
        rel = A.dry_run(coleta=self.coleta, saida=self.saida, sha_manifesto_hashes=self.sha_hashes,
                        git=GitFalso(), log=lambda *a: None)
        self.assertEqual((rel["casos"], rel["truncadas_na_geracao"]), (96, 2))
        self.assertEqual(rel["exatidao"], "nao_executada")
        self.assertEqual(rel["ragas"], {"faithfulness": {"PENDENTE": 96}, "answer_relevancy": {"PENDENTE": 96}})
        self.assertTrue(str(rel["ragas_liberado"]).startswith("bloqueado"))
        self.assertEqual(rel["protecao_sobrescrita"], "ok")
        self.assertFalse(os.path.exists(self.saida))
        self.assertEqual(sha_arquivos(self.coleta), antes)

    def test_dry_run_real_so_confere(self):
        saida = os.path.join(self.tmp.name, "saida_real")
        rel = A.dry_run(saida=saida, git=GitFalso(), log=lambda *a: None)
        self.assertEqual((rel["casos"], rel["truncadas_na_geracao"]), (96, 36))
        self.assertEqual(rel["disponibilidade"], {"presente": 69, "parcial": 15, "ausente": 12})
        self.assertFalse(os.path.exists(saida))

    def test_cli_exige_executar(self):
        with mock.patch("sys.stderr"):
            self.assertEqual(A.main(["exatidao", "--saida", self.saida], git=GitFalso()), 3)
            self.assertEqual(A.main(["ragas", "--metrica", "faithfulness", "--saida", self.saida], git=GitFalso()), 3)
        self.assertFalse(os.path.exists(self.saida))

    def test_executor_nao_escreve_na_coleta(self):
        fonte = open(os.path.join(PASTA, "avaliar_respostas_tcc2.py"), encoding="utf-8").read()
        self.assertNotIn("gravar_substituindo", fonte)
        self.assertEqual(A.COLETA, COLETA_REAL)
        self.assertNotEqual(os.path.normcase(A.SAIDA_PADRAO), os.path.normcase(COLETA_REAL))


if __name__ == "__main__":
    unittest.main()
