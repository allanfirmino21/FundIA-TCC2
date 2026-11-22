# Estados de código usados nas avaliações

Cada pasta contém o diretório `modulos/` de um commit do histórico de desenvolvimento, que é
privado e não está neste repositório. Os arquivos são cópias byte a byte, extraídas dos objetos
do Git em 22/11/2026.

| Pasta | Commit de origem | Árvore de `modulos/` | Avaliações |
|---|---|---|---|
| `1a08d00/modulos/` | `1a08d00` (também `6a9fee9`) | `f4cd20febe91954fe1b2ae41662852e0dc182f64` | Demonstração do fluxo (versão do TCC 1); pré-registro Flash × Pro |
| `75dbfc4/modulos/` | `75dbfc4` (também `58e88f5`) | `3bf40180a5625960fa9193e0b3cab83d7c05b694` | Piloto e coleta Flash × Pro; base da rodada inicial da WEGE3 |
| `183e69f/modulos/` | `183e69f` (também `504ce6d`) | `6b23d723d03327e0942cbfe61e09748dd43f8b58` | Rodada inicial da BBAS3 e da ZAMP3 |
| `e4d96e1/modulos/` | `e4d96e1` (também `c5f4464`) | `f1dc75c68a6a74f29f27106aac5fbae03b124b98` | Segunda rodada da validação manual |
| `269f3f1/modulos/` | `269f3f1` | `2aa495241569c7dca97d117e62af5b47439673fd` | Terceira rodada da validação manual |

O estado usado no protocolo RAGAS, na execução exploratória e na demonstração da aplicação web é o
`modulos/` da raiz do repositório (árvore `ed0f5af5b126287861a11d17cc9e56f79545f37c`).

**Uso.** Para executar o sistema num desses estados, substitua o `modulos/` da raiz pelo da pasta
correspondente numa cópia do repositório. O restante do código do sistema não mudou ao longo do
histórico. A redação usa o Gemini, que não é determinístico, por isso a reexecução produz uma nova
amostra; o cálculo das métricas sobre os documentos congelados é determinístico.

**Conferência.** `python verificar_distribuicao.py` recalcula o hash de árvore do Git de cada
pasta e o compara com a tabela acima. A rodada inicial da WEGE3 usou alterações não versionadas e
não pode ser reconstituída; ver `PROVENIENCIA.md`.
