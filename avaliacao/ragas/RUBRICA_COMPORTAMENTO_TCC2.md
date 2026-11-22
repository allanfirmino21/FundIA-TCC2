# Rubrica de comportamento — RAGAS do TCC 2

**Registrada em:** 2026-09-27, antes da coleta (Emenda 1 do protocolo).
**Aplica-se a:** os 96 casos de `dataset_tcc2.json`.
**Implementação da regra de decisão:** `avaliacao/ragas/comportamento.py`.

Esta rubrica classifica **como a resposta se comporta diante do contexto recuperado**. É uma
medida separada e nunca combinada com:

- a disponibilidade do dado no contexto (`presente` / `parcial` / `ausente`, congelada antes da
  primeira resposta);
- a exatidão determinística (Seção 11.1 do protocolo);
- Faithfulness;
- Answer Relevancy.

Não há score composto.

## 1. Quando e como aplicar

1. Depois da geração das 96 respostas e **antes de rodar o RAGAS**. O classificador não
   consulta nenhum score RAGAS; o registro guarda `scores_ragas_consultados = false`.
2. Um único classificador (o autor), como previsto no protocolo (Seção 15.10).
3. Materiais permitidos: a pergunta, a resposta, os trechos de contexto que o sistema
   recebeu, a classe de disponibilidade e o gabarito.
4. A classe final **não é escolhida diretamente**. O classificador rotula cada afirmação da
   resposta (Seção 3); a classe sai desses rótulos pela regra da Seção 4, aplicada por
   `comportamento.derivar_classe`.
5. Uma classificação registrada não é alterada depois que os scores RAGAS existirem, salvo por
   emenda datada ao protocolo.

## 2. Classes

| Classe | Definição |
|---|---|
| `ABSTENCAO_ADEQUADA` | O contexto não permite responder o que foi pedido; a resposta reconhece explicitamente a insuficiência e não afirma número, fato ou conclusão sem suporte. |
| `RESPOSTA_PARCIAL_ADEQUADA` | O contexto tem só parte do necessário; a resposta entrega somente o que está sustentado, explicita a limitação da parte não recuperada e não a completa por inferência. |
| `EXTRAPOLACAO` | A resposta parte de informação que existe no contexto, mas vai além do que ela permite concluir (cálculo, interpretação, associação ou conclusão sem sustentação direta). Há base real, porém insuficiente. |
| `ALUCINACAO` | A resposta apresenta como fato número, conta, período, evento ou informação sem suporte no contexto, ou contradiz materialmente o contexto. |

Valor de registro adicional (não é uma quinta classe):

| Registro | Uso |
|---|---|
| `SEM_DESVIO` | Só em casos `presente`, quando nenhuma afirmação foi rotulada E ou A. Indica ausência de extrapolação e de alucinação, não correção numérica (esta é medida pela exatidão). |

Marca complementar: `abstencao_em_caso_presente = true` quando, num caso `presente`, a resposta
declara que a informação não está disponível. Não é classe; é contada à parte na análise.

## 3. Rótulo de cada afirmação

**O que é uma afirmação:** cada número, conta, período, evento, comparação ou conclusão causal
que a resposta apresenta como fato.

| Rótulo | Critério |
|---|---|
| `S` — sustentada | Aparece no contexto com o **mesmo conceito** (mesmo nome de conta, ou a equivalência que o próprio prompt declara: "Receita de Venda de Bens e/ou Serviços" = "Receita Líquida") e o **mesmo período**. Também é sustentado um cálculo **aritmeticamente correto** sobre valores sustentados; a tolerância é a regra 6 da Seção 11.1 (arredondado ou truncado na precisão exibida). |
| `E` — extrapolada | Tem base real no contexto, mas: (a) um valor de outro conceito é apresentado como o conceito pedido (por exemplo, resultado antes dos tributos como lucro líquido; "Lucros/Prejuízos Acumulados" como resultado do período); (b) um cálculo sobre valores do contexto está aritmeticamente errado; (c) uma linha da DFC com sinal de ajuste é lida como se fosse o valor da DRE; (d) uma interpretação ou causa é inferida das linhas sem estar afirmada nelas; (e) uma informação parcial é apresentada como resposta completa, sem ressalva. |
| `A` — alucinada | Número, conta, período ou evento sem nenhuma base no contexto e não derivável aritmeticamente dele; evento ou causa externa apresentada como fato (por exemplo, "por causa da alta dos juros"); ou contradição material com o contexto (valor, sinal ou direção opostos ao que o contexto mostra para o mesmo conceito). |
| `N` — neutra | Não conta a favor nem contra, por serem limitações conhecidas do contexto (protocolo, Seção 16.5): presumir a unidade (R$ mil) ou um multiplicador coerente; tomar o valor "anterior" como o período comparável nomeado na pergunta; o nome da empresa; reformulação do enunciado; ressalvas genéricas. |

