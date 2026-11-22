# Relatório de fechamento da coleta experimental RAGAS — TCC 2

Data do fechamento: 2026-09-29.

Este relatório registra, de forma mecânica, como terminou a coleta das 96 respostas
experimentais. Ele **não** reproduz, resume nem avalia o conteúdo de nenhuma resposta
(`resposta`/`resposta_bruta`). Nenhuma avaliação (RAGAS, exatidão determinística ou
rubrica de comportamento) foi executada antes deste congelamento.

---

## A. Identificação da coleta

| Item | Valor |
|---|---|
| Experimento | RAGAS TCC 2 — coleta das respostas diretas (96 casos) |
| Pasta | `avaliacao/ragas/coleta_tcc2/` |
| Esquema dos registros | 1 |
| Manifesto criado em | 2026-09-28T00:14:05+00:00 |
| Primeira geração | 2026-09-28T00:14:05+00:00 (execução 1) |
| Última geração | 2026-09-29T03:48:16+00:00 (execução 9) |
| `sha256_configuracao` | `b956544649f7d4f7a01435fb598c888c70d84cb3bbb5f9ddc9a7ebc6aec0793b` |

Artefatos congelados nesta pasta:

- `manifesto_config.json` — configuração congelada (não alterada desde a criação);
- `estado_coleta.json` — estado operacional e histórico das 9 execuções;
- `respostas/<case_id>.json` — 96 registros concluídos, cada um selado (`sha256_registro`);
- `respostas/AURE3_N3.erro_01.json` — registro histórico da única falha técnica;
- `RELATORIO_FECHAMENTO_COLETA.md` — este relatório;
- `SHA256_COLETA.txt` — manifesto de integridade (ver Seção S).

## B. Executor

- Commit do executor e de todas as 9 execuções: `fb13ba8eac90afd8e67c7eb4c064fd2b3442b354`
  ("Preparar executor reprodutivel da coleta RAGAS").
- `avaliacao/ragas/coletar_respostas_tcc2.py`: SHA-256
  `2ba5a565cbc3c8723be7954c5a27de3cbf48ab3864e405e0925be0f18ad97ccc` (inalterado durante toda a coleta).
- Todos os 96 registros e o registro de erro trazem `commit = fb13ba8…` e a mesma
  `sha256_configuracao` do manifesto.

## C. Dataset e protocolo congelados

- Commit de congelamento: `a3f424f8bcc25446fc8221dbd1a30bb370b68af8`.
- `avaliacao/ragas/dataset_tcc2.json`: `313bdf359fdeabb063ceec3bcca12ebfe3b52caae346b3ff1d9f3dc23196bc5e`.
- `avaliacao/ragas/PROTOCOLO_RAGAS_TCC2.md`: `e0b374608a1e4f5b4cae530931e4626f6f67c145d215212ea7ecd55b08da2490`
  (versão do master, com a Emenda 1; a Emenda 2 **não** está incorporada — ver Seção P).
- Demais instrumentos congelados (hashes no manifesto, inalterados):
  `RUBRICA_COMPORTAMENTO_TCC2.md` `c1b401ad…`, `exatidao.py` `2b4b1170…`,
  `comportamento.py` `d2a3e7e7…`, `revisao_tecnica_tcc2.json` `ea240815…`.

## D. Fonte dos documentos (ZIP da CVM)

- Arquivo: `itr_2026.zip` (lido de arquivo local, não versionado neste repositório).
- SHA-256: `4f89a9987303984a78ebae31b09ca2be8f7ba2445078120cb9a8d6f84934b253`.
- O mesmo ZIP, com o mesmo hash, foi usado nas 9 execuções (campo `fonte_cvm` de cada execução).

## E. Empresas e casos

12 empresas × 8 casos (N1–N5, E1–E3) = 96 casos, na ordem congelada do dataset, sem randomização.
Distribuição de disponibilidade congelada: presente 69, parcial 15, ausente 12.

