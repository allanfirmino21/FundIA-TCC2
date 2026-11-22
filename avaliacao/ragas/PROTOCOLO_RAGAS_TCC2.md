# Protocolo experimental — avaliação RAGAS do TCC 2

**Projeto:** FundIA — TCC de Ciência de Dados, UFPB
**Data de registro:** 2026-09-27
**Commit de referência do sistema avaliado:** `777b256f15c3e36c762c9f332c3ba1171a3d466d`
**Status:** registrado ANTES de qualquer geração de resposta, de qualquer chamada ao
Gemini para este experimento e de qualquer cálculo de métrica RAGAS.

Este documento fixa o objeto avaliado, a amostra, as categorias de pergunta, a
classificação prévia da disponibilidade de informação, as métricas e o plano de análise
antes da coleta. Seu propósito é impedir racionalização posterior dos resultados.
Qualquer alteração feita depois do início da coleta deve ser registrada como **emenda
datada** ao final deste arquivo, com justificativa, e nunca por edição silenciosa do
texto original. Considera-se "início da coleta" a primeira chamada ao LLM para gerar a
resposta de qualquer um dos 96 casos.

---

## 1. Objetivo

Avaliar, em 12 companhias abertas e 96 casos, a capacidade do sistema de **responder
perguntas financeiras a partir do contexto numérico que ele próprio recupera** do ITR de
30/06/2026, medindo com o RAGAS:

- a aderência da resposta ao contexto recuperado (*faithfulness*);
- a relevância da resposta para a pergunta (*answer relevancy*).

De forma complementar e independente do RAGAS, uma **verificação determinística de
exatidão numérica** (Seção 11.1) confere os valores objetivos das respostas contra um
gabarito extraído diretamente dos dados estruturados da CVM.

O experimento amplia a avaliação RAGAS do TCC 1 (3 empresas, 15 casos), que listou essa
ampliação entre os trabalhos futuros. Acrescenta uma classificação prévia de
disponibilidade da informação no contexto, que permite separar falhas de geração de
falhas decorrentes do que a recuperação entrega.

## 2. Relação com a validação manual

| Avaliação | Objeto | O que responde |
|---|---|---|
| Validação manual (WEGE3, BBAS3, ZAMP3) | **narrativa final** de `analisar()` (Prompt 2 + métricas determinísticas + auditor) | os números, a interpretação contábil e a causalidade da narrativa conferem com a fonte? |
| RAGAS (este protocolo, 12 empresas) | **resposta direta** do LLM sobre o contexto recuperado | a resposta é sustentada pelo contexto e relevante para a pergunta? Complementarmente, fora do RAGAS: seus valores conferem com o gabarito CVM? |
| Avaliação qualitativa com investidores (futura) | narrativa como peça de comunicação | é clara, útil e confiável para o investidor? |

O RAGAS deste protocolo **não avalia a narrativa final**. No sistema atual, para
documentos estruturados da CVM, o contexto numérico recuperado não alimenta o Prompt 2
(a narrativa recebe as métricas calculadas e o contexto narrativo, que contém apenas o
cabeçalho). Nenhum resultado deste experimento será apresentado como evidência de
fidelidade da narrativa, de correção das métricas determinísticas ou de causalidade da
narrativa; essas propriedades pertencem à validação manual.

## 3. Amostra

Congelada; nenhuma empresa será incluída, removida ou substituída depois deste registro.

| # | Ticker | Companhia (DENOM_CIA) | Código CVM | Estrutura contábil |
|---|---|---|---|---|
| 1 | WEGE3 | WEG S.A. | 5410 | não financeira |
| 2 | BBAS3 | BCO BRASIL S.A. | 1023 | banco |
| 3 | ZAMP3 | ZAMP SA | 24317 | não financeira |
| 4 | LWSA3 | LWSA S/A | 24910 | não financeira |
| 5 | VALE3 | VALE S.A. | 4170 | não financeira |
| 6 | ITUB4 | ITAU UNIBANCO HOLDING S.A. | 19348 | banco |
| 7 | LAVV3 | LAVVI EMPREENDIMENTOS IMOBILIÁRIOS S.A. | 25062 | não financeira |
| 8 | POMO4 | MARCOPOLO S.A. | 8451 | não financeira |
| 9 | ITSA4 | ITAÚSA S.A. | 7617 | holding |
| 10 | IRBR3 | IRB - BRASIL RESSEGUROS S.A. | 24180 | resseguradora |
| 11 | CEAB3 | C&A MODAS S.A. | 24848 | não financeira |
| 12 | AURE3 | AUREN ENERGIA S.A. | 26620 | não financeira |

A execução usará os códigos CVM acima diretamente. Isso evita a resolução de ticker via
cadastro FCA, que gravaria entradas novas (CEAB3, AURE3) em `dados/ticker_map.csv`,
arquivo versionado.

AURE3, LWSA3, VALE3 e POMO4 permanecem na amostra embora a demonstração de resultado não
esteja no contexto recuperado (Seção 6). Essa ausência é uma característica do sistema
avaliado e será medida, não contornada.

## 4. Período e versões

- Documento: ITR, `DT_REFER = 2026-06-30`, versão mais recente disponível.
- Versões observadas no inventário de 2026-09-27 (ZIP de dados abertos da CVM e índice
  local `dados/meta_itr_2026.csv`, concordantes): **VALE3 v3, ITSA4 v2, IRBR3 v2; demais
  v1.**
- Escala declarada pela CVM (`ESCALA_MOEDA`): **MIL** nas 12.
- SHA-256 esperado do documento gerado por `cvm.baixar_documento` (formato CD_CONTA):

| Ticker | Versão | SHA-256 do documento |
|---|---|---|
| WEGE3 | 1 | `500d0c0d51df24cf9d0a166c24f3eea033b74a6eb63285cc4349036857bb8ba6` |
| BBAS3 | 1 | `96c321232278beb5eb5a4eff167b5cedf76611b55e47f8ccb62c6c051c96bde8` |
| ZAMP3 | 1 | `044d8ad11f532cc3f65127a798d06bd689aad50f20da38a0b42e80d0f3bcf983` |
| LWSA3 | 1 | `e088ffd53f2899ddef5f70e3e30a8b57a33b087767c040f93171a7dc7458eb26` |
| VALE3 | 3 | `32b625e17d4b90aac9575bac7995e0b5c0b07a64edb466da3d5f2ac6c306c470` |
| ITUB4 | 1 | `409ed7c7a7a4cc56caf4ac54c5bf0914955e48668b0ad9c10c892c67374811a0` |
| LAVV3 | 1 | `7d18d8725fd03ffc05c327335ce50ec1c8629fb680a2b76129fe7cebbf8dddf2` |
| POMO4 | 1 | `79bba9fbcdeed51b959826ca83d1ad7e2d2e5dda21d352754df598f40da9d43b` |
| ITSA4 | 2 | `f252b1eb14ee6e5c1ff7ee142e0d39be6e397cd822a920397c544303857464c6` |
| IRBR3 | 2 | `e528959c4a2cf094c27a669988b54b6add6e733cdb6755961bb6287493cfd5ea` |
| CEAB3 | 1 | `1dece32b1e39f0a1474f5cc95543d762eac066d691859792fbbb3214dba72511` |
| AURE3 | 1 | `9a3f3625a0e1e2603d67fddbed4436c8d46774ff647a717d4973847de678bd8b` |

Os hashes de WEGE3, BBAS3 e ZAMP3 coincidem com os das execuções congeladas da
validação manual; o de LWSA3 coincide com a fixture de testes.

**Regra de versão.** Se, na data da coleta, a CVM tiver publicado uma versão mais nova
de algum desses ITRs, ou se o documento gerado tiver SHA-256 diferente do registrado, a
coleta **não começa**: o fato é registrado e a decisão (manter a versão registrada ou
adotar a nova e refazer a classificação de disponibilidade) é tomada antes de qualquer
resposta ser gerada.

## 5. Arquitetura avaliada

Fluxo idêntico ao do TCC 1 (`avaliacao/coletar_respostas.py`):

```
pergunta → recuperar_contexto(ticker, "ITR", "2026-06-30") → contexto numérico (3 tabelas)
         → resposta direta do LLM (prompt do TCC 1) → Faithfulness + Answer Relevancy
```

- **Contexto passado ao LLM:** o contexto numérico devolvido por `recuperar_contexto`.
- **Contexto passado ao RAGAS** (`retrieved_contexts`): os trechos desse mesmo contexto,
  separados como no TCC 1 (`extrair_chunks`).
- **Modelo gerador:** `gemini-2.5-flash` (`config.MODELO_LLM`), temperatura 0,1,
  `max_output_tokens` 1024, como no TCC 1.
- **Prompt de resposta direta:** o mesmo texto do TCC 1, sem acréscimos. A única
  diferença está nos enunciados das perguntas, que nomeiam a empresa e o período.

  > Você é um analista financeiro. Com base EXCLUSIVAMENTE nos trechos abaixo, responda à
  > pergunta de forma objetiva e em português.
  >
  > Nota: "Receita de Venda de Bens e/ou Serviços" equivale à "Receita Líquida" para fins
  > de análise.
  >
  > ## TRECHOS DO DOCUMENTO
  > {contexto numérico}
  >
  > ## PERGUNTA
  > {pergunta}

- **Fora do fluxo avaliado:** `analisar()`, `calcular_metricas`, Prompt 1, Prompt 2,
  auditor e narrativa.

## 6. Recuperação congelada

A recuperação é parte do sistema avaliado e **não será alterada**:

- `recuperacao.QUERY_NUMERICO` atual (consulta fixa, independente da pergunta);
- `config.MAX_CHUNKS_NUMERICO = 3` (top-k = 3);
- `recuperar_contexto`, `_contextos`, `_base_principal` e `_recuperar_canal` atuais;
- `chunking.criar_chunks` e `_limpar_tabela` atuais (uma tabela inteira por chunk);
- embeddings `paraphrase-multilingual-mpnet-base-v2` (`config.MODELO_EMBEDDINGS`);
- estrutura do índice ChromaDB (uma coleção por ticker/tipo/período; metadados
  `tipo`, `secao`, `base`).

Como a consulta é fixa, o contexto de uma empresa é o mesmo para as 8 perguntas. No
inventário, duas chamadas seguidas devolveram texto idêntico nas 12 empresas.

**Contexto observado no inventário de 2026-09-27** (índice recriado do zero; ordem de
recuperação):

