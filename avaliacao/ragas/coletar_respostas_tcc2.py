# avaliacao/ragas/coletar_respostas_tcc2.py
#
# Executor da coleta experimental do RAGAS do TCC 2 (PROTOCOLO_RAGAS_TCC2.md).
#
#   dataset congelado → recuperação congelada → prompt do TCC 1 → Gemini
#   → resposta bruta, um arquivo por caso.
#
# A coleta termina nas respostas brutas. Este módulo NÃO importa o RAGAS, não
# chama exatidao.py nem comportamento.py e não produz estatísticas.
#
# Nome: "coletar_respostas_tcc2" e não "coletar_respostas" porque
# construir_dataset.py importa `extrair_chunks` de avaliacao/coletar_respostas.py
# (TCC 1) pelo nome do módulo; um homônimo nesta pasta poderia ser importado no
# lugar dele.
#
# Modos (um deles é obrigatório; sem argumentos nada é executado):
#   --dry-run    valida dataset, documentos, índices, contexto e requisições
#                dos 96 casos, sem Gemini, sem api_key.txt e sem gravar respostas.
#   --execute    coleta real (lê api_key.txt). Só com o código commitado.
#
# Uso: ver avaliacao/ragas/README_COLETA.md.

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
import zipfile
from collections import Counter
from datetime import datetime, timezone
from unittest import mock

PASTA = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(PASTA))
DATASET = os.path.join(PASTA, "dataset_tcc2.json")
PROTOCOLO = os.path.join(PASTA, "PROTOCOLO_RAGAS_TCC2.md")
SAIDA_PADRAO = os.path.join(PASTA, "coleta_tcc2")
RUNTIME_PADRAO = os.path.join(PASTA, "runtime")
CHAVE_PADRAO = os.path.join(RAIZ, "api_key.txt")
COLETOR_TCC1 = os.path.join(RAIZ, "avaliacao", "coletar_respostas.py")

EXPERIMENTO = "RAGAS TCC 2 — coleta das respostas diretas (96 casos)"
ESQUEMA = 1

# Marco congelado (commit "Congelar dataset e instrumentos da avaliacao RAGAS")
COMMIT_CONGELAMENTO = "a3f424f8bcc25446fc8221dbd1a30bb370b68af8"
SHA256_DATASET_CONGELADO = "313bdf359fdeabb063ceec3bcca12ebfe3b52caae346b3ff1d9f3dc23196bc5e"
SHA256_PROTOCOLO_CONGELADO = "e0b374608a1e4f5b4cae530931e4626f6f67c145d215212ea7ecd55b08da2490"

TIPO_DOC = "ITR"
PERIODO = "2026-06-30"
CATEGORIAS = ("N1", "N2", "N3", "N4", "N5", "E1", "E2", "E3")
DISTRIBUICAO_ESPERADA = {"presente": 69, "parcial": 15, "ausente": 12}

# Geração (protocolo, Seções 5 e 17; iguais a avaliacao/coletar_respostas.py do TCC 1)
MODELO = "gemini-2.5-flash"
TEMPERATURA = 0.1
MAX_OUTPUT_TOKENS = 1024
PROMPT_MODELO = (
    "Você é um analista financeiro. Com base EXCLUSIVAMENTE nos trechos abaixo, "
    "responda à pergunta de forma objetiva e em português.\n\n"
    "Nota: \"Receita de Venda de Bens e/ou Serviços\" equivale à \"Receita Líquida\" "
    "para fins de análise.\n\n"
    "## TRECHOS DO DOCUMENTO\n{contexto}\n\n"
    "## PERGUNTA\n{pergunta}"
)

# Código cujo conteúdo define a coleta (hash no manifesto; mudança bloqueia a retomada)
ARQUIVOS_CODIGO = ("config.py", "modulos/cvm.py", "modulos/extracao.py", "modulos/chunking.py",
                   "modulos/recuperacao.py", "avaliacao/coletar_respostas.py",
                   "avaliacao/ragas/coletar_respostas_tcc2.py")
# Instrumentos congelados da etapa seguinte (só o hash; não são executados aqui)
ARQUIVOS_INSTRUMENTOS = ("avaliacao/ragas/PROTOCOLO_RAGAS_TCC2.md",
                         "avaliacao/ragas/RUBRICA_COMPORTAMENTO_TCC2.md",
                         "avaliacao/ragas/exatidao.py", "avaliacao/ragas/comportamento.py",
                         "avaliacao/ragas/revisao_tecnica_tcc2.json")
DEPENDENCIAS = ("google-genai", "chromadb", "sentence-transformers", "transformers", "torch",
                "huggingface-hub", "tokenizers", "pandas", "numpy", "requests", "pdfplumber")
# Caminhos que precisam estar commitados e limpos para --execute
CAMINHOS_GIT = ("config.py", "modulos", "avaliacao/coletar_respostas.py", "avaliacao/ragas",
                ".gitattributes", "requirements.txt")

STATUS_CONCLUIDO, STATUS_ERRO = "CONCLUIDO", "ERRO"
ESTADO_PENDENTE, ESTADO_CORROMPIDO = "PENDENTE", "CORROMPIDO"


class ChamadaRealProibida(RuntimeError):
    """Tentativa de criar ou usar o cliente real do Gemini fora de --execute."""


class Bloqueio(RuntimeError):
    """Condição que impede a coleta (nenhuma chamada ao modelo é feita)."""


# Liberado apenas por main() com --execute (e sem --dry-run)
_EXECUCAO_REAL_AUTORIZADA = False


# ── utilidades ────────────────────────────────────────────────────────────────

def agora_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_texto(t: str) -> str:
    return sha256_bytes(t.encode("utf-8"))


def sha256_arquivo(caminho: str) -> str:
    with open(caminho, "rb") as f:
        return sha256_bytes(f.read())


