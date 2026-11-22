# avaliacao/ragas/avaliar_respostas_tcc2.py
#
# Executor da avaliação das 96 respostas congeladas do RAGAS do TCC 2
# (PROTOCOLO_RAGAS_TCC2.md, Seções 11, 11.1, 12 e 15; Emendas 1, 3 e 4).
#
# Etapas, separadas e nunca combinadas em índice:
#   exatidao        verificação determinística (exatidao.py congelado), com decisões
#                   manuais de sinal registradas em arquivo (nunca decididas aqui);
#   comportamento   modelo de anotação e validação da rubrica (comportamento.py
#                   congelado); a classificação é humana, sem LLM; os desvios do
#                   procedimento executado e o estado técnico PENDENTE_OPERACIONAL
#                   estão na Emenda 4;
#   ragas           Faithfulness e Answer Relevancy, uma métrica por chamada de
#                   ragas.evaluate (Emenda 3), só depois de exatidão, sinal e
#                   comportamento congelados em commit.
#
# Entradas: dataset congelado, coleta congelada (coleta_tcc2/, conferida por
# SHA256_COLETA.txt e pela configuração HISTÓRICA do manifesto — não pelo hash do
# protocolo emendado), instrumentos congelados. A coleta nunca é escrita.
# Saídas: avaliacao/ragas/avaliacao_tcc2/ (fora do git até o congelamento), sempre
# criadas de forma exclusiva: nada é sobrescrito.
#
# Uso:
#   python avaliar_respostas_tcc2.py dry-run [--verificar-ambiente]
#   python avaliar_respostas_tcc2.py exatidao --executar
#   python avaliar_respostas_tcc2.py comportamento --gerar-modelo | --validar
#   python avaliar_respostas_tcc2.py ragas --metrica faithfulness|answer_relevancy --executar
#          [--case-id ID ...] [--reavaliar-nan] [--pausa 10]
# O RAGAS só roda no venv da Emenda 3 (requirements_avaliacao.txt).

import argparse
import contextlib
import hashlib
import json
import logging
import math
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter
from datetime import datetime, timezone

PASTA = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(PASTA))
sys.path.insert(0, PASTA)

import coletar_respostas_tcc2 as C  # noqa: E402  (funções de selo/hash/gravação, sem alteração)
import comportamento as B  # noqa: E402
import exatidao as X  # noqa: E402

DATASET = C.DATASET
COLETA = os.path.join(PASTA, "coleta_tcc2")
SAIDA_PADRAO = os.path.join(PASTA, "avaliacao_tcc2")
CHAVE_PADRAO = os.path.join(RAIZ, "api_key.txt")
PROTOCOLO = os.path.join(PASTA, "PROTOCOLO_RAGAS_TCC2.md")

# Marcos congelados
SHA256_DATASET = "313bdf359fdeabb063ceec3bcca12ebfe3b52caae346b3ff1d9f3dc23196bc5e"
COMMIT_COLETA = "10eee310a6dfd0bc545f6d2a62bd82705b6624e5"
SHA256_SHA256_COLETA = "b8c016cea3a8903678bc7817f4c5b553c80bb98b6a7a5787d05ea4ce4eca45f2"  # SHA256_COLETA.txt
SHA256_CONFIG_HISTORICA = "b956544649f7d4f7a01435fb598c888c70d84cb3bbb5f9ddc9a7ebc6aec0793b"  # manifesto da coleta
N_CASOS = 96

# Avaliador (Seção 11; Emenda 3)
METRICAS = ("faithfulness", "answer_relevancy")
MODELO_AVALIADOR = "gemini-2.5-flash"
TEMPERATURA_CLIENTE = 0.0
TEMPERATURA_EFETIVA = {"faithfulness": 0.01, "answer_relevancy": 0.3}   # definidas pelo ragas 0.4.3
STRICTNESS = 3
RUN_CONFIG = {"timeout": 120, "max_retries": 3, "max_workers": 1}
PAUSA_PADRAO = 10.0
EMBEDDINGS = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
REVISAO_EMBEDDINGS = "4328cf26390c98c5e3c738b4460a05b95f4911f5"
VERSOES_FIXADAS = {"ragas": "0.4.3", "langchain-community": "0.4.2", "langchain-google-genai": "4.4.0"}
DEPENDENCIAS = ("ragas", "langchain-community", "langchain-google-genai", "langchain-core", "langchain",
                "langchain-openai", "google-genai", "openai", "instructor", "datasets",
                "sentence-transformers", "transformers", "torch", "huggingface-hub", "numpy")

# Arquivos que precisam estar commitados e limpos para qualquer etapa real
ARQUIVOS_VERSIONADOS = ("avaliacao/ragas/avaliar_respostas_tcc2.py", "avaliacao/ragas/exatidao.py",
                        "avaliacao/ragas/comportamento.py", "avaliacao/ragas/RUBRICA_COMPORTAMENTO_TCC2.md",
                        "avaliacao/ragas/PROTOCOLO_RAGAS_TCC2.md", "avaliacao/ragas/dataset_tcc2.json",
                        "avaliacao/ragas/requirements_avaliacao.txt", "avaliacao/ragas/requirements_avaliacao.lock",
                        "avaliacao/ragas/coleta_tcc2")

ESQUEMA = 1
_RE_RESPOSTA = re.compile(r"[A-Z0-9]+_[NE]\d\.json")
_RE_ERRO = re.compile(r"[A-Z0-9]+_[NE]\d\.erro_\d{2}\.json")


class Bloqueio(RuntimeError):
    """Condição que impede a avaliação (integridade, ordem das etapas, sobrescrita)."""


def agora_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ── coleta congelada ──────────────────────────────────────────────────────────

