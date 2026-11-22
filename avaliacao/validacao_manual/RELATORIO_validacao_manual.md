# Validação manual do FundIA — relatório consolidado

**Documento:** ITR, DT_REFER 2026-06-30, VERSAO 1 · **Empresas:** WEGE3, BBAS3, ZAMP3
**Código avaliado:** commit `183e69f` · **Modelo de redação:** `gemini-2.5-flash`

Este relatório consolida os quatro achados levantados na validação manual e o
rastreamento de cada um pelo código. Ele não altera nem corrige nenhum
resultado: tudo foi apurado sobre os artefatos congelados e sobre o código do
commit `183e69f`, sem modificá-lo. Outras observações da validação manual que
não foram rastreadas aqui não entram neste documento.

## 1. Execuções avaliadas

| Empresa | CVM | Fonte (SHA-256) | Tempo de `analisar()` | Auditoria do sistema | Commit registrado |
|---|---|---|---|---|---|
| WEGE3 | 5410 | `3afe4d4fce96…` | 53,3 s | 35/35 (100%) | `75dbfc4` + alterações de `183e69f` ainda não commitadas¹ |
| BBAS3 | 1023 | `5a38dc6e4e0a…` | 46,4 s | 30/30 (100%) | `183e69f` |
| ZAMP3 | 24317 | `666c2d05e720…` | 51,2 s | 40/40 (100%) | `504ce6d`² |

¹ O código executado é o mesmo que depois foi commitado como `183e69f`.
² `504ce6d` só acrescenta artefatos; o código do FundIA é idêntico ao de `183e69f`.

Nas três execuções, a chamada foi
`analisar(ticker, "ITR", periodo="2026-06-30", versao="1")`, sem erro em
nenhuma das 8 etapas, e o período e a versão retornados conferem com os pedidos.
Os artefatos de cada execução estão em `<TICKER>_ITR_2026-06-30_v1/`.

## 2. Achados

| # | Empresa | Afirmação da narrativa | Classificação | Etapa de origem |
|---|---|---|---|---|
| 1 | WEGE3 | Liquidez total de R$ 13,23 bi | Erro de cálculo (dupla contagem) | 7a · métricas |
| 2 | WEGE3 | "Resultado com juros" de R$ 3,92 mi → R$ 10,55 mi | Erro de associação conceitual (base individual) | 6 · recuperação → 7b · LLM |
| 3 | BBAS3 | "Não foi possível identificar os dados de captação no mercado aberto" | Falha de cálculo/métrica | 7a · métricas |
| 4 | ZAMP3 | "Receitas e despesas com juros" de R$ 103,42 mi → R$ 162,23 mi, e que isso "contribuiu para a piora do resultado final" | Erro de associação conceitual (conta da DFC) | 6 · recuperação → 7b · LLM |

A auditoria do próprio sistema marcou todos os números envolvidos como
**CONFERE**, e as três execuções saíram com 100% de conformidade.

### Achado 1 — WEGE3: liquidez total inflada

- **O que o sistema calculou:** caixa e equivalentes (7.750.256) + "Aplicações
  Financeiras" (5.477.045) = 13.227.301 (R$ mil), ou seja, R$ 13,23 bi.
- **Por que está errado:** `_aplicacoes_circulante()` (`metricas.py:224`) pega
  a primeira linha chamada "Aplicações Financeiras" depois de "Ativo
  Circulante", sem olhar o código da conta. Essa primeira linha é a
  **1.01.01.02**, filha do próprio caixa (1.01.01 = 1.01.01.01 Caixa e Bancos
  + 1.01.01.02). O mesmo valor entra duas vezes.
- **O valor correto pela regra do próprio sistema:** a aplicação de curto
  prazo é a conta **1.01.02** (1.050.886). A liquidez total seria R$ 8,80 bi.
- **O erro se propaga para a dívida líquida** (dívida bruta de 5.066.346):

  | Métrica | Sistema | Com a conta 1.01.02 |
  |---|---|---|
  | Liquidez total atual | R$ 13,23 bi | R$ 8,80 bi |
  | Liquidez total anterior | R$ 10,55 bi | R$ 7,28 bi |
  | Dívida líquida atual | −R$ 8,16 bi | −R$ 3,73 bi |
  | Dívida líquida anterior | −R$ 5,96 bi | −R$ 2,69 bi |
  | Dívida líquida com arrendamentos | −R$ 7,39 bi | −R$ 2,97 bi |

