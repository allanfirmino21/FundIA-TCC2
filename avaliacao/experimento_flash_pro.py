# avaliacao/experimento_flash_pro.py
#
# Experimento: Gemini 2.5 Flash vs. Gemini 2.5 Pro APENAS na etapa de redação.
# Critério e hipótese registrados em avaliacao/PRE_REGISTRO_flash_vs_pro.md ANTES
# da coleta — leia aquele arquivo antes de interpretar qualquer número daqui.
#
# A única variável é o modelo de redação. Documento, cálculo determinístico,
# contexto recuperado, prompt e temperatura são idênticos nos dois braços, e cada
# um desses é verificado por hash a cada execução.
#
# NÃO derive este script de comparar_modelos.py: aquele roda o Prompt 1 (extração
# via LLM) e troca o modelo nas DUAS etapas, o que viola a premissa de variável
# única. Aqui as métricas vêm exclusivamente de calcular_metricas.
#
# Sem rede: lê o .txt congelado em dados/cache/ e a collection já indexada no
# ChromaDB. A única saída de rede é a chamada de redação ao Gemini.
#
# Uso:
#   python avaliacao/experimento_flash_pro.py --tickers WEGE3 --execucoes 1
#   python avaliacao/experimento_flash_pro.py          # desenho completo (20)

import argparse
import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import modulos.prompt2 as prompt2
from modulos.extracao    import extrair_documento
from modulos.metricas    import calcular_metricas
from modulos.recuperacao import recuperar_contexto
from modulos.auditoria   import auditar_narrativa
from config              import MODELO_LLM, MODELO_LLM_PRO, CAMINHO_CACHE

# ── Desenho do experimento (fixo — ver pré-registro) ──────────────────────────

DT_REFER  = "2026-03-31"
CATEG_DOC = "ITR"
EXECUCOES = 2

TICKERS = ["WEGE3", "VALE3", "ITSA4", "BBAS3", "ZAMP3"]

# Nome da empresa CONGELADO. Ele entra no prompt (## CONTEXTO), então precisa ser
# idêntico entre os braços e estável entre execuções. Resolver via validar_ticker
# a cada rodada dispararia download do cadastro FCA (cache local vencido) — rede
# desnecessária durante a coleta, e um nome que mudasse alteraria o hash_prompt.
# Valores conferidos contra buscar_nome_empresa em 2026-08-30.
EMPRESAS = {
    "WEGE3": "WEG S.A.",
    "VALE3": "Vale S.A.",
    "ITSA4": "Itaúsa S.A.",
    "BBAS3": "Banco do Brasil S.A.",
    "ZAMP3": "ZAMP SA",
}

# Rótulo legível → id do modelo. A ordem desta lista define a intercalação.
MODELOS = [("flash", MODELO_LLM), ("pro", MODELO_LLM_PRO)]

PASTA           = os.path.dirname(os.path.abspath(__file__))
ARQ_CSV         = os.path.join(PASTA, "experimento_flash_pro.csv")
ARQ_VERIFIC     = os.path.join(PASTA, "experimento_flash_pro_verificacoes.json")
ARQ_MANIFESTO   = os.path.join(PASTA, "experimento_flash_pro_manifesto.json")
PASTA_NARRATIVAS = os.path.join(PASTA, "narrativas")

COLUNAS = [
    "ticker", "empresa", "dt_refer", "categ_doc",
    "hash_documento", "hash_contexto", "hash_prompt",
    "modelo", "execucao", "ordem_global", "timestamp",
    "latencia_s", "tokens_prompt", "tokens_saida", "tokens_raciocinio",
    "tokens_total", "finish_reason",
    "total_numeros", "conferem", "divergentes", "nao_encontrados",
    "taxa_conformidade",
]


class AbortoExperimento(Exception):
    """
    Condição que invalida a comparação. Não é 'resultado ruim': é sinal de que o
    experimento não mediu o que pretendia, e continuar produziria número sem
    significado. O progresso já gravado é preservado.
    """


