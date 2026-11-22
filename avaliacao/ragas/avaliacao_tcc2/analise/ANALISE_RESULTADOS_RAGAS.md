# Análise dos resultados RAGAS do TCC 2: descritiva e qualitativa diagnóstica

**Status:** etapa encerrada e congelada. A análise é **exploratória e posterior à observação dos
scores**. Não usa a exatidão nem o gabarito (`reference`) e não fez nenhuma chamada a LLM ou API.
Nenhum score foi alterado e nenhum limiar de aprovação foi criado.

## 1. Proveniência

- **Resultados RAGAS analisados:** commit `d78d5a5ddfdbc29491377e28ac98d665183ea0ce`.
  - 387 arquivos brutos em `avaliacao/ragas/avaliacao_tcc2/ragas/`.
  - SHA-256 do inventário: `7cea256cf0be5de00f53621283c31388d59d256fca89acb670b057dd6b630239`.
  - Formato do inventário: linhas `<sha256>  <caminho>` ordenadas por caminho.
- **Denominador global RAGAS:** 96.
- **Denominador das análises por classe de comportamento:** 91.
  - Os 5 casos `PENDENTE_OPERACIONAL` não têm classe (Emenda 4) e são relatados à parte.
- **Anotações de comportamento:** `c83cf6ce…7b18f`. **Pendências:** `d20f7361…5b71`.
  **Dataset:** `313bdf35…6bc5e`. Os hashes completos estão em `resultados_descritivos_ragas.json`,
  chave `proveniencia`.
- **Configuração do avaliador**, idêntica em todos os resultados e conferida pelo script:
  - modelo e temperaturas:
    - `gemini-2.5-flash`;
    - temperatura do cliente 0;
    - temperatura efetiva 0,01 em Faithfulness e 0,3 em Answer Relevancy;
  - `strictness` 3;
  - `RunConfig(timeout=120, max_retries=3, max_workers=1)`;
  - embeddings `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`, revisão `4328cf26…`;
  - `ragas==0.4.3`, `langchain-google-genai==4.4.0`, `langchain-community==0.4.2`;
  - uma métrica e uma amostra por chamada de `ragas.evaluate`.

## 2. Regra da tentativa final

- **Faithfulness:** vale a tentativa 2 válida, quando existe; senão, a tentativa 1 válida.
  Tentativas inválidas nunca entram.
  - A tentativa 2 existe só em **POMO4_N2** (a tentativa 1 teve NaN por `TimeoutError`) e em
    **ITSA4_E1** (a tentativa 1 foi interrompida e contou como inválida).
  - Nos dois casos a tentativa 2 é válida. Nos outros 94, vale a tentativa 1.
- **Answer Relevancy:** tentativa 1 nos 96 casos, todas válidas.
- **Auditoria** (registrada no JSON):
  - 96 ids, únicos e iguais aos da coleta;
  - 96 resultados finais por métrica;
  - nenhum NaN;
  - todos os scores dentro de [0, 1];
  - um resultado final por id e por métrica.

## 3. Artefatos e reprodução

| Arquivo | Conteúdo |
|---|---|
| `analisar_resultados_ragas.py` | Script único: confere os congelados, monta a base e calcula as estatísticas e as tabelas mecânicas |
| `base_analitica_ragas.csv` | 96 casos: metadados, comportamento, F e AR finais, tentativa final |
| `resultados_descritivos_ragas.json` | Estatísticas globais, faixas, recortes, correlação, extremos, proveniência |
| `tabelas_mecanicas_ragas.json` | Tabelas usadas na análise qualitativa (seções 6 a 9), incluindo os marcadores por caso |

```
python avaliacao/ragas/avaliacao_tcc2/analise/analisar_resultados_ragas.py verificar
```

O modo `verificar` faz o seguinte:
- confere que os 387 brutos e as anotações são idênticos ao commit `d78d5a5`;
- recalcula tudo em memória;
- compara byte a byte com os três arquivos versionados.

O modo `gerar` grava os arquivos de forma exclusiva e recusa sobrescrever.

**Estatística:**
- desvio-padrão amostral (n−1);
- quartis por interpolação linear (`statistics.quantiles`, `method="inclusive"`);
- Spearman calculado como Pearson sobre postos médios.

**Arquivos auxiliares não versionados:** os textos por caso, com pergunta, resposta, contexto e
anotação, foram usados na leitura qualitativa e não são versionados. Todos podem ser reconstruídos
da coleta e das anotações congeladas. A evidência necessária para auditar as conclusões está
citada nas seções 6 a 9.