def json_canonico(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sanitizar(texto: str, segredos=()) -> str:
    """Remove a chave (e qualquer coisa com cara de chave) de mensagens de erro."""
    t = str(texto)
    for s in segredos:
        if s and len(s) >= 8:
            t = t.replace(s, "***")
    t = re.sub(r"AIza[0-9A-Za-z_\-]{20,}", "***", t)
    t = re.sub(r"(?i)(key|token|authorization)(\s*[=:]\s*)[^\s&,'\"]+", r"\1\2***", t)
    return t[:1000]


def gravar_exclusivo(caminho: str, obj: dict) -> None:
    """Cria o arquivo; falha se ele já existe (nunca sobrescreve)."""
    dados = (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    fd = os.open(caminho, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0))
    try:
        os.write(fd, dados)
        os.fsync(fd)
    finally:
        os.close(fd)


def gravar_substituindo(caminho: str, obj: dict) -> None:
    """Só para o estado operacional (estado_coleta.json): troca atômica."""
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, caminho)


def selar(registro: dict) -> dict:
    """Acrescenta sha256_registro (hash do registro sem esse campo)."""
    r = {k: v for k, v in registro.items() if k != "sha256_registro"}
    r["sha256_registro"] = sha256_texto(json_canonico(r))
    return r


def selo_confere(registro: dict) -> bool:
    r = {k: v for k, v in registro.items() if k != "sha256_registro"}
    return registro.get("sha256_registro") == sha256_texto(json_canonico(r))


# ── separação de trechos do TCC 1 ─────────────────────────────────────────────

_TCC1 = None


def extrair_chunks(ctx_num: str) -> list[str]:
    """extrair_chunks de avaliacao/coletar_respostas.py (TCC 1), carregado pelo caminho."""
    global _TCC1
    if _TCC1 is None:
        sys.path.insert(0, RAIZ)
        spec = importlib.util.spec_from_file_location("_coletor_tcc1", COLETOR_TCC1)
        _TCC1 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_TCC1)
    return _TCC1.extrair_chunks(ctx_num)


# ── dataset ───────────────────────────────────────────────────────────────────

def carregar_dataset(caminho: str = DATASET) -> tuple[dict, str]:
    """Lê (somente leitura) e valida o dataset congelado. Devolve (dataset, sha256)."""
    with open(caminho, "rb") as f:
        bruto = f.read()
    ds = json.loads(bruto.decode("utf-8"))
    casos = ds["casos"]
    erros = []
    if len(casos) != 96:
        erros.append(f"{len(casos)} casos (esperado 96)")
    ids = [c["id"] for c in casos]
    if len(set(ids)) != len(ids):
        erros.append("IDs repetidos")
    por_emp = {}
    for c in casos:
        por_emp.setdefault(c["ticker"], []).append(c["categoria"])
        if c["id"] != f"{c['ticker']}_{c['categoria']}":
            erros.append(f"ID fora do padrão: {c['id']}")
    if len(por_emp) != 12 or set(por_emp) != set(ds["empresas"]):
        erros.append(f"{len(por_emp)} empresas (esperado 12)")
    for tk, cats in por_emp.items():
        if sorted(cats) != sorted(CATEGORIAS):
            erros.append(f"{tk}: categorias {sorted(cats)}")
    dist = dict(Counter(c["disponibilidade"] for c in casos))
    if dist != DISTRIBUICAO_ESPERADA:
        erros.append(f"disponibilidade {dist} (esperado {DISTRIBUICAO_ESPERADA})")
    sys.path.insert(0, PASTA)
    from validar_dataset import verificar, chaves, CHAVES_PROIBIDAS
    falhas = {k: v for k, v in verificar(ds).items() if v}
    if falhas:
        erros.append(f"validar_dataset: {falhas}")
    proibidas = [k for k, _ in chaves(ds) if k.lower() in CHAVES_PROIBIDAS]
    if proibidas:
        erros.append(f"dataset contém chaves de resultado: {proibidas}")
    if erros:
        raise Bloqueio("Dataset inválido: " + "; ".join(erros))
    return ds, sha256_bytes(bruto)


def verificar_protocolo(ds: dict) -> None:
    """O protocolo em disco é o congelado e é o mesmo registrado no dataset."""
    sha = sha256_arquivo(PROTOCOLO)
    if sha != SHA256_PROTOCOLO_CONGELADO or sha != ds["metadados"]["sha256_protocolo"]:
        raise Bloqueio(f"Protocolo {sha} difere do congelado {SHA256_PROTOCOLO_CONGELADO} "
                       "ou do registrado no dataset")


def empresa_do_caso(ds: dict, caso: dict) -> dict:
    e = ds["empresas"][caso["ticker"]]
    return {"ticker": caso["ticker"], "codigo_cvm": e["codigo_cvm"], "versao": e["versao"],
            "sha256_documento": e["sha256_documento"],
            "sha256_ctx_num": e["contexto_recuperado"]["sha256_ctx_num"],
            "sha256_trechos": e["contexto_recuperado"]["sha256_trechos"]}


def ordem_execucao(ds: dict) -> list[str]:
    """Ordem congelada: a ordem dos casos no dataset (sem randomização)."""
    return [c["id"] for c in ds["casos"]]


# ── requisição ao modelo ──────────────────────────────────────────────────────

def montar_prompt(ctx_num: str, pergunta: str) -> str:
    return PROMPT_MODELO.format(contexto=ctx_num, pergunta=pergunta)


def montar_requisicao(caso: dict, ctx_num: str) -> dict:
    """Única construção do payload: modelo, prompt (contexto + pergunta) e parâmetros."""
    return {"model": MODELO,
            "contents": montar_prompt(ctx_num, caso["pergunta"]),
            "config": {"temperature": TEMPERATURA, "max_output_tokens": MAX_OUTPUT_TOKENS}}