| Ticker | 1º | 2º | 3º | Tabela consolidada fora do contexto | Caracteres |
|---|---|---|---|---|---|
| WEGE3 | BP Ativo | DFC | DRE | BP Passivo | 10.620 |
| BBAS3 | DRE | BP Passivo | BP Ativo | DFC | 8.807 |
| ZAMP3 | BP Ativo | DFC | DRE | BP Passivo | 8.541 |
| LWSA3 | DFC | BP Ativo | BP Passivo | DRE | 10.706 |
| VALE3 | DFC | BP Ativo | BP Passivo | DRE | 12.768 |
| ITUB4 | DRE | BP Passivo | BP Ativo | DFC | 9.096 |
| LAVV3 | DFC | BP Ativo | DRE | BP Passivo | 11.101 |
| POMO4 | BP Ativo | DFC | BP Passivo | DRE | 12.210 |
| ITSA4 | DFC | BP Ativo | DRE | BP Passivo | 10.918 |
| IRBR3 | DFC | BP Ativo | DRE | BP Passivo | 9.313 |
| CEAB3 | BP Ativo | DFC | DRE | BP Passivo | 9.350 |
| AURE3 | DFC | BP Ativo | BP Passivo | DRE | 14.204 |

Resumo:

- sempre 3 das 4 tabelas consolidadas;
- **BP Ativo presente nas 12**;
- **DRE ausente em LWSA3, VALE3, POMO4 e AURE3**;
- **BP Passivo ausente em WEGE3, ZAMP3, LAVV3, ITSA4, IRBR3 e CEAB3**;
- DFC ausente nos dois bancos;
- DRE e BP Passivo juntos só em BBAS3 e ITUB4.

## 7. Núcleo comum — N1 a N5 (as 12 empresas)

A linha contábil de cada categoria é escolhida pelo **plano de contas** da demonstração
(comercial/industrial, instituição financeira, seguradora), nunca por regra específica
de ticker.

| Cat. | Conteúdo | Tipo | Adaptação por estrutura |
|---|---|---|---|
| **N1** | Linha de topo da DRE no período atual (1S26) | factual | não financeiras e holding: Receita de Venda de Bens e/ou Serviços; bancos: Receitas de Intermediação Financeira; resseguradora: Receitas das Atividades Seguradoras/Resseguradoras |
| **N2** | Lucro ou prejuízo **consolidado** do período atual | factual | o enunciado pede explicitamente o resultado consolidado, não o atribuído aos controladores |
| **N3** | Variação do resultado consolidado em relação ao período comparável (1S25) | comparativa | ver regra de percentual abaixo |
| **N4** | Principais componentes contábeis da DRE que explicam a variação do resultado | interpretativa | ver cadeias abaixo; **a DFC não é explicação causal do lucro** |
| **N5** | Caixa e equivalentes de caixa no período atual (30/06/2026) | factual | linha "Caixa e Equivalentes de Caixa" do BP Ativo em todas as estruturas |

**Decisão registrada antes da coleta.** O N5 era, na proposta inicial, o patrimônio
líquido. Foi substituído por caixa e equivalentes porque o inventário mostrou o PL no
contexto de apenas 6 das 12 empresas, enquanto o BP Ativo está presente nas 12. A troca
foi feita com base apenas na composição do contexto, antes de qualquer resposta ou score.

**Regra de percentual para N3.** O percentual de variação é esperado quando os dois
períodos têm o mesmo sinal e o anterior é diferente de zero. Com dois prejuízos, a
variação é expressa sobre a magnitude ("prejuízo X% maior/menor"). Com mudança de sinal
ou anterior igual a zero, esperam-se a direção e os dois valores, sem percentual. No
inventário, nenhuma das 12 empresas muda de sinal no resultado consolidado.

**Cadeias para N4:**

- **Comercial/industrial e holding:** resultado antes do resultado financeiro e dos
  tributos → resultado financeiro → resultado antes dos tributos → IR/CS → operações
  descontinuadas (quando diferentes de zero) → resultado consolidado. Na holding, a
  equivalência patrimonial é componente do resultado operacional.
- **Banco:** resultado bruto da intermediação financeira → outras despesas e receitas
  operacionais (incluindo, quando ali classificada, a provisão para perda de crédito) →
  resultado antes dos tributos → IR/CS → resultado consolidado.
- **Resseguradora:** resultado bruto das operações de resseguro → despesas
  administrativas e outras → resultado antes do resultado financeiro e dos tributos →
  resultado financeiro → resultado antes dos tributos → IR/CS → resultado consolidado.

## 8. Perguntas específicas — E1 a E3

| Estrutura | Empresas | E1 | E2 | E3 |
|---|---|---|---|---|
| Não financeira | WEGE3, ZAMP3, LWSA3, VALE3, LAVV3, POMO4, CEAB3, AURE3 | Margem líquida (resultado consolidado ÷ receita) | Caixa × empréstimos e financiamentos | Resultado financeiro (valor e evolução) |
| Banco | BBAS3, ITUB4 | Resultado bruto da intermediação financeira | Depósitos (captação) | Despesas de intermediação financeira |
| Holding | ITSA4 | Resultado de equivalência patrimonial | Caixa × dívida | Resultado financeiro |
| Resseguradora | IRBR3 | Resultado das operações de resseguro | Resultado financeiro / de investimentos | Aplicações financeiras |

Observações registradas:

- **Não financeiras.** O inventário mostra que E1, E2 e E3 não são respondíveis em todas
  as empresas, porque quatro recebem a DRE sem o BP Passivo e quatro recebem o BP
  Passivo sem a DRE. As categorias **não são substituídas** para caber no contexto; a
  disponibilidade é pré-registrada caso a caso (Seção 9).
- **Bancos, E3.** BBAS3 classifica a provisão para perda de crédito em "Outras Despesas
  e Receitas Operacionais"; ITUB4 a inclui nas "Despesas da Intermediação Financeira".
  **E3 não é um indicador comparável entre os dois bancos** e não será comparado entre
  eles.
- **Holding, E2.** Tem disponibilidade parcial: há caixa, mas o BP Passivo não está no
  contexto.
- **Resseguradora.** O PL não é usado porque o BP Passivo não está no contexto. E3 se
  refere às aplicações financeiras do BP Ativo. A linha "Despesas Financeiras" da IRBR3
  aparece positiva no período atual, como entregue à CVM.

**Redação dos enunciados** (a fazer depois deste protocolo, antes da coleta):

- nomear a empresa;
- nomear o período: "primeiro semestre de 2026" para DRE e DFC, "30 de junho de 2026"
  para o balanço;
- não usar "último trimestre" (o ITR de junho traz o acumulado do semestre);
- em N2 e N3, pedir o resultado consolidado;
- pedir exatamente os valores objetivos exigidos pela Seção 11.1 (por exemplo, em N3,
  os valores dos dois períodos e, quando a regra de percentual se aplica, a variação
  percentual).

A redação não pode mudar o conteúdo da categoria registrado aqui.

## 9. Classificação prévia da disponibilidade

Cada um dos 96 casos recebe, **antes da geração da resposta**, exatamente uma das
classes abaixo. A classe é determinada **exclusivamente pelo contexto recuperado**,
nunca pela resposta do modelo, por `metricas.py`, por conhecimento externo ou por
demonstração que não esteja no contexto.

| Classe | Definição |
|---|---|
| `presente` | O contexto contém as informações necessárias para responder corretamente à pergunta. |
| `parcial` | O contexto contém informação relacionada, mas insuficiente para uma resposta completa e segura. Exemplos: resultado antes dos tributos sem o resultado final; conceito disponível só em linha da DFC com sinal invertido; caixa presente e dívida ausente; apenas um dos insumos de um indicador derivado. |
| `ausente` | O contexto não contém a informação necessária. |

Regras de aplicação:

1. **Categorias de uma linha contábil** (todas, exceto N4, E1 margem líquida e E2 caixa
   × dívida): `presente` se a linha do conceito pedido está no contexto, nos períodos que
   a pergunta exige; `parcial` se só há um conceito vizinho (por exemplo, resultado antes
   dos tributos no lugar do resultado final); `ausente` caso contrário. N3 exige o
   resultado consolidado nos dois períodos.
2. **N2 e N3 pela DFC.** Uma linha da DFC consolidada que traz o **resultado do
   período** (não o resultado antes dos tributos) conta como `presente` para N2 e N3.
   É o caso da POMO4 ("Resultado do período", igual ao resultado consolidado da DRE).
3. **"Lucros/Prejuízos Acumulados" do BP Passivo** não conta como resultado do período.
4. **Indicadores derivados** (E1 margem, E2 caixa × dívida): `presente` com todos os
   insumos no contexto; `parcial` com parte deles; `ausente` sem nenhum.
5. **N4.** Nós da cadeia: resultado operacional, resultado financeiro, resultado antes
   dos tributos, IR/CS, descontinuadas e resultado consolidado, cada um nos dois
   períodos.
   - `presente` se a DRE está no contexto;
   - `parcial` se ao menos dois nós aparecem em outra tabela, inclusive com sinal
     invertido;
   - `ausente` com um nó ou nenhum.
6. **Sinal contábil invertido** (valores da DFC somados de volta, como o resultado
   financeiro da VALE3 e o IR/CS da POMO4) nunca torna o caso `presente`.
7. **Registro.** A classificação é feita pelo autor, por categoria, com a justificativa
   (tabela e linhas usadas) gravada no dataset. Ela é congelada junto com as perguntas e
   os gabaritos, **antes** da primeira resposta.
8. **Conferência.** Se, na execução, o contexto recriado diferir do inventariado (outra
   ordem, outras tabelas ou outro SHA-256 do documento), a classificação é refeita sobre
   o contexto efetivo antes de qualquer resposta, e a divergência é registrada.

**Classificação esperada**, derivada do inventário de 2026-09-27 (P = presente,
Pa = parcial, A = ausente):

| Ticker | N1 | N2 | N3 | N4 | N5 | E1 | E2 | E3 | P | Pa | A |
|---|---|---|---|---|---|---|---|---|---|---|---|
| WEGE3 | P | P | P | P | P | P | Pa | P | 7 | 1 | 0 |
| BBAS3 | P | P | P | P | P | P | P | P | 8 | 0 | 0 |
| ZAMP3 | P | P | P | P | P | P | Pa | P | 7 | 1 | 0 |
| LWSA3 | A | Pa | Pa | A | P | A | P | A | 2 | 2 | 4 |
| VALE3 | A | Pa | Pa | Pa | P | A | P | Pa | 2 | 4 | 2 |
| ITUB4 | P | P | P | P | P | P | P | P | 8 | 0 | 0 |
| LAVV3 | P | P | P | P | P | P | Pa | P | 7 | 1 | 0 |
| POMO4 | A | P | P | Pa | P | Pa | P | A | 4 | 2 | 2 |
| ITSA4 | P | P | P | P | P | P | Pa | P | 7 | 1 | 0 |
| IRBR3 | P | P | P | P | P | P | P | P | 8 | 0 | 0 |
| CEAB3 | P | P | P | P | P | P | Pa | P | 7 | 1 | 0 |
| AURE3 | A | Pa | Pa | A | P | A | P | A | 2 | 2 | 4 |
| **Total** | | | | | | | | | **69** | **15** | **12** |

