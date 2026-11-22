# Observações da exatidão com a Emenda 5 — RAGAS do TCC 2

Registradas em 2026-10-09, no congelamento do resultado pós-emenda. O resultado original da exatidão
não foi alterado e continua sendo o resultado reportado. Este resultado é **adicional** e deve ser
apresentado lado a lado com o original.

## Resultado gravado

- **Arquivo:** `resultado_exatidao_emenda5.json`.
  - SHA-256 `22af220e529edd04ba97f5a6fc4c841188edc02f9bdb6e46ad4daba7e1cef04f`.
  - Selo (`sha256_registro`) `e36c79ba9ca884095093262631bce6884d376a162db88824d4f12fa8c1f6af0a`, íntegro.
- **Geração:** em 2026-10-09T03:29:23Z, por `gerar_exatidao_emenda5.py --executar`.
  - Commit `f90e3bd820c8be200aaa46b21e84e6284e2468c2`, com a árvore limpa.
  - `exatidao.py` com SHA-256 `a08d1f95…`, chamado com `regra_sinal="emenda5"`.
- **Referência ao original:** `avaliacao_tcc2/exatidao/resultado_exatidao.json`.
  - SHA-256 `3c3e28c0…`, selo `8582e2e0…`.
  - Produzido pelo instrumento `2b4b1170…` (commit `a3f424f`) e congelado no commit `d49835d`.
  - O gerador conferiu, antes de gravar, que o modo padrão (`"original"`) do instrumento novo
    reproduz esse resultado em todos os campos.
- **Conteúdo:**
  - 96 casos, sem id duplicado ou ausente, com as mesmas respostas da coleta congelada (SHA-256 por
    caso);
  - nenhuma pendência de sinal e nenhuma decisão manual de sinal (`sha256_decisoes_sinal = null`).

## Os seis casos corrigidos

Todos são N2 com disponibilidade `presente`. Em todos, o valor confere em módulo, e o sinal era lido
como negativo por causa do rótulo "Lucro/Prejuízo" ou "lucro ou prejuízo" na mesma oração.

| Caso | Número | Sinal lido (original → Emenda 5) | Classe (original → Emenda 5) |
|---|---:|---|---|
| BBAS3_N2 | 6.362.961 | − → + | INCORRETO → CORRETO |
| CEAB3_N2 | 179.594 | − → + | INCORRETO → CORRETO |
| IRBR3_N2 | 90.305 | − → + | INCORRETO → CORRETO |
| ITSA4_N2 | 9.726.000 | − → + | INCORRETO → CORRETO |
| ITUB4_N2 | 24.199.000 | − → + | INCORRETO → CORRETO |
| LAVV3_N2 | 184.619 | − → + | INCORRETO → CORRETO |

## Mudança de sinal sem mudança de classe: BBAS3_N4

- No BBAS3_N4, o número 7.760.116 passa a ser lido como positivo (− → +).
- O caso é N4, sem verificação determinística (NAO_APLICAVEL nos dois resultados), então a classe não
  muda.
- O total é de 7 números com sinal lido alterado, em 7 casos.
- `sinal_revisao_manual` continua igual nos dois resultados: CEAB3_N4, ITSA4_E3 e WEGE3_E3.

## Resultados lado a lado

| Recorte | Original (congelado) | Emenda 5 (adicional) |
|---|---|---|
| Global | C 31 · P 5 · I 7 · NA 53 | C 37 · P 5 · I 1 · NA 53 |
| CORRETO / aplicáveis | 31/43 = 72,1% | 37/43 = 86,0% |
| `presente` | C 31 · P 2 · I 6 · NA 30; 31/39 = 79,5% | C 37 · P 2 · I 0 · NA 30; 37/39 = 94,9% |
| `parcial` | C 0 · P 3 · I 1 · NA 11; 0/4 | C 0 · P 3 · I 1 · NA 11; 0/4 |
| `ausente` | NA 12 (sem aplicáveis) | NA 12 (sem aplicáveis) |

**Casos que não mudam:**
- Os 5 PARCIALMENTE_CORRETO são os mesmos: WEGE3_E2, ZAMP3_N3, ITUB4_N3, ITSA4_E2 e CEAB3_E2.
- O único INCORRETO que sobra é **VALE3_E3** (`parcial`). Os números 2.237.000 e 2.186.000 conferem em
  módulo, mas os sinais lidos são opostos aos exigidos (1S26 negativo e 1S25 positivo). A Emenda 5 não
  altera essa leitura, e o caso continua INCORRETO.

## Caráter retrospectivo

- A Emenda 5 foi concebida **depois da observação do resultado da exatidão**.
- É uma correção post hoc do instrumento de medida, motivada por casos conhecidos.
- **Medidas para conter o risco de ajuste aos resultados:**
  - a regra é geral, sem ticker, id ou valor;
  - foi testada também em situações em que piora a classificação;
  - o resultado original é mantido e reportado;
  - os dois resultados são apresentados lado a lado.
- Essas medidas não eliminam o risco.

## Limitações remanescentes do instrumento

1. **Sinal no nível da oração.** A palavra negativa vale para toda a oração. Uma oração com uma
   palavra negativa e um único valor positivo ainda é lida como negativa, por exemplo "Apesar do
   prejuízo fiscal, o lucro contábil foi de…".
2. **Lista fechada de rótulos e separadores.** A Emenda 5 cobre os pares lucro/prejuízo,
   superávit/déficit e positivo/negativo, separados por "/", "ou", "e/ou" ou com parênteses fechados.
   - Rótulos com outra redação continuam sujeitos à regra 5 original.
   - Um rótulo sem marca negativa, numa empresa com prejuízo, deixa de conferir. Esse é o efeito
     esperado, coberto por teste.
3. **Parênteses (regra C).** Um número isolado entre parênteses, sem palavra negativa fora do rótulo,
   continua indo para revisão manual.
4. **As demais limitações registradas em `exatidao/OBSERVACOES_EXATIDAO.md` não mudam**, como os
   números incompletos por `MAX_TOKENS` e a leitura de escala implícita.
5. **N4 continua fora da verificação determinística.** O sinal lido em BBAS3_N4 não é avaliado.

## Correção da avaliação × melhoria do FundIA

- A Emenda 5 corrige a **leitura do instrumento de verificação**, não o sistema avaliado.
- As 96 respostas do FundIA são as mesmas da coleta congelada: nenhuma resposta, contexto ou
  configuração mudou.
- A passagem de 31/43 para 37/43 **não representa melhoria do FundIA**. Ela reflete a remoção de um
  falso negativo do instrumento em seis respostas cujo valor já estava correto em módulo e cuja
  redação não afirmava prejuízo.
- Os resultados RAGAS e a anotação de comportamento não dependem desta emenda e não foram alterados.