def carregar_coleta(ds: dict, sha_dataset: str, coleta: str = COLETA,
                    sha_manifesto_hashes: str = SHA256_SHA256_COLETA,
                    sha_config_historica: str = SHA256_CONFIG_HISTORICA,
                    sha_dataset_esperado: str = SHA256_DATASET) -> list[dict]:
    """
    Confere a coleta congelada e devolve os 96 casos prontos para avaliar, na ordem do
    dataset. Aborta (Bloqueio) com qualquer divergência. Só lê a coleta.
    """
    if sha_dataset != sha_dataset_esperado:
        raise Bloqueio(f"SHA-256 do dataset {sha_dataset} difere do congelado")
    p_hashes = os.path.join(coleta, "SHA256_COLETA.txt")
    if not os.path.isfile(p_hashes):
        raise Bloqueio("SHA256_COLETA.txt ausente: coleta não congelada")
    with open(p_hashes, "rb") as f:
        bruto = f.read()
    if sha256_bytes(bruto) != sha_manifesto_hashes:
        raise Bloqueio("SHA256_COLETA.txt difere do congelado")
    listados = {}
    for linha in bruto.decode("utf-8").splitlines():
        h, _, rel = linha.partition("  ")
        if not re.fullmatch(r"[0-9a-f]{64}", h) or not rel:
            raise Bloqueio(f"linha inválida em SHA256_COLETA.txt: {linha!r}")
        listados[rel] = h
    presentes = set()
    for raiz, _, arqs in os.walk(coleta):
        for a in arqs:
            presentes.add(os.path.relpath(os.path.join(raiz, a), coleta).replace(os.sep, "/"))
    presentes.discard("SHA256_COLETA.txt")
    if presentes != set(listados):
        raise Bloqueio(f"arquivos da coleta diferem do congelado: sobrando {sorted(presentes - set(listados))}, "
                       f"faltando {sorted(set(listados) - presentes)}")
    for rel, h in listados.items():
        with open(os.path.join(coleta, *rel.split("/")), "rb") as f:
            if sha256_bytes(f.read()) != h:
                raise Bloqueio(f"arquivo da coleta alterado após o congelamento: {rel}")

    with open(os.path.join(coleta, "manifesto_config.json"), encoding="utf-8") as f:
        manifesto = json.load(f)
    if not (C.sha_config(manifesto["configuracao"]) == manifesto["sha256_configuracao"] == sha_config_historica):
        raise Bloqueio("manifesto da coleta não confere com a configuração histórica")
    if manifesto["configuracao"]["dataset"]["sha256"] != sha_dataset:
        raise Bloqueio("o manifesto da coleta aponta para outro dataset")

    ordem = [c["id"] for c in ds["casos"]]
    if len(ordem) != N_CASOS or len(set(ordem)) != N_CASOS:
        raise Bloqueio("o dataset não tem 96 case_ids únicos")
    arquivos = sorted(n for n in os.listdir(os.path.join(coleta, "respostas")) if _RE_RESPOSTA.fullmatch(n))
    ids = [n[:-5] for n in arquivos]
    if set(ids) != set(ordem) or len(ids) != N_CASOS:
        raise Bloqueio(f"case_ids da coleta não correspondem ao dataset: faltando {sorted(set(ordem) - set(ids))}, "
                       f"sobrando {sorted(set(ids) - set(ordem))}")
    por_id = {c["id"]: c for c in ds["casos"]}
    casos, vistos = [], set()
    for cid in ordem:
        with open(os.path.join(coleta, "respostas", f"{cid}.json"), encoding="utf-8") as f:
            r = json.load(f)
        caso = por_id[cid]
        if r.get("case_id") != cid or cid in vistos:
            raise Bloqueio(f"case_id duplicado ou trocado no registro {cid}.json ({r.get('case_id')})")
        vistos.add(cid)
        if not C.selo_confere(r) or r.get("status") != "CONCLUIDO" or r.get("erro") is not None:
            raise Bloqueio(f"registro {cid} adulterado ou não concluído")
        if r["sha256_configuracao"] != sha_config_historica or r["sha256_dataset"] != sha_dataset:
            raise Bloqueio(f"registro {cid} não pertence à configuração histórica da coleta")
        if r["ticker"] != caso["ticker"] or r["pergunta"] != caso["pergunta"] or \
                r["disponibilidade_congelada"] != caso["disponibilidade"]:
            raise Bloqueio(f"registro {cid} difere do caso do dataset")
        resposta = r.get("resposta")
        if not isinstance(resposta, str) or not resposta.strip():
            raise Bloqueio(f"registro {cid} sem resposta")
        emp = C.empresa_do_caso(ds, caso)
        ctx = r["contexto"]
        textos = [t["texto"] for t in ctx["trechos"]]
        if C.sha256_texto(ctx["ctx_num"]) != emp["sha256_ctx_num"] or ctx["sha256_ctx_num"] != emp["sha256_ctx_num"] \
                or [C.sha256_texto(t) for t in textos] != emp["sha256_trechos"] \
                or [t["sha256"] for t in ctx["trechos"]] != emp["sha256_trechos"]:
            raise Bloqueio(f"contexto do registro {cid} difere do congelado")
        casos.append({
            "case_id": cid, "ticker": caso["ticker"], "estrutura": caso["estrutura"],
            "categoria": caso["categoria"], "disponibilidade": caso["disponibilidade"],
            "pergunta": caso["pergunta"], "resposta": resposta, "sha256_resposta": C.sha256_texto(resposta),
            "contextos": textos, "sha256_ctx_num": emp["sha256_ctx_num"], "sha256_trechos": emp["sha256_trechos"],
            "reference": caso["gabarito"], "truncada_na_geracao": bool(r["geracao"]["truncada_por_limite"]),
            "tentativa_geracao": r["tentativa"], "caso_dataset": caso,
        })
    return casos


def carregar_entradas(dataset_path: str = DATASET, coleta: str = COLETA, **kw) -> tuple[dict, str, list[dict]]:
    try:
        ds, sha = C.carregar_dataset(dataset_path)
    except C.Bloqueio as e:
        raise Bloqueio(str(e)) from None
    return ds, sha, carregar_coleta(ds, sha, coleta, **kw)


# ── git e proveniência ────────────────────────────────────────────────────────

class Git:
    def __init__(self, raiz: str = RAIZ):
        self.raiz = raiz

    def _run(self, *args) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], cwd=self.raiz, capture_output=True, text=True)

    def head(self) -> str:
        return self._run("rev-parse", "HEAD").stdout.strip()

    def pendencias(self, caminhos) -> list[str]:
        r = self._run("status", "--porcelain", "--untracked-files=all", "--", *caminhos)
        return [l for l in r.stdout.splitlines() if l.strip()]

    def rastreado(self, caminho: str) -> bool:
        return self._run("ls-files", "--error-unmatch", "--", caminho).returncode == 0


def verificar_git(git, extras=()) -> str:
    if git is None:
        raise Bloqueio("git não disponível: a avaliação real exige código e instrumentos commitados")
    pend = git.pendencias(list(ARQUIVOS_VERSIONADOS) + list(extras))
    if pend:
        raise Bloqueio("há alterações não commitadas em código/instrumentos/coleta: " + "; ".join(pend))
    return git.head()