Justificativas dos casos não `presente`:

- **LWSA3, VALE3 e AURE3, N2 e N3 (`parcial`):** só há o resultado antes dos tributos,
  na DFC.
- **VALE3, N4 (`parcial`):** a DFC traz o resultado antes dos tributos e o resultado
  financeiro com sinal invertido.
- **VALE3, E3 (`parcial`):** mesma linha da DFC, com sinal invertido.
- **POMO4, N4 (`parcial`):** a DFC traz o resultado do período e o IR/CS com sinal
  invertido.
- **POMO4, E1 (`parcial`):** o resultado está no contexto, a receita não.
- **E2 de WEGE3, ZAMP3, LAVV3, CEAB3 e ITSA4 (`parcial`):** há caixa, mas não a dívida.
- **LWSA3 e AURE3, N4 (`ausente`):** um único nó da cadeia (o resultado antes dos
  tributos).
- **LWSA3, VALE3, POMO4 e AURE3, N1 (`ausente`), e LWSA3, VALE3 e AURE3, E1
  (`ausente`):** sem a DRE, falta a receita e o resultado consolidado está ausente ou
  só parcial.
- **LWSA3, POMO4 e AURE3, E3 (`ausente`):** nenhuma linha de resultado financeiro no
  contexto.

## 10. Questões de avaliação

- **Q1 — Informação presente.** Nos casos `presente`, as respostas são fiéis ao contexto
  e relevantes para a pergunta (RAGAS), e seus valores objetivos conferem com o
  gabarito (verificação determinística, Seção 11.1)?
- **Q2 — Informação parcial.** Nos casos `parcial`, o sistema reconhece a limitação,
  responde parcialmente, extrapola ou inventa?
- **Q3 — Informação ausente.** Nos casos `ausente`, o sistema se abstém corretamente,
  informa que os dados não estão disponíveis ou produz informação sem suporte?
- **Q4 — Estruturas contábeis.** O desempenho difere entre não financeiras (8), bancos
  (2), holding (1) e resseguradora (1)?
- **Q5 — Recuperação.** Quais falhas decorrem da geração (caso `presente` com resposta
  inadequada) e quais decorrem da ausência, entre as três tabelas recuperadas, da
  demonstração necessária (casos `parcial` e `ausente`)?

Não há hipóteses estatísticas formais. Os subgrupos são pequenos (holding e resseguradora
com 8 casos cada; 15 casos `parcial` e 12 `ausente` esperados) e não sustentam testes
inferenciais. As questões serão respondidas descritivamente.

## 11. Métricas RAGAS e verificação complementar

Métricas RAGAS principais, as mesmas do TCC 1:

1. **Faithfulness.** O avaliador decompõe a resposta em afirmações e julga, uma a uma,
   se cada afirmação pode ser inferida do contexto recuperado. O score é a fração de
   afirmações sustentadas (0 a 1). Não usa gabarito.
2. **Answer Relevancy.** O avaliador gera perguntas que a resposta responderia. O score
   é a similaridade média, por embeddings, entre essas perguntas e a pergunta original.
   Respostas classificadas como evasivas recebem 0. Não usa gabarito.

Implementação pretendida, idêntica à de `avaliacao/rodar_ragas.py` do TCC 1:

| Item | Valor |
|---|---|
| Biblioteca | `ragas==0.4.3` |
| Faithfulness | `ragas.metrics._faithfulness.Faithfulness(llm=...)` |
| Answer Relevancy | `ragas.metrics._answer_relevance.AnswerRelevancy(llm=..., embeddings=...)` (parâmetros padrão) |
| Amostra | `ragas.dataset_schema.SingleTurnSample(user_input, response, retrieved_contexts, reference)` |
| Execução | `ragas.evaluate` sobre `EvaluationDataset` de 1 amostra; `RunConfig(timeout=120, max_retries=3, max_workers=1)`; pausa de 10 s entre casos |
| LLM avaliador | `gemini-2.5-flash`, temperatura 0, via `langchain_google_genai.ChatGoogleGenerativeAI` + `ragas.llms.LangchainLLMWrapper` |
| Embeddings | `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`, via `langchain_community.embeddings.HuggingFaceEmbeddings` + `ragas.embeddings.LangchainEmbeddingsWrapper` |

**Estado do ambiente em 2026-09-27 (apenas documentado, nada instalado):**

- Python 3.12.6.
- `ragas`, `langchain_google_genai` e `langchain_community` **não estão instalados**
  (`ModuleNotFoundError`), como já indica o `requirements.txt`.
- Por isso as classes acima não puderam ser conferidas no ambiente atual; ficam
  registradas conforme o código do TCC 1.

**Incompatibilidades e pontos de atenção conhecidos**, registrados no cabeçalho de
`rodar_ragas.py` ou identificados na leitura do código:

1. O script importa **módulos privados** do ragas (`_faithfulness`, `_answer_relevance`)
   porque `ragas.metrics.collections` é incompatível com `evaluate()` na 0.4.3. Exige
   fixar exatamente `ragas==0.4.3`.
2. `langchain_community.chat_models.vertexai` foi removido no `langchain-community` ≥
   0.3; o script injeta um módulo substituto antes de importar o ragas.
3. `requirements.txt` fixa `langchain-community~=0.4.0`, mas deixa
   `langchain-google-genai>=2.0` **sem versão exata**. A versão efetivamente instalada
   será registrada em `pip freeze`.
4. `HuggingFaceEmbeddings` de `langchain_community` é uma classe antiga; nada será
   trocado sem emenda.
5. A retomada de `rodar_ragas.py` identifica casos pelo texto da pergunta. Com
   enunciados que se repetem entre empresas, casos seriam pulados em silêncio. A
   adaptação necessária (identificador de caso) é de entrada e saída e não altera as
   métricas.
6. O número de chamadas do Answer Relevancy depende do parâmetro `strictness` (padrão
   presumido: 3). Será conferido após a instalação e registrado.

Nenhum desses pontos é corrigido neste protocolo. Se algum tornar a configuração acima
tecnicamente impossível, a coleta não começa e a decisão é registrada como emenda.

**Medidas complementares (fora do RAGAS).** Duas medidas não substituem nem se misturam
aos scores RAGAS:

- a verificação determinística de exatidão numérica (Seção 11.1), aplicada a todos os
  casos;
- a classificação manual do comportamento das respostas `parcial` e `ausente` (Seção
  12).

### 11.1 Verificação determinística de exatidão numérica (complementar, fora do RAGAS)

**Natureza.** Verifica se os valores objetivos apresentados na resposta correspondem ao
gabarito extraído dos dados estruturados da CVM (Seção 13).

- É uma avaliação complementar de correção factual/numérica.
- **Não é uma métrica RAGAS**, não substitui Faithfulness nem Answer Relevancy, e não
  será combinada com elas em índice composto.
- Não usa LLM: a classificação é feita por parsing e comparação numérica.
- Usa o gabarito congelado antes da geração das respostas.

**Unidade de avaliação.** O caso (uma pergunta de uma empresa).

**Valores objetivos exigidos por categoria.** Cada gabarito lista, antes da coleta, os
valores exigidos, as contas CVM de origem e as formas aceitas (total ou parcelas). O
enunciado de cada pergunta pede exatamente esses valores.

| Categoria | Estrutura | Valores exigidos |
|---|---|---|
| N1 | todas | linha de topo do 1S26 |
| N2 | todas | resultado consolidado do 1S26, com sinal |
| N3 | todas | resultado consolidado do 1S26 e do 1S25, com sinal; variação percentual quando a regra da Seção 7 a prevê |
| N4 | todas | nenhum: **`NAO_APLICAVEL` por definição** (pergunta interpretativa) |
| N5 | todas | caixa e equivalentes de caixa em 30/06/2026 |
| E1 | não financeira | margem líquida do 1S26 (%) |
| E2 | não financeira, holding | caixa e equivalentes e empréstimos e financiamentos (circulante + não circulante) em 30/06/2026; a dívida é aceita como total ou como as duas parcelas |
| E3 | não financeira, holding | resultado financeiro do 1S26 e do 1S25, com sinal |
| E1 | holding | resultado de equivalência patrimonial do 1S26 |
| E1 | banco | resultado bruto da intermediação financeira do 1S26 |
| E2 | banco | depósitos em 30/06/2026 |
| E3 | banco | despesas da intermediação financeira do 1S26 |
| E1 | resseguradora | resultado bruto das operações de resseguro do 1S26, com sinal |
| E2 | resseguradora | resultado financeiro do 1S26, com sinal |
| E3 | resseguradora | aplicações financeiras em 30/06/2026, nas contas e formas definidas no gabarito |

**Regras de leitura dos números da resposta**, fixas e reproduzíveis:

1. **Formato numérico.** Formato brasileiro: ponto separa milhares e vírgula separa
   decimais. Exceção: um número com ponto seguido de exatamente 10 dígitos (o formato
   não normalizado presente em algumas linhas do contexto, como `-34397820.0000000000`)
   é lido com o ponto como separador decimal.
2. **Multiplicadores explícitos:** "mil"; "milhão/milhões/mi/MM";
   "bilhão/bilhões/bi"; "trilhão/trilhões/tri". O valor é convertido para reais antes
   da comparação.
3. **Escala implícita.** Um número monetário sem multiplicador explícito (com ou sem
   "R$") é lido na escala da fonte, **R$ mil**, porque o contexto não declara a unidade
   e o modelo não tem como conhecê-la. O caso recebe a marca `escala_implicita`, que é
   registrada, mas não muda a classe. Um multiplicador explícito errado (por exemplo,
   "milhões" onde a fonte indica bilhões) não é escala implícita: o valor simplesmente
   não confere.
4. **Percentuais.** Números seguidos de "%" ou "por cento", comparados só com valores
   percentuais do gabarito, por valor absoluto (a direção de uma variação entre
   prejuízos é ambígua em percentual).
