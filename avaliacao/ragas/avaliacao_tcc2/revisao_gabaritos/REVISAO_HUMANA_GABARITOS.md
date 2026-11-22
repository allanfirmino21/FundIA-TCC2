# Revisão humana dos 96 gabaritos (Protocolo, Seção 13, item 8)

**Período da revisão:** 2026-10-06 a 2026-10-08.
**Responsável pelas decisões:** o autor.
**Apoio:** Claude Code (modelo de linguagem) organizou as evidências e executou a conferência mecânica.
**Objeto:** os 96 gabaritos do dataset congelado `avaliacao/ragas/dataset_tcc2.json`
(SHA-256 `313bdf359fdeabb063ceec3bcca12ebfe3b52caae346b3ff1d9f3dc23196bc5e`).

Este diretório preserva o registro da revisão. Nada aqui altera o dataset, o protocolo, o instrumento de
exatidão ou qualquer resultado congelado. A revisão não corrigiu nenhum gabarito e não mudou nenhuma
classificação de disponibilidade.

## 1. Resultado

| Situação | Casos |
|---|---:|
| Confirmados | **96** (2 com o rótulo "com ressalva": IRBR3_N2 e POMO4_E1) |
| Corrigidos | **0** |
| Pendentes | **0** |

| Etapa | Casos | Datas |
|---|---:|---|
| Atenção humana, blocos 1–4 | 16 | 2026-10-06 (8) e 2026-10-08 (8) |
| Atenção humana, bloco 5 (AURE3_N2, AURE3_N3) | 2 | 2026-10-08 |
| G1 (N1, 3.01) | 11 | 2026-10-08 |
| G2a (N2, 3.11) e G2b (N2, plano próprio) | 6 + 2 | 2026-10-08 |
| G3 (N3, variação) | 10 | 2026-10-08 |
| G4 (N4, cadeia; três partes) | 9 | 2026-10-08 |
| G5a (N5, 1.01.01) e G5b (N5 bancos, 1.01) | 10 + 2 | 2026-10-08 |
| G6 (E1 margem líquida) | 7 | 2026-10-08 |
| G7 (E1 bancos e holding) | 3 | 2026-10-08 |
| G8 (E2 caixa × dívida) | 7 | 2026-10-08 |
| G9 (E2 depósitos, bancos) | 2 | 2026-10-08 |
| G10 (E3 resultado financeiro) | 8 | 2026-10-08 |
| POMO4_E1 (revisão individual) | 1 | 2026-10-08 |
| **Total** | **96** | |

A tabela completa das 96 decisões finais está na Seção 7. O registro cronológico integral, com as
decisões provisórias substituídas e a evidência de cada caso, está em `decisoes_revisao_humana.md`.

## 2. Natureza de cada etapa: revisão humana, conferência mecânica e apoio de modelo

As três atividades abaixo são distintas e não se substituem.

1. **Revisão humana (decisões do autor).**
   - Cada uma das 96 decisões foi comunicada explicitamente pelo autor.
   - Cada decisão foi registrada por id, com data e justificativa, só depois dessa confirmação.
   - As opções foram apresentadas de forma neutra: CONFIRMAR, CONFIRMAR exceto, CORRIGIR e PENDENTE.
   - As justificativas da tabela são as do autor; nos grupos, a mesma justificativa vale para cada caso do grupo.
   - Decisões provisórias foram mantidas como histórico e não contam como finais. É o caso de AURE3_N2 e AURE3_N3,
     inicialmente PENDENTE para verificação documental.
2. **Conferência mecânica (Etapa 0).**
   - Script determinístico, sem LLM: `etapa0_preconferencia.py`, executado em 2026-10-08.
   - Recalculou nos 96 casos, contra o pacote oficial da CVM e o contexto congelado:
     - versões do documento;
     - linhas-fonte e valores;
     - períodos acumulados;
     - derivados;
     - sinal exigido;
     - texto do gabarito;
     - disponibilidade.
   - Resultado em `etapa0_resultado.json`:

     | Casos | Problemas | Avisos |
     |---|---:|---:|
     | 78 casos de grupo | 0 | 7 |
     | 18 casos de atenção humana | 0 | 1 |

   - Controle negativo: 5 defeitos plantados numa cópia temporária do dataset, 5 detectados
     (`controle_negativo_etapa0.md`).
   - A Etapa 0 **não é** revisão humana. Ela serviu para agrupar os casos e indicar os que exigiam atenção.
3. **Evidências organizadas com apoio de modelo.** O Claude Code fez o seguinte:
   - selecionou as contas;
   - extraiu as linhas do CSV oficial e do contexto congelado;
   - calculou reconciliações;
   - propôs o agrupamento dos 78 casos;
   - redigiu as apresentações de cada grupo com "particularidades e riscos";
   - registrou na tabela temporária o texto das decisões ditadas pelo autor.

   Os scripts preservados aqui (Seção 6) cobrem a Etapa 0 e as evidências de G8, G9, G10 e POMO4_E1.
   As evidências dos blocos 1–5 e dos grupos G1–G7 vieram de duas fontes:
   - o próprio `etapa0_resultado.json`, que traz as linhas-fonte oficiais e o diagnóstico de
     disponibilidade de cada caso;
   - comandos de leitura pontuais, só de leitura, que não foram salvos como arquivos.

   Esses comandos não foram reconstruídos.

### 2.1 Risco de ancoragem e limites de independência

- O autor decidiu sobre evidências **selecionadas e enquadradas pelo modelo**: as contas mostradas,
  os riscos destacados e as ressalvas sugeridas. Mesmo com opções neutras, a revisão pode ter sido ancorada
  nessa apresentação. Esse risco não é eliminado pela revisão integral, apenas declarado.
- O dataset foi construído e revisado tecnicamente antes da coleta com apoio do mesmo tipo de ferramenta
  (Claude Code). O resultado de 96 confirmações e 0 correções pode refletir tanto a qualidade do dataset
  quanto a **não independência** entre quem preparou os gabaritos e quem organizou as evidências da revisão.
- **Atenuantes:**
  - o pacote oficial da CVM é uma fonte externa ao pipeline avaliado e ao processo de construção do dataset
    (SHA-256 diferente do pacote usado na construção);
  - os valores e derivados foram recalculados mecanicamente;
  - o controle negativo mostrou que a conferência detecta erros plantados de cinco tipos.
- Continua sendo avaliação de **avaliador único**, sem segundo revisor humano e sem medida de concordância.

### 2.2 Momento da revisão

O protocolo (Seção 13, item 8) previa a revisão manual de 100% dos gabaritos **antes da execução do RAGAS
e antes da primeira resposta**. A revisão humana foi feita depois:
- da coleta;
- do RAGAS;
- da exatidão;
- da anotação de comportamento.

O que antecedeu a coleta foi a revisão técnica feita pelo Claude Code (`revisao_tecnica` no dataset), que
o próprio dataset declara não substituir a revisão humana.

Consequências:
- Nenhum gabarito nem disponibilidade mudou, então os resultados congelados não são afetados.
- Durante a revisão, os resultados RAGAS não foram consultados nem usados como critério.
- Não houve cegamento: o autor e o modelo já conheciam os resultados de exatidão e do RAGAS, analisados
  antes nesta mesma etapa do trabalho.

O registro formal deste desvio de momento no protocolo **ainda não foi feito**. Ele é um passo posterior
e depende de autorização própria.

## 3. Fontes e hierarquia de evidência

- **Primária:** as linhas CVM registradas no dataset congelado (`fontes_gabarito`: `CD_CONTA`,
  `DS_CONTA`, valor, período, versão).
- **Corroborativas:**
  - o contexto congelado da coleta, lido pelo executor `avaliar_respostas_tcc2.py`;
  - as cópias versionadas de ITR no repositório (BBAS3, ZAMP3, WEGE3, e LWSA3 em `tests/fixtures`),
    usadas nos blocos 1–2;
  - o pacote oficial da CVM descrito abaixo, a partir do bloco 5.
