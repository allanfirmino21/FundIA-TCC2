# Executor da coleta — RAGAS do TCC 2

`avaliacao/ragas/coletar_respostas_tcc2.py` gera as 96 respostas diretas do experimento definido
em `PROTOCOLO_RAGAS_TCC2.md`, sobre o dataset congelado `dataset_tcc2.json`. O dataset e os
instrumentos foram congelados no commit `a3f424f8bcc25446fc8221dbd1a30bb370b68af8`.

```
dataset congelado → recuperação congelada → prompt do TCC 1 → Gemini → resposta bruta (1 arquivo por caso)
```

**A coleta termina nas respostas brutas.** O executor não importa o RAGAS, não chama
`exatidao.py` nem `comportamento.py`, não classifica nada e não calcula estatísticas.

O arquivo se chama `coletar_respostas_tcc2.py`, e não `coletar_respostas.py`, porque o
`construir_dataset.py` importa `extrair_chunks` do `avaliacao/coletar_respostas.py` (TCC 1)
pelo nome do módulo. Um homônimo nesta pasta poderia ser importado no lugar dele.

## 1. O que é executado, e como

| Etapa | Implementação (sem alterar `modulos/`) | Protocolo |
|---|---|---|
| Documento | `cvm.baixar_documento`, com a versão registrada, a partir do ZIP de dados abertos da CVM. O SHA-256 precisa ser igual ao da Seção 4. | Seções 4 e 15.2 |
| Versão | A versão registrada precisa ser a mais recente no índice do ZIP (regra de versão). | Seção 4 |
| Índice | `criar_chunks` + `indexar_documento` num ChromaDB próprio, em `avaliacao/ragas/runtime/indices/`. A coleção é recriada do zero a cada execução, e o `chroma_db/` do sistema não é aberto. | Seções 6 e 15.1 |
| Recuperação | `recuperar_contexto` sem alteração: `QUERY_NUMERICO`, top-k = 3, embeddings `paraphrase-multilingual-mpnet-base-v2` do cache local (`HF_HUB_OFFLINE=1`). Roda uma vez por caso, como no TCC 1. | Seções 5 e 6 |
| Conferência do contexto | O SHA-256 do contexto e de cada trecho precisa ser igual ao congelado no dataset. Se diferir, **nada é gerado**. | Seção 9, regra 8 |
| Prompt | O texto do TCC 1, sem acréscimos, só com o contexto numérico e a pergunta. | Seção 5 |
| Geração | `gemini-2.5-flash`, temperatura 0,1, `max_output_tokens` 1024. | Seções 5 e 17 |

**O que o modelo recebe:** só o prompt montado por `montar_requisicao`. `verificar_requisicao`
recusa, antes de cada chamada, qualquer payload que traga outra coisa:

- gabarito;
- valores de referência;
- revisão técnica;
- justificativa ou classe de disponibilidade;
- parâmetros diferentes dos congelados.

A disponibilidade fica no registro apenas como metadado (`disponibilidade_congelada`).

## 2. Pré-condições da coleta real

1. O executor, seus testes e esta documentação estão commitados. Com alterações não
   commitadas em `config.py`, `modulos/`, `avaliacao/coletar_respostas.py`,
   `avaliacao/ragas/`, `.gitattributes` ou `requirements.txt`, o `--execute` para.
2. O HEAD descende do commit de congelamento `a3f424f…`.
3. O dataset tem o SHA-256 congelado (`313bdf35…`) e o protocolo também (`e0b37460…`).
4. O ZIP de dados abertos do ITR 2026 da CVM está disponível. Há duas formas de fornecê-lo:
   - `--baixar-zip`: baixa o ZIP atual da CVM. Atende à regra de versão "na data da coleta".
   - `--zip CAMINHO`: usa um ZIP local.

   Nos dois casos, a origem e o SHA-256 do ZIP ficam registrados.
5. O modelo de embeddings está no cache local do Hugging Face.
6. A chave está em `api_key.txt` (ignorado pelo git). Ela é lida só em `--execute`, nunca é
   impressa nem gravada, e as mensagens de erro passam por `sanitizar`.

## 3. Dry-run (sem Gemini)

```bash
python avaliacao/ragas/coletar_respostas_tcc2.py --dry-run --zip CAMINHO/itr_cia_aberta_2026.zip
```

