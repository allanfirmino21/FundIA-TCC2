# Guia de reprodutibilidade do FundIA (TCC 2)

Este guia liga cada avaliação do TCC 2 ao estado do código em que ela foi executada, aos scripts
e procedimentos usados e aos artefatos preservados. Ele segue o Quadro [m3] do trabalho
("Versões do sistema usadas em cada avaliação").

**Commits citados.** Os identificadores de commit deste guia (como `75dbfc4`) pertencem ao
histórico de desenvolvimento, que é privado e não está nesta distribuição pública. O código de
cada estado avaliado está em `estados_avaliados/` (tabela ao fim da seção 2). A correspondência
completa e os meios de conferência estão em `PROVENIENCIA.md`.

## 1. Princípios

- **Não há um único commit de execução.** O código mudou ao longo do TCC 2, e cada avaliação foi
  executada no estado vigente naquele momento (seção 2).
- **`f41137d` é a versão documentada.** É o estado representado na Figura 1 do TCC 2. Nele, o
  código do sistema (`modulos/`, `api.py`, `app.py`, `config.py`, `frontend/`) é idêntico ao do
  commit `777b256` (27/09/2026), a última alteração de código. Os commits seguintes alteram
  apenas scripts de avaliação, artefatos e documentação.
- **Artefatos congelados.** As saídas das avaliações estão versionadas, a maioria com SHA-256
  registrado. Em 20/11/2026, os hashes conferiram com os arquivos:
  - 100 em `avaliacao/ragas/coleta_tcc2/SHA256_COLETA.txt`;
  - 16 arquivos `.sha256` em `avaliacao/validacao_manual/`;
  - 11 no manifesto da demonstração web.
- **Limites da reexecução.** A redação e o juiz do RAGAS usam o Gemini, que não é
  determinístico (temperatura 0,3 na redação). Os modelos `gemini-2.5-*` podem ser
  descontinuados, e a CVM pode publicar novas versões dos documentos. Reexecutar produz novas
  amostras, não as mesmas saídas. O que pode ser refeito de forma determinística, com as versões
  de dependências registradas, é o cálculo sobre os documentos congelados e a análise dos
  artefatos preservados.

## 2. Mapa das avaliações

| Avaliação (seção do TCC 2) | Estado do código | Auditor | Modelo | Documento | Scripts ou procedimento | Artefatos |
|---|---|---|---|---|---|---|
| Demonstração do fluxo (4.1) | Versão do TCC 1. Artefatos preservados no commit `1a08d00`, cujo conteúdo é idêntico ao commit `7f19e7f` do repositório `TCC-1` | 1.0 | Gemini 2.5 Flash | ITR de 30/06/2026 da VALE3; versão do documento não registrada | Aplicação do TCC 1 | `avaliacao/demonstracao_VALE3_ITR_2026-06-30.json`; `avaliacao/auditoria_VALE3_2026-06-30.csv` |
| Comparação Flash × Pro (4.4) | Coleta em `75dbfc4`; pré-registro em `6a9fee9`; piloto em `58e88f5` | 1.0 | Gemini 2.5 Flash e Gemini 2.5 Pro | ITR de 31/03/2026 | `avaliacao/experimento_flash_pro.py`; resumo por `avaliacao/flash_pro/resumir_experimento_flash_pro.py` | `avaliacao/PRE_REGISTRO_flash_vs_pro.md`; `avaliacao/experimento_flash_pro*.csv` e `*.json`; `avaliacao/narrativas/`; `avaliacao/flash_pro/` |
| Validação manual, rodada inicial (4.2) | WEGE3: `75dbfc4`, com alterações não versionadas em `modulos/cvm.py`, `modulos/metricas.py` e `modulos/orquestrador.py`; BBAS3: `183e69f`; ZAMP3: `504ce6d`. As três usaram a versão 1 da instrução de redação | 1.0 | Gemini 2.5 Flash | ITR de 30/06/2026, versão 1 | `analisar(ticker, "ITR", periodo="2026-06-30", versao="1")` | `avaliacao/validacao_manual/*_ITR_2026-06-30_v1/`; `avaliacao/validacao_manual/RELATORIO_validacao_manual.md` |
| Validação manual, segunda rodada (4.2) | `e4d96e1`; versão 2 da instrução | 2.0 | Gemini 2.5 Flash | idem | idem | `avaliacao/validacao_manual/*_v1_final/`; `avaliacao/validacao_manual/RELATORIO_validacao_manual_final.md` |
| Validação manual, terceira rodada (4.2) | `c5f4464`, com alterações não versionadas depois registradas no commit `269f3f1`; versão 3 da instrução | 2.0 | Gemini 2.5 Flash | idem | idem | `avaliacao/validacao_manual/*_v1_pos_decomposicao_v2/`; `avaliacao/validacao_manual/RELATORIO_correcao_causalidade.md` |
| Respostas diretas, protocolo RAGAS (4.5) | Sistema em `777b256`; executor da coleta em `fb13ba8`; protocolo pré-registrado em `b17ea73`; conjunto de avaliação congelado em `a3f424f` | não se aplica | Gemini 2.5 Flash na resposta e como juiz | ITR de 30/06/2026, versão mais recente de cada companhia | `avaliacao/ragas/coletar_respostas_tcc2.py`; `avaliacao/ragas/avaliar_respostas_tcc2.py`; `avaliacao/ragas/exatidao.py`; `avaliacao/ragas/comportamento.py` | `avaliacao/ragas/dataset_tcc2.json`; `avaliacao/ragas/coleta_tcc2/`; `avaliacao/ragas/avaliacao_tcc2/` |
| Execução exploratória (4.2.5) | `8bf3994` | 2.0 | Gemini 2.5 Flash | ITR de 30/06/2026, versão 1 | Execução avulsa, fora de protocolo | `avaliacao/execucao_exploratoria_2026-10-18/` |
| Demonstração funcional da aplicação web (3.1.5 e 4.1) | `f41137d`, sem alteração de código | 2.0 | Gemini 2.5 Flash | ITR de 30/09/2026 da WEGE3, versão 1 (o mais recente na data) | `api.py` e `frontend/`; capturas por `capturar_telas.py` | `avaliacao/demonstracao_web_2026-11-11/` |

