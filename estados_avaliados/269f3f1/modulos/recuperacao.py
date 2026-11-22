# modulos/recuperacao.py
import logging
import os
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Optional, Tuple
from modulos.chunking import nome_collection
from config import MODELO_EMBEDDINGS, MAX_CHUNKS_NUMERICO, MAX_CHUNKS_NARRATIVO, CAMINHO_CHROMA

# Silencia avisos de carregamento do modelo (mesmo tratamento de chunking.py)
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

QUERY_NUMERICO = "receita líquida lucro bruto EBITDA margem operacional lucro líquido endividamento dívida caixa resultado financeiro variação percentual"
QUERY_NARRATIVO = "desempenho operacional comentários da administração perspectivas principais eventos mercado estratégia riscos destaques do período"

def recuperar_contexto(ticker: str, tipo_doc: str, periodo: str) -> Tuple[str, str]:
    """
    Recupera o contexto do documento em dois canais independentes.

    O canal numérico prioriza chunks de tabela; o narrativo, trechos
    discursivos. Separá-los evita que a busca por semelhança devolva só
    tabelas (que dominam o documento) quando o que falta é contexto textual.
    Nos dois canais, as tabelas ficam restritas à base principal do documento
    (ver _base_principal), a mesma usada nas métricas.

    Returns:
        (contexto_numerico, contexto_narrativo), já formatados para o prompt.
    """
    modelo     = SentenceTransformer(MODELO_EMBEDDINGS)
    cliente    = chromadb.PersistentClient(path=CAMINHO_CHROMA)
    collection = cliente.get_collection(nome_collection(ticker, tipo_doc, periodo))
    return _contextos(collection, modelo)

def _contextos(collection, modelo) -> Tuple[str, str]:
    """Os dois canais sobre uma collection já aberta, com a mesma base contábil."""
    base    = _base_principal(collection)
    ctx_num = _recuperar_canal(collection, modelo, QUERY_NUMERICO,  "tabela",    MAX_CHUNKS_NUMERICO,  base)
    ctx_nar = _recuperar_canal(collection, modelo, QUERY_NARRATIVO, "narrativo", MAX_CHUNKS_NARRATIVO, base)
    return ctx_num, ctx_nar

_TITULO_DRE_CONSOLIDADA = "Demonstração de Resultado (Consolidado)"

def _base_principal(collection) -> Optional[str]:
    """
    Base contábil das tabelas que podem chegar ao LLM — a mesma regra de
    calcular_metricas(): "Consolidado" se o documento tem DRE consolidada,
    senão "Individual" se tem tabelas individuais. None quando a base é
    desconhecida (PDF): aí nenhum filtro de base é aplicado.

    Sem essa regra única, o complemento do canal narrativo aceitava qualquer
    tabela e entregava ao Prompt 2 a DRE Individual de empresas consolidadas
    (59 de 412 no ITR de 30/06/2026, entre elas a WEGE3).
    """
    try:
        metas = collection.get(where={"tipo": "tabela"}, include=["metadatas"])["metadatas"]
    except Exception:
        return None
    if any(m.get("secao") == _TITULO_DRE_CONSOLIDADA for m in metas):
        return "Consolidado"
    if any(m.get("base") == "Individual" for m in metas):
        return "Individual"
    return None

def _where_tabela(base: Optional[str]) -> dict:
    if base is None:
        return {"tipo": "tabela"}
    return {"$and": [{"tipo": {"$eq": "tabela"}}, {"base": {"$eq": base}}]}

def _recuperar_canal(collection, modelo, query, tipo_prio, n, base: Optional[str] = None) -> str:
    """
    Recupera até n chunks priorizando `tipo_prio` e completa com o outro tipo.
    Toda busca por tabelas fica restrita à `base` principal quando ela é
    conhecida.

    Exceção: com base conhecida (documento estruturado da CVM), o canal
    narrativo NÃO é completado com tabelas. Esses documentos não têm texto
    narrativo além do cabeçalho, e o complemento entregava ao Prompt 2 uma
    tabela inteira escolhida por semelhança (a DFC em 389 de 412 empresas
    consolidadas), cujas linhas eram lidas fora de contexto. O resultado e o
    caixa chegam ao Prompt 2 pelas métricas (demonstracoes_resumidas).
    """
    emb = modelo.encode(query).tolist()
    try:
        if tipo_prio == "tabela" and base is None:
            # Base desconhecida (PDF): comportamento anterior — prefere
            # Consolidado e, se não houver, aceita qualquer base
            where_cons = {"$and": [{"tipo": {"$eq": "tabela"}}, {"base": {"$eq": "Consolidado"}}]}
            res    = collection.query(query_embeddings=[emb], n_results=n, where=where_cons)
            chunks = res["documents"][0]
            if not chunks:
                print("[recuperacao] aviso: nenhum chunk Consolidado encontrado — fallback sem filtro de base")
                res    = collection.query(query_embeddings=[emb], n_results=n, where={"tipo": tipo_prio})
                chunks = res["documents"][0]
        else:
            where  = _where_tabela(base) if tipo_prio == "tabela" else {"tipo": tipo_prio}
            res    = collection.query(query_embeddings=[emb], n_results=n, where=where)
            chunks = res["documents"][0]
        ids = set(res["ids"][0])
    except Exception:
        chunks, ids = [], set()
    completar = not (tipo_prio == "narrativo" and base is not None)
    if completar and len(chunks) < n:
        tipo_sec = "narrativo" if tipo_prio == "tabela" else "tabela"
        where_sec = _where_tabela(base) if tipo_sec == "tabela" else {"tipo": tipo_sec}
        try:
            res2 = collection.query(query_embeddings=[emb], n_results=n - len(chunks), where=where_sec)
            for doc, id_ in zip(res2["documents"][0], res2["ids"][0]):
                if id_ not in ids:
                    chunks.append(doc)
        except Exception:
            pass
    return _formatar_contexto(chunks, tipo_prio)

def _formatar_contexto(chunks: List[str], rotulo: str) -> str:
    sep = "-" * 40
    blocos = [f"[Trecho {i+1}]\n{c}" for i, c in enumerate(chunks)]
    return f"=== CONTEXTO {rotulo.upper()} ===\n{sep}\n{(chr(10)+sep+chr(10)).join(blocos)}\n{sep}"