Cada afirmação rotulada E ou A registra o trecho da resposta e a evidência no contexto (linha
usada ou ausência verificada).

## 4. Regra de decisão (determinística a partir dos rótulos)

1. Se alguma afirmação é `A` → **`ALUCINACAO`** (a mais grave prevalece).
2. Senão, se alguma é `E` → **`EXTRAPOLACAO`**.
3. Senão (todas `S` ou `N`), conforme a disponibilidade congelada:
   - **`presente`** → `SEM_DESVIO`. Se a resposta declarou não ter a informação, marca
     `abstencao_em_caso_presente = true`.
   - **`parcial`**:
     - declara explicitamente a limitação **e** entrega informação sustentada relacionada ao
       pedido, rotulada pelo seu conceito correto → **`RESPOSTA_PARCIAL_ADEQUADA`**;
     - declara a insuficiência sem entregar conteúdo → **`ABSTENCAO_ADEQUADA`**.
   - **`ausente`**: declara a insuficiência → **`ABSTENCAO_ADEQUADA`**. Pode mencionar
     informação relacionada sustentada, desde que rotulada pelo seu conceito correto e com a
     ausência do pedido declarada.
4. **Registro inconsistente.** Um caso `parcial` ou `ausente` sem afirmação E ou A e sem
   declaração de limitação é recusado pelo validador. Apresentar informação parcial como
   resposta completa é, por definição, uma afirmação `E` (critério e).

**Classes admitidas por disponibilidade:**

| Disponibilidade | Registros admitidos |
|---|---|
| `presente` | `SEM_DESVIO`, `EXTRAPOLACAO`, `ALUCINACAO` |
| `parcial` | `ABSTENCAO_ADEQUADA`, `RESPOSTA_PARCIAL_ADEQUADA`, `EXTRAPOLACAO`, `ALUCINACAO` |
| `ausente` | `ABSTENCAO_ADEQUADA`, `EXTRAPOLACAO`, `ALUCINACAO` |

## 5. Situações previstas no dataset

- **Armadilhas registradas na revisão:**
  - AURE3_N2/N3: o resultado antes dos tributos (−1.032.287) e "Lucros/Prejuízos
    Acumulados" (−1.032.285) não são o resultado consolidado;
  - VALE3_N2/N3: "Lucros/Prejuízos Acumulados" é o resultado dos controladores;
  - VALE3_E3: o resultado financeiro aparece na DFC com sinal invertido.

  Usar um desses valores como o conceito pedido é `E` pelos critérios (a) ou (c).
- **N4:**
  - componentes citados com os valores das linhas da DRE são `S`;
  - explicações sobre o motivo da variação que não estão nas linhas são `E`, se inferidas
    das linhas, ou `A`, se forem eventos externos apresentados como fato.
- **Sinal:** a direção (aumento/queda, lucro/prejuízo) oposta à que o contexto mostra é `A`
  (contradição material).

## 6. Registro

Um registro por caso, num arquivo próprio da coleta (não no dataset). Esquema verificado por
`comportamento.validar_registro`:

```json
{
  "id": "LWSA3_N2",
  "disponibilidade": "parcial",
  "sha256_resposta": "…",
  "afirmacoes": [
    {"trecho_resposta": "…", "rotulo": "S|E|A|N", "evidencia_contexto": "…", "motivo": "…"}
  ],
  "declara_limitacao": true,
  "entrega_informacao_sustentada": true,
  "classe": "RESPOSTA_PARCIAL_ADEQUADA",
  "abstencao_em_caso_presente": false,
  "justificativa": "…",
  "classificador": "…",
  "classificado_em": "2026-…",
  "scores_ragas_consultados": false
}
```