- **Por que a auditoria não pegou:** ela confrontou os R$ 13,23 bi com a
  própria métrica calculada (`endividamento.liquidez_total`), ou seja,
  comparou o número com ele mesmo.

### Achado 2 — WEGE3: resultado financeiro da DRE individual

- **Os valores citados** (10.552 e 3.924) são o "Resultado Financeiro" da
  **DRE individual**. O consolidado é 65.819 contra 47.595 (R$ 65,82 mi
  contra R$ 47,60 mi). A direção ("melhorou") é a mesma nas duas bases.
- **As métricas não calculam resultado financeiro.** O valor veio do contexto
  RAG enviado ao Prompt 2.
- **Como a DRE individual chegou ao LLM:** o canal narrativo
  (`recuperacao.py:49`) só encontra o cabeçalho como pedaço narrativo e
  completa a cota com pedaços de tabela **sem filtro de base contábil**
  (`recuperacao.py:54-60`). O pedaço escolhido foi a DRE (Individual).
  Reproduzido em leitura, o contexto tem 2.059 caracteres, igual ao log.
- **O resto da análise é consolidado** (`base_dados = "Consolidado"`). O
  destaque mistura bases sem avisar o leitor.

### Achado 3 — BBAS3: captação no mercado aberto "indisponível"

- **O dado existe:** a conta **2.02.02 "Captações no Mercado Aberto"** =
  845.408.764 (anterior: 727.039.247) está na fonte congelada, no balanço
  passivo consolidado. A extração funcionou.
- **Onde se perdeu:** `metricas.py:368` procura
  `"Captação no Mercado Aberto"`, no singular, e a comparação de nome é
  exata (`metricas.py:167`). A métrica ficou `nao_disponivel`, o destaque não
  foi gerado e `dados_ausentes` ficou vazio.
- **O LLM não tinha o dado:** o contexto enviado a ele tinha só o cabeçalho e
  a DFC consolidada, sem balanço passivo (4.177 caracteres, igual ao log). Ele
  recebeu o marcador `nao_disponivel` e o citou nas limitações, contrariando a
  regra 5 do prompt ("não mencione o que não existe"). A seção de limitações
  do mesmo prompt pede para citar o que faltou, e essas duas instruções
  conflitam.
- **É o mesmo padrão** do rótulo "Atribuído a/aos Sócios", já corrigido em
  `183e69f`: a regra para bancos existe, mas o nome buscado não é o que a CVM
  usa.

### Achado 4 — ZAMP3: linha da DFC apresentada como resultado financeiro

- **Os valores citados** (162.230 e 103.419) são da DFC consolidada, na linha
  "Juros, encargos, variação cambial, variação monetária e AVP sobre passivos
  de arrendamentos". É um **ajuste não caixa**, somado de volta ao prejuízo na
  conciliação do fluxo operacional. Ele cobre só arrendamentos, mistura juros
  com variação cambial e AVP, e não contém receita nenhuma.
- **A DRE consolidada nunca chegou ao LLM:** o contexto tinha só o cabeçalho e
  a DFC (4.241 caracteres, igual ao log), e as métricas não trazem resultado
  financeiro.
- **O rótulo "receitas e despesas com juros" vem do prompt:** a regra 2
  (`prompt2.py:36`) manda trocar "resultado financeiro" por esse termo, e o
  LLM o aplicou a uma conta que não é o resultado financeiro.
- **A conclusão causal é verdadeira na DRE, mas não pela conta citada:**

  | Item | 1S25 | 1S26 | Variação |
  |---|---|---|---|
  | Resultado operacional (DRE) | 22,53 mi | 26,76 mi | +4,23 mi |
  | Resultado financeiro (DRE) | −144,60 mi | −169,28 mi | −24,68 mi |
  | Prejuízo antes dos impostos (DRE) | −122,07 mi | −142,52 mi | −20,45 mi |
  | Linha citada (DFC) | 103,42 mi | 162,23 mi | +58,81 mi |

  A linha da DFC sobe mais que o dobro da piora real do resultado financeiro.

## 3. Causas comuns

Os quatro achados vêm de três mecanismos do sistema, e não de erros
aleatórios do LLM.

### 3.1 Seleção de contas pelo nome, não pelo código CVM (achados 1 e 3)

`calcular_metricas()` localiza as contas pelo texto exato da descrição e,
quando há nomes repetidos, pela ordem em que aparecem. Isso falha de dois
jeitos:

- **Homônimos em níveis diferentes da hierarquia:** "Aplicações Financeiras"
  é ao mesmo tempo 1.01.01.02 (filha do caixa) e 1.01.02.
