# capturar_telas.py
#
# Demonstração funcional da aplicação web do FundIA (api.py + frontend/), feita em 11/11/2026.
# Abre a interface real num Microsoft Edge sem janela, controlado pelo protocolo de depuração
# (CDP), aciona o botão de análise e salva capturas de tela e a trilha exportada pela própria
# interface. Não altera nenhum módulo do sistema: só opera o navegador.
#
# Pré-requisitos: backend em http://localhost:8000 (uvicorn api:app --port 8000) e frontend em
# http://localhost:5173 (npm run dev --prefix frontend).
#
# Uso:  python avaliacao/demonstracao_web_2026-11-11/capturar_telas.py [TICKER]
#
# Não é experimento científico: é uma execução única, sem leitura manual da narrativa.

import base64
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

import websocket  # websocket-client

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
URL = "http://localhost:5173"
PORTA = 9333
AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "capturas_originais")
TICKER = (sys.argv[1] if len(sys.argv) > 1 else "WEGE3").upper()
LARGURA, ALTURA, ESCALA = 1280, 900, 2

os.makedirs(SAIDA, exist_ok=True)
perfil = tempfile.mkdtemp(prefix="fundia_edge_")
proc = subprocess.Popen([EDGE, "--headless=new", f"--remote-debugging-port={PORTA}",
                         f"--user-data-dir={perfil}", f"--window-size={LARGURA},{ALTURA}",
                         "--hide-scrollbars", "about:blank"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

alvo = None
for _ in range(40):
    try:
        abas = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORTA}/json", timeout=2))
        alvo = [a for a in abas if a.get("type") == "page"][0]
        break
    except Exception:
        time.sleep(0.5)
if not alvo:
    proc.kill()
    sys.exit("Edge não respondeu na porta de depuração.")

ws = websocket.create_connection(alvo["webSocketDebuggerUrl"], timeout=120, suppress_origin=True)
_id = 0


def cdp(metodo, **params):
    global _id
    _id += 1
    ws.send(json.dumps({"id": _id, "method": metodo, "params": params}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == _id:
            if "error" in msg:
                raise RuntimeError(f"{metodo}: {msg['error']}")
            return msg.get("result", {})


def js(expr):
    r = cdp("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
    return r.get("result", {}).get("value")


def foto(nome, clip=None, pagina_inteira=False):
    params = {"format": "png"}
    if clip:
        params["clip"] = dict(clip, scale=1)
        params["captureBeyondViewport"] = True
    elif pagina_inteira:
        m = cdp("Page.getLayoutMetrics")["cssContentSize"]
        params["clip"] = {"x": 0, "y": 0, "width": m["width"], "height": m["height"], "scale": 1}
        params["captureBeyondViewport"] = True
    dados = cdp("Page.captureScreenshot", **params)["data"]
    caminho = os.path.join(SAIDA, nome)
    with open(caminho, "wb") as f:
        f.write(base64.b64decode(dados))
    print("captura:", nome)


registro = {"ticker": TICKER, "url": URL, "inicio_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "viewport": [LARGURA, ALTURA], "escala": ESCALA}
try:
    cdp("Page.enable")
    cdp("Runtime.enable")
    cdp("Emulation.setDeviceMetricsOverride", width=LARGURA, height=ALTURA,
        deviceScaleFactor=ESCALA, mobile=False)
    cdp("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": "light"}])
    cdp("Browser.setDownloadBehavior", behavior="allow", downloadPath=SAIDA)
    cdp("Page.navigate", url=URL)

    # Espera a interface confirmar a API (botão de análise habilitado)
    for _ in range(60):
        if js("(()=>{const b=document.querySelector('.botao-analisar');return !!b && !b.disabled})()"):
            break
        time.sleep(1)
    else:
        raise RuntimeError("Botão de análise não ficou disponível (API indisponível?).")

    # Preenche o código pelo próprio campo da barra lateral, se for diferente do padrão
    js("""(()=>{const i=document.querySelector('.sidebar input[type=text], aside input[type=text], input[placeholder^="Ex"]');
          if(!i) return false;
          const set=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
          set.call(i,%s); i.dispatchEvent(new Event('input',{bubbles:true})); return i.value})()""" % json.dumps(TICKER))
    time.sleep(0.5)
    registro["campo_ticker"] = js("document.querySelector('input[placeholder^=\"Ex\"]')?.value")
    foto("01_tela_inicial.png")

    # Aciona a análise pelo botão da interface
    js("document.querySelector('.botao-analisar').click()")
    t0 = time.time()
    fotografou_progresso = False
    estado = None
    while time.time() - t0 < 420:
        estado = js("""(()=>{if(document.querySelector('.alerta-erro')) return 'erro';
                             if(document.querySelector('details.auditoria')) return 'resultado';
                             return 'rodando'})()""")
        if estado != "rodando":
            break
        if not fotografou_progresso and time.time() - t0 > 6:
            foto("02_progresso.png")
            fotografou_progresso = True
        time.sleep(2)
    registro["duracao_s"] = round(time.time() - t0, 1)
    registro["estado_final"] = estado

    if estado == "erro":
        registro["erro"] = js("document.querySelector('.alerta-erro').innerText")
        foto("03_erro.png")
    elif estado == "resultado":
        time.sleep(1.5)
        js("window.scrollTo(0,0)")
        foto("03_analise_topo.png")
        foto("04_analise_pagina_inteira.png", pagina_inteira=True)
        with open(os.path.join(SAIDA, "texto_da_pagina.txt"), "w", encoding="utf-8") as f:
            f.write(js("document.querySelector('main').innerText") or "")

        # Abre o painel de auditoria pelo próprio controle da página
        js("document.querySelector('details.auditoria summary').click()")
        time.sleep(1)
        registro["selo"] = js("document.querySelector('details.auditoria .selo')?.innerText")
        linhas = js("""Array.from(document.querySelectorAll('.tabela-auditoria tbody tr')).map(tr=>
                         Array.from(tr.children).map(td=>td.innerText.trim()))""") or []
        registro["linhas_trilha"] = len(linhas)
        with open(os.path.join(SAIDA, "trilha_na_tela.json"), "w", encoding="utf-8") as f:
            json.dump(linhas, f, ensure_ascii=False, indent=1)
        caixa = js("""(()=>{const r=document.querySelector('details.auditoria').getBoundingClientRect();
                          return {x:r.left+window.scrollX,y:r.top+window.scrollY,width:r.width,height:r.height}})()""")
        registro["altura_painel_css"] = caixa["height"]
        foto("05_auditoria_painel_completo.png", clip=caixa)
        foto("06_auditoria_recorte.png", clip=dict(caixa, height=min(caixa["height"], 1150)))
        foto("07_pagina_inteira_com_auditoria.png", pagina_inteira=True)

        # Exporta a trilha pelo botão da interface (arquivo gerado pelo próprio frontend)
        js("""(()=>{const b=Array.from(document.querySelectorAll('.auditoria-acoes button'))
                    .find(x=>x.innerText.includes('Exportar trilha')); if(b) b.click(); return !!b})()""")
        time.sleep(3)
        registro["arquivos"] = sorted(os.listdir(SAIDA))
finally:
    registro["fim_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(os.path.join(AQUI, "execucao_demonstracao.json"), "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, indent=1)
    try:
        ws.close()
    except Exception:
        pass
    proc.terminate()
    print(json.dumps({k: v for k, v in registro.items() if k != "arquivos"}, ensure_ascii=False))
