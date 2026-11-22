# Controle negativo da Etapa 0 (2026-10-08)

**Objetivo:** verificar se a conferência mecânica (`etapa0_preconferencia.py`) detecta erros
plantados num gabarito.

**Execução:** 2026-10-08, 23:47 UTC, pelo Claude Code, com transcrição do log da sessão.

**Procedimento:**
1. Gerou-se `etapa0_controle.py` a partir de `etapa0_preconferencia.py`, por substituição textual
   (`sed`). A única mudança permite ler o dataset de `DS_PATH` e gravar a saída em `OUT_NAME`.
2. Gravou-se uma **cópia temporária** do dataset congelado, fora do repositório, com cinco defeitos
   plantados:

   | Caso | Defeito plantado | Tipo |
   |---|---|---|
   | WEGE3_N1 | `vl_conta_cvm` da fonte 3.01 alterado de 19611868 para 19611869 | valor-fonte errado |
   | LAVV3_N5 | texto do gabarito com "192.731" no lugar de "192.713" | texto errado |
   | WEGE3_N2 | `sinal_exigido = False` no resultado | sinal contra a tabela do §11.1 |
   | CEAB3_N1 | `disponibilidade = "ausente"` | disponibilidade errada |
   | WEGE3_N3 | valor do percentual de variação alterado para −3.2 | derivado errado |

3. Executou-se `etapa0_controle.py` sobre a cópia perturbada.
4. Em seguida, a cópia perturbada e a saída `etapa0_controle.json` foram **apagadas**.
5. O `git status` foi conferido e estava limpo (0 entradas).

**Comando de perturbação (transcrito):**

```python
C["WEGE3_N1"]["fontes_gabarito"][0]["vl_conta_cvm"]="19611869.0000000000"   # valor-fonte errado
C["LAVV3_N5"]["gabarito"]=C["LAVV3_N5"]["gabarito"].replace("192.713","192.731")  # texto errado
C["WEGE3_N2"]["valores_esperados"][0]["sinal_exigido"]=False                   # sinal contra tabela
C["CEAB3_N1"]["disponibilidade"]="ausente"                                     # disponibilidade errada
v=[v for v in C["WEGE3_N3"]["valores_esperados"] if v["tipo"]=="percentual"][0]; v["valor"]="-3.2"  # % errado
```

**Saída** (filtrada para os casos perturbados, com os acentos do console corrigidos):

```
== 78 restantes: 78 | com problema: 5 | com aviso: 7
  WEGE3_N1  [presente] P=['valor diverge 3.01 ÚLTIMO: dataset 19611869.0000000000 x oficial 19611868.0000000000', 'valor exigido topo_1s26=19611868000 x recalculado 19611869000.0000000000', "presente, mas faltam no contexto: ['3.01/ÚLTIMO']"] | A=[]
  WEGE3_N2  [presente] P=['sinal_exigido=False difere da tabela do §11.1 (True) em resultado_1s26'] | A=[]
  WEGE3_N3  [presente] P=['percentual variacao_percentual=-3.2 x recalculado -3.111168638031474166041511880', 'texto do gabarito não contém 3,20%'] | A=[]
  LAVV3_N5  [presente] P=['texto do gabarito não contém 192.713 (caixa_30jun26)'] | A=[]
  CEAB3_N1  [ausente] P=['parcial/ausente, mas todos os conceitos exigidos estão no contexto', "ausente, mas há insumo no contexto: ['3.01/ÚLTIMO']"] | A=[]
0
```

**Resultado:**
- Os **5 defeitos foram detectados**, cada um como "problema" no caso certo.
- Entre os 78 casos de grupo, nenhum outro passou a ter problema, e o número de avisos (7) é o mesmo da execução real.
- Na execução real, sobre o dataset congelado, a Etapa 0 registrou:
  - 78 casos de grupo, com 0 problemas e 7 avisos;
  - 18 casos de atenção humana, com 0 problemas e 1 aviso.

  O resultado está em `etapa0_resultado.json`.

**Limitação:** o controle cobre cinco tipos de defeito num pequeno número de casos. Ele não prova que
a conferência detecta qualquer erro. Também não cobre a regra 2 aplicada a insumos de indicadores
derivados (ver POMO4_E1).