## 4. Níveis de evidência

- **[registro]**: observado diretamente nos artefatos congelados (scores, respostas, contextos,
  anotações) ou em tabela mecânica calculada a partir deles.
- **[código]**: comportamento demonstrado pelo código do `ragas==0.4.3` instalado no ambiente da
  avaliação ou pelos testes congelados.
- **[inferência]**: interpretação exploratória, não observada diretamente.

**Limite central [registro].** Os resultados RAGAS persistem só o score, os tokens, os erros e os
metadados. **Não foram persistidos:**
- as afirmações extraídas pelo Faithfulness;
- os veredictos e as justificativas do juiz;
- as perguntas geradas pelo Answer Relevancy;
- as marcas `noncommittal`.

Por isso, nenhuma causa caso a caso pode ser afirmada como diretamente observada.

## 5. Estatísticas descritivas [registro]

| Métrica | n | Média | Mediana | DP | Mín | Q1 | Q3 | Máx |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Faithfulness | 96 | 0,784 | 1,000 | 0,332 | 0 | 0,667 | 1,000 | 1 |
| Answer Relevancy | 96 | 0,160 | 0 | 0,311 | 0 | 0 | 0 | 0,940 |

| Faixa | = 0 | (0; 0,25] | (0,25; 0,50] | (0,50; 0,75] | (0,75; 1) | = 1 |
|---|---:|---:|---:|---:|---:|---:|
| Faithfulness | 10 | 1 | 10 | 10 | 8 | **57** |
| Answer Relevancy | **75** | 0 | 1 | 10 | 10 | 0 |

**Recortes.** Cada célula mostra média / mediana; n entre parênteses.

| Recorte | Faithfulness | Answer Relevancy |
|---|---|---|
| presente (69) | 0,800 / 1 | 0,175 / 0 |
| parcial (15) | 0,664 / 0,875 | 0,179 / 0 |
| ausente (12) | 0,839 / 1 | 0,053 / 0 |
| truncado (36) | 0,684 / 1 | 0,184 / 0 |
| não truncado (60) | 0,844 / 1 | 0,146 / 0 |
| SEM_DESVIO (69, todos `presente`) | 0,800 / 1 | 0,175 / 0 |
| ABSTENCAO_ADEQUADA (17) | 0,879 / 1 | 0,071 / 0 |
| RESPOSTA_PARCIAL_ADEQUADA (4) | 0,689 / 0,683 | 0 / 0 |
| EXTRAPOLACAO (1: VALE3_E3) | 1,000 | 0 |
| ALUCINACAO (0) | — | — |
| `presente` com `abstencao_em_caso_presente` (34) | 0,930 / 1 | 0 / 0 |
| `presente` sem a marca (35) | 0,674 / 0,900 | 0,344 / 0 |

- **Pendentes operacionais**, sem classe, todos com F final na tentativa 1 (F / AR):
  - AURE3_E3 (ausente): 1 / 0
  - AURE3_N2 (parcial): 0 / 0,905
  - ITSA4_E2 (parcial): 0 / 0,644
  - LAVV3_E2 (parcial): 0 / 0
  - ZAMP3_E2 (parcial): 0,333 / 0,561
- **Correlação entre as métricas (n = 96):** Pearson −0,352; Spearman −0,233. Os dois
  coeficientes são dominados pelos 75 zeros de AR e pelos empates.
- **Extremos:**
  - Os 10 menores Faithfulness são exatamente os 10 zeros.
  - As listas dos menores AR e das maiores diferenças são decididas por desempate alfabético
    (75 empates em AR = 0; 47 empates em |F − AR| = 1) e não são informativas.

## 6. Mecanismo das métricas [código]

**Faithfulness:**
1. Um LLM decompõe a resposta em afirmações, recebendo a pergunta e a resposta.
2. Outro prompt julga cada afirmação com veredicto 1 se ela "pode ser inferida diretamente" do
   contexto (os trechos concatenados), ou 0 se não pode.
3. O score é a fração de afirmações com veredicto 1. Sem afirmações, o score é NaN.

Portanto, **F = 0 (e não NaN) significa que pelo menos uma afirmação foi extraída e todas
receberam 0**.

**Answer Relevancy:**
1. Com `strictness` 3, o LLM gera 3 pares (pergunta, `noncommittal`) **só a partir da resposta**,
   sem contexto e sem a pergunta original.
