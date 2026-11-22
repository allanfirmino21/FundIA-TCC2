# modulos/orquestrador.py
import os

from modulos.ticker      import validar_ticker, buscar_nome_empresa
from modulos.cvm         import (buscar_documento_mais_recente, baixar_documento,
                                 FORMATO_DOCUMENTO)
from modulos.extracao    import extrair_documento, verificar_qualidade_extracao
from modulos.chunking    import criar_chunks, indexar_documento
from modulos.recuperacao import recuperar_contexto
from modulos.metricas    import calcular_metricas
from modulos.auditoria   import auditar_narrativa
from modulos.prompt1     import executar_prompt_extracao
from modulos.prompt2     import executar_prompt_narrativa
from config              import CAMINHO_CACHE

def analisar(ticker: str, tipo_doc: str = "ITR", forcar: bool = False,
             on_progress: callable = None, periodo: str = "",
             versao: str = "") -> dict:
    """
    Executa as oito etapas do pipeline para um ticker da B3 e devolve a análise.

    Do código de negociação ao selo de auditoria: valida o ticker, baixa o
    documento da CVM, calcula as métricas em Python, gera a narrativa com o
    LLM e audita cada número citado contra a fonte.

    Args:
        ticker: código de negociação (ex.: "WEGE3").
        tipo_doc: "ITR" (trimestral) ou "DFP" (anual).
        forcar: ignora o cache local e baixa novamente da CVM.
        on_progress: callback (etapa, mensagem) chamado a cada etapa.
        periodo: DT_REFER exato ("AAAA-MM-DD"); vazio = mais recente.
        versao: VERSAO exata do documento; vazio = maior versão da referência.

    Returns:
        dict com ticker, nome_empresa, documento, etapas, analise e erro.
        Em caso de falha, "erro" traz a mensagem e "analise" fica None; a
        auditoria é opcional (falha nela não invalida a análise).
    """
    resultado = {
        "ticker":         ticker.upper(),
        "tipo_documento": tipo_doc,
        "etapas":         {},
        "analise":        None,
        "erro":           None,
    }

    # ── 1. Validacao do ticker ─────────────────────────────────────────────────
    try:
        _log("1/8", "Validando ticker...", on_progress)
        val = validar_ticker(ticker)
        if not val["valido"]:
            return _erro(resultado, val["motivo"], on_progress)
        codigo_cvm   = val["codigo_cvm"]
        nome_empresa = buscar_nome_empresa(codigo_cvm)
        resultado["etapas"]["validacao"] = "ok"
        resultado["nome_empresa"]        = nome_empresa
        _log("1/8", f"OK: {nome_empresa} ({codigo_cvm})", on_progress)
    except Exception as e:
        return _erro(resultado, f"Erro ao validar o ticker '{ticker}': {e}", on_progress)

    # ── 2. Busca do documento (mais recente ou período/versão fixados) ─────────
    try:
        alvo = f"{periodo or 'mais recente'}" + (f" versao {versao}" if versao else "")
        _log("2/8", f"Buscando {tipo_doc} ({alvo}) na CVM...", on_progress)
        meta = buscar_documento_mais_recente(codigo_cvm, tipo_doc,
                                             periodo=periodo or None,
                                             versao=versao or None)
        if not meta:
            if periodo or versao:
                return _erro(
                    resultado,
                    f"Documento {tipo_doc} {alvo} nao existe na CVM para '{ticker}'. "
                    "Nenhum outro periodo ou versao foi usado no lugar.",
                    on_progress
                )
            return _erro(
                resultado,
                f"Nenhum documento {tipo_doc} encontrado para '{ticker}'. "
                "Verifique se a empresa entregou o relatorio a CVM recentemente "
                "ou se o codigo CVM esta correto.",
                on_progress
            )
        resultado["etapas"]["busca_cvm"] = "ok"
        resultado["documento"] = {"periodo": meta["periodo"], "versao": meta["versao"],
                                  "link": meta.get("link", "")}
        _log("2/8", f"OK: Periodo {meta['periodo']} versao {meta['versao']} encontrado "
                    f"(entregue em {meta.get('data_entrega', '—')})", on_progress)
    except ValueError as e:
        # Seleção inválida ou documento inexistente para o período/versão pedidos
        return _erro(resultado, f"{e} Nenhum outro periodo ou versao foi usado no lugar.",
                     on_progress)
    except Exception as e:
        return _erro(
            resultado,
            f"Falha ao buscar documento na CVM: {e}. "
            "Verifique sua conexao com a internet e tente novamente.",
            on_progress
        )

    # ── 3. Download dos dados estruturados ─────────────────────────────────────
    try:
        _log("3/8", "Baixando dados estruturados...", on_progress)
        os.makedirs(CAMINHO_CACHE, exist_ok=True)
        periodo_fmt = meta["periodo"].replace("/", "-")
        # O nome do arquivo (ticker + tipo + período) é o que api.py e os
        # scripts de avaliação esperam; a versão fica no cabeçalho, e o
        # cabeçalho inteiro é conferido antes de qualquer reuso.
        caminho = os.path.join(CAMINHO_CACHE,
                               f"{ticker.upper()}_{tipo_doc}_{periodo_fmt}.txt")
        usar_cache = os.path.exists(caminho) and not forcar
        if usar_cache and not _cache_confere(caminho, codigo_cvm, tipo_doc,
                                             meta["periodo"], meta["versao"]):
            _log("3/8", f"Cache {os.path.basename(caminho)} nao corresponde a "
                        f"CVM {codigo_cvm} / {tipo_doc} {meta['periodo']} versao "
                        f"{meta['versao']} — descartando e baixando novamente.",
                 on_progress)
            os.remove(caminho)
            usar_cache = False
        if not usar_cache:
            caminho = baixar_documento(
                link       = meta.get("link", ""),
                destino    = caminho,
                codigo_cvm = codigo_cvm,
                tipo       = tipo_doc,
                periodo    = meta["periodo"],
                versao     = meta["versao"],
            )
            kb = os.path.getsize(caminho) // 1024
            _log("3/8", f"OK: {os.path.basename(caminho)} baixado ({kb} KB)", on_progress)
        else:
            kb = os.path.getsize(caminho) // 1024
            _log("3/8", f"OK: Cache local reutilizado ({kb} KB)", on_progress)
        resultado["etapas"]["download"] = "ok"
    except RuntimeError as e:
        # RuntimeError ja tem mensagem descritiva de cvm.py
        return _erro(resultado, str(e), on_progress)
    except Exception as e:
        return _erro(
            resultado,
            f"Falha ao baixar o documento da CVM: {e}. "
            "Verifique sua conexao e tente novamente mais tarde.",
            on_progress
        )

    # ── 4. Extracao de secoes ──────────────────────────────────────────────────
    try:
        _log("4/8", "Extraindo secoes...", on_progress)
        secoes    = extrair_documento(caminho)
        qualidade = verificar_qualidade_extracao(secoes)
        if not qualidade["extraivel"]:
            return _erro(
                resultado,
                qualidade.get(
                    "aviso",
                    "O documento nao contem dados financeiros legiveis. "
                    "Verifique se o arquivo foi baixado corretamente."
                ),
                on_progress
            )
        resultado["etapas"]["extracao"] = {
            "status": "ok",
            "secoes": qualidade["secoes_identificadas"],
        }
        _log("4/8", f"OK: {qualidade['secoes_identificadas']} secoes extraidas "
                    f"({qualidade['chars_totais']:,} caracteres)", on_progress)
    except ValueError as e:
        # ValueError ja tem mensagem clara de extracao.py
        return _erro(resultado, str(e), on_progress)
    except Exception as e:
        return _erro(resultado, f"Erro ao extrair o documento: {e}", on_progress)

    # ── 5. Embeddings e indexacao ──────────────────────────────────────────────
    try:
        _log("5/8", "Indexando chunks...", on_progress)
        chunks     = criar_chunks(secoes)
        # Documento recém-baixado: recria a collection, para não recuperar
        # chunks de uma versão anterior indexada com o mesmo ticker/período.
        collection = indexar_documento(ticker, chunks, tipo_doc, meta["periodo"],
                                       forcar=forcar or not usar_cache)
        resultado["etapas"]["indexacao"] = {"status": "ok", "chunks": len(chunks)}
        _log("5/8", f"OK: {len(chunks)} chunks indexados", on_progress)
    except Exception as e:
        return _erro(
            resultado,
            f"Falha ao gerar embeddings ou indexar o documento: {e}. "
            "Verifique se o modelo sentence-transformers esta instalado e ha memoria disponivel.",
            on_progress
        )

    # ── 6. Recuperacao RAG ─────────────────────────────────────────────────────
    try:
        _log("6/8", "Recuperando contexto RAG...", on_progress)
        ctx_num, ctx_nar = recuperar_contexto(ticker, tipo_doc, meta["periodo"])
        resultado["etapas"]["recuperacao"] = "ok"
        _log("6/8", f"OK: Contextos recuperados ({len(ctx_num):,} chars numericos, "
                    f"{len(ctx_nar):,} narrativos)", on_progress)
    except Exception as e:
        return _erro(
            resultado,
            f"Falha na recuperacao de contexto (RAG): {e}. "
            "Isso pode indicar um problema na indexacao. Tente com forcar=True.",
            on_progress
        )

    # ── 7a. Metricas — calculo deterministico em Python ───────────────────────
    # As metricas (variacoes, margem, divida liquida) sao calculadas em codigo
    # a partir do documento estruturado, eliminando erros de aritmetica do LLM.
    # Se o documento nao for parseavel (ex.: PDF antigo), cai no caminho legado
    # de extracao via LLM (Prompt 1).
    try:
        _log("7/8", "Calculando metricas (deterministico)...", on_progress)
        dados = {"sucesso": True, "dados": calcular_metricas(secoes)}
    except ValueError as e:
        _log("7/8", f"Calculo deterministico indisponivel ({e}) — "
                    "usando extracao via LLM (Prompt 1)...", on_progress)
        dados = executar_prompt_extracao(ctx_num)
        if not dados["sucesso"]:
            return _erro(resultado, dados["erro"], on_progress)

    # ── 7b. Prompt 2 — narrativa ───────────────────────────────────────────────
    _log("7/8", "Gerando analise - Prompt 2...", on_progress)
    narrativa = executar_prompt_narrativa(
        dados, ctx_nar, ticker.upper(), nome_empresa,
        periodo=meta["periodo"]
    )
    if not narrativa["sucesso"]:
        return _erro(resultado, narrativa["erro"], on_progress)

    resultado["etapas"]["geracao"] = "ok"
    resultado["analise"] = {
        "dados_extraidos":    dados["dados"],
        "secoes":             narrativa["secoes"],
        "narrativa_completa": narrativa["narrativa_completa"],
        "periodo":            meta["periodo"],
    }

    # ── 8. Auditoria de fidelidade numerica ────────────────────────────────────
    # Confere cada numero citado na narrativa contra o documento da CVM e as
    # metricas calculadas. Falha na auditoria nao invalida a analise — apenas
    # deixa de anexar o selo de conformidade.
    try:
        _log("8/8", "Auditando fidelidade numerica...", on_progress)
        auditoria = auditar_narrativa(narrativa["secoes"], secoes, dados["dados"])
        res_aud = auditoria["resumo"]
        resultado["etapas"]["auditoria"] = "ok"
        resultado["analise"]["auditoria"] = auditoria
        _log("8/8", f"OK: {res_aud['conferem']}/{res_aud['total_numeros']} numeros "
                    f"conferem com a fonte (conformidade {res_aud['taxa_conformidade']}%)",
             on_progress)
    except Exception as e:
        resultado["etapas"]["auditoria"] = f"indisponivel: {e}"
        resultado["analise"]["auditoria"] = None
        _log("8/8", f"Auditoria indisponivel: {e}", on_progress)

    _log("OK", f"Analise de {ticker.upper()} concluida.", on_progress)
    return resultado


