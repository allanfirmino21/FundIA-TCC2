# Adendo metodológico: revisão humana dos gabaritos (Protocolo, Seção 13, item 8)

**Data:** 2026-10-08.

**Documento de referência:** `avaliacao/ragas/PROTOCOLO_RAGAS_TCC2.md`, SHA-256
`3f6f8e030bf4f44d2882b65005431b8b7ff95df54bb479fa8e53e5a9b2c3925b`, inalterado.

**Registro da revisão:** commit `9dc164a19a1c5f0c399a4950461e8b63ec4cbfc9`
("Preservar revisao humana dos 96 gabaritos TCC2").

**Natureza:**
- Este adendo é **separado** do protocolo. O protocolo congelado, as Emendas 1 a 4, o dataset e os
  resultados não foram editados.
- O adendo registra como a revisão dos gabaritos foi de fato executada e em que ela difere do que foi
  planejado.
- O adendo não é uma emenda: não muda nenhuma regra, classe, métrica ou critério de decisão.

## 1. Resultado da revisão

Os 96 gabaritos de `avaliacao/ragas/dataset_tcc2.json` (SHA-256
`313bdf359fdeabb063ceec3bcca12ebfe3b52caae346b3ff1d9f3dc23196bc5e`) foram revisados pelo autor
de 2026-10-06 a 2026-10-08.

| Situação | Casos |
|---|---:|
| Confirmados | **96** (2 confirmados com ressalva: IRBR3_N2 e POMO4_E1) |
| Corrigidos | **0** |
| Pendentes | **0** |

Nenhum gabarito, valor exigido, sinal exigido ou classificação de disponibilidade foi alterado. As
decisões provisórias de AURE3_N2 e AURE3_N3 (PENDENTE, para verificação documental) foram
substituídas por CONFIRMAR depois da conferência no pacote oficial da CVM. Elas aparecem como
histórico e não contam como decisões finais.

## 2. Desvio de ordem em relação ao §13.8

- **Procedimento planejado:**
  - O §13.8 prevê "revisão manual de 100% dos 96 gabaritos antes da execução do RAGAS e antes da
    primeira resposta".
  - A Seção 17 repete o critério: "ground truth … com revisão manual de 100%".
- **O que existia antes da coleta:** só a revisão técnica feita pelo Claude Code (`revisao_tecnica`
  e `revisao_tecnica.revisao_final` no dataset). O próprio dataset e `RELATORIO_validacao_dataset.md`
  declaram que ela **não** substitui a revisão humana.
- **Procedimento executado:** a revisão humana dos 96 gabaritos foi feita **depois** de todas estas
  etapas:
  - a coleta das 96 respostas;
  - a verificação de exatidão (congelada no commit `d49835d`);
  - a anotação e ratificação do comportamento (commit `cd29dee`);
  - a avaliação RAGAS (commit `d78d5a5`);
  - a análise dos resultados RAGAS (commit `8844743`).

  **A ordem prevista no protocolo não foi cumprida.**
- **Consequência:**
  - O procedimento foi **retrospectivo**. Ele confirma, depois do fato, os gabaritos já usados nas
    etapas anteriores, mas não cumpre a função preventiva que o §13.8 lhe atribuía.
  - Como a revisão humana confirmou os 96 gabaritos sem correções, não houve alteração do dataset nem
    necessidade de recalcular as avaliações em decorrência dessa revisão. Os resultados anteriormente
    obtidos permanecem preservados. Essa constatação não elimina as limitações metodológicas
    decorrentes da realização retrospectiva da revisão, da ausência de cegamento e do apoio de IA na
    organização das evidências.
  - Conforme a metodologia registrada no protocolo (Seção 13), a avaliação RAGAS não utiliza esses
    gabaritos como referência. Eles servem à verificação de exatidão e à classificação de
    comportamento.

## 3. Ausência de cegamento, apoio de modelo e risco de ancoragem