# ── Hashes ────────────────────────────────────────────────────────────────────

def _sha256_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _sha256_arquivo(caminho: str) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()


# ── Manifesto: a memória do que precisa permanecer idêntico ───────────────────

def carregar_manifesto() -> dict:
    if os.path.exists(ARQ_MANIFESTO):
        with open(ARQ_MANIFESTO, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "criado_em":  datetime.now(timezone.utc).isoformat(),
        "dt_refer":   DT_REFER,
        "categ_doc":  CATEG_DOC,
        "documentos": {},   # ticker -> {caminho, hash_documento, empresa}
        "contextos":  {},   # ticker -> hash do contexto_narrativo
        "prompts":    {},   # ticker -> hash do prompt enviado
    }


def salvar_manifesto(manifesto: dict) -> None:
    with open(ARQ_MANIFESTO, "w", encoding="utf-8") as f:
        json.dump(manifesto, f, ensure_ascii=False, indent=2)


def _fixar_ou_conferir(manifesto: dict, secao: str, ticker: str,
                       valor: str, descricao: str) -> None:
    """
    Na primeira execução registra o hash; nas seguintes confere contra o
    registrado e aborta se divergir. É isto que sustenta a afirmação de que os
    dois modelos receberam entrada idêntica.
    """
    registrado = manifesto[secao].get(ticker)
    if registrado is None:
        manifesto[secao][ticker] = valor
        salvar_manifesto(manifesto)
        return
    if registrado != valor:
        raise AbortoExperimento(
            f"{descricao} de {ticker} mudou desde o registro no manifesto.\n"
            f"  esperado (manifesto): {registrado}\n"
            f"  encontrado agora:     {valor}\n"
            "A premissa de entrada idêntica caiu — a comparação entre modelos "
            "deixa de ser válida. Investigue antes de continuar."
        )


# ── Persistência dos resultados (com retomada) ────────────────────────────────

def carregar_feitas() -> set:
    """Combinações (ticker, modelo, execucao) já gravadas no CSV."""
    if not os.path.exists(ARQ_CSV):
        return set()
    with open(ARQ_CSV, "r", encoding="utf-8", newline="") as f:
        return {
            (linha["ticker"], linha["modelo"], int(linha["execucao"]))
            for linha in csv.DictReader(f)
        }


def gravar_linha(linha: dict) -> None:
    novo = not os.path.exists(ARQ_CSV)
    with open(ARQ_CSV, "a", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUNAS)
        if novo:
            escritor.writeheader()
        escritor.writerow(linha)
        f.flush()


def carregar_verificacoes() -> dict:
    if os.path.exists(ARQ_VERIFIC):
        with open(ARQ_VERIFIC, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def salvar_verificacoes(todas: dict) -> None:
    with open(ARQ_VERIFIC, "w", encoding="utf-8") as f:
        json.dump(todas, f, ensure_ascii=False, indent=2)


def salvar_narrativa(registro: dict) -> str:
    """
    Grava o texto integral da narrativa em .md, com um cabeçalho que torna o
    arquivo autossuficiente: quem lê o texto precisa saber de qual modelo e de
    qual entrada ele veio sem ter que cruzar com o CSV.
    """
    os.makedirs(PASTA_NARRATIVAS, exist_ok=True)
    nome = f"{registro['ticker']}_{registro['modelo']}_exec{registro['execucao']}.md"
    caminho = os.path.join(PASTA_NARRATIVAS, nome)

    r   = registro["resumo"]
    tel = registro["telemetria"]
    cabecalho = [
        f"# {registro['ticker']} — {registro['empresa']}",
        "",
        f"- **Modelo:** `{registro['modelo_id']}` (braço `{registro['modelo']}`)",
        f"- **Execução:** {registro['execucao']} | ordem global: {registro['ordem_global']}",
        f"- **Documento:** {CATEG_DOC} {DT_REFER}",
        f"- **Gerado em:** {registro['timestamp']}",
        f"- **Latência:** {tel.get('latencia_s')} s | "
        f"tokens: {tel.get('tokens_prompt')} entrada, {tel.get('tokens_saida')} saída, "
        f"{tel.get('tokens_raciocinio')} raciocínio | finish: `{tel.get('finish_reason')}`",
        f"- **Auditoria:** {r['conferem']}/{r['total_numeros']} conferem "
        f"({r['taxa_conformidade']}%) | divergentes: {r['divergentes']} | "
        f"não encontrados: {r['nao_encontrados']}",
        "- **Hashes:** documento `{}` | contexto `{}` | prompt `{}`".format(
            registro["hashes"]["documento"][:16],
            registro["hashes"]["contexto"][:16],
            (registro["hashes"]["prompt"] or "")[:16]),
        "",
        "---",
        "",
    ]
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(cabecalho))
        f.write(registro["narrativa_completa"] or "")
        f.write("\n")
    return caminho