- Não se declarou equivalência documental entre arquivos com SHA-256 diferente. As cópias locais em
  `dados/cache` de VALE3 e ITSA4 diferem dos documentos congelados e foram tratadas só como corroborativas.
- Nos casos da IRBR3 não houve conferência contra uma cópia integral independente do ITR.

### 3.1 Pacote oficial da CVM (não incluído no repositório)

| Campo | Valor |
|---|---|
| URL | https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_2026.zip |
| Download | 2026-10-08 (resposta HTTP de 2026-10-08 23:23:09 GMT), autorizado pelo autor |
| Last-Modified | 2026-10-04 10:45:31 GMT |
| Tamanho | 19.634.453 bytes |
| ETag | `"6ac22e4b-12b9915"` |
| SHA-256 | `0e1ef74291d2143e7bb55247b01c8bbd94995d995536f70f0d19de1d79d7e38c` |

- Os arquivos usados foram `itr_cia_aberta_2026.csv` (índice), `itr_cia_aberta_{DRE,BPA,BPP,DFC_MI}_con_2026.csv`.
- A leitura usou latin-1 e separador `;`.
- O SHA-256 difere do pacote usado na construção do dataset (`4f89a998…`), então não se declara identidade
  entre os dois.
- Em todas as contas conferidas, os valores coincidiram com o dataset.
- As versões do índice são iguais às do dataset nas 12 empresas:

  | Empresas | Versão |
  |---|---|
  | VALE3 | v3 |
  | ITSA4 | v2 |
  | IRBR3 | v2 |
  | as demais | v1 |

- Para reexecutar os scripts, o ZIP deve ser obtido na URL acima e conferido pelo SHA-256.
  A CVM pode republicar o arquivo, e um pacote com outro hash não é o mesmo pacote.

## 4. POMO4_E1: confirmado com ressalva (revisão individual)

| Item | Conteúdo |
|---|---|
| Gabarito | margem líquida consolidada do 1S26 de **13,30%** = 535.824 / 4.028.514 × 100 (R$ mil; 3.11 / 3.01) |
| Disponibilidade | **`parcial`** (1 de 2 insumos) |

**Justificativa do autor:**
- O numerador corresponde ao resultado consolidado total da DRE (3.11). Ele está na DFC consolidada como
  "Resultado do período" (535.824 mil), com o mesmo conceito, período, base e sinal.
