# Validação manual final do FundIA — revalidação pós-correções

## 1. Identificação da validação

| Item | Valor |
|---|---|
| Commit avaliado | `e4d96e1b1a12dd025b44c5c3f3f783bc366b2cf5`, sem alteração de código pendente |
| Documento | ITR, DT_REFER 2026-06-30, VERSAO 1 |
| Empresas | WEGE3 (CVM 5410), BBAS3 (CVM 1023), ZAMP3 (CVM 24317) |
| Chamada | `analisar(ticker, "ITR", periodo="2026-06-30", versao="1")` |
| Modelo de redação | `gemini-2.5-flash`; embeddings `paraphrase-multilingual-mpnet-base-v2` |
| Auditoria | versão 2.0 (`verificar_conceito=True`): existência do valor, sinal e direção, e par conceito + valor em valores monetários |
| Testes antes de cada execução | 139 de 139 |
| Artefatos | `<TICKER>_ITR_2026-06-30_v1_final/` |

**Objetivo.** A validação manual inicial (`RELATORIO_validacao_manual.md`,
commit `183e69f`) levantou quatro achados. Na etapa pós-Prompt 2 apareceu mais
um (EBIT × EBITDA na ZAMP3). Cada achado passou por diagnóstico e correção.
Esta revalidação roda as três empresas no estado final do código e confere, por
leitura manual integral de cada narrativa contra `resultado_analisar.json`,
`demonstracoes_resumidas` e `auditoria.json`:

- se os achados foram resolvidos;
- quais problemas continuam.

**Fontes usadas na comparação.** As execuções anteriores, todas preservadas sem
alteração:

| Pasta | Commit registrado |
|---|---|
| `_v1` | `183e69f` / `504ce6d` |
| `_pos_cd_conta` | só WEGE3 |
| `_pos_prompt2` | `870542e` + alterações depois commitadas em `cea3018` e `0b05768` |

Em todas as execuções finais:

- o documento veio do cache local, com a fonte byte a byte igual à das
  execuções pós-Prompt 2 (mesmo SHA-256);
- o período e a versão retornados conferem com os pedidos;
- nenhuma etapa falhou.

## 2. Resultado executivo

**Auditoria automática ≠ revisão manual.** As quatro primeiras linhas da tabela
são o que o sistema reportou. As demais são o resultado da revisão manual.

| | WEGE3 | BBAS3 | ZAMP3 |
|---|---|---|---|
| Números verificados pela auditoria | 50 | 44 | 47 |
| CONFERE | 49 | 43 | 47 |
| DIVERGENTE reportado | 1 | 1 | 0 |
| Conformidade reportada | 98,0% | 97,7% | 100,0% |
| DIVERGENTE que é falso alarme (revisão manual) | 1 de 1 | 1 de 1 | — |
| Conformidade numérica após revisão manual | 50/50 (100%) | 44/44 (100%) | 47/47 (100%) |
| Cobertura conceito + valor (moedas) | 22/24 (91,7%) | 17/21 (81,0%) | 26/26 (100%) |
| Erro numérico | não | não | não |
| Erro de associação conta × valor | não | não | não |
| Erro de causalidade/interpretação | sim (qualitativo) | **sim (grave)** | **sim** |
| Principais problemas restantes | fluxo de financiamento positivo lido como "melhora" | queda do lucro atribuída às causas erradas; efeito do IR/CS invertido; DFC usada para explicar lucro | piora atribuída também às despesas operacionais; IR/CS fora da explicação do RESUMO |
| Contextos (ctx_num / ctx_nar, caracteres) | 10.620 / 194 | 8.807 / 194 | 8.541 / 195 |
| ctx_nar | só Cabeçalho | só Cabeçalho | só Cabeçalho |

Os dois DIVERGENTES reportados foram examinados um a um (seção 5) e **não são
erros das narrativas**: o valor e o conceito citados estão corretos nos dois
casos.

## 3. Achados originais × estado final

