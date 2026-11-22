# Proveniência da distribuição pública do FundIA (TCC 2)

Este documento explica a relação entre este repositório e o histórico Git em que o FundIA foi
desenvolvido. Também indica como conferir essa relação sem acesso ao histórico.

## 1. Distribuição pública e histórico de desenvolvimento

Este repositório é uma **distribuição consolidada**, com histórico Git próprio. Ele começa em
`d69e583`, de 22/11/2026, e não contém os commits do desenvolvimento.

O FundIA foi desenvolvido em outro repositório Git, que permanece **privado**. Esse repositório
tem 48 commits na linha principal, de 30/08/2026 a 22/11/2026, e um ramo auxiliar. Ele foi
preservado integralmente num arquivo `git bundle`, verificado com `git bundle verify` e
restaurado em teste com todas as referências e objetos idênticos.

| Arquivo | Data | Tamanho | SHA-256 |
|---|---|---|---|
| `FundIA-TCC2_historico_original_2026-11-22.bundle` | 22/11/2026 | 26.706.711 bytes | `334fc4fc11ba3c0887e16c5595cbf2162303b1a99c8c0a3f823af3c327cf6f71` |

O histórico de desenvolvimento não foi publicado porque as mensagens de commit trazem linhas de
coautoria acrescentadas automaticamente por ferramentas de inteligência artificial usadas no
desenvolvimento. O autor optou por não publicar essas atribuições automáticas. O apoio dessas
ferramentas segue declarado nos documentos em que ocorreu, sem alteração; por exemplo, em
`avaliacao/ragas/PROTOCOLO_RAGAS_TCC2.md` e em
`avaliacao/ragas/avaliacao_tcc2/revisao_gabaritos/REVISAO_HUMANA_GABARITOS.md`.

**Os commits citados no TCC, neste repositório e nos artefatos** (identificadores como `f41137d`
ou `777b256`) pertencem ao histórico privado e **não estão disponíveis aqui**. Os artefatos
congelados continuam citando esses identificadores, porque alterá-los invalidaria os SHA-256
registrados. A seção 4 dá a correspondência de cada um.

## 2. O que pode ser conferido neste repositório

| Relação | Como conferir |
|---|---|
| A árvore do primeiro commit público (`d69e583`) é idêntica, byte a byte, à do último commit do histórico privado (`29aa6b1`) | `git rev-parse d69e583^{tree}` deve imprimir `21306229abad686b2fe526fc0de1939b0e8e4657` |
| Cada pasta de `estados_avaliados/` é o diretório `modulos/` do commit indicado | O hash de árvore do Git da pasta deve coincidir com a coluna "Árvore de `modulos/`" da seção 4 |
| O `modulos/` da raiz é o código de `777b256` a `29aa6b1` | Hash de árvore `ed0f5af5b126287861a11d17cc9e56f79545f37c` |
| Os artefatos das avaliações não foram alterados | SHA-256 registrados nos manifestos e em `verificacao/ragas_congelados_d78d5a5.sha256` |
| Os resumos e as análises decorrem dos artefatos | Recálculo pelos scripts originais, sem alterá-los |

`python verificar_distribuicao.py` faz todas essas conferências sem rede, sem chave de API e
sem o Git. Só a primeira linha da tabela usa o Git.

O hash de árvore do Git depende apenas dos nomes e do conteúdo dos arquivos, não das mensagens de
commit. Por isso a correspondência de conteúdo pode ser conferida aqui. Os identificadores de
commit, as datas e os títulos da seção 4 são registro do autor, extraído do histórico privado em
22/11/2026, e não podem ser conferidos sem ele.

## 3. Correspondência entre as avaliações e o código

O código do sistema fora de `modulos/` (`api.py`, `app.py`, `config.py` e `frontend/`) não mudou
ao longo do histórico, por isso cada estado é representado apenas pelo seu `modulos/`. O script
`avaliacao/experimento_flash_pro.py` é o da coleta (`75dbfc4`) e não mudou depois dela; a versão
anterior, usada no piloto (`58e88f5`), não está incluída.