5. **Sinal**, verificado apenas para valores que o gabarito marca "com sinal":
   - o valor é negativo se tiver "-" ou "−", estiver entre parênteses, ou estiver na
     mesma oração que "prejuízo", "negativo" ou "déficit";
   - com sinal divergente do gabarito, o valor não confere;
   - se a regra não for conclusiva (por exemplo, a oração qualifica mais de um valor), o
     sinal é decidido manualmente, e o caso recebe a marca `sinal_revisao_manual`, com
     registro da decisão.
6. **Arredondamento.** Seja *v* o valor apresentado, com *k* casas decimais na unidade
   em que foi escrito, e *g* o valor do gabarito convertido para essa mesma unidade, em
   precisão integral. O valor **confere** se *v* for igual a *g* arredondado para *k*
   casas (meio para cima) **ou** a *g* truncado em *k* casas.
   - Exemplo: *g* = 9.468.313 mil = 9,468313 bilhões. Conferem "R$ 9,47 bilhões",
     "R$ 9,46 bilhões", "R$ 9.468,3 milhões" e "9.468.313"; não confere "R$ 9,5 mil".
   - Diferenças exclusivamente de arredondamento não são erro.
   - Nenhuma outra tolerância é aplicada.
7. **Conciliação.** Cada valor exigido é **encontrado** se algum número da resposta
   conferir com ele pelas regras 1–6. Cada número da resposta concilia no máximo um valor
   exigido. Números da resposta que não conciliam nenhum valor exigido são listados
   (`valores_nao_conciliados`) para inspeção, sem alterar a classe.

**Classes:**

| Classe | Regra |
|---|---|
| `CORRETO` | todos os valores exigidos foram encontrados |
| `PARCIALMENTE_CORRETO` | ao menos um valor exigido foi encontrado e ao menos um não (omissão ou erro) |
| `INCORRETO` | nenhum valor exigido foi encontrado e a resposta apresenta ao menos um número monetário ou percentual (valor incompatível com o gabarito) |
| `NAO_APLICAVEL` | categoria N4; ou resposta sem nenhum número monetário ou percentual (por exemplo, abstenção) |

**Relação com a disponibilidade.** A verificação é aplicada aos 96 casos. A leitura,
porém, depende da classe de disponibilidade (Seção 9), e cinco registros são mantidos
separados em cada caso:

1. disponibilidade (`presente`/`parcial`/`ausente`);
2. comportamento, avaliado manualmente (apenas `parcial` e `ausente`);
3. exatidão determinística;
4. Faithfulness;
5. Answer Relevancy.

Consequências:

- **Abstenção correta** num caso `parcial` ou `ausente` recebe `NAO_APLICAVEL` e não é
  contada como erro numérico.
- **`INCORRETO` em caso `parcial` ou `ausente`** indica valor sem suporte e é lido junto
  com a classificação de comportamento.
- **`CORRETO` em caso `ausente`** (valor que confere com a fonte, mas não está no
  contexto) é reportado à parte, como correto sem suporte no contexto, e não como
  acerto do sistema.
- Casos `presente` com `INCORRETO` ou `PARCIALMENTE_CORRETO` são atribuídos à geração;
  as falhas em casos `parcial` ou `ausente` são lidas à luz da recuperação (Q5).

**Implementação e congelamento.**

- A verificação é um script determinístico.
- Seus testes unitários, sobre respostas sintéticas, cobrem: escalas, escala implícita,
  arredondamento e truncamento, sinal, percentuais, o formato não normalizado da regra
  1 e abstenção.
- Script e testes são **commitados antes da coleta**.
- Qualquer mudança depois de ver as respostas só entra por emenda, e os resultados da
  versão original também são reportados.
- A verificação roda depois da coleta. As decisões manuais de sinal são tomadas antes
  do RAGAS, junto com a classificação de comportamento.

Pelo inventário, 69 casos são `presente`. Os 8 N4 `presente` são `NAO_APLICAVEL` por
definição, então até **61 casos `presente`** entram na taxa de exatidão, menos os que se
tornarem `NAO_APLICAVEL` por não trazerem números.

## 12. Estratégia de análise

Todas as estatísticas são descritivas. Não há testes estatísticos ou inferenciais.

- Um score RAGAS é **válido** quando a métrica foi calculada (não NaN); casos inválidos
  são contados e reportados, nunca imputados.
- Na exatidão determinística, o denominador da taxa de `CORRETO` é o número de casos
  **aplicáveis** (`CORRETO` + `PARCIALMENTE_CORRETO` + `INCORRETO`); `NAO_APLICAVEL` é
  contado e reportado à parte, separando N4 de respostas sem número.
- As medidas podem ser apresentadas lado a lado, em uma mesma tabela, mas **nunca
  combinadas** em índice único. Cada uma é reportada com seu próprio n.

1. **Resultado global.**
   - Faithfulness e Answer Relevancy sobre todos os casos válidos (até 96): média,
     mediana, desvio-padrão, mínimo, máximo e n válido.
   - Distribuição das quatro classes de exatidão.
2. **Análise principal (Q1): casos `presente`.** É a leitura principal da qualidade
   das respostas quando o contexto contém a informação. Para esses casos:
   - Faithfulness e Answer Relevancy com as mesmas estatísticas e n válido;
   - taxa de `CORRETO` sobre os casos aplicáveis, com o n;
   - contagem de `PARCIALMENTE_CORRETO`, `INCORRETO` e `NAO_APLICAVEL`;
   - tabela descritiva de Faithfulness e Answer Relevancy por classe de exatidão (por
     exemplo, a distribuição de Faithfulness entre as respostas `CORRETO`). Serve para
     verificar, em escala, a observação do TCC 1 de que Faithfulness penaliza respostas
     numericamente corretas.
3. **Análise secundária (Q2, Q3): casos `parcial` e `ausente`, separados entre si.**
   - Scores RAGAS com as mesmas estatísticas.
   - Distribuição das classes de exatidão, lida conforme a Seção 11.1: abstenção não é
     erro numérico; `CORRETO` em caso `ausente` é reportado à parte.
   - Classificação manual do comportamento de cada resposta em uma de quatro classes:
     **abstenção adequada**, **resposta parcial adequada**, **extrapolação**,
     **alucinação/informação sem suporte**.
   - A classificação segue uma rubrica escrita e congelada junto com o dataset, e é
     feita **depois da coleta e antes de rodar o RAGAS**, para não ser influenciada
     pelos scores.
   - Esses casos não entram na conclusão principal sobre capacidade factual.
4. **Cortes adicionais** das três medidas (Faithfulness, Answer Relevancy e exatidão),
   sempre com o n de cada célula:
   - presente × parcial × ausente;
   - por estrutura contábil;
   - por categoria (N1–N5, E1–E3);
   - por empresa.

   Células com menos de 5 casos válidos são apresentadas caso a caso, sem média
   interpretada como tendência. E3 dos bancos não é comparado entre BBAS3 e ITUB4.
5. **Q5.** Uma resposta é inadequada se tiver exatidão `INCORRETO` ou
   `PARCIALMENTE_CORRETO`, ou comportamento de extrapolação ou alucinação. Os casos
   com resposta inadequada são atribuídos a:
   - geração (caso `presente`);
   - recuperação (caso `parcial` ou `ausente`).

   A atribuição usa a classificação prévia, e não a resposta.
6. **Revisão manual dos piores casos.** São revistos:
   - em cada métrica RAGAS, os casos `presente` no decil inferior e todos com score 0;
   - todos os casos `presente` com exatidão `INCORRETO` ou `PARCIALMENTE_CORRETO`.

   Cada caso revisto é classificado por causa provável:
   - avaliador não reconheceu valor correto;
   - resposta incorreta;
   - resposta evasiva;
   - problema de formato no contexto (por exemplo, número sem formatação ou sinal
     atípico).
7. **Sem limiares arbitrários.** Nenhum corte do tipo "acima de 0,8 é bom" será usado.

## 13. Ground truth

As duas métricas RAGAS **não usam o gabarito**. O gabarito serve a:

- a verificação determinística de exatidão (Seção 11.1);
- a classificação de comportamento (Seção 12);
- a revisão dos piores casos;
- a auditoria posterior.

1. **Fonte.** Dados estruturados da CVM do ITR registrado (arquivos
   `itr_cia_aberta_*_2026.csv`, `DT_REFER = 2026-06-30`, versão da Seção 4), por conta
   (`CD_CONTA`, `DS_CONTA`), valor, período (`ÚLTIMO`/`PENÚLTIMO`; acumulado do ano na DRE
   e na DFC) e versão.
2. **Independência.** O gabarito **não copia** a saída de `calcular_metricas`,
   `decomposicao_resultado` ou qualquer módulo do pipeline avaliado. É produzido por
   procedimento próprio sobre os CSVs, para evitar circularidade.
3. **Campos por caso:**
   - valor em R$ mil e em forma legível;
   - código e nome da conta;
   - período atual e comparável;
   - versão e SHA-256 do documento;
   - fórmula (se derivado);
   - classe de disponibilidade;
   - valores objetivos exigidos para a exatidão (Seção 11.1): se exigem sinal e quais
     formas são aceitas (total ou parcelas);
   - texto curto de referência.
4. **Referências de período, explícitas em cada gabarito:**
   - DRE e DFC: 1S26 (01/01 a 30/06/2026) contra **1S25**;
   - balanço: **30/06/2026** contra **31/12/2025**.
5. **Derivados** (margem, variação, caixa × dívida): calculados deterministicamente a
   partir das contas CVM, com fórmula registrada e precisão integral preservada; o
   arredondamento só aparece no texto.
6. **N4.** O gabarito lista **todos** os nós da cadeia da Seção 7 com os valores nos
   dois períodos, a variação de cada um e o sinal. Os componentes são ordenados por
   magnitude da variação, sem exigir redação única. A DFC não é usada como explicação
   causal.
7. **Casos `parcial` e `ausente`.** O gabarito registra a resposta correta segundo a
   fonte CVM e, separadamente, o que o contexto permite afirmar.
8. **Revisão.** Revisão manual de **100% dos 96 gabaritos** antes da execução do RAGAS e
   antes da primeira resposta. O dataset (perguntas, classes, gabaritos) é congelado com
   SHA-256.

## 14. Comparação com o TCC 1