| # | Empresa | Problema original | Causa identificada | Correção implementada | Evidência na execução final | Classificação |
|---|---|---|---|---|---|---|
| 1 | WEGE3 | Liquidez total de R$ 13,23 bi: a aplicação 1.01.01.02, que já está dentro do caixa, foi somada de novo; dívida líquida −R$ 8,16 bi | Seleção de conta pelo nome e pela ordem; o `.txt` não guardava `CD_CONTA` | `53ce987`: `CD_CONTA` gravado no documento; aplicação financeira = filha direta de "Ativo Circulante" (1.01.02) | Liquidez total R$ 8,80 bi; dívida líquida −R$ 3,73 bi; com arrendamentos −R$ 2,97 bi. Os três valores aparecem na narrativa com o conceito verificado pela auditoria. R$ 13,23 bi não aparece | **RESOLVIDO** |
| 2 | WEGE3 | "Resultado com juros" de R$ 3,92 mi → R$ 10,55 mi, que é o resultado financeiro da DRE **individual** num relatório consolidado | O canal narrativo completava a cota com qualquer tabela, sem filtro de base; o Prompt 2 rotulava resultado financeiro como "juros" | `873e013`: base principal na recuperação. `cea3018`: ctx_nar só com o cabeçalho e `demonstracoes_resumidas` na base principal. `0b05768`: regra 2 (resultado financeiro explicado como receitas menos despesas financeiras) | ctx_nar com 194 caracteres, só o Cabeçalho. Resultado financeiro de R$ 47,59 mi → R$ 65,82 mi, consolidado, com receitas (−1,1%) e despesas financeiras (3,0% menores) nas contas certas. 10,55 e 3,92 não aparecem | **RESOLVIDO** |
| 3 | BBAS3 | Captação no mercado aberto `nao_disponivel`, embora a conta 2.02.02 exista (845.408.764) | Busca pelo nome exato no singular; a CVM usa três grafias | `6096ce4`: busca pelo nome normalizado; a conta-pai vence a subconta homônima | `captacao_mercado_aberto` = R$ 845,41 bi; destaque "+16,3%" (de 727.039.247 para 845.408.764). Narrativa: "aumentou 16,3%… totalizando R$ 845,41 bilhões", CONFERE com o conceito verificado. Ressalva: não há campo `captacao_anterior`, então os R$ 727,04 bi ficam implícitos no percentual | **RESOLVIDO** |
| 3a | BBAS3 | Efeito de `nao_disponivel`: "Não foi possível identificar os dados de captação" nas limitações | Conflito entre a regra 5 e a seção de limitações do Prompt 2 | `0b05768`: regra 5 e limitações só a partir de `dados_ausentes`. No pós-Prompt 2, a captação ainda era `nao_disponivel` e não foi citada como ausente | Limitações sem nenhum campo `nao_disponivel` | **RESOLVIDO** |
| 3b | BBAS3 | Basileia e inadimplência citadas nas limitações, fora de `dados_ausentes` (original e pós-Prompt 2) | Fonte provável: a `nota` das métricas bancárias menciona esses indicadores, e o LLM a transforma em limitação | Regra de limitações do `0b05768`; a `nota` continua nas métricas | Não aparecem na execução final. Como a fonte do texto continua no contexto, não há garantia estrutural | **PARCIALMENTE RESOLVIDO** |
| 4 | ZAMP3 | "Receitas e despesas com juros" de R$ 103,42 mi → R$ 162,23 mi, uma linha de ajuste da DFC sobre arrendamentos, usada para explicar a piora do resultado | A DFC era a única tabela no canal narrativo; a DRE consolidada nunca chegava ao LLM; a regra 2 impunha o rótulo "juros" | `cea3018`: ctx_nar só com o cabeçalho; `demonstracoes_resumidas` com o primeiro nível da DRE e da DFC, sem os ajustes 6.01.01.xx. `0b05768`: regras 2 e 10 | 103,42 e 162,23 não aparecem. Resultado financeiro de −R$ 144,60 mi → −R$ 169,28 mi (DRE consolidada, conta 3.06), explicado pela composição: despesas financeiras 17,9% maiores contra receitas +21,4%. Nenhuma linha da DFC explica o prejuízo da ZAMP3 | **RESOLVIDO** |
| 5 | ZAMP3 | R$ 289,21 mi (EBITDA) atribuído ao "Resultado Antes do Resultado Financeiro e dos Tributos" (EBIT, R$ 26,76 mi), com CONFERE na auditoria 1.0 (achado do pós-Prompt 2) | Troca de rótulo pelo LLM; a auditoria 1.0 só verificava a existência do valor | `27dfdd5`: auditoria 2.0 com o par conceito + valor. Na reauditoria do pós-Prompt 2, esse número passa a DIVERGENTE, e testes plantados cobrem as quatro combinações. **Nenhuma alteração impede o LLM de gerar a troca** | EBIT citado duas vezes como R$ 26,76 mi (+18,8%), verificado como `ebit → ebit`. EBITDA não citado. Não houve troca nesta execução, mas isso não se pode atribuir a uma correção | **PARCIALMENTE RESOLVIDO**: a detecção está resolvida, a prevenção não |

