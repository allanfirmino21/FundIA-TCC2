# Resumo técnico do experimento Flash × Pro (pré-registrado)

**Natureza:** documento de consolidação, escrito depois do experimento. Não altera o
pré-registro, a coleta nem as verificações. Todos os números vêm de
`resumo_experimento_flash_pro.json`, gerado por `resumir_experimento_flash_pro.py`. O script
lê os artefatos congelados, confere seus SHA-256 e agrega deterministicamente, sem chamada a
LLM e sem reauditar narrativas.

**Fontes:**

| Artefato | Commit | SHA-256 (conteúdo com CRLF normalizado para LF) |
|---|---|---|
| `avaliacao/PRE_REGISTRO_flash_vs_pro.md` | `6a9fee9` (antes da coleta) | `eb1bab2a…` |
| `avaliacao/experimento_flash_pro.csv` (20 células) | `75dbfc4` | `a618a73b…` |
| `avaliacao/experimento_flash_pro_verificacoes.json` | `75dbfc4` | `694efac8…` |
| `avaliacao/experimento_flash_pro_manifesto.json` | `75dbfc4` | `053ae7de…` |
| `avaliacao/experimento_flash_pro_bruto_28linhas.csv` | `75dbfc4` | `436315fe…` |
| `avaliacao/experimento_flash_pro_descartadas.csv` | `75dbfc4` | `fe73b1ad…` |

Os hashes são calculados sobre o conteúdo com LF porque esses arquivos não têm `-text` no
`.gitattributes`. Assim coincidem com os blobs do git em qualquer checkout.

## 1. Desenho pré-registrado

- **Hipótese de equivalência:** depois da adoção do cálculo determinístico, o modelo de redação
  não afeta a fidelidade numérica.
- **Desenho:** 5 empresas (WEGE3, VALE3, ITSA4, BBAS3, ZAMP3) × 2 modelos (`gemini-2.5-flash`,
  `gemini-2.5-pro`) × 2 execuções = 20 análises.
- **Documento:** ITR de 31/03/2026.
- **Variável única:** o modelo de redação. Documento, métricas, contexto, prompt e temperatura
  (0,3) são idênticos entre os braços.
- **Instrumento: auditor 1.0.** É `auditar_narrativa` no estado do commit `75dbfc4`, que
  verifica a existência do valor, o sinal e a direção, mas não o conceito; a verificação de
  conceito só entrou em `27dfdd5`.
- **Dados e pipeline anteriores às correções do TCC 2:** os commits `183e69f` a `777b256` em
  `modulos/` são todos posteriores ao experimento.
- **Fidelidade de um braço:** 100 × Σ `conferem` / Σ `total_numeros` nas 10 execuções. Por
  empresa, a mesma razão nas 2 execuções.
- **Diferença de fidelidade:** |taxa Flash − taxa Pro|, em pontos percentuais.
- **Cobertura:** mediana de `total_numeros` por análise.
- **Critério de equivalência:** os dois precisam valer.
  1. Diferença agregada de fidelidade ≤ 2 p.p. **e** nenhuma empresa com diferença > 5 p.p.
  2. Diferença na mediana de `total_numeros` ≤ 10%.

## 2. Denominadores: o que cada contagem representa

O JSON de verificações tem uma entrada por número encontrado na narrativa:

| Contagem | Flash | Pro | Total | O que é |
|---|---:|---:|---:|---|
| Entradas no JSON | 335 | 229 | 564 | todas as verificações registradas |
| IGNORADO | 10 | 11 | 21 | recursos didáticos ("a cada R$ 100"), fora do denominador por definição |
| **`total_numeros` (denominador)** | **325** | **218** | **543** | entradas menos IGNORADO |
| CONFERE | 323 | 218 | 541 | numerador da fidelidade |
| DIVERGENTE | 1 | 0 | 1 | ZAMP3, exec. 1 |
| NAO_ENCONTRADO | 1 | 0 | 1 | ITSA4, exec. 2 |

**Relações:**
- 543 = 541 + 1 + 1.
- 564 = 543 + 21.
- O número 541 é a quantidade de vereditos CONFERE, não a quantidade de verificações.
- O denominador da fidelidade é 543 (325 + 218).

## 3. Integridade

Condições de aborto do pré-registro, Seção 6:

| Verificação | Resultado |
|---|---|
| 20 células únicas, iguais ao desenho | sim |
| `finish_reason` | `STOP` em todas (nenhum `MAX_TOKENS`) |
| `hash_documento` igual ao do manifesto | sim |
| `hash_contexto` único por empresa e igual ao do manifesto | sim |
| `hash_prompt` único por empresa, entre braços e execuções | sim |
| Ordem intercalada flash1 → pro1 → flash2 → pro2 em cada empresa | sim |
| Contagens do CSV = resumo do JSON = recontagem das verificações individuais | sim, nenhuma inconsistência |
| Modelos efetivamente retornados | `gemini-2.5-flash`, `gemini-2.5-pro` |

## 4. Resultados

### Fidelidade (critério 1)

| Empresa | Flash | Pro | Diferença |
|---|---|---|---|
| WEGE3 | 58/58 (100%) | 40/40 (100%) | 0 p.p. |
| VALE3 | 78/78 (100%) | 48/48 (100%) | 0 p.p. |
| ITSA4 | 71/72 (98,61%) | 37/37 (100%) | 1,39 p.p. |
| BBAS3 | 53/53 (100%) | 40/40 (100%) | 0 p.p. |
| ZAMP3 | 63/64 (98,44%) | 53/53 (100%) | 1,56 p.p. |
| **Agregado** | **323/325 (99,38%)** | **218/218 (100%)** | **0,62 p.p.** |

**Critério 1 satisfeito:** 0,62 ≤ 2 p.p.; pior empresa 1,56 ≤ 5 p.p.

As duas verificações não conformes, ambas no Flash:
- ITSA4, exec. 2, seção LUCRO: "R$ 220", NAO_ENCONTRADO;
- ZAMP3, exec. 1, seção RESUMO: "150,2%", DIVERGENTE, com o motivo "direção do verbo
  incompatível com o sinal da variação".

### Cobertura (critério 2)

| | Flash | Pro |
|---|---|---|
| `total_numeros` por análise | 31, 27, 37, 41, 35, 37, 30, 23, 34, 30 | 20, 20, 25, 23, 18, 19, 20, 20, 28, 25 |
| Mediana | **32,5** | **20,0** |

**Fórmula.** O pré-registro (Seção 5) fixa o limite de 10% para a "diferença na mediana de
`total_numeros`", mas **não especifica a base** da diferença relativa.

| Interpretação | Fórmula | Valor | Limite de 10% |
|---|---|---:|---|
| **Adotada** (base = mediana maior; leitura da mensagem do commit `75dbfc4`) | (32,5 − 20,0) / 32,5 | **38,5%** | ultrapassado |
| Alternativa (base = mediana menor) | (32,5 − 20,0) / 20,0 | 62,5% | ultrapassado |

**Critério 2 não satisfeito** nas duas interpretações.

A base da mediana maior é a mais conservadora, porque dá a menor diferença relativa. Mesmo
assim, o limite é ultrapassado.

### Veredito pré-registrado

**Não equivalentes pelo critério pré-registrado.** A fidelidade satisfaz o critério; a
cobertura não.

## 5. O que o veredito afirma e o que não afirma

**Afirma:**
- os critérios fixados antes da coleta não declaram os modelos equivalentes;
- a razão é a quantidade de valores verificáveis citados por análise;
- a diferença de fidelidade ficou dentro dos limites.

**Não afirma:**
- **superioridade de nenhum modelo**: nenhum limite define "melhor", e não há teste de
  significância (o pré-registro, Seção 8, proíbe apresentar os limites como teste);
- que citar mais valores seja melhor ou pior: a análise de cobertura (`analise_cobertura.md`,
  posterior e fora do critério) mostra repetição do mesmo fato nos dois braços;
- que o resultado vale para a configuração atual do sistema: o auditor e o pipeline mudaram
  depois do experimento;
- inferência para outras empresas, períodos ou documentos: n = 5 empresas, amostra
  intencional, um único período.

**Redação sugerida para o capítulo:**

> Pelos critérios pré-registrados, os modelos não foram declarados equivalentes: a
> fidelidade numérica foi praticamente igual (99,38% e 100%), mas o Flash citou mais valores
> verificáveis por análise (mediana de 32,5 contra 20,0), diferença acima do limite de 10%. O
> resultado não estabelece superioridade de nenhum dos modelos.

## 6. Variabilidade entre execuções (pré-registro, Seção 8; descritivo)

Comparação de `total_numeros` entre as duas execuções de cada braço e entre os braços:

| Empresa | Flash (exec. 1; 2) | Pro (exec. 1; 2) | Variação dentro do Flash | Variação dentro do Pro | Diferença entre médias |
|---|---|---|---|---|---|
| WEGE3 | 31; 27 | 20; 20 | 4 | 0 | 9 |
| VALE3 | 37; 41 | 25; 23 | 4 | 2 | 15 |
| ITSA4 | 35; 37 | 18; 19 | 2 | 1 | 17,5 |
| BBAS3 | 30; 23 | 20; 20 | **7** | 0 | **6,5** |
| ZAMP3 | 34; 30 | 28; 25 | 4 | 3 | 5,5 |

- Em 4 das 5 empresas, a diferença entre os modelos supera a variação entre execuções do mesmo
  modelo.
- Em BBAS3, a variação entre as duas execuções do Flash (7) supera a diferença entre os modelos
  (6,5).
- O pré-registro manda reportar essa aproximação como achado. Com duas execuções por célula, a
  variabilidade é estimada só de forma grosseira.

## 7. Medidas secundárias (descritivas, sem critério)

| Medida, mediana (mín.–máx.) | Flash | Pro |
|---|---|---|
| Latência da redação (s) | 25,9 (15,3–54,0) | 31,9 (30,2–34,8) |
| Tokens de saída | 1.093,5 (888–1.437) | 907,5 (834–1.027) |
| Tokens de raciocínio | 4.176,5 (2.137–6.605) | 3.521 (3.155–3.796) |
| Tokens totais | 9.527 (7.514–12.439) | 8.792,5 (8.384–8.947) |

Não houve medição de custo monetário.

## 8. Incidente de coleta e robustez do veredito

**Fatos registrados no commit `75dbfc4`:**
- Um laço de retentativa voltou a rodar em paralelo com a execução principal.
- O CSV recebeu 28 linhas para 20 células.
- As 8 células duplicadas são BBAS3 (as 4), ITSA4 exec. 2 (os dois braços) e ZAMP3 exec. 1 (os
  dois braços).
- As linhas duplicadas são gerações distintas, com contagens diferentes.
- O CSV versionado manteve as linhas que correspondem ao JSON de verificações e às narrativas
  `.md`.
- As linhas descartadas foram preservadas. Versionadas mais descartadas reproduzem exatamente
  as 28 linhas brutas.

**Robustez, recalculada sobre todas as 2⁸ = 256 seleções possíveis de uma linha por célula
duplicada:**

| | Seleções |
|---|---|
| Equivalentes | **0 de 256** |
| Critério de fidelidade satisfeito | 256 de 256 (diferença agregada de 0,13 a 0,96 p.p.; pior empresa de 1,56 a 3,51 p.p.) |
| Critério de cobertura satisfeito (base adotada) | 0 de 256 (diferença de 26,2% a 38,5% sobre a mediana maior) |
| Critério de cobertura satisfeito (base alternativa) | 0 de 256 |

**O veredito não depende da seleção das duplicatas.**

Os critérios das 256 combinações foram conferidos por um segundo cálculo independente, com
frações exatas e sem reaproveitar o código do resumo. As contagens e as faixas coincidiram, e
a seleção versionada é uma das 256.

**Desvio de procedimento:**
- o incidente produziu gerações além das 20 previstas;
- a regra de seleção foi aplicada depois da coleta;
- o pré-registro não tem emenda sobre isso (a seção "Emendas" continua vazia);
- o registro ficou só na mensagem de commit.

**Classificação:** desvio de procedimento não emendado, com veredito robusto.
- **Não é** condição de aborto do pré-registro (Seção 6): todas as gerações terminaram em
  `STOP` e os hashes de entrada são idênticos.
- **É** desvio do procedimento: houve gerações além das 20 previstas, a seleção foi feita
  depois da coleta e não há emenda datada.

O capítulo deve declarar esse desvio.

## 9. Limitações

- n = 5 empresas e 2 execuções; amostra intencional; um período (ITR de 31/03/2026).
- **Auditor 1.0:** verifica existência, sinal e direção, mas não o conceito; não avalia
  afirmações qualitativas nem causalidade. Os resultados não se transferem ao auditor 2.0.
- Fidelidade alta não significa análise correta. A validação manual do TCC 2 encontrou erros de
  causalidade com 100% de números conferidos.
- **Anterior às correções do TCC 2:** documento de 31/03/2026, métricas e Prompt 2 no estado
  de `75dbfc4`; as correções vão de `183e69f` a `777b256`. O resultado não descreve a
  configuração atual do sistema.