# ── Preparo por empresa (uma vez, reaproveitado nas 4 execuções) ──────────────

def preparar(ticker: str, manifesto: dict) -> dict:
    """
    Documento congelado -> métricas determinísticas -> contexto do ChromaDB.
    Nenhuma etapa aqui chama a rede nem reindexa.
    """
    caminho = os.path.join(CAMINHO_CACHE, f"{ticker}_{CATEG_DOC}_{DT_REFER}.txt")
    if not os.path.exists(caminho):
        raise AbortoExperimento(
            f"Documento ausente: {caminho}\n"
            "O experimento não baixa nada — o .txt precisa estar congelado no cache."
        )

    hash_documento = _sha256_arquivo(caminho)
    registrado = manifesto["documentos"].get(ticker)
    if registrado is None:
        manifesto["documentos"][ticker] = {
            "caminho":        os.path.relpath(caminho, os.path.dirname(PASTA)),
            "hash_documento": hash_documento,
            "empresa":        EMPRESAS[ticker],
            "registrado_em":  datetime.now(timezone.utc).isoformat(),
        }
        salvar_manifesto(manifesto)
    elif registrado["hash_documento"] != hash_documento:
        raise AbortoExperimento(
            f"O documento de {ticker} mudou desde o registro no manifesto.\n"
            f"  esperado: {registrado['hash_documento']}\n"
            f"  atual:    {hash_documento}\n"
            f"  arquivo:  {caminho}\n"
            "Restaure o .txt original ou refaça o experimento inteiro — misturar "
            "documentos entre as rodadas invalida a comparação."
        )

    print(f"  documento: {os.path.basename(caminho)}  sha256={hash_documento[:16]}...")

    secoes = extrair_documento(caminho)
    dados  = {"sucesso": True, "dados": calcular_metricas(secoes)}

    print("  recuperando contexto do ChromaDB (sem reindexar)...")
    _ctx_num, ctx_nar = recuperar_contexto(ticker, CATEG_DOC, DT_REFER)
    hash_contexto = _sha256_texto(ctx_nar)
    _fixar_ou_conferir(manifesto, "contextos", ticker, hash_contexto,
                       "O contexto narrativo")
    print(f"  contexto:  {len(ctx_nar):,} chars  sha256={hash_contexto[:16]}...")

    return {
        "caminho":        caminho,
        "hash_documento": hash_documento,
        "secoes":         secoes,
        "dados":          dados,
        "contexto":       ctx_nar,
        "hash_contexto":  hash_contexto,
    }


# ── Uma execução (ticker, modelo, repetição) ──────────────────────────────────

