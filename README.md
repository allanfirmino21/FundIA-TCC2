# FundIA

O FundIA analisa as demonstrações financeiras estruturadas que as companhias abertas
brasileiras entregam à Comissão de Valores Mobiliários (CVM). Ele calcula os indicadores em
código Python, usa um modelo de linguagem apenas para redigir uma narrativa em linguagem
acessível e confere os números identificados nessa narrativa com um auditor baseado em regras.
Cada número verificado recebe um veredito e a indicação da fonte contra a qual foi conferido.

Este repositório acompanha o Trabalho de Conclusão de Curso (TCC 2) do Bacharelado em Ciência de
Dados para Negócios da Universidade Federal da Paraíba (UFPB). Ele reúne o código, os testes e os
artefatos das avaliações descritas no trabalho. O texto do TCC não está incluído.

O sistema foi construído no TCC 1, cujo código está em
[allanfirmino21/TCC-1](https://github.com/allanfirmino21/TCC-1). O histórico deste repositório
começa no commit `1a08d00`, com conteúdo idêntico ao do commit `7f19e7f` daquele repositório, e
registra as correções e as avaliações feitas no TCC 2.

> O FundIA é um protótipo acadêmico. A análise gerada não constitui recomendação de investimento
> e não substitui a leitura do documento entregue à CVM.

## O que o sistema faz

- Resolve o código de negociação da B3 (por exemplo, `WEGE3`) para o código da companhia na CVM.
- Seleciona o formulário (ITR ou DFP) por data de referência e versão; sem indicação explícita,
  usa a referência mais recente e, nela, a maior versão.
- Baixa os dados abertos da CVM e extrai a demonstração do resultado, o balanço patrimonial e a
  demonstração dos fluxos de caixa.
- Calcula em código os indicadores: receita, lucro, variações, margem, EBITDA aproximado, dívida
  bruta e líquida, liquidez, indicadores bancários e a decomposição da variação do resultado.
- Redige uma narrativa em sete seções com o Gemini 2.5 Flash, a partir dos valores já calculados.
- Audita os valores monetários, percentuais e razões citados na narrativa e produz a trilha de
  auditoria.
- Apresenta o resultado numa aplicação web (FastAPI e React), com a trilha exportável em CSV.

## Arquitetura

O fluxo tem oito etapas, executadas por `modulos/orquestrador.py`:

| Etapa | Módulo | Função |
|---|---|---|
| 1. Identificação da companhia | `ticker.py` | Código de negociação para código CVM: mapa embutido, `dados/ticker_map.csv` e cadastro FCA da CVM |
| 2. Seleção do documento | `cvm.py` | Formulário por empresa, tipo, data de referência e versão |
| 3. Obtenção dos dados estruturados | `cvm.py` | Arquivo anual da CVM, recorte da empresa e verificação de consistência |
| 4. Extração das demonstrações | `extracao.py` | Resultado, balanço e fluxos de caixa, base consolidada e resultado individual |
| 5. Segmentação e indexação vetorial | `chunking.py` | Segmentos por demonstração, indexados no ChromaDB |
| 6. Recuperação em dois canais | `recuperacao.py` | Canal narrativo (só o cabeçalho, no caso dos documentos estruturados) e canal numérico (até três tabelas) |
| 7a. Cálculo determinístico | `metricas.py` | Indicadores e decomposição do resultado, sem modelo de linguagem |
| 7b. Redação da narrativa | `prompt2.py` | Gemini 2.5 Flash, temperatura 0,3, sete seções |
| 8. Auditoria dos números citados | `auditoria.py` | Veredito (`CONFERE`, `DIVERGENTE`, `NAO_ENCONTRADO` ou `IGNORADO`) e proveniência de cada valor |

Três pontos de projeto merecem destaque:
- **Separação entre cálculo e redação.** A redação recebe as métricas calculadas e o cabeçalho do
  documento. O canal numérico da recuperação não é enviado à redação; ele serve às respostas
  diretas avaliadas pelo protocolo RAGAS.
- **Duas versões do auditor.** A versão 1.0 confere existência na fonte, sinal e direção. A
  versão 2.0, padrão atual, verifica também se o valor monetário com rótulo reconhecido foi
  associado ao conceito certo. Nenhuma das duas verifica interpretações, relações causais ou
  afirmações sem número.
- **Caminho legado.** Quando o cálculo em código não encontra uma demonstração do resultado
  utilizável, o sistema recorre à extração pelo modelo (`prompt1.py`). As narrativas avaliadas no
  TCC 2 não usaram esse caminho.

**Interfaces**

| Interface | Arquivos | Trilha de auditoria |
|---|---|---|
| Aplicação web | `api.py` (FastAPI, progresso por SSE) e `frontend/` (React e Vite) | Sim, com exportação em CSV |
| Interface inicial | `app.py` (Streamlit) | Não |
| Relatório em PDF | `modulos/relatorio_pdf.py` | Não; contém as sete seções da narrativa |

## Requisitos

- Python 3.12.
- Node.js 20.19 ou superior (o Vite 8 exige `^20.19.0` ou `>=22.12.0`), para a aplicação web.
- Uma chave da API do Google Gemini.
- Acesso à internet. Na primeira execução, o sistema baixa o modelo de embeddings
  `paraphrase-multilingual-mpnet-base-v2` (cerca de 1 GB) e os arquivos da CVM.

## Instalação

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
npm install --prefix frontend
```

`requirements.txt` fixa as versões das dependências diretas. As dependências da avaliação RAGAS
ficam num ambiente separado, com resolução completa em `avaliacao/ragas/requirements_avaliacao.lock`
(ver [REPRODUTIBILIDADE.md](REPRODUTIBILIDADE.md)).

## Configuração

O código lê a chave da variável de ambiente `GEMINI_API_KEY`:

```bash
export GEMINI_API_KEY="<sua-chave>"          # Linux/macOS
$env:GEMINI_API_KEY = "<sua-chave>"          # Windows PowerShell
```

Também é possível gravar a chave, sozinha, num arquivo `api_key.txt` na raiz do projeto; `api.py`
a lê na inicialização. O arquivo [`.env.example`](.env.example) mostra a variável esperada, mas não
é carregado automaticamente. `api_key.txt`, `.env` e `.claude/` estão no `.gitignore` e não devem
ser versionados.

## Execução

**Aplicação web**, em dois terminais:

```bash
uvicorn api:app --port 8000
```

```bash
npm run dev --prefix frontend
```

A interface fica em `http://localhost:5173`. Ela analisa o documento mais recente da companhia; a
interface não oferece escolha de período.

**Interface inicial (Streamlit):**

```bash
streamlit run app.py
```

**Chamada direta, com período e versão definidos** (forma usada nas avaliações do TCC 2):

```python
from modulos.orquestrador import analisar

resultado = analisar("WEGE3", "ITR", periodo="2026-06-30", versao="1")
narrativa = resultado["analise"]["secoes"]
auditoria = resultado["analise"]["auditoria"]
```

## Testes

```bash
python -m unittest discover -s tests
```

A suíte tem 395 testes, cobrindo métricas, auditoria, recuperação, seleção de período e versão,
regras da instrução de redação e os instrumentos da avaliação RAGAS. Ela usa dados sintéticos e
fixtures em `tests/fixtures/` e não chama a API do Gemini. Alguns testes carregam o modelo de
embeddings, que precisa estar disponível localmente ou ser baixado na primeira execução. Na
máquina de desenvolvimento, em 20/11/2026, a suíte terminou sem falhas (6 testes pulados).

## Estrutura

```
api.py, app.py, config.py   aplicação web (FastAPI), interface Streamlit e constantes
modulos/                    as oito etapas do fluxo, a auditoria e o PDF
frontend/                   interface React (Vite)
tests/                      testes unitários e fixtures
dados/ticker_map.csv        mapa ticker -> código CVM (os demais arquivos de dados/ são baixados)
avaliacao/                  scripts, protocolos e artefatos das avaliações
NOTAS_DESENVOLVIMENTO.md    decisões de critério e histórico técnico
REPRODUTIBILIDADE.md        guia que liga cada avaliação ao seu estado de código e artefatos
```

Arquivos gerados e não versionados: `dados/cache/`, `dados/meta_*.csv`, `dados/fca_*.csv`,
`chroma_db/` e `avaliacao/ragas/runtime/`.

## Avaliações do TCC 2

As avaliações não usaram uma única versão do sistema. O código mudou ao longo do TCC 2, e cada
avaliação está associada ao estado do código em que foi executada. O guia
[REPRODUTIBILIDADE.md](REPRODUTIBILIDADE.md) traz, para cada uma, o commit, os scripts, os
artefatos e o grau de reprodutibilidade:
- demonstração do fluxo, com a versão do TCC 1;
- comparação pré-registrada entre o Gemini 2.5 Flash e o Gemini 2.5 Pro;
- validação manual em três rodadas (WEGE3, BBAS3 e ZAMP3);
- avaliação das respostas diretas pelo protocolo RAGAS, com verificação de exatidão e anotação de
  comportamento;
- execução exploratória;
- demonstração funcional da aplicação web.

O commit `f41137d` é a versão documentada no TCC 2. Nele, o código do sistema é idêntico ao do
commit `777b256`, a última alteração de código (27/09/2026). Ele não é o commit de execução das
avaliações.

Em resumo, nas condições examinadas, depois das correções, a leitura manual não encontrou número
divergente da fonte nem atribuído à conta errada nas narrativas da segunda e da terceira rodadas
(141 de 141 e 150 de 150 números). Ainda assim, houve erros de interpretação com valores corretos,
o que mostra que a conformidade reportada pelo auditor mede a procedência dos números, e não a
correção da análise.

## Limitações

- Cobre apenas documentos ITR e DFP disponíveis no Portal de Dados Abertos da CVM; as avaliações
  do TCC 2 usaram apenas ITR.
- O código presume valores em milhares de reais e não lê o campo `ESCALA_MOEDA`.
- O EBITDA é uma aproximação declarada e pode divergir do valor divulgado pela companhia.
- O auditor não verifica o conceito de percentuais e razões, o período, a base contábil, a
  interpretação nem afirmações sem número.
- A narrativa depende de um modelo proprietário e não determinístico; os modelos `gemini-2.5-*`
  podem deixar de estar disponíveis.
- Nenhuma avaliação mediu se a análise é compreensível ou útil para o investidor.

## Licença e citação

O código e a documentação de autoria do projeto estão sob a licença MIT (ver [LICENSE](LICENSE)).
Os metadados de citação estão em [CITATION.cff](CITATION.cff).

A licença MIT não se aplica a materiais de terceiros incluídos no repositório:
- os dados e documentos da CVM copiados em `avaliacao/` e `tests/fixtures/`, que são dados
  públicos do [Portal de Dados Abertos da CVM](https://dados.cvm.gov.br), sujeitos às condições da
  fonte e preservados como evidência;
- os textos gerados pelos modelos Gemini, preservados como evidência das avaliações;
- as dependências instaladas por `requirements.txt` e `frontend/package.json`, cada uma com a sua
  licença;
- o arquivo `frontend/src/assets/vite.svg`, proveniente do modelo de projeto do Vite.

## Contexto acadêmico

- Autor: Allan Vitor Sousa Firmino
- Orientador: Prof. Dr. Hilton Martins de Brito Ramalho
- Curso: Bacharelado em Ciência de Dados para Negócios, Centro de Ciências Sociais Aplicadas, UFPB
- Ano: 2026
