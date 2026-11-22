# avaliacao/ragas/construir_dataset.py
#
# Constrói o dataset experimental do RAGAS do TCC 2 (96 casos) conforme
# avaliacao/ragas/PROTOCOLO_RAGAS_TCC2.md, que é a fonte de verdade:
# amostra, códigos CVM, versões, SHA-256 e classificação estimada são lidos
# do próprio protocolo.
#
# Três fontes, mantidas separadas:
#   1. gabarito  — CSVs de dados abertos da CVM (ZIP itr_cia_aberta_2026.zip),
#      por conta (CD_CONTA/DS_CONTA), sem usar calcular_metricas nem qualquer
#      saída do pipeline (protocolo, Seção 13);
#   2. contexto  — o que recuperar_contexto devolve na configuração congelada,
#      reconstruído num ChromaDB temporário (o chroma_db/ do projeto não é
#      tocado) a partir do documento gerado por cvm.baixar_documento;
#   3. disponibilidade — presente/parcial/ausente, derivada SÓ do contexto
#      (Seção 9), comparando linhas do contexto com os valores da CVM.
#
# Não chama LLM, não gera respostas, não roda RAGAS, não altera modulos/.
#
# Uso:
#   python avaliacao/ragas/construir_dataset.py --zip CAMINHO/itr_cia_aberta_2026.zip
#   python avaliacao/ragas/construir_dataset.py --reaplicar-revisao
#       (só reaplica revisao_tecnica_tcc2.json ao dataset existente)

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

PASTA = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(PASTA))
PROTOCOLO = os.path.join(PASTA, "PROTOCOLO_RAGAS_TCC2.md")
SAIDA = os.path.join(PASTA, "dataset_tcc2.json")
REVISAO = os.path.join(PASTA, "revisao_tecnica_tcc2.json")
PERIODO = "2026-06-30"
TIPO_DOC = "ITR"
CATEGORIAS = ("N1", "N2", "N3", "N4", "N5", "E1", "E2", "E3")

# Nome usado nos enunciados (a DENOM_CIA da CVM fica em "empresa").
NOMES = {
    "WEGE3": ("WEG", "da WEG", "a WEG"),
    "BBAS3": ("Banco do Brasil", "do Banco do Brasil", "o Banco do Brasil"),
    "ZAMP3": ("Zamp", "da Zamp", "a Zamp"),
    "LWSA3": ("Locaweb", "da Locaweb", "a Locaweb"),
    "VALE3": ("Vale", "da Vale", "a Vale"),
    "ITUB4": ("Itaú Unibanco", "do Itaú Unibanco", "o Itaú Unibanco"),
    "LAVV3": ("Lavvi", "da Lavvi", "a Lavvi"),
    "POMO4": ("Marcopolo", "da Marcopolo", "a Marcopolo"),
    "ITSA4": ("Itaúsa", "da Itaúsa", "a Itaúsa"),
    "IRBR3": ("IRB Brasil RE", "do IRB Brasil RE", "o IRB Brasil RE"),
    "CEAB3": ("C&A", "da C&A", "a C&A"),
    "AURE3": ("Auren Energia", "da Auren Energia", "a Auren Energia"),
}
ESTRUTURAS = {"não financeira": "nao_financeira", "banco": "banco",
              "holding": "holding", "resseguradora": "resseguradora"}

S26 = "1S26 (01/01/2026 a 30/06/2026)"
S25 = "1S25 (01/01/2025 a 30/06/2025)"
B26 = "30/06/2026"
B25 = "31/12/2025"


def norm(s: str) -> str:
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().strip()