def verificar_requisicao(req: dict, caso: dict, ctx_num: str) -> None:
    """Barreira antes de qualquer chamada: o payload tem só o que o protocolo permite."""
    if set(req) != {"model", "contents", "config"} or req["model"] != MODELO or \
            req["config"] != {"temperature": TEMPERATURA, "max_output_tokens": MAX_OUTPUT_TOKENS}:
        raise Bloqueio(f"{caso['id']}: requisição fora da configuração congelada")
    if req["contents"] != montar_prompt(ctx_num, caso["pergunta"]):
        raise Bloqueio(f"{caso['id']}: prompt diferente do modelo do TCC 1")
    fora_do_contexto = req["contents"].replace(ctx_num, "", 1)
    vazamentos = [caso.get("gabarito"), caso.get("justificativa_disponibilidade"),
                  (caso.get("revisao_tecnica") or {}).get("atencao_humana"),
                  (caso.get("revisao_tecnica") or {}).get("observacao")]
    vazamentos += [v.get("apresentacao_referencia") for v in caso.get("valores_esperados", [])]
    for v in vazamentos:
        if v and v in fora_do_contexto:
            raise Bloqueio(f"{caso['id']}: informação do gabarito/revisão no prompt")
    esqueleto = fora_do_contexto.replace(caso["pergunta"], "", 1).lower()
    if "disponibilidade" in esqueleto or caso["disponibilidade"] in esqueleto:
        raise Bloqueio(f"{caso['id']}: disponibilidade no prompt")


# ── gerador ───────────────────────────────────────────────────────────────────

def gerador_proibido(req: dict) -> dict:
    raise ChamadaRealProibida("Chamada ao Gemini fora de --execute (dry-run ou modo não autorizado).")


def ler_chave(caminho: str) -> str:
    with open(caminho, encoding="utf-8") as f:
        chave = f.read().strip()
    if not chave:
        raise Bloqueio("api_key.txt vazio")
    return chave


class GeradorGemini:
    """Cliente real (google-genai). Criado só com --execute; a chave não sai daqui."""

    def __init__(self, caminho_chave: str = CHAVE_PADRAO):
        if not _EXECUCAO_REAL_AUTORIZADA:
            raise ChamadaRealProibida("Cliente real do Gemini só pode ser criado com --execute.")
        from google import genai
        from google.genai import types
        self._types = types
        chave = ler_chave(caminho_chave)
        self.segredos = (chave,)
        self._cliente = genai.Client(api_key=chave)

    def __repr__(self):
        return "GeradorGemini(***)"

    def __call__(self, req: dict) -> dict:
        if not _EXECUCAO_REAL_AUTORIZADA:
            raise ChamadaRealProibida("Chamada ao Gemini fora de --execute.")
        resp = self._cliente.models.generate_content(
            model=req["model"], contents=req["contents"],
            config=self._types.GenerateContentConfig(**req["config"]))
        cand = (getattr(resp, "candidates", None) or [None])[0]
        fr = getattr(cand, "finish_reason", None) if cand is not None else None
        uso = getattr(resp, "usage_metadata", None)
        campos = ("prompt_token_count", "candidates_token_count", "thoughts_token_count", "total_token_count")
        return {"texto": resp.text,
                "modelo_retornado": getattr(resp, "model_version", None),
                "finish_reason": getattr(fr, "name", None) or (str(fr) if fr is not None else None),
                "uso_tokens": {c: getattr(uso, c, None) for c in campos} if uso is not None else None}


# ── recuperação congelada ─────────────────────────────────────────────────────

class RecuperadorCongelado:
    """
    Documento (cvm.baixar_documento, ZIP da CVM servido localmente) → criar_chunks
    → indexar_documento num ChromaDB próprio (`pasta_runtime/indices/chroma`,
    coleção recriada do zero) → recuperar_contexto. Nada é alterado em
    modulos/; o chroma_db/ do sistema não é aberto.
    """

    def __init__(self, zip_bytes: bytes, pasta_runtime: str):
        os.environ["HF_HUB_OFFLINE"] = "1"        # embeddings do cache local, sem rede
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        self.zip = zip_bytes
        self.chroma = os.path.join(pasta_runtime, "indices", "chroma")
        self.docs = os.path.join(pasta_runtime, "documentos")
        os.makedirs(self.chroma, exist_ok=True)
        os.makedirs(self.docs, exist_ok=True)
        sys.path.insert(0, RAIZ)

    @contextlib.contextmanager
    def _indice_experimental(self):
        from modulos import chunking, recuperacao
        with mock.patch.object(chunking, "CAMINHO_CHROMA", self.chroma), \
                mock.patch.object(recuperacao, "CAMINHO_CHROMA", self.chroma):
            yield chunking, recuperacao

    def verificar_versoes(self, empresas: list[dict]) -> list[str]:
        """Regra de versão (Seção 4): a versão registrada é a mais recente no índice do ZIP."""
        import pandas as pd
        with zipfile.ZipFile(io.BytesIO(self.zip)) as z:
            idx = pd.read_csv(z.open("itr_cia_aberta_2026.csv"), sep=";", encoding="latin-1", dtype=str)
        idx = idx[(idx.DT_REFER == PERIODO) & (idx.CATEG_DOC == TIPO_DOC)]
        problemas = []
        for e in empresas:
            v = idx[idx.CD_CVM.str.lstrip("0") == str(e["codigo_cvm"])].VERSAO.astype(int)
            if v.empty or int(v.max()) != int(e["versao"]):
                problemas.append(f"{e['ticker']}: versão mais recente {None if v.empty else int(v.max())}, "
                                 f"registrada {e['versao']}")
        return problemas

    def preparar(self, emp: dict) -> str:
        from modulos import cvm
        from modulos.extracao import extrair_documento
        url = cvm._url_dados_zip(TIPO_DOC, int(PERIODO[:4]))
        zip_bytes = self.zip

        class _Resp:
            content = zip_bytes
            status_code = 200
            def raise_for_status(self): pass

        def _get(u, timeout=None):
            if u != url:
                raise Bloqueio(f"URL inesperada: {u}")
            return _Resp()

        destino = os.path.join(self.docs, f"{emp['ticker']}_{TIPO_DOC}_{PERIODO}.txt")
        if os.path.exists(destino):
            os.remove(destino)                     # documento de runtime: sempre regerado
        with mock.patch.object(cvm.requests, "get", _get):
            cvm.baixar_documento("", destino, codigo_cvm=str(emp["codigo_cvm"]), tipo=TIPO_DOC,
                                 periodo=PERIODO, versao=str(emp["versao"]))
        sha = sha256_arquivo(destino)
        if sha != emp["sha256_documento"]:
            raise Bloqueio(f"{emp['ticker']}: SHA-256 do documento {sha} difere do registrado "
                           f"{emp['sha256_documento']} (protocolo, Seção 4)")
        with self._indice_experimental() as (chunking, _):
            chunks = chunking.criar_chunks(extrair_documento(destino))
            chunking.indexar_documento(emp["ticker"], chunks, TIPO_DOC, PERIODO, forcar=True)
        return sha

    def recuperar(self, emp: dict) -> dict:
        import chromadb
        with self._indice_experimental() as (chunking, recuperacao):
            ctx_num, _ = recuperacao.recuperar_contexto(emp["ticker"], TIPO_DOC, PERIODO)
            col = chromadb.PersistentClient(path=self.chroma).get_collection(
                chunking.nome_collection(emp["ticker"], TIPO_DOC, PERIODO))
            docs = col.get(include=["documents"])
        por_texto = {d.replace("-" * 40, "").strip(): i for d, i in zip(docs["documents"], docs["ids"])}
        return {"ctx_num": ctx_num, "ids": [por_texto.get(t) for t in extrair_chunks(ctx_num)]}


