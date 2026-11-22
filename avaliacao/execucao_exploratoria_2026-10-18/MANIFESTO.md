# Execução exploratória de 18/10/2026: evidência mínima preservada

**Natureza.** Execução adicional do FundIA, feita em 18/10/2026 durante uma auditoria do sistema,
**depois** das três rodadas da validação manual e **fora** de qualquer protocolo experimental. Não
é uma quarta rodada de validação, não teve leitura manual integral das narrativas e não entra nos
denominadores da validação manual (Seções 4.2.2 a 4.2.4). É usada no TCC 2 apenas como observação
exploratória (Seções 4.2.5, 4.6.1 e 4.7.2).

**Origem.** Pasta não versionada `auditoria_execucao_2026-10-18/`, na raiz do projeto, e o
documento derivado `CONCLUSOES_CONSOLIDADAS_AUDITORIAS_FUNDIA.md` (§5). Esta pasta guarda só cópias
byte a byte dos arquivos necessários para identificar a execução e os dois achados citados no texto.
Os originais não foram alterados nem removidos. Os demais arquivos da pasta de origem (cerca de
27 MB, com o ZIP da CVM, o banco vetorial e os extratos) não foram copiados; seus hashes relevantes
estão listados abaixo.

## Identificação da execução

| Item | Valor | Fonte |
|---|---|---|
| Início | 2026-10-18T21:36:51 UTC | `execucoes.json` |
| Commit | `8bf39943b8787e1d9e0b6fcfcc42bf5f932a48b0` | `execucoes.json` |
| Código dos módulos | SHA-256 dos 12 arquivos de `modulos/` registrados em `execucoes.json`; iguais aos blobs do commit `8bf3994` com fim de linha CRLF (diferença só de conversão de fim de linha) | conferência do passo de fechamento, 30/10/2026 |
| Diferença de código em relação à terceira rodada (`269f3f1`) | só `modulos/metricas.py`, pelo commit `777b256` (deduplicação de arrendamentos); `prompt2.py`, `auditoria.py` e `recuperacao.py` idênticos | `git diff 269f3f1 8bf3994 -- modulos` |
| Modelo de redação | `gemini-2.5-flash` | `execucoes.json` |
| Documento | ITR, `DT_REFER` 2026-06-30, versão 1 | `execucoes.json` |
| Auditor | versão 2.0 (`verificar_conceito=True`) | `execucoes.json` |
| Execuções | uma por empresa (WEGE3, BBAS3, ZAMP3), sem erro | `execucoes.json` |
| Conformidade reportada pelo auditor | WEGE3 33/37; BBAS3 31/32; ZAMP3 45/48 | `execucoes.json` (não usada no texto) |

## Identidade com a terceira rodada

| Verificação | Resultado |
|---|---|
| Documento-fonte | SHA-256 idêntico ao da pasta `_pos_decomposicao_v2` e ao `.sha256` registrado, nas três empresas |
| Métricas calculadas (`dados_extraidos`) | idênticas às de `resultado_analisar.json` da pasta `_pos_decomposicao_v2`, nas três empresas (comparação direta dos JSON) |
| Narrativas | diferentes das da terceira rodada (nova geração do modelo) |

## Achados citados no texto (conferidos nos arquivos)

1. **BBAS3**, `BBAS3/narrativa.md`, seção "O QUE FOI POSITIVO", linha 24: "O Imposto de Renda e
   Contribuição Social sobre o Lucro diminuiu 40,5%, o que contribuiu para o resultado final." A
   mesma narrativa (linha 12) registra que essa linha "reduziu o resultado em -R$ 2,48 bilhões". O
   auditor marcou "40,5%" como CONFERE (percentual, sem verificação de conceito).