2. O prompt define noncommittal como resposta "evasive, vague, or ambiguous".
3. O score é: `média(cos(pergunta original, pergunta gerada_i)) × int(not all(noncommittal))`.

**Correção registrada:** o multiplicador zero ocorre **só quando as três gerações são marcadas
`noncommittal`**. Uma única geração marcada não zera o score. O relatório descritivo anterior
afirmava erroneamente que bastava "alguma" geração. O teste congelado
`test_resposta_evasiva_recebe_zero` (`tests/test_ragas_avaliacao_ambiente.py`) cobre o caso das
três gerações marcadas.

**[registro]**
- Os 75 zeros de AR são exatamente 0.0.
- Não há nenhum valor entre 0 e 0,456; o menor AR positivo é 0,4561.
- Nenhum AR é negativo.

**[inferência]** Esse padrão é compatível com o multiplicador 0/1 e não com uma similaridade baixa.
Mesmo assim, as marcas de cada caso não foram persistidas.

**Representação do contexto [registro]:**
- Os 96 contextos são tabelas no formato `valor (anterior: valor)`, com quatro cabeçalhos
  possíveis: BP Ativo, BP Passivo, DFC e DRE, todos consolidados.
- **Nenhum dos 96 contém marca de data ou período nem o nome da empresa.**
- Varredura usada:
  - data ou período: regex `20\d\d|semestre|junho|trimestre|exercício|\b1S|\b6M`, sem distinção de
    maiúsculas;
  - nome da empresa: com limite de palavra.

## 7. Diagnóstico dos 10 casos com Faithfulness = 0

Os valores e os cálculos foram conferidos por mim **contra o contexto**, não contra o gabarito ou
a exatidão.

| Caso: pergunta | Disp. / trunc. / classe | O que a resposta afirma | O que o contexto tem [registro] | Leitura |
|---|---|---|---|---|
| ZAMP3_E3: resultado financeiro 1S26 vs 1S25 | presente / não / SEM_DESVIO (SSS) | -169.280 "no 1º sem. 2026", -144.604 "no 1º sem. 2025", "mais negativo" | DRE `Resultado Financeiro -169.280 (anterior: -144.604)` | Valores e comparação conferem. O único elemento não literal é a atribuição a "Zamp" e aos semestres |
| ITSA4_E3: idem | presente / não / SEM_DESVIO (SSS) | R$ 193.000 (1S26), R$ -844.000 (1S25), "melhora" | DRE `Resultado Financeiro 193.000 (anterior: -844.000)` | Idem; há também a unidade "R$" presumida, mas ITSA4_N3 usa "R$" e tem F = 1 |
| CEAB3_N3: variação do resultado líquido | presente / não / SEM_DESVIO (SSSS) | 179.594; 204.384; -24.790; -12,13% | DRE `Lucro/Prejuízo Consolidado do Período 179.594 (anterior: 204.384)` | Valores e os dois cálculos conferem. Só a atribuição de período não é literal |
| IRBR3_N3: idem | presente / não / SEM_DESVIO (SSS) | 90.305; 240.662; -150.357; -62,48% | DRE `Lucro/Prejuízo Consolidado do Período 90.305 (anterior: 240.662)` | Idem |
| ITSA4_E2: caixa × empréstimos em 30/6/2026 | parcial / sim / pendente (S) | "Em 30 de junho de 2026: Caixa 4.709.000 · Empr" | BP Ativo, caixa 4.709.000; não há BP Passivo | Caixa confere; atribuição de data e fragmento "Empr". ITSA4_N5 (mesmo valor, com ressalva sobre a data) tem F = 1 |
| BBAS3_N3: variação do resultado líquido | presente / sim / SEM_DESVIO (sem afirmação) | "Resultado líquido no 1S26: 6.362.96" | DRE `6.362.961` | O corte gerou um número que, como valor, não está no contexto |
| AURE3_N2: resultado líquido | parcial / sim / pendente (sem afirmação) | "resultado líquido (prejuízo) … no 1S26 foi de **-1.0" | Não há DRE nem linha de lucro líquido; há vários valores iniciados por -1.0 (p. ex. prejuízo antes do IR -1.032.287 na DFC; prejuízos acumulados -1.032.285 no BP) | Afirma um conceito que o contexto não traz, com número incompleto |
| LAVV3_E2: caixa × empréstimos | parcial / sim / pendente (sem afirmação) | "Caixa (30 de junho de 2026): R$" | Caixa 192.713 | O corte removeu o valor |
| CEAB3_N4: componentes da variação | presente / sim / SEM_DESVIO (sem afirmação) | "a variação … entre o período anterior (204.384) e" | 204.384 está na DRE | Fragmento sem predicado; a rubrica registra 0 afirmações, mas o RAGAS pontuou |
| WEGE3_N4: idem | presente / sim / SEM_DESVIO (sem afirmação) | Só repete o enunciado até "…e o primeiro semestre de" | Não se aplica | Nenhum conteúdo factual, mas o fragmento foi pontuado |