def proveniencia(sha_dataset: str, head: str | None) -> dict:
    with open(PROTOCOLO, "rb") as f:
        prot = f.read()
    with open(os.path.abspath(__file__), "rb") as f:
        executor = f.read()
    return {"commit": head, "commit_coleta": COMMIT_COLETA, "sha256_executor": sha256_bytes(executor),
            "sha256_protocolo_emendado": sha256_bytes(prot), "sha256_dataset": sha_dataset,
            "sha256_configuracao_historica_coleta": SHA256_CONFIG_HISTORICA,
            "sha256_SHA256_COLETA": SHA256_SHA256_COLETA,
            "sha256_exatidao_py": C.sha256_arquivo(X.__file__),
            "sha256_comportamento_py": C.sha256_arquivo(B.__file__),
            "python": platform.python_version()}


@contextlib.contextmanager
def trava(saida: str):
    os.makedirs(saida, exist_ok=True)
    p = os.path.join(saida, ".trava")
    try:
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    except FileExistsError:
        raise Bloqueio(f"outra avaliação em andamento (ou encerrada sem liberar): remova {p} após conferir")
    os.write(fd, agora_utc().encode())
    os.close(fd)
    try:
        yield
    finally:
        os.remove(p)


def _ler_json(caminho: str):
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


# ── A. exatidão determinística ────────────────────────────────────────────────

def _pendentes_do_caso(caso: dict, textos_pendentes: list[str]) -> list[dict]:
    """Números de sinal inconclusivo que a conciliação precisa: posição, texto e oração."""
    resp = caso["resposta"]
    oracoes = X._oracoes(resp)
    return [{"inicio": n.inicio, "texto": n.texto, "oracao": resp[slice(*oracoes[n.oracao])].strip()}
            for n in X.extrair_numeros(resp) if n.sinal == "?" and n.texto in textos_pendentes]


def ler_decisoes_sinal(caminho: str, casos: list[dict]) -> dict:
    """
    Arquivo de decisões manuais de sinal (Seção 11.1, regra 5), preenchido pelo autor:
    {"decidido_por": "...", "decidido_em": "...",
     "casos": {case_id: {"sha256_resposta": "...", "decisoes": [
         {"inicio": int, "texto": "...", "sinal": "+"|"-", "justificativa": "..."}]}}}
    Devolve {case_id: {inicio: sinal}}. Cada decisão tem de apontar para um número de
    sinal inconclusivo da resposta congelada.
    """
    if not os.path.exists(caminho):
        return {}
    d = _ler_json(caminho)
    if not str(d.get("decidido_por", "")).strip() or not str(d.get("decidido_em", "")).strip():
        raise Bloqueio("decisões de sinal sem autor ou data")
    por_id = {c["case_id"]: c for c in casos}
    out = {}
    for cid, reg in (d.get("casos") or {}).items():
        caso = por_id.get(cid)
        if caso is None:
            raise Bloqueio(f"decisão de sinal para caso inexistente: {cid}")
        if reg.get("sha256_resposta") != caso["sha256_resposta"]:
            raise Bloqueio(f"decisão de sinal de {cid} não corresponde à resposta congelada")
        ambiguos = {n.inicio: n.texto for n in X.extrair_numeros(caso["resposta"]) if n.sinal == "?"}
        out[cid] = {}
        for dec in reg.get("decisoes") or []:
            ini = dec.get("inicio")
            if ini not in ambiguos or dec.get("texto") != ambiguos[ini]:
                raise Bloqueio(f"decisão de sinal de {cid} não aponta para um número de sinal inconclusivo: {dec}")
            if dec.get("sinal") not in ("+", "-") or not str(dec.get("justificativa", "")).strip():
                raise Bloqueio(f"decisão de sinal de {cid} sem sinal válido ou sem justificativa: {dec}")
            out[cid][ini] = dec["sinal"]
    return out


def exatidao(*, casos: list[dict], sha_dataset: str, saida: str = SAIDA_PADRAO, git=None,
             exigir_git: bool = True, log=print) -> dict:
    """
    Classifica os 96 casos com exatidao.classificar. Se algum depender de decisão manual de
    sinal ainda não registrada, grava a lista de pendências e NÃO grava resultado. Quando
    não há pendência, grava resultado_exatidao.json (uma vez; nunca sobrescreve).
    """
    head = verificar_git(git) if exigir_git else (git.head() if git else None)
    pasta = os.path.join(saida, "exatidao")
    os.makedirs(pasta, exist_ok=True)
    p_res = os.path.join(pasta, "resultado_exatidao.json")
    p_dec = os.path.join(pasta, "decisoes_sinal.json")
    if os.path.exists(p_res):
        raise Bloqueio("resultado_exatidao.json já existe: a exatidão não é recalculada nem sobrescrita")
    with trava(saida):
        decisoes = ler_decisoes_sinal(p_dec, casos)
        resultados, pendencias = [], {}
        for caso in casos:
            r = X.classificar(caso["resposta"], caso["caso_dataset"], decisoes.get(caso["case_id"], {}))
            if r["classe"] == X.PENDENTE_SINAL:
                pendencias[caso["case_id"]] = {"sha256_resposta": caso["sha256_resposta"],
                                               "numeros": _pendentes_do_caso(caso, r["pendencias_sinal"])}
            resultados.append({"case_id": caso["case_id"], "ticker": caso["ticker"], "categoria": caso["categoria"],
                               "estrutura": caso["estrutura"], "disponibilidade": caso["disponibilidade"],
                               "sha256_resposta": caso["sha256_resposta"],
                               "truncada_na_geracao": caso["truncada_na_geracao"],
                               "decisoes_manuais_sinal": {str(k): v for k, v in
                                                          sorted(decisoes.get(caso["case_id"], {}).items())},
                               **r})
        if pendencias:
            k = 1
            while os.path.exists(os.path.join(pasta, f"pendencias_sinal_{k:02d}.json")):
                k += 1
            anterior = os.path.join(pasta, f"pendencias_sinal_{k - 1:02d}.json")
            if k > 1 and _ler_json(anterior).get("casos") == pendencias:       # nada mudou: não duplica
                log(f"exatidão: pendências de sinal inalteradas -> {anterior}")
                return {"status": "pendente_sinal", "pendencias": sorted(pendencias), "arquivo": anterior}
            destino = os.path.join(pasta, f"pendencias_sinal_{k:02d}.json")
            C.gravar_exclusivo(destino, C.selar({
                "esquema": ESQUEMA, "gerado_em": agora_utc(), "n_casos_pendentes": len(pendencias),
                "instrucao": "Decidir o sinal de cada número em decisoes_sinal.json (Seção 11.1, regra 5) "
                             "e rodar a exatidão de novo. Nenhum resultado de exatidão foi gravado.",
                "casos": pendencias}))
            log(f"exatidão: {len(pendencias)} caso(s) aguardam decisão manual de sinal -> {destino}")
            return {"status": "pendente_sinal", "pendencias": sorted(pendencias), "arquivo": destino}
        registro = {"esquema": ESQUEMA, "etapa": "exatidao", "gerado_em": agora_utc(),
                    "proveniencia": proveniencia(sha_dataset, head),
                    "sha256_decisoes_sinal": C.sha256_arquivo(p_dec) if os.path.exists(p_dec) else None,
                    "n_casos": len(resultados), "resultados": resultados}
        C.gravar_exclusivo(p_res, C.selar(registro))
        log(f"exatidão: {len(resultados)} casos gravados em {p_res}")
        return {"status": "concluida", "arquivo": p_res}