def parametros_recuperacao() -> dict:
    sys.path.insert(0, RAIZ)
    import config
    with open(os.path.join(RAIZ, "modulos", "recuperacao.py"), encoding="utf-8") as f:
        fonte = f.read()
    query = re.search(r'^QUERY_NUMERICO = "(.*)"$', fonte, re.M).group(1)
    return {"funcao": "modulos.recuperacao.recuperar_contexto", "tipo_doc": TIPO_DOC, "periodo": PERIODO,
            "query_numerico": query, "top_k": config.MAX_CHUNKS_NUMERICO,
            "embeddings": config.MODELO_EMBEDDINGS, "embeddings_revisao_local": revisao_embeddings(config.MODELO_EMBEDDINGS),
            "chunking": {"funcao": "modulos.chunking.criar_chunks", "tabela": "uma tabela inteira por chunk",
                         "max_palavras_narrativo": config.MAX_PALAVRAS_CHUNK, "overlap": config.OVERLAP_PALAVRAS},
            "indice": "ChromaDB próprio (avaliacao/ragas/runtime/indices), coleção recriada do zero a cada execução",
            "separacao_trechos": "avaliacao/coletar_respostas.extrair_chunks (TCC 1)"}


def revisao_embeddings(nome: str):
    try:
        from huggingface_hub import constants
        ref = os.path.join(constants.HF_HUB_CACHE, f"models--sentence-transformers--{nome}", "refs", "main")
        with open(ref, encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return None


# ── configuração e manifesto ──────────────────────────────────────────────────

def versoes_dependencias() -> dict:
    import importlib.metadata as md
    v = {}
    for p in DEPENDENCIAS:
        try:
            v[p] = md.version(p)
        except md.PackageNotFoundError:
            v[p] = None
    return v


def configuracao(ds: dict, sha_dataset: str, recuperacao: dict | None = None,
                 dependencias: dict | None = None) -> dict:
    """Tudo o que define a coleta. O hash disto (sha256_configuracao) trava a retomada."""
    casos = ds["casos"]
    return {
        "experimento": EXPERIMENTO, "esquema": ESQUEMA,
        "dataset": {"arquivo": "avaliacao/ragas/dataset_tcc2.json", "sha256": sha_dataset},
        "sha256_protocolo_no_dataset": ds["metadados"]["sha256_protocolo"],
        "n_casos": len(casos),
        "empresas": sorted(ds["empresas"]),
        "categorias": list(CATEGORIAS),
        "distribuicao_disponibilidade": dict(sorted(Counter(c["disponibilidade"] for c in casos).items())),
        "ordem_casos": ordem_execucao(ds),
        "ordem_criterio": "ordem congelada dos casos no dataset (sem randomização)",
        "documentos": {tk: {"codigo_cvm": e["codigo_cvm"], "versao": e["versao"],
                            "sha256_documento": e["sha256_documento"],
                            "sha256_ctx_num": e["contexto_recuperado"]["sha256_ctx_num"]}
                       for tk, e in sorted(ds["empresas"].items())},
        "geracao": {"provedor": "Google Gemini API (google-genai)", "modelo": MODELO,
                    "temperatura": TEMPERATURA, "max_output_tokens": MAX_OUTPUT_TOKENS,
                    "prompt_modelo": PROMPT_MODELO, "sha256_prompt_modelo": sha256_texto(PROMPT_MODELO),
                    "retentativas_automaticas": 0,
                    "politica_erro": "falha grava ERRO e interrompe a execução; nova tentativa só com --retentar-erros"},
        "recuperacao": recuperacao if recuperacao is not None else parametros_recuperacao(),
        "codigo": {p: sha256_arquivo(os.path.join(RAIZ, p)) for p in ARQUIVOS_CODIGO},
        "instrumentos_congelados": {p: sha256_arquivo(os.path.join(RAIZ, p)) for p in ARQUIVOS_INSTRUMENTOS},
        "ambiente": {"python": platform.python_version(),
                     "dependencias": dependencias if dependencias is not None else versoes_dependencias()},
    }


def sha_config(cfg: dict) -> str:
    return sha256_texto(json_canonico(cfg))


class Git:
    def __init__(self, raiz: str = RAIZ):
        self.raiz = raiz

    def _run(self, *args) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], cwd=self.raiz, capture_output=True, text=True)

    def head(self) -> str:
        return self._run("rev-parse", "HEAD").stdout.strip()

    def pendencias(self) -> list[str]:
        """Alterações não commitadas em código/instrumentos (fora da saída e do runtime)."""
        r = self._run("status", "--porcelain", "--untracked-files=all", "--", *CAMINHOS_GIT,
                      ":(exclude)avaliacao/ragas/coleta_tcc2", ":(exclude)avaliacao/ragas/runtime")
        return [l for l in r.stdout.splitlines() if l.strip()]

    def descende_de(self, commit: str) -> bool:
        return self._run("merge-base", "--is-ancestor", commit, "HEAD").returncode == 0

    def alterados_desde(self, commit: str) -> list[str]:
        return [l for l in self._run("diff", "--name-only", commit, "HEAD").stdout.splitlines() if l]


