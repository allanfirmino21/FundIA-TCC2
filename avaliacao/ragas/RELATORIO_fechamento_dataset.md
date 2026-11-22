# Relatório de fechamento do dataset — RAGAS do TCC 2

**Data:** 2026-09-27 (antes da coleta)
**Base:** commit `b17ea73` (protocolo pré-registrado) + alterações não commitadas listadas na Seção L.
**Revisão executada por:** Claude Code. **Não substitui a revisão humana do autor**, que é a
última etapa antes do congelamento.

> O dataset ainda não contém respostas experimentais e nenhuma métrica RAGAS foi executada.

Nesta etapa não houve chamada ao Gemini nem a qualquer outro LLM, o RAGAS não foi instalado
nem executado, e `modulos/` e `dados/ticker_map.csv` não foram alterados.

---

## A. Estado inicial

- O protocolo estava pré-registrado no commit `b17ea73`, com a seção "Emendas" vazia.
- O dataset tinha 96 casos construídos e revisados tecnicamente, com três pendências de
  método:
  1. IRBR3_E3 somava as aplicações do circulante e do longo prazo (R$ 8.353.283 mil).
  2. O leitor de números não tinha regras para datas, códigos, marcadores de lista,
     parênteses e pontuação final.
  3. Faltava a rubrica de comportamento prevista na Seção 12 do protocolo.
- `avaliacao/ragas/**` não tinha regra de fim de linha no `.gitattributes`.
- Uma cópia do dataset anterior ao fechamento foi guardada fora do repositório, para
  comparação.

## B. IRBR3_E3

A regra conservadora foi adotada pela **Emenda 1, item 1**. O gabarito reflete apenas a
conta explicitamente pedida.

| Campo | Valor |
|---|---|
| Conta | Aplicações Financeiras (ativo circulante) |
| CD_CONTA | `1.01.02` |
| DS_CONTA | `Aplicações Financeiras` |
| Valor | R$ 4.414.934 mil (R$ 4,41 bilhões) |
| Período | 30/06/2026 (BPA consolidado, ITR v2) |
| Motivo | É a única conta do ITR com esse DS_CONTA. `1.02.01.01/.02/.03` são subcontas do longo prazo por categoria de mensuração, sem conta agregada de mesmo nome, e não são somadas por semelhança econômica. |

**Contas não somadas**, registradas no caso em `decisao_metodologica.contas_nao_somadas`:

- `1.02.01.01` = 0
- `1.02.01.02` = 3.881.323
- `1.02.01.03` = 57.026

**Mudanças no caso:**

- A pergunta passou a pedir "o saldo de aplicações financeiras registrado no ativo circulante
  consolidado".
- O tipo mudou de `derivada` para `factual`.
- As fórmulas e as formas alternativas de soma foram removidas.
- A disponibilidade continua `presente`: a linha `[BPA] Aplicações Financeiras 4.414.934`
  está no contexto recuperado.

**Outras agregações nos gabaritos:** foram verificadas, apenas para relatório, e nenhuma
correção foi feita. Só existem estas duas:

1. **E2, nos 9 casos que têm a pergunta**, dívida = `2.01.04 + 2.02.01`. A soma é suportada
   porque a pergunta pede explicitamente "circulante e não circulante somados", e as duas
   contas têm o mesmo DS_CONTA ("Empréstimos e Financiamentos").
2. **IRBR3_N4**, componente "despesas administrativas e outras" = `3.04 + 3.05 + 3.06`. É a
   cadeia do plano de seguros definida no protocolo. N4 não passa pela exatidão
   determinística.

Nenhuma agregação sem suporte foi encontrada.

## C. Leitor de números (regras complementares A–D)

As regras estão formalizadas na **Emenda 1, item 2**, e implementadas em `exatidao.py`. As
demais regras da Seção 11.1 não mudaram: escala, multiplicadores, arredondamento ou
truncamento, percentuais, conciliação e classes.

| Regra | Comportamento | Testes |
|---|---|---|
| A | Datas, anos isolados, códigos contábeis, 1S25/1S26, "Trecho N" e inteiros < 1000 sem marca monetária não são lidos como valores. Nenhum valor exigido do dataset é < 1000 em R$ mil. | `RegrasComplementares` e `test_nenhum_valor_monetario_exigido_abaixo_de_mil` |
| B | O "-" de marcador de lista não é sinal. | `RegrasComplementares` |
| C | Parênteses não significam negativo por si. Um número isolado entre parênteses gera `PENDENTE_REVISAO_SINAL`; a decisão manual resolve. Com "prejuízo/negativo/déficit" na oração, é negativo. "(R$ 19,6 bilhões)" é reapresentação positiva e não impede CORRETO. | `RegrasComplementares` (5 testes) |
| D | Número brasileiro seguido de pontuação é lido inteiro. | `RegrasComplementares` |

