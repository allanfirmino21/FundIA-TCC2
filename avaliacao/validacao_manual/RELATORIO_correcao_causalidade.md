# Correção de causalidade da narrativa — decomposição do resultado

Relatório complementar a `RELATORIO_validacao_manual_final.md` (commit
`c5f4464`), que permanece congelado e sem alteração. Registra a Correção 4:
diagnóstico, implementação e revalidação da explicação da variação do
lucro/prejuízo.

## 1. Identificação

| Item | Valor |
|---|---|
| Commit de partida | `c5f44643880e191472155a2d4b5821265a32c6d4` |
| Código avaliado | `c5f4464` + diff pendente `git diff HEAD` SHA-256 `83eac381f0fbee163c0784002a743ce2632490a75699fa35a737bddf3f851f96` (commitado junto com este relatório) |
| Documento | ITR, DT_REFER 2026-06-30, VERSAO 1 |
| Empresas | WEGE3 (CVM 5410), BBAS3 (CVM 1023), ZAMP3 (CVM 24317) |
| Chamada | `analisar(ticker, "ITR", periodo="2026-06-30", versao="1")` |
| Modelo de redação | `gemini-2.5-flash` |
| Auditoria | versão 2.0 (`verificar_conceito=True`), sem alteração nesta etapa |
| Testes | 175 de 175 (163 anteriores + 12 desta etapa) |
| Execuções | uma por empresa em cada rodada |

| Pasta | Código | Papel |
|---|---|---|
| `<TICKER>_ITR_2026-06-30_v1_pos_decomposicao/` | `c5f4464` + diff `d46a891d4c419af4…` | primeira tentativa (decomposição + regras iniciais do Prompt 2) |
| `<TICKER>_ITR_2026-06-30_v1_pos_decomposicao_v2/` | `c5f4464` + diff `83eac381f0fbee16…` | versão validada (posição dos subtotais + regras 11 e 12 + LIMITAÇÕES) |

Nas seis execuções a fonte é byte a byte a mesma das execuções `_final`
(mesmo SHA-256), o contexto narrativo é só o Cabeçalho (194–195 caracteres) e
a chave da API não aparece em nenhum artefato.

## 2. Objetivo

Corrigir a classe de erros em que o LLM explica corretamente os números, mas
atribui causalidade errada à variação do lucro/prejuízo. Na validação final
(`_final`), os casos eram:

- ZAMP3: atribuir o aumento do prejuízo às despesas operacionais, com o
  resultado operacional em alta;
- BBAS3: ler ao contrário o efeito do IR/CS e tratar o resultado antes dos
  tributos como fator da queda;
- uso de fluxos de caixa (DFC) como sinal de melhora/piora e como destaque
  positivo ou de atenção apenas pela direção.

## 3. Solução

### 3.1 `decomposicao_resultado` (`modulos/metricas.py`)

Bloco novo nas métricas, calculado de forma determinística a partir das linhas
de primeiro nível da DRE (`CD_CONTA` `3.xx`, exceto `3.99`):

- **Cadeia e subtotais.** Uma linha é subtotal quando é igual à soma acumulada
  das linhas anteriores nos dois períodos (tolerância de R$ 1 mil); linha
  zerada nos dois períodos nunca é subtotal. Não há regra por empresa nem por
  ticker; os únicos nomes usados são as contas fixas dos planos da CVM.
- **Âncora.** "Resultado Antes do Resultado Financeiro e dos Tributos"
  (comercial, seguradoras) ou, na falta dela, "Resultado Antes dos Tributos
  sobre o Lucro" (bancos). Plano bancário sem resultado financeiro forçado.
- **Ponte e contribuições.** A âncora e as parcelas seguintes com valor, até o
  resultado final. `contribuicao` = valor atual − valor anterior.
- **`efeito`.** Puramente aritmético: "aumentou o resultado", "reduziu o
  resultado" ou "não alterou o resultado". Sem palavras de julgamento, sem
  `maior_contribuicao` nem ranking.
- **Abertura da âncora.** Como a âncora se formou (subtotal anterior + linhas
  até a âncora), com efeito sobre "o subtotal", nunca sobre o resultado final.
  Descartada se não fechar.
- **Subtotais intermediários.** Informativos, deduplicados; cada um tem `apos`
  e `antes`, as parcelas da ponte entre as quais ele fica. Não entram na soma.