**Categorias de causa:**
- **Erro de valor ou de cálculo:** nenhum demonstrado nos 10 [registro].
- **Associação conceitual inadequada:** nenhuma demonstrada; é apenas possível em AURE3_N2, cujo
  corte veio antes do valor.
- **Falta de sustentação pelo contexto:** AURE3_N2, porque o conceito afirmado não está no
  contexto [registro].
- **Atribuição temporal ou de entidade não literal:** está presente nos 4 zeros não truncados e em
  ITSA4_E2 [registro], mas **não é demonstrável como causa**, porque os veredictos não foram
  persistidos. Além disso, das 8 respostas não truncadas que nomeiam o período sem ressalva, 4 têm
  F = 0 (CEAB3_N3, IRBR3_N3, ITSA4_E3, ZAMP3_E3) e 4 têm F = 1 (ITSA4_N3, LWSA3_E2, POMO4_E2,
  VALE3_E2), todas com valores anotados como S [registro]. O mesmo padrão textual recebe
  veredictos opostos.
- **Efeito de truncamento observável:** em BBAS3_N3 (número cortado), LAVV3_E2 (valor removido),
  CEAB3_N4 e WEGE3_N4 (oração sem predicado) e, em parte, em AURE3_N2 [registro].
  - [código] Esses fragmentos são pontuados porque o extrator produziu afirmações. O RAGAS só
    devolveria NaN se não extraísse nenhuma.
- **[inferência]** Nos 4 zeros não truncados, o zero não é explicado pelo conteúdo numérico. Ele é
  compatível com um tratamento rigoroso e inconsistente do juiz para a atribuição de período e de
  entidade, que o contexto nunca contém.

## 8. Answer Relevancy = 0

### 8.1 Decomposição dos 75 zeros [registro]

| Grupo | Total | AR = 0 | AR > 0 | Zeros truncados / não truncados |
|---|---:|---:|---:|---|
| SEM_DESVIO com `abstencao_em_caso_presente` | 34 | 34 | 0 | 7 / 27 |
| SEM_DESVIO sem abstenção | 35 | 19 | 16 | 9 / 10 |
| ABSTENCAO_ADEQUADA | 17 | 15 | 2 | 7 / 8 |
| RESPOSTA_PARCIAL_ADEQUADA | 4 | 4 | 0 | 1 / 3 |
| EXTRAPOLACAO | 1 | 1 | 0 | 0 / 1 |
| PENDENTE_OPERACIONAL | 5 | 2 | 3 | 2 / 0 |
| **Total** | **96** | **75** | **21** | **26 / 49** |

- **Por truncamento:** AR = 0 em 26/36 truncados e em 49/60 não truncados.
- **Os 19 zeros de SEM_DESVIO sem abstenção:**
  - 14 respostas que entregam o valor pedido com ressalva: BBAS3_N1, BBAS3_N2, CEAB3_N2, IRBR3_N1,
    IRBR3_N5, ITSA4_E1, ITSA4_N2, ITUB4_N3, LAVV3_E3, LAVV3_N1, LAVV3_N2, LAVV3_N3, WEGE3_E3,
    ZAMP3_N2;
  - 5 sem entrega: CEAB3_E3, truncada depois de uma ressalva, e os fragmentos CEAB3_N4, IRBR3_N4,
    LAVV3_N4 e WEGE3_N4.
- **Contraste:**
  - as 14 entregas **sem** ressalva desse grupo têm todas AR > 0;
  - das 15 entregas **com** ressalva, só ITSA4_N5 tem AR > 0.

### 8.2 Marcadores textuais de ressalva (exploratórios)

Os marcadores foram definidos **depois da observação dos scores** e não são variável
pré-registrada. As regex estão em `tabelas_mecanicas_ragas.json`, em `definicoes`.

