# Observações da etapa de exatidão — RAGAS do TCC 2

Registradas em 2026-09-30, no congelamento da etapa. Nenhuma classificação foi alterada.

## Resultado congelado

- Arquivo: `resultado_exatidao.json`.
- SHA-256: `3c3e28c080a9884f53f1197bd0c4106fd414105b2aa4de3ff2928f401a05a6db`. O selo
  (`sha256_registro`) está íntegro.
- Gerado em 2026-09-30T00:28:38Z por `avaliar_respostas_tcc2.py exatidao --executar`:
  - commit `259952381d8076bd106c1dea8476fb54e0d49e63`;
  - `exatidao.py` com SHA-256 `2b4b1170…`, congelado antes da coleta.
- Classes nos 96 casos: CORRETO 31, PARCIALMENTE_CORRETO 5, INCORRETO 7, NAO_APLICAVEL 53.
  - Os 53 NAO_APLICAVEL são 12 por categoria N4 e 41 por resposta sem número monetário ou
    percentual.
  - Aplicáveis: 43.
- Não houve pendência de sinal nem decisão manual de sinal (`decisoes_sinal.json` não existe).

## Observação metodológica: números incompletos por `MAX_TOKENS`

Duas respostas truncadas na geração (`finish_reason = MAX_TOKENS`) terminam exatamente no meio
de um número:

| Caso | Disponibilidade | Último token da resposta |
|---|---|---|
| BBAS3_N3 | presente | `6.362.96` |
| AURE3_N2 | parcial | `**-1.0` |

- O leitor congelado (Seção 11.1, regra 1; Emenda 1, regra A) não lê esses tokens como número
  monetário: um número colado a ponto seguido de dígito é tratado como código.
- Por isso os dois casos permanecem `NAO_APLICAVEL` ("resposta sem número monetário ou
  percentual"), pela regra congelada.
- A classificação não foi alterada nem reinterpretada.
- Na análise, os dois casos devem ser lidos à luz da marca `truncada_na_geracao`.

## Marca `sinal_revisao_manual` sem pendência

- WEGE3_E3, ITSA4_E3 e CEAB3_N4 têm números de sinal ambíguo e por isso receberam a marca.
- Esses números não entraram na conciliação com os valores exigidos.
- Por isso a classe não depende deles e o instrumento não exigiu decisão manual.

## Complemento (2026-10-09): números interrompidos por `MAX_TOKENS`, incluindo ZAMP3_E2

Este complemento foi acrescentado depois do congelamento. O texto acima não foi alterado, e a
classificação dos cinco casos abaixo continua a mesma, tanto no resultado original quanto no da
Emenda 5.

A seção "Números incompletos por `MAX_TOKENS`" lista dois casos, mas a lista está incompleta. Entre
as 36 respostas truncadas, **cinco** terminam no meio de um valor. Outras terminam em fragmento de
ano ("de 202"), que não é valor monetário.

**Fragmento não aproveitado numericamente: o caso fica NAO_APLICAVEL.** São os casos em que o único
valor da resposta é o fragmento final.

| Caso | Disponibilidade | Fim da resposta | Leitura pelo instrumento | Classe |
|---|---|---|---|---|
| BBAS3_N3 | presente | `6.362.96` | não lido (número colado a ponto seguido de dígito) | NAO_APLICAVEL |
| AURE3_N2 | parcial | `**-1.0` | não lido (idem) | NAO_APLICAVEL |
| ZAMP3_E2 | parcial | `Caixa e Equivalentes de Caixa:** 13` | "13" descartado pela Emenda 1, regra A (inteiro < 1000 sem R$, multiplicador, % ou casas decimais) | NAO_APLICAVEL |

**Classe mantida pelos outros números da resposta.** O fragmento final não altera a classe.

| Caso | Disponibilidade | Fim da resposta | Leitura pelo instrumento | Classe |
|---|---|---|---|---|
| ITUB4_N3 | presente | `Variação Absoluta:** 24.199.` | lido como 24.199 (R$ mil, escala implícita), sem conciliação com nenhum valor exigido | PARCIALMENTE_CORRETO, pelos dois resultados conferidos antes |
| LAVV3_N3 | presente | `…do período atual foi de 184` | "184" descartado pela regra A | CORRETO, pelos valores conferidos antes |

**ZAMP3_E2, fatos comprovados:**
- A resposta (SHA-256 `ba937b5a…`) termina em "13", e a geração terminou com
  `finish_reason = MAX_TOKENS`.
- O uso registrado foi de 41 tokens de saída e 979 de raciocínio, com limite de 1024.
- O caixa do gabarito, 135.651 (conta 1.01.01), aparece no contexto em duas linhas:
  "Caixa e Equivalentes de Caixa" (BPA) e "Saldo Final de Caixa e Equivalentes" (DFC).
- O instrumento descarta "13" pela regra A, e a classe é NAO_APLICAVEL ("resposta sem número
  monetário ou percentual") também no resultado da Emenda 5.
- A anotação de comportamento trata "13" como fragmento (Convenção 1), e o caso ficou em
  `PENDENTE_OPERACIONAL` (Emenda 4).

**ZAMP3_E2, hipóteses não verificadas:**
1. **Que "13" seria o início de 135.651.** É plausível, porque o rótulo é o da linha do BPA, mas o
   contexto tem outros números que começam por 13 (−130.470 e −13.541, na DFC). O texto da resposta
   não permite confirmar.
2. **Que o consumo de tokens de raciocínio teria causado o corte.** É compatível com os números
   registrados (979 + 41 = 1.020 de 1.024), mas o mecanismo de contagem da API não foi verificado.
3. **Qual seria a continuação da resposta.** Não pode ser inferida: nem o valor do caixa, nem a
   dívida, nem a comparação pedida.

**Consequências para a interpretação:**
- ZAMP3_E2 permanece NAO_APLICAVEL **por truncamento**, não por abstenção nem por erro numérico.
- Não há evidência suficiente para avaliar a exatidão numérica dessa resposta.
- O caso não entra nos 43 aplicáveis e não conta como acerto nem como erro.
- Na anotação de comportamento, o caso também ficou sem classe.
- O mesmo vale para BBAS3_N3 e AURE3_N2.
- Em ITUB4_N3 e LAVV3_N3, a classe vem dos números completos que a resposta apresentou antes do
  corte.
