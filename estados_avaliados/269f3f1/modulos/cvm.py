# modulos/cvm.py
#
# Fonte de dados: CVM Open Data (dados.cvm.gov.br)
#
# As URLs /META/ITR_CIA_ABERTA_{ano}.csv estão inativas (404).
# O ZIP correto é /DADOS/itr_cia_aberta_{ano}.zip, que contém:
#   • itr_cia_aberta_{ano}.csv          → índice de documentos (empresa, período, link)
#   • itr_cia_aberta_DRE_con_{ano}.csv  → demonstrações financeiras
#   • itr_cia_aberta_BPA_con_{ano}.csv  → balanço ativo
#   • itr_cia_aberta_BPP_con_{ano}.csv  → balanço passivo
#   • itr_cia_aberta_DFC_MD_con_{ano}.csv → fluxo de caixa
#   • ... demais demonstrações

import requests
import zipfile
import io
import os
import time
import pandas as pd
from datetime import datetime

BASE_DADOS  = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC"
CACHE_DIR   = "dados"
CACHE_HORAS = 24

# Formato do .txt gerado por baixar_documento, gravado no cabeçalho. Caches
# sem este marcador não trazem CD_CONTA nas linhas e são descartados pelo
# orquestrador.
FORMATO_DOCUMENTO = "CD_CONTA"

# ── Cache em memória (por tipo + ano) ────────────────────────────────────────
# Armazena o índice já extraído para evitar re-download no mesmo processo
_indice_cache: dict[str, pd.DataFrame] = {}


# ── URLs ──────────────────────────────────────────────────────────────────────

def _url_dados_zip(tipo: str, ano: int) -> str:
    """URL do ZIP anual de dados estruturados."""
    return f"{BASE_DADOS}/{tipo}/DADOS/{tipo.lower()}_cia_aberta_{ano}.zip"


def _cache_path_indice(tipo: str, ano: int) -> str:
    """Caminho local do índice de documentos extraído do ZIP."""
    return os.path.join(CACHE_DIR, f"meta_{tipo.lower()}_{ano}.csv")


# ── Carregamento do índice de documentos ─────────────────────────────────────

def _carregar_indice_ano(tipo: str, ano: int) -> pd.DataFrame | None:
    """
    Retorna o DataFrame-índice de documentos para um dado tipo/ano.

    Estratégia de cache (em ordem de prioridade):
      1. Memória (mesmo processo)
      2. Disco (arquivo CSV local com menos de CACHE_HORAS)
      3. Download do ZIP → extrai só o arquivo-índice → salva em disco
      4. Fallback: cache em disco expirado (se o download falhar)
    """
    chave = f"{tipo}_{ano}"

    # 1. Memória
    if chave in _indice_cache:
        return _indice_cache[chave]

    # 2. Disco (cache válido)
    caminho = _cache_path_indice(tipo, ano)
    if os.path.exists(caminho):
        idade_h = (time.time() - os.path.getmtime(caminho)) / 3600
        if idade_h < CACHE_HORAS:
            df = pd.read_csv(caminho, sep=";", encoding="latin-1", dtype=str)
            _indice_cache[chave] = df
            return df

    # 3. Download
    url = _url_dados_zip(tipo, ano)
    print(f"[cvm] Baixando índice {tipo} {ano}...")
    try:
        resp = requests.get(url, timeout=120)
        if resp.status_code == 404:
            print(f"[cvm] ZIP {tipo}/{ano} não encontrado (404).")
            return None
        resp.raise_for_status()

        nome_indice = f"{tipo.lower()}_cia_aberta_{ano}.csv"
        with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
            if nome_indice not in z.namelist():
                # Tenta o primeiro CSV disponível como índice
                candidatos = [n for n in z.namelist() if n.endswith(".csv")
                              and "_" not in n.replace(f"{tipo.lower()}_cia_aberta_", "").replace(f"_{ano}.csv", "")]
                if not candidatos:
                    print(f"[cvm] Arquivo-índice não encontrado no ZIP {tipo}/{ano}.")
                    return None
                nome_indice = candidatos[0]
            with z.open(nome_indice) as f:
                df = pd.read_csv(f, sep=";", encoding="latin-1", dtype=str)

        os.makedirs(CACHE_DIR, exist_ok=True)
        df.to_csv(caminho, sep=";", index=False, encoding="latin-1")
        _indice_cache[chave] = df
        print(f"[cvm] OK:{len(df):,} registros no indice {tipo}/{ano}")
        return df

    except Exception as e:
        print(f"[cvm] Erro ao baixar indice {tipo}/{ano}: {e}")

    # 4. Fallback: cache expirado
    if os.path.exists(caminho):
        print(f"[cvm] Usando cache expirado como fallback ({caminho}).")
        df = pd.read_csv(caminho, sep=";", encoding="latin-1", dtype=str)
        _indice_cache[chave] = df
        return df

    return None