- A receita de vendas (3.01), necessária como denominador, está ausente do contexto.
- A regra 4 da Seção 9 admite `parcial` quando só parte dos insumos está presente.
- O próprio protocolo congelado pré-registrou `parcial` para POMO4_E1 ("o resultado está no contexto, a
  receita não").

**Ressalva:**
- A regra 2 da Seção 9 autoriza expressamente a DFC para N2/N3, mas não esclarece se vale para insumos de
  indicadores derivados.
- A regra 4 não exige que os insumos estejam na DRE.
- Registra-se essa ambiguidade de redação e a leitura adotada, sem alterar o protocolo retroativamente.

Os avisos da Etapa 0 para este caso refletem uma implementação mais restritiva da regra 2 (via DFC aceita só
em N2/N3) e não são, isoladamente, evidência de erro no gabarito.

## 5. Ressalvas metodológicas

1. **Procedimento e evidência.**
   - Evidência primária: `fontes_gabarito`.
   - Evidência corroborativa: o pacote oficial CVM (SHA-256 `0e1ef742…`) e o contexto congelado.
   - Não há equivalência documental entre arquivos com hashes diferentes.
   - Não houve conferência contra uma cópia integral independente do ITR da IRBR3.
   - A Etapa 0 é conferência mecânica, não revisão humana.
   - A organização das evidências teve apoio de modelo, com risco de ancoragem (Seção 2.1).
2. **N4.** A confirmação se refere à consistência contábil da decomposição (os componentes reconciliam a
   variação do resultado), sem atribuir causalidade econômica além do que a DRE demonstra.
   No ITUB4_N4, os subcomponentes da 3.04 se compensam.
3. **Comparabilidade entre bancos.**
   - BBAS3 e ITUB4 não são comparáveis em composição na 3.01 (N1), na 3.03 (E1) e na 3.02 (E3).
     A provisão para perda de crédito, as tarifas e os seguros são classificados em lugares diferentes.
   - Nos depósitos (E2), os códigos diferem (2.02.01 e 2.03.01). Os dois são depósitos a custo amortizado,
     e a falta de subcontas no CSV impede verificar se a composição é homogênea.
   - A 3.01 da IRBR3 segue o plano próprio das resseguradoras.
4. **E2 caixa × dívida (não financeiras e holding).**
   - A definição é estritamente caixa (1.01.01) contra empréstimos e financiamentos (2.01.04 + 2.02.01).
   - A inclusão de arrendamentos, debêntures e CRI depende da classificação de cada empresa: por exemplo,
     arrendamentos ficam dentro em AURE3, LAVV3 e LWSA3 e fora em WEGE3, ZAMP3, CEAB3, POMO4 e ITSA4.
   - Por isso o indicador não é diretamente comparável quanto à composição econômica da dívida.
   - Fluxos da DFC não substituem saldos do BPP.
   - A conclusão caixa × dívida de cada caso não muda sob os critérios alternativos testados.
5. **Caixa e datas.**
   - O caixa é a conta 1.01.01, sem as aplicações financeiras (1.01.02); nos bancos é a conta 1.01.
   - O comparativo do balanço é 31/12/2025; o da DRE e da DFC é o 1S25 (saldo final da DFC em 30/06/2025).
6. **Resultado consolidado total.** O resultado é o consolidado total, não a parcela da controladora:
   - 3.11 na maioria;
   - 3.13 na IRBR3;
   - 3.09 no ITUB4.

   Em POMO4, a linha "Resultado do período" da DFC é igual a 3.11, e não a 3.11.01.
7. **Subcontas zeradas que não reconciliam o total** (IRBR3_N2, ZAMP3_E2, AURE3_E2): prevalece o total
   oficial do grupo.
8. **Sinais.**
   - O sinal positivo atípico de "Despesas Financeiras" na IRBR3 (E2) foi registrado, sem esclarecimento
     da sua natureza.
   - Valores negativos foram preservados, por exemplo a margem de ZAMP3 (−5,69%) e de AURE3 (−16,00%).
   - Inversões de sinal entre períodos foram preservadas (LWSA3_E3, ITSA4_E3).
9. **Dupla contagem.** Rótulos repetidos entre grupo e subconta no contexto podem induzir dupla contagem
   (WEGE3_N5, LAVV3_N5, LAVV3_E2, AURE3_E2, POMO4_E2, CEAB3_E3). O gabarito usa sempre o total do grupo.
10. **E3 resultado financeiro.**
    - O valor é o da conta 3.06 da DRE consolidada, com sinal, nos dois semestres.
    - Ajustes não caixa e juros pagos na DFC não equivalem à 3.06.
    - VALE3_E3 é `parcial` pela linha da DFC com sinal invertido.
    - LWSA3, POMO4 e AURE3 são `ausente`, porque o contexto não tem nenhuma linha de resultado financeiro.
11. **Disponibilidade via DFC.**
    - A regra 2 sustenta POMO4_N2 e POMO4_N3 (`presente`).
    - Em POMO4_E1 há ambiguidade de redação entre as regras 2 e 4, e a leitura adotada está na Seção 4.
    - O protocolo não foi alterado retroativamente.
12. **Versões dos documentos.** VALE3 v3, ITSA4 v2, IRBR3 v2 e as demais v1, todas iguais à versão mais
    recente do índice da CVM consultado.
13. **Observações sem efeito no gabarito.**
    - A grafia "R$ 1,13 trilhões" (ITUB4_E2) seria "trilhão" pela norma. A exatidão lê o número, e o gabarito
      congelado não é alterado.
    - Os avisos da Etapa 0 foram examinados e atribuídos a três causas:
      - o caixa exigido reaparece como "Saldo Final de Caixa e Equivalentes" da DFC (WEGE3_E2, ZAMP3_E2,
        LAVV3_E2, CEAB3_E2, ITSA4_E2);
      - o uso da regra 2 foi sinalizado em POMO4_N2 e POMO4_N3;
      - em POMO4_E1, a implementação restritiva da regra 2 gerou o aviso (Seção 4).

## 6. Arquivos deste diretório

| Arquivo | Natureza | SHA-256 |
|---|---|---|
| `REVISAO_HUMANA_GABARITOS.md` | este documento | — |
| `decisoes_revisao_humana.md` | registro cronológico de trabalho, transcrito sem alteração da pasta temporária, com decisões provisórias e evidência por caso | `f095f3ca0ef3da830210e9ccdc71e9242393dabdfaba61ea2b6d77a122f1791b` |
| `etapa0_resultado.json` | saída da Etapa 0 (96 casos: problemas, avisos e evidência; versões; SHA-256 do pacote) | `28a3f39faf0c8b4e588b4951380216d8f2883309c0437ff3aef1a78d99061bc1` |
| `etapa0_preconferencia.py` | script da Etapa 0, como executado | `dc77bef9dd7d235d2493459865adc3277b924dd862e2ac349e92287a87f91825` |
| `etapa0_controle.py` | variante do script usada no controle negativo (difere só na leitura de `DS_PATH` e `OUT_NAME`) | `9bd1c184ec28c9d0b235a6e0e0ee75d3aaa4caaeabb7bdd73d59db07743c9687` |
| `controle_negativo_etapa0.md` | registro do controle negativo (comando e saída), transcrito do log da sessão | `1d2268e03be741f92774843a70c924b603dde5443a9107a57644c740004de51b` |
| `g8_evidencias.py` / `g8_evidencias.txt` | evidências do G8 (E2 caixa × dívida) e saída | `38f86c8a915585984dc2b1504cd42055a7f933e36c9f2b537035426a80e6b0f9` / `c42ad94ef94603b9501f27e944e531439978585bb1e6aef233354917b6bceccf` |
| `g9_evidencias.py` / `g9_evidencias.txt` | evidências do G9 (E2 depósitos) e saída | `ef3bde28ea0b0ff8fcb066ed67c7b0845d890399ec986f21f5114b636e0a437a` / `bb5ab069cce9ff3f253addb9401dea98f8e8e4cef3b16e98022be06dd76acc7a` |
| `g10_evidencias.py` / `g10_evidencias.txt` | evidências do G10 (E3) e saída | `295cdf291db9425210a902c54677498e6c3cd1a4cba10a1dbbf2f21884c1c2ba` / `d960df263e8e0a7324c28a9f7a0c0a41ad91514734c25ccd3079ac50fb3dbc2e` |
| `pomo4_e1_evidencias.py` / `pomo4_e1_evidencias.txt` | evidências do POMO4_E1 e saída | `3dcc595cd8f7fcafb314ca9074d8f6eaee5fdcfb5f07722ffb12fa3ae1a25362` / `0ff252110eb280501e6b0400efdd27d67f94d2a00fd7946ee8fdd14feba2ab4a` |
| `integridade_registro.py` | conferência do registro usada ao fim da revisão | `e0ee4cebc0291a8173187d4f0ed454fa46f3f0895835784d82a08eddd61e4afb` |
| `tabela_decisoes_finais.py` | **criado na preservação** (não usado na revisão): gera e confere a tabela da Seção 7 a partir do registro | `ba56eff316114d74d7ac6300fa5b6440b99522d77facf48cc3b7eed55a1f99e5` |

**Notas de reprodutibilidade:**
- Os scripts usados na revisão estão **como foram executados**, inclusive com caminhos absolutos da máquina
  do autor.
- Eles exigem o ZIP em `cvm/itr_cia_aberta_2026.zip`, ao lado do script, e conferem o SHA-256 do pacote.
- Eles também exigem a árvore Git limpa.
- Eles gravam a saída no próprio diretório. Para reexecutá-los, copie-os para uma pasta temporária,
  com o ZIP em `cvm/`.
- A saída do comando pontual que leu os campos do dataset para o G9 não foi preservada.
- Na saída de console reproduzida em `controle_negativo_etapa0.md`, os acentos foram corrigidos.

## 7. As 96 decisões finais

A tabela está na ordem do dataset e foi gerada mecanicamente a partir de `decisoes_revisao_humana.md`
por `tabela_decisoes_finais.py --markdown`. A conferência `tabela_decisoes_finais.py --verificar`
compara este bloco com o registro.
- Nos casos decididos em grupo, a justificativa do grupo se repete em cada caso, com as ressalvas próprias
  do caso quando houver.
- A evidência específica de cada caso está no registro cronológico.

<!-- INICIO_TABELA_DECISOES_FINAIS -->
| nº | id | etapa | decisão humana final | data | justificativa (do autor) |
|---:|---|---|---|---|---|
| 1 | WEGE3_N1 | G1 | CONFIRMAR gabarito atual (grupo G1) | 2026-10-08 | Os valores dos 11 gabaritos correspondem à conta 3.01 da DRE consolidada de cada empresa, no acumulado de 01/01 a 30/06/2026, e foram confirmados no CSV oficial da CVM. As classificações de disponibilidade também estão coerentes com os contextos congelados. |
| 2 | WEGE3_N2 | G2a | CONFIRMAR gabarito atual (grupo G2a) | 2026-10-08 | Os seis gabaritos correspondem à conta 3.11 da DRE consolidada, acumulada de 01/01 a 30/06/2026, e coincidem com os valores do CSV oficial da CVM. Em todos os casos, a soma das parcelas atribuídas aos controladores e não controladores reconcilia o resultado consolidado total. |
| 3 | WEGE3_N3 | G3 | CONFIRMAR gabarito atual (grupo G3) | 2026-10-08 | Os dez gabaritos apresentam corretamente os resultados líquidos consolidados de 1S26 e 1S25, com os sinais exigidos, e as variações percentuais calculadas conforme o protocolo. Os valores coincidem com as respectivas contas da DRE consolidada no CSV oficial da CVM, e as direções de aumento ou redução estão corretas. |
| 4 | WEGE3_N4 | G4 | CONFIRMAR gabarito atual (grupo G4) | 2026-10-08 | A variação de −103.597 mil reconcilia com os componentes −159.934, +38.113 e +18.224 mil, corretamente ordenados por magnitude. Disponibilidade `presente` mantida. |
| 5 | WEGE3_N5 | G5a | CONFIRMAR gabarito atual (grupo G5a) | 2026-10-08 | Os dez gabaritos correspondem à conta 1.01.01 do BPA consolidado em 30/06/2026, coincidem com o CSV oficial da CVM e são corroborados pelos saldos finais de caixa da DFC. Todos possuem disponibilidade `presente`. Ressalva: preservar 7.750.256 mil; a subconta 1.01.01.02 (5.477.045 mil) já integra esse valor, não somá-la novamente; a conta 1.01.02 (1.050.886 mil) não integra o gabarito. Ressalva geral: manter a distinção entre caixa e equivalentes (1.01.01) e aplicações financeiras classificadas separadamente (1.01.02); não confundir a data comparativa do BPA (31/12/2025) com a da DFC (30/06/2025). |
| 6 | WEGE3_E1 | G6 | CONFIRMAR gabarito atual (grupo G6) | 2026-10-08 | Os sete gabaritos calculam corretamente a margem líquida do 1S26 pela fórmula resultado líquido consolidado total (3.11) dividido pela receita de venda de bens e/ou serviços (3.01), multiplicado por 100. Os insumos coincidem com o CSV oficial da CVM, e os percentuais estão corretamente arredondados a duas casas decimais. Ressalva: utilizar o resultado consolidado total, não apenas a parcela da controladora. Disponibilidade `presente` mantida. |
| 7 | WEGE3_E2 | G8 | CONFIRMAR gabarito atual (grupo G8) | 2026-10-08 | Caixa 7.750.256 mil versus dívida 5.066.346 mil. Manter `parcial`. Não incluir aplicações financeiras 1.01.02 nem arrendamentos classificados fora das contas de dívida definidas. |
| 8 | WEGE3_E3 | G10 | CONFIRMAR gabarito atual (grupo G10) | 2026-10-08 | Resultado financeiro de +65.819 mil no 1S26 e +47.595 mil no 1S25. Manter `presente`. Não confundir ajustes de juros da DFC com o resultado financeiro total da DRE. |
| 9 | BBAS3_N1 | G1 | CONFIRMAR gabarito atual (grupo G1) | 2026-10-08 | Os valores dos 11 gabaritos correspondem à conta 3.01 da DRE consolidada de cada empresa, no acumulado de 01/01 a 30/06/2026, e foram confirmados no CSV oficial da CVM. As classificações de disponibilidade também estão coerentes com os contextos congelados. Ressalva: correto segundo o plano de contas do banco; a 3.01 do BBAS3 corresponde à receita de juros (3.01.01). Limitação de comparabilidade com ITUB4_N1; gabarito não alterado. |
| 10 | BBAS3_N2 | atenção humana, blocos 1–4 | CONFIRMAR gabarito atual | 2026-10-06 | A conta 3.11 representa o resultado consolidado total e 3.11.01 + 3.11.02 = 6.362.961, distinguindo corretamente o total da parcela atribuída aos controladores. |
| 11 | BBAS3_N3 | G3 | CONFIRMAR gabarito atual (grupo G3) | 2026-10-08 | Os dez gabaritos apresentam corretamente os resultados líquidos consolidados de 1S26 e 1S25, com os sinais exigidos, e as variações percentuais calculadas conforme o protocolo. Os valores coincidem com as respectivas contas da DRE consolidada no CSV oficial da CVM, e as direções de aumento ou redução estão corretas. Ressalva: preservar o código do plano bancário. |
| 12 | BBAS3_N4 | atenção humana, blocos 1–4 | CONFIRMAR gabarito atual | 2026-10-06 | Os componentes selecionados reconciliam exatamente a variação do resultado consolidado; o IR/CS positivo e a posição da provisão dentro de 3.04 estão coerentes com a estrutura apresentada. |
| 13 | BBAS3_N5 | G5b | CONFIRMAR gabarito atual (grupo G5b) | 2026-10-08 | O valor de 65.017.849 mil corresponde à conta 1.01 do BPA consolidado em 30/06/2026 e coincide com o CSV oficial da CVM. As subcontas Caixa (27.063.120) e Aplicações de Liquidez (37.954.729) já compõem esse total. Os depósitos compulsórios classificados em 1.02 não integram o gabarito. Disponibilidade `presente` mantida. |
| 14 | BBAS3_E1 | G7 | CONFIRMAR gabarito atual (grupo G7) | 2026-10-08 | Resultado bruto da intermediação financeira de 49.463.309 mil, conta 3.03, reconciliado por 160.747.114 − 111.283.805. Manter disponibilidade `presente`. As perdas de crédito classificadas em 3.04 não estão descontadas desse resultado. |
| 15 | BBAS3_E2 | G9 | CONFIRMAR gabarito atual (grupo G9) | 2026-10-08 | Saldo de depósitos de 954.018.837 mil em 30/06/2026, conta 2.02.01 do BPP consolidado, coincidente com o CSV oficial e com o contexto. Manter disponibilidade `presente`. Não incluir depósitos compulsórios, aplicações interfinanceiras ou outras captações. |
| 16 | BBAS3_E3 | atenção humana, blocos 1–4 | CONFIRMAR gabarito atual | 2026-10-06 | A conta 3.02 corresponde às despesas de intermediação financeira e a reconciliação com 3.01 e 3.03 fecha; 3.04.01 está fora desse agregado. |
| 17 | ZAMP3_N1 | G1 | CONFIRMAR gabarito atual (grupo G1) | 2026-10-08 | Os valores dos 11 gabaritos correspondem à conta 3.01 da DRE consolidada de cada empresa, no acumulado de 01/01 a 30/06/2026, e foram confirmados no CSV oficial da CVM. As classificações de disponibilidade também estão coerentes com os contextos congelados. |
| 18 | ZAMP3_N2 | G2a | CONFIRMAR gabarito atual (grupo G2a) | 2026-10-08 | Os seis gabaritos correspondem à conta 3.11 da DRE consolidada, acumulada de 01/01 a 30/06/2026, e coincidem com os valores do CSV oficial da CVM. Em todos os casos, a soma das parcelas atribuídas aos controladores e não controladores reconcilia o resultado consolidado total. Ressalva: preservar o sinal negativo do prejuízo. |
| 19 | ZAMP3_N3 | atenção humana, blocos 1–4 | CONFIRMAR gabarito atual | 2026-10-06 | Os valores de 1S26 e 1S25 conferem com 3.11 e a variação sobre a magnitude resulta em 33,33%. |
| 20 | ZAMP3_N4 | G4 | CONFIRMAR gabarito atual (grupo G4) | 2026-10-08 | A variação de −38.668 mil reconcilia com −24.676, −18.217 e +4.225 mil. Preservar a mudança de sinal do IR/CS entre os semestres. Disponibilidade `presente` mantida. |
| 21 | ZAMP3_N5 | G5a | CONFIRMAR gabarito atual (grupo G5a) | 2026-10-08 | Os dez gabaritos correspondem à conta 1.01.01 do BPA consolidado em 30/06/2026, coincidem com o CSV oficial da CVM e são corroborados pelos saldos finais de caixa da DFC. Todos possuem disponibilidade `presente`. Ressalva geral: manter a distinção entre caixa e equivalentes (1.01.01) e aplicações financeiras classificadas separadamente (1.01.02); não confundir a data comparativa do BPA (31/12/2025) com a da DFC (30/06/2025). |
| 22 | ZAMP3_E1 | G6 | CONFIRMAR gabarito atual (grupo G6) | 2026-10-08 | Os sete gabaritos calculam corretamente a margem líquida do 1S26 pela fórmula resultado líquido consolidado total (3.11) dividido pela receita de venda de bens e/ou serviços (3.01), multiplicado por 100. Os insumos coincidem com o CSV oficial da CVM, e os percentuais estão corretamente arredondados a duas casas decimais. Ressalva: preservar a margem negativa de −5,69%. Disponibilidade `presente` mantida. |
| 23 | ZAMP3_E2 | G8 | CONFIRMAR gabarito atual (grupo G8) | 2026-10-08 | Caixa 135.651 mil versus dívida 1.545.074 mil. Manter `parcial`. Os totais oficiais prevalecem sobre subcontas zeradas que não os reconciliam. |
| 24 | ZAMP3_E3 | G10 | CONFIRMAR gabarito atual (grupo G10) | 2026-10-08 | Resultado financeiro de −169.280 mil no 1S26 e −144.604 mil no 1S25. Manter `presente`. Os ajustes de arrendamentos da DFC não substituem o 3.06. |
| 25 | LWSA3_N1 | G1 | CONFIRMAR gabarito atual (grupo G1) | 2026-10-08 | Os valores dos 11 gabaritos correspondem à conta 3.01 da DRE consolidada de cada empresa, no acumulado de 01/01 a 30/06/2026, e foram confirmados no CSV oficial da CVM. As classificações de disponibilidade também estão coerentes com os contextos congelados. |
| 26 | LWSA3_N2 | G2a | CONFIRMAR gabarito atual (grupo G2a) | 2026-10-08 | Os seis gabaritos correspondem à conta 3.11 da DRE consolidada, acumulada de 01/01 a 30/06/2026, e coincidem com os valores do CSV oficial da CVM. Em todos os casos, a soma das parcelas atribuídas aos controladores e não controladores reconcilia o resultado consolidado total. Ressalva: manter disponibilidade `parcial`, pois o contexto não contém o resultado líquido consolidado; o resultado antes dos tributos é apenas um conceito relacionado. |
| 27 | LWSA3_N3 | G3 | CONFIRMAR gabarito atual (grupo G3) | 2026-10-08 | Os dez gabaritos apresentam corretamente os resultados líquidos consolidados de 1S26 e 1S25, com os sinais exigidos, e as variações percentuais calculadas conforme o protocolo. Os valores coincidem com as respectivas contas da DRE consolidada no CSV oficial da CVM, e as direções de aumento ou redução estão corretas. Ressalva: manter `parcial`, pois o contexto contém apenas conceitos relacionados, não o resultado líquido consolidado. |
| 28 | LWSA3_N4 | G4 | CONFIRMAR gabarito atual (grupo G4) | 2026-10-08 | A variação de +25.225 mil reconcilia com +22.840, +22.786 e −20.401 mil, na ordem correta. Disponibilidade `ausente` mantida, conforme a regra 5 da Seção 9, porque apenas um nó aparece no contexto fora da DRE. |
| 29 | LWSA3_N5 | G5a | CONFIRMAR gabarito atual (grupo G5a) | 2026-10-08 | Os dez gabaritos correspondem à conta 1.01.01 do BPA consolidado em 30/06/2026, coincidem com o CSV oficial da CVM e são corroborados pelos saldos finais de caixa da DFC. Todos possuem disponibilidade `presente`. Ressalva geral: manter a distinção entre caixa e equivalentes (1.01.01) e aplicações financeiras classificadas separadamente (1.01.02); não confundir a data comparativa do BPA (31/12/2025) com a da DFC (30/06/2025). |
| 30 | LWSA3_E1 | G6 | CONFIRMAR gabarito atual (grupo G6) | 2026-10-08 | Os sete gabaritos calculam corretamente a margem líquida do 1S26 pela fórmula resultado líquido consolidado total (3.11) dividido pela receita de venda de bens e/ou serviços (3.01), multiplicado por 100. Os insumos coincidem com o CSV oficial da CVM, e os percentuais estão corretamente arredondados a duas casas decimais. Ressalva: manter disponibilidade `ausente`, pois nenhum dos dois insumos necessários aparece no contexto. |
| 31 | LWSA3_E2 | atenção humana, blocos 1–4 | CONFIRMAR gabarito atual | 2026-10-06 | 2.01.04 + 2.02.01 = 71.915; os valores são integralmente passivos de arrendamento, mas estão classificados pela própria estrutura CVM dentro de Empréstimos e Financiamentos. Caixa de 314.495 é superior a 71.915. |
| 32 | LWSA3_E3 | G10 | CONFIRMAR gabarito atual (grupo G10) | 2026-10-08 | Resultado financeiro de +6.396 mil no 1S26 e −16.390 mil no 1S25. Manter `ausente`. Preservar a inversão de sinal; os ajustes financeiros da DFC não fornecem o indicador. |
| 33 | VALE3_N1 | G1 | CONFIRMAR gabarito atual (grupo G1) | 2026-10-08 | Os valores dos 11 gabaritos correspondem à conta 3.01 da DRE consolidada de cada empresa, no acumulado de 01/01 a 30/06/2026, e foram confirmados no CSV oficial da CVM. As classificações de disponibilidade também estão coerentes com os contextos congelados. |
| 34 | VALE3_N2 | atenção humana, blocos 1–4 | CONFIRMAR gabarito atual | 2026-10-06 | DRE consolidada 3.11 = 17.240.000 e a decomposição 16.800.000 + 440.000 reconcilia o total. O contexto recuperado não contém esse total, sustentando a disponibilidade `parcial`. |
| 35 | VALE3_N3 | G3 | CONFIRMAR gabarito atual (grupo G3) | 2026-10-08 | Os dez gabaritos apresentam corretamente os resultados líquidos consolidados de 1S26 e 1S25, com os sinais exigidos, e as variações percentuais calculadas conforme o protocolo. Os valores coincidem com as respectivas contas da DRE consolidada no CSV oficial da CVM, e as direções de aumento ou redução estão corretas. Ressalva: manter `parcial`; não confundir tributos da DFC com a despesa tributária da DRE. |
| 36 | VALE3_N4 | G4 | CONFIRMAR gabarito atual (grupo G4) | 2026-10-08 | A variação de −3.120.000 mil reconcilia com os componentes −4.423.000, +2.141.000 e −838.000 mil, corretamente ordenados. Disponibilidade `parcial` mantida, pois dois nós aparecem na DFC, incluindo o resultado financeiro com sinal invertido. Não confundir tributos da DFC com IR/CS da DRE. |
| 37 | VALE3_N5 | G5a | CONFIRMAR gabarito atual (grupo G5a) | 2026-10-08 | Os dez gabaritos correspondem à conta 1.01.01 do BPA consolidado em 30/06/2026, coincidem com o CSV oficial da CVM e são corroborados pelos saldos finais de caixa da DFC. Todos possuem disponibilidade `presente`. Ressalva geral: manter a distinção entre caixa e equivalentes (1.01.01) e aplicações financeiras classificadas separadamente (1.01.02); não confundir a data comparativa do BPA (31/12/2025) com a da DFC (30/06/2025). |
| 38 | VALE3_E1 | G6 | CONFIRMAR gabarito atual (grupo G6) | 2026-10-08 | Os sete gabaritos calculam corretamente a margem líquida do 1S26 pela fórmula resultado líquido consolidado total (3.11) dividido pela receita de venda de bens e/ou serviços (3.01), multiplicado por 100. Os insumos coincidem com o CSV oficial da CVM, e os percentuais estão corretamente arredondados a duas casas decimais. Ressalva: manter disponibilidade `ausente`, pois nenhum dos dois insumos necessários aparece no contexto. |
| 39 | VALE3_E2 | atenção humana, blocos 1–4 | CONFIRMAR gabarito atual | 2026-10-06 | Pela definição congelada, 2.01.04 + 2.02.01 = 98.034.000. Os arrendamentos pertencem a essas contas e as debêntures participativas estão fora delas. |
| 40 | VALE3_E3 | atenção humana, blocos 1–4 | CONFIRMAR gabarito atual | 2026-10-06 | A DRE 3.06 registra −2.237.000 em 1S26 e +2.186.000 em 1S25. A linha da DFC possui sinal oposto por sua função de reconciliação e não substitui o resultado financeiro da DRE. |
| 41 | ITUB4_N1 | G1 | CONFIRMAR gabarito atual (grupo G1) | 2026-10-08 | Os valores dos 11 gabaritos correspondem à conta 3.01 da DRE consolidada de cada empresa, no acumulado de 01/01 a 30/06/2026, e foram confirmados no CSV oficial da CVM. As classificações de disponibilidade também estão coerentes com os contextos congelados. Ressalva: correto segundo o plano de contas do banco; a 3.01 do ITUB4 inclui também tarifas bancárias (3.01.05), resultado de seguros (3.01.06), entre outros componentes. Limitação de comparabilidade com BBAS3_N1; gabarito não alterado. |
| 42 | ITUB4_N2 | G2b | CONFIRMAR gabarito atual (grupo G2b) | 2026-10-08 | O resultado líquido consolidado de 24.199.000 mil corresponde à conta 3.09 da DRE consolidada, confere com o CSV oficial da CVM e está presente no contexto congelado. A soma entre controladora e não controladores reconcilia o total. Disponibilidade `presente` mantida; gabarito original preservado. |
| 43 | ITUB4_N3 | G3 | CONFIRMAR gabarito atual (grupo G3) | 2026-10-08 | Os dez gabaritos apresentam corretamente os resultados líquidos consolidados de 1S26 e 1S25, com os sinais exigidos, e as variações percentuais calculadas conforme o protocolo. Os valores coincidem com as respectivas contas da DRE consolidada no CSV oficial da CVM, e as direções de aumento ou redução estão corretas. Ressalva: preservar o código do plano bancário (3.09). |
| 44 | ITUB4_N4 | G4 | CONFIRMAR gabarito atual (grupo G4) | 2026-10-08 | A variação de +2.094.000 mil reconcilia com +4.767.000, −2.345.000 e −328.000 mil, conforme a cadeia bancária. Disponibilidade `presente` mantida. Registrado: o agregado 3.04 contém subcomponentes com variações compensatórias (outras despesas administrativas −1.519.000; despesas tributárias −55.000; equivalência patrimonial +1.246.000), sem alterar o nível de agregação do gabarito. |
| 45 | ITUB4_N5 | G5b | CONFIRMAR gabarito atual (grupo G5b) | 2026-10-08 | O valor de 35.351.000 mil corresponde à conta 1.01 do BPA consolidado em 30/06/2026 e coincide com o CSV oficial da CVM. Os demais ativos financeiros classificados em 1.02 não integram o gabarito. Disponibilidade `presente` mantida. |
| 46 | ITUB4_E1 | G7 | CONFIRMAR gabarito atual (grupo G7) | 2026-10-08 | Resultado bruto da intermediação financeira de 71.756.000 mil, conta 3.03, reconciliado por 199.118.000 − 127.362.000. Manter disponibilidade `presente`. Sua composição inclui perdas de crédito em 3.02 e tarifas e seguros em 3.01. |
| 47 | ITUB4_E2 | G9 | CONFIRMAR gabarito atual (grupo G9) | 2026-10-08 | Saldo de depósitos de 1.134.485.000 mil em 30/06/2026, conta 2.03.01 do BPP consolidado, coincidente com o CSV oficial e com o contexto. Manter disponibilidade `presente`. Não incluir depósitos no Banco Central, aplicações interfinanceiras, seguros ou outras captações. |
| 48 | ITUB4_E3 | atenção humana, blocos 1–4 | CONFIRMAR gabarito atual | 2026-10-08 | A conta 3.02 corresponde a −127.362.000 e inclui as perdas esperadas de crédito na estrutura contábil do Itaú. |
| 49 | LAVV3_N1 | G1 | CONFIRMAR gabarito atual (grupo G1) | 2026-10-08 | Os valores dos 11 gabaritos correspondem à conta 3.01 da DRE consolidada de cada empresa, no acumulado de 01/01 a 30/06/2026, e foram confirmados no CSV oficial da CVM. As classificações de disponibilidade também estão coerentes com os contextos congelados. |
| 50 | LAVV3_N2 | G2a | CONFIRMAR gabarito atual (grupo G2a) | 2026-10-08 | Os seis gabaritos correspondem à conta 3.11 da DRE consolidada, acumulada de 01/01 a 30/06/2026, e coincidem com os valores do CSV oficial da CVM. Em todos os casos, a soma das parcelas atribuídas aos controladores e não controladores reconcilia o resultado consolidado total. |
| 51 | LAVV3_N3 | G3 | CONFIRMAR gabarito atual (grupo G3) | 2026-10-08 | Os dez gabaritos apresentam corretamente os resultados líquidos consolidados de 1S26 e 1S25, com os sinais exigidos, e as variações percentuais calculadas conforme o protocolo. Os valores coincidem com as respectivas contas da DRE consolidada no CSV oficial da CVM, e as direções de aumento ou redução estão corretas. |
| 52 | LAVV3_N4 | G4 | CONFIRMAR gabarito atual (grupo G4) | 2026-10-08 | A variação de −40.279 mil reconcilia com −34.807, −15.425 e +9.953 mil, corretamente ordenados. Disponibilidade `presente` mantida; preservar o resultado consolidado total, incluindo não controladores. |
| 53 | LAVV3_N5 | G5a | CONFIRMAR gabarito atual (grupo G5a) | 2026-10-08 | Os dez gabaritos correspondem à conta 1.01.01 do BPA consolidado em 30/06/2026, coincidem com o CSV oficial da CVM e são corroborados pelos saldos finais de caixa da DFC. Todos possuem disponibilidade `presente`. Ressalva: preservar 192.713 mil; a repetição do rótulo representa conta principal e subconta, não valores adicionais. Ressalva geral: manter a distinção entre caixa e equivalentes (1.01.01) e aplicações financeiras classificadas separadamente (1.01.02); não confundir a data comparativa do BPA (31/12/2025) com a da DFC (30/06/2025). |
| 54 | LAVV3_E1 | G6 | CONFIRMAR gabarito atual (grupo G6) | 2026-10-08 | Os sete gabaritos calculam corretamente a margem líquida do 1S26 pela fórmula resultado líquido consolidado total (3.11) dividido pela receita de venda de bens e/ou serviços (3.01), multiplicado por 100. Os insumos coincidem com o CSV oficial da CVM, e os percentuais estão corretamente arredondados a duas casas decimais. Ressalva: utilizar o resultado consolidado total, não apenas a parcela da controladora. Disponibilidade `presente` mantida. |
| 55 | LAVV3_E2 | G8 | CONFIRMAR gabarito atual (grupo G8) | 2026-10-08 | Caixa 192.713 mil versus dívida 1.471.530 mil. Manter `parcial`. A dívida inclui CRI e pequenos arrendamentos classificados dentro das contas definidas; não duplicar a linha de caixa. |
| 56 | LAVV3_E3 | G10 | CONFIRMAR gabarito atual (grupo G10) | 2026-10-08 | Resultado financeiro de +3.044 mil no 1S26 e +18.469 mil no 1S25. Manter `presente`. Os ajustes de juros e CRI da DFC possuem escopo diferente. |
| 57 | POMO4_N1 | G1 | CONFIRMAR gabarito atual (grupo G1) | 2026-10-08 | Os valores dos 11 gabaritos correspondem à conta 3.01 da DRE consolidada de cada empresa, no acumulado de 01/01 a 30/06/2026, e foram confirmados no CSV oficial da CVM. As classificações de disponibilidade também estão coerentes com os contextos congelados. |
| 58 | POMO4_N2 | atenção humana, blocos 1–4 | CONFIRMAR gabarito atual | 2026-10-08 | A DRE 3.11 e a DFC apresentam 535.824, e a disponibilidade `presente` está amparada pela regra 2 da Seção 9. |
| 59 | POMO4_N3 | G3 | CONFIRMAR gabarito atual (grupo G3) | 2026-10-08 | Os dez gabaritos apresentam corretamente os resultados líquidos consolidados de 1S26 e 1S25, com os sinais exigidos, e as variações percentuais calculadas conforme o protocolo. Os valores coincidem com as respectivas contas da DRE consolidada no CSV oficial da CVM, e as direções de aumento ou redução estão corretas. Ressalva: manter `presente`, conforme a regra 2 da Seção 9; a DFC apresenta o resultado consolidado dos dois períodos (caso atípico). |
| 60 | POMO4_N4 | atenção humana, blocos 1–4 | CONFIRMAR gabarito atual | 2026-10-08 | Os componentes da DRE reconciliam a variação de −28.338, com tratamento correto do sinal do IR/CS. |
| 61 | POMO4_N5 | G5a | CONFIRMAR gabarito atual (grupo G5a) | 2026-10-08 | Os dez gabaritos correspondem à conta 1.01.01 do BPA consolidado em 30/06/2026, coincidem com o CSV oficial da CVM e são corroborados pelos saldos finais de caixa da DFC. Todos possuem disponibilidade `presente`. Ressalva geral: manter a distinção entre caixa e equivalentes (1.01.01) e aplicações financeiras classificadas separadamente (1.01.02); não confundir a data comparativa do BPA (31/12/2025) com a da DFC (30/06/2025). |
| 62 | POMO4_E1 | revisão individual | CONFIRMAR COM RESSALVA (revisão individual) | 2026-10-08 | Gabarito confirmado: margem líquida consolidada do 1S26 de 13,30%, calculada por 535.824 / 4.028.514 × 100. Disponibilidade confirmada: `parcial` (1/2 insumos). O numerador corresponde ao resultado consolidado total da DRE (3.11) e está presente na DFC consolidada como "Resultado do período" (535.824 mil), com mesmo conceito, período, base e sinal. A receita de vendas (3.01), necessária como denominador, está ausente do contexto. A regra 4 admite disponibilidade parcial quando apenas parte dos insumos está presente, e o próprio protocolo congelado pré-registrou `parcial` para POMO4_E1. Ressalva: ambiguidade de redação entre as regras 2 e 4 (ver acima). |
| 63 | POMO4_E2 | G8 | CONFIRMAR gabarito atual (grupo G8) | 2026-10-08 | Caixa 1.587.320 mil versus dívida 3.400.431 mil. Manter `presente`. Excluir obrigações de arrendamento classificadas fora das contas definidas e evitar dupla contagem. |
| 64 | POMO4_E3 | G10 | CONFIRMAR gabarito atual (grupo G10) | 2026-10-08 | Resultado financeiro de +98.715 mil no 1S26 e +152.020 mil no 1S25. Manter `ausente`. Não confundir o ajuste da DFC com o resultado financeiro da DRE. |
| 65 | ITSA4_N1 | atenção humana, blocos 1–4 | CONFIRMAR gabarito atual | 2026-10-08 | A receita de vendas corresponde à DRE 3.01, sem incluir a equivalência patrimonial. |
| 66 | ITSA4_N2 | G2a | CONFIRMAR gabarito atual (grupo G2a) | 2026-10-08 | Os seis gabaritos correspondem à conta 3.11 da DRE consolidada, acumulada de 01/01 a 30/06/2026, e coincidem com os valores do CSV oficial da CVM. Em todos os casos, a soma das parcelas atribuídas aos controladores e não controladores reconcilia o resultado consolidado total. |
| 67 | ITSA4_N3 | G3 | CONFIRMAR gabarito atual (grupo G3) | 2026-10-08 | Os dez gabaritos apresentam corretamente os resultados líquidos consolidados de 1S26 e 1S25, com os sinais exigidos, e as variações percentuais calculadas conforme o protocolo. Os valores coincidem com as respectivas contas da DRE consolidada no CSV oficial da CVM, e as direções de aumento ou redução estão corretas. |
| 68 | ITSA4_N4 | G4 | CONFIRMAR gabarito atual (grupo G4) | 2026-10-08 | A variação de +1.678.000 mil reconcilia com +1.038.000, +1.037.000 e −397.000 mil, corretamente ordenados. Disponibilidade `presente` mantida. Preservar a equivalência patrimonial dentro do agregado 3.05 e as mudanças de sinal do resultado financeiro e do IR/CS. |
| 69 | ITSA4_N5 | G5a | CONFIRMAR gabarito atual (grupo G5a) | 2026-10-08 | Os dez gabaritos correspondem à conta 1.01.01 do BPA consolidado em 30/06/2026, coincidem com o CSV oficial da CVM e são corroborados pelos saldos finais de caixa da DFC. Todos possuem disponibilidade `presente`. Ressalva geral: manter a distinção entre caixa e equivalentes (1.01.01) e aplicações financeiras classificadas separadamente (1.01.02); não confundir a data comparativa do BPA (31/12/2025) com a da DFC (30/06/2025). |
| 70 | ITSA4_E1 | G7 | CONFIRMAR gabarito atual (grupo G7) | 2026-10-08 | Resultado de equivalência patrimonial de 9.354.000 mil, conta 3.04.06. Manter disponibilidade `presente`. A DFC apresenta ajuste de reconciliação com sinal invertido (−9.354.000), enquanto o BPA apresenta o saldo dos investimentos (93.348.000), que não deve ser confundido com o resultado do semestre. |
| 71 | ITSA4_E2 | G8 | CONFIRMAR gabarito atual (grupo G8) | 2026-10-08 | Caixa 4.709.000 mil versus dívida 10.618.000 mil. Manter `parcial`. Incluir debêntures classificadas nas contas definidas e excluir passivos de arrendamento classificados separadamente. |
| 72 | ITSA4_E3 | G10 | CONFIRMAR gabarito atual (grupo G10) | 2026-10-08 | Resultado financeiro de +193.000 mil no 1S26 e −844.000 mil no 1S25. Manter `presente`. Preservar a inversão de sinal e não confundir resultado financeiro com equivalência patrimonial ou fluxos de dividendos. |
| 73 | IRBR3_N1 | G1 | CONFIRMAR gabarito atual (grupo G1) | 2026-10-08 | Os valores dos 11 gabaritos correspondem à conta 3.01 da DRE consolidada de cada empresa, no acumulado de 01/01 a 30/06/2026, e foram confirmados no CSV oficial da CVM. As classificações de disponibilidade também estão coerentes com os contextos congelados. Correto conforme o plano de contas específico das resseguradoras (3.01 = 3.01.02 Receitas com Resseguros). |
| 74 | IRBR3_N2 | G2b | CONFIRMAR gabarito atual, com ressalva (grupo G2b) | 2026-10-08 | O resultado líquido consolidado de 90.305 mil corresponde à conta 3.13 da DRE consolidada, confere com o CSV oficial e está presente no contexto congelado. A cadeia da DRE reconcilia o valor. Ressalva: as subcontas 3.13.01 e 3.13.02 estão zeradas e não reconciliam o total; limitação registrada sem presumir sua causa. Disponibilidade `presente` mantida; gabarito original preservado. |
| 75 | IRBR3_N3 | G3 | CONFIRMAR gabarito atual (grupo G3) | 2026-10-08 | Os dez gabaritos apresentam corretamente os resultados líquidos consolidados de 1S26 e 1S25, com os sinais exigidos, e as variações percentuais calculadas conforme o protocolo. Os valores coincidem com as respectivas contas da DRE consolidada no CSV oficial da CVM, e as direções de aumento ou redução estão corretas. Ressalva: preservar o código do plano de seguros (3.13) e a ressalva já registrada sobre as subcontas de atribuição zeradas (IRBR3_N2). |
| 76 | IRBR3_N4 | atenção humana, blocos 1–4 | CONFIRMAR gabarito atual | 2026-10-08 | A decomposição da DRE reconcilia a variação de −150.357 mil no resultado líquido, respeitando o agrupamento de contas previsto no protocolo. |
| 77 | IRBR3_N5 | G5a | CONFIRMAR gabarito atual (grupo G5a) | 2026-10-08 | Os dez gabaritos correspondem à conta 1.01.01 do BPA consolidado em 30/06/2026, coincidem com o CSV oficial da CVM e são corroborados pelos saldos finais de caixa da DFC. Todos possuem disponibilidade `presente`. Ressalva geral: manter a distinção entre caixa e equivalentes (1.01.01) e aplicações financeiras classificadas separadamente (1.01.02); não confundir a data comparativa do BPA (31/12/2025) com a da DFC (30/06/2025). |
| 78 | IRBR3_E1 | atenção humana, blocos 1–4 | CONFIRMAR gabarito atual | 2026-10-08 | A conta 3.03 apresenta resultado bruto de −41.006 mil, confirmado pela diferença entre receitas e despesas de resseguro. |
| 79 | IRBR3_E2 | atenção humana, blocos 1–4 | CONFIRMAR gabarito atual | 2026-10-08 | A conta 3.08 apresenta +117.761 mil, com reconciliação exata. Registrado: a rubrica Despesas Financeiras possui sinal positivo atípico na fonte disponível, cuja natureza não foi esclarecida. |
| 80 | IRBR3_E3 | atenção humana, blocos 1–4 | CONFIRMAR gabarito atual | 2026-10-08 | A conta 1.01.02 do ativo circulante apresenta 4.414.934 mil, conforme a definição corrigida antes da coleta pela Emenda 1. |
| 81 | CEAB3_N1 | G1 | CONFIRMAR gabarito atual (grupo G1) | 2026-10-08 | Os valores dos 11 gabaritos correspondem à conta 3.01 da DRE consolidada de cada empresa, no acumulado de 01/01 a 30/06/2026, e foram confirmados no CSV oficial da CVM. As classificações de disponibilidade também estão coerentes com os contextos congelados. |
| 82 | CEAB3_N2 | G2a | CONFIRMAR gabarito atual (grupo G2a) | 2026-10-08 | Os seis gabaritos correspondem à conta 3.11 da DRE consolidada, acumulada de 01/01 a 30/06/2026, e coincidem com os valores do CSV oficial da CVM. Em todos os casos, a soma das parcelas atribuídas aos controladores e não controladores reconcilia o resultado consolidado total. Ressalva: preservar o total consolidado de 179.594 mil, distinto dos 179.595 mil atribuídos à controladora. |
| 83 | CEAB3_N3 | G3 | CONFIRMAR gabarito atual (grupo G3) | 2026-10-08 | Os dez gabaritos apresentam corretamente os resultados líquidos consolidados de 1S26 e 1S25, com os sinais exigidos, e as variações percentuais calculadas conforme o protocolo. Os valores coincidem com as respectivas contas da DRE consolidada no CSV oficial da CVM, e as direções de aumento ou redução estão corretas. |
| 84 | CEAB3_N4 | G4 | CONFIRMAR gabarito atual (grupo G4) | 2026-10-08 | A variação de −24.790 mil reconcilia com −80.106, +31.255 e +24.061 mil. Disponibilidade `presente` mantida; preservar o resultado consolidado total de 179.594 mil, distinto da parcela da controladora. |
| 85 | CEAB3_N5 | G5a | CONFIRMAR gabarito atual (grupo G5a) | 2026-10-08 | Os dez gabaritos correspondem à conta 1.01.01 do BPA consolidado em 30/06/2026, coincidem com o CSV oficial da CVM e são corroborados pelos saldos finais de caixa da DFC. Todos possuem disponibilidade `presente`. Ressalva geral: manter a distinção entre caixa e equivalentes (1.01.01) e aplicações financeiras classificadas separadamente (1.01.02); não confundir a data comparativa do BPA (31/12/2025) com a da DFC (30/06/2025). |
| 86 | CEAB3_E1 | G6 | CONFIRMAR gabarito atual (grupo G6) | 2026-10-08 | Os sete gabaritos calculam corretamente a margem líquida do 1S26 pela fórmula resultado líquido consolidado total (3.11) dividido pela receita de venda de bens e/ou serviços (3.01), multiplicado por 100. Os insumos coincidem com o CSV oficial da CVM, e os percentuais estão corretamente arredondados a duas casas decimais. Ressalva: utilizar o resultado consolidado total, não apenas a parcela da controladora. Disponibilidade `presente` mantida. |
| 87 | CEAB3_E2 | G8 | CONFIRMAR gabarito atual (grupo G8) | 2026-10-08 | Caixa 540.690 mil versus dívida 949.383 mil. Manter `parcial`. Os financiamentos por arrendamento classificados fora de 2.01.04 e 2.02.01 não integram o gabarito, apesar da semelhança dos rótulos. |
| 88 | CEAB3_E3 | G10 | CONFIRMAR gabarito atual (grupo G10) | 2026-10-08 | Resultado financeiro de −132.964 mil no 1S26 e −164.219 mil no 1S25. Manter `presente`. Evitar dupla contagem das receitas e despesas financeiras repetidas entre contas principais e subcontas. |
| 89 | AURE3_N1 | G1 | CONFIRMAR gabarito atual (grupo G1) | 2026-10-08 | Os valores dos 11 gabaritos correspondem à conta 3.01 da DRE consolidada de cada empresa, no acumulado de 01/01 a 30/06/2026, e foram confirmados no CSV oficial da CVM. As classificações de disponibilidade também estão coerentes com os contextos congelados. |
| 90 | AURE3_N2 | atenção humana, bloco 5 | CONFIRMAR gabarito atual | 2026-10-08 | A DRE consolidada oficial da CVM, ITR de 30/06/2026, versão 1, conta 3.11, confirma −980.667 mil. A decomposição entre controladora (−1.032.285) e não controladores (+51.618) reconcilia o total. Disponibilidade `parcial` mantida. |
| 91 | AURE3_N3 | atenção humana, bloco 5 | CONFIRMAR gabarito atual | 2026-10-08 | A conta 3.11 confirma −980.667 mil em 1S26 e −508.856 mil em 1S25, ambos acumulados semestrais. O aumento da magnitude do prejuízo é de 92,72%. Disponibilidade `parcial` mantida. |
| 92 | AURE3_N4 | G4 | CONFIRMAR gabarito atual (grupo G4) | 2026-10-08 | A variação de −471.811 mil reconcilia com −711.793, +185.355 e +54.627 mil. Disponibilidade `ausente` mantida, conforme a regra 5 da Seção 9, pois somente um nó aparece na DFC. Preservar o sinal negativo do prejuízo e a mudança de sinal do IR/CS. |
| 93 | AURE3_N5 | G5a | CONFIRMAR gabarito atual (grupo G5a) | 2026-10-08 | Os dez gabaritos correspondem à conta 1.01.01 do BPA consolidado em 30/06/2026, coincidem com o CSV oficial da CVM e são corroborados pelos saldos finais de caixa da DFC. Todos possuem disponibilidade `presente`. Ressalva geral: manter a distinção entre caixa e equivalentes (1.01.01) e aplicações financeiras classificadas separadamente (1.01.02); não confundir a data comparativa do BPA (31/12/2025) com a da DFC (30/06/2025). |
| 94 | AURE3_E1 | G6 | CONFIRMAR gabarito atual (grupo G6) | 2026-10-08 | Os sete gabaritos calculam corretamente a margem líquida do 1S26 pela fórmula resultado líquido consolidado total (3.11) dividido pela receita de venda de bens e/ou serviços (3.01), multiplicado por 100. Os insumos coincidem com o CSV oficial da CVM, e os percentuais estão corretamente arredondados a duas casas decimais. Ressalva: preservar a margem negativa de −16,00%; manter disponibilidade `ausente`, pois nenhum dos dois insumos necessários aparece no contexto. |
| 95 | AURE3_E2 | G8 | CONFIRMAR gabarito atual (grupo G8) | 2026-10-08 | Caixa 2.949.774 mil versus dívida 23.654.224 mil. Manter `presente`. Incluir os arrendamentos classificados nas contas definidas e evitar dupla contagem de grupos e subgrupos repetidos. |
| 96 | AURE3_E3 | G10 | CONFIRMAR gabarito atual (grupo G10) | 2026-10-08 | Resultado financeiro de −1.321.977 mil no 1S26 e −1.376.604 mil no 1S25. Manter `ausente`. Ajustes de juros, derivativos e saldos patrimoniais não substituem a linha 3.06. |
<!-- FIM_TABELA_DECISOES_FINAIS -->

### 7.1 Decisões provisórias substituídas (histórico; não contam como finais)

| id | decisão provisória | data | substituída por |
|---|---|---|---|
| AURE3_N2 | PENDENTE — verificação documental | 2026-10-08 | CONFIRMAR (bloco 5, 2026-10-08), após conferência no pacote oficial da CVM |
| AURE3_N3 | PENDENTE — verificação documental | 2026-10-08 | CONFIRMAR (bloco 5, 2026-10-08), após conferência no pacote oficial da CVM |

## 8. Integridade

Conferência com `tabela_decisoes_finais.py --verificar`, executada antes do commit de preservação:
- 98 linhas de decisão no registro, sendo 96 finais e 2 provisórias substituídas;
- os 96 ids finais são únicos e iguais aos 96 ids do dataset, com 12 por categoria;
- nenhuma decisão final duplicada ou ausente;
- nenhuma correção;
- todas as decisões finais são CONFIRMAR e têm data;
- a tabela da Seção 7 é igual à gerada a partir do registro.
