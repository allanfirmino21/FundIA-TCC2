# Análise focalizada das discordâncias entre instrumentos — TCC 2

**Natureza:** investigação **documental** de 12 casos selecionados, feita depois da observação de todos os
resultados.
- Não reavalia os 96 casos, não executa o RAGAS e não chama LLM.
- Não altera nenhuma classificação, métrica, resposta, gabarito ou o protocolo.
- Não cria categoria de avaliação.

**Fontes:**
- Cruzamentos: `sintese/sintese_resultados_tcc2.json` (commit `ea31628`, SHA-256 `db7b090c…`).
- Respostas e contextos: coleta congelada, lida pelo executor.
- Exatidão: `exatidao/resultado_exatidao.json` (`3c3e28c0…`) e
  `exatidao_emenda5/resultado_exatidao_emenda5.json` (`22af220e…`).
- Comportamento: `comportamento/anotacoes_comportamento.json` (`c83cf6ce…`).
- RAGAS:
  - os resultados brutos em `ragas/faithfulness/` e `ragas/answer_relevancy/` (commit `d78d5a5`);
  - `analise/tabelas_mecanicas_ragas.json`, com os marcadores exploratórios de ressalva.

**Níveis de evidência** (os mesmos de `analise/ANALISE_RESULTADOS_RAGAS.md`):
- **[registro]:** observado diretamente nos artefatos congelados;
- **[código]:** comportamento demonstrado pelo código do `ragas==0.4.3` ou pelos testes congelados;
- **[inferência]:** interpretação ou hipótese não confirmada, não observada.

Em cada seção, os fatos comprovados [registro], o comportamento verificável do código [código] e as
interpretações [inferência] aparecem separados. Nas citações, o espaçamento das tabelas e a marcação de
negrito das respostas foram normalizados. Todos os números citados foram conferidos contra os artefatos
congelados antes do versionamento.

## 0. Limite comum: o que os registros RAGAS permitem explicar

**[registro]** Cada resultado bruto do RAGAS guarda apenas:
- score, validade e erros;
- modelo e tokens;
- os hashes da entrada;
- a configuração do avaliador e a proveniência.

**Não foram persistidos:**
- as afirmações extraídas pelo Faithfulness;
- os veredictos e as justificativas do juiz;
- as perguntas geradas pelo Answer Relevancy;
- as marcas `noncommittal`.

**Consequência:** nenhum resultado individual dos juízes RAGAS pode ser explicado com evidência direta. As
leituras abaixo dizem o que é **compatível** com os registros. A causa de um score específico não fica
demonstrada. Os tokens de saída do juiz, que variam de 1.864 a 10.590 nos casos examinados, não indicam o
conteúdo do julgamento.

## 1. Exatidão CORRETO com Faithfulness = 0: CEAB3_N3, IRBR3_N3, ITSA4_E3, ZAMP3_E3

Os quatro são casos `presente`, não truncados, com comportamento SEM_DESVIO e marca de abstenção falsa.
A exatidão é CORRETO no original e na Emenda 5.

| Caso | Pergunta | O que a resposta afirma | Linha do contexto [registro] | F | AR |
|---|---|---|---|---:|---:|
| CEAB3_N3 | variação do resultado líquido 1S26 × 1S25 | 179.594 (1S26), 204.384 (1S25), −24.790, redução de 12,13% | DRE "Lucro/Prejuízo Consolidado do Período 179.594 (anterior: 204.384)" | 0 | 0,828 |
| IRBR3_N3 | idem | 90.305 e 240.662 ("Lucro"), −150.357, queda de 62,48% | DRE "Lucro/Prejuízo Consolidado do Período 90.305 (anterior: 240.662)" | 0 | 0,666 |
| ITSA4_E3 | resultado financeiro 1S26 × 1S25 | "R$ 193.000" (1S26), "R$ -844.000" (1S25), "melhora significativa" | DRE "Resultado Financeiro 193.000 (anterior: -844.000)" | 0 | 0,915 |
| ZAMP3_E3 | idem | −169.280 (1S26), −144.604 (1S25), "mais negativo" | DRE "Resultado Financeiro -169.280 (anterior: -144.604)" | 0 | 0,940 |