# ── Busca do documento mais recente ──────────────────────────────────────────

def _validar_selecao(tipo, periodo=None, versao=None):
    tipo = tipo.strip().upper()
    if tipo not in ("ITR", "DFP"):
        raise ValueError("Tipo deve ser ITR ou DFP.")
    if periodo is not None:
        if datetime.strptime(periodo, "%Y-%m-%d").strftime("%Y-%m-%d") != periodo:
            raise ValueError("Período deve usar AAAA-MM-DD.")
    if versao is not None:
        if not str(versao).isdigit() or int(versao) < 1:
            raise ValueError("Versão deve ser um inteiro positivo.")
        versao = int(versao)
    return tipo, periodo, versao


def _filtrar_identidade(df, codigo_cvm, periodo=None, versao=None):
    obrigatorias = {"CD_CVM", "DT_REFER", "VERSAO"}
    if not obrigatorias.issubset(df.columns):
        raise ValueError(f"Colunas obrigatórias ausentes: {obrigatorias - set(df.columns)}")
    selecionado = df[df["CD_CVM"].astype(str).str.strip().str.lstrip("0")
                     == str(codigo_cvm).strip().lstrip("0")].copy()
    if periodo is not None:
        selecionado = selecionado[selecionado["DT_REFER"] == periodo]
    selecionado["VERSAO"] = pd.to_numeric(selecionado["VERSAO"], errors="raise")
    if versao is not None:
        selecionado = selecionado[selecionado["VERSAO"] == versao]
    return selecionado


def buscar_documento_mais_recente(codigo_cvm: str, tipo: str = "ITR",
                                  periodo: str | None = None,
                                  versao: int | None = None) -> dict | None:
    """Busca referência exata ou a mais recente; sem versão, escolhe a maior.

    Seleção explícita inexistente gera erro, nunca substituição por outra data.
    """
    tipo, periodo, versao = _validar_selecao(tipo, periodo, versao)
    anos = (int(periodo[:4]),) if periodo else (datetime.now().year, datetime.now().year - 1)
    for ano in anos:
        df = _carregar_indice_ano(tipo, ano)
        if df is None:
            continue
        if "CATEG_DOC" not in df.columns:
            raise ValueError("Índice sem CATEG_DOC; tipo não verificável.")
        empresa = _filtrar_identidade(df, codigo_cvm, periodo)
        empresa = empresa[empresa["CATEG_DOC"].str.strip().str.upper() == tipo]
        if empresa.empty:
            continue
        referencia = periodo or empresa["DT_REFER"].max()
        empresa = empresa[empresa["DT_REFER"] == referencia]
        escolhida = versao if versao is not None else int(empresa["VERSAO"].max())
        empresa = empresa[empresa["VERSAO"] == escolhida].drop_duplicates()
        if empresa.empty:
            raise ValueError(f"Documento inexistente: CVM {codigo_cvm}, {tipo}, {referencia}, versão {escolhida}.")
        if len(empresa) != 1:
            raise ValueError("Documento ambíguo para empresa/tipo/período/versão.")
        doc = empresa.iloc[0]
        return {
            "empresa": str(doc.get("DENOM_CIA", "—")),
            "periodo": referencia,
            "data_entrega": str(doc.get("DT_RECEB", "—")),
            "link": str(doc.get("LINK_DOC", "")).replace("http://", "https://", 1),
            "id_doc": str(doc.get("ID_DOC", "")),
            "versao": escolhida,
            "ano": int(referencia[:4]),
        }
    if periodo is not None or versao is not None:
        raise ValueError(f"Documento inexistente ou índice indisponível: CVM {codigo_cvm}, {tipo}, {periodo}, versão {versao}.")
    return None


# ── Seções financeiras que serão extraídas ───────────────────────────────────

SECOES_RELEVANTES = {
    "DRE_con":            "Demonstração de Resultado (Consolidado)",
    "DRE_ind":            "Demonstração de Resultado (Individual)",
    "BPA_con":            "Balanço Patrimonial — Ativo (Consolidado)",
    "BPP_con":            "Balanço Patrimonial — Passivo (Consolidado)",
    # A CVM publica a DFC em dois formatos: método indireto (DFC_MI, usado pela
    # quase totalidade das empresas — é o que traz a linha de depreciação e
    # amortização, insumo do EBITDA) e método direto (DFC_MD). Tenta o MI
    # primeiro; o MD fica como alternativa. Títulos iguais: só um é gravado.
    "DFC_MI_con":         "Demonstração de Fluxo de Caixa (Consolidado)",
    "DFC_MD_con":         "Demonstração de Fluxo de Caixa (Consolidado)",
    "composicao_capital": "Composição do Capital Social",
}