**O que o dry-run faz:**

- valida o dataset (96 casos, 12 empresas, N1–N5/E1–E3, IDs únicos, 69/15/12, sem
  respostas nem scores);
- confere os SHA-256 do dataset e do protocolo;
- aplica a regra de versão;
- gera os 12 documentos e confere seus SHA-256;
- recria os 12 índices num diretório temporário e recupera o contexto;
- confere os contextos contra o dataset;
- monta e verifica as 96 requisições.

**O que o dry-run não faz:**

- não cria o cliente do Gemini (tentar criá-lo levanta `ChamadaRealProibida`);
- não lê `api_key.txt`;
- não grava nada em `coleta_tcc2/`.

Ao final, informa quantos casos estão prontos e se o estado do git permitiria o `--execute`.

## 4. Coleta real (ainda NÃO autorizada)

A coleta real só começa depois da autorização do autor. **Nenhum `--execute` foi rodado até
aqui.** A forma prevista é:

```bash
python avaliacao/ragas/coletar_respostas_tcc2.py --execute --baixar-zip
```

**Proteções contra disparo acidental:**

- sem `--dry-run` nem `--execute`, o script não faz nada (código de saída 2);
- `--dry-run` e `--execute` são mutuamente exclusivos;
- o cliente real só é criado quando `main()` recebe `--execute`.

**Opções operacionais** (não definem piloto; o protocolo, Seção 15.9, não prevê piloto real):

| Opção | Efeito |
|---|---|
| `--case-id ID` | Restringe a execução a um caso; pode ser repetida. |
| `--limit N` | No máximo N casos nesta execução. |
| `--pausa S` | Segundos de espera entre casos. |
| `--retentar-erros` | Refaz casos com ERRO ou registro corrompido. |
| `--reexecutar-concluido --case-id ID --motivo "..."` | Gera uma versão separada de um caso já concluído. Viola a Seção 15.8 ("cada caso é gerado uma única vez"), por isso só com emenda ao protocolo. A observação original nunca é alterada. |

**Ordem:** a ordem congelada dos casos no dataset (WEGE3_N1 … AURE3_E3), sem randomização. Fica
registrada em `manifesto_config.json`.

## 5. Arquivos gerados

```
avaliacao/ragas/coleta_tcc2/
  manifesto_config.json            configuração congelada da coleta (criado uma vez, nunca alterado)
  estado_coleta.json               estado operacional: execuções, casos tentados, encerramento
  respostas/<case_id>.json         resposta concluída (um arquivo por caso)
  respostas/<case_id>.erro_NN.json tentativa com falha técnica (preservada)
  respostas/<case_id>.reexecucao_NN.json  só com --reexecutar-concluido
  respostas/_invalidos/            registros corrompidos, preservados antes de uma nova tentativa
avaliacao/ragas/runtime/           documentos e índices recriados (ignorado pelo git)
```

### `manifesto_config.json`

Contém:

- `commit_inicio`, `commit_congelamento_dataset`, `criado_em_utc`, `fonte_cvm_inicio`;
- `sha256_configuracao` e `configuracao`, que registra:
  - o nome do experimento e o SHA-256 do dataset;
  - o SHA-256 do protocolo registrado no dataset;
  - n = 96, as empresas, as categorias, a distribuição de disponibilidade e a ordem dos casos;
  - os documentos (versão e SHA-256);
  - a geração: modelo, temperatura, tokens, texto e hash do prompt, nenhuma retentativa
    automática;
  - a recuperação: função, `QUERY_NUMERICO`, top-k, embeddings e sua revisão local, chunking,
    índice;
  - o SHA-256 do código usado e dos instrumentos congelados;
  - a versão do Python e das dependências.

Não contém gabaritos, respostas esperadas nem a chave.

### `respostas/<case_id>.json`

**Identificação e documento:** `case_id`, ticker, código CVM, empresa, estrutura, categoria,
pergunta, `disponibilidade_congelada` (metadado), versão e SHA-256 do documento.

**Contexto e recuperação:**

- `recuperacao`: parâmetros usados;
- `contexto`: `ctx_num` integral, SHA-256 e `trechos`. Cada trecho traz ordem, título,
  `chroma_id`, SHA-256 e texto. São os `retrieved_contexts` do RAGAS, separados por
  `extrair_chunks` do TCC 1.