def executar(ticker: str, rotulo: str, modelo_id: str, execucao: int,
             ordem_global: int, ctx: dict, manifesto: dict) -> tuple:
    """Roda a redação instrumentada e audita. Devolve (linha_csv, registro_json)."""
    # Reatribui a constante que prompt2 ligou ao próprio namespace no import.
    # Só o modelo muda entre os braços; nada mais é tocado.
    prompt2.MODELO_LLM = modelo_id

    narrativa = prompt2.executar_prompt_narrativa(
        ctx["dados"], ctx["contexto"], ticker, EMPRESAS[ticker],
        periodo=DT_REFER, retornar_telemetria=True,
    )
    tel = narrativa.get("telemetria") or {}

    if tel.get("modelo_efetivo") != modelo_id:
        raise AbortoExperimento(
            f"O modelo efetivamente chamado ({tel.get('modelo_efetivo')}) não é o "
            f"pretendido ({modelo_id}). A troca de modelo em runtime falhou."
        )

    # Entrada idêntica entre execuções da mesma empresa — o controle central.
    _fixar_ou_conferir(manifesto, "prompts", ticker, tel.get("hash_prompt") or "",
                       "O prompt enviado")

    if tel.get("finish_reason") == "MAX_TOKENS":
        raise AbortoExperimento(
            f"finish_reason = MAX_TOKENS em {ticker}/{rotulo}/exec{execucao}.\n"
            "A narrativa foi truncada: a métrica de cobertura (total_numeros) fica "
            "corrompida, porque o texto parou antes de citar tudo o que citaria.\n"
            "O desenho precisa mudar antes de continuar (ver pré-registro, seção 6)."
        )

    if not narrativa["sucesso"]:
        raise AbortoExperimento(
            f"A redação falhou em {ticker}/{rotulo}/exec{execucao}: {narrativa['erro']}\n"
            "Nada foi gravado para esta combinação; a retomada continua daqui."
        )

    auditoria = auditar_narrativa(narrativa["secoes"], ctx["secoes"], ctx["dados"]["dados"])
    resumo    = auditoria["resumo"]

    linha = {
        "ticker":            ticker,
        "empresa":           EMPRESAS[ticker],
        "dt_refer":          DT_REFER,
        "categ_doc":         CATEG_DOC,
        "hash_documento":    ctx["hash_documento"],
        "hash_contexto":     ctx["hash_contexto"],
        "hash_prompt":       tel.get("hash_prompt"),
        "modelo":            rotulo,
        "execucao":          execucao,
        "ordem_global":      ordem_global,
        "timestamp":         datetime.now(timezone.utc).isoformat(),
        "latencia_s":        tel.get("latencia_s"),
        "tokens_prompt":     tel.get("tokens_prompt"),
        "tokens_saida":      tel.get("tokens_saida"),
        "tokens_raciocinio": tel.get("tokens_raciocinio"),
        "tokens_total":      tel.get("tokens_total"),
        "finish_reason":     tel.get("finish_reason"),
        # Denominador: total_numeros JÁ exclui os IGNORADO. Nunca len(verificacoes).
        "total_numeros":     resumo["total_numeros"],
        "conferem":          resumo["conferem"],
        "divergentes":       resumo["divergentes"],
        "nao_encontrados":   resumo["nao_encontrados"],
        "taxa_conformidade": resumo["taxa_conformidade"],
    }

    # A lista COMPLETA, com os CONFERE individuais: sem eles a contagem não é
    # reauditável por terceiros (foi o que se perdeu na rodada de julho/2026).
    registro = {
        "ticker":       ticker,
        "empresa":      EMPRESAS[ticker],
        "modelo":       rotulo,
        "modelo_id":    modelo_id,
        "execucao":     execucao,
        "ordem_global": ordem_global,
        "timestamp":    linha["timestamp"],
        "hashes": {
            "documento": ctx["hash_documento"],
            "contexto":  ctx["hash_contexto"],
            "prompt":    tel.get("hash_prompt"),
        },
        "telemetria":         tel,
        "resumo":             resumo,
        "verificacoes":       auditoria["verificacoes"],
        "narrativa_completa": narrativa["narrativa_completa"],
    }
    return linha, registro


# ── Plano de execução ─────────────────────────────────────────────────────────