def conferir_resultado_exatidao(saida: str, casos: list[dict]) -> dict:
    p = os.path.join(saida, "exatidao", "resultado_exatidao.json")
    if not os.path.exists(p):
        raise Bloqueio("exatidão ainda não concluída")
    r = _ler_json(p)
    if not C.selo_confere(r):
        raise Bloqueio("resultado_exatidao.json adulterado")
    esperado = {c["case_id"]: c["sha256_resposta"] for c in casos}
    obtido = {x["case_id"]: x["sha256_resposta"] for x in r["resultados"]}
    if obtido != esperado or len(r["resultados"]) != N_CASOS:
        raise Bloqueio("resultado de exatidão não corresponde às 96 respostas congeladas")
    if any(x["classe"] not in (X.CORRETO, X.PARCIALMENTE_CORRETO, X.INCORRETO, X.NAO_APLICAVEL)
           for x in r["resultados"]):
        raise Bloqueio("resultado de exatidão com classe pendente ou inválida")
    p_dec = os.path.join(saida, "exatidao", "decisoes_sinal.json")
    atual = C.sha256_arquivo(p_dec) if os.path.exists(p_dec) else None
    if atual != r["sha256_decisoes_sinal"]:
        raise Bloqueio("decisoes_sinal.json mudou depois do resultado de exatidão")
    return r


# ── B. comportamento (rubrica; classificação humana) ──────────────────────────

def arquivo_anotacoes(saida: str) -> str:
    return os.path.join(saida, "comportamento", "anotacoes_comportamento.json")


def gerar_modelo_anotacao(casos: list[dict], saida: str = SAIDA_PADRAO) -> str:
    """Cria (uma vez) o arquivo de anotação com um registro vazio por caso."""
    p = arquivo_anotacoes(saida)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    registros = [{"id": c["case_id"], "ticker": c["ticker"], "categoria": c["categoria"],
                  "disponibilidade": c["disponibilidade"], "sha256_resposta": c["sha256_resposta"],
                  "afirmacoes": [], "declara_limitacao": None, "entrega_informacao_sustentada": None,
                  "classe": None, "abstencao_em_caso_presente": None, "justificativa": "",
                  "classificador": "", "classificado_em": "", "scores_ragas_consultados": False}
                 for c in casos]
    C.gravar_exclusivo(p, {
        "esquema": ESQUEMA, "rubrica": "avaliacao/ragas/RUBRICA_COMPORTAMENTO_TCC2.md",
        "instrucoes": [
            "Um registro por caso. Rotular cada afirmação da resposta: S, E, A ou N (rubrica, Seção 3); "
            "E e A exigem motivo e evidência no contexto.",
            "Preencher declara_limitacao e entrega_informacao_sustentada.",
            "A classe NÃO é escolhida: usar a classe derivada que o validador informa "
            "(comportamento.derivar_classe) e o respectivo abstencao_em_caso_presente.",
            "Materiais permitidos: pergunta, resposta, trechos de contexto, disponibilidade e gabarito. "
            "Nenhum score RAGAS pode ser consultado (scores_ragas_consultados = false).",
        ],
        "registros": registros})
    return p


# Emenda 4: estado técnico (não é classe de comportamento) dos casos truncados que a regra
# congelada não classifica. A autorização vem só do arquivo de pendências; nenhum id aqui.
PENDENTE_OPERACIONAL = "PENDENTE_OPERACIONAL"
ESTADO_PENDENCIA = "PENDENTE_POR_TRUNCAMENTO_E_REGRA_DO_VALIDADOR"
RECUSA_ESTRUTURAL = "caso parcial/ausente sem afirmação E/A e sem declaração de limitação"  # comportamento.py


def arquivo_pendencias(saida: str) -> str:
    return os.path.join(saida, "comportamento", "pendencias_comportamento.json")


def documentos_comportamento(saida: str) -> list[str]:
    """Documentos da anotação que precisam estar congelados em commit antes do RAGAS (Emenda 4)."""
    pasta = os.path.join(saida, "comportamento")
    return [os.path.join(pasta, "CONVENCOES_ANOTACAO_COMPORTAMENTO.md"),
            os.path.join(pasta, "RATIFICACAO_COMPORTAMENTO.md")]


def ler_pendencias(casos: list[dict], saida: str = SAIDA_PADRAO) -> dict | None:
    """
    Lê pendencias_comportamento.json (Emenda 4) e devolve {case_id: entrada} da lista
    "pendencias". Sem o arquivo, devolve None (comportamento anterior). Estrutura inválida,
    case_id inexistente ou repetido bloqueiam.
    """
    p = arquivo_pendencias(saida)
    if not os.path.exists(p):
        return None
    doc = _ler_json(p)
    lista = doc.get("pendencias") if isinstance(doc, dict) else None
    if not isinstance(lista, list) or not all(isinstance(e, dict) for e in lista):
        raise Bloqueio("arquivo de pendências de comportamento sem lista 'pendencias' válida")
    ids = [e.get("id") for e in lista]
    dup = sorted({str(i) for i in ids if ids.count(i) > 1})
    if dup:
        raise Bloqueio(f"pendência de comportamento com case_id duplicado: {dup}")
    estranhos = sorted({str(i) for i in ids} - {c["case_id"] for c in casos})
    if estranhos:
        raise Bloqueio(f"pendência de comportamento com case_id inexistente: {estranhos}")
    return {e["id"]: e for e in lista}