def _cache_confere(caminho: str, codigo_cvm: str, tipo: str,
                   periodo: str, versao: str) -> bool:
    """
    Confere se o cabeçalho do cache ("DOCUMENTO: <tipo> — <período>",
    "EMPRESA CVM:", "VERSAO:", "FORMATO:") corresponde exatamente ao documento
    pedido e ao formato atual de cvm.py. Um cache de outra empresa (mapeamento
    antigo errado), de outro período ou de outra versão pode estar sob o mesmo
    nome de arquivo; nesse caso — ou se faltar qualquer campo, como nos caches
    anteriores à versão ou ao CD_CONTA nas linhas — o arquivo deve ser
    descartado.
    """
    campos = {}
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            for linha in [f.readline() for _ in range(5)]:
                if ":" in linha:
                    chave, valor = linha.split(":", 1)
                    campos[chave.strip().upper()] = valor.strip()
    except Exception:
        return False

    return (
        campos.get("DOCUMENTO") == f"{tipo} — {periodo}"
        and campos.get("EMPRESA CVM", "").lstrip("0") == str(codigo_cvm).strip().lstrip("0")
        and campos.get("VERSAO") == str(versao).strip()
        and campos.get("FORMATO") == FORMATO_DOCUMENTO
    )


def _log(etapa, msg, on_progress=None):
    print(f"[{etapa}] {msg}")
    if on_progress:
        on_progress(etapa, msg)

def _erro(r, msg, on_progress=None):
    r["erro"] = msg
    _log("ERRO", msg, on_progress)
    return r
