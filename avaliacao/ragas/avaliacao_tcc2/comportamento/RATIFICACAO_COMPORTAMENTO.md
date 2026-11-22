# Ratificação da anotação de comportamento — RAGAS do TCC 2

**Data da ratificação:** 2026-10-03.
**Arquivo ratificado:** `avaliacao/ragas/avaliacao_tcc2/comportamento/anotacoes_comportamento.json`
**SHA-256 desse arquivo no momento do registro:**
`c83cf6cef724f88ab35ac439978d13f0ad812c0ce25859ab7155eef97627b18f`

Este documento registra que os 96 casos da avaliação passaram por revisão humana caso a caso.
Ele não altera nenhum registro de anotação, a rubrica, o protocolo, `comportamento.py` nem o
executor. Não trata da redação metodológica sobre autoria da anotação, que será decidida em
etapa própria; o campo `classificador = "autor"` permanece como está.

## 1. Resultado

- **96/96 casos submetidos à revisão humana.**
- **Nenhuma divergência final.** Em todos os blocos de revisão o autor ratificou todos os casos
  apresentados.
- **Nenhuma sobreposição** entre os grupos de revisão: cada um dos 96 ids da coleta aparece em
  exatamente um grupo.
- Os **73 julgamentos provenientes da anotação em escala** (os 96 menos os 7 de calibração e os
  16 da etapa de pendências) foram **ratificados individualmente**, em 15 blocos.
- Durante a revisão, o autor determinou **duas correções** de texto de evidência (Seção 4),
  que não alteraram nenhum rótulo, campo ou classe.

## 2. Composição da revisão

| Grupo | Casos | Forma de revisão |
|---|---:|---|
| Calibração | 7 | decisões do autor no piloto e nos 6 casos-piloto, aprovadas antes da anotação em escala |
| Etapa de pendências | 16 | decisão do autor caso a caso: 11 classificados normalmente; 5 mantidos no estado operacional (Seção 3) |
| Revisão em 11 blocos | 55 | ratificação individual: truncados, `abstencao_em_caso_presente = true` e amostra mecânica |
| Revisão em 4 blocos finais | 18 | ratificação individual dos casos restantes |
| **Total** | **96** | |

**Calibração (7):** AURE3_N1, AURE3_N3, AURE3_N5, CEAB3_N3, CEAB3_N5, ITSA4_N5, POMO4_E1.

**Etapa de pendências (16):** AURE3_E3, AURE3_N2, AURE3_N4, BBAS3_N4, CEAB3_N4, IRBR3_E3,
ITSA4_E2, ITSA4_N4, ITUB4_E3, LAVV3_E2, LWSA3_N3, POMO4_E3, VALE3_E3, WEGE3_N3, ZAMP3_E2,
ZAMP3_N4.

**Revisão em 11 blocos (55):**

| Bloco | Casos |
|---:|---|
| 1 | AURE3_E1, AURE3_E2, BBAS3_N3, CEAB3_E3, IRBR3_N4 |
| 2 | ITUB4_N3, LAVV3_E3, LAVV3_N2, LAVV3_N3, LAVV3_N4 |
| 3 | LAVV3_N5, LWSA3_E3, LWSA3_N2, POMO4_N3, POMO4_N4 |
| 4 | VALE3_E1, WEGE3_E2, WEGE3_N4, WEGE3_N5, ZAMP3_N3 |
| 5 | BBAS3_E1, BBAS3_E2, BBAS3_E3, BBAS3_N5, CEAB3_N1 |
| 6 | IRBR3_E1, IRBR3_E2, IRBR3_N2, ITSA4_N1, ITUB4_E1 |
| 7 | ITUB4_E2, ITUB4_N1, ITUB4_N2, ITUB4_N4, ITUB4_N5 |
| 8 | LAVV3_E1, LWSA3_N5, POMO4_N2, POMO4_N5, VALE3_N5 |
| 9 | WEGE3_E1, WEGE3_N1, WEGE3_N2, ZAMP3_E1, ZAMP3_N1 |
| 10 | ZAMP3_N5, IRBR3_N5, CEAB3_E2, ITSA4_N2, CEAB3_N2 |
| 11 | VALE3_N4, LWSA3_N4, BBAS3_N2, LWSA3_E2, ITSA4_E1 |