| | n | AR = 0 | AR > 0 |
|---|---:|---:|---:|
| Com ressalva ("não é possível…", "não especifica/menciona/contém…") | 72 | **69** | 3 (ITSA4_N5, POMO4_E1, POMO4_E3) |
| Sem ressalva | 24 | 6 | 18 |

Os 6 zeros sem ressalva são todos respostas truncadas:
- 5 cortadas antes de qualquer afirmação completa ou declaração: CEAB3_N4, IRBR3_N4, LAVV3_E2,
  LAVV3_N4, WEGE3_N4;
- AURE3_E3, pendente, com uma afirmação S anotada antes do corte.

**[inferência]** O AR = 0 acompanha a expressão de incerteza ou limitação, o que é compatível com a
marca `noncommittal`, mais do que a entrega da informação.

### 8.3 Amostra qualitativa

A seleção cobre cada grupo exigido e inclui os contraexemplos, que distinguem o mecanismo de uma
coincidência.

| Tipo | Casos | F / AR | Observação |
|---|---|---|---|
| Abstenção em caso `presente` | POMO4_N5, VALE3_N5 | 1 / 0 | A única afirmação é "as tabelas não especificam as datas", verdadeira sobre a representação |
| Abstenção que também entrega o valor | BBAS3_N5, ITUB4_N5 | 1 / 0 | Entrega o valor e mesmo assim tem AR 0 |
| Abstenção adequada (ausente) | AURE3_N1, VALE3_N1 | 1 / 0 | Mesmo par de scores da abstenção indevida |
| Abstenção adequada com AR > 0 | POMO4_E1 (0,571), POMO4_E3 (0,637) | 1 / >0 | O zero não é determinístico |
| SEM_DESVIO que entregou e teve AR 0 | WEGE3_E3, ZAMP3_N2, IRBR3_N5 | 1 / 0 | Valor (e comparação) corretos, com ressalva sobre o período |
| Contraste | ITSA4_N5 (com ressalva) | 1 / 0,890 | Exceção à regra da ressalva |
| Contraste | ITSA4_N3, VALE3_E2 (sem ressalva) | 1 / >0,8 | Entrega sem ressalva, AR alto |
| Resposta parcial | CEAB3_E2, WEGE3_E2, AURE3_N3, VALE3_N4 | 0,5–0,889 / 0 | Entrega parte e declara a falta do resto |
| Truncada | WEGE3_N5 (só declaração) vs. CEAB3_N4 (fragmento) | 1 / 0 vs. 0 / 0 | Ver seção 9.3 |

## 9. Discordâncias, abstenções e truncamento

### 9.1 Discordância entre as métricas

**A. Faithfulness baixo / AR alto:** ZAMP3_E3 (0 / 0,940), ITSA4_E3 (0 / 0,915), AURE3_N2
(0 / 0,905), CEAB3_N3 (0 / 0,828).
- [código] O AR compara a pergunta com perguntas reconstruídas da resposta, sem olhar o contexto.
  O Faithfulness compara a resposta com o contexto.
- [inferência] Uma resposta que repete a entidade e o período da pergunta e afirma sem ressalva
  tende a gerar perguntas próximas da original, o que dá AR alto. Esses mesmos elementos não
  existem em nenhum contexto [registro].
- Não é uma regra fixa: o mesmo padrão tem F = 1 em 4 outros casos (seção 7).
- AURE3_N2 mostra que o AR não verifica a correção nem a completude do valor: a resposta para em
  "-1.0".

**B. Faithfulness = 1 / AR = 0 (47 casos) [registro]:**

| Grupo | Casos |
|---|---:|
| SEM_DESVIO com abstenção | 27 |
| SEM_DESVIO sem abstenção | 9 |
| ABSTENCAO_ADEQUADA | 9 |
| EXTRAPOLACAO | 1 |
| PENDENTE_OPERACIONAL (AURE3_E3) | 1 |

- Abstenções indevidas (POMO4_N5) e adequadas (VALE3_N1) têm o mesmo par 1 / 0.
- VALE3_E3, a única EXTRAPOLACAO, tem F = 1. A rubrica a anotou como E, critérios (a) e (c):
  ela usou a linha `Resultado financeiro, líquido` da DFC, com sinal de ajuste, como se fosse o
  resultado financeiro.