**Requisição e geração:**

- `requisicao`: modelo, temperatura, `max_output_tokens`, prompt enviado e seu SHA-256;
- `geracao`: modelo retornado pela API, `finish_reason`, `truncada_por_limite`, uso de tokens
  (inclusive de raciocínio);
- `resposta`: o texto sem espaços nas pontas, como no TCC 1;
- `resposta_bruta`: o texto como a API devolveu.

**Execução e integridade:** `inicio_utc`, `fim_utc`, `duracao_s`, `tentativa`, `status`,
`erro`, `commit`, `sha256_dataset`, `sha256_configuracao` e `sha256_registro` (selo de
integridade).

Nenhum campo do gabarito ou da revisão técnica é copiado.

## 6. Retomada

A cada execução, o executor:

1. valida o manifesto e o selo do próprio manifesto;
2. recalcula a configuração e para se algo mudou: dataset, protocolo, código, parâmetros,
   dependências ou Python;
3. verifica que os commits posteriores ao início só alteram `coleta_tcc2/`;
4. classifica cada `case_id` pelo seu arquivo:
   - `CONCLUIDO`: só quando o registro é íntegro (JSON legível, selo confere, mesmo `case_id`,
     mesma configuração, resposta não vazia);
   - `ERRO`: há `erro_NN.json` e nenhum registro concluído;
   - `CORROMPIDO`: o arquivo principal está ilegível ou adulterado. Não conta como concluído;
   - `PENDENTE`: nenhum arquivo.
5. executa só os `PENDENTE`. `ERRO` e `CORROMPIDO` entram apenas com `--retentar-erros`.

A retomada nunca usa o texto da pergunta como identificador. Uma interrupção no caso 73 não
exige refazer os 72 anteriores.

## 7. Erros

- **Não há retentativa automática.** Uma falha da API grava `respostas/<id>.erro_NN.json`
  (status `ERRO`, tipo e mensagem sanitizada, sem traceback) e **interrompe a execução**.
- Uma resposta sem texto (por exemplo, bloqueada) é `ERRO` (`RESPOSTA_SEM_TEXTO`), com o
  `finish_reason` registrado. Isso segue o TCC 1, em que `resp.text.strip()` sobre `None`
  interrompia a coleta.
- Uma falha nunca vira resposta. Nenhum texto substituto é gravado.
- Uma nova tentativa só acontece com `--retentar-erros`. Ela recebe o próximo número de
  tentativa, e os arquivos de erro anteriores são mantidos.
- Diferença em relação ao TCC 1: o script antigo repetia automaticamente os erros 503 até 4
  vezes. Aqui cada nova tentativa é explícita e fica registrada, conforme o pedido para esta
  etapa. Um 503 não gera resposta, então isso não afeta a regra de geração única (Seção 15.8).
- `Ctrl+C` encerra a execução como `interrompida` e libera a trava. O caso em andamento
  continua `PENDENTE`.
- Uma trava (`coleta_tcc2/.trava`) impede duas execuções simultâneas.

## 8. Proteção contra sobrescrita

- Os arquivos de caso são criados com `O_EXCL`: se o arquivo já existe, a gravação falha.
- Um caso concluído é pulado.
- A reexecução explícita grava `reexecucao_NN.json` à parte.
- Um registro corrompido é movido para `_invalidos/` antes de uma nova tentativa, sem ser
  apagado.

## 9. Separação entre coleta e avaliação

Etapas seguintes, **fora deste executor**:

1. exatidão determinística (`exatidao.py`);
2. classificação manual de comportamento (`RUBRICA_COMPORTAMENTO_TCC2.md`, `comportamento.py`);
3. congelamento das respostas, classificações e decisões de sinal;
4. só depois disso, o RAGAS.

Os testes verificam que o executor não importa `ragas`, `langchain*`, `exatidao` nem
`comportamento`, e que funciona com esses módulos bloqueados.

## 10. O que NÃO deve ser executado ainda

- `--execute`, com ou sem `--limit` ou `--case-id`;
- qualquer chamada ao Gemini;
- instalação ou execução do RAGAS;
- classificação de comportamento ou exatidão sobre respostas.

Os testes (`tests/test_ragas_coleta.py`) usam recuperador, gerador e git falsos, bloqueiam o
socket e gravam só em diretórios temporários.