Blocos 1–4: casos truncados por `MAX_TOKENS` (20). Blocos 5–10 (até ZAMP3_N5): casos com
`abstencao_em_caso_presente = true` não truncados (26). Restante dos blocos 10–11: amostra
mecânica (9), escolhida pela ordem de SHA-256(`"ratificacao-comportamento-tcc2|<id>"`), sem
consulta ao conteúdo. As fichas desses 55 casos estão em `RESUMO_RATIFICACAO_COMPORTAMENTO.md`
(gerado antes das correções da Seção 4; ver a nota abaixo).

**Revisão em 4 blocos finais (18):**

| Bloco | Casos |
|---:|---|
| 1 | BBAS3_N1, CEAB3_E1, IRBR3_N1, IRBR3_N3, ITSA4_E3 |
| 2 | ITSA4_N3, LAVV3_N1, LWSA3_E1, LWSA3_N1, POMO4_E2 |
| 3 | POMO4_N1, VALE3_E2, VALE3_N1, VALE3_N2, VALE3_N3 |
| 4 | WEGE3_E3, ZAMP3_E3, ZAMP3_N2 |

Em cada ficha de revisão foram apresentados: pergunta, disponibilidade congelada, resposta
congelada completa, afirmações e rótulos, `declara_limitacao`, `entrega_informacao_sustentada`,
classe derivada, `abstencao_em_caso_presente`, contexto necessário e justificativa registrada.
Nenhum resultado de exatidão e nenhum score RAGAS foi consultado; nenhum score RAGAS existe.

**Nota sobre `RESUMO_RATIFICACAO_COMPORTAMENTO.md`:** o arquivo foi preservado sem alterações e
sem caixas marcadas. As fichas de LWSA3_E3 e WEGE3_E2 nele contidas mostram o texto de evidência
anterior às correções da Seção 4. A ratificação está registrada neste documento, não no resumo.

## 3. Os 5 casos recusados pelo validador

Estado do validador observado na data deste registro
(`avaliar_respostas_tcc2.py comportamento --validar`): **91 válidos e 5 recusados**
(`{"VALIDO": 91, "INCOMPLETO": 0, "INVALIDO": 5}`).

| Caso | Disponibilidade |
|---|---|
| AURE3_E3 | ausente |
| AURE3_N2 | parcial |
| ITSA4_E2 | parcial |
| LAVV3_E2 | parcial |
| ZAMP3_E2 | parcial |

- Esses 5 casos **foram revisados por humano**: fazem parte dos 16 decididos pelo autor na etapa
  de pendências, e as anotações registradas para eles foram aprovadas pelo autor.
- Eles permanecem **sem `classe` e sem `abstencao_em_caso_presente`** porque as respostas foram
  interrompidas por `MAX_TOKENS` antes de produzir elementos que permitam derivar uma classe, e a
  regra congelada (`comportamento.derivar_classe`) recusa caso `parcial` ou `ausente` sem
  afirmação E/A e sem declaração de limitação. É uma incompatibilidade estrutural entre o
  truncamento e a regra do validador (Convenção 6 de `CONVENCOES_ANOTACAO_COMPORTAMENTO.md`;
  estado operacional `PENDENTE_POR_TRUNCAMENTO_E_REGRA_DO_VALIDADOR`).
- Essa pendência operacional **não é divergência humana** e **não é anotação incompleta**: a
  revisão desses casos está concluída; o que falta é apenas uma classe que a regra congelada não
  consegue derivar.
