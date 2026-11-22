# tests/test_periodo_versao.py
#
# Garante que o pipeline usa exatamente empresa + tipo + DT_REFER + VERSAO
# pedidos, sem aproveitar dados de outra data. Sem rede: os ZIPs da CVM são
# montados em memória e requests.get é substituído.
#
# Execução (na raiz do projeto):
#   python -m unittest tests.test_periodo_versao -v

import io
import os
import sys
import tempfile
import types
import unittest
import zipfile
from unittest import mock

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# O orquestrador importa embeddings/ChromaDB/LLM no topo; os testes param na
# etapa 3, então esses módulos são trocados por stubs para o import ser rápido
# e não depender de modelo nem de chave de API.
for _nome, _attrs in {
    "modulos.chunking":    ("criar_chunks", "indexar_documento"),
    "modulos.recuperacao": ("recuperar_contexto",),
    "modulos.prompt1":     ("executar_prompt_extracao",),
    "modulos.prompt2":     ("executar_prompt_narrativa",),
}.items():
    if _nome not in sys.modules:
        _stub = types.ModuleType(_nome)
        for _a in _attrs:
            setattr(_stub, _a, mock.MagicMock(name=_a))
        sys.modules[_nome] = _stub

from modulos import cvm, orquestrador  # noqa: E402

CVM_WEG = "5410"
OUTRA   = "1023"


# ── Dados sintéticos ──────────────────────────────────────────────────────────

def _indice(linhas):
    cols = ["CNPJ_CIA", "DT_REFER", "VERSAO", "DENOM_CIA", "CD_CVM",
            "CATEG_DOC", "ID_DOC", "DT_RECEB", "LINK_DOC"]
    return pd.DataFrame(
        [["x", ref, ver, "WEG S.A.", cod, cat, id_doc, "2026-07-22", f"http://l/{id_doc}"]
         for cod, cat, ref, ver, id_doc in linhas],
        columns=cols, dtype=str,
    )


def _dre(linhas):
    """linhas: (cd_cvm, dt_refer, versao, valor_receita)."""
    cols = ["CNPJ_CIA", "DT_REFER", "VERSAO", "DENOM_CIA", "CD_CVM", "ORDEM_EXERC",
            "DT_INI_EXERC", "DT_FIM_EXERC", "CD_CONTA", "DS_CONTA", "VL_CONTA"]
    return pd.DataFrame(
        [["x", ref, ver, "WEG", cod, "ÚLTIMO", ref[:4] + "-01-01", ref,
          "3.01", "Receita de Venda de Bens e/ou Serviços", valor]
         for cod, ref, ver, valor in linhas],
        columns=cols, dtype=str,
    )


SECOES_COMPLETAS = ("DRE_con", "BPA_con", "BPP_con", "DFC_MI_con")


def _zip(ano, dre_linhas, com_composicao=True, secoes=SECOES_COMPLETAS, linhas_por_secao=None):
    """ZIP no formato da CVM. Por padrão, todas as seções essenciais recebem
    as mesmas linhas; `linhas_por_secao` sobrescreve as de uma seção."""
    linhas_por_secao = linhas_por_secao or {}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for sufixo in secoes:
            z.writestr(f"itr_cia_aberta_{sufixo}_{ano}.csv",
                       _dre(linhas_por_secao.get(sufixo, dre_linhas)).to_csv(sep=";", index=False))
        if com_composicao:
            # Formato real da CVM: sem CD_CVM (só CNPJ)
            z.writestr(f"itr_cia_aberta_composicao_capital_{ano}.csv",
                       "CNPJ_CIA;DT_REFER;VERSAO;DENOM_CIA;QT_ACAO_TOTAL_CAP_INTEGR\n"
                       f"x;{ano}-06-30;1;WEG;100\n")
    return buf.getvalue()


def _resposta(conteudo=b"", status=200):
    r = mock.MagicMock(status_code=status, content=conteudo)
    if status >= 400:
        import requests
        r.raise_for_status.side_effect = requests.HTTPError(f"{status}")
    return r