| Avaliação (Quadro [m3] do TCC) | Commits do histórico privado | Código nesta distribuição |
|---|---|---|
| Demonstração do fluxo (4.1) | `1a08d00`, versão do TCC 1 | `estados_avaliados/1a08d00/modulos/` |
| Comparação Flash × Pro (4.4) | pré-registro `6a9fee9`; piloto `58e88f5`; coleta `75dbfc4` | `estados_avaliados/1a08d00/modulos/` (pré-registro) e `estados_avaliados/75dbfc4/modulos/` (piloto e coleta) |
| Validação manual, rodada inicial (4.2) | WEGE3: `75dbfc4` com alterações não versionadas; BBAS3: `183e69f`; ZAMP3: `504ce6d` | WEGE3: só o estado de base, `estados_avaliados/75dbfc4/modulos/`; BBAS3 e ZAMP3: `estados_avaliados/183e69f/modulos/` |
| Validação manual, segunda rodada (4.2) | `e4d96e1` | `estados_avaliados/e4d96e1/modulos/` |
| Validação manual, terceira rodada (4.2) | `c5f4464` com alterações depois registradas em `269f3f1` | `estados_avaliados/269f3f1/modulos/` |
| Respostas diretas, protocolo RAGAS (4.5) | sistema em `777b256`; instrumentos e artefatos de `b17ea73` a `9da5536` | `modulos/` |
| Execução exploratória (4.2.5) | `8bf3994` | `modulos/` |
| Demonstração funcional da aplicação web | `f41137d`, versão documentada no TCC | `modulos/` |

**Limites desta correspondência:**
- **Rodada inicial da WEGE3:** incluiu alterações não versionadas e não pode ser reconstituída
  nem pelo histórico privado.
- **Terceira rodada:** a equivalência com `269f3f1` foi conferida no histórico privado. O SHA-256
  das alterações, registrado em `execucao.json`, coincide com o da diferença entre `c5f4464` e
  `269f3f1` nos arquivos alterados.
- **Seis estados intermediários de `modulos/` não foram incluídos.** São etapas de correção que
  nenhuma avaliação usou como estado de execução (seção 4, "não incluído").
- **Ramo auxiliar `a83a78c`** (28/09/2026, "Registrar emenda operacional da coleta RAGAS"): está
  fora da linha principal e é citado no relatório de fechamento da coleta e em dois testes.

