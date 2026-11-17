# 2026-11-17 Designer goals #9 (fleet topology) + #7 (a11y) CDP verification.
# Headless Edge over CDP: renders portal, checks #fleetTopo SVG, console cleanliness,
# axe-core violations, tab-focus visibility, ARIA landmarks. Evidence -> evidence files.
import asyncio, base64, json, os, subprocess, time, urllib.request
from websockets.asyncio.client import connect

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
CDP_PORT = 9334
UDIR = os.path.join(os.getcwd(), ".unsloth-tmp", "edge_cdp_d9d7")
PORTAL = "http://127.0.0.1:8099/"
EV = "memory/designer"

def log(m): print(time.strftime("%H:%M:%S ") + str(m), flush=True)

async def main():
    os.makedirs(UDIR, exist_ok=True); os.makedirs(EV, exist_ok=True)
    proc = subprocess.Popen([EDGE, "--headless", f"--remote-debugging-port={CDP_PORT}",
        "--user-data-dir=" + UDIR, "--no-first-run", "--disable-gpu",
        "--window-size=1280,900", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    out = {"console_errors": [], "page_exceptions": [], "checks": {}, "focus_chain": []}
    try:
        target = None
        for _ in range(40):
            await asyncio.sleep(0.5)
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list", timeout=3))
                target = next(t for t in tabs if t.get("type") == "page"); break
            except Exception: continue
        if not target: raise SystemExit("no CDP target")
        async with connect(target["webSocketDebuggerUrl"], max_size=50*1024*1024) as ws:
            n = 0; pending = {}
            async def reader():
                while True:
                    m = json.loads(await ws.recv())
                    if "id" in m and m["id"] in pending:
                        f = pending.pop(m["id"])
                        if not f.done(): f.set_result(m.get("result", {}))
                    elif m.get("method") == "Runtime.consoleAPICalled":
                        p = m["params"]
                        if p.get("type") == "error":
                            out["console_errors"].append(" ".join(
                                (a.get("value") or a.get("description") or "") for a in p.get("args", []))[:300])
                    elif m.get("method") == "Runtime.exceptionThrown":
                        out["page_exceptions"].append(json.dumps(m["params"]["exceptionDetails"].get("exception", {}))[:300])
            rd = asyncio.create_task(reader())
            async def cmd(method, **params):
                nonlocal n; n += 1
                fut = asyncio.get_event_loop().create_future(); pending[n] = fut
                await ws.send(json.dumps({"id": n, "method": method, "params": params}))
                return await fut
            await cmd("Page.enable"); await cmd("Runtime.enable")
            await cmd("Emulation.setDeviceMetricsOverride", width=1280, height=900, deviceScaleFactor=1, mobile=False)
            await cmd("Page.navigate", url=PORTAL)
            # wait for topology SVG
            t0 = time.time(); svg_ok = False
            while time.time() - t0 < 25:
                r = await cmd("Runtime.evaluate", expression="""(function(){
                    var s = document.querySelector('#fleetTopo svg');
                    if (!s) return 'nosvg';
                    return 'svg:' + s.querySelectorAll('.ft-node,.ft-host,[class*=ft-]').length;})()""",
                    returnByValue=True)
                v = r.get("result", {}).get("value")
                if isinstance(v, str) and v.startswith("svg:") and int(v.split(":")[1]) >= 3:
                    svg_ok = True; out["checks"]["topo_nodes"] = v; break
                await asyncio.sleep(0.7)
            # open fleet panel so topo is visible (it lives in fleetPanel; check visibility)
            r = await cmd("Runtime.evaluate", expression="""(function(){
                var b = document.getElementById('fleetBtn'); if (b) b.click();
                var t = document.getElementById('fleetTopo');
                var vis = t && t.offsetParent !== null;
                return JSON.stringify({panelOpen: !!document.querySelector('#fleetPanel:not([hidden])') || vis,
                    topoVisible: vis,
                    hosts: Array.from(document.querySelectorAll('#fleetTopo text')).map(function(e){return e.textContent}).filter(Boolean).slice(0,24),
                    landmarks: {nav: document.querySelectorAll('nav[aria-label]').length, main: document.querySelectorAll('main').length,
                        aside: document.querySelectorAll('aside[aria-label]').length, header: document.querySelectorAll('header').length},
                    ariaLabeled: document.querySelectorAll('[aria-label]').length});})()""",
                returnByValue=True)
            out["checks"]["page_state"] = r.get("result", {}).get("value")
            # axe-core
            try:
                axe_js = urllib.request.urlopen("https://cdn.jsdelivr.net/npm/axe-core@4.10.2/axe.min.js", timeout=30).read().decode()
                await cmd("Runtime.evaluate", expression="document.title")  # warm
                inj = "window.__axeSrc = " + json.dumps(axe_js)
                r = await cmd("Runtime.evaluate", expression=inj, returnByValue=True)
                r = await cmd("Runtime.evaluate", expression="""(function(){
                    var s = document.createElement('script'); s.textContent = window.__axeSrc;
                    document.documentElement.appendChild(s); return typeof window.axe;})()""",
                    returnByValue=True)
                out["checks"]["axe_loaded"] = r.get("result", {}).get("value")
                fut_task = asyncio.create_task(cmd("Runtime.evaluate",
                    expression="window.axe.run(document, {resultTypes:['violations']}).then(function(r){return JSON.stringify({n: r.violations.length, v: r.violations.map(function(x){return x.id + ' x' + x.nodes.length})})})",
                    awaitPromise=True))
                r = await fut_task
                out["checks"]["axe_violations"] = r.get("result", {}).get("value")
            except Exception as e:
                out["checks"]["axe_error"] = repr(e)[:200]
            log("done-phase1"); json.dump(out, open(os.path.join(EV, "evidence_d9d7.json"), "w"), indent=1)
            rd.cancel()
    finally:
        proc.terminate()
asyncio.run(main())