# Um ano com três trimestres (valores distintos) e uma reapresentação do 2T.
DRE_2026 = [
    (CVM_WEG, "2026-03-31", "1", "1111"),
    (CVM_WEG, "2026-06-30", "1", "2222"),
    (CVM_WEG, "2026-06-30", "2", "2299"),
    (CVM_WEG, "2026-09-30", "1", "3333"),
    (OUTRA,   "2026-06-30", "1", "9999"),
]


# ── buscar_documento_mais_recente ────────────────────────────────────────────

class TestBuscarDocumento(unittest.TestCase):

    def setUp(self):
        self.indice = _indice([
            (CVM_WEG, "ITR", "2026-03-31", "1", "100"),
            (CVM_WEG, "ITR", "2026-06-30", "1", "200"),
            (CVM_WEG, "ITR", "2026-06-30", "2", "201"),
            (OUTRA,   "ITR", "2026-09-30", "1", "300"),
        ])
        p = mock.patch.object(cvm, "_carregar_indice_ano",
                              side_effect=lambda t, a: self.indice if a == 2026 else None)
        self.carregar = p.start()
        self.addCleanup(p.stop)

    def test_periodo_e_versao_corretos_sao_aceitos(self):
        meta = cvm.buscar_documento_mais_recente(CVM_WEG, "ITR", "2026-06-30", 1)
        self.assertEqual(meta["periodo"], "2026-06-30")
        self.assertEqual(meta["versao"], 1)
        self.assertEqual(meta["id_doc"], "200")
        self.assertTrue(meta["link"].startswith("https://"))

    def test_sem_versao_escolhe_a_maior_da_referencia(self):
        meta = cvm.buscar_documento_mais_recente(CVM_WEG, "ITR", "2026-06-30")
        self.assertEqual(meta["versao"], 2)
        self.assertEqual(meta["id_doc"], "201")

    def test_versao_explicita_e_respeitada_mesmo_havendo_mais_nova(self):
        meta = cvm.buscar_documento_mais_recente(CVM_WEG, "ITR", "2026-06-30", "1")
        self.assertEqual((meta["versao"], meta["id_doc"]), (1, "200"))

    def test_periodo_inexistente_gera_erro(self):
        # 2026-09-30 existe para OUTRA empresa, não para a WEG: nada de fallback
        with self.assertRaises(ValueError):
            cvm.buscar_documento_mais_recente(CVM_WEG, "ITR", "2026-09-30", 1)

    def test_versao_inexistente_gera_erro(self):
        with self.assertRaises(ValueError):
            cvm.buscar_documento_mais_recente(CVM_WEG, "ITR", "2026-06-30", 3)

    def test_periodo_de_outro_ano_nao_consulta_ano_vizinho(self):
        with self.assertRaises(ValueError):
            cvm.buscar_documento_mais_recente(CVM_WEG, "ITR", "2025-06-30", 1)
        anos = [c.args[1] for c in self.carregar.call_args_list]
        self.assertEqual(anos, [2025])

    def test_formato_de_periodo_invalido_gera_erro(self):
        for invalido in ("2026-06", "30/06/2026", "2026-6-30"):
            with self.assertRaises(ValueError, msg=invalido):
                cvm.buscar_documento_mais_recente(CVM_WEG, "ITR", invalido, 1)

    def test_tipo_errado_nao_casa(self):
        self.indice = _indice([(CVM_WEG, "DFP", "2026-06-30", "1", "999")])
        with self.assertRaises(ValueError):
            cvm.buscar_documento_mais_recente(CVM_WEG, "ITR", "2026-06-30", 1)


# ── baixar_documento ─────────────────────────────────────────────────────────