A detecção de banco não era achado da validação inicial. Foi corrigida à parte
(`cb73bf6`: CSU Digital e Rodobens eram classificadas como banco). Na BBAS3
final, a classificação e o tratamento bancário estão corretos:

- EBITDA, dívida bruta e dívida líquida `nao_aplicavel`;
- depósitos de R$ 897,94 → R$ 954,02 bi (+6,2%);
- captação presente.

## 4. Problemas remanescentes nas narrativas finais

Todos os números citados conferem. Os problemas abaixo são de interpretação,
completude ou redação.

Tipos usados na classificação:

- **N**: numérico;
- **A**: associação conceito × valor;
- **C**: causalidade/interpretação;
- **P**: completude;
- **R**: redação.

### WEGE3

| # | Problema | Tipo | Gravidade |
|---|---|---|---|
| W1 | "O Caixa Líquido Atividades de Financiamento passou de negativo para positivo, mostrando uma **melhora**…", em "O QUE FOI POSITIVO". O fato está certo (−R$ 2,74 bi → +R$ 627,84 mi, sem percentual, como manda a regra de inversão de sinal). Mas fluxo de financiamento positivo é entrada líquida de recursos de terceiros, coerente com a dívida bruta +10,4%, e não uma melhora | C | moderada |
| W2 | "O custo… ficou menos negativo… **o que é positivo**": o custo caiu menos que a receita (−2,1% contra −3,3%) e a margem bruta encolheu | C | menor |
| W3 | EBITDA (R$ 4,32 bi) não citado; também omitido no pós-Prompt 2 | P | menor |
| W4 | Limitações: "Não foi possível identificar dados ausentes…" soa como falha, quando simplesmente não há dados ausentes | R | menor |

### BBAS3

| # | Problema | Tipo | Gravidade |
|---|---|---|---|
| B1 | RESUMO: "O aumento das despesas de intermediação financeira e a redução do caixa gerado pelas operações foram fatores que contribuíram para essa queda [do lucro]". O resultado bruto de intermediação **cresceu** 3,1% e o resultado antes dos tributos cresceu 65,8%. O fator que de fato derrubou o lucro, o IR/CS, não é citado | C | **grave** |
| B2 | "**Mesmo com a diminuição dos impostos**, o Lucro… diminuiu 18,0%". O IR/CS é positivo, um crédito que soma ao lucro: 1.643.370 + 6.116.746 = 7.760.116 e 2.725.127 + 3.637.834 = 6.362.961. A queda desse crédito (−R$ 2,48 bi) supera o ganho antes dos tributos (+R$ 1,08 bi) e **é a causa** da queda do lucro. A narrativa inverte o efeito | C | **grave** |
| B3 | Caixa operacional usado como causa do lucro (B1), o que viola a regra 10 (a DFC não explica lucro) | C | grave (parte de B1) |
| B4 | "Caixa operacional −53,0%… indicando menor geração de dinheiro das operações principais": num banco, esse fluxo reflete sobretudo as variações de depósitos e empréstimos, não a geração operacional | C | moderada |
| B5 | "Esse crescimento indica que o banco conseguiu expandir suas operações": as receitas de intermediação também variam com a taxa de juros | C | menor |
| B6 | "Depósitos de clientes" nomeia a conta 2.02.01 inteira, que inclui depósitos interfinanceiros; o rótulo vem da métrica | R | menor |

### ZAMP3

A composição real da piora do prejuízo (DRE consolidada, 1S25 → 1S26):

| Item | Variação | Efeito |
|---|---|---|
| Resultado operacional | +R$ 4,23 mi | melhorou |
| Resultado financeiro | −R$ 24,68 mi | piorou |
| IR/CS (+R$ 6,06 mi → −R$ 12,16 mi) | −R$ 18,22 mi | piorou |
| Prejuízo | −R$ 38,67 mi | piorou |