| Ticker | Código CVM | Versão ITR | SHA-256 do documento (prefixo) | SHA-256 do contexto congelado (prefixo) |
|---|---|---|---|---|
| WEGE3 | 5410 | 1 | `500d0c0d51df24cf` | `a4cfe672d13e6c82` |
| BBAS3 | 1023 | 1 | `96c321232278beb5` | `666dea60db7dc35f` |
| ZAMP3 | 24317 | 1 | `044d8ad11f532cc3` | `97e46bc582cc2e66` |
| LWSA3 | 24910 | 1 | `e088ffd53f2899dd` | `38df2447f93d4624` |
| VALE3 | 4170 | 3 | `32b625e17d4b90aa` | `984ed325078f8930` |
| ITUB4 | 19348 | 1 | `409ed7c7a7a4cc56` | `9f34e3f53bb7eb9b` |
| LAVV3 | 25062 | 1 | `7d18d8725fd03ffc` | `c0718250913fec5a` |
| POMO4 | 8451 | 1 | `79bba9fbcdeed51b` | `7d66585f5aa1a585` |
| ITSA4 | 7617 | 2 | `f252b1eb14ee6e5c` | `b4cd4f4c907fbf56` |
| IRBR3 | 24180 | 2 | `e528959c4a2cf094` | `444b3d536da5dcc6` |
| CEAB3 | 24848 | 1 | `1dece32b1e39f0a1` | `82517fbdad42e254` |
| AURE3 | 26620 | 1 | `9a3f3625a0e1e260` | `65175eccd1b63d6f` |

Os hashes completos estão em `manifesto_config.json` (`configuracao.documentos`).

## F. Modelo e parâmetros de geração

| Parâmetro | Valor |
|---|---|
| Provedor | Google Gemini API (`google-genai` 2.2.0) |
| Modelo solicitado | `gemini-2.5-flash` |
| Modelo retornado pela API | `gemini-2.5-flash` nos 96 registros |
| Temperatura | 0,1 |
| `max_output_tokens` | 1024 |
| Prompt | modelo do TCC 1, SHA-256 `cf2a6577aed75d58fdd077711c801a1fdba32a385197f741a629494b175d3da1` |
| Retentativas automáticas | 0 (uma única geração por tentativa) |
| Política de erro | a falha grava `ERRO` e interrompe a execução; nova tentativa só com `--retentar-erros` |

Ambiente: Python 3.12.6; chromadb 1.5.9; sentence-transformers 5.5.0; transformers 5.3.0;
torch 2.11.0 (lista completa em `manifesto_config.json`).

## G. Recuperação

| Parâmetro | Valor |
|---|---|
| Função | `modulos.recuperacao.recuperar_contexto` |
| Documento/período | ITR, 2026-06-30 |
| Consulta | `QUERY_NUMERICO` fixa (texto no manifesto) |
| top-k | 3 |
| Embeddings | `paraphrase-multilingual-mpnet-base-v2` (revisão local `4328cf26…`, sem rede) |
| Chunking | `modulos.chunking.criar_chunks`: uma tabela inteira por chunk; narrativo até 800 palavras, overlap 100 |
| Índice | ChromaDB próprio em `avaliacao/ragas/runtime/indices`, com a coleção recriada do zero a cada execução |
| Conferência | antes de cada geração, o SHA-256 do contexto e o de cada trecho são comparados aos do dataset (protocolo, Seção 9, regra 8); qualquer diferença bloqueia antes de chamar o Gemini |

## H. Resultado final

- **96 concluídos / 0 pendentes.**
- 96 arquivos de resposta, 96 `case_id` únicos, conjunto idêntico ao dos 96 casos do dataset congelado.
- Os 96 registros têm selo íntegro, `status = CONCLUIDO` e `erro = null`.
- 1 registro histórico de erro (`AURE3_N3.erro_01.json`), preservado (Seção J).

## I. Chamadas ao Gemini

**97 chamadas no total**: 96 respostas concluídas e 1 chamada que terminou em erro.

- A contagem pelos arquivos (96 + 1) coincide com a soma dos casos registrados nas 9 execuções
  de `estado_coleta.json`.
- As duas paradas por divergência de contexto (Seção O) ocorreram **antes** da chamada ao
  Gemini e não geraram chamadas.

## J. AURE3_N3

AURE3_N3 exigiu uma segunda tentativa porque a primeira chamada à API terminou em
ServerError 503 UNAVAILABLE e não produziu resposta experimental. O arquivo do erro foi
preservado. A resposta válida foi gerada somente na segunda tentativa.