**Versões da instrução de redação** (`PROMPT_NARRATIVA`, em `modulos/prompt2.py`)

| Versão | Commit de origem | SHA-256 do texto | Usada em |
|---|---|---|---|
| 1 | `1a08d00` (mantida em `58e88f5`) | `f78100591e5f8e40d8d6fc7857dd1abd973b2fd7fffdd288c48889a92706b300` | Comparação Flash × Pro; rodada inicial |
| 2 | `0b05768` | `6f193e23b8b99fd93ba9144fdf8ced0cda971ab29929bd096c5fab1d352946b0` | Segunda rodada |
| 3 | `269f3f1` | `1e9732698c3a257bd391acdaf190ba9c00dd8b3a33eabe170834b894e7b7e043` | Terceira rodada; execução exploratória; estado atual |

**Código de cada estado nesta distribuição.** O código do sistema fora de `modulos/` não mudou
ao longo do histórico; cada estado é representado pelo seu `modulos/`.

| Estado do código | Pasta |
|---|---|
| `1a08d00` e `6a9fee9` | `estados_avaliados/1a08d00/modulos/` |
| `58e88f5` e `75dbfc4` | `estados_avaliados/75dbfc4/modulos/` |
| `183e69f` e `504ce6d` | `estados_avaliados/183e69f/modulos/` |
| `e4d96e1` e `c5f4464` | `estados_avaliados/e4d96e1/modulos/` |
| `269f3f1` | `estados_avaliados/269f3f1/modulos/` |
| `777b256` em diante (inclui `8bf3994` e `f41137d`) | `modulos/` da raiz |

## 3. Detalhes por avaliação

### 3.1 Demonstração do fluxo

A execução é do TCC 1 e anterior ao primeiro commit do histórico de desenvolvimento. O JSON
registra a narrativa e a auditoria de uma execução, com 42 valores conformes e um ignorado. O CSV é a trilha exportada
de outra execução sobre o mesmo documento, com 47 registros: 46 conformes e um ignorado. A versão
do documento entregue à CVM não foi registrada, e a reexecução não reproduz as mesmas saídas.

### 3.2 Comparação Flash × Pro

- **Desenho:** o pré-registro (`avaliacao/PRE_REGISTRO_flash_vs_pro.md`) fixa hipótese, critérios
  e plano de análise antes da coleta.
- **Coleta:** feita em `75dbfc4`, com 20 execuções (cinco empresas, dois modelos, duas execuções).
  O manifesto registra o hash do prompt preenchido por execução.
- **Conferência do resumo:** a partir do estado atual,
  `python avaliacao/flash_pro/resumir_experimento_flash_pro.py verificar` recalcula o resumo
  sobre os artefatos e o compara com `avaliacao/flash_pro/resumo_experimento_flash_pro.json`.