def plano_canonico() -> list:
    """
    As 20 execuções do desenho completo, na ordem intercalada:
    Flash-exec1, Pro-exec1, Flash-exec2, Pro-exec2 — empresa por empresa.

    Blocos por modelo confundiriam variação temporal da API com diferença entre
    modelos. O índice nesta lista é o ordem_global e vem SEMPRE do desenho
    completo, mesmo em rodadas parciais, para que a numeração não mude quando o
    restante for executado depois.
    """
    return [
        (ticker, rotulo, modelo_id, execucao)
        for ticker in TICKERS
        for execucao in range(1, EXECUCOES + 1)
        for rotulo, modelo_id in MODELOS
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description="Experimento Flash vs Pro (redação).")
    ap.add_argument("--tickers", nargs="+", default=None, metavar="TICKER",
                    help="subconjunto de empresas (padrão: todas as 5)")
    ap.add_argument("--execucoes", type=int, default=None, metavar="N",
                    help="rodar apenas as execuções 1..N (padrão: todas)")
    args = ap.parse_args()

    if not os.getenv("GEMINI_API_KEY"):
        print("Erro: defina GEMINI_API_KEY antes de rodar.", file=sys.stderr)
        return 2

    alvo_tickers = [t.upper() for t in (args.tickers or TICKERS)]
    desconhecidos = [t for t in alvo_tickers if t not in TICKERS]
    if desconhecidos:
        print(f"Erro: ticker(s) fora do desenho: {desconhecidos}", file=sys.stderr)
        return 2
    limite_exec = args.execucoes or EXECUCOES

    manifesto    = carregar_manifesto()
    feitas       = carregar_feitas()
    verificacoes = carregar_verificacoes()

    plano = plano_canonico()
    selecionadas = [
        (i + 1, t, r, m, e) for i, (t, r, m, e) in enumerate(plano)
        if t in alvo_tickers and e <= limite_exec
    ]
    pendentes = [x for x in selecionadas if (x[1], x[2], x[4]) not in feitas]

    print(f"Desenho completo: {len(plano)} execuções | selecionadas: "
          f"{len(selecionadas)} | já feitas: {len(selecionadas) - len(pendentes)} | "
          f"pendentes: {len(pendentes)}")
    if not pendentes:
        print("Nada a fazer.")
        return 0

    preparados: dict = {}
    concluidas = 0
    try:
        for ordem_global, ticker, rotulo, modelo_id, execucao in pendentes:
            if ticker not in preparados:
                print(f"\n=== {ticker} ({EMPRESAS[ticker]}) ===")
                preparados[ticker] = preparar(ticker, manifesto)

            print(f"[{ordem_global:>2}/20] {ticker} {rotulo:<5} exec{execucao} "
                  f"({modelo_id})...", flush=True)

            linha, registro = executar(ticker, rotulo, modelo_id, execucao,
                                       ordem_global, preparados[ticker], manifesto)

            gravar_linha(linha)
            verificacoes[f"{ticker}_{rotulo}_exec{execucao}"] = registro
            salvar_verificacoes(verificacoes)
            salvar_narrativa(registro)
            concluidas += 1

            print(f"         OK  {linha['conferem']}/{linha['total_numeros']} conferem "
                  f"({linha['taxa_conformidade']}%)  {linha['latencia_s']}s  "
                  f"{linha['tokens_total']} tokens "
                  f"(raciocínio: {linha['tokens_raciocinio']})")

    except AbortoExperimento as e:
        print(f"\n{'!' * 70}\nABORTADO\n{'!' * 70}\n{e}\n", file=sys.stderr)
        print(f"{concluidas} execução(ões) desta rodada foram gravadas. "
              f"Resultados parciais em:\n  {ARQ_CSV}\n  {ARQ_VERIFIC}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print(f"\nInterrompido. {concluidas} execução(ões) gravadas; "
              "rode de novo para retomar de onde parou.", file=sys.stderr)
        return 130

    print(f"\nOK: {concluidas} execução(ões) nesta rodada.")
    print(f"  {ARQ_CSV}\n  {ARQ_VERIFIC}\n  {ARQ_MANIFESTO}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