| # | Problema | Tipo | Gravidade |
|---|---|---|---|
| Z1 | RESUMO: "o crescimento das despesas operacionais e financeiras impactou negativamente o lucro". As despesas operacionais cresceram 17,7%, mas o resultado operacional **melhorou** 18,8%. A mesma frase já existia no pós-Prompt 2 | C | **relevante** |
| Z2 | O RESUMO omite o IR/CS, que responde por cerca de 47% da piora. Na seção LUCRO, o efeito é descrito só como "impactando o resultado final", sem direção nem valor; o pós-Prompt 2 dizia "contribuindo para o aumento do prejuízo" | P / C | moderada |
| Z3 | A composição em LUCRO pula o "Resultado Antes dos Tributos sobre o Lucro" (−R$ 142,52 mi, −16,8%) | P | menor |
| Z4 | EBITDA (R$ 289,21 mi) não citado; não há troca | P | menor |
| Z5 | Caixa operacional "mais negativo… **indicando que as operações geraram menos dinheiro**": o fluxo é negativo nos dois períodos, então as operações consumiram mais caixa (o pós-Prompt 2 dizia isso) | R | menor |
| Z6 | "mais compromissos financeiros **de longo prazo**": os arrendamentos incluem a parcela de curto prazo, e os dados não sustentam o "longo prazo" | C | menor |
| Z7 | "quando o prejuízo foi de **−R$** 116,01 milhões": dupla negação | R | menor |

Não há nenhum problema do tipo N (numérico) ou A (associação conta × valor)
nas três narrativas finais.

## 5. Avaliação da auditoria 2.0

### Acertos

- Das 71 moedas das três narrativas, 65 tiveram o par conceito + valor
  verificado (91,5%), todas corretamente, sem erro de associação que passasse
  despercebido.
- Em todos os casos verificados pela revisão manual, o conceito reivindicado e
  o do fato estão certos:
  - liquidez total, dívida líquida e dívida com arrendamentos (WEGE3);
  - depósitos e captação (BBAS3);
  - EBIT, resultado financeiro e receitas financeiras (ZAMP3).
- Na reauditoria das narrativas anteriores, a 2.0 muda um único veredito: o
  R$ 289,21 mi da ZAMP3 pós-Prompt 2, erro real de associação. Com
  `verificar_conceito=False`, a auditoria reproduz exatamente as auditorias
  congeladas.

### Falsos DIVERGENTES

| Empresa | Trecho | Por que é falso alarme |
|---|---|---|
| WEGE3 | "…'caixa e equivalentes' e 'aplicações financeiras de curto prazo' **(liquidez total)**, somou R$ 8,80 bilhões" | O valor é a liquidez total, e o texto diz isso. A regra de extração descarta parênteses por tratá-los como explicação, mas aqui o parêntese é o próprio rótulo. Sobra "aplicações financeiras" como conceito mais próximo |
| BBAS3 | "O Imposto de Renda e Contribuição Social sobre o **Lucro** diminuiu 40,5%, para R$ 3,64 bilhões" | O valor é o IR/CS (conta 3.06). O léxico casa "Imposto de Renda" e deixa o "Lucro" final do nome da conta como conceito separado, que por ser o mais próximo vira o conceito reivindicado (lucro líquido). No documento a mesma conta é classificada certo, porque ali vale o primeiro conceito e, na narrativa, o último |
| ZAMP3 | — | Nenhum falso alarme |

- **Efeito na taxa reportada:** 139 de 141 (98,6%) nas três empresas. A taxa
  real após a revisão manual é 141 de 141.
- **Ironia do caso BBAS3:** a frase marcada tem de fato um erro, na causalidade
  (B2), mas a auditoria a marcou pelo motivo errado.

### Cobertura conceitual

| Empresa | Cobertura | Moedas que ficaram na regra 1.0 |
|---|---|---|
| WEGE3 | 91,7% (22/24) | 2: lucro com o sujeito longe do número; valor dentro de "(ou −R$ 2,97 bi considerando os arrendamentos)" |
| BBAS3 | 81,0% (17/21) | 4: ponto de "S.A." lido como fim de frase; "Despesas de Intermediação" fora do léxico (duas vezes); conceito só dentro de parêntese |
| ZAMP3 | 100% (26/26) | — |