- **Reexecução**, com chave e rede: numa cópia do repositório, substituir `modulos/` por
  `estados_avaliados/75dbfc4/modulos/` e rodar `python avaliacao/experimento_flash_pro.py`, que
  não mudou desde a coleta. O resultado é uma nova amostra.

### 3.3 Validação manual

**Conteúdo de cada pasta** de `avaliacao/validacao_manual/`:
- o documento da CVM usado (`*.txt`) e seu SHA-256 (`*.txt.sha256`);
- `execucao.json`, com o commit e o `git status` no momento da execução;
- `resultado_analisar.json`, com as métricas e as seções da narrativa;
- `narrativa.md`;
- `auditoria.json`.

**Pastas fora das três rodadas:** são execuções intermediárias, preservadas como registro.
- `*_v1_pos_cd_conta` (WEGE3, `657a225` com alterações não versionadas);
- `*_v1_pos_prompt2` (`870542e` com alterações não versionadas, de onde vem o quinto achado);
- `*_v1_pos_decomposicao` (`c5f4464`, primeira tentativa da correção causal, cujo texto não está
  no histórico de desenvolvimento).

Essas execuções combinaram um commit com alterações não versionadas e não podem ser reconstituídas.
O estado de base de `657a225` é o de `estados_avaliados/183e69f/modulos/`; o de `870542e` não está
em `estados_avaliados/`.

**Reprodutibilidade:**
- As execuções chamaram `modulos.orquestrador.analisar` com período e versão explícitos. O script
  auxiliar que gravou as pastas não está versionado.
- Com os documentos congelados, o cálculo das métricas é determinístico e pode ser refeito com o
  código de cada rodada em `estados_avaliados/`; a narrativa, não.
- O estado exato da rodada inicial da WEGE3 inclui alterações não versionadas e não pode ser
  reconstituído, nem pelo histórico de desenvolvimento.
- O da terceira rodada corresponde a `estados_avaliados/269f3f1/modulos/`. A equivalência foi
  conferida no histórico de desenvolvimento: o SHA-256 das alterações registrado em
  `execucao.json` coincide com o de `git diff c5f4464 269f3f1` nos arquivos alterados.

### 3.4 Respostas diretas (RAGAS)

**Linha do tempo:**

| Commit (histórico de desenvolvimento) | Etapa |
|---|---|
| `b17ea73` | Protocolo pré-registrado (`avaliacao/ragas/PROTOCOLO_RAGAS_TCC2.md`) |
| `a3f424f` | Conjunto de 96 perguntas congelado (`dataset_tcc2.json`) |
| `fb13ba8` | Executor da coleta |
| `10eee31` | Coleta congelada |
| `203cbd8` | Emenda operacional da coleta |
| `d49835d` | Resultado da exatidão |
| `cd29dee` | Anotação de comportamento |
| `d78d5a5` | Escores do RAGAS |
| `8844743` | Análise dos resultados |
| `9dc164a` | Revisão humana dos gabaritos |
| `f90e3bd` e `9da5536` | Emenda 5 da exatidão (análise complementar; o resultado reportado é o original) |

**Ambiente:**
- a exatidão e a rubrica rodam no ambiente principal;
- o RAGAS roda num ambiente separado, com `avaliacao/ragas/requirements_avaliacao.txt` e a
  resolução completa em `avaliacao/ragas/requirements_avaliacao.lock`;
- instruções detalhadas em `avaliacao/ragas/README_COLETA.md` e
  `avaliacao/ragas/README_AVALIACAO.md`.

**Conferência dos artefatos, sem rede:**
- `python avaliacao/ragas/avaliacao_tcc2/sintese/sintetizar_resultados_tcc2.py verificar`;
- `python avaliacao/ragas/avaliacao_tcc2/exatidao_emenda5/gerar_exatidao_emenda5.py` (sem
  `--executar`, apenas confere);
- a análise, por `python verificar_distribuicao.py`.

O modo `verificar` de `analisar_resultados_ragas.py` compara os 387 arquivos brutos com o commit
`d78d5a5` por meio do Git e, por isso, falha nesta distribuição. O verificador público substitui
só essa etapa pela conferência contra `verificacao/ragas_congelados_d78d5a5.sha256`, gerado dos
blobs daquele commit. Depois, executa o cálculo do script original, sem alterá-lo, e compara as
três saídas byte a byte.