| | TCC 1 | TCC 2 (planejado) |
|---|---|---|
| Empresas | 3 (WEGE3, LWSA3, LAVV3) | 12 |
| Documento | ITR 31/03/2026 | ITR 30/06/2026, versão mais recente |
| Casos | 15 (5 por empresa) | 96 (8 por empresa) |
| Perguntas | escritas à mão, específicas por empresa | 5 categorias comuns + 3 por estrutura contábil |
| Disponibilidade no contexto | não registrada | classificada antes da coleta |
| Faithfulness médio | 0,4375 (≈ 0,44) | — |
| Answer Relevancy médio | 0,8064 (≈ 0,81) | — |
| Faithfulness mediano | 0,33 (5 de 15 casos com 0) | — |
| Answer Relevancy mediano | 0,87 | — |

A comparação será **descritiva**, não experimental. Mudaram a amostra, o período, as
perguntas, o número de casos, possivelmente as versões de bibliotecas e do modelo, e o
desenho (classificação de disponibilidade). Nenhuma diferença de score será atribuída
exclusivamente às correções feitas no pipeline durante o TCC 2. As correções de
causalidade e de arrendamentos, em particular, atuam em `calcular_metricas` e no
Prompt 2, que estão fora do fluxo avaliado.

Correção de enquadramento em relação ao texto do TCC 1: Faithfulness e Answer Relevancy
medem a resposta dada o contexto recuperado, e não a qualidade da recuperação em si. Com
consulta fixa, o contexto não depende da pergunta. No TCC 2 o objeto será descrito como
"recuperação atual + resposta direta".

## 15. Reprodutibilidade

A execução deverá:

1. **Recriar os índices das 12 empresas do zero** (coleção excluída e recriada), a
   partir dos documentos da Seção 4. Não reutilizar coleções existentes do
   `chroma_db/`: o nome da coleção (`fundia_{ticker}_itr_2026-06-30`) não identifica a
   versão do documento, e o inventário encontrou coleções antigas de origem não
   verificável.
2. Gerar os documentos pelo `cvm.baixar_documento` do commit de referência, com versão
   explícita, sem `analisar()` e sem gerar narrativa.
3. Registrar por empresa:
   - código CVM, versão e SHA-256 do documento;
   - ordem e título das tabelas recuperadas;
   - SHA-256 do contexto numérico completo e de cada trecho.
4. Registrar por caso:
   - identificador do caso, ticker, companhia, período, versão;
   - categoria, estrutura e classe de disponibilidade;
   - pergunta, resposta, gabarito e contextos;
   - modelo gerador e modelo avaliador (identificadores retornados pela API);
   - temperaturas;
   - data e hora de geração e de avaliação;
   - tentativas e erro;
   - Faithfulness e Answer Relevancy;
   - exatidão: classe, valores encontrados e não encontrados, valores não
     conciliados, marcas `escala_implicita` e `sinal_revisao_manual`, e decisões
     manuais de sinal.
5. Congelar, cada um com SHA-256 e antes da etapa seguinte:
   - o dataset;
   - o script de exatidão e seus testes (antes da coleta);
   - as respostas e os contextos;
   - a classificação de comportamento e as decisões manuais de sinal;
   - os resultados da exatidão;
   - os resultados RAGAS;
   - `pip freeze` do ambiente de avaliação;
   - o commit do código.
6. **Não alterar arquivos versionados durante a coleta.** O ticker não é resolvido pelo
   cadastro FCA (Seção 3), e `dados/ticker_map.csv` não é tocado.
7. A chave da API é lida em tempo de execução e nunca gravada em artefato.
8. **Aleatoriedade conhecida:**
   - geração a temperatura 0,1, sem semente;
   - avaliador a temperatura 0, o que não garante determinismo.

   Cada caso é gerado e avaliado **uma única vez**. Casos com NaN após as 3 tentativas
   internas podem ser reavaliados **uma vez**, em passada separada e registrada. Se
   persistirem, são reportados como inválidos.
9. **Não há piloto real.** Um teste técnico dos scripts pode ser feito antes da coleta,
   sem consumir a API sempre que possível (respostas e chamadas simuladas). Seus
   resultados não fazem parte dos 96 casos e não são analisados.
10. **Avaliador único.** A classificação de comportamento e as decisões manuais de sinal
    são feitas pelo autor, sem segundo avaliador.

## 16. Limitações conhecidas

1. **O RAGAS não avalia a narrativa final** (Seção 2).
2. **Contexto fixo por empresa.** A consulta não depende da pergunta, e a composição de
   3 tabelas varia entre empresas. 27 dos 96 casos são esperados como `parcial` ou
   `ausente`.
3. **Fragilidade do ranking.** A distância entre a 3ª e a 4ª tabela é pequena em várias
   empresas (0,10 na POMO4). Mudanças no texto dos chunks podem trocar a tabela incluída,
   por isso o commit do código fica congelado.
4. **A AURE3 perde a característica que motivou sua escolha.** Ela entrou por ter
   prejuízo de origem operacional e IR/CS mudando de sinal; a DRE não é recuperada e
   isso não é observável neste experimento. O mesmo vale, em grau menor, para LWSA3,
   VALE3 e POMO4. Nenhuma delas será substituída.
5. **Contexto sem unidade e sem datas.** O contexto não informa a unidade monetária (R$
   mil) nem a data do valor "anterior" (1S25 na DRE e DFC; 31/12/2025 no balanço). Essa
   informação não será inserida no contexto sem emenda formal do desenho.
6. **Formatos numéricos mistos.** Linhas com nome de conta longo saem sem formatação:
   2 no BBAS3 e 4 no ITUB4 (por exemplo, `-34397820.0000000000`).
7. **Armadilhas quando falta a DRE:**
   - a DFC começa pelo resultado antes dos tributos na maioria das empresas;
   - valores somados de volta na DFC aparecem com sinal invertido (resultado financeiro
     da VALE3, IR/CS da POMO4);
   - "Lucros/Prejuízos Acumulados" pode coincidir com o resultado dos controladores
     (VALE3, AURE3) ou não (LWSA3);
   - na AURE3, esse valor (−1.032.285) é quase igual ao resultado antes dos tributos
     (−1.032.287).
8. **Sinal atípico** de "Despesas Financeiras" na IRBR3, como entregue.
9. **Heterogeneidade entre bancos** na classificação da provisão para perda de crédito
   (E3 não comparável).
10. **Mesmo modelo como gerador e avaliador** (`gemini-2.5-flash`): risco de
    autofavorecimento e fraqueza documentada em julgamento numérico sobre tabelas
    densas.
11. **Faithfulness pode penalizar respostas numericamente corretas** sobre tabelas
    densas, como observado no TCC 1 (receita da WEG, score 0,00).
12. **Amostra intencional.** Os resultados não estimam desempenho sobre a população de
    companhias abertas.
13. **Dependências de avaliação não instaladas**, com importação de módulos privados e
    uma dependência sem versão exata (Seção 11).
14. **Alcance da verificação de exatidão:**
    - confere apenas os valores exigidos: números adicionais da resposta são listados,
      mas não julgados;
    - não verifica a direção de variações descrita em palavras, o sinal de percentuais
      (comparados em valor absoluto) nem a explicação de N4;
    - a regra de sinal por palavras pode ser inconclusiva e depende de decisão manual
      registrada;
    - a escala implícita (R$ mil) é presumida quando a resposta não declara
      multiplicador.
15. **Avaliador único** para a classificação de comportamento e as decisões de sinal.

## 17. Critérios congelados antes da coleta

As decisões abaixo não serão alteradas depois do início da coleta, salvo por emenda
datada e justificada (cabeçalho). Nenhuma delas será revista com base em scores
observados.

- 12 empresas, as da Seção 3, com os códigos CVM ali listados.
- Período: ITR de 30/06/2026.
- Versão mais recente disponível de cada ITR (VALE3 v3, ITSA4 v2, IRBR3 v2, demais v1 no
  inventário), com a regra de versão da Seção 4.
- 8 perguntas por empresa, 96 casos.
- 5 categorias comuns: N1 linha de topo, N2 resultado consolidado, N3 variação do
  resultado, N4 componentes da variação, N5 caixa e equivalentes.
- 3 categorias específicas por estrutura, conforme a Seção 8.
- **N5 = caixa e equivalentes de caixa** (substitui o PL; decisão anterior à coleta).
- Recuperação atual do sistema, sem alterações.
- top-k = 3 (`MAX_CHUNKS_NUMERICO`).
- `QUERY_NUMERICO` atual.
- Chunking, índice e embeddings atuais; índices recriados do zero.
- Prompt de resposta direta do TCC 1, modelo gerador `gemini-2.5-flash`, temperatura
  0,1, `max_output_tokens` 1024.
- Classificação prévia `presente`/`parcial`/`ausente` pelas regras da Seção 9, feita
  exclusivamente sobre o contexto recuperado e congelada antes da primeira resposta.
- Métricas RAGAS: Faithfulness e Answer Relevancy, na implementação da Seção 11.
- **Verificação determinística de exatidão numérica** (Seção 11.1), complementar e fora
  do RAGAS, com estes elementos fixos:
  - valores exigidos por categoria;
  - regras de leitura, escala, sinal e arredondamento (arredondado **ou** truncado na
    precisão exibida, sem outra tolerância);
  - classes `CORRETO`/`PARCIALMENTE_CORRETO`/`INCORRETO`/`NAO_APLICAVEL`;
  - N4 como `NAO_APLICAVEL`;
  - sem LLM;
  - script e testes commitados antes da coleta.
- Disponibilidade, comportamento, exatidão, Faithfulness e Answer Relevancy registrados
  e reportados separadamente, sem índice composto.
- Gemini 2.5 Flash, temperatura 0, como avaliador.
- Embeddings `paraphrase-multilingual-mpnet-base-v2`.
- Análise principal nos casos `presente`: Faithfulness, Answer Relevancy e taxa de
  `CORRETO`, cada uma com seu n válido.
- Tratamento de NaN: sem imputação; no máximo uma reavaliação registrada; persistindo,
  o caso é inválido.
- Sem piloto real; teste técnico sem API sempre que possível, fora dos 96 casos.
- Casos `parcial` e `ausente` analisados separadamente, com classificação manual de
  comportamento feita antes do RAGAS.
- Ground truth extraído dos CSVs da CVM, independente de `calcular_metricas`, com
  revisão manual de 100%.
- Comparação com o TCC 1 apenas descritiva.
- Nenhuma empresa será removida ou substituída com base nos resultados ou na composição
  do contexto.
- Nenhuma pergunta será removida porque teve score ruim.
- Nenhuma categoria será redefinida depois de observar os scores.
- Nenhuma classificação de disponibilidade será alterada depois de observar as
  respostas.

---

## Emendas