2. **ZAMP3**, `ZAMP3/narrativa.md`, linha 25: "O Resultado Antes do Resultado Financeiro e dos
   Tributos (EBITDA aproximado, ...) aumentou 18,8%, para R$ 26,76 milhões." R$ 26,76 milhões é o
   EBIT; o EBITDA calculado é R$ 289,21 milhões, citado corretamente na linha 29. Em
   `ZAMP3/resultado.json`, o auditor marcou "R$ 26,76 milhões" como CONFERE, com conceito
   reivindicado `ebit`: pela regra implementada, o rótulo entre parênteses é desconsiderado
   (teste `test_parentese_explicativo_nao_muda_o_sujeito`).

Não são usados no texto do TCC 2: os demais apontamentos da auditoria de 18/10, inclusive os oito
alertas classificados como falso positivo, que foram classificados na própria auditoria e não por
revisão manual do autor.

## SHA-256

**Cópias nesta pasta** (iguais aos originais):

| Arquivo | SHA-256 |
|---|---|
| `execucoes.json` | `81a3bc40c9fe9ebf793e8d8c09234852bba9102ebe9d1f09d81da0a31dc631bb` |
| `WEGE3/narrativa.md` | `c5068f1924b686ce8ab5429e4ec7bcdcef09b8db1767e2c463f9a594a39e5777` |
| `WEGE3/resultado.json` | `599b520090c1461dec9a1357a9bcda5b6bac5ac7fef8bf9a32d200dcfc7109f3` |
| `BBAS3/narrativa.md` | `0c073079f849e1dac85ed980592dd6c927f37ad8029b642f494b11dd160967c0` |
| `BBAS3/resultado.json` | `ff28b9431bbca18e0758aa4afb70a90c0752742daec36d450e7152de57f16759` |
| `ZAMP3/narrativa.md` | `848e2fefa5bea93e96c4c01c366b24314a13206c8871421aa93dc26c8cf359af` |
| `ZAMP3/resultado.json` | `03fae2b61d6f9d5d0d27b400a7c8fae4a450793371479d15b8b1026df31a6a06` |

**Arquivos de origem não copiados:**

| Arquivo (em `auditoria_execucao_2026-10-18/`, salvo indicação) | SHA-256 |
|---|---|
| `cache/WEGE3_ITR_2026-06-30.txt` | `500d0c0d51df24cf9d0a166c24f3eea033b74a6eb63285cc4349036857bb8ba6` |
| `cache/BBAS3_ITR_2026-06-30.txt` | `96c321232278beb5eb5a4eff167b5cedf76611b55e47f8ccb62c6c051c96bde8` |
| `cache/ZAMP3_ITR_2026-06-30.txt` | `044d8ad11f532cc3f65127a798d06bd689aad50f20da38a0b42e80d0f3bcf983` |
| `comparacao_metricas_historico.json` | `b62176fccbc36879f1bd5a13f6a923c829ea3dc39f9c11b0d672a99aba7101aa` |
| `comparacao_csv_txt.json` | `06f6cb3009256e3af934d6426c2685564a6d1c7af3ba171a4b0ce7846e290869` |
| `reauditoria_historico.json` | `9e8d8a062d10108f8892472c6f0c28383c1538c3a5321b74d9eed537ea6743db` |
| `integridade_codigo.json` | `a2c081334fab31ce7e95976abb561306e5cf9f72d01fd81b6863c5837b037802` |
| `RELATORIO_AUDITORIA.md` | `aa5ecb3f709fb37226f483a783d92523ce14ef2af2168d0693fe7f745c179501` |
| `CONCLUSOES_CONSOLIDADAS_AUDITORIAS_FUNDIA.md` (raiz) | `8e2303379afae7525d6fde2457a0b47eb83be9f4b5166a49c65a19d6ea24828a` |
| `Auditoria_FundIA_2026-10-18.pdf` (raiz) | `2000e453e25b8713aecf803c649b4eef70116c0ec8ed8a874af9ba2c600cb5e2` |

Hashes calculados sobre os bytes dos arquivos em disco, em 30/10/2026. O `.gitattributes` desta
pasta impede conversão de fim de linha nas cópias.