- [inferência] O Faithfulness não detecta associação conceitual inadequada quando a linha existe
  literalmente no contexto.

**C. Ambas baixas:** CEAB3_N4 (0 / 0), WEGE3_N4 (0 / 0), LAVV3_E2 (0 / 0), LAVV3_N4 (0,333 / 0),
IRBR3_N4 (0,25 / 0).
- Todas foram truncadas antes de qualquer afirmação completa ou declaração [registro].
- [inferência] O fragmento é vago, compatível com `noncommittal`, e as afirmações extraídas dele
  não são verificáveis.
- Os fragmentos cortados depois do início de um valor têm AR > 0 e F baixo: BBAS3_N3, AURE3_N2,
  ZAMP3_E2.

### 9.2 As 34 abstenções em caso `presente`

**[registro]**

| Medida | Valor |
|---|---|
| Faithfulness médio | 0,930 |
| Casos com F = 1 | 27 |
| Casos com F < 1 | 7: CEAB3_N5, ITUB4_E3 (truncada), ITUB4_N4, WEGE3_E1, WEGE3_N2, ZAMP3_E1, ZAMP3_N1 |
| Answer Relevancy | 0 nos 34 |
| Abstenções que também entregam o valor (`entrega_informacao_sustentada`) | 12 (F médio 1,0; AR 0) |
| F médio das 22 que não entregam o valor | 0,892 |

A interpretação proposta (o Faithfulness avalia a sustentação das afirmações; o AR penaliza
respostas que não atendem à pergunta; logo, uma abstenção indevida pode ser fiel e pouco
relevante) **se confirma no mecanismo e precisa de dois refinamentos:**

1. **O Faithfulness alto não atesta a adequação da abstenção.** A afirmação "o contexto não
   especifica o período" é literalmente verdadeira, porque 0/96 contextos têm data. O Faithfulness
   avalia a coerência com o texto do contexto, não a convenção do protocolo para atual/anterior.
2. **O AR = 0 não é específico de "não atender à pergunta".** Ele ocorre em:
   - 15/17 abstenções adequadas;
   - 4/4 respostas parciais adequadas;
   - na única EXTRAPOLACAO;
   - em 14 das 15 respostas SEM_DESVIO sem abstenção que entregaram o valor com ressalva;
   - nas 12 abstenções que também entregaram o valor.

Formulação compatível com os dados [inferência]: o Faithfulness verifica se as afirmações são
inferíveis do texto do contexto, inclusive afirmações sobre o que o contexto não contém. O AR,
nesta configuração, zera respostas que expressam incerteza ou limitação, seja a limitação
procedente ou não e tenha a informação sido entregue ou não. **O par F alto / AR zero não
distingue abstenção adequada de indevida.**

Comparação com os 35 casos `presente` sem a marca: F médio 0,674; 16 com AR > 0, dos quais 14
entregam o valor sem ressalva.

### 9.3 Truncamento [registro]

Esta seção é descritiva: não há teste de hipótese nem conclusão causal.

| | F = 0 | F > 0 | n |
|---|---:|---:|---:|
| Truncado | 6 (16,7%) | 30 (83,3%) | 36 |
| Não truncado | 4 (6,7%) | 56 (93,3%) | 60 |

Os truncados são 37,5% dos 96 e 60% dos zeros de Faithfulness. Por subgrupo:

| Subgrupo | n | F médio | F = 0 |
|---|---:|---:|---|
| Truncadas antes de qualquer afirmação completa ou declaração (0 afirmações, sem declaração) | 8 | **0,115** | 5: AURE3_N2, BBAS3_N3, CEAB3_N4, LAVV3_E2, WEGE3_N4 |
| Demais truncadas (com afirmação ou declaração) | 28 | **0,846** | 1: ITSA4_E2 |
| Não truncadas | 60 | **0,844** | 4 |

- **Truncadas cujo único conteúdo é uma declaração de limitação** (0 afirmações, com declaração;
  8 casos):
  - F = 1 em 6: AURE3_N4, LAVV3_N5, LWSA3_N3, POMO4_N3, WEGE3_N3, WEGE3_N5;
  - F = 0,5 em 2: ITUB4_E3, VALE3_E1.
- **Mecanismos observáveis nos zeros truncados:**
  - número cortado: BBAS3_N3, AURE3_N2;
  - valor removido: LAVV3_E2;
  - oração sem predicado: CEAB3_N4, WEGE3_N4.