1. **Sem cegamento.**
   - Quando revisou os gabaritos, o autor já conhecia os resultados de exatidão e do RAGAS.
   - Os resultados de exatidão tinham sido analisados nesta mesma etapa do trabalho.
   - Durante a revisão, os resultados RAGAS não foram consultados nem usados como critério.
   - Mesmo assim, o conhecimento prévio dos resultados não pode ser descartado como influência.
2. **Evidências organizadas com apoio de modelo.**
   - O Claude Code (modelo de linguagem):
     - selecionou as contas e extraiu as linhas do CSV oficial e do contexto congelado;
     - calculou reconciliações e propôs o agrupamento dos casos;
     - redigiu as apresentações com "particularidades e riscos";
     - registrou o texto das decisões ditadas pelo autor.
   - As opções foram apresentadas de forma neutra (CONFIRMAR, CONFIRMAR exceto, CORRIGIR, PENDENTE).
   - Cada decisão só foi registrada depois de comunicada explicitamente pelo autor.
3. **Risco de ancoragem.**
   - O autor decidiu sobre evidências selecionadas e enquadradas pelo modelo, então as decisões
     podem ter sido ancoradas nessa apresentação.
   - O dataset também foi construído e revisado tecnicamente com apoio do mesmo tipo de ferramenta.
   - O resultado de 96 confirmações e 0 correções é compatível tanto com gabaritos corretos quanto
     com essa falta de independência. Este adendo não separa as duas explicações.
   - Atenuantes:
     - conferência contra o pacote oficial da CVM, uma fonte externa ao pipeline avaliado
       (SHA-256 `0e1ef74291d2143e7bb55247b01c8bbd94995d995536f70f0d19de1d79d7e38c`);
     - recálculo mecânico de valores e derivados;
     - controle negativo com defeitos plantados.

     Os atenuantes reduzem o risco, mas não o eliminam.
4. **Avaliador único.** Não houve segundo revisor humano nem medida de concordância.

## 4. Conferência mecânica (Etapa 0) e revisão humana

- **Etapa 0.** Conferência mecânica e determinística, sem LLM, feita pelo Claude Code com
  `etapa0_preconferencia.py` em 2026-10-08.
  - Contra o pacote oficial da CVM e o contexto congelado, conferiu:
    - versões dos documentos;
    - linhas-fonte e valores;
    - períodos acumulados;
    - derivados;
    - sinal exigido;
    - texto do gabarito;
    - disponibilidade.
  - Resultado: 0 problemas nos 96 casos, com 7 avisos nos 78 casos de grupo e 1 nos 18 de atenção
    humana.
  - Controle negativo: 5 defeitos plantados numa cópia temporária do dataset, todos detectados.
  - **A Etapa 0 não é revisão humana.** Ela serviu para agrupar os casos e apontar os que exigiam
    atenção. Seus avisos não decidiram nenhum caso.
- **Revisão humana.** Foram as decisões do autor, caso a caso ou por grupo, cada uma com justificativa
  e data:
  - 18 casos de atenção humana, em 5 blocos;
  - 77 casos em 10 grupos;
  - 1 caso em revisão individual (POMO4_E1).

## 5. Ambiguidade entre as regras 2 e 4 da Seção 9 (POMO4_E1)

**Texto das regras:**
- **Regra 2:** "Uma linha da DFC consolidada que traz o resultado do período … conta como `presente`
  para N2 e N3."
- **Regra 4:** "Indicadores derivados (E1 margem, E2 caixa × dívida): `presente` com todos os
  insumos no contexto; `parcial` com parte deles; `ausente` sem nenhum."

**A ambiguidade:**
- A regra 2 autoriza a DFC expressamente só para N2/N3 e não diz se vale para insumos de indicadores
  derivados.
- A regra 4 não exige que os insumos venham da DRE.
- Em POMO4_E1 (margem líquida do 1S26), o numerador (3.11, 535.824 mil) está no contexto apenas como
  "Resultado do período" da DFC consolidada, com o mesmo conceito, período, base e sinal.
