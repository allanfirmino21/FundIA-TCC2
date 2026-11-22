# Relatório de validação do dataset — RAGAS do TCC 2

Gerado por `validar_dataset.py` a partir de `dataset_tcc2.json` (fonte canônica). Protocolo: `avaliacao/ragas/PROTOCOLO_RAGAS_TCC2.md` (SHA-256 `e0b374608a1e4f5b…`). Construído em 2026-09-27T20:08:12+00:00 no commit `b17ea73`.

Nenhuma resposta foi gerada, nenhum LLM foi chamado e nenhum score RAGAS ou resultado de exatidão existe neste dataset.

## 1. Totais

- Empresas: **12**; casos: **96**
- Casos por categoria: E1 12, E2 12, E3 12, N1 12, N2 12, N3 12, N4 12, N5 12
- Casos por estrutura: banco 16, holding 8, nao_financeira 64, resseguradora 8
- Disponibilidade: presente **69**, parcial **15**, ausente **12** (estimativa pré-registrada: 69/15/12)
- Divergências em relação à estimativa: **0**
- Verificação determinística aplicável: **84** casos; N4 (não aplicável por definição): **12**
- Casos `presente` com exatidão aplicável: **61**

## 2. Gabaritos

- Valores esperados (nível principal): **126**; incluindo parcelas alternativas: 144
- Valores simples (uma conta CVM): **97**
- Valores derivados (fórmula sobre contas CVM): **29**
- Percentuais: **20**
- Casos com comparação temporal (1S26 e 1S25): **21**
- Casos com múltiplos valores esperados: **30**
- Casos com formas alternativas aceitas (total ou parcelas): **9**
- Valores que exigem sinal: **56**

## 3. Integridade

| Verificação | Resultado |
|---|---|
| ids duplicados | OK (0) |
| perguntas duplicadas | OK (0) |
| campos ausentes | OK (0) |
| documentos divergentes | OK (0) |
| versoes divergentes | OK (0) |
| hashes divergentes | OK (0) |
| codigos divergentes | OK (0) |
| estruturas divergentes | OK (0) |
| gabaritos sem fonte | OK (0) |
| derivados sem formula | OK (0) |
| valores nao parseaveis | OK (0) |
| chaves proibidas | OK (0) |
| divergencias sem justificativa | OK (0) |

## 4. Contexto recuperado por empresa

| Ticker | Versão | SHA-256 documento | Tabelas recuperadas (ordem) | Caracteres | SHA-256 contexto |
|---|---|---|---|---|---|
| WEGE3 | 1 | `500d0c0d51df…` | Balanço Patrimonial — Ativo → Demonstração de Fluxo de Caixa → Demonstração de Resultado | 10,620 | `a4cfe672d13e…` |
| BBAS3 | 1 | `96c321232278…` | Demonstração de Resultado → Balanço Patrimonial — Passivo → Balanço Patrimonial — Ativo | 8,807 | `666dea60db7d…` |
| ZAMP3 | 1 | `044d8ad11f53…` | Balanço Patrimonial — Ativo → Demonstração de Fluxo de Caixa → Demonstração de Resultado | 8,541 | `97e46bc582cc…` |
| LWSA3 | 1 | `e088ffd53f28…` | Demonstração de Fluxo de Caixa → Balanço Patrimonial — Ativo → Balanço Patrimonial — Passivo | 10,706 | `38df2447f93d…` |
| VALE3 | 3 | `32b625e17d4b…` | Demonstração de Fluxo de Caixa → Balanço Patrimonial — Ativo → Balanço Patrimonial — Passivo | 12,768 | `984ed325078f…` |
| ITUB4 | 1 | `409ed7c7a7a4…` | Demonstração de Resultado → Balanço Patrimonial — Passivo → Balanço Patrimonial — Ativo | 9,096 | `9f34e3f53bb7…` |
| LAVV3 | 1 | `7d18d8725fd0…` | Demonstração de Fluxo de Caixa → Balanço Patrimonial — Ativo → Demonstração de Resultado | 11,101 | `c0718250913f…` |
| POMO4 | 1 | `79bba9fbcdee…` | Balanço Patrimonial — Ativo → Demonstração de Fluxo de Caixa → Balanço Patrimonial — Passivo | 12,210 | `7d66585f5aa1…` |
| ITSA4 | 2 | `f252b1eb14ee…` | Demonstração de Fluxo de Caixa → Balanço Patrimonial — Ativo → Demonstração de Resultado | 10,918 | `b4cd4f4c907f…` |
| IRBR3 | 2 | `e528959c4a2c…` | Demonstração de Fluxo de Caixa → Balanço Patrimonial — Ativo → Demonstração de Resultado | 9,313 | `444b3d536da5…` |
| CEAB3 | 1 | `1dece32b1e39…` | Balanço Patrimonial — Ativo → Demonstração de Fluxo de Caixa → Demonstração de Resultado | 9,350 | `82517fbdad42…` |
| AURE3 | 1 | `9a3f3625a0e1…` | Demonstração de Fluxo de Caixa → Balanço Patrimonial — Ativo → Balanço Patrimonial — Passivo | 14,204 | `65175eccd1b6…` |