- **Fechamento (`fecha`).** `true` só quando o resultado final da DRE é igual a
  `lucro_liquido` e a soma das contribuições é igual à variação do resultado,
  sem parcela residual. Caso contrário, `fecha=false` com `motivo` e a
  instrução de não usar a estrutura para explicar a variação.

Correção associada: o `lucro_liquido` passou a reconhecer "Lucro ou Prejuízo
Líquido do Período", a conta final do plano bancário individual. Afeta só os 5
bancos listados na seção 4.

### 3.2 Regras do Prompt 2 (`modulos/prompt2.py`)

- **Regra 11 — POR QUE O RESULTADO MUDOU**, válida para todas as seções,
  inclusive o RESUMO:
  - causa, contribuição, compensação ou fator da variação vêm exclusivamente
    de `decomposicao_resultado`, e só com `fecha=true`;
  - `efeito` é soberano: parcela que aumentou o resultado nunca é apresentada
    como fator da queda (nem como "menor contribuição/impacto"), e parcela que
    reduziu nunca é fator da melhora;
  - o efeito não é deduzido pelo nome da conta, pelo sinal nem pelo percentual;
  - exemplo genérico de banco: resultado antes dos tributos positivo + IR/CS
    negativo → a queda se explica pela parcela negativa;
  - a abertura não substitui a contribuição líquida da parcela;
  - os subtotais intermediários são apresentados na posição `apos`/`antes`;
  - com `fecha=false`, nenhuma causa, só as variações.
- **Regra 12 — FLUXOS DE CAIXA:**
  - não são receita, despesa nem lucro e nunca explicam o lucro/prejuízo;
  - só descritos em SAÚDE DO CAIXA E DÍVIDAS, pelo que aconteceu;
  - inversão de sinal é somente inversão de sinal;
  - sem "melhora", "piora", "positivo", "negativo", "favorável" ou
    "desfavorável" como juízo da direção;
  - fora de "O QUE FOI POSITIVO" e "O QUE MERECE ATENÇÃO" por direção (regra
    repetida dentro das duas listas);
  - em bancos, o fluxo operacional não é "geração de caixa das operações
    principais".
- **RESUMO:** "Se disser por que o resultado mudou, siga a regra 11."
- **LUCRO:** usa a ponte e cita os subtotais na posição indicada.
- **LIMITAÇÕES:** somente `dados_ausentes`. Nunca regras do prompt, termos
  proibidos, demonstrações, métricas não pedidas, campos `nao_aplicavel` ou
  ausência de trechos narrativos. Com a lista vazia: "Não foram identificados
  dados ausentes específicos nesta análise."
- Nenhuma regra cita ticker (verificado por teste).

### 3.3 Testes

- `tests/test_decomposicao_resultado.py` (novo): planos comercial, bancário
  com participações, banco IFRS, seguradora, plano antigo sem âncora, DRE
  zerada, âncora de fallback, sem âncora, sem `CD_CONTA`, tolerância, final ≠
  `lucro_liquido`, correção do lucro bancário, valores exatos de
  WEGE3/BBAS3/ZAMP3 e posição dos subtotais (`apos`/`antes`, subtotal fora da
  soma).
- `tests/test_prompt2_regras.py` (novo): presença das regras críticas no texto
  do prompt, sem chamar o LLM, e ausência de tickers.
- `tests/test_cd_conta.py`, `tests/test_demonstracoes_resumidas.py`: ajustes
  para o novo bloco de métricas.

## 4. Abrangência nas 629 companhias

Medição feita com o código validado (`HEAD` × working tree, ITR 2026-06-30,
última versão de cada companhia), comparada com a rodada anterior da
decomposição. Os números abaixo foram reconferidos a partir dos resultados
salvos da varredura, sem refazê-la.

| Verificação | Resultado |
|---|---|
| `fecha = true` | 626 de 629 |
| Exceções | 2 DREs zeradas (CIA SEC DE CRÉDITOS FINANCEIROS CARTÕES CONSIGNADOS I, CLI SUL) e Dibens Leasing (plano antigo, sem âncora) — as mesmas de antes |
| Contribuição, resultado, abertura, fechamento ou motivo alterados | nenhum |
| Subtotais intermediários | mesmos valores; só acrescidos de `apos`/`antes` |
| Métricas preexistentes alteradas | só `lucro_liquido` dos 5 bancos: Banpará (1171), BNB (1228), Paraná Banco (20729), ABC Brasil (20958), Banese (1120); 624 companhias idênticas |
| Dependência de ticker | nenhuma regra |