- A receita (3.01) está ausente do contexto.
- Lendo a regra 2 como restrição geral, o caso seria `ausente` (0/2).
- Lendo a regra 4 pelos insumos, o caso é `parcial` (1/2).

**Decisão do autor:**
- Mantém o gabarito (13,30%) e a disponibilidade **`parcial`**.
- O fundamento é o **pré-registro do próprio protocolo congelado**: "POMO4, E1 (`parcial`): o
  resultado está no contexto, a receita não".
- Mudar para `ausente` contrariaria esse pré-registro e alteraria uma classificação congelada depois de
  observadas as respostas, o que a Seção 17 veda.

**Registro:**
- A ambiguidade de redação fica registrada aqui, sem alteração retroativa do protocolo.
- Os avisos da Etapa 0 para este caso refletem uma implementação mais restritiva da regra 2 e não
  são, isoladamente, evidência de erro.

## 6. Alcance da confirmação

- A confirmação diz respeito **só aos gabaritos**: valores de referência, contas-fonte, valores
  exigidos, sinal e disponibilidade.
- Ela **não** confirma, valida nem avalia as respostas produzidas pelo FundIA.
- A qualidade das respostas é medida separadamente:
  - pela verificação de exatidão;
  - pela anotação de comportamento;
  - pelas métricas RAGAS.

  Essas medidas têm suas próprias limitações.
- Nos casos N4, a confirmação se refere à consistência contábil da decomposição, sem atribuir
  causalidade econômica.

## 7. Documentos e evidências preservados (commit `9dc164a`)

Todos em `avaliacao/ragas/avaliacao_tcc2/revisao_gabaritos/`:

| Arquivo | Conteúdo | SHA-256 |
|---|---|---|
| `REVISAO_HUMANA_GABARITOS.md` | documento consolidado: 96 decisões finais, balanço, 13 ressalvas, POMO4_E1, natureza das etapas, risco de ancoragem e referência ao pacote CVM | `8e9a94feec55aa65cb5782548b0f530406ad58b8d0506c97cddb00fb0a824546` |
| `decisoes_revisao_humana.md` | registro cronológico de trabalho, com decisões provisórias e evidência por caso | `f095f3ca0ef3da830210e9ccdc71e9242393dabdfaba61ea2b6d77a122f1791b` |
| `etapa0_resultado.json` | resultado da Etapa 0 | `28a3f39faf0c8b4e588b4951380216d8f2883309c0437ff3aef1a78d99061bc1` |
| `controle_negativo_etapa0.md` | controle negativo (comando e saída, transcritos do log da sessão) | ver `REVISAO_HUMANA_GABARITOS.md`, Seção 6 |
| scripts e saídas de evidência | `etapa0_preconferencia.py`, `etapa0_controle.py`, `g8_`/`g9_`/`g10_`/`pomo4_e1_evidencias.py` e `.txt`, `integridade_registro.py`, `tabela_decisoes_finais.py` | ver `REVISAO_HUMANA_GABARITOS.md`, Seção 6 |

**Evidências não preservadas:**
- Nos blocos 1–5 e nos grupos G1–G7, as evidências vieram em parte de comandos pontuais de leitura que
  não foram salvos como arquivos.
- Esses comandos **não** foram reconstruídos.
- O que está preservado para esses casos:
  - as linhas-fonte e o diagnóstico de disponibilidade de cada caso em `etapa0_resultado.json`;
  - a evidência descrita no registro cronológico.

## 8. Como apresentar este procedimento

- A revisão humana dos gabaritos foi **retrospectiva**: feita depois das etapas que usam os gabaritos,
  sem cegamento, com evidências organizadas com apoio de modelo e por um único avaliador.
- Ela **não deve ser apresentada como validação independente nem prospectiva** dos gabaritos.
- A formulação adotada é: "Foi realizada uma revisão humana retrospectiva de 100% dos gabaritos pelo
  autor, com evidências organizadas com apoio de inteligência artificial, após a coleta e as
  avaliações originalmente previstas."
- Ela deve vir acompanhada das limitações declaradas neste adendo.