## 5. Disponibilidade por caso

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

`*` = diverge da estimativa pré-registrada.

## 6. Revisão técnica pré-coleta

- Casos revisados: **96/96** (revisor: Claude Code - revisão técnica pré-coleta)
- A revisão técnica **não** substitui a revisão humana de 100% exigida pela Seção 13 do protocolo; o dataset não está congelado.

### Casos que merecem atenção na revisão humana

| Caso | Motivo |
|---|---|
| BBAS3_N2 | Resultado consolidado (6,36 bi) difere do atribuído ao controlador (4,79 bi); ambos aparecem no contexto. |
| BBAS3_N4 | Maior componente é o IR/CS positivo (crédito) nos dois períodos, que cai 2,48 bi; a provisão para perda de crédito está em 'outras despesas e receitas operacionais'. |
| BBAS3_E3 | Despesas de intermediação sem sinal exigido; não comparável com ITUB4_E3 (Seção 8). |
| ZAMP3_N3 | Dois prejuízos: percentual sobre a magnitude (33,33%). Respostas com os dois valores numa mesma oração com 'prejuízo' exigirão decisão manual de sinal (regra 5). |
| LWSA3_E2 | Empréstimos e financiamentos da LWSA3 são integralmente 'Financiamento por Arrendamento' (19.361 + 52.554); gabarito segue as contas. |
| VALE3_N2 | Caso parcial: 'Lucros/Prejuízos Acumulados' do contexto (16.800.000) é o resultado dos controladores, não o consolidado (17.240.000). |
| VALE3_E2 | Dívida definida pelas contas 2.01.04 + 2.02.01 (inclui arrendamentos dentro de Empréstimos e Financiamentos; exclui debêntures participativas de 11,97 bi). |
| VALE3_E3 | Caso parcial: a DFC traz o resultado financeiro com sinal invertido (+2.237.000) em relação à DRE (−2.237.000). |
| ITUB4_E3 | Despesas de intermediação incluem a perda esperada de crédito; não comparável com BBAS3_E3 (Seção 8). |
| POMO4_N2 | Presente pela regra 2 da Seção 9: 'Resultado do período' da DFC igual ao consolidado da DRE (535.824). |
| POMO4_N4 | Parcial: DFC traz o resultado do período e o IR/CS com sinal invertido; o gabarito usa só a DRE. |
| ITSA4_N1 | Linha de topo da holding pelo plano de contas (receita de venda R$ 4,25 bi), embora o resultado seja dominado pela equivalência (R$ 9,35 bi, E1). |
| IRBR3_N4 | Cadeia do plano de seguros: 'despesas administrativas e outras' agrega 3.04 + 3.05 + 3.06; o sinal atípico das despesas financeiras afeta o componente financeiro. |
| IRBR3_E1 | Linha 'Resultado Bruto' da DRE de resseguradora, negativa no 1S26 (−41,0 mi) e positiva no 1S25; sinal exigido. |
| IRBR3_E2 | 'Despesas Financeiras' positiva no 1S26 (+106,8 mi, como entregue à CVM) compõe o resultado financeiro de +117,8 mi. |
| IRBR3_E3 | Decisão da Emenda 1: gabarito = conta 1.01.02 'Aplicações Financeiras' (ativo circulante), R$ 4.414.934 mil em 30/06/2026; pergunta passou a pedir o saldo registrado no ativo circulante. Antes: circulante + longo prazo = R$ 8.353.283 mil (1.01.02 + 1.02.01.01/.02/.03), agregação sem suporte no conceito pedido. |
| AURE3_N2 | Caso parcial com armadilha: no contexto há o resultado antes dos tributos (−1.032.287, DFC) e 'Lucros/Prejuízos Acumulados' (−1.032.285, controladores); o consolidado é −980.667. |
| AURE3_N3 | Dois prejuízos: percentual sobre a magnitude (92,72%); caso parcial. Mesmo alerta de sinal de ZAMP3_N3. |

## 7. Perguntas e gabaritos

A lista completa (pergunta, gabarito, fontes, disponibilidade e justificativa) está em `dataset_tcc2_revisao.csv`, derivado deste dataset.