### Emenda 1 — 2026-09-27 (antes da coleta)

**Momento.** Registrada antes da primeira resposta: nenhuma resposta foi gerada, nenhum LLM
foi chamado e nenhuma métrica RAGAS foi executada. O texto pré-registrado acima desta seção
não foi alterado.

**1. IRBR3_E3 — conta do gabarito.**
- *Decisão:* o gabarito de E3 da resseguradora usa só a conta `1.01.02 Aplicações
  Financeiras` (ativo circulante, R$ 4.414.934 mil em 30/06/2026). O enunciado pede o saldo
  de aplicações financeiras registrado no ativo circulante.
- *Motivo:* o gabarito reflete o conceito contábil explicitamente solicitado. É a única conta
  do ITR com DS_CONTA "Aplicações Financeiras"; as contas do realizável a longo prazo
  (`1.02.01.01` a `1.02.01.03`) são subcontas por categoria de mensuração, sem conta
  agregada de mesmo nome, e não são somadas por semelhança econômica.
- *Impacto:* substitui a definição usada na construção do dataset (circulante + longo prazo =
  R$ 8.353.283 mil). A disponibilidade do caso continua `presente`.

**2. Regras complementares do leitor de números (Seção 11.1).** Operacionalizam as regras 1–5
sem alterar escala, arredondamento, truncamento, percentuais nem classes.
- **A.** Não são números monetários: datas; anos isolados; códigos contábeis (3.01);
  períodos (1S25, 1S26); "Trecho N"; inteiros menores que 1000 sem R$, multiplicador, % ou
  casas decimais. Nenhum valor exigido do dataset é menor que 1000 em R$ mil.
- **B.** O "-" de marcador de lista no início da linha não é sinal.
- **C.** Parênteses não indicam sinal negativo por si. "(R$ 19,6 bilhões)" é reapresentação
  (positivo). Um número isolado entre parênteses tem sinal ambíguo: vai para decisão manual
  (`sinal_revisao_manual`), salvo se a oração o qualificar pela regra 5 (prejuízo, negativo,
  déficit). Isto substitui a leitura "entre parênteses = negativo" da regra 5.
- **D.** Número brasileiro seguido de pontuação ("R$ 9.468.313.") é lido inteiro.

**3. Rubrica de comportamento.**
- *Decisão:* a rubrica prevista na Seção 12 fica em `avaliacao/ragas/RUBRICA_COMPORTAMENTO_TCC2.md`,
  com a regra de decisão em `avaliacao/ragas/comportamento.py`. O classificador rotula cada
  afirmação da resposta (sustentada, extrapolada, alucinada, neutra); a classe sai
  deterministicamente desses rótulos.
- *Extensão:* a rubrica também é aplicada aos casos `presente`, para registrar extrapolação ou
  alucinação. Neles, a ausência de desvio é registrada como `SEM_DESVIO`, que não é uma quinta
  classe. A análise principal (Seção 12, item 2) não muda; as quatro classes continuam as
  previstas.
- *Momento de aplicação:* depois da coleta e antes do RAGAS, sem consultar scores (inalterado).

**4. Fim de linha.** `.gitattributes` passa a guardar `avaliacao/ragas/**` byte a byte
(`-text`), para que os SHA-256 dos artefatos não mudem com a conversão de fim de linha.

### Emenda 2 — 2026-09-28 (durante a coleta, antes das respostas 49–96)

**Momento.** Registrada depois de 48 das 96 respostas e antes de qualquer geração dos casos
restantes. Nenhuma resposta foi avaliada: não foram executados RAGAS, exatidão determinística
nem rubrica de comportamento. O texto pré-registrado e a Emenda 1 não foram alterados.

**1. Evento observado.**
- A coleta oficial começou com o executor congelado no commit `fb13ba8`
  (`avaliacao/ragas/coletar_respostas_tcc2.py`).
- Execução 1 (2026-09-28, 00:14–00:17 UTC): WEGE3 e BBAS3 concluídas (16 respostas). Antes de
  `ZAMP3_N1`, o executor detectou divergência entre o contexto recuperado e o contexto congelado
  (Seção 9, regra 8) e parou antes da chamada ao Gemini.
- Execução 2, retomada sem alteração (01:37–01:42 UTC): ZAMP3, LWSA3, VALE3 e ITUB4 concluídas
  (32 respostas). Antes de `LAVV3_N1`, nova divergência de contexto; novamente a parada ocorreu
  antes da chamada ao Gemini.
- Estado resultante: 48/96 casos concluídos, 48/96 pendentes, 0 erros, 0 respostas geradas com
  contexto divergente. Nenhuma resposta concluída será regenerada.

**2. Diagnóstico técnico** (testes sem chamadas ao Gemini, em índices descartáveis, com as
funções reais do executor congelado).
- *Fatos:*
  - A falha foi reproduzida nos testes diagnósticos. A exceção observada no Chroma 1.5.9 foi
    `InternalError: Error executing plan: Internal error: Error creating hnsw segment reader:
    Nothing found on disk`.
  - `modulos/recuperacao.py` captura essa exceção em silêncio; nessas ocorrências a recuperação
    resultou em contexto vazio (nenhum trecho). O executor detecta que esse contexto diverge do
    congelado e interrompe antes da geração.
  - Os arquivos HNSW da coleção afetada estavam presentes em disco. Abrir o mesmo índice num
    processo novo voltou a funcionar.
  - A falha foi intermitente em execuções com várias coleções (10 a 12) manipuladas no mesmo
    processo: ocorreu em 4 de 8 execuções longas, em empresas diferentes. Nos testes com 1 a 5
    coleções por processo não houve falha.
  - Nas recuperações bem-sucedidas, embeddings, ranking e distâncias permaneceram estáveis e o
    contexto foi idêntico ao congelado.
  - Não foi encontrado mecanismo técnico ligado ao número 16 (as paradas ocorreram após 2 e 4
    empresas completas de 8 casos). O OneDrive não foi demonstrado como causa necessária: a
    falha ocorreu também fora da pasta sincronizada.
- *Inferência:* a evidência é compatível com uma falha de estado interno do Chroma quando
  múltiplas coleções são manipuladas no mesmo processo. A causa raiz permanece **não
  determinada**.
- *Limitação:* o executor não armazenou o hash do contexto divergente nas duas paradas
  oficiais. A associação entre essas paradas e a exceção reproduzida é fortemente sustentada
  pelo padrão observado (pré-voo aprovado, falha na consulta posterior; reprodução no mesmo
  ponto, `LAVV3_N1` após os 32 casos), mas não é demonstrada diretamente pelo hash daquelas
  ocorrências.

**3. Decisão operacional** (tomada antes da geração dos casos 49–96).
- As seis empresas restantes serão executadas em processos independentes, na ordem congelada:
  1. LAVV3;
  2. POMO4;
  3. ITSA4;
  4. IRBR3;
  5. CEAB3;
  6. AURE3.
- Cada processo seleciona somente os oito `case_id` daquela empresa com a opção `--case-id`, já
  existente no executor congelado. A seleção de casos não entra no hash da configuração
  experimental.
- Cada execução mantém:
  - o mesmo executor (`fb13ba8`), o mesmo dataset congelado e o mesmo ZIP local
    (SHA-256 `4f89a998…`) e documentos;
  - a mesma geração: `gemini-2.5-flash`, temperatura 0,1, `max_output_tokens` 1024 e o mesmo
    prompt;
  - a mesma recuperação: `QUERY_NUMERICO`, top-k = 3 e a mesma conferência SHA-256 do contexto;
  - a mesma pasta oficial da coleta e a regra de uma única geração por caso.
- Como o executor exige o protocolo byte a byte congelado durante a coleta, esta emenda é
  registrada em commit próprio antes da continuação. A coleta prossegue a partir de `fb13ba8`,
  e a emenda é integrada ao ramo principal depois dos 96 casos.
- **Esta emenda altera somente a organização operacional dos processos. Não altera nenhum
  parâmetro científico do experimento nem o conteúdo do sistema avaliado.**

**4. Preservação das 48 respostas.** As 48 respostas existentes permanecem válidas e não serão
descartadas nem regeneradas:
- todas têm contexto com SHA-256 igual ao congelado;
- quando houve contexto divergente, o executor parou antes da geração;
- não há evidência de resposta gerada sobre contexto incorreto.

Nenhuma avaliação de conteúdo foi feita.

**5. Regra de parada** (vale para cada processo):
- se o contexto divergir do congelado, a execução para imediatamente;
- o caso não é repetido automaticamente;
- recuperação, Chroma, executor e dataset não são modificados durante a coleta;
- o evento é registrado antes de qualquer nova intervenção.

**6. Justificativa.**
- Reiniciar a coleta descartaria 48 respostas válidas e violaria sem necessidade a regra de
  geração única (Seção 15.8).
- Alterar `recuperacao.py`, o Chroma ou o executor agora modificaria o sistema avaliado ou o
  instrumento já congelado.
- Separar as empresas em processos independentes preserva todos os parâmetros experimentais e
  reduz o estado compartilhado do Chroma observado no diagnóstico.

Isso não significa que o problema foi resolvido: a trava de contexto permanece ativa e qualquer
nova divergência interrompe a coleta.

### Emenda 3 — 2026-09-29 (depois da coleta, antes de qualquer avaliação)

**Momento.** Registrada depois do congelamento da coleta (commit `10eee31`) e da integração da
Emenda 2 (commit `203cbd8`), e antes de qualquer execução sobre as 96 respostas de:
- exatidão;
- rubrica de comportamento;
- Faithfulness;
- Answer Relevancy.

Nenhuma resposta foi avaliada nem lida semanticamente para esta emenda. O texto pré-registrado e
as Emendas 1 e 2 não foram alterados. Os fatos abaixo vêm da leitura do código-fonte das
bibliotecas nas versões indicadas.

**1. Temperatura efetiva do avaliador (Seções 11 e 17).**
- *Fato:* no `ragas==0.4.3`, o `LangchainLLMWrapper` substitui a temperatura do modelo a cada
  chamada em que o prompt não a informa (`get_temperature`): 0,01 com `n = 1` e 0,3 com
  `n > 1`. Isso só não acontece com `bypass_temperature=True`.
- Os prompts de Faithfulness usam `n = 1`. O Answer Relevancy gera `strictness = 3` perguntas
  (`n = 3`), pedidas numa única chamada porque o `ChatGoogleGenerativeAI` expõe `n`
  (`candidate_count`).