class _BaseBaixar(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.destino = os.path.join(self.tmp.name, "WEGE3_ITR_2026-06-30.txt")

    def _baixar(self, periodo, versao, conteudo=None, status=200):
        conteudo = _zip(2026, DRE_2026) if conteudo is None else conteudo
        with mock.patch.object(cvm.requests, "get",
                               return_value=_resposta(conteudo, status)) as get:
            try:
                return cvm.baixar_documento("", self.destino, CVM_WEG, "ITR",
                                            periodo, versao), get
            finally:
                self.get = get

    def _ler(self):
        with open(self.destino, encoding="utf-8") as f:
            return f.read()


class TestBaixarDocumento(_BaseBaixar):

    def test_periodo_correto_grava_so_os_valores_dele(self):
        self._baixar("2026-06-30", 1)
        texto = self._ler()
        self.assertIn("DOCUMENTO: ITR — 2026-06-30", texto)
        self.assertIn("EMPRESA CVM: 5410", texto)
        self.assertIn("VERSAO: 1", texto)
        self.assertIn("2222", texto)
        # Nenhum valor de outro trimestre, outra versão ou outra empresa
        for intruso in ("1111", "2299", "3333", "9999"):
            self.assertNotIn(intruso, texto)

    def test_versao_2_seleciona_a_reapresentacao(self):
        self._baixar("2026-06-30", 2)
        texto = self._ler()
        self.assertIn("VERSAO: 2", texto)
        self.assertIn("2299", texto)
        self.assertNotIn("2222", texto)

    def test_periodo_inexistente_gera_erro_sem_gravar(self):
        # Antes da correção, o filtro vazio caía para TODAS as linhas da
        # empresa e o 1T entrava no lugar do período pedido.
        with self.assertRaises(RuntimeError):
            self._baixar("2026-12-31", 1)
        self.assertFalse(os.path.exists(self.destino))

    def test_versao_inexistente_gera_erro_sem_gravar(self):
        with self.assertRaises(RuntimeError):
            self._baixar("2026-06-30", 3)
        self.assertFalse(os.path.exists(self.destino))

    def test_mesmo_mes_com_outro_dia_nao_e_aceito(self):
        # O filtro antigo era por prefixo "AAAA-MM"
        dre = [(CVM_WEG, "2026-06-29", "1", "5555")]
        with self.assertRaises(RuntimeError):
            self._baixar("2026-06-30", 1, conteudo=_zip(2026, dre))

    def test_zip_indisponivel_nao_cai_para_o_ano_anterior(self):
        with self.assertRaises(Exception):
            self._baixar("2026-06-30", 1, status=404)
        self.assertEqual(self.get.call_count, 1)
        self.assertIn("itr_cia_aberta_2026.zip", self.get.call_args.args[0])
        self.assertFalse(os.path.exists(self.destino))

    def test_periodo_e_versao_obrigatorios(self):
        for periodo, versao in (("", 1), ("2026-06-30", ""), ("2026-06-30", None)):
            with self.assertRaises(ValueError):
                cvm.baixar_documento("", self.destino, CVM_WEG, "ITR", periodo, versao)


class TestSecoesEssenciais(_BaseBaixar):
    """Documento incompleto no período/versão pedidos não pode ser gravado."""

    SO_1T = [(CVM_WEG, "2026-03-31", "1", "1111")]

    def _erro_de(self, **kw):
        with self.assertRaises(RuntimeError) as ctx:
            self._baixar("2026-06-30", 1, conteudo=_zip(2026, DRE_2026, **kw))
        self.assertFalse(os.path.exists(self.destino))
        return str(ctx.exception)

    def test_dfc_so_de_outro_periodo_gera_erro_nomeando_a_secao(self):
        # A empresa tem DFC no ZIP, mas só do 1T: antes, a seção sumia calada
        msg = self._erro_de(linhas_por_secao={"DFC_MI_con": self.SO_1T})
        self.assertIn("Demonstração de Fluxo de Caixa (Consolidado)", msg)
        self.assertNotIn("Ativo", msg)

    def test_balanco_ausente_gera_erro_nomeando_as_secoes(self):
        msg = self._erro_de(secoes=("DRE_con", "DFC_MI_con"))
        self.assertIn("Balanço Patrimonial — Ativo (Consolidado)", msg)
        self.assertIn("Balanço Patrimonial — Passivo (Consolidado)", msg)

    def test_dre_ausente_gera_erro(self):
        msg = self._erro_de(linhas_por_secao={"DRE_con": self.SO_1T})
        self.assertIn("Demonstração de Resultado", msg)

    def test_dfc_pelo_metodo_direto_e_aceita(self):
        self._baixar("2026-06-30", 1, conteudo=_zip(
            2026, DRE_2026, secoes=("DRE_con", "BPA_con", "BPP_con", "DFC_MD_con")))
        self.assertIn("Demonstração de Fluxo de Caixa (Consolidado)", self._ler())

    def test_composicao_capital_nao_e_essencial(self):
        self._baixar("2026-06-30", 1, conteudo=_zip(2026, DRE_2026, com_composicao=False))
        self.assertTrue(os.path.exists(self.destino))

    def test_empresa_sem_consolidado_exige_so_a_dre_individual(self):
        self._baixar("2026-06-30", 1, conteudo=_zip(2026, DRE_2026, secoes=("DRE_ind",)))
        self.assertIn("Demonstração de Resultado (Individual)", self._ler())


# ── calcular_metricas: lucro atribuível ──────────────────────────────────────

def _metricas(controladora, nao_controladores, valores=(6362961, 4794808, 1568153)):
    """Documento mínimo com a DRE de um banco; os rótulos das linhas de
    atribuição variam conforme a nomenclatura da empresa."""
    from modulos.extracao import extrair_documento
    from modulos.metricas import calcular_metricas
    lucro, ctrl, minor = valores
    texto = "\n".join([
        "DOCUMENTO: ITR — 2026-06-30", "EMPRESA CVM: 1023", "VERSAO: 1", "",
        "\n" + "=" * 50, "Demonstração de Resultado (Consolidado)", "=" * 50,
        "Receitas de Intermediação Financeira   160747114.0  (anterior: 149252571.0)",
        f"Lucro ou Prejuízo Líquido Consolidado do Período   {lucro}.0  (anterior: 7760116.0)",
        f"{controladora}   {ctrl}.0  (anterior: 6220887.0)",
        f"{nao_controladores}   {minor}.0  (anterior: 1539229.0)",
    ])
    with tempfile.TemporaryDirectory() as tmp:
        caminho = os.path.join(tmp, "BBAS3_ITR_2026-06-30.txt")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(texto)
        return calcular_metricas(extrair_documento(caminho))


class TestLucroAtribuivel(unittest.TestCase):

    DESTAQUE = "Lucro atribuído a sócios da controladora: R$ 4,79 bilhões"

    def test_nomenclatura_do_bbas3_aos_socios(self):
        m = _metricas("Atribuído aos Sócios da Empresa Controladora",
                      "Atribuído aos Sócios não Controladores")
        self.assertIn(self.DESTAQUE, m["outros_destaques"])

    def test_nomenclatura_padrao_a_socios_preservada(self):
        m = _metricas("Atribuído a Sócios da Empresa Controladora",
                      "Atribuído a Sócios Não Controladores")
        self.assertIn(self.DESTAQUE, m["outros_destaques"])

    def test_nao_controladores_negativo_com_nomenclatura_do_bbas3(self):
        m = _metricas("Atribuído aos Sócios da Empresa Controladora",
                      "Atribuído aos Sócios não Controladores",
                      valores=(6362961, 6500000, -137039))
        self.assertTrue(any("não controladores é negativo" in a
                            for a in m["advertencias"]))


# ── Cache do orquestrador ────────────────────────────────────────────────────

def _cabecalho(tipo="ITR", periodo="2026-06-30", cvm_=CVM_WEG, versao="1",
               formato=cvm.FORMATO_DOCUMENTO):
    linhas = [f"DOCUMENTO: {tipo} — {periodo}", f"EMPRESA CVM: {cvm_}"]
    if versao is not None:
        linhas.append(f"VERSAO: {versao}")
    if formato is not None:
        linhas.append(f"FORMATO: {formato}")
    return "\n".join(linhas + ["", "conteudo"])


class TestCacheConfere(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.caminho = os.path.join(self.tmp.name, "c.txt")

    def _confere(self, **cab):
        with open(self.caminho, "w", encoding="utf-8") as f:
            f.write(_cabecalho(**cab))
        return orquestrador._cache_confere(self.caminho, CVM_WEG, "ITR", "2026-06-30", 1)

    def test_cabecalho_identico_e_aceito(self):
        self.assertTrue(self._confere())

    def test_outro_periodo_rejeitado(self):
        self.assertFalse(self._confere(periodo="2026-03-31"))

    def test_outra_versao_rejeitada(self):
        self.assertFalse(self._confere(versao="2"))

    def test_outra_empresa_rejeitada(self):
        self.assertFalse(self._confere(cvm_=OUTRA))

    def test_outro_tipo_rejeitado(self):
        self.assertFalse(self._confere(tipo="DFP"))

    def test_cache_antigo_sem_versao_rejeitado(self):
        self.assertFalse(self._confere(versao=None))

    def test_cache_sem_formato_cd_conta_rejeitado(self):
        # Caches da validação (183e69f) têm VERSAO, mas não CD_CONTA nas linhas
        self.assertFalse(self._confere(formato=None))

    def test_cache_de_outro_formato_rejeitado(self):
        self.assertFalse(self._confere(formato="OUTRO"))


class TestAnalisarCache(unittest.TestCase):
    """analisar() até a etapa 3: decide entre reusar o cache e baixar de novo."""

    META = {"periodo": "2026-06-30", "versao": 1, "link": "", "data_entrega": "x"}

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.caminho = os.path.join(self.tmp.name, "WEGE3_ITR_2026-06-30.txt")
        patches = {
            "CAMINHO_CACHE":      self.tmp.name,
            "validar_ticker":     mock.MagicMock(return_value={"valido": True, "codigo_cvm": CVM_WEG}),
            "buscar_nome_empresa": mock.MagicMock(return_value="WEG S.A."),
            "buscar_documento_mais_recente": mock.MagicMock(return_value=dict(self.META)),
            "baixar_documento":   mock.MagicMock(side_effect=RuntimeError("baixou")),
            # Interrompe logo depois do download: o que importa é a decisão de cache
            "extrair_documento":  mock.MagicMock(side_effect=ValueError("parou na etapa 4")),
        }
        for nome, valor in patches.items():
            p = mock.patch.object(orquestrador, nome, valor)
            p.start()
            self.addCleanup(p.stop)

    def _grava_cache(self, **cab):
        with open(self.caminho, "w", encoding="utf-8") as f:
            f.write(_cabecalho(**cab))

    def test_periodo_e_versao_sao_repassados(self):
        orquestrador.analisar("WEGE3", "ITR", periodo="2026-06-30", versao="1")
        orquestrador.buscar_documento_mais_recente.assert_called_once_with(
            CVM_WEG, "ITR", periodo="2026-06-30", versao="1")
        kwargs = orquestrador.baixar_documento.call_args.kwargs
        self.assertEqual((kwargs["periodo"], kwargs["versao"]), ("2026-06-30", 1))

    def test_sem_periodo_busca_o_mais_recente(self):
        orquestrador.analisar("WEGE3", "ITR")
        orquestrador.buscar_documento_mais_recente.assert_called_once_with(
            CVM_WEG, "ITR", periodo=None, versao=None)

    def test_cache_de_outro_periodo_nao_e_reutilizado(self):
        # Arquivo com o nome do 2T26, mas conteúdo do 1T26
        self._grava_cache(periodo="2026-03-31")
        r = orquestrador.analisar("WEGE3", "ITR", periodo="2026-06-30", versao="1")
        orquestrador.baixar_documento.assert_called_once()
        orquestrador.extrair_documento.assert_not_called()
        self.assertEqual(r["erro"], "baixou")

    def test_cache_de_outra_versao_nao_e_reutilizado(self):
        self._grava_cache(versao="2")
        orquestrador.analisar("WEGE3", "ITR", periodo="2026-06-30", versao="1")
        orquestrador.baixar_documento.assert_called_once()

    def test_cache_correto_e_reutilizado(self):
        self._grava_cache()
        r = orquestrador.analisar("WEGE3", "ITR", periodo="2026-06-30", versao="1")
        orquestrador.baixar_documento.assert_not_called()
        orquestrador.extrair_documento.assert_called_once_with(self.caminho)
        self.assertEqual(r["etapas"]["download"], "ok")

    def test_documento_inexistente_gera_erro_explicito(self):
        orquestrador.buscar_documento_mais_recente.side_effect = ValueError(
            "Documento inexistente: CVM 5410, ITR, 2026-12-31, versão 1.")
        r = orquestrador.analisar("WEGE3", "ITR", periodo="2026-12-31", versao="1")
        self.assertIn("Documento inexistente", r["erro"])
        self.assertIsNone(r["analise"])
        orquestrador.baixar_documento.assert_not_called()


if __name__ == "__main__":
    unittest.main()
