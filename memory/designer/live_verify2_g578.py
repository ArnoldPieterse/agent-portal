#!/usr/bin/env python3
# 2026-11-17 (Orchestrator seat): corrected live probe v2 - forced overflow via absolute div,
# tabwalk via CDP Input.dispatchKeyEvent, landmark inventory, input visibility audit.
import asyncio, base64, json, os, subprocess, time, urllib.request
from websockets.asyncio.client import connect

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
CDP_PORT = 9335
UDIR = os.path.join(os.getcwd(), ".unsloth-tmp", "edge_cdp_g578b")
PORTAL = "http://127.0.0.1:8099/"
EVDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "breakpoint-evidence")
os.makedirs(EVDIR, exist_ok=True)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live-verify2-2026-11-17.json")

class CDP:
    def __init__(self, ws):
        self.ws = ws; self.n = 0; self.pending = {}
    async def cmd(self, method, **params):
        self.n += 1; i = self.n
        fut = asyncio.get_event_loop().create_future()
        self.pending[i] = fut
        await self.ws.send(json.dumps({"id": i, "method": method, "params": params}))
        return await asyncio.wait_for(fut, 20)
    async def reader(self):
        while True:
            try: m = json.loads(await self.ws.recv())
            except Exception: return
            if "id" in m and m["id"] in self.pending:
                f = self.pending.pop(m["id"])
                if not f.done(): f.set_result(m.get("result", {}))
    async def js(self, expr):
        r = await self.cmd("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
        if "exceptionDetails" in r: raise RuntimeError(str(r["exceptionDetails"])[:200])
        return (r.get("result") or {}).get("value")
    async def key(self, k):
        await self.cmd("Input.dispatchKeyEvent", type="keyDown", key=k, code=k, windowsVirtualKeyCode=9)
        await self.cmd("Input.dispatchKeyEvent", type="keyUp", key=k, code=k, windowsVirtualKeyCode=9)

JS_LANDMARKS = r'''
(() => {
  const inv = {};
  for (const t of ["header","nav","main","aside","footer"]) inv[t] = document.querySelectorAll(t).length;
  inv.region_labeled = [...document.querySelectorAll('[role=region][aria-label]')].map(e=>e.getAttribute("aria-label"));
  inv.maybe_cols = [...document.querySelectorAll("section,div")].filter(e=>{
    const r=e.getBoundingClientRect(); const s=getComputedStyle(e);
    return r.width>200 && r.height>400 && (s.position==="sticky"||e.id); }).slice(0,12)
      .map(e=>({id:e.id||null, cls:typeof e.className=="string"?e.className.slice(0,40):null, role:e.getAttribute("role"), al:e.getAttribute("aria-label")}));
  return inv;
})()'''

JS_INPUTS = r'''
(() => {
  return [...document.querySelectorAll("input,select,textarea")].map(e => {
    const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
    const visible = r.width>0 && r.height>0 && s.visibility!=="hidden" && s.display!=="none";
    const labeled = !!( (e.id && document.querySelector(`label[for="${e.id}"]`)) || e.closest("label")
      || e.getAttribute("aria-label") || e.placeholder );
    return { id: e.id || e.tagName, type: e.type||null, visible, labeled,
             ph: (e.placeholder||"").slice(0,24), title: (e.title||"").slice(0,24) };
  }).filter(x => x.visible);
})()'''

JS_TABWALK = r'''(() => { const e=document.activeElement; if(!e||e===document.body) return null;
  const s=getComputedStyle(e); return {tag:e.tagName.toLowerCase(), id:e.id||null,
    outlineW:s.outlineWidth, outlineC:s.outlineColor, shadow:s.boxShadow!=="none"}; })()'''

async def main():
    os.makedirs(UDIR, exist_ok=True)
    proc = subprocess.Popen([EDGE, "--headless", f"--remote-debugging-port={CDP_PORT}",
                             "--user-data-dir=" + UDIR, "--no-first-run", "--disable-gpu",
                             "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    res = {"ts": time.strftime("%Y-%m-%d %H:%M:%S")}
    reader = None
    try:
        target = None
        for _ in range(40):
            await asyncio.sleep(0.5)
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list", timeout=3))
                target = next(t for t in tabs if t.get("type") == "page"); break
            except Exception: pass
        if not target: raise SystemExit("no CDP target")
        async with connect(target["webSocketDebuggerUrl"], max_size=50*1024*1024) as ws:
            cdp = CDP(ws)
            reader = asyncio.create_task(cdp.reader())
            await cdp.cmd("Runtime.enable"); await cdp.cmd("Page.enable")
            await cdp.cmd("Page.navigate", url=PORTAL)
            for _ in range(24): await asyncio.sleep(0.5)

            # 1) forced overflow, absolute (contributes to scrollWidth), at 375
            await cdp.cmd("Emulation.setDeviceMetricsOverride", width=375, height=800, deviceScaleFactor=1, mobile=True)
            await asyncio.sleep(1.0)
            base = await cdp.js("({sw: document.documentElement.scrollWidth, iw: window.innerWidth})")
            await cdp.js("const d=document.createElement('div');d.id='__force';d.style.cssText='position:absolute;top:0;left:0;width:900px;height:40px;background:red;z-index:99999';document.body.appendChild(d);1")
            await asyncio.sleep(0.8)
            forced = await cdp.js("({sw: document.documentElement.scrollWidth, iw: window.innerWidth})")
            r = await cdp.cmd("Page.captureScreenshot", format="png")
            with open(os.path.join(EVDIR, "live2-375-forced-overflow.png"), "wb") as f: f.write(base64.b64decode(r["data"]))
            res["forced_overflow"] = {"base": base, "forced": forced,
                                      "gate_would_fail": (forced["sw"] - forced["iw"]) > 2}
            await cdp.js("document.getElementById('__force')?.remove();1")

            # 2) tabwalk via real CDP input at 1280
            await cdp.cmd("Emulation.setDeviceMetricsOverride", width=1280, height=900, deviceScaleFactor=1, mobile=False)
            await asyncio.sleep(0.8)
            await cdp.js("document.body.focus();1")
            walk = []
            for _ in range(30):
                await cdp.key("Tab"); await asyncio.sleep(0.12)
                a = await cdp.js(JS_TABWALK)
                if not a: break
                walk.append(a)
            res["tabwalk"] = {"count": len(walk), "invisible": [w for w in walk if w["outlineW"]=="0px" and not w["shadow"]], "sample": walk[:15]}

            # 3) landmarks + visible-input audit
            res["landmarks"] = await cdp.js(JS_LANDMARKS)
            vis_inputs = await cdp.js(JS_INPUTS)
            res["visible_inputs"] = vis_inputs
            res["unlabeled_visible"] = [v["id"] for v in vis_inputs if not v["labeled"]]
    finally:
        try: reader.cancel()
        except Exception: pass
        proc.terminate()
    with open(OUT, "w", encoding="utf-8") as f: json.dump(res, f, indent=1)
    print(f"overflow base={res['forced_overflow']['base']} forced={res['forced_overflow']['forced']} would_fail={res['forced_overflow']['gate_would_fail']} | tab={res['tabwalk']['count']} invis={len(res['tabwalk']['invisible'])} | unlabeled_visible={len(res['unlabeled_visible'])}")

if __name__ == "__main__":
    asyncio.run(main())