A regra C substitui a leitura "entre parênteses = negativo" da regra 5. Por isso o caso
`(154.679)` saiu do teste de sinal explícito e foi substituído por `(-154.679)`, que é
explícito. O comportamento antigo passou a ser coberto pelo teste de ambiguidade da regra C.
Nenhum teste foi removido sem substituto nem enfraquecido.

## D. Rubrica de comportamento

Ficou registrada na **Emenda 1, item 3**. Os arquivos são:

- `RUBRICA_COMPORTAMENTO_TCC2.md`
- `comportamento.py`
- `tests/test_ragas_comportamento.py` (12 testes)

**Classes:** `ABSTENCAO_ADEQUADA`, `RESPOSTA_PARCIAL_ADEQUADA`, `EXTRAPOLACAO`,
`ALUCINACAO`.

**Como a classe é atribuída:**

- O classificador rotula cada afirmação como S, E, A ou N.
- A classe sai dos rótulos de forma determinística: A prevalece sobre E, e E prevalece sobre
  a análise por disponibilidade.
- Um registro `parcial` ou `ausente` sem desvio e sem declaração de limitação é recusado.

**Cobertura:** casos `presente`, `parcial` e `ausente`. Nos casos `presente` sem desvio, o
registro é `SEM_DESVIO`, que **não** é uma quinta classe. A marca
`abstencao_em_caso_presente` é contada à parte.

**Independência:** a rubrica é separada da disponibilidade, da exatidão, de Faithfulness e de
Answer Relevancy. Não há score composto. É aplicada depois da geração e antes do RAGAS, e o
registro exige `scores_ragas_consultados = false`.

**Apenas estrutura e código.** Nenhuma resposta foi classificada, e o dataset não contém
campos de comportamento; o teste de chaves proibidas verifica isso.

## E. Revisão final dos 96 casos

Um script próprio fez a conferência independente. Ele relê os CSVs da CVM
(`itr_cia_aberta_{DRE,BPA,BPP}_con_2026.csv`) sem usar `construir_dataset` nem
`calcular_metricas`. Para cada caso, conferiu:

- as fontes: CD_CONTA, DS_CONTA, VL_CONTA, escala `MIL`, moeda `REAL` e período (acumulado
  do ano na DRE; 30/06/2026 e 31/12/2025 no balanço);
- o conceito esperado por categoria e estrutura;
- o `sinal_exigido` contra a tabela da Seção 11.1;
- as somas e os percentuais recalculados (N3 sobre a magnitude quando há dois prejuízos;
  margem em E1);
- o fechamento da cadeia N4;
- a redação da pergunta (empresa, período, "consolidado", ausência de "trimestre");
- a disponibilidade contra a estimativa do protocolo.

**Resultado:** 96 casos verificados, **0 com observação**.

Cada caso recebeu o registro `revisao_tecnica.revisao_final`, com revisor, data, resultado
(`confirmado`/`corrigido`) e detalhe. O registro deixa explícito que não substitui a revisão
humana.

**Contexto:** os hashes do contexto reconstruído do zero (`reconstruido_de_cache = false`)
são idênticos aos do cache anterior nas 12 empresas.

## F. Os 18 casos com atenção humana

Os números de cada nota foram conferidos no CSV e as armadilhas, no texto do contexto
recuperado.