**Fatos comprovados [registro]:**
- Os valores conferem com o gabarito e com a DRE do contexto. Os cálculos de CEAB3_N3 e IRBR3_N3
  (variação absoluta e percentual) estão corretos.
- A anotação de comportamento rotulou todas as afirmações como S, sustentadas.
- As quatro respostas atribuem os valores a "1º semestre de 2026/2025", nomeiam a empresa ou o conceito e
  não fazem ressalva. Nenhum dos 96 contextos tem data, período ou nome da empresa (análise RAGAS, Seção 6).
- ITSA4_E3 escreve "R$ 193.000" sem "mil". A exatidão aplica a escala implícita em R$ mil (regra 3), e a
  anotação trata a unidade presumida como neutra (§16, item 5).
- **O mesmo padrão textual aparece com F = 0 e com F = 1.** Das 8 respostas não truncadas que nomeiam o
  período sem ressalva, 4 têm F = 0 (estas) e 4 têm F = 1 (ITSA4_N3, LWSA3_E2, POMO4_E2, VALE3_E2), conforme a análise
  RAGAS, Seção 7.

**Interpretações plausíveis [inferência], hipóteses não confirmadas:**
- O juiz pode ter recusado como "não inferível diretamente" a atribuição temporal ou de entidade, que o
  contexto nunca contém.
- Pode também ter recusado os cálculos derivados ou a qualificação ("melhora significativa", "prejuízo
  financeiro").
- Pode ainda refletir variabilidade do juiz, porque houve uma única execução por caso.
- Nenhuma dessas leituras é verificável.

**Conclusão utilizável no TCC:** em 4 dos 37 casos com exatidão CORRETO, o Faithfulness foi 0. Isso
confirma, nesta amostra, a limitação pré-registrada de que o Faithfulness pode penalizar respostas
numericamente corretas (§16, item 11). A causa não pode ser determinada porque os veredictos não foram
persistidos.

## 2. VALE3_E3: extrapolação, erro de sinal e Faithfulness = 1

**Dados do caso:**
- Disponibilidade `parcial`.
- O contexto não tem DRE. Traz a linha da DFC "Resultado financeiro, líquido 2.237.000 (anterior:
  -2.186.000)", com sinal invertido em relação ao resultado financeiro da DRE (regra 6 da Seção 9).
- Gabarito: −2.237.000 (1S26) e +2.186.000 (1S25), com sinal exigido.

**A resposta:** declara que "não é possível determinar o resultado financeiro […] pois as tabelas não
especificam os períodos". Mesmo assim, informa a linha da DFC: "2.237.000 para o período atual e
-2.186.000 para o período anterior".

| Instrumento | Resultado | O que mede |
|---|---|---|
| Exatidão (original e Emenda 5) | INCORRETO: os dois valores conferem em módulo, com sinais opostos aos exigidos | valor e sinal contra o gabarito |
| Comportamento | EXTRAPOLACAO (E, critérios a e c, decisão do autor), com `declara_limitacao` verdadeira | uso de uma linha de outro conceito como se fosse o pedido |
| Faithfulness | 1,0 | se as afirmações são inferíveis do texto do contexto |
| Answer Relevancy | 0 | proximidade de perguntas reconstruídas da resposta |

**Fatos comprovados [registro]**, em dois planos distintos:
- **Presença literal:** os números da resposta são literalmente os da linha da DFC presente no contexto.
- **Adequação do conceito contábil:** a linha não é o conceito pedido. É um ajuste de reconciliação da
  DFC, com sinal invertido em relação à DRE, conforme o gabarito, a regra 6 da Seção 9 e a anotação de
  comportamento.
- A presença literal não implica adequação conceitual: os dois planos divergem neste caso.
- A Emenda 5 não muda a leitura deste caso.

**Comportamento do código [código]:** o Faithfulness julga se cada afirmação é inferível do texto do
contexto. Esse critério não inclui verificar se a linha corresponde ao conceito contábil pedido.