Posições observadas dos subtotais intermediários:

| Após | Antes | Casos |
|---|---|---|
| Resultado financeiro | IR/CS | 560 |
| IR/CS | Resultado líquido de operações descontinuadas | 31 |
| IR/CS | Participações nos lucros e contribuições estatutárias | 6 |

## 5. Validação nas três empresas (`_pos_decomposicao_v2`)

Leitura manual integral de cada narrativa contra `resultado_analisar.json`.

### WEGE3

| Parcela da ponte | Contribuição | Efeito |
|---|---|---|
| Resultado antes do resultado financeiro e dos tributos | −R$ 159,93 mi | reduziu o resultado |
| Resultado financeiro | +R$ 18,22 mi | aumentou o resultado |
| IR/CS | +R$ 38,11 mi | aumentou o resultado |

- Causalidade correta no RESUMO e no LUCRO: queda explicada pelo operacional,
  com compensação parcial do financeiro e do IR/CS.
- Abertura da âncora descrita como formação do subtotal.
- DFC fora da causalidade; fluxos só descritos em SAÚDE DO CAIXA ("passou de
  negativo para positivo"), sem melhora/piora.
- Nenhum fluxo em POSITIVO/ATENÇÃO apenas pela direção.
- LIMITAÇÕES: frase neutra.

### BBAS3

| Parcela da ponte | Contribuição | Efeito |
|---|---|---|
| Resultado antes dos tributos sobre o lucro | ≈ +R$ 1,08 bi | aumentou o resultado |
| IR/CS | ≈ −R$ 2,48 bi | reduziu o resultado |

- RESUMO reconhece o resultado antes dos tributos como contribuição positiva
  ("contribuído positivamente em R$ 1,08 bilhão").
- Queda do lucro atribuída ao IR/CS, que reduziu o resultado em R$ 2,48 bi
  (RESUMO e LUCRO).
- DFC fora da causalidade; nenhuma inversão chamada de melhora/piora; sem
  "geração de caixa das operações principais".
- LIMITAÇÕES: frase neutra; sem texto introdutório antes do RESUMO.
- **Desvio remanescente:** "Caixa Líquido das Atividades Operacionais diminuiu
  53,0%" em O QUE MERECE ATENÇÃO, e o RESUMO termina com "a diminuição do caixa
  líquido das atividades operacionais também merece atenção" — seleção pela
  direção, contrariando a regra 12.

### ZAMP3

| Parcela da ponte | Contribuição | Efeito |
|---|---|---|
| Resultado antes do resultado financeiro e dos tributos | +R$ 4,22 mi | aumentou o resultado |
| Resultado financeiro | −R$ 24,68 mi | reduziu o resultado |
| IR/CS | −R$ 18,22 mi | reduziu o resultado |

- Operacional como contribuição positiva; financeiro e IR/CS como parcelas que
  reduziram o resultado (RESUMO e LUCRO).
- Resultado antes dos tributos (−R$ 142,52 mi) na posição correta: após o
  resultado financeiro e antes do IR/CS.
- Despesas operacionais fora da causalidade final: aparecem só na abertura,
  "reduzindo o subtotal" (−R$ 274,11 mi), ao lado do resultado bruto
  (+R$ 278,33 mi).
- DFC fora da explicação (nenhum fluxo citado).
- LIMITAÇÕES: frase neutra.

### Evolução em relação à primeira tentativa (`_pos_decomposicao`)

| Empresa | Problema na primeira tentativa | Na v2 |
|---|---|---|
| WEGE3 | Caixa operacional em POSITIVO pela direção | resolvido |
| BBAS3 | RESUMO: "menor impacto positivo do resultado antes dos tributos" | resolvido |
| BBAS3 | Inversão de fluxo tratada como "melhora" em POSITIVO | resolvido |
| BBAS3 | Fluxos em POSITIVO/ATENÇÃO pela direção | parcial (resta o fluxo operacional) |
| BBAS3 | LIMITAÇÕES com itens inventados; texto introdutório | resolvido |
| ZAMP3 | Resultado antes dos tributos fora de ordem | resolvido |
| ZAMP3 | "Despesas financeiras" no RESUMO em vez do resultado financeiro | resolvido |
| ZAMP3 | Custo descrito como "ponto positivo" | resolvido |

## 6. Auditoria

Resultados reportados pelo auditor 2.0, sem alteração do auditor:

| | WEGE3 | BBAS3 | ZAMP3 |
|---|---|---|---|
| Números verificados | 50 | 48 | 52 |
| CONFERE / DIVERGENTE | 43 / 7 | 43 / 5 | 49 / 3 |
| Conformidade reportada | 86,0% | 89,6% | 94,2% |
| Cobertura conceito + valor | 91,9% | 93,5% | 97,4% |
| DIVERGENTES falsos (revisão manual) | 7 de 7 | 5 de 5 | 3 de 3 |
| Números corretos (revisão manual) | 50/50 | 48/48 | 52/52 |

Na primeira tentativa o auditor reportou 34/36 (94,4%), 45/46 (97,8%) e
44/46 (95,7%). A queda da taxa reportada na v2 não indica erro novo: as
narrativas passaram a citar contribuições pelo nome completo das contas, que
é justamente o formato em que o auditor produz falsos alarmes.

Padrões de falso alarme observados (15 no total):

1. **"Lucro" no final do nome composto de IR/CS** ("Imposto de Renda e
   Contribuição Social sobre o Lucro"): o valor é lido como lucro líquido.
2. **Sinal inferido do contexto textual:** "variação do lucro em R$ X" lido
   como lucro positivo; "passou de negativo para positivo, atingindo R$ X"
   lido como valor negativo.
3. **Parêntese em "Aumento (Redução) de Caixa":** o auditor descarta o
   parêntese e o conceito vira "caixa".
4. **Rótulo entre crases após o valor:** fica fora da janela de leitura do
   auditor.

Nenhum desses padrões foi corrigido nesta etapa.

## 7. Limitações remanescentes

- BBAS3: fluxo operacional ainda selecionado para ATENÇÃO e RESUMO pela
  direção (regra 12 não seguida integralmente).
- BBAS3: não explicita que o IR/CS positivo (R$ 6,12 bi → R$ 3,64 bi)
  funciona como crédito tributário que soma ao resultado, e que foi a redução
  desse crédito que reduziu o lucro (o efeito aritmético está correto).
- WEGE3: EBITDA omitido na narrativa.
- ZAMP3, redação: dupla negação ("reduziu o resultado em −R$ 24,68 milhões",
  "prejuízo de −R$ 154,68 milhões"), "compromissos financeiros de longo prazo"
  sem sustentação nos dados e 5 itens em ATENÇÃO (o formato pede 2 a 4).
- WEGE3, redação: nomes de contas entre crases.
- Auditor 2.0: os quatro padrões de falso alarme da seção 6.
- Uma única execução do LLM por empresa nesta rodada: a variabilidade entre
  execuções não foi medida.

## 8. Conclusão

- A Correção 4 resolveu a classe central de erros de causalidade observada na
  validação manual: nas três empresas, a variação do resultado é explicada
  pelas parcelas da ponte, com o efeito de cada uma respeitado, inclusive no
  RESUMO.
- Não houve erro numérico novo nem erro de conta × valor (150 de 150 números
  corretos na revisão manual).
- Nenhuma DFC foi usada para explicar o lucro/prejuízo.
- A ponte generalizou estruturalmente: fecha em 626 das 629 companhias, e as 3
  exceções declaram `fecha=false` com motivo.
- Permanecem limitações qualitativas de geração (seção 7) e limitações do
  auditor, que agora subestima a conformidade real. Os resultados valem para
  uma execução por empresa e não autorizam afirmar que o sistema está
  totalmente correto.

## 9. Integridade dos artefatos

Artefatos anteriores verificados byte a byte antes do commit (idênticos aos
de `c5f4464`):

```
96c321232278beb5eb5a4eff167b5cedf76611b55e47f8ccb62c6c051c96bde8  BBAS3_ITR_2026-06-30_v1_final/BBAS3_ITR_2026-06-30.txt
269deb61d5d99e65dba274bae6602d196eebb9da32a868364cacc04bd3d78860  BBAS3_ITR_2026-06-30_v1_final/BBAS3_ITR_2026-06-30.txt.sha256
3d474162855dc61ac85f2b5a5ae3b648645654f1827dc7ad62552ecd7db83408  BBAS3_ITR_2026-06-30_v1_final/auditoria.json
f7fabcbf07dad69d1eab7a62c52adc7f02bccf1200fbc90da4a2a7489f536054  BBAS3_ITR_2026-06-30_v1_final/execucao.json
2116922557290f682785742f5f2946a093ea2510e8209b42cd7e2ad8ef592898  BBAS3_ITR_2026-06-30_v1_final/narrativa.md
a61c5a7f2b029d523af56551152f32cecf77d2acc736ce219cc89746819ce1c5  BBAS3_ITR_2026-06-30_v1_final/resultado_analisar.json
500d0c0d51df24cf9d0a166c24f3eea033b74a6eb63285cc4349036857bb8ba6  WEGE3_ITR_2026-06-30_v1_final/WEGE3_ITR_2026-06-30.txt
7b8aa7f3a21ab1535db5e7f58df80398d3aa2017b3ff7d891348c314627283b8  WEGE3_ITR_2026-06-30_v1_final/WEGE3_ITR_2026-06-30.txt.sha256
8312d43218d8b5a8ffbd33d2246a4c8d447a891ab534058de9b19643e4f8c800  WEGE3_ITR_2026-06-30_v1_final/auditoria.json
9f5d6b1a56eaa7e5a8710288503b6b5c18ba8903234c4d33a48f9fd0a8b7b45f  WEGE3_ITR_2026-06-30_v1_final/execucao.json
d003e2c179dab32b83171539131cfa4a56c2bb0a5c339280fb39b952bfa49eaa  WEGE3_ITR_2026-06-30_v1_final/narrativa.md
d989a077af0335435307c9ead64f0b72cfff55a14ca0c4b8fbda97cb7497a526  WEGE3_ITR_2026-06-30_v1_final/resultado_analisar.json
044d8ad11f532cc3f65127a798d06bd689aad50f20da38a0b42e80d0f3bcf983  ZAMP3_ITR_2026-06-30_v1_final/ZAMP3_ITR_2026-06-30.txt
7a5a057689258121174d43e28f8f10549a1ac9fc373d900a6dd22535d9ffd42e  ZAMP3_ITR_2026-06-30_v1_final/ZAMP3_ITR_2026-06-30.txt.sha256
525aad3493ea809c53c500b30f2c17ed0150521a007feedb4215fcec7fe276ed  ZAMP3_ITR_2026-06-30_v1_final/auditoria.json
f889281f8ab2a10dc148164a683810013d6188dbbb890f81cf74df816f327763  ZAMP3_ITR_2026-06-30_v1_final/execucao.json
e83a03567f523037c3ac06a20f7aa49f2564fc66344dd69fbfe85365495554ef  ZAMP3_ITR_2026-06-30_v1_final/narrativa.md
febfeecd29f9f2b831bfe6f8c09055946fa67fccb589658a4644c5b3e0d514df  ZAMP3_ITR_2026-06-30_v1_final/resultado_analisar.json
5b8e9163da88897267205fc92ecf7bece34853ed8116bce68256afeec3cbc7a0  RELATORIO_validacao_manual_final.md
```

Artefatos desta etapa:

```
0548a1417ad6b06f407056a774202beb4067b5df00296f84309343e3cfab1bdc  BBAS3_ITR_2026-06-30_v1_pos_decomposicao/auditoria.json
f4fc575b8f8b0d86c468cff2baab3a3f31a3c6694e4797b58df1ecf498104ad0  BBAS3_ITR_2026-06-30_v1_pos_decomposicao/execucao.json
cff7e8637e19f708ff0a1513fcbc765a6f2546e0edf0b5cabd2f6def3e59a4f5  BBAS3_ITR_2026-06-30_v1_pos_decomposicao/narrativa.md
3de1acf4b2dbd9e77453cd5f1d1a90d84cc606cc58af17cd4236dd16b029a8d4  BBAS3_ITR_2026-06-30_v1_pos_decomposicao/resultado_analisar.json
1afb01486944bbfcef5a5088fae78f66165799872c450390c9d400d50d4becb4  BBAS3_ITR_2026-06-30_v1_pos_decomposicao_v2/auditoria.json
71b86bb157a7157f681d7be57d7577844fadfba1012e4a96c543821cbcdb5af1  BBAS3_ITR_2026-06-30_v1_pos_decomposicao_v2/execucao.json
5f2ce482ae87d9e2df7f115849a52f4274627b920c0fb36d5b324c0c9401e9eb  BBAS3_ITR_2026-06-30_v1_pos_decomposicao_v2/narrativa.md
36c60292341c91d0f77388907969049c1535888a849c40656f216033d5cc2d28  BBAS3_ITR_2026-06-30_v1_pos_decomposicao_v2/resultado_analisar.json
9044ead349b7d7eb38c626c6f89eea69f19d22697c4352424e1fbc0cee2f74c3  WEGE3_ITR_2026-06-30_v1_pos_decomposicao/auditoria.json
f9c38cedfb2093e071a65ac9a8b14cf1a8511289faa044c7e7ec359aedf5e10b  WEGE3_ITR_2026-06-30_v1_pos_decomposicao/execucao.json
87cf3d4ab429fa7560d1d4c3745046a0bf79c4b5e77b2512e20dc439e7b08544  WEGE3_ITR_2026-06-30_v1_pos_decomposicao/narrativa.md
d5441e1984e5c5df3cbcbcf0f37681af160deb4cca2d3dde191aa0d75b78e50b  WEGE3_ITR_2026-06-30_v1_pos_decomposicao/resultado_analisar.json
0f93c4b35b3cd6e997e842d67370f785c550ce94f1c5f5c509d4802d00df70fe  WEGE3_ITR_2026-06-30_v1_pos_decomposicao_v2/auditoria.json
39993e4b42d13449c5cd1c8319fdab58c5394b1413be409dc7da09bbc04de536  WEGE3_ITR_2026-06-30_v1_pos_decomposicao_v2/execucao.json
becee9311c379f4b576af37573dfced7398c7af60820dd6a863d3dde08275128  WEGE3_ITR_2026-06-30_v1_pos_decomposicao_v2/narrativa.md
3c630b4fdf522741bc7a11d6f7c0c778e894c4a9dfaa93bce24cbe81fc3dbb83  WEGE3_ITR_2026-06-30_v1_pos_decomposicao_v2/resultado_analisar.json
0dc112d34ce07bec0ab2e26f13b04cf380649a310040fb80129bb43da8460f92  ZAMP3_ITR_2026-06-30_v1_pos_decomposicao/auditoria.json
9a8acc6910f349a14ed006e28ee3e9d434cd56917791f37f4a71c314990081ba  ZAMP3_ITR_2026-06-30_v1_pos_decomposicao/execucao.json
8ad9f553250f510493dfbf5fa622a07eb4596530f7fc8ad9891147265fcef621  ZAMP3_ITR_2026-06-30_v1_pos_decomposicao/narrativa.md
30906ba5ecb8e792a3ab8f2b206aa1de5dc436345a0f0c0ba75485292baf6b75  ZAMP3_ITR_2026-06-30_v1_pos_decomposicao/resultado_analisar.json
eea0cb25833fdf4b020e8300aaeb33c1f8b3fb6b21c7bd75d52e68edba3b160e  ZAMP3_ITR_2026-06-30_v1_pos_decomposicao_v2/auditoria.json
d25d51ae7196aba9e560c068a8ae7964ce93c60205f50ae83c13531c2b32c93d  ZAMP3_ITR_2026-06-30_v1_pos_decomposicao_v2/execucao.json
5b453ca6386e954dc2bf7f6fee13176281bf08332e21f1746a28784d2d45dded  ZAMP3_ITR_2026-06-30_v1_pos_decomposicao_v2/narrativa.md
58d2f7d9d096e28ed65ed90a119e8934cd40ab4125ac4c044b13680e6db9801a  ZAMP3_ITR_2026-06-30_v1_pos_decomposicao_v2/resultado_analisar.json
```

As fontes (`<TICKER>_ITR_2026-06-30.txt` e `.sha256`) das seis pastas são
idênticas às das pastas `_final` (hashes acima).