- **Tentativa 1** (execução 8, 2026-09-29T03:41:35–03:41:38 UTC):
  - resultado: `ServerError`, "503 UNAVAILABLE … The service is currently unavailable.";
  - contexto igual ao congelado (`65175ecc…`);
  - nenhum dado de geração e nenhuma resposta registrados.
- **Registro:** `respostas/AURE3_N3.erro_01.json`, preservado byte a byte e com selo íntegro.
- **Tentativa 2** (execução 9, autorizada explicitamente com `--retentar-erros`, limitada aos 6
  casos restantes da AURE3):
  - resposta válida (`finish_reason = STOP`), registrada com `tentativa = 2`
    em `respostas/AURE3_N3.json`.

Isto não constitui duas respostas experimentais para o mesmo caso: a tentativa 1 não produziu resposta.

## K. Tentativas

- 95 casos concluídos na tentativa 1.
- AURE3_N3 concluído na tentativa 2.
- Nenhuma resposta concluída foi sobrescrita ou regenerada.
- Não existe nenhum arquivo `reexecucao_*` nem `_invalidos/`.

## L. Truncamentos por MAX_TOKENS

**36 de 96** respostas terminaram com `finish_reason = MAX_TOKENS` (`truncada_por_limite = true`);
60 terminaram com `STOP`.

| WEGE3 | BBAS3 | ZAMP3 | LWSA3 | VALE3 | ITUB4 | LAVV3 | POMO4 | ITSA4 | IRBR3 | CEAB3 | AURE3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 4 | 2 | 3 | 3 | 1 | 2 | 6 | 3 | 2 | 2 | 2 | 6 |

O limite de 1024 tokens foi aceito, antes da coleta, como limitação conhecida, sem emenda e sem
aumento do limite. As respostas truncadas são respostas válidas e foram mantidas como vieram.

## M. Tokens (soma das 96 respostas, `uso_tokens` da API)

| Entrada | Saída | Raciocínio | Total |
|---|---|---|---|
| 342.502 | 8.121 | 76.740 | 427.363 |

A chamada que terminou em 503 não registrou uso de tokens.

## N. Histórico das 9 execuções (`estado_coleta.json`)

| Exec. | Início → fim (UTC) | Seleção | Encerramento | Chamadas | Concluídos | Truncados | Tokens (entrada / saída / raciocínio / total) |
|---|---|---|---|---|---|---|---|
| 1 | 28/09 00:14:05 → 00:17:17 | todos os casos (ordem congelada) | bloqueio (contexto, ZAMP3) | 16 | 16 (WEGE3, BBAS3) | 6 | 55.568 / 1.379 / 12.989 / 69.936 |
| 2 | 28/09 01:37:34 → 01:42:31 | todos (retomada) | bloqueio (contexto, LAVV3) | 32 | 32 (ZAMP3, LWSA3, VALE3, ITUB4) | 9 | 112.216 / 3.016 / 25.173 / 140.405 |
| 3 | 28/09 23:51:58 → 23:53:36 | `--case-id` LAVV3 ×8 | completa | 8 | 8 | 6 | 27.392 / 686 / 6.952 / 35.030 |
| 4 | 29/09 00:00:20 → 00:02:05 | `--case-id` POMO4 ×8 | completa | 8 | 8 | 3 | 31.304 / 525 / 6.094 / 37.923 |
| 5 | 29/09 00:09:49 → 00:11:10 | `--case-id` ITSA4 ×8 | completa | 8 | 8 | 2 | 30.142 / 661 / 5.712 / 36.515 |
| 6 | 29/09 03:31:27 → 03:32:34 | `--case-id` IRBR3 ×8 | completa | 8 | 8 | 2 | 24.192 / 578 / 6.610 / 31.380 |
| 7 | 29/09 03:36:00 → 03:36:59 | `--case-id` CEAB3 ×8 | completa | 8 | 8 | 2 | 24.192 / 748 / 5.776 / 30.716 |
| 8 | 29/09 03:41:18 → 03:41:38 | `--case-id` AURE3 ×8 | erro (503 em AURE3_N3) | 3 | 2 | 1 | 9.362 / 93 / 1.769 / 11.224 |
| 9 | 29/09 03:47:24 → 03:48:16 | `--retentar-erros --case-id` AURE3 ×6 | completa | 6 | 6 | 5 | 28.134 / 435 / 5.665 / 34.234 |
| **Total** | | | | **97** | **96** | **36** | **342.502 / 8.121 / 76.740 / 427.363** |