### O que permanece fora do escopo

A auditoria 2.0 detecta:

- valor inexistente na fonte;
- sinal trocado;
- direção do verbo trocada;
- valor atribuído ao conceito errado, em moedas com conceito identificável.

Ela **não** valida:

- **causalidade econômica** (B1, B2, Z1);
- **completude** da explicação (Z2, Z3);
- **qualidade da interpretação e juízos de valor** (W1, W2, B4);
- afirmações sem número;
- conceito de percentuais e razões;
- **período** (valor anterior citado como atual) e **base contábil** (valor
  individual citado como consolidado). Essas duas limitações estão fixadas em
  testes.

A ZAMP3 final ilustra o ponto: **100% de conformidade, 100% de cobertura
conceitual, e ainda assim uma atribuição causal errada no RESUMO.** Uma taxa
de 100% mostra que os números citados procedem da fonte e estão associados aos
conceitos certos. Ela não prova que a narrativa esteja integralmente correta.

## 6. Evolução do sistema

O ciclo seguido para cada achado:

> validação manual → identificação do erro → diagnóstico da causa → correção
> estrutural → testes de regressão → nova execução → revalidação manual

| Commit | Correção | Mecanismo | Abrangência registrada no projeto |
|---|---|---|---|
| `53ce987` | Aplicações financeiras pela hierarquia | Regra pela posição da conta no plano (`CD_CONTA`), igual para toda empresa; documentos sem código mantêm a regra antiga | 13 das 400 empresas não financeiras têm "Aplicações Financeiras" em 1.01.01.xx (`NOTAS_DESENVOLVIMENTO.md`) |
| `873e013` | Base contábil única na recuperação | Mesma regra de base de `calcular_metricas()` | Antes, 59 de 412 empresas consolidadas recebiam a DRE individual no canal narrativo (`recuperacao.py`) |
| `cea3018` | Canal narrativo só com o cabeçalho; `demonstracoes_resumidas` | Estrutural: nenhuma tabela entra no ctx_nar de documento estruturado; resumo por nível de conta | Antes, a DFC era a tabela entregue em 389 de 412 empresas consolidadas (`recuperacao.py`) |
| `0b05768` | Regras do Prompt 2 | Regras gerais: resultado financeiro, `nao_disponivel`, `interpretacao_variacao`, fontes e contas | — |
| `6096ce4` | Captação no mercado aberto | Nome normalizado, cobrindo as três grafias da CVM | 9 dos 10 bancos com a conta passam a ter o valor (mensagem do commit) |
| `cb73bf6` | Detecção de banco só pela receita de intermediação | Critério do plano de contas, sem lista de empresas | 627 das 629 companhias com métricas idênticas; só CSU Digital e Rodobens mudam (`NOTAS_DESENVOLVIMENTO.md`) |
| `27dfdd5` | Auditoria 2.0 (conceito + valor) | Léxico fechado, determinístico, desligável | Nas 6 narrativas de validação só o erro real muda; na variante do teste de falso positivo com rótulo, o CONFERE indevido cai de 27,8% para 0% (`NOTAS_DESENVOLVIMENTO.md`) |
| `e4d96e1` | `.gitattributes` para fixtures e artefatos | Integridade dos artefatos em qualquer checkout | — |

Nenhuma correção é exceção para WEGE3, BBAS3 ou ZAMP3. Todas atuam por regra
geral (hierarquia de contas, base principal, grafias da CVM, plano de contas,
léxico de conceitos). São cobertas por testes sintéticos independentes das
empresas e por regressão sobre os documentos reais, e foram medidas no conjunto
de companhias do ITR de 30/06/2026 quando aplicável.

## 7. Conclusão

1. **Os problemas originais foram resolvidos?** Sim, os quatro achados da
   validação inicial:
   - a dupla contagem da liquidez;
   - a mistura de base;
   - a captação não identificada e seu efeito nas limitações;
   - a linha da DFC tratada como resultado financeiro.

   Todos têm correção estrutural e evidência na execução final. A troca
   EBIT × EBITDA está **parcialmente** resolvida: a auditoria passou a
   detectá-la, mas nada impede o LLM de repeti-la. Não se repetiu aqui.