- Documentação técnica de cada caso: `pendencias_comportamento.json`.

## 4. Correções determinadas pelo autor durante a revisão

Ambas alteraram **somente** o texto do campo `evidencia_contexto` da 2ª afirmação do registro.
**Não** alteraram rótulo (a afirmação continua S), classe, `declara_limitacao`,
`entrega_informacao_sustentada` nem `abstencao_em_caso_presente`.

1. **LWSA3_E3** (bloco 3), classe `ABSTENCAO_ADEQUADA`.
   - Antes: "Não há linha de resultado financeiro, receitas financeiras ou despesas financeiras
     no contexto."
   - Depois: "O contexto contém DFC, BP Ativo e BP Passivo, sem DRE. A DFC contém a linha
     “Juros, derivativos e variação cambiais e monetárias 1.952 (anterior: 1.200)”, que é um
     ajuste de natureza financeira, mas não constitui uma linha de Resultado Financeiro nem
     linhas separadas de receitas e despesas financeiras."
2. **WEGE3_E2** (bloco 4), classe `RESPOSTA_PARCIAL_ADEQUADA`.
   - Antes: "Os três trechos são BP Ativo, DFC e DRE; não há BP Passivo nem linha de empréstimos
     e financiamentos."
   - Depois: "O contexto contém BP Ativo, DFC e DRE, sem BP Passivo. A DFC contém linhas de fluxo
     de empréstimos e financiamentos (juros provisionados, juros pagos, captação e pagamento),
     mas nenhuma linha de saldo de empréstimos e financiamentos."

## 5. Ajustes levantados e não determinados (mantidos conscientemente)

Os pontos abaixo foram apresentados ao autor durante a revisão e **não** foram determinados;
por isso **não** foram aplicados. Nenhum deles altera rótulo ou classe.

- **LAVV3_E3** (bloco 2): o campo `motivo` da afirmação de comparação diz "queda de cerca de
  84%", enquanto o valor exato é cerca de 83,5% ((3.044 − 18.469) / 18.469). O percentual não
  aparece na resposta, que foi truncada antes dele; o julgamento não muda.
- **Evidências de afirmações N** em BBAS3_E1, BBAS3_E3, ITUB4_E1, ITUB4_E2, ITUB4_N5 e BBAS3_N1:
  o campo `evidencia_contexto` menciona só a ausência de datas na representação, enquanto o
  campo `motivo` também menciona a ausência do nome da companhia.

## 6. Verificações mecânicas feitas antes deste registro

- 7 + 16 + 55 + 18 = 96.
- Nenhum id repetido entre ou dentro dos grupos.
- Os 96 ids da coleta congelada aparecem exatamente uma vez na cobertura de revisão.
- Os 5 recusados estão entre os 96 revisados (no grupo da etapa de pendências).
- As duas correções da Seção 4 estão presentes no arquivo de anotação; comparado ao estado
  anterior a elas, só esses dois campos mudaram.
- Nenhum dos ajustes da Seção 5 foi aplicado.

## 7. Arquivos de referência no momento do registro (não alterados por este documento)

| Arquivo | SHA-256 |
|---|---|
| `anotacoes_comportamento.json` | `c83cf6cef724f88ab35ac439978d13f0ad812c0ce25859ab7155eef97627b18f` |
| `pendencias_comportamento.json` | `d20f736187f69cd441a53795b4425ff212d54d7ee9274d79c894e02825976b71` |
| `CONVENCOES_ANOTACAO_COMPORTAMENTO.md` | `cfbd6276df3241b27b7f781036ca2f53037a000920f42e7a5574d79dfa96d84d` |
| `RESUMO_RATIFICACAO_COMPORTAMENTO.md` | `e41237370c02bd35fb7dd39799e04ab329824fc7afd7364bc340fae465e87cc9` |

Todos em `avaliacao/ragas/avaliacao_tcc2/comportamento/`.