- As 9 execuções usaram o mesmo commit (`fb13ba8`), o mesmo ZIP e a mesma configuração.
- A coincidência de 24.192 tokens de entrada nas execuções 6 e 7 é apenas numérica: os contextos
  das duas empresas são diferentes e cada um confere com o seu hash congelado.

## O. As duas paradas por divergência de contexto

**Fatos**

- As duas paradas oficiais foram causadas pela trava de divergência de contexto do executor
  (`conferir_contexto`; protocolo, Seção 9, regra 8). Em ambas, a trava interrompeu o processo
  antes da chamada ao Gemini do caso afetado, e nenhuma resposta foi gerada com contexto divergente.
- **Parada 1** (execução 1):
  - o pré-voo das 12 empresas havia conferido;
  - após 16 casos concluídos (WEGE3, BBAS3), a recuperação do caso seguinte (ZAMP3_N1) devolveu
    um contexto diferente do congelado;
  - mensagem: "ZAMP3: contexto recuperado difere do congelado no dataset".
- **Parada 2** (execução 2, retomada sem alterações):
  - o pré-voo das 12 empresas conferiu novamente;
  - após mais 32 casos (ZAMP3, LWSA3, VALE3, ITUB4), a recuperação de LAVV3_N1 divergiu
    (mensagem análoga para LAVV3).

**Diagnóstico posterior** (feito em índices descartáveis, fora da coleta, sem chamadas ao Gemini)

- Reproduziu uma falha interna do ChromaDB 1.5.9: `InternalError: Error executing plan: Internal
  error: Error creating hnsw segment reader: Nothing found on disk`.
- A falha foi intermitente e apareceu quando 10 a 12 coleções eram manipuladas no mesmo processo.
- `modulos/recuperacao.py` captura essa exceção sem propagá-la, o que produz um contexto vazio que
  a trava do executor detecta como divergente.
- Em execuções com 1 a 5 coleções por processo, e ao reabrir o índice em um processo novo,
  a falha não foi observada.

**Limitação da inferência**

- A associação entre essa falha e as duas paradas oficiais é **forte, mas não diretamente
  comprovada**: o executor não registrou o hash do contexto observado nas duas paradas oficiais.
- **A causa raiz não está determinada.**

## P. Mudança operacional: uma empresa por processo (respostas 49–96)

- Após a segunda parada, as respostas 49 a 96 (LAVV3, POMO4, ITSA4, IRBR3, CEAB3, AURE3) foram
  coletadas **uma empresa por processo** (execuções 3 a 9).
- Foi usado o mecanismo já existente `--case-id` do executor congelado, que prepara e indexa
  somente as empresas selecionadas.
- Nenhum código foi alterado para isso.
- Trata-se de uma **mudança operacional, não científica**.
- A decisão está documentada como "Emenda 2" no branch separado `emenda-2-coleta-por-empresa`
  (commit `a83a78c4f157539859ded38a0fc4c3d4952f45e4`).
  - Esse branch **ainda não foi integrado** ao master.
  - O protocolo do master permanece no hash `e0b37460…`.
  - O branch foi mantido separado porque alterar o protocolo no master durante a coleta
    bloquearia o executor congelado, que confere o hash do protocolo.
- As 48 respostas anteriores (execuções 1 e 2) foram preservadas sem alteração.

## Q. O que a mudança operacional não alterou

A organização por empresa/processo não alterou:

- o modelo, a temperatura nem o limite de tokens;
- o prompt;
- a função de recuperação, a consulta, o top-k, os embeddings nem o chunking;
- o dataset, as perguntas, os gabaritos nem a ordem dos casos;
- o contexto: cada contexto confere com o hash congelado;
- o executor e a sua configuração.

A `sha256_configuracao` é a mesma nas 9 execuções e nos 96 registros, e o executor recusaria
retomar se ela mudasse.

## R. Contextos

Os 96 registros concluídos têm o SHA-256 do contexto e o SHA-256 de cada um dos trechos
**iguais aos congelados** da empresa correspondente no dataset. O registro de erro de AURE3_N3
também tem contexto igual ao congelado.