def verificar_git(git) -> str:
    head = git.head()
    if not git.descende_de(COMMIT_CONGELAMENTO):
        raise Bloqueio(f"HEAD {head} não descende do marco congelado {COMMIT_CONGELAMENTO}")
    pend = git.pendencias()
    if pend:
        raise Bloqueio("Código/instrumentos com alterações não commitadas: " + "; ".join(pend))
    return head


def novo_manifesto(cfg: dict, head: str, criado_em: str, fonte_cvm: dict | None = None) -> dict:
    return {"manifesto": "configuração congelada da coleta (não é alterado depois de criado)",
            "commit_inicio": head, "commit_congelamento_dataset": COMMIT_CONGELAMENTO,
            "criado_em_utc": criado_em, "sha256_configuracao": sha_config(cfg),
            "fonte_cvm_inicio": fonte_cvm,
            "chave_api": "lida em tempo de execução de api_key.txt; nunca registrada",
            "configuracao": cfg}


def validar_retomada(manifesto: dict, cfg: dict, git, saida_rel: str) -> None:
    dif = []
    antigo = manifesto["configuracao"]
    if manifesto.get("sha256_configuracao") != sha_config(antigo):
        dif.append("manifesto adulterado (hash da configuração não confere)")
    if antigo["dataset"]["sha256"] != cfg["dataset"]["sha256"]:
        dif.append("SHA-256 do dataset mudou")
    for k in sorted(set(antigo) | set(cfg)):
        if antigo.get(k) != cfg.get(k) and k != "dataset":
            dif.append(f"configuração mudou: {k}")
    if git is not None:
        fora = [p for p in git.alterados_desde(manifesto["commit_inicio"])
                if not p.startswith(saida_rel.rstrip("/") + "/")]
        if fora:
            dif.append("commits posteriores ao início alteram: " + ", ".join(fora))
    if dif:
        raise Bloqueio("Retomada bloqueada: " + "; ".join(dif))


# ── estado dos casos ──────────────────────────────────────────────────────────

def caminho_resposta(saida: str, case_id: str) -> str:
    return os.path.join(saida, "respostas", f"{case_id}.json")


def arquivos_erro(saida: str, case_id: str) -> list[str]:
    pasta = os.path.join(saida, "respostas")
    if not os.path.isdir(pasta):
        return []
    return sorted(os.path.join(pasta, n) for n in os.listdir(pasta)
                  if re.fullmatch(re.escape(case_id) + r"\.erro_\d{2}\.json", n))


def estado_caso(saida: str, case_id: str, sha_cfg: str) -> str:
    """CONCLUIDO só com registro íntegro; arquivo ilegível/incompleto é CORROMPIDO."""
    p = caminho_resposta(saida, case_id)
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                r = json.load(f)
            ok = (selo_confere(r) and r.get("case_id") == case_id and r.get("status") == STATUS_CONCLUIDO
                  and r.get("sha256_configuracao") == sha_cfg and isinstance(r.get("resposta"), str)
                  and r["resposta"].strip())
        except (OSError, ValueError, AttributeError):
            ok = False
        return STATUS_CONCLUIDO if ok else ESTADO_CORROMPIDO
    return STATUS_ERRO if arquivos_erro(saida, case_id) else ESTADO_PENDENTE


def resumo_estados(saida: str, ids: list[str], sha_cfg: str) -> dict:
    return dict(Counter(estado_caso(saida, i, sha_cfg) for i in ids))


@contextlib.contextmanager
def trava(saida: str):
    p = os.path.join(saida, ".trava")
    try:
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    except FileExistsError:
        raise Bloqueio(f"Outra execução em andamento (ou encerrada sem liberar): remova {p} após conferir.")
    os.write(fd, agora_utc().encode())
    os.close(fd)
    try:
        yield
    finally:
        os.remove(p)


# ── registros ─────────────────────────────────────────────────────────────────

def _identificacao(caso: dict, emp: dict) -> dict:
    return {"esquema": ESQUEMA, "case_id": caso["id"], "ticker": caso["ticker"],
            "codigo_cvm": caso["codigo_cvm"], "empresa": caso["empresa"], "estrutura": caso["estrutura"],
            "categoria": caso["categoria"], "tipo_pergunta": caso["tipo_pergunta"], "pergunta": caso["pergunta"],
            "disponibilidade_congelada": caso["disponibilidade"],
            "documento": {"tipo": TIPO_DOC, "periodo": PERIODO, "versao": emp["versao"],
                          "sha256_documento": emp["sha256_documento"]}}


def _contexto(ctx_num: str, ids: list) -> dict:
    trechos = extrair_chunks(ctx_num)
    return {"sha256_ctx_num": sha256_texto(ctx_num), "ctx_num": ctx_num,
            "trechos": [{"ordem": i + 1, "titulo": t.split("\n", 1)[0], "chroma_id": ids[i] if i < len(ids) else None,
                         "sha256": sha256_texto(t), "texto": t} for i, t in enumerate(trechos)]}


# ── coleta ────────────────────────────────────────────────────────────────────

def conferir_contexto(emp: dict, rec: dict) -> None:
    """Seção 9, regra 8: contexto diferente do congelado impede qualquer resposta."""
    trechos = extrair_chunks(rec["ctx_num"])
    if sha256_texto(rec["ctx_num"]) != emp["sha256_ctx_num"] or \
            [sha256_texto(t) for t in trechos] != emp["sha256_trechos"]:
        raise Bloqueio(f"{emp['ticker']}: contexto recuperado difere do congelado no dataset "
                       "(protocolo, Seção 9, regra 8: reclassificar antes de qualquer resposta)")


