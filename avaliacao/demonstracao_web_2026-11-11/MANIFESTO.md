# Demonstração funcional da aplicação web (11/11/2026)

**Natureza.** Execução única da aplicação web do FundIA (`api.py` e `frontend/`), feita para
ilustrar a interface no TCC 2 e verificar o funcionamento integrado com a versão atual. Não é
experimento, não teve leitura manual da narrativa e não entra em nenhum denominador das avaliações.

## Identificação

| Item | Valor |
|---|---|
| Código | commit `f41137d`, sem alteração em `api.py`, `frontend/src`, `modulos/`, `config.py` e `tests/` (`git status`) |
| Backend | `uvicorn api:app --port 8000` (iniciou; `/api/status` respondeu) |
| Frontend | `npm run dev --prefix frontend`, em http://localhost:5173 (iniciou) |
| Navegador | Microsoft Edge sem janela, controlado por `capturar_telas.py`; viewport 1280 x 900, escala 2 |
| Empresa | WEGE3 (CVM 5410), código preenchido no campo da interface |
| Documento | ITR, DT_REFER 2026-09-30, VERSAO 1: o mais recente, escolhido pelo sistema (a interface não oferece seleção de período) |
| Modelo de redação | `gemini-2.5-flash` (configuração do sistema) |
| Início e fim (UTC) | 2026-11-11T12:59:01Z a 2026-11-11T13:00:37Z |
| Duração da análise | 82.5 s, do clique em "Analisar" à exibição do resultado |
| Selo exibido | 39/42 números conferem · 92.9% |
| Registros da trilha na tela | 43 (39 confere, 3 divergente, 1 ignorado, conforme o CSV exportado) |
| Auditor | versão 2.0: dois dos três vereditos divergentes trazem o motivo da verificação de conceito |

## O que foi exercitado

- carregamento da interface e confirmação da chave pela API;
- solicitação da análise pelo botão da interface, com progresso por etapas;
- exibição dos indicadores, das seções da narrativa e do painel de auditoria;
- exportação da trilha em CSV pelo botão da interface.

Não exercitados: relatório em PDF, download do documento pela interface, tipo DFP, tema escuro e
outras companhias.

## Divergências acusadas (sem leitura manual integral)

1. "R$ 85,68 milhões" (Lucro): sinal incompatível com o fato. A frase diz "queda de R$ 85,68 milhões".
2. "R$ 22,27 milhões" (Lucro): conceito; a frase cita o "Imposto de Renda e Contribuição Social sobre o Lucro".
3. "R$ 792,09 milhões" (Caixa e Dívidas): conceito; a frase cita os passivos de arrendamento e, em seguida, a dívida bruta.

As duas primeiras seguem padrões de falso alarme descritos na Seção 4.3.3 do TCC 2. Nenhuma foi
classificada por revisão manual sistemática.

## Efeitos colaterais da execução

A aplicação baixou o índice atual de ITR da CVM e o documento de 30/09/2026 para `dados/cache/`, e criou
a coleção correspondente no banco vetorial. Os índices locais anteriores (`dados/meta_itr_2025.csv` e
`dados/meta_itr_2026.csv`) foram restaurados depois da execução.

## SHA-256

| Arquivo | SHA-256 |
|---|---|
| `capturas_originais/01_tela_inicial.png` | `3b60d6b4cffd1764a071cab359f4040af3a1ef54fe5993d15972e1ff4cc2f4c8` |
| `capturas_originais/02_progresso.png` | `002e6e54da9277fb4597b9bbbb34f6ab645be752ccaf258571dbddcb1cc1f56a` |
| `capturas_originais/03_analise_topo.png` | `7b92af857c0a394edf5aa9e4177b6fffb762794289fb87a44b0df4b5ed9cabc6` |
| `capturas_originais/04_analise_pagina_inteira.png` | `83ff0387860dd48c137d69f382784b77797d373eae35efff86af93020ef60067` |
| `capturas_originais/05_auditoria_painel_completo.png` | `b303f3ce5e38d694c9bdc0feaaf39a9022049f38518d29432cfd208b41ff434f` |
| `capturas_originais/06_auditoria_recorte.png` | `5618027d942260389d05e97bfb755d6e7039ba578f5d2b400fe987e42c30ef40` |
| `capturas_originais/07_pagina_inteira_com_auditoria.png` | `5631bf9b608e666bd29ce1dc35974bbf49514bfea1510f7596546595e81ba261` |
| `capturas_originais/auditoria_WEGE3_2026-09-30.csv` | `52a37cd9d0d4c6238a8d9462a3475df4205f1f3b67553623f7c5acb772cf6fd5` |
| `capturas_originais/texto_da_pagina.txt` | `7f3f95ad4f92820972968d856e9cdfea6c651b750d6f2a886a7c23af4c091e78` |
| `capturas_originais/trilha_na_tela.json` | `83582ea7ec9c7125e3e502d2e17c11f055a41116ebc5d2372cb57b60ae1a10dd` |
| `WEGE3_ITR_2026-09-30.txt` | `c7561a2875adedd2f1fb3cf7886e8d7256887bf8c1442994b22a5bb84342c9b0` |

## Figuras do TCC 2 derivadas das capturas

| Figura | Origem | SHA-256 |
|---|---|---|
| `redacao_tcc2/figuras/figura2_interface_fundia_tela_inicial.png` | cópia integral de 01_tela_inicial.png | `3b60d6b4cffd1764a071cab359f4040af3a1ef54fe5993d15972e1ff4cc2f4c8` |
| `redacao_tcc2/figuras/figura3_interface_fundia_analise_wege3.png` | recorte contíguo de 04_analise_pagina_inteira.png, caixa (x0,y0,x1,y1) = (600, 0, 2560, 2130), sem a barra lateral | `41595312c840ffd72eb23f4685cc054e75c321d6e0074c06623901f65ec1b103` |
| `redacao_tcc2/figuras/figura4_interface_fundia_auditoria_wege3.png` | cópia integral de 06_auditoria_recorte.png (parte superior do painel de auditoria) | `5618027d942260389d05e97bfb755d6e7039ba578f5d2b400fe987e42c30ef40` |