- Consequência: no código do TCC 1 (`ChatGoogleGenerativeAI(temperature=0.0)` com o wrapper
  sem `bypass_temperature`), as temperaturas efetivamente enviadas são:
  - 0,01 em Faithfulness;
  - 0,3 na geração das perguntas do Answer Relevancy.

  O valor 0 configurado não chega à API.
- *Decisão:* manter a implementação literal do TCC 1 (Seção 11):
  - `ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)`;
  - `LangchainLLMWrapper` com os parâmetros padrão, sem `bypass_temperature` nem `bypass_n`.

  "Temperatura 0" (Seção 17) passa a ser lida como a temperatura configurada no cliente. As
  temperaturas efetivas são 0,01 e 0,3, definidas pela biblioteca, e são registradas nos
  resultados.
- *Motivo:*
  - preserva as métricas como implementadas e usadas no TCC 1 (comparação descritiva, Seção 14);
  - forçar temperatura 0 real alteraria o Answer Relevancy, porque as três perguntas geradas
    tenderiam a ser idênticas.

**2. Ambiente de avaliação (Seção 11; Seção 16, item 13).**
- A avaliação roda num ambiente virtual isolado. O ambiente da coleta (`google-genai==2.2.0`)
  não é alterado, porque `langchain-google-genai==4.4.0` exige `google-genai>=2.20`.
- Versões fixadas:
  - `ragas==0.4.3`;
  - `langchain-community==0.4.2`, a versão atual compatível com o `~=0.4.0` do
    `requirements.txt`;
  - `langchain-google-genai==4.4.0`.
- As demais dependências são resolvidas pelo `pip` na instalação e registradas integralmente
  (`pip freeze`) num arquivo versionado, antes de qualquer avaliação real.
- O ambiente reutiliza o `torch` e o `sentence-transformers` do ambiente da coleta.
- Os embeddings `paraphrase-multilingual-mpnet-base-v2` vêm do cache local, na revisão
  `4328cf26390c98c5e3c738b4460a05b95f4911f5` (a mesma da coleta), sem acesso à rede.
- Se o `ragas` 0.4.3 não for importável ou executável com essas versões, a avaliação não começa.
  Trocar versões exige nova emenda.

**3. Uma métrica por chamada (Seção 11, "Execução"; Seção 15.8).**
- Cada métrica é calculada numa chamada própria de `ragas.evaluate`:
  - sobre um `EvaluationDataset` de 1 amostra;
  - com `RunConfig(timeout=120, max_retries=3, max_workers=1)`;
  - com pausa de 10 s entre casos.
- O cálculo não muda, porque as duas métricas são independentes.
- *Motivo:* com as duas métricas na mesma chamada, a reavaliação de um NaN em uma delas
  recalcularia também a outra, já válida, violando a avaliação única (Seção 15.8).
- A reavaliação passa a ser feita por métrica e por caso:
  - no máximo uma, em passada separada e registrada;
  - a primeira tentativa é preservada.

**4. Detalhes operacionais que não alteram as métricas.**
- *Entradas de cada amostra:*
  - `user_input`: a `pergunta` do dataset;
  - `response`: o campo `resposta` do registro congelado, sem correção. As 36 respostas
    truncadas por `MAX_TOKENS` entram como estão, com marca para a análise;
  - `retrieved_contexts`: os textos dos três trechos do registro, iguais aos de `extrair_chunks`
    e conferidos por SHA-256;
  - `reference`: o campo `gabarito` do dataset, como no TCC 1. Nenhuma das duas métricas o usa.
- *Telemetria:* `RAGAS_DO_NOT_TRACK=true`, porque o `ragas` envia dados de uso a um servidor
  externo.
- *Compatibilidade:* substituto de `langchain_community.chat_models.vertexai`, como no TCC 1.
- *Erros:*
  - `evaluate` mantém `raise_exceptions=False` (padrão, como no TCC 1), o que transforma erro
    em NaN;
  - o executor registra as exceções capturadas e os identificadores de modelo devolvidos pela API.
- *Integridade:* os registros da coleta são validados por `SHA256_COLETA.txt` e pela
  configuração histórica do manifesto (`sha256_configuracao` `b9565446…`), e não pelo hash do
  protocolo emendado.
- *Ordem* (Seções 11.1 e 12; rubrica, Seção 1):
  1. exatidão;
  2. decisões manuais de sinal e rubrica de comportamento;
  3. congelamento (commit) desses registros;
  4. só então, RAGAS.

  O executor recusa o RAGAS antes do congelamento.

**5. O que não muda:**
- as métricas e os prompts do `ragas`;
- `strictness = 3`;
- o modelo avaliador e os embeddings;
- os instrumentos de exatidão e de comportamento;
- o dataset;
- a coleta;
- a política de NaN (sem imputação; no máximo uma reavaliação; persistindo, o caso é inválido).

### Emenda 4 — 2026-10-03 (depois da anotação de comportamento, antes do RAGAS)

**Momento.** Registrada depois do congelamento da exatidão (commit `d49835d`) e da anotação e
ratificação do comportamento dos 96 casos, e antes de qualquer execução de Faithfulness ou
Answer Relevancy. Não existe nenhum score RAGAS. O resultado da exatidão não foi consultado
durante a anotação de comportamento nem na preparação desta emenda. O texto pré-registrado, a
rubrica e as Emendas 1 a 3 não foram alterados. Esta emenda registra dois desvios entre o
procedimento planejado e o executado, com o tratamento adotado para cada um.

**1. Apoio de modelo de linguagem na anotação de comportamento.**
- *Procedimento planejado:* um único classificador, o autor, rotularia cada afirmação
  (Seção 15.10; rubrica, Seção 1). `README_AVALIACAO.md` (passo 3) descreve a etapa como
  "classificação humana, sem LLM", e `RELATORIO_fechamento_dataset.md` (item 3) diz que o autor
  classifica sozinho.
- *Procedimento executado:*
  - A anotação foi preparada com apoio de Claude, da Anthropic, em sessão do Claude Code.
  - O modelo organizou e apresentou os casos, aplicou preliminarmente a rubrica e as
    convenções, identificou as afirmações, propôs os rótulos S/E/A/N e os campos
    `declara_limitacao` e `entrega_informacao_sustentada`, estruturou os registros, fez
    verificações mecânicas e apontou casos limítrofes para decisão do autor.
  - A classe de cada caso foi derivada dos rótulos por `comportamento.derivar_classe`.
  - O autor revisou os 96 casos, sem sobreposição entre os grupos: 7 de calibração e 16 da
    etapa de pendências, com decisões determinadas por ele; 55 em 11 blocos; e 18 em 4 blocos
    finais.
  - Não houve divergências finais. O autor determinou duas correções no texto de
    `evidencia_contexto` (LWSA3_E3 e WEGE3_E2), sem mudança de rótulo ou classe.
- *Justificativa:* o apoio do modelo foi usado para operacionalizar a anotação em escala,
  incluindo a organização dos casos, a aplicação preliminar das regras e a proposição dos
  rótulos. A decisão final ficou sob responsabilidade do autor, por meio da revisão dos 96
  casos. Esse procedimento reduziu o trabalho operacional da anotação, mas difere do
  procedimento planejado e introduz risco de ancoragem nas propostas iniciais do modelo; por
  isso, o desvio e essa limitação são registrados aqui.
- *Impacto metodológico:*
  - Os julgamentos finais são do autor. Nos 73 casos da anotação em escala, porém, a proposta
    inicial de rótulos veio do modelo, e a revisão pode ter sido ancorada nessas propostas.
    Esse risco não é eliminado pela revisão integral, apenas declarado.
  - A medida continua sendo de avaliador único, sem segundo avaliador humano e sem medida de
    concordância.
  - A rubrica, as classes e a regra de decisão não mudam.
- *Tratamento:*
  - `classificador = "autor"` é mantido nos 96 registros e identifica o responsável humano
    pelo julgamento final; não indica que a preparação das anotações ocorreu sem apoio de
    modelo.
  - O procedimento executado está registrado em `CONVENCOES_ANOTACAO_COMPORTAMENTO.md` (seção
    "Apoio de modelo de linguagem na anotação") e em `RATIFICACAO_COMPORTAMENTO.md`.
  - Os documentos que descrevem o procedimento planejado não são editados.

**2. Casos truncados que a regra de decisão não classifica (`PENDENTE_OPERACIONAL`).**
- *Procedimento planejado:* a rubrica (Seção 4, item 4) determina que um caso `parcial` ou
  `ausente` sem afirmação E ou A e sem declaração de limitação seja recusado pelo validador, e
  associa a apresentação de informação parcial como resposta completa ao critério E(e). O
  executor libera o RAGAS só quando os 96 registros são válidos.
- *Procedimento executado:*
  - Cinco casos estão nessa situação: AURE3_E3 (`ausente`) e AURE3_N2, ITSA4_E2, LAVV3_E2 e
    ZAMP3_E2 (`parcial`).
  - Nos cinco, a coleta congelada registra o fim da geração pelo limite de tokens
    (`finish_reason = MAX_TOKENS`). O texto gerado até o corte não contém afirmação rotulada E
    ou A, e as anotações ratificadas registram `declara_limitacao = false`.
  - Atribuir E pelo critério (e) exigiria inferir que o fragmento produzido estava sendo
    apresentado como resposta completa. O autor decidiu não fazer essa inferência só a partir
    do truncamento (Convenção 6 de `CONVENCOES_ANOTACAO_COMPORTAMENTO.md`).
  - As anotações desses casos foram revisadas e ratificadas e ficam com `classe` e
    `abstencao_em_caso_presente` nulos. `comportamento.derivar_classe` os recusa.
- *Desvio em relação à rubrica:* o tratamento não é só uma adaptação do executor. A rubrica
  prevê a recusa desses registros e trata a informação parcial apresentada como completa pelo
  critério E(e). A Convenção 6 é mais conservadora para respostas truncadas: não infere E(e)
  quando o corte impede observar se a resposta apresentaria o conteúdo parcial como completo. A
  Convenção 6 foi definida com esses casos já conhecidos, antes de qualquer score RAGAS existir
  e sem consulta ao resultado da exatidão durante a anotação.
- *Justificativa:* atribuir E, A ou declaração de limitação só para obter uma classe
  registraria um desvio que o texto gerado não demonstra. Alterar `comportamento.py` ou a
  rubrica depois da anotação mudaria o instrumento para acomodar casos já vistos.