**Interpretação [inferência]:** o F = 1 é compatível com esse mecanismo, porque a linha existe
literalmente no contexto. O veredicto deste caso não foi persistido, então essa leitura não é
demonstrada.

**Conclusão utilizável no TCC:**
- Os três instrumentos medem coisas diferentes, e o caso mostra isso de forma direta.
- O Faithfulness alto **não garante adequação conceitual**.
- A extrapolação foi detectada pela exatidão (pelo sinal) e pelo comportamento (pelo conceito), mas não
  pelo RAGAS.
- É um único caso, de disponibilidade `parcial`, e não sustenta generalização.

## 3. PARCIALMENTE_CORRETO com truncamento: ITUB4_N3 e ZAMP3_N3

As duas respostas terminaram por `finish_reason = MAX_TOKENS`, com a mesma classe no original e na Emenda 5.

| Caso | Tokens (saída / raciocínio, limite 1024) | Valores corretos apresentados | Valores ausentes | Fim da resposta |
|---|---|---|---|---|
| ITUB4_N3 | 170 / 850 | 24.199.000 (atual) e 22.105.000 (anterior); direção "aumentou" | variação percentual (9,47%) | `Variação Absoluta:** 24.199.` |
| ZAMP3_N3 | 69 / 951 | −154.679 (1S26) | 1S25 (−116.011) e variação (33,33%) | `(1º Semestre de 202` |

**Fatos comprovados [registro]:**
- Os valores apresentados conferem.
- Os valores ausentes **não aparecem** em nenhum ponto da resposta, e o texto termina no corte.
- Em ITUB4_N3, o fragmento "24.199." foi lido como 24.199 e não foi conciliado. Ele **não coincide** com o
  início da variação absoluta correta (24.199.000 − 22.105.000 = 2.094.000).
- Os scores RAGAS foram F 0,900 / AR 0 em ITUB4_N3 e F 0,333 / AR 0,671 em ZAMP3_N3.
- A anotação de comportamento trata os dois fragmentos finais como não afirmação (Convenção 1). Os dois
  casos ficaram SEM_DESVIO, com entrega.
- ITUB4_N3 começa com uma ressalva sobre os períodos antes de entregar os valores.

**Efeito comprovado do truncamento:** a resposta termina antes dos valores que faltam, então a classe
PARCIALMENTE_CORRETO decorre de **valores não apresentados**, e não de valores errados.

**Interpretação [inferência]:** que, sem o corte, os valores ausentes estariam corretos não pode ser
afirmado. Também não se sabe o que o fragmento de ITUB4_N3 seria.

**Conclusão utilizável no TCC:**
- Com a Emenda 5, nenhum caso `presente` aplicável tem valor errado.
- Os dois casos `presente` não totalmente corretos são incompletos por truncamento, uma limitação
  operacional da coleta (limite de 1024 tokens, aceito antes da coleta).

## 4. Answer Relevancy = 0 com exatidão CORRETO: exemplos

**Critério de seleção.** O critério é explícito e usa só campos já anotados. Foi definido antes da leitura do texto das
respostas selecionadas e não tem pretensão de representatividade estatística.
1. **Universo:** os 25 casos com exatidão CORRETO (Emenda 5) e AR = 0.
2. **Filtro:** CORRETO também no original (sem depender da Emenda 5), resposta não truncada e F = 1,
   para isolar o AR. Restam 15 casos.
3. **Estratos:** os campos já anotados `abstencao_em_caso_presente` (verdadeiro ou falso) × estrutura
   contábil.
4. **Escolha:** o primeiro caso de cada estrato na ordem do dataset, que dá 6, e destes os 5 primeiros na
   ordem do dataset.

