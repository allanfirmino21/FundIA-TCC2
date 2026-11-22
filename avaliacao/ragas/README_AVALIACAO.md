# Avaliação das respostas do RAGAS do TCC 2

Executor: `avaliacao/ragas/avaliar_respostas_tcc2.py`.
Regras: `PROTOCOLO_RAGAS_TCC2.md` (Seções 11, 11.1, 12 e 15; Emendas 1 e 3) e
`RUBRICA_COMPORTAMENTO_TCC2.md`.

As cinco medidas (disponibilidade, comportamento, exatidão, Faithfulness e Answer Relevancy)
são registradas separadamente e **nunca combinadas** em índice.

## Entradas

Todas são congeladas e conferidas a cada execução; qualquer divergência aborta.

- **Dataset:** `dataset_tcc2.json` (SHA-256 `313bdf35…`).
- **Coleta:** `coleta_tcc2/` (commit `10eee31`). A conferência é feita:
  - pelo `SHA256_COLETA.txt`, cujo próprio hash está fixado no executor;
  - pela **configuração histórica** do manifesto (`b9565446…`);
  - pelo selo de cada registro;
  - pelo contexto, comparado ao congelado.

  O hash do protocolo atual, já emendado, **não** é usado para validar a coleta.
- **Texto avaliado:** o campo `resposta` de cada registro, sem correção. As 36 respostas
  truncadas por `MAX_TOKENS` entram como estão, com a marca `truncada_na_geracao`.
- **Instrumentos:** `exatidao.py` e `comportamento.py`, sem alteração.

A coleta nunca é escrita. As saídas vão para `avaliacao/ragas/avaliacao_tcc2/`, fora do git até
o congelamento de cada etapa. Todo arquivo é criado de forma exclusiva, e nada é sobrescrito.

## Ambiente (Emenda 3)

A exatidão e a rubrica rodam no ambiente principal. O RAGAS roda só num venv isolado:

```
python -m venv --system-site-packages C:\Users\allan\.venvs\tcc2-avaliacao-ragas
C:\Users\allan\.venvs\tcc2-avaliacao-ragas\Scripts\python -m pip install -r avaliacao/ragas/requirements_avaliacao.txt
```

- **Versões fixadas:** `ragas==0.4.3`, `langchain-community==0.4.2`, `langchain-google-genai==4.4.0`.
- **Resolução completa:** `requirements_avaliacao.lock`.
- **Por que isolado:** o ambiente da coleta (`google-genai==2.2.0`) não pode ser alterado.
- **Conferência:** o executor confere as versões e a revisão local dos embeddings (`4328cf26…`)
  antes de qualquer chamada.

## Ordem das etapas

1. **Dry-run**, sem LLM e sem score: confere entradas, hashes, amostras, estado e proteção contra
   sobrescrita.

   ```
   python avaliacao/ragas/avaliar_respostas_tcc2.py dry-run [--verificar-ambiente]
   ```

2. **Exatidão determinística** (Seção 11.1):

   ```
   python avaliacao/ragas/avaliar_respostas_tcc2.py exatidao --executar
   ```

   - Se algum número de sinal inconclusivo for necessário (regra 5 e regra C), o executor grava
     `exatidao/pendencias_sinal_NN.json` e **não grava resultado**.
   - O autor decide cada sinal em `exatidao/decisoes_sinal.json`. Cada decisão registra `inicio`,
     `texto`, `sinal` (`+` ou `-`), `justificativa`, e o arquivo inteiro registra
     `decidido_por` e `decidido_em`.
   - O executor nunca decide um sinal sozinho.
   - Sem pendências, grava `exatidao/resultado_exatidao.json` uma única vez.

3. **Rubrica de comportamento** (classificação humana, sem LLM e sem consultar scores RAGAS):

   ```
   python avaliacao/ragas/avaliar_respostas_tcc2.py comportamento --gerar-modelo
   python avaliacao/ragas/avaliar_respostas_tcc2.py comportamento --validar
   ```

   - O autor rotula as afirmações de cada caso (S, E, A ou N) em
     `comportamento/anotacoes_comportamento.json`.
   - O validador:
     - informa a classe derivada (`comportamento.derivar_classe`);
     - recusa registros inconsistentes;
     - confere o `sha256_resposta` contra a resposta congelada.
   - A classe nunca é escolhida à mão.

   > **Nota operacional (Emenda 4).** Os desvios entre o procedimento descrito acima e o
   > executado estão registrados na Emenda 4 do protocolo. Casos truncados listados em
   > `comportamento/pendencias_comportamento.json` que cumprem as condições da emenda recebem o
   > estado técnico `PENDENTE_OPERACIONAL`, que não é classe de comportamento. A etapa só é
   > considerada completa com 0 inválidos, 0 incompletos e válidos + `PENDENTE_OPERACIONAL` = 96.
   > Antes do RAGAS, anotações, pendências, convenções e ratificação precisam estar em commit.

4. **Congelamento em commit** de `resultado_exatidao.json`, `decisoes_sinal.json` (se houver) e
   `anotacoes_comportamento.json`. O executor recusa o RAGAS antes disso.

5. **RAGAS**, uma métrica por chamada de `ragas.evaluate`, rodado no venv:

   ```
   python avaliacao/ragas/avaliar_respostas_tcc2.py ragas --metrica faithfulness --executar
   python avaliacao/ragas/avaliar_respostas_tcc2.py ragas --metrica answer_relevancy --executar
   python avaliacao/ragas/avaliar_respostas_tcc2.py ragas --metrica <m> --executar --reavaliar-nan
   ```

   - Por caso, o executor grava `ragas/<métrica>/<case_id>.tentativa_01.inicio.json` antes da
     chamada e `…tentativa_01.json` depois dela.
   - Uma tentativa interrompida conta como inválida.
   - Casos NaN admitem **uma** reavaliação (`tentativa_02`), em passada separada, com a primeira
     preservada. Se o NaN persistir, o caso é inválido.
   - Sem `--reavaliar-nan`, só são avaliados casos nunca avaliados.

## O que cada resultado registra

- `case_id` e hashes da pergunta, da resposta, do contexto e dos trechos;
- a marca de truncamento;
- o modelo avaliador e os identificadores devolvidos pela API;
- a temperatura configurada (0) e a temperatura efetiva: 0,01 em Faithfulness e 0,3 no Answer
  Relevancy (Emenda 3);
- `RunConfig`, `strictness` e embeddings, com a revisão;
- as versões das dependências;
- as exceções capturadas (sanitizadas);
- a tentativa, o commit, os hashes do executor, do protocolo e do dataset, a configuração
  histórica da coleta e os hashes das etapas anteriores congeladas;
- o selo (`sha256_registro`).

## Testes

- `tests/test_ragas_avaliacao.py`: executor completo sobre uma coleta **sintética**, sem rede.
- `tests/test_ragas_avaliacao_ambiente.py`: adaptador RAGAS real com um modelo de chat falso.
  - No venv, roda de verdade.
  - No ambiente principal, é pulado.
