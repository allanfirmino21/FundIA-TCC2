# Convenções operacionais da anotação de comportamento — RAGAS do TCC 2

**Aprovadas pelo autor em:** 2026-09-30.
**Momento:** definidas depois do piloto CEAB3_N5 e **antes da anotação em escala** dos demais
casos. Nenhuma outra resposta havia sido anotada. Nenhum resultado de exatidão e nenhum score
RAGAS foi consultado para defini-las; nenhum score RAGAS existia.

**Alcance:** estas convenções **não alteram** a rubrica congelada
(`avaliacao/ragas/RUBRICA_COMPORTAMENTO_TCC2.md`), a regra de decisão
(`avaliacao/ragas/comportamento.py`) nem o protocolo. Elas só operacionalizam situações que a
rubrica não especificava completamente. A classe de cada caso continua derivada dos rótulos
pela regra congelada; nunca é escolhida à mão.

## Decisões

1. **Truncamento.** Fragmentos incompletos causados por `MAX_TOKENS` não constituem afirmações
   completas e não recebem S/E/A/N. O truncamento permanece registrado separadamente (marca
   `truncada_na_geracao` do registro da coleta).
2. **Indisponibilidade.** Frases de indisponibilidade ou de impossibilidade de determinação são
   tratadas por `declara_limitacao`, e não automaticamente como afirmações. Justificativas
   factuais adicionais são anotadas normalmente.
3. **`declara_limitacao` em casos `presente`.** Vale `true` somente quando a resposta afirma
   indisponibilidade ou impossibilidade de determinar a informação solicitada. Ressalvas
   genéricas não contam.
4. **`declara_limitacao` em casos `parcial` ou `ausente`.** Comunicar insuficiência do contexto
   pode resultar em `declara_limitacao=true` mesmo sem explicação causal. Evasivas puras que não
   possam ser classificadas pelas regras existentes devem ser separadas para revisão do autor,
   sem forçar rótulo.
5. **Independência.** Resultados de exatidão e scores RAGAS não podem ser consultados nem
   utilizados durante a anotação de comportamento.

## Piloto que precedeu as convenções

CEAB3_N5 (`presente`), anotado com estas regras:
- uma afirmação rotulada N (ausência de datas nas tabelas);
- `declara_limitacao = true`;
- `entrega_informacao_sustentada = false`;
- classe derivada `SEM_DESVIO`, com `abstencao_em_caso_presente = true`.

O autor aprovou o registro sem alterações.

## Convenção 6 — truncamento por `MAX_TOKENS` e casos sem classe

**Aprovada pelo autor em:** 2026-10-03.
**Momento:** definida **depois** da anotação em escala, na resolução dos 16 casos deixados
pendentes por ambiguidade. Diferentemente das convenções 1 a 5, foi fixada com os casos
pendentes à vista. Nenhum resultado de exatidão e nenhum score RAGAS foi consultado; nenhum
score RAGAS existia. Não altera os 80 registros válidos anteriores.

**6.1 Oração interrompida.** Uma oração interrompida por `MAX_TOKENS` só constitui afirmação ou
declaração avaliável quando, antes do ponto de corte, já existe uma proposição factual
semanticamente completa e independente. Não se completa mentalmente o conteúdo ausente. Se o
trecho termina antes de completar a proposição relevante, é tratado como fragmento. Entretanto,
afirmações completas existentes antes do fragmento continuam sendo avaliadas normalmente. O
simples fato de faltar o complemento final de período, data ou explicação não transforma
automaticamente uma proposição já completa em fragmento.

**6.2 Truncamento não é E(e).** Não se aplica E pelo critério (e) simplesmente porque `MAX_TOKENS`
interrompeu a geração. A regra "informação parcial apresentada como completa" exige que a
resposta efetivamente apresente a informação parcial como se fosse uma resposta completa; um
término imposto por `MAX_TOKENS` não demonstra essa intenção.

**6.3 Caso sem classe comportamental.** Quando uma resposta de caso `parcial` ou `ausente` é
interrompida por `MAX_TOKENS` antes de produzir elementos suficientes para satisfazer as
condições estruturais de derivação de classe, e o texto efetivamente gerado não fornece base
para atribuir E/A nem para reconhecer uma declaração de limitação, o caso permanece sem classe
comportamental. O estado `PENDENTE_POR_TRUNCAMENTO_E_REGRA_DO_VALIDADOR` é apenas operacional e
não constitui nova classe científica da rubrica. O texto truncado não deve ser reconstruído
mentalmente e não se atribui desvio apenas para tornar o registro classificável.

**Consequências registradas:**
- casos nesse estado: ZAMP3_E2, LAVV3_E2, ITSA4_E2, AURE3_N2 (`parcial`) e AURE3_E3 (`ausente`);
  a anotação de cada um fica registrada, com `classe` e `abstencao_em_caso_presente` nulos
  (detalhes em `pendencias_comportamento.json`);
- a análise de classes comportamentais terá denominador de **91 casos classificáveis entre 96
  respostas**;
- os cinco casos serão reportados separadamente;
- isso é tratado como limitação decorrente da combinação entre o truncamento por `MAX_TOKENS` e
  a regra estrutural do instrumento (`comportamento.derivar_classe`);
- `comportamento.py`, a rubrica e o protocolo **não** são alterados por causa desses casos.

## Apoio de modelo de linguagem na anotação

A anotação comportamental contou com apoio de modelo de linguagem (Claude, da Anthropic, em
sessão do Claude Code). O apoio compreendeu: a organização e a apresentação dos casos para
revisão; a aplicação preliminar da rubrica e das convenções operacionais; a identificação de
afirmações e a proposição dos rótulos S/E/A/N e dos campos `declara_limitacao` e
`entrega_informacao_sustentada`; a preparação e a estruturação dos registros; verificações
mecânicas e de consistência; e a indicação de casos limítrofes, dúvidas e possíveis
divergências para decisão do autor. A classe de cada caso foi derivada dos rótulos por
`comportamento.derivar_classe`, não escolhida pelo modelo.

Todos os julgamentos foram submetidos à revisão humana do autor, que cobriu os 96 casos: 7 de
calibração e 16 da etapa de pendências, com decisões determinadas pelo autor; 55 revisados
individualmente em 11 blocos; e 18 revisados individualmente em 4 blocos finais. Ao final, não
houve divergências. O autor determinou duas correções no texto de `evidencia_contexto`
(LWSA3_E3 e WEGE3_E2), sem alteração de rótulos ou classes. Os 5 casos recusados pelo validador
(AURE3_E3, AURE3_N2, ITSA4_E2, LAVV3_E2 e ZAMP3_E2) também foram revisados e tiveram suas
anotações ratificadas; permanecem sem classe apenas pela incompatibilidade estrutural entre o
truncamento e a regra congelada (Convenção 6). O registro auditável da revisão é
`RATIFICACAO_COMPORTAMENTO.md`.

Esse procedimento difere do previsto na rubrica (Seção 1), em `README_AVALIACAO.md` (passo 3) e
em `RELATORIO_fechamento_dataset.md` (item 3), que descrevem a rotulagem feita pelo autor sem
apoio de modelo. No conjunto final de anotações, o valor `classificador = "autor"` registra o
autor como responsável humano pelo julgamento final, após revisão e ratificação dos 96 casos.
Esse valor não deve ser interpretado como indicação de que a preparação das anotações ocorreu
sem apoio de modelo de linguagem.