def sha256_arquivo(caminho: str) -> str:
    with open(caminho, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def sha256_texto(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def dec(v) -> Decimal:
    return Decimal(str(v))


def txt(d: Decimal) -> str:
    """Decimal sem expoente e sem zeros à direita."""
    s = format(d.normalize(), "f")
    return s


def fmt_mil(v: Decimal) -> str:
    """19611868 -> '19.611.868' (valor em R$ mil, formato do contexto)."""
    s = f"{abs(v):,.0f}".replace(",", ".")
    return ("-" if v < 0 else "") + s


def fmt_legivel(reais: Decimal) -> str:
    a = abs(reais)
    for lim, nome in ((Decimal("1e12"), "trilhões"), (Decimal("1e9"), "bilhões"),
                      (Decimal("1e6"), "milhões"), (Decimal("1e3"), "mil")):
        if a >= lim:
            v = (a / lim).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"{'-' if reais < 0 else ''}R$ {s} {nome}"
    return f"R$ {reais}"


def fmt_pct(p: Decimal) -> str:
    v = p.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{v}".replace(".", ",") + "%"


# ── Protocolo: fonte de verdade da amostra ────────────────────────────────────

def ler_protocolo() -> dict:
    with open(PROTOCOLO, encoding="utf-8") as f:
        t = f.read()
    amostra = re.findall(
        r"^\| (\d+) \| ([A-Z]{4}\d{1,2}) \| (.+?) \| (\d+) \| (não financeira|banco|holding|resseguradora) \|$",
        t, re.M)
    shas = dict(re.findall(r"^\| ([A-Z]{4}\d{1,2}) \| \d+ \| `([0-9a-f]{64})` \|$", t, re.M))
    versoes = {tk: int(v) for tk, v in re.findall(r"^\| ([A-Z]{4}\d{1,2}) \| (\d+) \| `[0-9a-f]{64}` \|$", t, re.M)}
    estimada = {}
    for linha in re.findall(r"^\| ([A-Z]{4}\d{1,2}) \|((?: (?:P|Pa|A) \|){8})", t, re.M):
        cls = [c.strip() for c in linha[1].strip("|").split("|")]
        estimada[linha[0]] = dict(zip(CATEGORIAS, [{"P": "presente", "Pa": "parcial", "A": "ausente"}[c] for c in cls]))
    empresas = []
    for _, tk, denom, cod, est in amostra:
        empresas.append({"ticker": tk, "codigo_cvm": cod, "denom_protocolo": denom,
                         "estrutura": ESTRUTURAS[est], "versao": versoes[tk], "sha256_documento": shas[tk]})
    if len(empresas) != 12 or len(shas) != 12 or len(estimada) != 12:
        sys.exit("Protocolo: não foi possível ler as 12 empresas, hashes e classificação estimada.")
    return {"empresas": empresas, "estimada": estimada, "sha256_protocolo": sha256_arquivo(PROTOCOLO)}


# ── CVM: dados estruturados ───────────────────────────────────────────────────

class FonteCVM:
    """Leitura direta dos CSVs do ZIP de dados abertos (independente do pipeline)."""
    ARQ = {"DRE": "itr_cia_aberta_DRE_con_2026.csv", "BPA": "itr_cia_aberta_BPA_con_2026.csv",
           "BPP": "itr_cia_aberta_BPP_con_2026.csv"}

    def __init__(self, zip_bytes: bytes):
        z = zipfile.ZipFile(io.BytesIO(zip_bytes))
        idx = pd.read_csv(z.open("itr_cia_aberta_2026.csv"), sep=";", encoding="latin-1", dtype=str)
        self.indice = idx[(idx.DT_REFER == PERIODO) & (idx.CATEG_DOC == TIPO_DOC)]
        self.df = {}
        for demo, arq in self.ARQ.items():
            d = pd.read_csv(z.open(arq), sep=";", encoding="latin-1", dtype=str)
            self.df[demo] = d[d.DT_REFER == PERIODO]

    def versao_mais_recente(self, cod: str) -> int:
        r = self.indice[self.indice.CD_CVM.str.lstrip("0") == cod]
        return int(r.VERSAO.astype(int).max())

    def empresa(self, cod: str, versao: int) -> "ContasEmpresa":
        return ContasEmpresa({k: d[(d.CD_CVM.str.lstrip("0") == cod) & (d.VERSAO == str(versao))]
                              for k, d in self.df.items()}, self.ARQ)


class ContasEmpresa:
    def __init__(self, dfs: dict, arquivos: dict):
        self.dfs, self.arquivos = dfs, arquivos

    def _ultimo(self, demo):
        d = self.dfs[demo]
        return d[d.ORDEM_EXERC.map(norm) == "ultimo"]

    def achar(self, demo: str, nomes, pontos: int, prefixo: str = "") -> str:
        """CD_CONTA da conta com DS_CONTA em `nomes`, no nível dado (nº de pontos)."""
        alvo = {norm(n) for n in nomes}
        d = self._ultimo(demo)
        d = d[d.DS_CONTA.map(norm).isin(alvo) & (d.CD_CONTA.str.count(r"\.") == pontos)
              & d.CD_CONTA.str.startswith(prefixo)]
        cods = sorted(set(d.CD_CONTA))
        if len(cods) != 1:
            raise ValueError(f"{demo}: conta {nomes} (nível {pontos}, prefixo '{prefixo}') -> {cods}")
        return cods[0]

    def filhas(self, demo: str, pai: str, prefixo_nome: str) -> list[str]:
        d = self._ultimo(demo)
        d = d[d.CD_CONTA.str.startswith(pai + ".") & (d.CD_CONTA.str.count(r"\.") == pai.count(".") + 1)
              & d.DS_CONTA.map(norm).str.startswith(norm(prefixo_nome))]
        return sorted(set(d.CD_CONTA))

    def fonte(self, demo: str, cd: str, anterior: bool = False) -> dict:
        """Uma linha da CVM, com o período exato (acumulado do ano na DRE)."""
        d = self.dfs[demo]
        ordem = d.ORDEM_EXERC.map(norm)
        d = d[(d.CD_CONTA == cd) & (ordem == ("penultimo" if anterior else "ultimo"))]
        if demo == "DRE":
            ini, fim = ("2025-01-01", "2025-06-30") if anterior else ("2026-01-01", "2026-06-30")
            d = d[(d.DT_INI_EXERC == ini) & (d.DT_FIM_EXERC == fim)]
            rotulo = S25 if anterior else S26
        else:
            fim = "2025-12-31" if anterior else "2026-06-30"
            d = d[d.DT_FIM_EXERC == fim]
            rotulo = B25 if anterior else B26
        if len(d) != 1:
            raise ValueError(f"{demo} {cd} anterior={anterior}: {len(d)} linhas")
        r = d.iloc[0]
        return {
            "demonstracao": {"DRE": "Demonstração de Resultado", "BPA": "Balanço Patrimonial — Ativo",
                             "BPP": "Balanço Patrimonial — Passivo"}[demo],
            "arquivo_cvm": self.arquivos[demo], "base": "Consolidado",
            "cd_conta": cd, "ds_conta": r.DS_CONTA, "periodo": rotulo,
            "ordem_exerc": r.ORDEM_EXERC,
            "dt_ini_exerc": r.DT_INI_EXERC if demo == "DRE" else None, "dt_fim_exerc": r.DT_FIM_EXERC,
            "vl_conta_cvm": r.VL_CONTA, "moeda": r.MOEDA, "escala_moeda": r.ESCALA_MOEDA,
            "unidade": "R$ mil",
        }


def valor_mil(f: dict) -> Decimal:
    if f["escala_moeda"] != "MIL" or f["moeda"] != "REAL":
        raise ValueError(f"Escala/moeda inesperada: {f['escala_moeda']} {f['moeda']}")
    return dec(f["vl_conta_cvm"])


# ── Documento e contexto (configuração congelada) ─────────────────────────────

def reconstruir_contexto(emp: dict, zip_bytes: bytes, tmp: str, cache: dict | None) -> dict:
    """Gera o documento, confere o SHA-256 e reconstrói o contexto numérico."""
    sys.path.insert(0, RAIZ)
    from modulos import cvm

    class _Resp:
        content = zip_bytes
        def raise_for_status(self): pass
    cvm.requests.get = lambda url, timeout=None: _Resp()   # só neste processo: ZIP local
    destino = os.path.join(tmp, f"{emp['ticker']}_{TIPO_DOC}_{PERIODO}.txt")
    cvm.baixar_documento("", destino, codigo_cvm=emp["codigo_cvm"], tipo=TIPO_DOC,
                         periodo=PERIODO, versao=str(emp["versao"]))
    sha = sha256_arquivo(destino)
    if sha != emp["sha256_documento"]:
        sys.exit(f"PARADA: SHA-256 de {emp['ticker']} diverge do protocolo ({sha}).")

    if cache and cache.get(emp["ticker"], {}).get("sha256_documento") == sha:
        ctx_num, de_cache = cache[emp["ticker"]]["ctx_num"], True
    else:
        from modulos import chunking, recuperacao
        from modulos.extracao import extrair_documento
        chroma = os.path.join(tmp, "chroma")
        chunking.CAMINHO_CHROMA = chroma          # índice temporário, fora do projeto
        recuperacao.CAMINHO_CHROMA = chroma
        chunks = chunking.criar_chunks(extrair_documento(destino))
        chunking.indexar_documento(emp["ticker"], chunks, TIPO_DOC, PERIODO, forcar=True)
        ctx_num, _ = recuperacao.recuperar_contexto(emp["ticker"], TIPO_DOC, PERIODO)
        de_cache = False
    sys.path.insert(0, os.path.join(RAIZ, "avaliacao"))
    from coletar_respostas import extrair_chunks          # separação do TCC 1
    trechos = extrair_chunks(ctx_num)
    titulos = [t.split("\n", 1)[0] for t in trechos]
    return {"sha256_documento": sha, "ctx_num": ctx_num, "trechos": trechos,
            "registro": {"tabelas_recuperadas": titulos, "n_trechos": len(trechos),
                         "caracteres_ctx_num": len(ctx_num), "sha256_ctx_num": sha256_texto(ctx_num),
                         "sha256_trechos": [sha256_texto(t) for t in trechos],
                         "reconstruido_de_cache": de_cache}}


_RE_LINHA = re.compile(r"^(?P<conta>.*?)\s+(?P<atual>-?[\d.,]+)(?:\s+\(anterior:\s*(?P<ant>-?[\d.,]+)\))?\s*$")
_TABELAS = {"demonstracao de resultado": "DRE", "balanco patrimonial — ativo": "BPA",
            "balanco patrimonial — passivo": "BPP", "demonstracao de fluxo de caixa": "DFC"}


def _num_ctx(s: str) -> Decimal:
    if re.fullmatch(r"-?\d+\.\d{10}", s):
        return dec(s)
    return dec(s.replace(".", "").replace(",", "."))


def linhas_contexto(trechos: list[str]) -> list[dict]:
    linhas = []
    for t in trechos:
        cab, *corpo = t.split("\n")
        titulo = norm(cab.strip("[]").split("|", 1)[1]).split(" (")[0]
        tab = next(v for k, v in _TABELAS.items() if titulo.startswith(norm(k)))
        for l in corpo:
            m = _RE_LINHA.match(l.strip())
            if m:
                linhas.append({"tabela": tab, "conta": m.group("conta").strip(),
                               "atual": _num_ctx(m.group("atual")),
                               "anterior": _num_ctx(m.group("ant")) if m.group("ant") else None,
                               "texto": l.strip()})
    return linhas


def _familia(nome: str, fam: str) -> bool:
    n = norm(nome)
    return {
        "resultado": bool(re.search(r"lucro|resultado|prejuizo", n)) and ("periodo" in n or "liquido" in n)
                     and not any(x in n for x in ("antes", "financeiro", "equivalencia", "operac")),
        "lair": "antes" in n and any(x in n for x in ("imposto", "tribut")) and "financeiro" not in n,
        "rf": "resultado financeiro" in n,
        "ir": any(x in n for x in ("imposto de renda", "impostos sobre o lucro", "tributos sobre o lucro"))
              and not any(x in n for x in ("pago", "recolher", "recuperar", "antes")),
        "ebit": "antes do resultado financeiro" in n,
        "desc": "descontinuad" in n,
    }.get(fam, False)


class Contexto:
    def __init__(self, trechos):
        self.linhas = linhas_contexto(trechos)
        self.tabelas = {l["tabela"] for l in self.linhas}

    def propria(self, demo: str, ds: str, atual: Decimal, anterior: Decimal | None = None):
        for l in self.linhas:
            if l["tabela"] == demo and norm(l["conta"]) == norm(ds) and l["atual"] == atual \
                    and (anterior is None or l["anterior"] == anterior):
                return l
        return None

    def em_outra_tabela(self, fam: str, atual: Decimal, anterior: Decimal | None, exceto=("DRE",)):
        """Linha de outra demonstração com o mesmo conceito e mesmo valor (mesmo sinal ou invertido)."""
        for l in self.linhas:
            if l["tabela"] in exceto or not _familia(l["conta"], fam):
                continue
            if norm(l["conta"]).startswith("lucros/prejuizos acumulados"):
                continue                                   # regra 3 da Seção 9
            for sinal, rotulo in ((1, "mesmo_sinal"), (-1, "sinal_invertido")):
                if l["atual"] == sinal * atual and (anterior is None or l["anterior"] == sinal * anterior):
                    return l, rotulo
        return None, None


def _j(l: dict | None, rotulo: str = "") -> str:
    return f"[{l['tabela']}] {l['texto']}" + (f" ({rotulo})" if rotulo else "") if l else ""


# ── Construção dos casos ──────────────────────────────────────────────────────

def item(ident, conceito, tipo, valor, fontes, sinal_exigido, periodo, formula=None,
         valor_origem=None, formas_alternativas=None):
    """Valor objetivo esperado, pronto para exatidao.classificar (sem LLM)."""
    d = {"id": ident, "conceito": conceito, "tipo": tipo, "periodo": periodo,
         "valor": txt(valor), "sinal_exigido": sinal_exigido,
         "sinal_esperado": "-" if valor < 0 else "+",
         "fontes": fontes, "formula": formula, "formas_alternativas": formas_alternativas or []}
    if tipo == "monetario":
        d.update({"valor_origem": txt(valor_origem), "unidade_origem": "R$ mil", "escala": "MIL",
                  "unidade_valor": "R$", "apresentacao_referencia": fmt_legivel(valor)})
    else:
        d.update({"unidade_valor": "%", "apresentacao_referencia": fmt_pct(valor)})
    return d


def monet(ident, conceito, fonte, sinal_exigido, formula=None):
    v = valor_mil(fonte)
    return item(ident, conceito, "monetario", v * 1000, [fonte["cd_conta"]], sinal_exigido,
                fonte["periodo"], formula, valor_origem=v)


def construir_empresa(emp: dict, contas: ContasEmpresa, ctx: Contexto) -> list[dict]:
    tk, est = emp["ticker"], emp["estrutura"]
    nome, de, art = NOMES[tk]
    F = contas.fonte
    fontes_usadas = {}

    def fo(demo, cd, ant=False):
        f = F(demo, cd, ant)
        fontes_usadas[(demo, cd, ant)] = f
        return f

    # contas por plano de contas (nunca por ticker)
    if est in ("nao_financeira", "holding"):
        c_receita = contas.achar("DRE", ["Receita de Venda de Bens e/ou Serviços"], 1)
        c_res = contas.achar("DRE", ["Lucro/Prejuízo Consolidado do Período"], 1)
        c_ebit = contas.achar("DRE", ["Resultado Antes do Resultado Financeiro e dos Tributos"], 1)
        c_rf = contas.achar("DRE", ["Resultado Financeiro"], 1)
        c_lair = contas.achar("DRE", ["Resultado Antes dos Tributos sobre o Lucro"], 1)
        c_ir = contas.achar("DRE", ["Imposto de Renda e Contribuição Social sobre o Lucro"], 1)
        c_desc = contas.achar("DRE", ["Resultado Líquido de Operações Descontinuadas"], 1)
        c_caixa = contas.achar("BPA", ["Caixa e Equivalentes de Caixa"], 2, "1.01")
        c_emp_c = contas.achar("BPP", ["Empréstimos e Financiamentos"], 2, "2.01")
        c_emp_nc = contas.achar("BPP", ["Empréstimos e Financiamentos"], 2, "2.02")
        componentes = [("ebit", c_ebit, "resultado antes do resultado financeiro e dos tributos"),
                       ("rf", c_rf, "resultado financeiro"), ("ir", c_ir, "IR/CS"),
                       ("desc", c_desc, "operações descontinuadas")]
        nos_n4 = [("ebit", c_ebit), ("rf", c_rf), ("lair", c_lair), ("ir", c_ir), ("desc", c_desc), ("resultado", c_res)]
    elif est == "banco":
        c_receita = contas.achar("DRE", ["Receitas de Intermediação Financeira", "Receitas da Intermediação Financeira"], 1)
        c_res = contas.achar("DRE", ["Lucro/Prejuízo Consolidado do Período", "Lucro ou Prejuízo Líquido Consolidado do Período"], 1)
        c_desp = contas.achar("DRE", ["Despesas de Intermediação Financeira", "Despesas da Intermediação Financeira"], 1)
        c_bruto = contas.achar("DRE", ["Resultado Bruto de Intermediação Financeira", "Resultado Bruto Intermediação Financeira"], 1)
        c_outras = contas.achar("DRE", ["Outras Despesas e Receitas Operacionais", "Outras Despesas/Receitas Operacionais"], 1)
        c_lair = contas.achar("DRE", ["Resultado Antes dos Tributos sobre o Lucro"], 1)
        c_ir = contas.achar("DRE", ["Imposto de Renda e Contribuição Social sobre o Lucro"], 1)
        c_desc = contas.achar("DRE", ["Resultado Líquido das Operações Descontinuadas", "Resultado Líquido de Operações Descontinuadas"], 1)
        c_caixa = contas.achar("BPA", ["Caixa e Equivalentes de Caixa"], 1, "1.01")
        c_dep = contas.achar("BPP", ["Depósitos"], 2)
        componentes = [("bruto_intermediacao", c_bruto, "resultado bruto da intermediação financeira"),
                       ("outras_operacionais", c_outras, "outras despesas e receitas operacionais"),
                       ("ir", c_ir, "IR/CS"), ("desc", c_desc, "operações descontinuadas")]
        try:
            c_part = contas.achar("DRE", ["Participações nos Lucros e Contribuições Estatutárias"], 1)
            componentes.append(("participacoes", c_part, "participações nos lucros e contribuições estatutárias"))
        except ValueError:
            pass
        nos_n4 = [(k, c) for k, c, _ in componentes[:2]] + [("lair", c_lair), ("ir", c_ir), ("desc", c_desc)] + \
                 [(k, c) for k, c, _ in componentes[4:]] + [("resultado", c_res)]
    else:  # resseguradora
        c_receita = contas.achar("DRE", ["Receitas das Atividades Seguradoras/Resseguradoras"], 1)
        c_res = contas.achar("DRE", ["Lucro/Prejuízo Consolidado do Período"], 1)
        c_bruto = contas.achar("DRE", ["Resultado Bruto"], 1)
        c_adm = contas.achar("DRE", ["Despesas Administrativas"], 1)
        c_outras = contas.achar("DRE", ["Outras Receitas e Despesas Operacionais"], 1)
        c_eq = contas.achar("DRE", ["Resultado de Equivalência Patrimonial"], 1)
        c_ebit = contas.achar("DRE", ["Resultado Antes do Resultado Financeiro e dos Tributos"], 1)
        c_rf = contas.achar("DRE", ["Resultado Financeiro"], 1)
        c_lair = contas.achar("DRE", ["Resultado Antes dos Tributos sobre o Lucro"], 1)
        c_ir = contas.achar("DRE", ["Imposto de Renda e Contribuição Social sobre o Lucro"], 1)
        c_desc = contas.achar("DRE", ["Resultado Líquido de Operações Descontinuadas"], 1)
        c_caixa = contas.achar("BPA", ["Caixa e Equivalentes de Caixa"], 2, "1.01")
        c_apl_c = contas.achar("BPA", ["Aplicações Financeiras"], 2, "1.01")
        c_rlp = contas.achar("BPA", ["Ativo Realizável a Longo Prazo"], 2, "1.02")
        c_apl_lp = contas.filhas("BPA", c_rlp, "Aplicações Financeiras")
        componentes = [("resultado_bruto", c_bruto, "resultado bruto das operações de resseguro"),
                       ("administrativas_e_outras", [c_adm, c_outras, c_eq], "despesas administrativas e outras"),
                       ("rf", c_rf, "resultado financeiro"), ("ir", c_ir, "IR/CS"),
                       ("desc", c_desc, "operações descontinuadas")]
        nos_n4 = [("resultado_bruto", c_bruto), ("ebit", c_ebit), ("rf", c_rf), ("lair", c_lair),
                  ("ir", c_ir), ("desc", c_desc), ("resultado", c_res)]

    def vm(demo, cd, ant=False):
        return valor_mil(fo(demo, cd, ant))

    def soma(demo, cds, ant=False):
        cds = cds if isinstance(cds, list) else [cds]
        return sum((vm(demo, c, ant) for c in cds), Decimal(0))

    # fechamento aritmético da DRE (o gabarito de N4 depende dele)
    for ant in (False, True):
        total = sum((soma("DRE", c, ant) for _, c, _ in componentes), Decimal(0))
        if total != vm("DRE", c_res, ant):
            raise ValueError(f"{tk}: componentes não fecham o resultado (anterior={ant}): {total} x {vm('DRE', c_res, ant)}")

    res_a, res_b = vm("DRE", c_res), vm("DRE", c_res, True)
    f_res_a, f_res_b = fo("DRE", c_res), fo("DRE", c_res, True)
    casos = []

    def caso(cat, tipo, pergunta, valores, gabarito, fontes, disp, just, extra=None):
        c = {"id": f"{tk}_{cat}", "ticker": tk, "codigo_cvm": emp["codigo_cvm"], "empresa": emp["denom_cvm"],
             "nome_na_pergunta": nome, "estrutura": est, "categoria": cat, "tipo_pergunta": tipo,
             "pergunta": pergunta, "documento": TIPO_DOC, "periodo": PERIODO, "versao": emp["versao"],
             "sha256_documento": emp["sha256_documento"],
             "disponibilidade": disp,
             "disponibilidade_estimada_protocolo": emp["estimada"][cat],
             "justificativa_disponibilidade": just,
             "gabarito": gabarito, "fontes_gabarito": fontes, "valores_esperados": valores,
             "verificacao_deterministica_aplicavel": cat != "N4"}
        if extra:
            c.update(extra)
        casos.append(c)

    def fontes_de(*chaves):
        return [fontes_usadas[k] for k in chaves]

    # ── N1 — linha de topo
    f = fo("DRE", c_receita)
    rotulo_topo = f["ds_conta"]
    perg = {
        "nao_financeira": f"Qual foi a receita de venda de bens e/ou serviços consolidada {de} no primeiro semestre de 2026?",
        "holding": f"Qual foi a receita de venda de bens e/ou serviços consolidada {de} no primeiro semestre de 2026?",
        "banco": f"Qual foi o total das receitas de intermediação financeira consolidadas {de} no primeiro semestre de 2026?",
        "resseguradora": f"Qual foi o total das receitas das atividades seguradoras e resseguradoras consolidadas {de} no primeiro semestre de 2026?",
    }[est]
    v = monet("topo_1s26", rotulo_topo, f, False)
    l = ctx.propria("DRE", f["ds_conta"], valor_mil(f))
    disp, just = ("presente", _j(l)) if l else ("ausente", "A DRE não está no contexto; nenhuma outra tabela recuperada traz a linha de topo.")
    caso("N1", "factual", perg, [v],
         f"{rotulo_topo} consolidada do 1S26: R$ {fmt_mil(valor_mil(f))} mil ({v['apresentacao_referencia']}).",
         fontes_de(("DRE", c_receita, False)), disp, just)

    # ── N2 / N3 — resultado consolidado
    def disp_resultado(com_anterior: bool):
        l = ctx.propria("DRE", f_res_a["ds_conta"], res_a, res_b if com_anterior else None)
        if l:
            return "presente", _j(l)
        l, s = ctx.em_outra_tabela("resultado", res_a, res_b if com_anterior else None)
        if l and s == "mesmo_sinal":
            return "presente", _j(l, "DFC: resultado do período igual ao consolidado da DRE — regra 2 da Seção 9")
        lair_a, lair_b = vm("DRE", c_lair), vm("DRE", c_lair, True)
        l2, s2 = ctx.em_outra_tabela("lair", lair_a, lair_b if com_anterior else None)
        if l2:
            return "parcial", _j(l2, "só o resultado antes dos tributos (conceito vizinho); o resultado consolidado não está no contexto")
        return "ausente", "Nenhuma linha do contexto traz o resultado consolidado ou conceito vizinho."

    sinal_res = "lucro" if res_a >= 0 else "prejuízo"
    v2 = monet("resultado_1s26", f_res_a["ds_conta"], f_res_a, True)
    d, j = disp_resultado(False)
    caso("N2", "factual",
         f"Qual foi o resultado líquido consolidado (lucro ou prejuízo) {de} no primeiro semestre de 2026? "
         f"Considere o resultado consolidado total do período, e não apenas a parcela atribuída aos controladores.",
         [v2], f"{sinal_res.capitalize()} consolidado do 1S26: R$ {fmt_mil(res_a)} mil ({v2['apresentacao_referencia']}).",
         fontes_de(("DRE", c_res, False)), d, j)

    va = monet("resultado_1s26", f_res_a["ds_conta"], f_res_a, True)
    vb = monet("resultado_1s25", f_res_b["ds_conta"], f_res_b, True)
    valores = [va, vb]
    pct_aplicavel = (res_a >= 0) == (res_b >= 0) and res_b != 0
    if pct_aplicavel:
        if res_a < 0:
            pct = (abs(res_a) - abs(res_b)) / abs(res_b) * 100
            formula = "(|resultado 1S26| - |resultado 1S25|) / |resultado 1S25| × 100 (variação sobre a magnitude do prejuízo)"
        else:
            pct = (res_a - res_b) / res_b * 100
            formula = "(resultado 1S26 - resultado 1S25) / resultado 1S25 × 100"
        valores.append(item("variacao_percentual", "variação percentual do resultado consolidado", "percentual",
                            pct, [c_res], False, "1S26 vs 1S25", formula))
    direcao = ("aumento" if res_a > res_b else "redução") if res_a >= 0 else \
        ("prejuízo maior" if abs(res_a) > abs(res_b) else "prejuízo menor")
    d, j = disp_resultado(True)
    caso("N3", "comparativa",
         f"Como variou o resultado líquido consolidado (lucro ou prejuízo) {de} no primeiro semestre de 2026 "
         f"em relação ao primeiro semestre de 2025? Informe o valor de cada período"
         + (" e a variação percentual." if pct_aplicavel else "."),
         valores,
         f"1S26: R$ {fmt_mil(res_a)} mil; 1S25: R$ {fmt_mil(res_b)} mil; {direcao}"
         + (f", variação de {fmt_pct(dec(valores[2]['valor']))}." if pct_aplicavel else "."),
         fontes_de(("DRE", c_res, False), ("DRE", c_res, True)), d, j,
         {"regra_percentual_n3": "aplicável: mesmo sinal nos dois períodos e anterior diferente de zero"
          if pct_aplicavel else "não aplicável: mudança de sinal ou anterior igual a zero"})

    # ── N4 — componentes da variação (sem valores exigidos para a exatidão)
    cadeia = []
    for chave, cd, rot in componentes:
        a, b = soma("DRE", cd), soma("DRE", cd, True)
        if a == 0 and b == 0 and chave in ("desc", "participacoes"):
            continue
        cds = cd if isinstance(cd, list) else [cd]
        cadeia.append({"componente": chave, "descricao": rot, "cd_contas": cds,
                       "valor_1s26_mil": txt(a), "valor_1s25_mil": txt(b), "variacao_mil": txt(a - b)})
    ordenados = sorted(cadeia, key=lambda x: -abs(dec(x["variacao_mil"])))
    contas_cadeia = {cd for _, cds, _ in componentes for cd in (cds if isinstance(cds, list) else [cds])}
    nos = []
    for chave, cd in nos_n4:
        a, b = vm("DRE", cd), vm("DRE", cd, True)
        if chave == "desc" and a == 0 and b == 0:
            continue
        contas_cadeia.add(cd)
        fo("DRE", cd, True)
        nos.append({"no": chave, "cd_conta": cd, "ds_conta": fo("DRE", cd)["ds_conta"],
                    "valor_1s26_mil": txt(a), "valor_1s25_mil": txt(b)})
    if "DRE" in ctx.tabelas:
        d, j = "presente", "A DRE consolidada está no contexto (regra 5 da Seção 9)."
    else:
        achados = []
        for no in nos:
            l, s = ctx.em_outra_tabela(no["no"], dec(no["valor_1s26_mil"]), dec(no["valor_1s25_mil"]))
            if l:
                achados.append(f"{no['no']}: " + _j(l, s))
        d = "parcial" if len(achados) >= 2 else "ausente"
        j = (f"DRE fora do contexto; {len(achados)} nó(s) da cadeia em outra tabela: " + "; ".join(achados)) if achados \
            else "DRE fora do contexto; nenhum nó da cadeia em outra tabela."
    texto_n4 = "; ".join(f"{c['descricao']}: {fmt_mil(dec(c['valor_1s25_mil']))} → {fmt_mil(dec(c['valor_1s26_mil']))} "
                         f"(Δ {fmt_mil(dec(c['variacao_mil']))})" for c in ordenados)
    caso("N4", "interpretativa",
         f"Quais componentes da demonstração de resultado explicam a variação do resultado líquido consolidado {de} "
         f"entre o primeiro semestre de 2025 e o primeiro semestre de 2026?",
         [], f"Variação do resultado consolidado: {fmt_mil(res_b)} → {fmt_mil(res_a)} (Δ {fmt_mil(res_a - res_b)}), "
             f"em R$ mil. Componentes por magnitude da variação: {texto_n4}.",
         [fontes_usadas[k] for k in sorted(fontes_usadas)
          if k[0] == "DRE" and k[1] in contas_cadeia], d, j,
         {"cadeia_n4": {"estrutura_da_cadeia": est, "nos": nos, "componentes_por_magnitude": ordenados,
                        "variacao_resultado_mil": txt(res_a - res_b),
                        "fechamento": "soma das variações dos componentes = variação do resultado consolidado"},
          "motivo_nao_aplicavel_exatidao": "N4 é NAO_APLICAVEL por definição (Seção 11.1); continua nos 96 casos e no RAGAS."})

    # ── N5 — caixa e equivalentes
    f = fo("BPA", c_caixa)
    v = monet("caixa_30jun26", f["ds_conta"], f, False)
    l = ctx.propria("BPA", f["ds_conta"], valor_mil(f))
    caso("N5", "factual", f"Qual era o saldo de caixa e equivalentes de caixa consolidado {de} em 30 de junho de 2026?",
         [v], f"Caixa e equivalentes de caixa em 30/06/2026: R$ {fmt_mil(valor_mil(f))} mil ({v['apresentacao_referencia']}).",
         fontes_de(("BPA", c_caixa, False)), "presente" if l else "ausente",
         _j(l) if l else "Linha de caixa e equivalentes não encontrada no contexto.")

    # ── E1 / E2 / E3
    if est in ("nao_financeira", "holding"):
        if est == "nao_financeira":
            rec = vm("DRE", c_receita)
            margem = res_a / rec * 100
            v = item("margem_liquida_1s26", "margem líquida consolidada", "percentual", margem, [c_res, c_receita], False,
                     S26, "resultado consolidado 1S26 / receita de venda de bens e/ou serviços 1S26 × 100")
            l_rec = ctx.propria("DRE", fo("DRE", c_receita)["ds_conta"], rec)
            l_res = ctx.propria("DRE", f_res_a["ds_conta"], res_a)
            if not l_res:
                l_res, s = ctx.em_outra_tabela("resultado", res_a, None)
                l_res = l_res if s == "mesmo_sinal" else None
            n = sum(x is not None for x in (l_rec, l_res))
            d = {2: "presente", 1: "parcial", 0: "ausente"}[n]
            j = f"Insumos no contexto ({n}/2): receita: {_j(l_rec) or 'ausente'}; resultado consolidado: {_j(l_res) or 'ausente'}."
            caso("E1", "derivada",
                 f"Qual foi a margem líquida consolidada {de} no primeiro semestre de 2026, calculada como o resultado "
                 f"líquido consolidado dividido pela receita de venda de bens e/ou serviços?",
                 [v], f"Margem líquida do 1S26: {fmt_pct(margem)} = {fmt_mil(res_a)} / {fmt_mil(rec)} (R$ mil).",
                 fontes_de(("DRE", c_res, False), ("DRE", c_receita, False)), d, j)
        else:
            c_eqp = contas.achar("DRE", ["Resultado de Equivalência Patrimonial"], 2, "3.04")
            f = fo("DRE", c_eqp)
            v = monet("equivalencia_1s26", f["ds_conta"], f, False)
            l = ctx.propria("DRE", f["ds_conta"], valor_mil(f))
            caso("E1", "factual", f"Qual foi o resultado de equivalência patrimonial consolidado {de} no primeiro semestre de 2026?",
                 [v], f"Resultado de equivalência patrimonial do 1S26: R$ {fmt_mil(valor_mil(f))} mil ({v['apresentacao_referencia']}).",
                 fontes_de(("DRE", c_eqp, False)), "presente" if l else "ausente", _j(l) or "Linha não encontrada no contexto.")
        # E2 — caixa × empréstimos
        fc, f1, f2 = fo("BPA", c_caixa), fo("BPP", c_emp_c), fo("BPP", c_emp_nc)
        cx, e1v, e2v = valor_mil(fc), valor_mil(f1), valor_mil(f2)
        v_cx = monet("caixa_30jun26", fc["ds_conta"], fc, False)
        p1 = monet("emprestimos_circulante_30jun26", "Empréstimos e Financiamentos (circulante)", f1, False)
        p2 = monet("emprestimos_nao_circulante_30jun26", "Empréstimos e Financiamentos (não circulante)", f2, False)
        v_div = item("emprestimos_total_30jun26", "Empréstimos e Financiamentos (circulante + não circulante)", "monetario",
                     (e1v + e2v) * 1000, [c_emp_c, c_emp_nc], False, B26,
                     f"{c_emp_c} + {c_emp_nc}", valor_origem=e1v + e2v, formas_alternativas=[{"parcelas": [p1, p2]}])
        ins = [("caixa", ctx.propria("BPA", fc["ds_conta"], cx)),
               ("empréstimos circulante", ctx.propria("BPP", f1["ds_conta"], e1v)),
               ("empréstimos não circulante", ctx.propria("BPP", f2["ds_conta"], e2v))]
        n = sum(l is not None for _, l in ins)
        d = "presente" if n == 3 else ("parcial" if n else "ausente")
        j = f"Insumos no contexto ({n}/3): " + "; ".join(f"{k}: {_j(l) or 'ausente'}" for k, l in ins) +             ("" if n == 3 else ". O BP Passivo, que traz os empréstimos, não está entre as tabelas recuperadas.")
        mais = "mais caixa" if cx > e1v + e2v else "mais empréstimos e financiamentos"
        caso("E2", "derivada",
             f"Em 30 de junho de 2026, {art} tinha mais caixa e equivalentes de caixa ou mais empréstimos e financiamentos "
             f"(circulante e não circulante somados)? Informe o saldo de caixa e equivalentes e o total de empréstimos e financiamentos.",
             [v_cx, v_div],
             f"Em 30/06/2026: caixa e equivalentes R$ {fmt_mil(cx)} mil; empréstimos e financiamentos R$ {fmt_mil(e1v + e2v)} mil "
             f"(circulante {fmt_mil(e1v)} + não circulante {fmt_mil(e2v)}); {mais}.",
             fontes_de(("BPA", c_caixa, False), ("BPP", c_emp_c, False), ("BPP", c_emp_nc, False)), d, j)
        # E3 — resultado financeiro
        fa, fb = fo("DRE", c_rf), fo("DRE", c_rf, True)
        rfa, rfb = valor_mil(fa), valor_mil(fb)
        l = ctx.propria("DRE", fa["ds_conta"], rfa, rfb)
        if l:
            d, j = "presente", _j(l)
        else:
            l, s = ctx.em_outra_tabela("rf", rfa, rfb)
            if l and s == "sinal_invertido":
                d, j = "parcial", _j(l, "linha da DFC com sinal invertido — regra 6 da Seção 9")
            elif l:
                d, j = "presente", _j(l, "linha do conceito fora da DRE, mesmo sinal")
            else:
                d, j = "ausente", "Nenhuma linha de resultado financeiro no contexto."
        caso("E3", "comparativa",
             f"Qual foi o resultado financeiro consolidado {de} no primeiro semestre de 2026 e como ele se compara ao do "
             f"primeiro semestre de 2025? Informe o valor de cada período.",
             [monet("resultado_financeiro_1s26", fa["ds_conta"], fa, True),
              monet("resultado_financeiro_1s25", fb["ds_conta"], fb, True)],
             f"Resultado financeiro: 1S26 R$ {fmt_mil(rfa)} mil; 1S25 R$ {fmt_mil(rfb)} mil.",
             fontes_de(("DRE", c_rf, False), ("DRE", c_rf, True)), d, j)

    elif est == "banco":
        for cat, cd, demo, perg, ident, rot in (
            ("E1", c_bruto, "DRE", f"Qual foi o resultado bruto da intermediação financeira consolidado {de} no primeiro semestre de 2026?",
             "resultado_bruto_intermediacao_1s26", "Resultado bruto da intermediação financeira do 1S26"),
            ("E2", c_dep, "BPP", f"Qual era o saldo de depósitos consolidado {de} em 30 de junho de 2026?",
             "depositos_30jun26", "Depósitos em 30/06/2026"),
            ("E3", c_desp, "DRE", f"Qual foi o total das despesas de intermediação financeira consolidadas {de} no primeiro semestre de 2026?",
             "despesas_intermediacao_1s26", "Despesas de intermediação financeira do 1S26"),
        ):
            f = fo(demo, cd)
            v = monet(ident, f["ds_conta"], f, False)
            l = ctx.propria(demo, f["ds_conta"], valor_mil(f))
            extra = {"nota_comparabilidade": "E3 não é comparável entre BBAS3 e ITUB4 (classificação da provisão para perda de crédito; Seção 8)."} if cat == "E3" else None
            caso(cat, "factual", perg, [v], f"{rot}: R$ {fmt_mil(valor_mil(f))} mil ({v['apresentacao_referencia']}).",
                 fontes_de((demo, cd, False)), "presente" if l else "ausente", _j(l) or "Linha não encontrada no contexto.", extra)

    else:  # resseguradora
        f = fo("DRE", c_bruto)
        v = monet("resultado_bruto_resseguro_1s26", f["ds_conta"], f, True)
        l = ctx.propria("DRE", f["ds_conta"], valor_mil(f))
        caso("E1", "factual", f"Qual foi o resultado bruto das operações de resseguro consolidado {de} no primeiro semestre de 2026?",
             [v], f"Resultado bruto (receitas menos despesas da atividade de resseguro) do 1S26: R$ {fmt_mil(valor_mil(f))} mil ({v['apresentacao_referencia']}).",
             fontes_de(("DRE", c_bruto, False)), "presente" if l else "ausente", _j(l) or "Linha não encontrada no contexto.")
        f = fo("DRE", c_rf)
        v = monet("resultado_financeiro_1s26", f["ds_conta"], f, True)
        l = ctx.propria("DRE", f["ds_conta"], valor_mil(f))
        caso("E2", "factual", f"Qual foi o resultado financeiro consolidado {de} no primeiro semestre de 2026?",
             [v], f"Resultado financeiro do 1S26: R$ {fmt_mil(valor_mil(f))} mil ({v['apresentacao_referencia']}).",
             fontes_de(("DRE", c_rf, False)), "presente" if l else "ausente", _j(l) or "Linha não encontrada no contexto.")
        # E3 — aplicações financeiras (Emenda 1 do protocolo): só a conta cujo
        # DS_CONTA é exatamente "Aplicações Financeiras" — 1.01.02, no ativo
        # circulante. As contas de longo prazo são subcontas por categoria de
        # mensuração, sem conta agregada com esse nome, e não são somadas.
        f_c = fo("BPA", c_apl_c)
        v = monet("aplicacoes_financeiras_30jun26", f_c["ds_conta"], f_c, False)
        l = ctx.propria("BPA", f_c["ds_conta"], valor_mil(f_c))
        caso("E3", "factual",
             f"Qual era o saldo de aplicações financeiras registrado no ativo circulante consolidado {de} "
             f"em 30 de junho de 2026?",
             [v], f"Aplicações Financeiras ({c_apl_c}, ativo circulante) em 30/06/2026: R$ {fmt_mil(valor_mil(f_c))} mil "
                  f"({v['apresentacao_referencia']}).",
             fontes_de(("BPA", c_apl_c, False)), "presente" if l else "ausente",
             _j(l) or "Linha não encontrada no contexto.",
             {"decisao_metodologica": {
                 "referencia": "Emenda 1 do protocolo (2026-09-27, antes da coleta)",
                 "conta_utilizada": {"cd_conta": c_apl_c, "ds_conta": f_c["ds_conta"], "demonstracao": f_c["demonstracao"],
                                     "valor_mil": txt(valor_mil(f_c)), "periodo": f_c["periodo"]},
                 "contas_nao_somadas": [{"cd_conta": c, "ds_conta": fo("BPA", c)["ds_conta"],
                                         "valor_mil": txt(valor_mil(fo("BPA", c)))} for c in c_apl_lp],
                 "motivo": "O gabarito reflete o conceito contábil explicitamente solicitado. Só a conta 1.01.02 tem "
                           "DS_CONTA 'Aplicações Financeiras'; as contas do realizável a longo prazo são subcontas por "
                           "categoria de mensuração, sem conta agregada de mesmo nome, e não são agregadas por "
                           "semelhança econômica. Substitui a definição anterior (circulante + longo prazo = 8.353.283 mil).",
             }})

    for c in casos:
        c["divergencia_da_estimativa"] = c["disponibilidade"] != c["disponibilidade_estimada_protocolo"]
        c["justificativa_divergencia"] = None
    return casos


# ── Orquestração ──────────────────────────────────────────────────────────────

def aplicar_revisao(dataset: dict) -> dict:
    rev = {}
    if os.path.exists(REVISAO):
        with open(REVISAO, encoding="utf-8") as f:
            rev = json.load(f)
    for c in dataset["casos"]:
        r = rev.get(c["id"])
        c["revisao_tecnica"] = r if r else {"revisado": False, "revisor": None, "observacao": None}
    dataset["metadados"]["revisao_tecnica_arquivo"] = os.path.basename(REVISAO) if rev else None
    dataset["metadados"]["sha256_revisao_tecnica"] = sha256_arquivo(REVISAO) if rev else None
    return dataset


def salvar(dataset: dict):
    with open(SAIDA, "w", encoding="utf-8", newline="\n") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=1)
        f.write("\n")


def construir(zip_path: str, cache_path: str | None):
    prot = ler_protocolo()
    zip_bytes = open(zip_path, "rb").read()
    cvm = FonteCVM(zip_bytes)
    cache = json.load(open(cache_path, encoding="utf-8")) if cache_path and os.path.exists(cache_path) else None
    novo_cache, casos, empresas_meta = {}, [], {}
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    # ignore_cleanup_errors: no Windows o ChromaDB mantém o índice temporário aberto
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        for emp in prot["empresas"]:
            tk = emp["ticker"]
            if cvm.versao_mais_recente(emp["codigo_cvm"]) != emp["versao"]:
                sys.exit(f"PARADA: versão mais recente de {tk} no ZIP difere do protocolo.")
            idx = cvm.indice[cvm.indice.CD_CVM.str.lstrip("0") == emp["codigo_cvm"]]
            emp["denom_cvm"] = idx[idx.VERSAO == str(emp["versao"])].DENOM_CIA.iloc[0]
            emp["estimada"] = prot["estimada"][tk]
            rc = reconstruir_contexto(emp, zip_bytes, tmp, cache)
            novo_cache[tk] = {"sha256_documento": rc["sha256_documento"], "ctx_num": rc["ctx_num"]}
            casos += construir_empresa(emp, cvm.empresa(emp["codigo_cvm"], emp["versao"]), Contexto(rc["trechos"]))
            empresas_meta[tk] = {"codigo_cvm": emp["codigo_cvm"], "empresa": emp["denom_cvm"],
                                 "estrutura": emp["estrutura"], "documento": TIPO_DOC, "periodo": PERIODO,
                                 "versao": emp["versao"], "sha256_documento": rc["sha256_documento"],
                                 "contexto_recuperado": rc["registro"]}
            print(f"{tk}: v{emp['versao']} sha ok | {rc['registro']['tabelas_recuperadas']}", flush=True)
            if cache_path:
                json.dump(novo_cache, open(cache_path, "w", encoding="utf-8"), ensure_ascii=False)
    dataset = {
        "metadados": {
            "descricao": "Dataset experimental do RAGAS do TCC 2 — 96 casos (12 empresas × 8 categorias). "
                         "Sem respostas, sem scores e sem resultados de exatidão: tudo isso é produzido na coleta.",
            "protocolo": "avaliacao/ragas/PROTOCOLO_RAGAS_TCC2.md",
            "sha256_protocolo": prot["sha256_protocolo"],
            "commit_sistema_avaliado": "777b256f15c3e36c762c9f332c3ba1171a3d466d",
            "commit_construcao": commit,
            "fonte_gabarito": {"arquivo": os.path.basename(zip_path), "sha256": hashlib.sha256(zip_bytes).hexdigest(),
                               "csvs": list(FonteCVM.ARQ.values()) + ["itr_cia_aberta_2026.csv"],
                               "observacao": "Valores lidos diretamente dos CSVs da CVM; calcular_metricas não é usado."},
            "periodos": {"dre": {"atual": S26, "comparavel": S25}, "balanco": {"atual": B26, "comparavel": B25}},
            "unidade_fonte": "R$ mil (ESCALA_MOEDA = MIL)",
            "construido_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "contexto": "Reconstruído com cvm.baixar_documento + criar_chunks + indexar_documento (índice temporário) + "
                        "recuperar_contexto, sem alterações; separado em trechos por extrair_chunks (TCC 1).",
        },
        "empresas": empresas_meta,
        "casos": casos,
    }
    salvar(aplicar_revisao(dataset))
    print(f"OK: {len(casos)} casos em {SAIDA}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip")
    ap.add_argument("--cache-contextos")
    ap.add_argument("--reaplicar-revisao", action="store_true")
    a = ap.parse_args()
    if a.reaplicar_revisao:
        with open(SAIDA, encoding="utf-8") as f:
            salvar(aplicar_revisao(json.load(f)))
        print("OK: revisão reaplicada")
    elif a.zip:
        construir(a.zip, a.cache_contextos)
    else:
        ap.error("informe --zip ou --reaplicar-revisao")