# Seções sem as quais o documento não pode ser gravado. Empresa que publica
# DRE consolidada precisa ter também balanço e DFC consolidados no mesmo
# período/versão; empresa sem consolidado só tem a DRE individual aqui
# (BPA/BPP/DFC individuais não são extraídos). composicao_capital não entra.
SECOES_ESSENCIAIS_CONSOLIDADO = (
    SECOES_RELEVANTES["DRE_con"],
    SECOES_RELEVANTES["BPA_con"],
    SECOES_RELEVANTES["BPP_con"],
    SECOES_RELEVANTES["DFC_MI_con"],   # MI ou MD: mesmo título
)


# ── Download e formatação dos dados financeiros ───────────────────────────────

def baixar_documento(link: str, destino: str,
                     codigo_cvm: str = "", tipo: str = "ITR",
                     periodo: str = "", versao: str = "") -> str:
    """
    Baixa os demonstrativos financeiros estruturados do ZIP de dados da CVM
    e grava um arquivo .txt formatado para o pipeline de RAG.

    Só aceita linhas com DT_REFER == periodo e VERSAO == versao, lidas do ZIP
    do próprio ano do período. Não há fallback para outro ano nem para outra
    referência: se a empresa tem dados na seção, mas não daquele período e
    versão, lança RuntimeError em vez de gravar valores de outra data.
    """
    tipo, periodo, versao = _validar_selecao(tipo, periodo, versao)
    if not codigo_cvm or not periodo or versao is None:
        raise ValueError("Código CVM, período e versão são obrigatórios.")
    ano_referencia = int(periodo[:4])
    ano_usado = ano_referencia
    resp = requests.get(_url_dados_zip(tipo, ano_usado), timeout=120)
    resp.raise_for_status()  # Sem fallback para outro ano.
    conteudo_zip = resp.content

    secoes_texto = [
        f"DOCUMENTO: {tipo} — {periodo}",
        f"EMPRESA CVM: {codigo_cvm}",
        f"VERSAO: {versao}",
        f"FORMATO: {FORMATO_DOCUMENTO}",
        "",
    ]
    tamanho_cabecalho = len(secoes_texto)

    secoes_gravadas: set[str] = set()

    with zipfile.ZipFile(io.BytesIO(conteudo_zip)) as z:
        arquivos_zip = set(z.namelist())
        for sufixo, nome_secao in SECOES_RELEVANTES.items():
            if nome_secao in secoes_gravadas:
                continue
            # Nome canônico do CSV dentro do ZIP
            nome_csv = f"{tipo.lower()}_cia_aberta_{sufixo}_{ano_usado}.csv"
            if nome_csv not in arquivos_zip:
                continue
            with z.open(nome_csv) as f:
                df = pd.read_csv(f, sep=";", encoding="latin-1", dtype=str)
            if "CD_CVM" not in df.columns:
                # composicao_capital identifica a empresa só por CNPJ; sempre
                # foi ignorada aqui (não entra no documento).
                continue
            empresa_df = _filtrar_identidade(df, codigo_cvm, periodo, versao)
            if empresa_df.empty:
                continue  # Seção ausente; nunca aproveitar outra referência/versão.

            secoes_texto.append(f"\n{'='*50}")
            secoes_texto.append(nome_secao)
            secoes_texto.append("=" * 50)
            secoes_texto.append(_formatar_df_financeiro(empresa_df))
            secoes_gravadas.add(nome_secao)

    if len(secoes_texto) <= tamanho_cabecalho:
        raise RuntimeError(
            f"Nenhum dado estruturado encontrado para CVM {codigo_cvm} "
            f"no período '{periodo}' versão {versao}. "
            "Verifique se o código CVM está correto e se a empresa entregou ITR nesse período."
        )

    if SECOES_RELEVANTES["DRE_con"] in secoes_gravadas:
        ausentes = [s for s in SECOES_ESSENCIAIS_CONSOLIDADO if s not in secoes_gravadas]
    elif SECOES_RELEVANTES["DRE_ind"] in secoes_gravadas:
        ausentes = []
    else:
        ausentes = ["Demonstração de Resultado (Consolidado ou Individual)"]
    if ausentes:
        raise RuntimeError(
            f"Documento incompleto para CVM {codigo_cvm}, {tipo} {periodo} "
            f"versão {versao}: seção(ões) essencial(is) ausente(s): "
            f"{'; '.join(ausentes)}. Nenhum documento foi gravado."
        )

    # Garante extensão .txt (o destino pode vir como .pdf em fluxos legados)
    destino_final = (destino if destino.endswith(".txt")
                     else os.path.splitext(destino)[0] + ".txt")
    os.makedirs(os.path.dirname(os.path.abspath(destino_final)), exist_ok=True)

    with open(destino_final, "w", encoding="utf-8") as f:
        f.write("\n".join(secoes_texto))

    tamanho = os.path.getsize(destino_final) / 1024
    print(f"[cvm] Documento salvo: {destino_final} ({tamanho:.0f} KB)")
    return destino_final