def conferir_pendente(reg: dict | None, caso: dict, entrada: dict) -> str | None:
    """
    Condições da Emenda 4 para PENDENTE_OPERACIONAL. Devolve None se todas são satisfeitas,
    ou o motivo da primeira que falha (o registro é então INVALIDO).
    """
    if reg is None:
        return "listado nas pendências, mas sem registro de anotação"
    if entrada.get("estado") != ESTADO_PENDENCIA:
        return f"pendência com estado diferente de {ESTADO_PENDENCIA}"
    if entrada.get("disponibilidade") != caso["disponibilidade"] or \
            entrada.get("truncada_na_geracao") is not caso["truncada_na_geracao"]:
        return "pendência difere da coleta congelada (disponibilidade ou truncamento)"
    if caso["disponibilidade"] not in ("parcial", "ausente"):
        return "PENDENTE_OPERACIONAL só se aplica a casos parcial ou ausente"
    if caso["truncada_na_geracao"] is not True:
        return "resposta não truncada por limite de tokens na coleta congelada"
    if reg.get("sha256_resposta") != caso["sha256_resposta"]:
        return "sha256_resposta difere da resposta congelada"
    # verificações de comportamento.validar_registro que não dependem da classe
    faltando = [c for c in B.CAMPOS if c not in reg]
    if faltando:
        return f"campos ausentes: {faltando}"
    if reg["id"] != caso["case_id"] or reg["disponibilidade"] != caso["disponibilidade"]:
        return "id ou disponibilidade diferente do dataset congelado"
    if reg["scores_ragas_consultados"] is not False:
        return "a classificação deve ser feita sem consultar scores RAGAS"
    if not str(reg["justificativa"]).strip() or not str(reg["classificador"]).strip():
        return "justificativa e classificador são obrigatórios"
    afs = reg["afirmacoes"]
    if not isinstance(afs, list) or any(not isinstance(a, dict) or a.get("rotulo") not in B.ROTULOS
                                         or not str(a.get("trecho_resposta", "")).strip() for a in afs):
        return "afirmação inválida"
    rotulos = [a["rotulo"] for a in afs]
    if any(r in ("E", "A") for r in rotulos):
        return "há afirmação E ou A: o caso é classificável"
    if reg["declara_limitacao"] is not False:
        return "declara_limitacao deve ser false"
    if not isinstance(reg["entrega_informacao_sustentada"], bool):
        return "entrega_informacao_sustentada não preenchido"
    if reg["classe"] is not None or reg["abstencao_em_caso_presente"] is not None:
        return "listado nas pendências, mas com classe ou abstencao_em_caso_presente preenchidos"
    try:
        B.derivar_classe(caso["disponibilidade"], rotulos, reg["declara_limitacao"],
                         reg["entrega_informacao_sustentada"])
    except B.RegistroInconsistente as e:
        if str(e).startswith(RECUSA_ESTRUTURAL):
            return None
        return f"recusa diferente da regra estrutural: {e}"
    return "comportamento.derivar_classe não recusa o registro: o caso é classificável"


def validar_anotacoes(casos: list[dict], saida: str = SAIDA_PADRAO) -> dict:
    """
    Valida o arquivo de anotação: VALIDO (registro completo e consistente com a regra da
    rubrica), INCOMPLETO (ainda sem classe; informa a classe derivada quando possível) ou
    INVALIDO (inconsistente). Com pendencias_comportamento.json (Emenda 4), um caso listado
    é PENDENTE_OPERACIONAL se cumprir todas as condições, e INVALIDO caso contrário.
    Não escreve nada.
    """
    p = arquivo_anotacoes(saida)
    if not os.path.exists(p):
        raise Bloqueio("arquivo de anotação de comportamento inexistente")
    doc = _ler_json(p)
    por_id = {c["case_id"]: c for c in casos}
    regs = doc.get("registros")
    if not isinstance(regs, list):
        raise Bloqueio("arquivo de anotação sem lista de registros")
    ids = [r.get("id") for r in regs]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise Bloqueio(f"anotação com case_id duplicado: {dup}")
    estranhos = sorted(set(ids) - set(por_id))
    if estranhos:
        raise Bloqueio(f"anotação com case_id inexistente: {estranhos}")
    pendencias = ler_pendencias(casos, saida)
    status = {}
    for cid in por_id:
        reg = next((r for r in regs if r.get("id") == cid), None)
        caso = por_id[cid]
        if pendencias is not None and cid in pendencias:
            motivo = conferir_pendente(reg, caso, pendencias[cid])
            status[cid] = {"status": PENDENTE_OPERACIONAL, "motivo": ESTADO_PENDENCIA} if motivo is None \
                else {"status": "INVALIDO", "motivo": motivo}
            continue
        if reg is None:
            status[cid] = {"status": "INCOMPLETO", "motivo": "sem registro"}
            continue
        if reg.get("sha256_resposta") != caso["sha256_resposta"]:
            status[cid] = {"status": "INVALIDO", "motivo": "sha256_resposta difere da resposta congelada"}
            continue
        if reg.get("classe") in (None, ""):
            st = {"status": "INCOMPLETO", "motivo": "classe não registrada"}
            if reg.get("afirmacoes") is not None and reg.get("declara_limitacao") is not None:
                try:
                    classe, abst = B.derivar_classe(caso["disponibilidade"],
                                                    [a.get("rotulo") for a in reg["afirmacoes"]],
                                                    reg["declara_limitacao"],
                                                    bool(reg.get("entrega_informacao_sustentada")))
                    st["classe_derivada"], st["abstencao_em_caso_presente_derivada"] = classe, abst
                except B.RegistroInconsistente as e:
                    st = {"status": "INVALIDO", "motivo": str(e)}
            status[cid] = st
            continue
        try:
            B.validar_registro(reg, {"id": cid, "disponibilidade": caso["disponibilidade"]})
            status[cid] = {"status": "VALIDO", "classe": reg["classe"]}
        except B.RegistroInconsistente as e:
            status[cid] = {"status": "INVALIDO", "motivo": str(e)}
    estados = ("VALIDO", "INCOMPLETO", "INVALIDO") if pendencias is None \
        else ("VALIDO", PENDENTE_OPERACIONAL, "INCOMPLETO", "INVALIDO")
    cont = {s: sum(1 for v in status.values() if v["status"] == s) for s in estados}
    completo = cont["INVALIDO"] == 0 and cont["INCOMPLETO"] == 0 and \
        cont["VALIDO"] + cont.get(PENDENTE_OPERACIONAL, 0) == N_CASOS
    return {"arquivo": p, "contagem": cont, "completo": completo, "casos": status}


# ── C/D. RAGAS ────────────────────────────────────────────────────────────────