Pela mesma razão, `coletar_respostas_tcc2.py --execute` recusa uma nova coleta nesta
distribuição: ele exige que o commit atual descenda de `a3f424f`.

**Reexecução**, com chave e rede: siga `README_COLETA.md` (`--dry-run` antes de `--execute`) e
`README_AVALIACAO.md`. A coleta e o juiz geram novas amostras.

### 3.5 Execução exploratória

Execução avulsa de 18/10/2026, fora de protocolo e sem leitura manual integral. A pasta guarda
cópias byte a byte dos arquivos necessários para identificar a execução e os achados citados. Os
demais arquivos da pasta de origem não foram versionados; os hashes relevantes estão no
`MANIFESTO.md`.

### 3.6 Demonstração funcional da aplicação web

Execução única de 11/11/2026, para verificar o funcionamento integrado da aplicação com a versão
atual. Não é experimento nem validação.

**Conteúdo da pasta:**
- o manifesto, com os SHA-256;
- o registro da execução (`execucao_demonstracao.json`);
- o documento da CVM usado;
- o script de captura;
- em `capturas_originais/`: as sete capturas de tela, a trilha exportada em CSV, o texto da página
  e a trilha lida da tela.

## 4. Verificações que não exigem rede nem chave

`python verificar_distribuicao.py` reúne as conferências abaixo, exceto os testes unitários, e
não grava arquivos. Com `--rapido`, omite o teste de falso positivo do auditor.

Em 22/11/2026, todas foram executadas nesta distribuição, sem chave de API no ambiente e sem
acesso à rede pelos scripts. A mesma bateria tinha sido executada em 21/11/2026 num clone limpo
do histórico de desenvolvimento, com os mesmos resultados.

| Verificação | Comando | Resultado em 22/11/2026 |
|---|---|---|
| Testes unitários | `python -m unittest discover -s tests` | 395 testes, sem falhas (6 pulados) |
| Hashes dos artefatos | `python verificar_distribuicao.py` | Coleta RAGAS 100/100, validação manual 16/16, execução exploratória 7/7, demonstração web 11/11; resultados RAGAS brutos e anotações 392/392 |
| Estados de código | idem | As cinco pastas de `estados_avaliados/` e o `modulos/` da raiz coincidem com as árvores registradas em `PROVENIENCIA.md` |
| Primeiro commit público | idem | Árvore `21306229abad…`, idêntica à do último commit do histórico de desenvolvimento |
| Falso positivo do auditor (TCC 1) | idem, ou `python avaliacao/testar_falso_positivo_auditor.py` | Controle 9/9; falso positivo de 0/400 em percentuais e 123/400 (30,8%) em moedas, idêntico ao arquivado em `avaliacao/resultado_falso_positivo_2026-07-19.txt` |
| Frases plantadas (TCC 1) | idem, ou `python avaliacao/testar_auditor_plantado.py` | 5/5 frases com o veredito esperado |
| Resumo Flash × Pro | idem, ou ver seção 3.2 | Recalculado e idêntico a `resumo_experimento_flash_pro.json` |
| Síntese RAGAS | idem, ou ver seção 3.4 | Recalculada e idêntica a `sintese_resultados_tcc2.json` |
| Análise RAGAS | idem (ver seção 3.4) | As três saídas recalculadas e idênticas às versionadas |
| Exatidão com a Emenda 5 (conferência) | idem, ou ver seção 3.4 | CORRETO em 31/43 aplicáveis no resultado original e 37/43 com a Emenda 5, como registrado; nada gravado |

O verificador também foi testado numa cópia adulterada de propósito, com um byte acrescentado num
resultado RAGAS, num arquivo da demonstração web e num módulo de `estados_avaliados/`. Ele acusou
as três alterações.

## 5. Artefatos herdados do TCC 1

Permanecem em `avaliacao/` os artefatos do TCC 1, presentes desde o primeiro commit do histórico
de desenvolvimento (`1a08d00`):
- o experimento de falso positivo;
- a avaliação RAGAS com 15 perguntas (`rodar_ragas.py`, `coletar_respostas.py`,
  `injetar_ground_truth.py`, `resultados_ragas.json`, `respostas_coletadas.json`);
- a comparação entre modelos anterior ao cálculo determinístico (`comparar_modelos.py`,
  `comparacao_modelos.json`, `auditoria_por_modelo_2026-07-19.json`);
- as evidências da WEGE3 (`evidencia_fidelidade_WEGE3*.csv`).

Eles descrevem a versão do TCC 1 e não devem ser lidos como resultados do TCC 2.