# ── Formatação dos dados financeiros ─────────────────────────────────────────

def _formatar_df_financeiro(df: pd.DataFrame) -> str:
    """
    Formata as linhas do demonstrativo financeiro em texto legível.
    Exibe valor atual e, quando disponível, o valor do período anterior.
    """
    col_conta  = next((c for c in df.columns if "DS_CONTA"     in c.upper()), None)
    col_valor  = next((c for c in df.columns if "VL_CONTA"     in c.upper()), None)
    col_ordem  = next((c for c in df.columns if "ORDEM_EXERC"  in c.upper()), None)
    col_codigo = next((c for c in df.columns if "CD_CONTA"     in c.upper()), None)
    col_ini    = next((c for c in df.columns if "DT_INI_EXERC" in c.upper()), None)

    if not col_conta or not col_valor:
        return df.to_string(index=False, max_rows=50)

    # A chave é o CÓDIGO da conta: contas distintas repetem o mesmo nome (ex:
    # "Empréstimos e Financiamentos" no circulante e no não circulante) e,
    # indexando por nome, uma sobrescreveria a outra.
    col_chave = col_codigo or col_conta

    # No ITR de 2º/3º trimestre, a DRE e a DFC trazem DUAS linhas ÚLTIMO por
    # conta: o ACUMULADO do ano (DT_INI_EXERC = 01/01) e o TRIMESTRE ISOLADO
    # (DT_INI_EXERC = início do trimestre). Sem tratar isso, as duas duplicam e
    # a escolha do valor fica ao acaso da ordem do CSV — podendo até misturar
    # receita acumulada com lucro trimestral. Mantemos sempre o ACUMULADO (a
    # menor DT_INI_EXERC por conta), que é a base da análise fundamentalista e
    # a mesma do valor "anterior". A ordem original das linhas é preservada
    # (não fazemos sort), porque metricas.py rastreia blocos pela ordem. Os
    # balanços não têm DT_INI_EXERC (são posições pontuais) e passam intactos.
    def _manter_acumulado(sub: pd.DataFrame) -> pd.DataFrame:
        if col_ini is None or sub.empty:
            return sub
        ini     = sub[col_ini].astype(str)
        ini_min = ini.groupby(sub[col_chave]).transform("min")
        return sub[ini.eq(ini_min)].drop_duplicates(subset=[col_chave], keep="first")

    if col_ordem:
        # "LTIM" aparece em ÚLTIMO e em PENÚLTIMO; é preciso excluir o segundo
        # explicitamente para não duplicar as linhas no contexto.
        ordem_str   = df[col_ordem].astype(str).str.upper()
        mask_penult = ordem_str.str.contains("PEN.LTIM|PENULT", na=False, regex=True)
        mask_atual  = ordem_str.str.contains("LTIM", na=False) & ~mask_penult
        atual    = _manter_acumulado(df[mask_atual])
        anterior = _manter_acumulado(df[mask_penult])
    else:
        atual    = _manter_acumulado(df)
        anterior = pd.DataFrame()

    map_anterior: dict[str, str] = {}
    if not anterior.empty:
        for _, row in anterior.iterrows():
            map_anterior[str(row[col_chave])] = str(row[col_valor])

    # Cada linha leva o CD_CONTA como prefixo "[1.01.02] ". Sem ele, contas
    # homônimas em níveis diferentes do plano (ex.: "Aplicações Financeiras"
    # 1.01.01.02, filha do caixa, e 1.01.02) ficam indistinguíveis adiante.
    # O prefixo fica FORA do alinhamento de 55 colunas: sem ele, a linha é
    # idêntica à do formato anterior (o chunking depende disso).
    linhas = []
    for _, row in atual.iterrows():
        conta   = str(row[col_conta])
        prefixo = f"[{str(row[col_codigo]).strip()}] " if col_codigo else ""
        valor   = str(row[col_valor])
        var     = map_anterior.get(str(row[col_chave]), "")
        linhas.append(
            f"{prefixo}{conta:<55} {valor:>20}  (anterior: {var})" if var
            else f"{prefixo}{conta:<55} {valor:>20}"
        )
    return "\n".join(linhas)
