# Pré-registro — Gemini 2.5 Flash vs. Gemini 2.5 Pro na etapa de redação

**Projeto:** FundIA — TCC de Ciência de Dados, UFPB
**Data de registro:** 2026-08-30
**Status:** registrado ANTES de qualquer chamada à API para este experimento.

Este documento fixa a hipótese, o critério de decisão e o plano de análise antes da
coleta dos dados. Seu propósito é impedir racionalização posterior do resultado: o
critério abaixo foi escolhido sem conhecimento dos números que ele vai julgar. Qualquer
alteração feita depois do início da coleta deve ser registrada como emenda datada ao
final deste arquivo, com justificativa, e nunca por edição silenciosa do texto original.

---

## 1. Hipótese

> Após a adoção do cálculo determinístico, a escolha do modelo de redação não afeta a
> fidelidade numérica da análise.

A hipótese é de **equivalência**, não de diferença. O desenho pretende dar ao resultado
"os modelos diferem" uma chance real de aparecer; se ele não aparecer, a conclusão é que
a fidelidade numérica passou a ser propriedade do pipeline determinístico e não do
modelo de linguagem empregado na redação.

Motivação: se a fidelidade for de fato indiferente ao modelo, a escolha entre Flash e
Pro passa a ser decidida por custo e latência, e não por qualidade — o que sustenta a
escolha atual do Flash em produção. O experimento existe para testar essa premissa, não
para confirmá-la.

## 2. Desenho

5 empresas × 2 modelos × 2 execuções = **20 análises**.

**Variável independente (única):** o modelo de redação (`prompt2.MODELO_LLM`), com dois
níveis — `gemini-2.5-flash` e `gemini-2.5-pro`.

**Mantidos idênticos entre os braços, e verificados por hash:**

| Item | Como é mantido fixo | Verificação |
|---|---|---|
| Documento da CVM | `.txt` congelado em `dados/cache/`, lido por caminho explícito | `hash_documento` (sha256) contra manifesto |
| Cálculo das métricas | `calcular_metricas` determinístico em Python | determinístico por construção |
| Contexto recuperado | ChromaDB já indexado, sem reindexação | `hash_contexto` (sha256) |
| Prompt enviado | mesma string em `contents` | `hash_prompt` (sha256) |
| Temperatura | 0,3 nos dois braços | literal em `prompt2.py` |
| `max_output_tokens` | `MAX_TOKENS_NARRATIVA` = 8192 nos dois braços | constante em `config.py` |

O `hash_prompt` é o controle central: é ele que prova que os dois modelos receberam
entrada idêntica. Sem essa igualdade, qualquer diferença observada é inconclusiva.

**Não há chamada ao Prompt 1 (extração via LLM).** As métricas vêm exclusivamente do
caminho determinístico. Isso distingue este experimento da rodada arquivada em
`comparacao_modelos.json` (julho/2026), que era pré-determinística e trocava o modelo
nas duas etapas — motivo pelo qual aqueles dados não são comparáveis a estes.

**Sem rede durante a coleta.** Nenhum download da CVM, nenhuma reindexação. A única
saída de rede é a chamada de redação ao Gemini.

## 3. Amostra

Cinco empresas, todas em **ITR** com **DT_REFER = 2026-03-31**. Escolhidas para cobrir
os caminhos distintos do pipeline, não por amostragem aleatória — a amostra é uma
ilustração do instrumento sobre casos contrastantes, e o relatório final deve dizer isso
explicitamente. Não se pretende inferência para o universo das companhias abertas.

| Ticker | Empresa | Por que está na amostra |
|---|---|---|
| WEGE3 | WEG S.A. | Contas homônimas entre circulante e não circulante; escala R$ mil. Lucro R$ 1,58 bi (−3,5%), caixa líquido negativo (−R$ 6,47 bi). |
| VALE3 | Vale S.A. | Demonstração completa, sem lacunas: exercita o pipeline inteiro. Lucro R$ 10,20 bi (+24,8%). |
| ITSA4 | Itaúsa S.A. | Holding: lucro (R$ 4,46 bi) maior que a receita (R$ 2,02 bi), `margem_liquida_pct` nula e `ebitda.margem_pct` = `nao_disponivel`. Testa a regra 5 do prompt sem inventar margem. |
| BBAS3 | Banco do Brasil S.A. | Instituição financeira: dívida e EBITDA `nao_aplicavel`, `captacao_mercado_aberto` = `nao_disponivel` no mesmo bloco. Lucro caiu 25,6%, acionando a regra 4 ("nunca suavize"). |
| ZAMP3 | Zamp S.A. | Prejuízo de R$ 108,86 mi, "prejuízo 2,5 vezes maior" (inversão de polaridade e token de razão), margem negativa, queda de caixa de 47,0%, arrendamentos que quase dobram a dívida. |