| Caso | Estrutura / abstenção | Valor entregue (confere) | Ressalva na resposta [registro] | F / AR |
|---|---|---|---|---|
| WEGE3_E3 | não financeira / não | 65.819 e 47.595, comparação correta | "Os trechos não especificam que esses períodos correspondem ao primeiro semestre de 2026 e 2025" | 1 / 0 |
| BBAS3_N5 | banco / sim | 65.017.849 (e o anterior) | "não é possível determinar o saldo […] pois as datas de referência […] não são especificadas" | 1 / 0 |
| ZAMP3_N5 | não financeira / sim | 135.651 (e o anterior) | "não é possível determinar o saldo […] pois as tabelas não contêm informações de data" | 1 / 0 |
| ITSA4_E1 | holding / não | 9.354.000 | "Os trechos não especificam que este valor se refere ao primeiro semestre de 2026" | 1 / 0 |
| IRBR3_N1 | resseguradora / não | 1.920.140 | "não é possível confirmar se corresponde ao primeiro semestre de 2026" | 1 / 0 |

**Contraste agregado nos 37 CORRETO (Emenda 5) [registro]:** usa o marcador exploratório `m_ressalva` de
`tabelas_mecanicas_ragas.json`. O marcador **foi definido depois da observação dos scores**, não foi
pré-registrado nem validado. A tabela descreve uma associação e não estabelece causalidade.

| | AR = 0 | AR > 0 |
|---|---:|---:|
| Com ressalva | 25 | 1 (ITSA4_N5, 0,890) |
| Sem ressalva | 0 | 11 |

**Fatos comprovados [registro]:**
- Nos cinco exemplos, o valor pedido é entregue e confere, e o F é 1.
- A ressalva sobre o período aparece **antes ou depois** do valor.
- O AR fica exatamente em 0, e não em um valor baixo.
- Os 4 casos CORRETO com F = 0 (Seção 1) estão todos no grupo sem ressalva, com AR alto.

**Comportamento do código [código]:** o Answer Relevancy aplica o multiplicador `noncommittal`, e o score
zera quando as três perguntas geradas a partir da resposta são marcadas como evasivas.

**Interpretação [inferência]:**
- A associação entre ressalva e AR = 0 é compatível com esse multiplicador.
- As marcas de cada caso não foram persistidas, então a associação não demonstra causalidade.
- ITSA4_N5 mostra que a associação com a ressalva não é determinística.

**Conclusão utilizável no TCC:**
- Nesta configuração, o AR = 0 **não indica resposta errada nem irrelevante**: 25 dos 37 CORRETO têm AR = 0.
- Nesta amostra, o AR = 0 aparece associado à presença de ressalva, e não à falta da informação pedida.
  A associação é compatível com `noncommittal`, sem afirmação de causalidade.
- O marcador de ressalva é exploratório, foi definido depois dos scores e não foi validado.

## 5. Síntese do que pode e do que não pode ser afirmado

| Afirmação | Situação |
|---|---|
| F = 0 em 4 respostas numericamente corretas | **comprovada** [registro] |
| Causa desses zeros (período, entidade, cálculo, variabilidade) | **não determinável**: intermediários não persistidos |
| F = 1 em uma extrapolação com sinal invertido (VALE3_E3) | **comprovada** [registro]; compatível com o mecanismo [código] |
| Os 2 PARCIALMENTE_CORRETO em `presente` têm valores corretos apresentados e os demais ausentes por truncamento | **comprovada** [registro] |
| O que as respostas truncadas diriam sem o corte | **não determinável** |
| AR = 0 em 25 de 37 respostas CORRETO, todas com ressalva | **comprovada** [registro], com marcador exploratório definido depois dos scores |
| AR = 0 associado à marca `noncommittal` | **compatível** [código]; não observada caso a caso; sem afirmação de causalidade |
| Os instrumentos medem dimensões diferentes e não se substituem | **sustentada** pelos casos acima; não é generalização estatística |

## 6. Limitações desta análise

- A análise é posterior à observação de todos os resultados e examina 12 casos escolhidos por
  discordância. Ela ilustra mecanismos e não estima frequências.
- Os resultados RAGAS vêm de uma única execução por caso (fora as reavaliações registradas). A
  variabilidade do juiz não foi estimada.
- O marcador de ressalva é exploratório e foi definido depois dos scores.
- O mesmo modelo (`gemini-2.5-flash`) gerou as respostas e atuou como juiz (§16, item 10).