| Caso | Disp. | Conferência |
|---|---|---|
| BBAS3_N2 | presente | 3.11 = 6.362.961 (gabarito) e 3.11.01 = 4.794.808; as duas linhas estão no contexto. |
| BBAS3_N4 | presente | O IR/CS 3.06 é positivo nos dois períodos e cai de 6.116.746 para 3.637.834 (−2.478.912), o maior componente. |
| BBAS3_E3 | presente | 3.02 = −111.283.805; sinal não exigido. |
| ZAMP3_N3 | presente | −154.679 / −116.011; 33,33% sobre a magnitude. |
| LWSA3_E2 | presente | 19.361 + 52.554, ambos "Financiamento por Arrendamento". |
| VALE3_N2 | parcial | 3.11 = 17.240.000. O contexto traz "Lucros/Prejuízos Acumulados 16.800.000" (= 3.11.01) e o resultado da DFC antes dos tributos. |
| VALE3_E2 | presente | 6.534.000 + 91.500.000; debêntures participativas (11.973.000) fora da soma. |
| VALE3_E3 | parcial | DRE −2.237.000; DFC do contexto +2.237.000 (sinal invertido). |
| ITUB4_E3 | presente | 3.02 = −127.362.000, com perda esperada de crédito (3.02.02 e 3.02.03). |
| POMO4_N2 | presente | "Resultado do período" 535.824 na DFC = DRE 3.11. |
| POMO4_N4 | parcial | DRE fora do contexto; a DFC traz o IR/CS com sinal invertido (120.446). |
| ITSA4_N1 | presente | 3.01 = 4.250.000; equivalência 9.354.000. |
| IRBR3_N4 | presente | 3.04 + 3.05 + 3.06; a cadeia fecha. |
| IRBR3_E1 | presente | 3.03 = −41.006 (1S26) e 431.005 (1S25). |
| IRBR3_E2 | presente | 3.08.02 = +106.826 (como entregue à CVM); 3.08 = 117.761. |
| IRBR3_E3 | presente | **Corrigido** (Seção B). |
| AURE3_N2 | parcial | 3.11 = −980.667. O contexto só traz −1.032.287 (DFC, antes dos tributos) e −1.032.285 (Lucros/Prejuízos Acumulados). |
| AURE3_N3 | parcial | −980.667 / −508.856; 92,72% sobre a magnitude. |

## G. Correções (antes → depois)

A única correção de gabarito foi em **IRBR3_E3**:

| Campo | Antes | Depois |
|---|---|---|
| pergunta | "Qual era o saldo total de aplicações financeiras consolidado do IRB Brasil RE em 30 de junho de 2026, somando as aplicações do circulante e do longo prazo…" | "Qual era o saldo de aplicações financeiras registrado no ativo circulante consolidado do IRB Brasil RE em 30 de junho de 2026?" |
| tipo_pergunta | derivada | factual |
| valor_origem | 8353283 | 4414934 |
| id do valor | aplicacoes_total_30jun26 | aplicacoes_financeiras_30jun26 |
| fontes | 1.01.02, 1.02.01.01, 1.02.01.02, 1.02.01.03 | 1.01.02 |
| formas_alternativas | 2 | 0 |
| apresentacao_referencia | R$ 8,35 bilhões | R$ 4,41 bilhões |
| decisao_metodologica | — | registrada (Emenda 1) |

**Consequências nos metadados:**

- `sha256_protocolo` passou de `6c3a5c74…` para `e0b37460…`, por causa da emenda.
- `sha256_revisao_tecnica` foi atualizado.
- `construido_em` foi atualizado.

Nenhum outro campo de nenhum outro caso mudou. Isso foi verificado por comparação estrutural
com a cópia anterior ao fechamento.

## H. Contagem

| Item | Valor |
|---|---|
| Casos | 96 |
| Empresas | 12 (8 casos cada) |
| Categorias | N1–N5 e E1–E3 (12 de cada) |
| presente / parcial / ausente | **69 / 15 / 12** |
| Divergências da estimativa do protocolo | 0 |
| Casos com verificação determinística | 84 (N4 = NAO_APLICAVEL, 12) |
| Respostas, scores e classes de comportamento no dataset | nenhum |

## I. Testes

A suíte completa foi rodada com `python -W default -m unittest`, em 14 módulos:

| Conjunto | Testes |
|---|---|
| Existentes (11 módulos) | 190 |
| `test_ragas_dataset` | 19 |
| `test_ragas_exatidao` | 33 |
| `test_ragas_comportamento` | 12 |
| **Total** | **254 — OK, 0 falhas, 0 warnings** |

Novos testes do dataset:

- o texto pré-registrado do protocolo está intacto (hash do prefixo);
- IRBR3_E3 usa só a conta 1.01.02;
- nenhum valor exigido é menor que 1000.

## J. Integridade e segurança

- **Segredos:** a varredura dos 14 arquivos novos ou modificados não encontrou nada.
  `api_key.txt` é ignorado pelo git e não está rastreado.
- **Código e mapa de tickers:** `modulos/` e `dados/ticker_map.csv` estão inalterados
  (`git diff --quiet`).
- **Artefatos congelados:** os de `avaliacao/validacao_manual/` são byte-idênticos.
  `sha256sum -c` passou nas duas listas (37 e 36 arquivos) e o git não mostra alterações em
  `avaliacao/validacao_manual/` nem em `tests/fixtures/`.