- **Variação de nomenclatura entre empresas:** "Captação" contra "Captações";
  "Atribuído a" contra "Atribuído aos".

O `.txt` gerado não guarda `CD_CONTA`, então a hierarquia não existe mais
quando as métricas são calculadas.

### 3.2 O canal narrativo sem controle de base e sem seção relevante (achados 2 e 4)

- **Não há texto narrativo nos documentos estruturados da CVM:** o único
  pedaço narrativo é o cabeçalho.
- **O complemento pega qualquer tabela:** o canal narrativo completa a cota
  com pedaços de tabela escolhidos por semelhança com uma busca de "desempenho
  e estratégia", sem filtro de base.
- **O que chegou ao LLM nas três empresas:** a DRE individual (WEGE3) e a DFC
  consolidada (BBAS3, ZAMP3). A DRE consolidada não chegou em nenhuma.
- **O que o LLM fez:** usou essas tabelas para afirmar coisas que as métricas
  não cobrem, como resultado financeiro e juros.

O filtro "Consolidado" existe só no canal numérico, que o fluxo atual usa
apenas no caminho antigo do Prompt 1.

### 3.3 A auditoria verifica a existência do número, não o significado (todos)

Com 100% de conformidade nas três empresas, a auditoria não detectou nenhum
dos quatro achados:

| Limitação da auditoria | Achados afetados |
|---|---|
| Valores das métricas são conferidos contra as próprias métricas: um erro de cálculo passa sempre | 1 |
| Valores do documento são procurados em todas as seções, sem considerar a base, a demonstração ou a conta (`_fatos_do_documento`, `auditoria.py:136`) | 2, 4 |
| Frases sem número e afirmações qualitativas ou causais não são avaliadas | 3, 4 |
| Não existe verificação de que um campo `nao_disponivel` realmente falta na fonte | 3 |

**Implicação para o TCC:** a taxa de conformidade mede a **procedência
numérica** (o número citado existe na fonte ou nas métricas). Ela não mede a
**correção** (o número é o certo para o que a frase afirma). Os resultados da
auditoria precisam ser apresentados com essa ressalva.

### 3.4 Fatores do prompt (achados 3 e 4)

- **Regra 2:** o termo imposto "receitas e despesas com juros" é aplicado a
  qualquer linha que pareça financeira.
- **Regra 5 contra a seção de limitações:** a regra 5 manda não mencionar
  campos `nao_disponivel`, e a seção de limitações manda citar o que faltou.

## 4. Síntese

| Classificação | Achados |
|---|---|
| Correto | — |
| Erro de cálculo / falha de métrica | 1 (WEGE3 liquidez), 3 (BBAS3 captação) |
| Erro de associação conceitual | 2 (WEGE3 base individual), 4 (ZAMP3 conta da DFC) |
| Alucinação sem base no contexto | — |
| Falha de extração ou dado ausente na fonte | — |

- **Etapas preservadas:** em nenhum caso o documento baixado da CVM estava
  errado ou incompleto. As correções de período, versão e seções essenciais
  feitas em `183e69f` se mantiveram nas três empresas.
- **Onde estão as falhas:** na etapa determinística de métricas (seleção de
  contas) e na montagem do contexto do LLM.
- **O papel do LLM:** ele não inventou números; todos os valores citados
  existem na fonte ou nas métricas. As falhas dele são de interpretação: deu o
  rótulo errado a contas (achados 2 e 4), tirou uma conclusão causal que o
  contexto não sustentava (achado 4) e mencionou um campo `nao_disponivel`
  (achado 3).

## 5. Rastreabilidade

- **Artefatos brutos:** estão em `<TICKER>_ITR_2026-06-30_v1/`, com as
  seguintes funções:

  | Arquivo | Uso |
  |---|---|
  | `resultado_analisar.json` | Métricas e seções da narrativa |
  | `auditoria.json` | Veredito e origem de cada número |
  | Fonte `.txt` + `.sha256` | Documento congelado |

- **Contextos RAG:** foram reproduzidos em leitura a partir do ChromaDB. A
  recuperação é determinística, e o tamanho de cada contexto bate com o log da
  execução: 2.059, 4.177 e 4.241 caracteres.
- **Códigos de conta:** os `CD_CONTA` citados foram conferidos no ZIP oficial
  `itr_cia_aberta_2026.zip` da CVM, filtrando DT_REFER 2026-06-30 e VERSAO 1.