def selecionar(ds, saida, sha_cfg, case_ids=None, limit=None, retentar_erros=False,
               reexecutar_concluido=False) -> tuple[list[dict], dict]:
    ordem = ordem_execucao(ds)
    por_id = {c["id"]: c for c in ds["casos"]}
    if case_ids:
        desconhecidos = [i for i in case_ids if i not in por_id]
        if desconhecidos:
            raise Bloqueio(f"case_id inexistente: {desconhecidos}")
        ordem = [i for i in ordem if i in set(case_ids)]
    if reexecutar_concluido and not case_ids:
        raise Bloqueio("--reexecutar-concluido exige --case-id")
    escolhidos, pulados = [], {}
    for i in ordem:
        st = estado_caso(saida, i, sha_cfg)
        if st == ESTADO_PENDENTE or (st == STATUS_ERRO and retentar_erros) or \
                (st == STATUS_CONCLUIDO and reexecutar_concluido) or (st == ESTADO_CORROMPIDO and retentar_erros):
            escolhidos.append(por_id[i])
        else:
            pulados[i] = st
    if limit is not None:
        escolhidos = escolhidos[:limit]
    return escolhidos, pulados


def coletar(*, recuperador, gerador, git, dataset_path: str = DATASET, saida: str = SAIDA_PADRAO,
            sha_dataset_esperado: str | None = SHA256_DATASET_CONGELADO, case_ids=None, limit=None,
            retentar_erros=False, reexecutar_concluido=False, motivo=None, segredos=(), pausa=0.0,
            fonte_cvm=None, cfg_extra=None, log=None) -> dict:
    """Coleta real (ou com gerador falso, nos testes). Devolve o resumo da execução."""
    log = log or print
    ds, sha_ds = carregar_dataset(dataset_path)
    if sha_dataset_esperado and sha_ds != sha_dataset_esperado:
        raise Bloqueio(f"SHA-256 do dataset {sha_ds} difere do congelado {sha_dataset_esperado}")
    verificar_protocolo(ds)
    if reexecutar_concluido and not (motivo and motivo.strip()):
        raise Bloqueio("--reexecutar-concluido exige --motivo (e emenda ao protocolo, Seção 15.8)")
    cfg = configuracao(ds, sha_ds, **(cfg_extra or {}))
    scfg = sha_config(cfg)
    head = verificar_git(git)
    saida_rel = os.path.relpath(saida, RAIZ).replace(os.sep, "/")
    os.makedirs(os.path.join(saida, "respostas"), exist_ok=True)
    p_manifesto = os.path.join(saida, "manifesto_config.json")
    p_estado = os.path.join(saida, "estado_coleta.json")

    with trava(saida):
        manifesto = None
        if os.path.exists(p_manifesto):
            with open(p_manifesto, encoding="utf-8") as f:
                manifesto = json.load(f)
            validar_retomada(manifesto, cfg, git, saida_rel)
        selecao, pulados = selecionar(ds, saida, scfg, case_ids, limit, retentar_erros, reexecutar_concluido)
        corrompidos = [i for i, s in pulados.items() if s == ESTADO_CORROMPIDO]
        if corrompidos:
            log(f"AVISO: registros corrompidos (não contam como concluídos): {corrompidos}; "
                "use --retentar-erros para preservá-los em respostas/_invalidos e refazer")
        if not selecao:
            log("Nada a coletar: todos os casos selecionados já estão concluídos ou aguardam decisão.")
            return {"executados": [], "pulados": pulados, "encerramento": "nada_a_fazer",
                    "estados": resumo_estados(saida, ordem_execucao(ds), scfg)}

        # Pré-voo (antes de qualquer chamada): documentos, índices recriados e contexto congelado
        empresas = {}
        for c in selecao:
            if c["ticker"] not in empresas:
                empresas[c["ticker"]] = empresa_do_caso(ds, c)
        problemas = recuperador.verificar_versoes(list(empresas.values()))
        if problemas:
            raise Bloqueio("Regra de versão (Seção 4): " + "; ".join(problemas))
        for tk, emp in empresas.items():
            recuperador.preparar(emp)
            conferir_contexto(emp, recuperador.recuperar(emp))
            log(f"pré-voo {tk}: documento, índice e contexto conferem")

        if manifesto is None:
            manifesto = novo_manifesto(cfg, head, agora_utc(), fonte_cvm)
            gravar_exclusivo(p_manifesto, manifesto)
        estado = {"experimento": EXPERIMENTO, "sha256_configuracao": scfg, "execucoes": []}
        if os.path.exists(p_estado):
            with open(p_estado, encoding="utf-8") as f:
                estado = json.load(f)
        execucao = {"n": len(estado["execucoes"]) + 1, "inicio_utc": agora_utc(), "commit": head,
                    "fonte_cvm": fonte_cvm,
                    "argumentos": {"case_ids": case_ids, "limit": limit, "retentar_erros": retentar_erros,
                                   "reexecutar_concluido": reexecutar_concluido, "motivo": motivo, "pausa_s": pausa},
                    "casos": [], "encerramento": None}
        estado["execucoes"].append(execucao)

        def salvar_estado(enc=None):
            execucao["encerramento"] = enc
            execucao["fim_utc"] = agora_utc() if enc else None
            if enc or "resumo" not in estado:                 # resumo completo só no encerramento
                estado["resumo"] = resumo_estados(saida, ordem_execucao(ds), scfg)
            gravar_substituindo(p_estado, estado)

        salvar_estado()
        encerramento = "completa"
        try:
            for n, caso in enumerate(selecao, 1):
                emp = empresas[caso["ticker"]]
                st_antes = estado_caso(saida, caso["id"], scfg)
                if st_antes == ESTADO_CORROMPIDO:
                    inval = os.path.join(saida, "respostas", "_invalidos")
                    os.makedirs(inval, exist_ok=True)
                    os.rename(caminho_resposta(saida, caso["id"]),
                              os.path.join(inval, f"{caso['id']}.{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"))
                tentativa = len(arquivos_erro(saida, caso["id"])) + 1
                base = _identificacao(caso, emp)
                base.update({"tentativa": tentativa, "commit": head, "sha256_dataset": sha_ds,
                             "sha256_configuracao": scfg,
                             "recuperacao": {k: cfg["recuperacao"][k] for k in
                                             ("funcao", "query_numerico", "top_k", "embeddings", "indice")}})
                inicio, t0 = agora_utc(), time.monotonic()

                rec = recuperador.recuperar(emp)                 # fluxo do TCC 1: recupera por pergunta
                conferir_contexto(emp, rec)
                req = montar_requisicao(caso, rec["ctx_num"])
                verificar_requisicao(req, caso, rec["ctx_num"])
                base["contexto"] = _contexto(rec["ctx_num"], rec.get("ids") or [])
                base["requisicao"] = {"modelo": req["model"], "temperatura": req["config"]["temperature"],
                                      "max_output_tokens": req["config"]["max_output_tokens"],
                                      "sha256_prompt": sha256_texto(req["contents"]), "prompt": req["contents"]}
                erro, saida_ger = None, None
                try:
                    saida_ger = gerador(req)
                    texto = saida_ger.get("texto")
                    if not isinstance(texto, str) or not texto.strip():
                        erro = {"etapa": "geracao", "tipo": "RESPOSTA_SEM_TEXTO",
                                "mensagem": f"API sem texto (finish_reason={saida_ger.get('finish_reason')})"}
                except ChamadaRealProibida:
                    raise
                except Exception as e:  # falha técnica: não é resposta
                    erro = {"etapa": "geracao", "tipo": type(e).__name__, "mensagem": sanitizar(e, segredos)}
                base.update({"inicio_utc": inicio, "fim_utc": agora_utc(),
                             "duracao_s": round(time.monotonic() - t0, 3)})
                if saida_ger:
                    base["geracao"] = {"modelo_retornado": saida_ger.get("modelo_retornado"),
                                       "finish_reason": saida_ger.get("finish_reason"),
                                       "truncada_por_limite": saida_ger.get("finish_reason") == "MAX_TOKENS",
                                       "uso_tokens": saida_ger.get("uso_tokens")}
                if erro:
                    base.update({"status": STATUS_ERRO, "erro": erro})
                    gravar_exclusivo(os.path.join(saida, "respostas", f"{caso['id']}.erro_{tentativa:02d}.json"),
                                     selar(base))
                    execucao["casos"].append({"case_id": caso["id"], "status": STATUS_ERRO, "tipo": erro["tipo"]})
                    log(f"[{n}/{len(selecao)}] {caso['id']}: ERRO ({erro['tipo']}) — execução interrompida")
                    encerramento = "erro"
                    break
                base.update({"status": STATUS_CONCLUIDO, "erro": None,
                             "resposta": saida_ger["texto"].strip(), "resposta_bruta": saida_ger["texto"]})
                if st_antes == STATUS_CONCLUIDO:          # reexecução explícita: versão separada
                    k = 1
                    while os.path.exists(os.path.join(saida, "respostas", f"{caso['id']}.reexecucao_{k:02d}.json")):
                        k += 1
                    base.update({"status": "REEXECUCAO", "motivo_reexecucao": motivo})
                    destino = os.path.join(saida, "respostas", f"{caso['id']}.reexecucao_{k:02d}.json")
                else:
                    destino = caminho_resposta(saida, caso["id"])
                gravar_exclusivo(destino, selar(base))
                execucao["casos"].append({"case_id": caso["id"], "status": base["status"]})
                salvar_estado()
                log(f"[{n}/{len(selecao)}] {caso['id']}: {base['status']} "
                    f"(finish_reason={base.get('geracao', {}).get('finish_reason')})")
                if pausa and n < len(selecao):
                    time.sleep(pausa)
        except KeyboardInterrupt:
            encerramento = "interrompida"
            raise
        except Bloqueio:
            encerramento = "bloqueio"
            raise
        except ChamadaRealProibida:
            encerramento = "proibida"
            raise
        except Exception:
            encerramento = "falha_interna"
            raise
        finally:
            salvar_estado(encerramento)
    return {"executados": execucao["casos"], "pulados": pulados, "encerramento": encerramento,
            "estados": estado["resumo"], "sha256_configuracao": scfg}