## 4. Métricas

Todas derivadas de `auditar_narrativa` (`modulos/auditoria.py`), aplicada a cada uma das
20 análises.

**Denominador:** usar sempre `resumo["total_numeros"]`, **nunca** `len(verificacoes)`.
O total já exclui os vereditos `IGNORADO` (recursos didáticos do tipo "a cada R$ 100"),
que não devem contar na taxa. Confundir os dois infla o denominador e deprime
artificialmente a taxa de conformidade.

- **Fidelidade:** `taxa_conformidade` = `conferem` / `total_numeros`.
- **Cobertura:** `total_numeros` por análise — quantos valores verificáveis o texto
  arrisca citar. Um modelo pode alcançar fidelidade alta simplesmente citando menos
  números; a cobertura existe para flagrar essa troca.
- **Secundárias, descritivas, sem critério de corte:** latência da chamada de redação,
  tokens de entrada, saída, raciocínio e total; e a distribuição dos vereditos
  `DIVERGENTE` e `NAO_ENCONTRADO`.

## 5. Critério de equivalência

Os **dois** critérios precisam ser satisfeitos para que os modelos sejam declarados
equivalentes:

1. **Fidelidade** — a diferença na taxa de conformidade agregada é **≤ 2 p.p.**
   **E** nenhuma empresa individual apresenta diferença **> 5 p.p.**
2. **Cobertura** — a diferença na mediana de `total_numeros` por análise é **≤ 10%**.

**Falhando qualquer um dos dois, os modelos NÃO são equivalentes e o resultado será
reportado como tal, ainda que contrarie a escolha atual do Flash.**

A taxa agregada é calculada somando `conferem` e `total_numeros` sobre as 10 execuções
de cada braço (não é média de taxas por empresa — essa ponderaria igualmente análises
com número muito distinto de valores citados). A taxa por empresa agrega as 2 execuções
daquela empresa naquele braço.

## 6. Condições de aborto

A coleta é interrompida e o resultado reportado sem prosseguir se:

- **`finish_reason` = `MAX_TOKENS`** em qualquer chamada. Narrativa truncada corrompe a
  métrica de cobertura, e o desenho precisa mudar antes de continuar.
- **`hash_documento`** divergir do manifesto — o documento congelado mudou.
- **`hash_contexto`** ou **`hash_prompt`** divergirem entre execuções da mesma empresa —
  a premissa de entrada idêntica caiu, e nenhuma comparação é válida.

Aborto não é resultado negativo: é sinal de que o experimento não mediu o que pretendia.

## 7. Ordem de execução

Intercalada por empresa, nunca em blocos por modelo:

```
Flash-exec1, Pro-exec1, Flash-exec2, Pro-exec2
```

Blocos por modelo confundiriam variação temporal do lado da API (carga, roteamento,
degradação) com diferença entre modelos. A intercalação não elimina esse ruído, mas
impede que ele se alinhe sistematicamente com a variável de interesse.

A ordem global de cada chamada é registrada em `ordem_global`, permitindo verificar
depois se houve deriva ao longo da coleta.

## 8. Análise e limitações declaradas

O relatório final deve trazer, por braço: taxa agregada, taxa por empresa, mediana e
dispersão de `total_numeros`, e as estatísticas descritivas de latência e tokens. A
lista completa de verificações — **incluindo os `CONFERE` individuais** — é arquivada em
`experimento_flash_pro_verificacoes.json`, para que qualquer pessoa possa refazer a
contagem sem confiar nos agregados. (A rodada de julho/2026 guardou apenas os
não-`CONFERE` e por isso não é reauditável; este experimento não repete esse erro.)

Limitações que serão declaradas independentemente do resultado:

- **n = 5 empresas, 2 execuções.** Não há poder estatístico para teste de hipótese
  formal. Os critérios da seção 5 são limiares de decisão pré-fixados, não testes de
  significância, e não serão apresentados como tal.
- A amostra é intencional (casos contrastantes), não aleatória.
- Duas execuções por célula estimam a variabilidade dentro do modelo de forma grosseira;
  se a variação entre as duas execuções do mesmo modelo se aproximar da diferença entre
  modelos, isso será reportado como achado, e o critério da seção 5 perde interpretação
  — a conclusão passa a ser "não distinguível com este n".
- O auditor verifica valores monetários, percentuais e razões, com sinal e direção. Não
  verifica afirmações qualitativas nem números por extenso. Fidelidade numérica alta não
  significa análise correta.
- Um único período (2026-03-31) e um único tipo de documento (ITR).

---

## Emendas

_(Nenhuma até o momento. Qualquer alteração posterior ao início da coleta deve ser
registrada aqui, com data e justificativa.)_