def verificar_etapas_anteriores(casos: list[dict], saida: str, git) -> dict:
    """
    RAGAS só depois de exatidão, sinal e comportamento completos e congelados em commit.
    Emenda 4: também convenções, ratificação e (se existir) pendências do comportamento.
    """
    r_ex = conferir_resultado_exatidao(saida, casos)
    val = validar_anotacoes(casos, saida)
    if not val["completo"]:
        raise Bloqueio(f"rubrica de comportamento incompleta ou inválida: {val['contagem']}")
    docs = documentos_comportamento(saida)
    ausentes = [os.path.basename(d) for d in docs if not os.path.exists(d)]
    if ausentes:
        raise Bloqueio(f"documentos da anotação de comportamento ausentes (Emenda 4): {ausentes}")
    p_pend = arquivo_pendencias(saida)
    congelar = [arquivo_anotacoes(saida), os.path.join(saida, "exatidao", "resultado_exatidao.json"), *docs]
    if os.path.exists(p_pend):
        congelar.append(p_pend)
    p_dec = os.path.join(saida, "exatidao", "decisoes_sinal.json")
    if os.path.exists(p_dec):
        congelar.append(p_dec)
    rel = [os.path.relpath(p, RAIZ).replace(os.sep, "/") for p in congelar]
    if git is None or any(not git.rastreado(p) for p in rel) or git.pendencias(rel):
        raise Bloqueio("exatidão, decisões de sinal e comportamento (anotações, pendências, convenções e "
                       "ratificação) precisam estar congelados em commit antes do RAGAS "
                       "(protocolo, Seção 12; rubrica, Seção 1; Emenda 4)")
    return {"sha256_resultado_exatidao": C.sha256_arquivo(congelar[1]),
            "sha256_anotacoes_comportamento": C.sha256_arquivo(congelar[0]),
            "sha256_decisoes_sinal": r_ex["sha256_decisoes_sinal"],
            "sha256_pendencias_comportamento": C.sha256_arquivo(p_pend) if os.path.exists(p_pend) else None,
            "sha256_convencoes_comportamento": C.sha256_arquivo(docs[0]),
            "sha256_ratificacao_comportamento": C.sha256_arquivo(docs[1])}


def _arquivos_ragas(saida: str, metrica: str, cid: str, t: int) -> tuple[str, str]:
    base = os.path.join(saida, "ragas", metrica, f"{cid}.tentativa_{t:02d}")
    return base + ".inicio.json", base + ".json"


def estado_ragas(saida: str, metrica: str, caso: dict) -> dict:
    """
    PENDENTE | CONCLUIDO (score válido na 1ª) | NAN_1 (1ª inválida: NaN ou interrompida;
    admite uma reavaliação) | FINAL (2ª tentativa existe; nada mais é permitido).
    """
    def ler(t):
        ini, res = _arquivos_ragas(saida, metrica, caso["case_id"], t)
        if os.path.exists(res):
            r = _ler_json(res)
            if not C.selo_confere(r) or r.get("sha256_resposta") != caso["sha256_resposta"]:
                raise Bloqueio(f"resultado RAGAS adulterado ou de outra resposta: {res}")
            return "resultado", r
        return ("interrompida", None) if os.path.exists(ini) else (None, None)
    s1, r1 = ler(1)
    s2, _ = ler(2)
    if s2 is not None:
        return {"estado": "FINAL", "tentativas": 2}
    if s1 is None:
        return {"estado": "PENDENTE", "tentativas": 0}
    if s1 == "resultado" and r1["valido"]:
        return {"estado": "CONCLUIDO", "tentativas": 1}
    return {"estado": "NAN_1", "tentativas": 1, "motivo": "interrompida" if s1 == "interrompida" else "NaN"}