- *Impacto metodológico:*
  - A distribuição das quatro classes de comportamento (Seção 12, item 3) usa os casos
    classificados de cada grupo: 11 de 15 casos `parcial` e 11 de 12 casos `ausente`. Os 69
    casos `presente` não entram nesse denominador. Os 5 casos sem classe são reportados à
    parte.
  - Para auditoria, 91 dos 96 registros têm `classe`; esse total não é usado como denominador
    da distribuição das classes de comportamento.
  - Na Seção 12, item 5, os 5 casos entram só pelos critérios que podem ser calculados para
    eles, em particular a exatidão, e são identificados como "sem classe de comportamento por
    truncamento". Nenhuma classe de comportamento é atribuída a eles.
  - Faithfulness, Answer Relevancy e exatidão continuam calculados sobre os 96 casos; esses 5
    entram como estão, com a marca de truncamento (Emenda 3, item 4).
- *Tratamento:*
  - O executor passa a reconhecer o estado técnico `PENDENTE_OPERACIONAL`. Não é uma classe de
    comportamento: as quatro classes, o registro `SEM_DESVIO` e `comportamento.py` não mudam.
  - Um registro recebe esse estado só se atender a todas as condições:
    1. o id está em `pendencias_comportamento.json` com o estado
       `PENDENTE_POR_TRUNCAMENTO_E_REGRA_DO_VALIDADOR`, e a disponibilidade e a marca de
       truncamento da lista são iguais às da coleta congelada;
    2. a disponibilidade congelada é `parcial` ou `ausente`;
    3. a resposta foi truncada por limite de tokens na coleta congelada;
    4. o `sha256_resposta` confere com a resposta congelada;
    5. o registro passa nas verificações de `comportamento.validar_registro` que não dependem
       da classe;
    6. nenhuma afirmação tem rótulo E ou A, `declara_limitacao` é `false` e
       `entrega_informacao_sustentada` está preenchido;
    7. `classe` e `abstencao_em_caso_presente` são nulos;
    8. `comportamento.derivar_classe` recusa o registro pela regra da rubrica, Seção 4,
       item 4.
  - Um registro listado que falhe em qualquer condição é inválido, inclusive quando tem
    `classe` ou `abstencao_em_caso_presente` preenchidos. Um registro não listado segue as
    regras anteriores. Sem o arquivo de pendências, o comportamento do executor é o anterior.
  - O executor não contém ids de casos; a autorização vem só do arquivo de pendências. O nome
    `PENDENTE_POR_TRUNCAMENTO_E_REGRA_DO_VALIDADOR`, usado nos documentos da anotação, designa
    os mesmos casos.
  - A etapa de comportamento só é considerada completa com nenhum registro inválido, nenhum
    incompleto e válidos mais `PENDENTE_OPERACIONAL` iguais a 96.
  - Antes do RAGAS, o executor exige que `anotacoes_comportamento.json`,
    `pendencias_comportamento.json`, `CONVENCOES_ANOTACAO_COMPORTAMENTO.md` e
    `RATIFICACAO_COMPORTAMENTO.md` estejam versionados, commitados e sem alterações, e grava o
    SHA-256 de cada um na proveniência de cada resultado RAGAS. O hash do arquivo de pendências
    não é fixado no código do executor.

**3. Estado registrado (SHA-256):**
- `anotacoes_comportamento.json`: `c83cf6cef724f88ab35ac439978d13f0ad812c0ce25859ab7155eef97627b18f`
- `pendencias_comportamento.json`: `d20f736187f69cd441a53795b4425ff212d54d7ee9274d79c894e02825976b71`
- `CONVENCOES_ANOTACAO_COMPORTAMENTO.md`: `e45f82c4dd46a27a475085ee0e06d4ffc7f1de94b7c15d38e30adfe90a379169`
- `RATIFICACAO_COMPORTAMENTO.md`: `eee5e92412a941e1bc090e0338120660f7200c793e1636f72af337454c258c36`
- Validação esperada com o executor ajustado: 91 válidos, 5 `PENDENTE_OPERACIONAL`,
  0 incompletos, 0 inválidos.

**4. O que não muda:**
- a rubrica, `comportamento.py`, as classes e a regra de decisão;
- as anotações;
- o dataset e a coleta;
- o instrumento e o resultado da exatidão; a alteração do executor não toca no código da
  exatidão;
- as métricas, os prompts e os parâmetros do `ragas`;
- a ordem das etapas (Emenda 3, item 4).

**Nota de transparência.** A preparação e a redação desta emenda contaram com apoio de Claude,
da Anthropic, em sessão do Claude Code. O texto final foi revisado e aprovado pelo autor, e as
decisões metodológicas registradas aqui são do autor.

### Emenda 5 — 2026-10-09 (depois da exatidão, do comportamento e do RAGAS: rótulo ambivalente na regra de sinal)

**Momento.** Registrada depois de todas estas etapas:
- congelamento da exatidão (commit `d49835d`);
- anotação de comportamento (`cd29dee`);
- avaliação RAGAS (`d78d5a5`);
- análise dos seus resultados (`8844743`);
- revisão humana dos gabaritos (`9dc164a`, `81dd443`).

A correção foi **concebida depois da observação dos resultados**: o problema apareceu na análise do
resultado congelado da exatidão. O texto pré-registrado e as Emendas 1 a 4 não foram alterados.

**1. Problema.**
- A regra 5 da Seção 11.1 considera negativo um número quando a palavra "prejuízo", "negativo" ou
  "déficit" está na mesma oração.
- Seis respostas N2 de empresas com resultado positivo foram classificadas INCORRETO: BBAS3, CEAB3,
  IRBR3, ITSA4, ITUB4 e LAVV3, todas `presente`.
- Nelas, o valor confere em módulo, mas a oração repete o rótulo contábil da conta ("Lucro/Prejuízo
  Consolidado do Período") ou a alternativa da pergunta ("lucro ou prejuízo").
- A palavra "prejuízo" do rótulo foi lida como sinal negativo. O rótulo nomeia a conta ou a
  alternativa e não afirma prejuízo.

**2. Regra adotada (opção A, variante A1).** Com `regra_sinal="emenda5"`, um rótulo ambivalente é
desconsiderado na busca da palavra negativa, tanto na regra 5 quanto na regra C da Emenda 1.
- **Rótulo ambivalente:** o termo negativo em par alternativo com o antônimo positivo, em qualquer
  ordem, no texto sem acento e em minúsculas: lucro(s)/prejuízo(s), superávit/déficit,
  positivo/negativo.
- **Formas aceitas:**
  - separados por "/", "ou" ou "e/ou";
  - o segundo termo sozinho entre parênteses fechados, como em "Lucro (Prejuízo)".
  - Um parêntese explicativo, como em "prejuízo (lucro operacional foi positivo)", não é rótulo.
- **Continuam valendo:**
  - o traço explícito;
  - a palavra negativa fora do par na mesma oração;
  - a palavra negativa isolada;
  - a revisão manual de número isolado entre parênteses sem palavra negativa fora do par.
- A regra é geral: não contém ticker, id de caso nem valor.

**3. Implementação.**
- `exatidao.py` recebe o parâmetro `regra_sinal` em `extrair_numeros` e `classificar`. Os valores são
  `"original"` (padrão) e `"emenda5"`, e qualquer outro valor é rejeitado com `ValueError`.
- No padrão, o instrumento se comporta como o congelado antes da coleta (SHA-256 `2b4b1170…`,
  commit `a3f424f`).
  - Antes do commit, os 96 casos foram reclassificados com o padrão e ficaram idênticos ao
    `resultado_exatidao.json` congelado em todos os campos, inclusive números e sinais lidos.
  - Os testes existentes continuam passando.
- A classe `Emenda5RotuloAmbivalente` (`tests/test_ragas_exatidao.py`) tem 17 testes sintéticos:
  - 14 da regra;
  - 3 complementares: o padrão é o original, valor desconhecido é rejeitado, e o parêntese
    explicativo não é neutralizado.
- O executor `avaliar_respostas_tcc2.py` não muda e continua usando o padrão.
- O resultado com a emenda é produzido por um gerador separado,
  `avaliacao_tcc2/exatidao_emenda5/gerar_exatidao_emenda5.py`. Ele só grava com o código commitado e
  limpo, confere o selo e o SHA-256 do resultado original e exige que o modo padrão o reproduza.
  Grava uma única vez, sem sobrescrever.

**4. Resultados.**
- O resultado congelado, `avaliacao_tcc2/exatidao/resultado_exatidao.json` (SHA-256 `3c3e28c0…`),
  **não é alterado e continua sendo o resultado reportado da exatidão**, com 31 CORRETO de 43
  aplicáveis.
- O resultado com a Emenda 5 fica em `avaliacao_tcc2/exatidao_emenda5/`, com proveniência própria e
  referência ao original, e é **reportado em acréscimo, lado a lado com o original**.
- Na simulação prévia:
  - os seis casos N2 acima passam de INCORRETO para CORRETO, e nenhuma outra classe muda (37 de 43);
  - um sétimo número muda de sinal lido, em BBAS3_N4, sem efeito na classe, porque N4 é
    NAO_APLICAVEL.

**5. Natureza e limitações.**
- A emenda é uma **correção post hoc do instrumento de medida**. Foi motivada por casos conhecidos
  depois de observado o resultado.
- A regra é geral e foi testada também onde piora a classificação: um rótulo sem marca negativa
  numa empresa com prejuízo deixa de conferir. Mesmo assim, o risco de ajuste aos resultados não é
  eliminado, e por isso os dois resultados são apresentados.
- **A emenda não representa melhoria do sistema FundIA.** As 96 respostas são as mesmas. Muda apenas
  a leitura do sinal pelo instrumento de verificação.
- A leitura do sinal continua no nível da oração. As demais limitações da regra 5 não são tratadas.

**6. Proveniência.**
- O `exatidao.py` do repositório passa a ter outro SHA-256.
- O resultado congelado da exatidão e os resultados brutos do RAGAS continuam registrando o hash
  do instrumento com que foram produzidos (`2b4b1170…`).
- Esse instrumento é recuperável no commit `a3f424f`, e o padrão `"original"` reproduz o seu
  resultado.

**7. O que não muda:**
- o dataset, os gabaritos e as classes de disponibilidade;
- a coleta, a anotação de comportamento e os resultados RAGAS;
- o resultado congelado da exatidão;
- o executor;
- as demais regras da Seção 11.1 e da Emenda 1.

**Nota de transparência.** A preparação desta emenda contou com apoio de Claude, da Anthropic, em
sessão do Claude Code. A redação foi preparada a partir do plano técnico aprovado pelo autor
(variante A1, resultado separado e original preservado), e as decisões metodológicas registradas
aqui são do autor.
