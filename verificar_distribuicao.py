"""Conferência da distribuição pública do FundIA (TCC 2), sem rede e sem chave de API.

    python verificar_distribuicao.py            # todas as conferências
    python verificar_distribuicao.py --rapido   # sem o teste de falso positivo do auditor

Confere, sem gravar nenhum arquivo:
  1. os SHA-256 registrados nos manifestos dos artefatos;
  2. a identidade dos estados de código em estados_avaliados/ e em modulos/ com as árvores
     registradas em PROVENIENCIA.md (hash de árvore do Git, calculado aqui sem o Git);
  3. a árvore do primeiro commit público, quando o diretório .git está presente;
  4. o recálculo dos resumos e análises a partir dos artefatos congelados, com os scripts
     originais, sem alterá-los.

A conferência original da análise RAGAS compara os arquivos brutos com o commit d78d5a5 do
histórico privado, que não está neste repositório. Aqui essa etapa é substituída pela
conferência contra verificacao/ragas_congelados_d78d5a5.sha256; o restante do cálculo é o do
script original. Ver REPRODUTIBILIDADE.md e PROVENIENCIA.md.
"""
import glob
import hashlib
import importlib.util
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True
RAIZ = os.path.dirname(os.path.abspath(__file__))
os.chdir(RAIZ)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

PRIMEIRO_COMMIT = "d69e5838e9a6766d6b13ee6a9ed4d175984eee62"
ARVORE_PRIMEIRO_COMMIT = "21306229abad686b2fe526fc0de1939b0e8e4657"
ESTADOS = {  # pasta -> árvore de modulos/ no commit correspondente do histórico privado
    "estados_avaliados/1a08d00/modulos": "f4cd20febe91954fe1b2ae41662852e0dc182f64",
    "estados_avaliados/75dbfc4/modulos": "3bf40180a5625960fa9193e0b3cab83d7c05b694",
    "estados_avaliados/183e69f/modulos": "6b23d723d03327e0942cbfe61e09748dd43f8b58",
    "estados_avaliados/e4d96e1/modulos": "f1dc75c68a6a74f29f27106aac5fbae03b124b98",
    "estados_avaliados/269f3f1/modulos": "2aa495241569c7dca97d117e62af5b47439673fd",
    "modulos": "ed0f5af5b126287861a11d17cc9e56f79545f37c",  # 777b256 a 29aa6b1
}
ENV = {k: v for k, v in os.environ.items() if k not in ("GEMINI_API_KEY", "GOOGLE_API_KEY")}
ENV["PYTHONIOENCODING"] = "utf-8"
resultados = []


def registrar(nome, ok, detalhe):
    resultados.append((nome, ok))
    print(f"[{'OK ' if ok else 'ERRO'}] {nome}: {detalhe}")