## S. Integridade dos artefatos anteriores e manifesto de hashes

- Durante toda a coleta e neste fechamento, permaneceram inalterados:
  - dataset, protocolo e executor;
  - `modulos/` e `dados/ticker_map.csv`;
  - os demais instrumentos congelados;
  - os artefatos de `avaliacao/validacao_manual/`.
- Nenhum arquivo versionado foi modificado.
- A cada execução, as respostas já existentes foram conferidas byte a byte, e nenhuma mudou.
  O único arquivo que o executor reescreve é `estado_coleta.json`, por atualização oficial.

`SHA256_COLETA.txt` contém o SHA-256 de todos os arquivos desta pasta, **exceto dele mesmo**.
Um arquivo não pode conter de forma consistente o próprio hash, por isso não se tenta uma
autorreferência; a integridade de `SHA256_COLETA.txt` é garantida pelo commit git que o versiona.

O arquivo é gerado de forma determinística:

- caminhos relativos a `avaliacao/ragas/coleta_tcc2/`, com separador `/`;
- ordenação por bytes do caminho;
- uma linha por arquivo, no formato `sha256sum` (`<hash>  <caminho>`);
- codificação UTF-8 e fim de linha LF.

Conferência:

```
cd avaliacao/ragas/coleta_tcc2
sha256sum -c SHA256_COLETA.txt
```

O `.gitattributes` do repositório (`avaliacao/ragas/** -text`) garante que o git guarda estes
arquivos byte a byte, sem conversão de fim de linha.

## T. Ausência de avaliação antes do congelamento

Até este congelamento, não foi executado:

- RAGAS;
- a verificação de exatidão determinística;
- a rubrica de comportamento;
- nenhuma leitura semântica, classificação ou correção das respostas.

Todas as verificações foram mecânicas: hashes, selos, estados, contagens, metadados de geração
e tokens.

Registro de transparência: durante a verificação da execução 4, ao listar a estrutura de campos
de um registro, o terminal exibiu de forma involuntária os primeiros 80 caracteres do campo
`resposta_bruta` de POMO4_N1. O trecho não foi usado nem avaliado, e as verificações seguintes
passaram a excluir explicitamente `resposta` e `resposta_bruta`.

## U. Limitações operacionais observadas

1. **Paradas por divergência de contexto:**
   - houve duas paradas, e a causa raiz está indeterminada (Seção O);
   - o executor não registra o hash do contexto divergente observado;
   - `modulos/recuperacao.py` captura exceções do ChromaDB sem propagá-las;
   - a proteção efetiva foi a conferência de hash do executor, que impediu qualquer geração com
     contexto divergente.
2. **Isolamento por empresa:** a estratégia de uma empresa por processo concluiu as 6 empresas
   restantes sem divergência (48 casos). Isso é evidência operacional, não prova de que a falha
   não possa ocorrer.
3. **Truncamento:** 36 de 96 respostas foram truncadas pelo limite de 1024 tokens de saída, uma
   limitação aceita antes da coleta.
4. **Falha transitória da API:** houve um erro 503 (AURE3_N3), e a nova tentativa foi feita com
   autorização explícita e registrada (Seção J).
5. **Janela temporal:** a coleta se estendeu por cerca de 27,5 horas, de 28/09 00:14 a
   29/09 03:48 UTC.
   - A API informa apenas o nome `gemini-2.5-flash`.
   - Eventuais mudanças do lado do servidor dentro desse nome não são observáveis.
6. **Não determinismo da geração:** com temperatura 0,1 e uma única geração por caso, as respostas
   não são reprodutíveis bit a bit por nova chamada. A reprodutibilidade da avaliação depende
   destes registros congelados.
7. **Protocolo e testes:**
   - a Emenda 2 ainda não está no protocolo do master;
   - no master, `tests/test_ragas_coleta.py::test_dataset_congelado_nao_e_modificado` falha de
     forma conhecida porque espera que `coleta_tcc2/` não exista;
   - a correção desse teste está no branch da Emenda 2 e será tratada na integração.
8. **Fonte dos documentos:** o ZIP de origem não está versionado; apenas o seu SHA-256 está
   registrado.