O primeiro commit do histórico privado (`1a08d00`) tem a árvore
`e42f2c1c51776fa535bd232e8672b30aa493fb4f`, a mesma do commit `7f19e7f` do repositório público
[allanfirmino21/TCC-1](https://github.com/allanfirmino21/TCC-1), que pode ser conferido lá.

## 4. Commits do histórico privado

Títulos das mensagens como registrados, sem o corpo nem as linhas de coautoria. Árvores
abreviadas em 12 caracteres.

| # | Commit | Data | Título da mensagem | Árvore raiz | Árvore de `modulos/` | Código na distribuição |
|---|---|---|---|---|---|---|
| 1 | `1a08d00` | 2026-08-30 | Baseline do TCC 2: pipeline deterministico com auditoria de fidelidade | `e42f2c1c5177` | `f4cd20febe91` | `estados_avaliados/1a08d00/modulos/` |
| 2 | `6a9fee9` | 2026-08-30 | Pre-registro do experimento Flash vs Pro (antes da coleta) | `d291a2d55452` | `f4cd20febe91` | `estados_avaliados/1a08d00/modulos/` |
| 3 | `58e88f5` | 2026-08-30 | Instrumentacao de telemetria e piloto WEGE3 do experimento Flash vs Pro | `a86eb5832d28` | `3bf40180a562` | `estados_avaliados/75dbfc4/modulos/` |
| 4 | `75dbfc4` | 2026-08-30 | Coleta completa do experimento Flash vs Pro (20 execucoes) e analise de cobertura | `2a74eae94b70` | `3bf40180a562` | `estados_avaliados/75dbfc4/modulos/` |
| 5 | `183e69f` | 2026-09-22 | Preparar pipeline para validação manual TCC2 | `02b3199f4a4b` | `6b23d723d033` | `estados_avaliados/183e69f/modulos/` |
| 6 | `504ce6d` | 2026-09-23 | Artefatos da validação manual: WEGE3 e BBAS3 (ITR 2026-06-30 v1) | `d8037824148f` | `6b23d723d033` | `estados_avaliados/183e69f/modulos/` |
| 7 | `657a225` | 2026-09-23 | Artefatos da validação manual: ZAMP3 (ITR 2026-06-30 v1) | `687e88438bf9` | `6b23d723d033` | `estados_avaliados/183e69f/modulos/` |
| 8 | `873e013` | 2026-09-25 | Garantir consistencia da base contabil na recuperacao | `4e7a2a27453d` | `f18043bf686b` | não incluído |
| 9 | `53ce987` | 2026-09-25 | Corrigir selecao hierarquica de aplicacoes financeiras | `bffde8992c4a` | `74879f39eb27` | não incluído |
| 10 | `870542e` | 2026-09-25 | Relatorio da validacao manual e evidencia pos-correcao da WEGE3 | `999c0cec74ac` | `74879f39eb27` | não incluído |
| 11 | `cea3018` | 2026-09-26 | Resumir resultado e caixa nas metricas e tirar tabelas do contexto narrativo | `7f2dbd37d577` | `de23563dfbc2` | não incluído |
| 12 | `0b05768` | 2026-09-26 | Ajustar regras do Prompt 2 e registrar narrativas regeneradas | `100034e500f0` | `7c1f2e542e3f` | não incluído |
| 13 | `6096ce4` | 2026-09-26 | Encontrar captacao no mercado aberto nas tres grafias da CVM | `a65ef7dee8be` | `8505d6eb0bfc` | não incluído |
| 14 | `cb73bf6` | 2026-09-26 | Identificar banco so pela receita de intermediacao financeira | `8cdd8ee115ac` | `57ae0e5c6f1c` | não incluído |
| 15 | `27dfdd5` | 2026-09-26 | Conferir o par conceito + valor na auditoria (versao 2.0) | `ec28edcc0e9d` | `f1dc75c68a6a` | `estados_avaliados/e4d96e1/modulos/` |
| 16 | `e4d96e1` | 2026-09-26 | Guardar fixtures e artefatos da validacao sem conversao de fim de linha | `d2cbaf3ac510` | `f1dc75c68a6a` | `estados_avaliados/e4d96e1/modulos/` |
| 17 | `c5f4464` | 2026-09-26 | Consolidar validacao manual final de WEGE3 BBAS3 e ZAMP3 | `d3488fa2aa4e` | `f1dc75c68a6a` | `estados_avaliados/e4d96e1/modulos/` |
| 18 | `269f3f1` | 2026-09-26 | Corrigir causalidade da narrativa com decomposicao do resultado | `c2e50d5cd0e0` | `2aa495241569` | `estados_avaliados/269f3f1/modulos/` |
| 19 | `777b256` | 2026-09-27 | Deduplicar arrendamentos pela hierarquia do CD_CONTA | `61fe2a238d4d` | `ed0f5af5b126` | `modulos/` |
| 20 | `b17ea73` | 2026-09-27 | Pre-registrar protocolo de avaliacao RAGAS do TCC2 | `ba95ea88f0bb` | `ed0f5af5b126` | `modulos/` |
| 21 | `a3f424f` | 2026-09-27 | Congelar dataset e instrumentos da avaliacao RAGAS | `4281e245c660` | `ed0f5af5b126` | `modulos/` |
| 22 | `fb13ba8` | 2026-09-27 | Preparar executor reprodutivel da coleta RAGAS | `f77c8d6f39d2` | `ed0f5af5b126` | `modulos/` |
| 23 | `10eee31` | 2026-09-29 | Congelar coleta experimental RAGAS do TCC2 | `60a49352ff8b` | `ed0f5af5b126` | `modulos/` |
| 24 | `203cbd8` | 2026-09-29 | Registrar emenda operacional da coleta RAGAS | `ad5b6bcffc7b` | `ed0f5af5b126` | `modulos/` |
| 25 | `2599523` | 2026-09-29 | Preparar executor reprodutivel da avaliacao RAGAS | `f56130888d7f` | `ed0f5af5b126` | `modulos/` |
| 26 | `d49835d` | 2026-09-29 | Congelar resultado da exatidao da avaliacao RAGAS | `454579f41994` | `ed0f5af5b126` | `modulos/` |
| 27 | `cd29dee` | 2026-10-03 | Congelar anotacao de comportamento TCC2 | `09a00e85b61c` | `ed0f5af5b126` | `modulos/` |
| 28 | `69b2b49` | 2026-10-03 | Registrar Emenda 4 e liberar pendencias operacionais | `76a3e3d4c623` | `ed0f5af5b126` | `modulos/` |
| 29 | `d78d5a5` | 2026-10-04 | Congelar resultados RAGAS TCC2 | `989859bafe69` | `ed0f5af5b126` | `modulos/` |
| 30 | `8844743` | 2026-10-06 | Congelar analise dos resultados RAGAS TCC2 | `f4bc67be0226` | `ed0f5af5b126` | `modulos/` |
| 31 | `9dc164a` | 2026-10-08 | Preservar revisao humana dos 96 gabaritos TCC2 | `48bc1e0c28cf` | `ed0f5af5b126` | `modulos/` |
| 32 | `81dd443` | 2026-10-08 | Registrar adendo metodologico da revisao dos gabaritos TCC2 | `cd19ccff0ed3` | `ed0f5af5b126` | `modulos/` |
| 33 | `f90e3bd` | 2026-10-09 | Implementar Emenda 5 da exatidao (regra_sinal) TCC2 | `413b5cbae83c` | `ed0f5af5b126` | `modulos/` |
| 34 | `9da5536` | 2026-10-09 | Congelar resultado da exatidao com a Emenda 5 TCC2 | `959d22994398` | `ed0f5af5b126` | `modulos/` |
| 35 | `e25a3e8` | 2026-10-09 | Complementar observacoes da exatidao sobre numeros truncados TCC2 | `00324a6dec57` | `ed0f5af5b126` | `modulos/` |
| 36 | `ea31628` | 2026-10-09 | Preservar cruzamentos da sintese integrada TCC2 | `22073de91888` | `ed0f5af5b126` | `modulos/` |
| 37 | `fb234bd` | 2026-10-09 | Documentar discordancias entre instrumentos TCC2 | `844c9febcfb3` | `ed0f5af5b126` | `modulos/` |
| 38 | `3a588f1` | 2026-10-10 | Documentar resultados reproduziveis Flash Pro TCC2 | `3abe65848170` | `ed0f5af5b126` | `modulos/` |
| 39 | `c667d87` | 2026-10-11 | Consolidar redacao das secoes 4.1 e 4.2 TCC2 | `e13ba7524a68` | `ed0f5af5b126` | `modulos/` |
| 40 | `16dac39` | 2026-10-11 | Consolidar avaliacao do auditor no TCC2 | `3f18e3f72997` | `ed0f5af5b126` | `modulos/` |
| 41 | `2a0609b` | 2026-10-11 | Consolidar comparacao Flash Pro no TCC2 | `ff14300b4cd2` | `ed0f5af5b126` | `modulos/` |
| 42 | `c053c46` | 2026-10-11 | Consolidar avaliacao RAGAS no TCC2 | `ac7b962068ed` | `ed0f5af5b126` | `modulos/` |
| 43 | `3a78709` | 2026-10-11 | Consolidar discussao integrada TCC2 | `6b0109b6f9dd` | `ed0f5af5b126` | `modulos/` |
| 44 | `8bf3994` | 2026-10-11 | Consolidar ameacas a validade TCC2 | `91cc18bf2ea7` | `ed0f5af5b126` | `modulos/` |
| 45 | `f41137d` | 2026-10-30 | Fechar pendencias P1-01 e P1-02 do capitulo 4 TCC2 | `a5b5b03a7e98` | `ed0f5af5b126` | `modulos/` |
| 46 | `d25ecbb` | 2026-11-20 | Preparar documentacao e configuracao do repositorio publico FundIA-TCC2 | `5bee511e0800` | `ed0f5af5b126` | `modulos/` |
| 47 | `1039049` | 2026-11-20 | Versionar evidencia da demonstracao web do FundIA (11/11/2026) | `e8552df241f0` | `ed0f5af5b126` | `modulos/` |
| 48 | `29aa6b1` | 2026-11-22 | Registrar no guia de reprodutibilidade as verificacoes do clone limpo | `21306229abad` | `ed0f5af5b126` | `modulos/` |

Na coluna "Código na distribuição", `modulos/` indica o diretório da raiz deste repositório.