def sha256(caminho):
    with open(caminho, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def conferir_pares(nome, pares):
    ruins = [p for h, p in pares if not os.path.exists(p) or sha256(p) != h]
    registrar(nome, not ruins and bool(pares), f"{len(pares) - len(ruins)}/{len(pares)} conferem"
              + (f"; divergentes ou ausentes: {ruins[:5]}" if ruins else ""))


# 1. Manifestos SHA-256 ------------------------------------------------------------------
def manifestos():
    base = "avaliacao/ragas/coleta_tcc2/"
    pares = []
    for linha in open(base + "SHA256_COLETA.txt", encoding="utf-8"):
        m = re.match(r"^([0-9a-f]{64})\s+\*?(.+)$", linha.strip())
        if m:
            h, f = m.groups()
            cands = [f, base + f, "avaliacao/ragas/" + f]
            pares.append((h, next((c for c in cands if os.path.exists(c)), base + f)))
    conferir_pares("Coleta RAGAS (SHA256_COLETA.txt)", pares)

    pares = []
    for s in sorted(glob.glob("avaliacao/validacao_manual/*/*.sha256")):
        s = s.replace(os.sep, "/")
        pares.append((open(s, encoding="utf-8").read().split()[0], s[: -len(".sha256")]))
    conferir_pares("Validação manual (*.sha256)", pares)

    for nome, pasta in (("Execução exploratória (MANIFESTO.md)", "avaliacao/execucao_exploratoria_2026-10-18/"),
                        ("Demonstração web (MANIFESTO.md)", "avaliacao/demonstracao_web_2026-11-11/")):
        pares = []
        for linha in open(pasta + "MANIFESTO.md", encoding="utf-8"):
            m = re.match(r"^\|\s*`([^`]+)`[^|]*\|\s*`([0-9a-f]{64})`\s*\|\s*$", linha.strip())
            if m and os.path.exists(pasta + m.group(1)):  # só os arquivos da própria pasta
                pares.append((m.group(2), pasta + m.group(1)))
        conferir_pares(nome, pares)

    pares = []
    for linha in open("verificacao/ragas_congelados_d78d5a5.sha256", encoding="utf-8"):
        if not linha.startswith("#") and linha.strip():
            h, p = linha.rstrip("\n").split("  ", 1)
            pares.append((h, p))
    conferir_pares("Resultados RAGAS brutos e anotações (d78d5a5)", pares)


# 2. Estados de código -------------------------------------------------------------------
def arvore_git(pasta, normalizar_eol=False):
    """Hash da árvore do Git (SHA-1) para os arquivos de uma pasta, sem usar o Git.

    Com normalizar_eol, CRLF vira LF antes do cálculo, como o Git faz ao versionar arquivos de
    texto. Serve ao modulos/ da raiz, que um checkout com core.autocrlf=true grava com CRLF; as
    pastas de estados_avaliados/ têm "-text" no .gitattributes e são conferidas byte a byte.
    """
    entradas = []
    for nome in os.listdir(pasta):
        if nome == "__pycache__" or nome.endswith(".pyc"):
            continue
        caminho = os.path.join(pasta, nome)
        if os.path.isdir(caminho):
            entradas.append((nome + "/", b"40000", nome, bytes.fromhex(arvore_git(caminho, normalizar_eol))))
        else:
            with open(caminho, "rb") as fh:
                dados = fh.read()
            if normalizar_eol:
                dados = dados.replace(b"\r\n", b"\n")
            blob = hashlib.sha1(b"blob %d\0" % len(dados) + dados).digest()
            entradas.append((nome, b"100644", nome, blob))
    corpo = b"".join(modo + b" " + nome.encode("utf-8") + b"\0" + h
                     for _, modo, nome, h in sorted(entradas, key=lambda e: e[0].encode("utf-8")))
    return hashlib.sha1(b"tree %d\0" % len(corpo) + corpo).hexdigest()


def estados():
    for pasta, esperado in ESTADOS.items():
        obtido = arvore_git(pasta, normalizar_eol=(pasta == "modulos"))
        registrar(f"Árvore de {pasta}", obtido == esperado, obtido[:12] + ("" if obtido == esperado
                                                                          else f" (esperado {esperado[:12]})"))


def primeiro_commit():
    if not os.path.isdir(".git"):
        print("[ -- ] Primeiro commit público: sem diretório .git (cópia sem histórico); não conferido")
        return
    r = subprocess.run(["git", "rev-parse", PRIMEIRO_COMMIT + "^{tree}"], capture_output=True, text=True)
    registrar("Árvore do primeiro commit público", r.stdout.strip() == ARVORE_PRIMEIRO_COMMIT,
              (r.stdout.strip() or r.stderr.strip())[:40])


# 3. Recálculo com os scripts originais --------------------------------------------------
def rodar(*args):
    return subprocess.run([sys.executable, "-B", *args], capture_output=True, text=True, encoding="utf-8",
                          env=ENV, cwd=RAIZ)


def recalculos(rapido):
    r = rodar("avaliacao/flash_pro/resumir_experimento_flash_pro.py", "verificar")
    registrar("Resumo Flash × Pro", r.returncode == 0, r.stdout.strip().splitlines()[-1][:70] if r.stdout else r.stderr[-200:])

    r = rodar("avaliacao/ragas/avaliacao_tcc2/sintese/sintetizar_resultados_tcc2.py", "verificar")
    registrar("Síntese RAGAS", r.returncode == 0, r.stdout.strip()[:70] or r.stderr[-200:])

    analise_ragas()

    reg = "avaliacao/ragas/avaliacao_tcc2/exatidao_emenda5/resultado_exatidao_emenda5.json"
    import json
    resumo = json.load(open(reg, encoding="utf-8"))["resumo"]
    esperados = [resumo["original"]["correto_sobre_aplicaveis"], resumo["emenda5"]["correto_sobre_aplicaveis"]]
    r = rodar("avaliacao/ragas/avaliacao_tcc2/exatidao_emenda5/gerar_exatidao_emenda5.py")
    ok = r.returncode == 0 and all(f"CORRETO/aplicáveis {e}" in r.stdout for e in esperados) \
        and "nada foi gravado" in r.stdout
    registrar("Exatidão com a Emenda 5 (conferência)", ok,
              f"original {esperados[0]}, Emenda 5 {esperados[1]}" if ok else (r.stdout + r.stderr)[-300:])

    r = rodar("avaliacao/testar_auditor_plantado.py")
    m = re.search(r"RESUMO: (\d+)/(\d+)", r.stdout)
    registrar("Frases plantadas (auditor)", bool(m) and m.group(1) == m.group(2), m.group(0) if m else r.stderr[-200:])

    if rapido:
        print("[ -- ] Falso positivo do auditor: omitido (--rapido)")
        return
    r = rodar("avaliacao/testar_falso_positivo_auditor.py")
    chave = lambda t: [l.rstrip() for l in t.splitlines()
                       if l.startswith("[Controle]") or l.lstrip().startswith(("Percentuais:", "Moedas:"))]
    arquivado = open("avaliacao/resultado_falso_positivo_2026-07-19.txt", encoding="utf-8").read()
    ok = r.returncode == 0 and chave(r.stdout) == chave(arquivado) and len(chave(arquivado)) == 5
    registrar("Falso positivo do auditor", ok, "idêntico ao resultado arquivado em 19/07/2026" if ok
              else "difere do arquivado")


def analise_ragas():
    caminho = "avaliacao/ragas/avaliacao_tcc2/analise/analisar_resultados_ragas.py"
    spec = importlib.util.spec_from_file_location("analisar_resultados_ragas", caminho)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    def conferir_congelados_sem_git():
        """Mesmas garantias da função original, contra o manifesto SHA-256 em vez do commit."""
        manifesto = {}
        for linha in open("verificacao/ragas_congelados_d78d5a5.sha256", encoding="utf-8"):
            if not linha.startswith("#") and linha.strip():
                h, p = linha.rstrip("\n").split("  ", 1)
                manifesto[p] = h
        comport = "avaliacao/ragas/avaliacao_tcc2/comportamento"
        brutos = sorted(p for p in manifesto if p.startswith(mod.DIR_BRUTOS + "/"))
        assert len(brutos) == mod.N_BRUTOS, f"esperados {mod.N_BRUTOS} brutos no manifesto, há {len(brutos)}"
        em_disco = sorted(os.path.relpath(os.path.join(r, f), RAIZ).replace(os.sep, "/")
                          for d in (mod.DIR_BRUTOS, comport) for r, _, fs in os.walk(d) for f in fs)
        assert em_disco == sorted(manifesto), "arquivos em disco diferem do manifesto"
        for p in em_disco:
            assert sha256(p) == manifesto[p], f"conteúdo difere do manifesto: {p}"
        linhas = "".join(f"{manifesto[p]}  {p}\n" for p in brutos)
        return hashlib.sha256(linhas.encode("utf-8")).hexdigest()

    mod.conferir_congelados = conferir_congelados_sem_git
    try:
        saidas = mod.calcular()
        difs = [n for n, c in saidas.items() if open(os.path.join(mod.AQUI, n), "rb").read() != c]
        registrar("Análise RAGAS (3 saídas)", not difs, "idênticas às versionadas" if not difs else f"diferem: {difs}")
    except AssertionError as e:
        registrar("Análise RAGAS (3 saídas)", False, str(e))


def main():
    rapido = "--rapido" in sys.argv[1:]
    print("Conferência da distribuição pública do FundIA (TCC 2)\n")
    manifestos()
    estados()
    primeiro_commit()
    recalculos(rapido)
    falhas = [n for n, ok in resultados if not ok]
    print(f"\n{len(resultados) - len(falhas)}/{len(resultados)} conferências corretas"
          + (f"; falharam: {falhas}" if falhas else ""))
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