# ── dry-run ───────────────────────────────────────────────────────────────────

def dry_run(*, recuperador, git=None, dataset_path: str = DATASET,
            sha_dataset_esperado: str | None = SHA256_DATASET_CONGELADO, cfg_extra=None, log=None) -> dict:
    """Valida tudo o que a coleta real usaria, sem gerador e sem gravar respostas."""
    log = log or print
    ds, sha_ds = carregar_dataset(dataset_path)
    avisos = []
    if sha_dataset_esperado and sha_ds != sha_dataset_esperado:
        raise Bloqueio(f"SHA-256 do dataset {sha_ds} difere do congelado {sha_dataset_esperado}")
    verificar_protocolo(ds)
    cfg = configuracao(ds, sha_ds, **(cfg_extra or {}))
    ordem = ordem_execucao(ds)
    por_id = {c["id"]: c for c in ds["casos"]}
    empresas = {}
    for i in ordem:
        tk = por_id[i]["ticker"]
        if tk not in empresas:
            empresas[tk] = empresa_do_caso(ds, por_id[i])
    problemas = recuperador.verificar_versoes(list(empresas.values()))
    if problemas:
        raise Bloqueio("Regra de versão (Seção 4): " + "; ".join(problemas))
    contextos = {}
    for tk, emp in empresas.items():
        recuperador.preparar(emp)
        rec = recuperador.recuperar(emp)
        conferir_contexto(emp, rec)
        conferir_contexto(emp, recuperador.recuperar(emp))    # a coleta recupera de novo a cada caso
        if not rec.get("ids") or None in rec["ids"]:
            avisos.append(f"{tk}: id de trecho não localizado no índice")
        contextos[tk] = rec
        log(f"dry-run {tk}: documento v{emp['versao']} e contexto ({len(rec['ctx_num'])} caracteres) conferem")
    prontos = []
    for i in ordem:
        caso = por_id[i]
        req = montar_requisicao(caso, contextos[caso["ticker"]]["ctx_num"])
        verificar_requisicao(req, caso, contextos[caso["ticker"]]["ctx_num"])
        prontos.append(i)
    situacao_git = None
    if git is not None:
        try:
            situacao_git = {"head": verificar_git(git), "apto_para_execute": True}
        except Bloqueio as b:
            situacao_git = {"head": git.head(), "apto_para_execute": False, "motivo": str(b)}
    log(f"DRY-RUN OK: {len(prontos)} casos prontos (nenhuma chamada ao Gemini, nenhuma resposta gravada).")
    return {"prontos": prontos, "sha256_dataset": sha_ds, "sha256_configuracao": sha_config(cfg),
            "configuracao": cfg, "avisos": avisos, "git": situacao_git}