- **Protocolo:**
  - O prefixo pré-registrado (tudo antes de "## Emendas") tem SHA-256
    `32e6fef3…575a`, igual ao do commit `b17ea73`.
  - O diff só substitui o marcador "*(nenhuma)*" pela Emenda 1.
- **.gitattributes:** a regra `avaliacao/ragas/** -text` foi acrescentada sem alterar as
  existentes.
  - Com ela, `git hash-object` e `git hash-object --no-filters` coincidem em todos os
    arquivos de `avaliacao/ragas/`.
  - Antes dela, só `dataset_tcc2_revisao.csv` (CRLF, gerado pelo módulo `csv`) mudaria na
    normalização.
  - O git avisa que o próprio `.gitattributes` (LF) será convertido para CRLF na cópia de
    trabalho quando for tocado; isso não afeta o conteúdo versionado.

## K. Limitações

1. A revisão final foi feita por Claude Code, com um script independente. **Ela não
   substitui a revisão humana do autor.**
2. A regra C transfere para decisão manual os números isolados entre parênteses, o que pode
   aumentar os casos `PENDENTE_REVISAO_SINAL` na coleta.
3. Quem classifica o comportamento é o próprio autor, sozinho (protocolo, Seção 15.10). Não
   há medida de concordância entre avaliadores.
4. O contexto é o mesmo para as 8 perguntas de cada empresa (consulta fixa). A
   disponibilidade reflete esse contexto, não o documento completo.
5. A Emenda 1 muda um gabarito e o leitor de sinais antes da coleta. O protocolo registra o
   motivo e o momento. Os resultados devem citar a emenda.

## L. Arquivos prontos

**Modificados (versionados):**

| Arquivo | SHA-256 |
|---|---|
| `.gitattributes` | `e71870b6e9488e33f6d74f0efa021d7e26999a41e1f0bc9ce7adac1bc1488c83` |
| `avaliacao/ragas/PROTOCOLO_RAGAS_TCC2.md` | `e0b374608a1e4f5b4cae530931e4626f6f67c145d215212ea7ecd55b08da2490` |

**Novos (não rastreados):**

| Arquivo | SHA-256 |
|---|---|
| `avaliacao/ragas/dataset_tcc2.json` | `313bdf359fdeabb063ceec3bcca12ebfe3b52caae346b3ff1d9f3dc23196bc5e` |
| `avaliacao/ragas/revisao_tecnica_tcc2.json` | `ea2408151cf38f1ba38c30893a9a3c5c169848c6732fd6791df3345770d5d244` |
| `avaliacao/ragas/dataset_tcc2_revisao.csv` | `6b3cf7ef306075a16b2e23d391e1a03c5393292c4c03288f2d88ccc68c1fd9f1` |
| `avaliacao/ragas/RELATORIO_validacao_dataset.md` | `bc1fc2a0b9f40b81b7fe0e11ab2eb7f29745474ab4f0808b0babfb9c882de82c` |
| `avaliacao/ragas/RUBRICA_COMPORTAMENTO_TCC2.md` | `c1b401ad11bb6a828c85ed1aa92515a71feaa04222089766a8411d2950ee69dc` |
| `avaliacao/ragas/comportamento.py` | `d2a3e7e79d2275b9de3dff0b64b0bc3b0455c3fa9090766e068c290117febad2` |
| `avaliacao/ragas/construir_dataset.py` | `8f45d9666f46bc5767dae3be5e8460068732ebf0f6cad2f97a7da286f2a704eb` |
| `avaliacao/ragas/exatidao.py` | `2b4b11706841701ed6ffd551a4789431fa9102c65cf1302104cfa600ce432ff0` |
| `avaliacao/ragas/validar_dataset.py` | `8b2f23e457ee1a92ac31937a26fa477ae867f06b0267ad6f9c611ee7c5570a10` |
| `tests/test_ragas_dataset.py` | `e23dc63c552607878649d1babe2059504e1d08f89b12498bdf951487e6ef7c82` |
| `tests/test_ragas_exatidao.py` | `8cd206fed26b7a4436dd5dc130c76370642b1aa25b3a27a2e4382d52c4b79784` |
| `tests/test_ragas_comportamento.py` | `26b2d659d11059f1f352f40450e01bb018d480a93d9830f2bef0073e674c002b` |
| `avaliacao/ragas/RELATORIO_fechamento_dataset.md` | este arquivo |

O dataset registra o SHA-256 do protocolo com a emenda e o da revisão técnica, e os testes
conferem os dois.