def _score_valido(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and 0.0 <= x <= 1.0


def avaliar_ragas(*, metrica: str, casos: list[dict], sha_dataset: str, avaliador, git, saida: str = SAIDA_PADRAO,
                  case_ids=None, reavaliar_nan: bool = False, pausa: float = PAUSA_PADRAO, log=print) -> dict:
    """
    Calcula UMA métrica (Emenda 3) para os casos selecionados. Sem --reavaliar-nan: só casos
    nunca avaliados. Com --reavaliar-nan: só casos com a 1ª tentativa inválida, uma única vez
    (tentativa 2), preservando a 1ª. Grava um marcador antes da chamada e o resultado depois,
    ambos exclusivos.
    """
    if metrica not in METRICAS:
        raise Bloqueio(f"métrica desconhecida: {metrica}")
    head = verificar_git(git)
    congelados = verificar_etapas_anteriores(casos, saida, git)
    ids = [c["case_id"] for c in casos]
    if case_ids:
        desconhecidos = sorted(set(case_ids) - set(ids))
        if desconhecidos:
            raise Bloqueio(f"case_id inexistente: {desconhecidos}")
    alvo = [c for c in casos if not case_ids or c["case_id"] in set(case_ids)]
    os.makedirs(os.path.join(saida, "ragas", metrica), exist_ok=True)
    executados = []
    with trava(saida):
        selecao = []
        for c in alvo:
            e = estado_ragas(saida, metrica, c)
            if (not reavaliar_nan and e["estado"] == "PENDENTE") or (reavaliar_nan and e["estado"] == "NAN_1"):
                selecao.append((c, 2 if reavaliar_nan else 1))
        descricao = avaliador.descricao()
        prov = proveniencia(sha_dataset, head)
        for n, (c, t) in enumerate(selecao, 1):
            ini, res = _arquivos_ragas(saida, metrica, c["case_id"], t)
            entrada = {"sha256_pergunta": C.sha256_texto(c["pergunta"]), "sha256_resposta": c["sha256_resposta"],
                       "sha256_ctx_num": c["sha256_ctx_num"], "sha256_trechos": c["sha256_trechos"],
                       "sha256_reference": C.sha256_texto(c["reference"]),
                       "truncada_na_geracao": c["truncada_na_geracao"], "disponibilidade": c["disponibilidade"],
                       "categoria": c["categoria"], "estrutura": c["estrutura"], "ticker": c["ticker"]}
            inicio = agora_utc()
            C.gravar_exclusivo(ini, C.selar({"esquema": ESQUEMA, "case_id": c["case_id"], "metrica": metrica,
                                             "tentativa": t, "inicio_utc": inicio,
                                             "sha256_resposta": c["sha256_resposta"]}))
            t0 = time.monotonic()
            amostra = {"user_input": c["pergunta"], "response": c["resposta"],
                       "retrieved_contexts": list(c["contextos"]), "reference": c["reference"]}
            interromper = None
            try:
                saida_av = avaliador.avaliar(metrica, amostra)
                score = saida_av.get("score")
                erros = list(saida_av.get("erros") or [])
            except Exception as ex:          # falha fora do evaluate: registra e interrompe
                saida_av, score = {}, None
                erros = [f"{type(ex).__name__}: {C.sanitizar(ex, getattr(avaliador, 'segredos', ()))}"]
                interromper = ex
            valido = _score_valido(score)
            registro = {"esquema": ESQUEMA, "etapa": "ragas", "case_id": c["case_id"], "metrica": metrica,
                        "tentativa": t, "passada": "reavaliacao_nan" if t == 2 else "avaliacao",
                        "score": float(score) if valido else None, "valido": valido,
                        "nan": not valido, "erros": erros,
                        "modelos_retornados": saida_av.get("modelos_retornados") or [],
                        "uso_tokens": saida_av.get("uso_tokens"),
                        "sha256_resposta": c["sha256_resposta"], "entrada": entrada,
                        "avaliador": {**descricao, "temperatura_efetiva": TEMPERATURA_EFETIVA[metrica]},
                        "etapas_anteriores_congeladas": congelados, "proveniencia": prov,
                        "inicio_utc": inicio, "fim_utc": agora_utc(),
                        "duracao_s": round(time.monotonic() - t0, 3)}
            C.gravar_exclusivo(res, C.selar(registro))
            executados.append({"case_id": c["case_id"], "tentativa": t, "valido": valido})
            log(f"[{n}/{len(selecao)}] {c['case_id']} {metrica} t{t}: {'válido' if valido else 'INVÁLIDO (NaN)'}")
            if interromper is not None:
                log(f"execução interrompida por falha do avaliador: {erros[0]}")
                return {"executados": executados, "encerramento": "erro"}
            if pausa and n < len(selecao):
                time.sleep(pausa)
    return {"executados": executados, "encerramento": "completa"}


class AvaliadorRagas:
    """
    Avaliador real (Seção 11 + Emenda 3): código do TCC 1, uma métrica por evaluate().
    Importa ragas/langchain só aqui; exige o venv da Emenda 3. Faz chamadas à API.
    `chat` só é passado nos testes (modelo falso do langchain, sem rede).
    """

    def __init__(self, chave: str, chat=None):
        self.segredos = (chave,)
        os.environ["RAGAS_DO_NOT_TRACK"] = "true"
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        verificar_ambiente(exigir=True)
        from types import ModuleType
        if "langchain_community.chat_models.vertexai" not in sys.modules:   # stub do TCC 1
            stub = ModuleType("langchain_community.chat_models.vertexai")
            stub.ChatVertexAI = type("ChatVertexAI", (), {})
            sys.modules["langchain_community.chat_models.vertexai"] = stub
        from ragas import EvaluationDataset, evaluate
        from ragas.dataset_schema import SingleTurnSample
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from ragas.llms import LangchainLLMWrapper
        from ragas.metrics._answer_relevance import AnswerRelevancy
        from ragas.metrics._faithfulness import Faithfulness
        from ragas.run_config import RunConfig
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_google_genai import ChatGoogleGenerativeAI
        self._ED, self._evaluate, self._STS, self._RunConfig = EvaluationDataset, evaluate, SingleTurnSample, RunConfig
        if chat is None:
            chat = ChatGoogleGenerativeAI(model=MODELO_AVALIADOR, google_api_key=chave,
                                          temperature=TEMPERATURA_CLIENTE)
        llm = LangchainLLMWrapper(chat)
        emb = LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(model_name=EMBEDDINGS))
        self._metricas = {"faithfulness": Faithfulness(llm=llm),
                          "answer_relevancy": AnswerRelevancy(llm=llm, embeddings=emb)}
        if self._metricas["answer_relevancy"].strictness != STRICTNESS:
            raise Bloqueio("strictness do Answer Relevancy difere de 3")

    def descricao(self) -> dict:
        return {"modelo": MODELO_AVALIADOR, "temperatura_cliente": TEMPERATURA_CLIENTE,
                "temperaturas_efetivas_ragas": TEMPERATURA_EFETIVA, "strictness": STRICTNESS,
                "run_config": RUN_CONFIG, "embeddings": EMBEDDINGS, "revisao_embeddings": REVISAO_EMBEDDINGS,
                "wrapper": "ragas.llms.LangchainLLMWrapper (sem bypass)", "execucao": "ragas.evaluate, 1 métrica, 1 amostra",
                "dependencias": versoes_dependencias()}

    def avaliar(self, metrica: str, amostra: dict) -> dict:
        from langchain_core.callbacks import BaseCallbackHandler

        modelos, uso = [], []

        class _Captura(BaseCallbackHandler):
            def on_llm_end(self, response, **kw):
                for gens in response.generations:
                    for g in gens:
                        md = getattr(getattr(g, "message", None), "response_metadata", {}) or {}
                        if md.get("model_name"):
                            modelos.append(md["model_name"])
                        um = getattr(getattr(g, "message", None), "usage_metadata", None)
                        if um:
                            uso.append(dict(um))

        erros = []

        class _Erros(logging.Handler):
            def emit(self, rec):
                if rec.levelno >= logging.WARNING:
                    erros.append(C.sanitizar(rec.getMessage() + (f" | {rec.exc_info[1]!r}" if rec.exc_info else ""),
                                             outer.segredos))

        outer = self
        h = _Erros()
        lg = logging.getLogger("ragas")
        lg.addHandler(h)
        try:
            ds = self._ED(samples=[self._STS(**amostra)])
            r = self._evaluate(dataset=ds, metrics=[self._metricas[metrica]],
                               run_config=self._RunConfig(**RUN_CONFIG), callbacks=[_Captura()])
            score = float(r.to_pandas().iloc[0][metrica])
        finally:
            lg.removeHandler(h)
        total = {}
        for u in uso:
            for k, v in u.items():
                if isinstance(v, (int, float)):
                    total[k] = total.get(k, 0) + v
        return {"score": score, "erros": erros, "modelos_retornados": sorted(set(modelos)),
                "uso_tokens": total or None}


def versoes_dependencias() -> dict:
    from importlib import metadata
    out = {}
    for p in DEPENDENCIAS:
        try:
            out[p] = metadata.version(p)
        except metadata.PackageNotFoundError:
            out[p] = None
    return out


def verificar_ambiente(exigir: bool = False) -> dict:
    """Versões fixadas pela Emenda 3 e revisão local dos embeddings; nenhuma chamada à API."""
    v = versoes_dependencias()
    problemas = [f"{p}=={v.get(p)} (esperado {e})" for p, e in VERSOES_FIXADAS.items() if v.get(p) != e]
    revisoes = None
    try:
        from huggingface_hub import scan_cache_dir
        revisoes = sorted(rv.commit_hash for r in scan_cache_dir().repos if r.repo_id == EMBEDDINGS
                          for rv in r.revisions)
    except Exception as e:  # noqa: BLE001
        problemas.append(f"cache de embeddings ilegível: {type(e).__name__}")
    if revisoes is not None and revisoes != [REVISAO_EMBEDDINGS]:
        problemas.append(f"revisões de embeddings no cache {revisoes} (esperada só {REVISAO_EMBEDDINGS})")
    if exigir and problemas:
        raise Bloqueio("ambiente de avaliação fora da Emenda 3: " + "; ".join(problemas))
    return {"dependencias": v, "revisoes_embeddings": revisoes, "problemas": problemas}