# ── linha de comando ──────────────────────────────────────────────────────────

def _obter_zip(args, pasta_runtime: str) -> tuple[bytes, dict]:
    if args.zip:
        with open(args.zip, "rb") as f:
            b = f.read()
        return b, {"origem": "arquivo local", "arquivo": os.path.basename(args.zip), "sha256": sha256_bytes(b),
                   "lido_em_utc": agora_utc()}
    if args.baixar_zip:
        import requests
        sys.path.insert(0, RAIZ)
        from modulos import cvm
        url = cvm._url_dados_zip(TIPO_DOC, int(PERIODO[:4]))
        r = requests.get(url, timeout=300)
        r.raise_for_status()
        destino = os.path.join(pasta_runtime, "cvm", f"itr_cia_aberta_2026_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.zip")
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, "wb") as f:
            f.write(r.content)
        return r.content, {"origem": url, "arquivo": os.path.basename(destino), "sha256": sha256_bytes(r.content),
                           "baixado_em_utc": agora_utc()}
    raise Bloqueio("Informe --zip CAMINHO ou --baixar-zip (ZIP de dados abertos do ITR 2026 da CVM)")


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Executor da coleta do RAGAS do TCC 2 (ver README_COLETA.md).")
    m = p.add_mutually_exclusive_group()
    m.add_argument("--dry-run", action="store_true", help="valida tudo sem Gemini e sem gravar respostas")
    m.add_argument("--execute", action="store_true", help="coleta REAL (chama o Gemini)")
    p.add_argument("--zip", help="ZIP itr_cia_aberta_2026.zip local")
    p.add_argument("--baixar-zip", action="store_true", help="baixa o ZIP atual da CVM")
    p.add_argument("--case-id", action="append", help="restringe a um caso (pode repetir)")
    p.add_argument("--limit", type=int, help="no máximo N casos nesta execução (controle operacional)")
    p.add_argument("--retentar-erros", action="store_true", help="refaz casos com ERRO ou registro corrompido")
    p.add_argument("--reexecutar-concluido", action="store_true",
                   help="gera versão separada de caso concluído (exige --case-id, --motivo e emenda)")
    p.add_argument("--motivo", help="justificativa da reexecução")
    p.add_argument("--pausa", type=float, default=0.0, help="segundos entre casos")
    p.add_argument("--saida", default=SAIDA_PADRAO)
    p.add_argument("--runtime", default=RUNTIME_PADRAO)
    p.add_argument("--chave", default=CHAVE_PADRAO)
    return p


def main(argv=None, *, fabrica_recuperador=None, fabrica_gerador=None, git=None,
         dataset_path: str = DATASET, sha_dataset_esperado: str = SHA256_DATASET_CONGELADO) -> int:
    global _EXECUCAO_REAL_AUTORIZADA
    args = _parser().parse_args(argv)
    fabrica_recuperador = fabrica_recuperador or RecuperadorCongelado
    if not args.dry_run and not args.execute:
        print("Nada foi executado. Use --dry-run (validação, sem Gemini) ou --execute (coleta real).")
        return 2
    git = git or Git()
    try:
        if args.dry_run:
            _EXECUCAO_REAL_AUTORIZADA = False
            with tempfile.TemporaryDirectory(prefix="coleta_dry_", ignore_cleanup_errors=True) as tmp:
                zip_bytes, fonte = _obter_zip(args, tmp)
                r = dry_run(recuperador=fabrica_recuperador(zip_bytes, tmp), git=git,
                            dataset_path=dataset_path, sha_dataset_esperado=sha_dataset_esperado)
            print(f"ZIP: {fonte['arquivo']} sha256={fonte['sha256']}")
            print(f"sha256_configuracao={r['sha256_configuracao']}")
            for a in r["avisos"]:
                print("AVISO:", a)
            if r["git"] and not r["git"]["apto_para_execute"]:
                print("Situação para --execute: BLOQUEADO —", r["git"]["motivo"])
            return 0
        _EXECUCAO_REAL_AUTORIZADA = True
        zip_bytes, fonte = _obter_zip(args, args.runtime)
        gerador = (fabrica_gerador or GeradorGemini)(args.chave)
        r = coletar(recuperador=fabrica_recuperador(zip_bytes, args.runtime), gerador=gerador, git=git,
                    dataset_path=dataset_path, sha_dataset_esperado=sha_dataset_esperado, saida=args.saida,
                    case_ids=args.case_id, limit=args.limit,
                    retentar_erros=args.retentar_erros, reexecutar_concluido=args.reexecutar_concluido,
                    motivo=args.motivo, segredos=getattr(gerador, "segredos", ()), pausa=args.pausa,
                    fonte_cvm=fonte)
        print(f"Encerramento: {r['encerramento']} | estados: {r['estados']}")
        return 0 if r["encerramento"] in ("completa", "nada_a_fazer") else 1
    except Bloqueio as b:
        print(f"PARADA: {b}")
        return 3
    finally:
        _EXECUCAO_REAL_AUTORIZADA = False


if __name__ == "__main__":
    sys.exit(main())
