# tests/test_prompt2_regras.py
#
# Presença das regras críticas no template do Prompt 2 (texto do prompt, sem
# chamar o LLM). Regras vindas da revalidação da decomposicao_resultado no
# TCC 2: causalidade só pela ponte em qualquer seção, "efeito" soberano, DFC
# sem julgamento pela direção e LIMITAÇÕES só a partir de dados_ausentes.
#
# Execução (na raiz do projeto):
#   python -m unittest tests.test_prompt2_regras -v

import importlib.util
import os
import re
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _prompt():
    # Carrega o módulo real pelo arquivo: tests.test_periodo_versao troca
    # modulos.prompt2 por um stub em sys.modules.
    spec = importlib.util.spec_from_file_location(
        "prompt2_real", os.path.join(RAIZ, "modulos", "prompt2.py"))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo.PROMPT_NARRATIVA


PROMPT = _prompt()
_, LIMITACOES = PROMPT.split("### LIMITAÇÕES DESTA ANÁLISE")
LIMITACOES = LIMITACOES.split("## DADOS FINANCEIROS EXTRAÍDOS")[0]


def _plano(texto):
    return re.sub(r"\s+", " ", texto)


class TestRegrasCriticas(unittest.TestCase):

    def test_template_formata(self):
        texto = PROMPT.format(dados_json="{}", contexto_narrativo="x", ticker="T",
                              nome_empresa="N", periodo="p")
        self.assertIn("## DADOS FINANCEIROS EXTRAÍDOS", texto)

    def test_causalidade_em_qualquer_secao(self):
        p = _plano(PROMPT)
        self.assertIn("vale para TODAS as seções, inclusive o RESUMO", p)
        self.assertIn('vem exclusivamente de "decomposicao_resultado", e somente quando "fecha" for true', p)
        self.assertIn("Se disser por que o resultado mudou, siga a regra 11.", p)

    def test_efeito_soberano(self):
        p = _plano(PROMPT)
        self.assertIn('O campo "efeito" é soberano.', p)
        self.assertIn('nunca pode ser apresentada como fator que reduziu o lucro', p)
        self.assertIn('nunca pode ser apresentada como fator que aumentou o lucro', p)
        self.assertIn("Não deduza o efeito pelo nome da conta, pelo sinal do valor nem pelo percentual", p)
        self.assertIn("a queda do lucro se explica pela parcela negativa", p)

    def test_abertura_e_subtotais(self):
        p = _plano(PROMPT)
        self.assertIn("Suas linhas não substituem a contribuição líquida dessa parcela", p)
        self.assertIn('entre as parcelas indicadas em "apos" e "antes"', p)

    def test_dfc_sem_julgamento_pela_direcao(self):
        p = _plano(PROMPT)
        self.assertIn("nunca explicam o lucro/prejuízo", p)
        self.assertIn("Inversão de sinal significa somente inversão de sinal.", p)
        self.assertIn('Não use "melhora", "piora", "positivo", "negativo", "favorável" ou '
                      '"desfavorável" para qualificar a direção de um fluxo', p)
        self.assertIn('Não coloque um fluxo de caixa em "O QUE FOI POSITIVO" ou "O QUE MERECE ATENÇÃO"', p)
        self.assertEqual(p.count("Não inclua fluxos de caixa por terem aumentado, diminuído ou "
                                 "invertido o sinal (regra 12)."), 2)   # POSITIVO e ATENÇÃO
        self.assertIn('não descreva o fluxo operacional como "geração de caixa das operações principais"', p)

    def test_limitacoes_somente_dados_ausentes(self):
        l = _plano(LIMITACOES)
        self.assertIn('Use somente o campo "dados_ausentes"', l)
        self.assertIn("Nunca transforme em limitação as regras deste prompt, os termos da regra 2", l)
        self.assertNotIn("O que esta análise NÃO pode responder", l)

    def test_limitacoes_com_dados_ausentes_vazio(self):
        l = _plano(LIMITACOES)
        self.assertIn('Se "dados_ausentes" estiver vazio, escreva apenas: "Não foram identificados '
                      'dados ausentes específicos nesta análise."', l)
        self.assertIn("Não liste métricas, demonstrações nem indicadores nesse caso.", l)

    def test_sem_ticker_no_prompt(self):
        self.assertIsNone(re.search(r"\b[A-Z]{4}\d{1,2}\b", PROMPT.replace("{ticker}", "")))


if __name__ == "__main__":
    unittest.main()