def ler_chave(caminho: str = CHAVE_PADRAO) -> str:
    return C.ler_chave(caminho)


# ── dry-run ───────────────────────────────────────────────────────────────────

def dry_run(*, dataset_path: str = DATASET, coleta: str = COLETA, saida: str = SAIDA_PADRAO,
            verificar_amb: bool = False, git=None, log=print, **kw_coleta) -> dict:
    """
    Sem LLM, sem RAGAS, sem score: valida entradas, hashes, esquema das amostras, estado das
    etapas, seleção e proteção contra sobrescrita. Não escreve em saida/ nem na coleta.
    """
    ds, sha, casos = carregar_entradas(dataset_path, coleta, **kw_coleta)
    log(f"coleta conferida: {len(casos)} casos, SHA256_COLETA.txt e configuração histórica OK")
    trunc = sum(c["truncada_na_geracao"] for c in casos)
    for c in casos:     # esquema das amostras RAGAS (só tipos, tamanhos e hashes)
        if not (isinstance(c["pergunta"], str) and c["pergunta"].strip() and isinstance(c["reference"], str)
                and len(c["contextos"]) == 3 and all(isinstance(t, str) and t.strip() for t in c["contextos"])):
            raise Bloqueio(f"amostra RAGAS inválida: {c['case_id']}")
    rel = {"casos": len(casos), "truncadas_na_geracao": trunc,
           "disponibilidade": {d: sum(c["disponibilidade"] == d for c in casos) for d in ("presente", "parcial", "ausente")},
           "n4_nao_aplicavel": sum(not c["caso_dataset"]["verificacao_deterministica_aplicavel"] for c in casos)}
    # estado das etapas (sem calcular nada)
    p_res = os.path.join(saida, "exatidao", "resultado_exatidao.json")
    rel["exatidao"] = "concluida" if os.path.exists(p_res) else "nao_executada"
    p_dec = os.path.join(saida, "exatidao", "decisoes_sinal.json")
    if os.path.exists(p_dec):
        ler_decisoes_sinal(p_dec, casos)
        rel["decisoes_sinal"] = "arquivo válido"
    rel["comportamento"] = validar_anotacoes(casos, saida)["contagem"] if os.path.exists(arquivo_anotacoes(saida)) \
        else "modelo de anotação ainda não gerado"
    rel["ragas"] = {m: dict(Counter(estado_ragas(saida, m, c)["estado"] for c in casos)) for m in METRICAS}
    try:
        verificar_etapas_anteriores(casos, saida, git or Git())
        rel["ragas_liberado"] = True
    except Bloqueio as e:
        rel["ragas_liberado"] = f"bloqueado: {e}"
    # proteção contra sobrescrita, num diretório temporário
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "x.json")
        C.gravar_exclusivo(p, {"a": 1})
        try:
            C.gravar_exclusivo(p, {"a": 2})
            rel["protecao_sobrescrita"] = "FALHOU"
        except FileExistsError:
            rel["protecao_sobrescrita"] = "ok"
    if verificar_amb:
        amb = verificar_ambiente()
        rel["ambiente"] = {"problemas": amb["problemas"],
                           "fixadas": {p: amb["dependencias"].get(p) for p in VERSOES_FIXADAS},
                           "revisoes_embeddings": amb["revisoes_embeddings"]}
    for k, v in rel.items():
        log(f"  {k}: {v}")
    return rel


# ── CLI ───────────────────────────────────────────────────────────────────────

def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Avaliação das 96 respostas congeladas (RAGAS do TCC 2)")
    sub = p.add_subparsers(dest="etapa", required=True)
    d = sub.add_parser("dry-run")
    d.add_argument("--verificar-ambiente", action="store_true")
    e = sub.add_parser("exatidao")
    e.add_argument("--executar", action="store_true")
    b = sub.add_parser("comportamento")
    g = b.add_mutually_exclusive_group(required=True)
    g.add_argument("--gerar-modelo", action="store_true")
    g.add_argument("--validar", action="store_true")
    r = sub.add_parser("ragas")
    r.add_argument("--metrica", choices=METRICAS, required=True)
    r.add_argument("--executar", action="store_true")
    r.add_argument("--case-id", action="append")
    r.add_argument("--reavaliar-nan", action="store_true")
    r.add_argument("--pausa", type=float, default=PAUSA_PADRAO)
    for s in (d, e, b, r):
        s.add_argument("--saida", default=SAIDA_PADRAO)
    return p


def main(argv=None, *, fabrica_avaliador=None, git=None) -> int:
    a = _parser().parse_args(argv)
    try:
        if a.etapa == "dry-run":
            dry_run(saida=a.saida, verificar_amb=a.verificar_ambiente)
            return 0
        ds, sha, casos = carregar_entradas()
        git = git or Git()
        if a.etapa == "exatidao":
            if not a.executar:
                raise Bloqueio("a exatidão sobre as respostas reais exige --executar")
            exatidao(casos=casos, sha_dataset=sha, saida=a.saida, git=git)
        elif a.etapa == "comportamento":
            if a.gerar_modelo:
                print("modelo de anotação:", gerar_modelo_anotacao(casos, a.saida))
            else:
                v = validar_anotacoes(casos, a.saida)
                print(json.dumps({"contagem": v["contagem"], "completo": v["completo"]}, ensure_ascii=False))
                for cid, s in v["casos"].items():
                    if s["status"] != "VALIDO":
                        print(cid, json.dumps(s, ensure_ascii=False))
        elif a.etapa == "ragas":
            if not a.executar:
                raise Bloqueio("o RAGAS sobre as respostas reais exige --executar")
            avaliador = (fabrica_avaliador or (lambda: AvaliadorRagas(ler_chave())))()
            r = avaliar_ragas(metrica=a.metrica, casos=casos, sha_dataset=sha, avaliador=avaliador, git=git,
                              saida=a.saida, case_ids=a.case_id, reavaliar_nan=a.reavaliar_nan, pausa=a.pausa)
            return 0 if r["encerramento"] == "completa" else 1
        return 0
    except Bloqueio as e:
        print(f"BLOQUEIO: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