2. **Os valores das narrativas finais são confiáveis dentro desta amostra?**
   Sim. Os 141 números citados conferem com a fonte e com as métricas após
   revisão manual, e nenhum valor está associado à conta errada. As métricas
   determinísticas usadas (liquidez, dívida, captação, depósitos, composição
   da DRE e da DFC) estão corretas nas três empresas.
3. **Ainda existem erros relevantes?** Sim. Dois graves na BBAS3 (B1, B2) e um
   relevante na ZAMP3 (Z1), mais ressalvas qualitativas nas três.
4. **Qual a natureza desses erros?** Interpretação e causalidade produzidas
   pelo LLM sobre números corretos:
   - a causa da variação do lucro atribuída a itens que não a explicam
     (despesas que não pioraram o resultado, fluxo de caixa);
   - o efeito de um IR/CS positivo lido ao contrário;
   - fluxos da DFC com juízos de valor ("melhora").

   Não são erros de cálculo, de extração, de recuperação nem de associação
   conta × valor. A auditoria não os detecta por construção.
5. **O sistema pode avançar para uma amostra maior?** Sim, na dimensão factual
   e numérica. Os erros estruturais que motivaram esta rodada foram corrigidos
   e testados. Com uma condição: a avaliação na amostra maior não pode se
   apoiar só na taxa de conformidade. Precisa de um critério explícito de
   revisão da interpretação e da causalidade, porque esse é o tipo de erro que
   persiste. Os falsos DIVERGENTES conhecidos do auditor (rótulo entre
   parênteses; nome composto de conta) devem ser reportados como tal.
6. **O que fica como limitação ou próxima etapa?**
   - Erros de causalidade e interpretação do LLM (B1, B2, Z1, W1), sem
     verificação automática.
   - Auditoria:
     - os dois padrões de falso alarme;
     - cobertura conceitual abaixo de 100% (81% a 100% nesta amostra);
     - sem verificação conceitual de percentuais, período e base contábil;
     - sem avaliação de causalidade ou completude.
   - Reprodutibilidade do LLM: foi uma execução por empresa. Comportamentos
     como Basileia nas limitações, a troca EBIT × EBITDA e a "melhora" do
     financiamento variaram entre execuções com o mesmo contexto; ausência
     numa execução não prova ausência sistemática.
   - Pendências já registradas em `NOTAS_DESENVOLVIMENTO.md`:
     - fragilidades de `_somar_arrendamentos`, `_somar_depreciacao_amortizacao`
       e `_emprestimos_por_bloco`;
     - Rodobens (conglomerado com braço financeiro);
     - nomenclatura de depósitos de Inter e BMG;
     - ausência de `captacao_anterior` nas métricas.
   - Amostra de três empresas: as conclusões valem para ela e para as medições
     estruturais registradas no conjunto de 629 companhias, não para a
     qualidade narrativa em geral.

## 8. Integridade dos artefatos

**Antes da criação deste relatório:**

- HEAD `e4d96e1`;
- `git diff HEAD` vazio: nenhum arquivo versionado alterado;
- `git status`: só as três pastas `_final`, untracked.

**Hashes SHA-256 (prefixo de 12 caracteres) das três pastas `_final`,** iguais
aos registrados logo após cada execução:

| Arquivo | WEGE3 | BBAS3 | ZAMP3 |
|---|---|---|---|
| fonte `.txt` | `500d0c0d51df` | `96c321232278` | `044d8ad11f53` |
| fonte `.txt.sha256` | `7b8aa7f3a21a` | `269deb61d5d9` | `7a5a05768925` |
| `auditoria.json` | `8312d43218d8` | `3d474162855d` | `525aad3493ea` |
| `execucao.json` | `9f5d6b1a56ea` | `f7fabcbf07da` | `f889281f8ab2` |
| `narrativa.md` | `d003e2c179da` | `211692255729` | `e83a03567f52` |
| `resultado_analisar.json` | `d989a077af03` | `a61c5a7f2b02` | `febfeecd29f9` |

**Depois da criação deste relatório:** mesmos HEAD e `git diff`; os 18 hashes
continuam idênticos. A única mudança no `git status` é este arquivo, untracked.
Nenhum commit foi feito.