- [código] O RAGAS pontua fragmentos que a rubrica exclui (Convenção 1).
- [inferência] O truncamento sozinho não acompanha a perda de sustentação. A associação se
  concentra nas respostas cortadas antes de qualquer conteúdo completo.

## 10. Achados descritivos preservados

Nenhum destes achados é afirmação causal.

1. Faithfulness: média 0,784, mediana 1,000; 57/96 scores iguais a 1.
2. Answer Relevancy: média 0,160, mediana 0; 75/96 scores iguais a 0.
3. 69 das 72 respostas com marcadores textuais de ressalva têm AR = 0. Os marcadores são
   exploratórios.
4. 34/34 casos `presente` com `abstencao_em_caso_presente` têm AR = 0.
5. O par Faithfulness alto / Answer Relevancy zero não distingue abstenção adequada de indevida.
6. Faithfulness alto não garante adequação semântica ou conceitual.
7. A única EXTRAPOLACAO comportamental (VALE3_E3) recebeu Faithfulness = 1.
8. Entre os 10 casos com Faithfulness = 0, nenhum apresenta erro de valor ou de cálculo
   demonstrável. As causas dos 4 zeros não truncados não podem ser determinadas diretamente,
   porque os veredictos intermediários não foram persistidos.
9. Truncados: 6/36 com Faithfulness = 0. Não truncados: 4/60.
10. Faithfulness médio: 0,115 nas 8 respostas truncadas antes de conteúdo completo; 0,846 nas
    outras 28 truncadas; 0,844 nas não truncadas.

## 11. Correções registradas

1. **Answer Relevancy e `noncommittal`** (seção 6): o score só zera quando as três gerações são
   marcadas `noncommittal`. O relatório descritivo anterior dizia que bastava "alguma".
2. **Na consolidação da análise qualitativa**, a conferência com as tabelas mecânicas corrigiu duas
   formulações do relato anterior em conversa. Os números não mudaram.
   - O relato dizia que os 6 zeros de AR sem ressalva eram "fragmentos sem conteúdo". O correto:
     os 6 são truncados; 5 não têm afirmação completa nem declaração, e AURE3_E3 tem uma afirmação
     S anotada antes do corte (seção 8.2).
   - O relato listava 6 respostas truncadas iniciadas por abstenção, "todas com F = 1". O correto:
     são 8 truncadas cujo único conteúdo é uma declaração de limitação, 6 com F = 1 e 2 com F = 0,5
     (ITUB4_E3, VALE3_E1) (seção 9.3).

## 12. Limitações metodológicas

1. **Intermediários não persistidos.** Afirmações extraídas, veredictos, perguntas geradas e marcas
   `noncommittal` não foram gravados. Toda causa caso a caso é inferência.
2. **Variabilidade do juiz não estimada.** Houve uma execução por caso (fora as 2 reavaliações por
   NaN ou interrupção), sem repetição suficiente para estimar a variabilidade do juiz RAGAS. O
   contraste 4 × 4 da seção 7 pode refletir essa variabilidade ou fatores não examinados.
3. **Marcadores exploratórios.** Os marcadores textuais de ressalva foram definidos depois da
   observação dos scores, não foram validados e não são variável pré-registrada. As contagens
   dependem das regex.
4. **Contexto sem entidade e sem data.** Nenhum dos 96 contextos contém o nome da empresa nem
   marca de período ou data. Isso afeta tanto o Faithfulness (atribuições não literais) quanto a
   interpretação das abstenções.
5. **Apoio de LLM na anotação.** A anotação comportamental teve apoio de LLM, como está documentado
   em `comportamento/CONVENCOES_ANOTACAO_COMPORTAMENTO.md` e em `RATIFICACAO_COMPORTAMENTO.md`. As
   leituras por classe dependem dessa anotação.
6. **Análise posterior aos scores.** A análise é exploratória e foi feita depois da observação dos
   scores. Os padrões descritos geram hipóteses; não as testam.
7. **"Correto" quer dizer coerente com o contexto.** Valores e cálculos foram conferidos contra o
   contexto, não contra o gabarito nem contra a exatidão, que não foram consultados.
8. **Grupos pequenos.** RESPOSTA_PARCIAL_ADEQUADA tem 4 casos, EXTRAPOLACAO 1 e os pendentes 5;
   não há ALUCINACAO.
9. **Empates.** Os empates (75 zeros de AR e 57 uns de F) limitam a correlação e as listas de
   extremos.
