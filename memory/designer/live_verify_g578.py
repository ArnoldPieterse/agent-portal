#!/usr/bin/env python3
# 2026-11-17 (Orchestrator seat): live CDP verification for Designer goals #5, #7, #8.
# Runs on the non-sandbox Studio/White seat against loopback :8099 (Designer sandbox blocks sockets).
# Evidence: memory/designer/live-verify-g578-2026-11-17.json + screenshots in breakpoint-evidence/.
import asyncio, base64, json, os, subprocess, sys, time, urllib.request
from websockets.asyncio.client import connect

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
CDP_PORT = 9334
UDIR = os.path.join(os.getcwd(), ".unsloth-tmp", "edge_cdp_g578")
PORTAL = "http://127.0.0.1:8099/"
EVDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "breakpoint-evidence")
os.makedirs(EVDIR, exist_ok=True)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live-verify-g578-2026-11-17.json")

class CDP:
    def __init__(self, ws):
        self.ws = ws; self.n = 0; self.pending = {}; self.events = []
    async def cmd(self, method, **params):
        self.n += 1; i = self.n
        fut = asyncio.get_event_loop().create_future()
        self.pending[i] = fut
        await self.ws.send(json.dumps({"id": i, "method": method, "params": params}))
        return await asyncio.wait_for(fut, 20)
    async def reader(self):
        while True:
            try:
                m = json.loads(await self.ws.recv())
            except Exception:
                return
            if "id" in m and m["id"] in self.pending:
                f = self.pending.pop(m["id"]) 
                if not f.done(): f.set_result(m.get("result", {}))
            else:
                self.events.append(m)
    async def js(self, expr, timeout=10):
        r = await self.cmd("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
        if "exceptionDetails" in r: raise RuntimeError(str(r["exceptionDetails"])[:200])
        return (r.get("result") or {}).get("value")
    def take_errors(self):
        errs = []
        for m in self.events:
            me = m.get("method")
            if me == "Runtime.consoleAPICalled" and m["params"].get("type") == "error":
                a = m["params"].get("args", [])
                errs.append(" ".join(str(x.get("value", x.get("description", ""))) for x in a)[:200])
            elif me == "Runtime.exceptionThrown":
                d = m["params"]["exceptionDetails"]
                errs.append((d.get("text") or "") + " " + str((d.get("exception") or {}).get("description", ""))[:200])
            elif me == "Log.entryAdded" and m["params"]["entry"].get("level") == "error":
                errs.append(str(m["params"]["entry"].get("message", ""))[:200])
        self.events = [m for m in self.events if m.get("method") not in
                       ("Runtime.consoleAPICalled", "Runtime.exceptionThrown", "Log.entryAdded")]
        return errs

async def shot(cdp, path):
    r = await cdp.cmd("Page.captureScreenshot", format="png")
    with open(path, "wb") as f: f.write(base64.b64decode(r["data"]))

JS_MEASURE = r'''
(() => {
  const iw = document.documentElement.clientWidth || window.innerWidth;
  const sw = document.documentElement.scrollWidth;
  const vis = (sel) => { const e = document.querySelector(sel); if (!e) return false;
    const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && s.visibility !== "hidden" && s.display !== "none"; };
  return { scrollWidth: sw, innerWidth: iw, overflowPx: sw - iw,
           header: vis("header"), agentList: vis("#agentList"), chatCol: vis("#chatCol") };
})()'''

JS_A11Y = r'''
(() => {
  const regions = [...document.querySelectorAll('section[role=region][aria-label]')].map(e => e.getAttribute("aria-label"));
  const navs = document.querySelectorAll("nav").length;
  const inputsUnlabeled = [...document.querySelectorAll("input,select,textarea")].filter(e => {
    if (e.type === "hidden" || e.disabled) return false;
    const id = e.id; 
    if (id && document.querySelector(`label[for="${id}"]`)) return false;
    if (e.closest("label")) return false;
    if (e.getAttribute("aria-label") || e.getAttribute("title")) return false;
    return true;
  }).map(e => e.id || e.tagName);
  const live = document.querySelectorAll("[aria-live]").length;
  const btnsNoName = [...document.querySelectorAll("button")].filter(b => !b.textContent.trim() && !b.getAttribute("aria-label") && !b.title).length;
  return { regions, navs, inputsUnlabeled, live, btnsNoName };
})()'''

JS_TABWALK = r'''
(async () => {
  const out = [];
  const el = document.activeElement;
  for (let i = 0; i < 25; i++) {
    const ev = new KeyboardEvent("keydown", {key: "Tab", code: "Tab", keyCode: 9, bubbles: true});
    document.activeElement.dispatchEvent(ev);
    await new Promise(r => setTimeout(r, 40));
    const a = document.activeElement;
    if (!a || a === document.body) break;
    const s = getComputedStyle(a);
    out.push({ tag: a.tagName.toLowerCase(), id: a.id || null,
               outlineW: s.outlineWidth, outlineC: s.outlineColor, boxShadow: s.boxShadow !== "none" });
  }
  return out;
})()'''

JS_TYPEO = r'''
(() => {
  const sample = [...document.querySelectorAll("body, h1, h2, h3, p, button, .ah, #queueHead, #actBody, .msg, li, span")];
  const seen = new Set(); const rows = [];
  for (const e of sample) {
    if (!e.textContent.trim()) continue;
    const s = getComputedStyle(e);
    const key = e.tagName + "|" + [...e.classList].join(".") + "|" + s.fontSize;
    if (seen.has(key)) continue; seen.add(key);
    rows.push({ sel: e.tagName.toLowerCase() + (e.id ? "#"+e.id : "") + (e.className && typeof e.className==="string" ? "."+e.className.trim().split(/\s+/).join(".") : ""),
      fontSize: s.fontSize, lineHeight: s.lineHeight, weight: s.fontWeight,
      transform: s.textTransform, letterSpacing: s.letterSpacing });
  }
  return rows;
})()'''

async def main():
    os.makedirs(UDIR, exist_ok=True)
    proc = subprocess.Popen([EDGE, "--headless", f"--remote-debugging-port={CDP_PORT}",
                             "--user-data-dir=" + UDIR, "--no-first-run", "--disable-gpu",
                             "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    res = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "portal": PORTAL}
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
            await cdp.cmd("Runtime.enable"); await cdp.cmd("Log.enable"); await cdp.cmd("Page.enable")
            await cdp.cmd("Page.navigate", url=PORTAL)
            for _ in range(30): await asyncio.sleep(0.5)
            ready = await cdp.js("document.readyState")
            res["readyState"] = ready

            # ---- G5: breakpoints ----
            g5 = {}
            for w in (375, 768):
                await cdp.cmd("Emulation.setDeviceMetricsOverride", width=w, height=800, deviceScaleFactor=1, mobile=(w==375))
                await asyncio.sleep(1.2)
                m = await cdp.js(JS_MEASURE)
                errs = cdp.take_errors()
                ok = (m["overflowPx"] <= 2) and not errs and m["header"] and m["agentList"] and m["chatCol"]
                p = os.path.join(EVDIR, f"live-{w}.png"); await shot(cdp, p)
                g5[str(w)] = {**m, "consoleErrors": errs, "pass": ok, "screenshot": p}
            # forced overflow at 375
            await cdp.cmd("Emulation.setDeviceMetricsOverride", width=375, height=800, deviceScaleFactor=1, mobile=True)
            await cdp.js("const d=document.createElement('div');d.id='__force';d.style.cssText='position:fixed;top:0;left:0;width:900px;height:40px;background:red;z-index:99999';document.body.appendChild(d);1")
            await asyncio.sleep(0.6)
            m2 = await cdp.js(JS_MEASURE)
            p2 = os.path.join(EVDIR, "live-375-forced-overflow.png"); await shot(cdp, p2)
            g5["forced_overflow_375"] = {**m2, "expected": "FAIL", "got_fail": m2["overflowPx"] > 2,
                                         "screenshot": p2}
            await cdp.js("document.getElementById('__force')?.remove();1")
            res["g5_breakpoint_gate"] = g5

            # ---- G7: focus + ARIA (desktop width) ----
            await cdp.cmd("Emulation.setDeviceMetricsOverride", width=1280, height=900, deviceScaleFactor=1, mobile=False)
            await asyncio.sleep(0.8)
            a11y = await cdp.js(JS_A11Y)
            walk = await cdp.js(JS_TABWALK)
            invisible = [w for w in walk if not (w["outlineW"] not in ("0px",) or w["boxShadow"])]
            res["g7_focus_aria"] = {"landmarks": a11y, "tabwalk_count": len(walk),
                                    "tabwalk_invisible_focus": invisible,
                                    "tabwalk_sample": walk[:12]}

            # ---- G8: computed typography ----
            rows = await cdp.js(JS_TYPEO)
            viol = []
            weights = set()
            for r in rows:
                try:
                    fs = float(r["fontSize"].rstrip("px")); lh = float(r["lineHeight"].rstrip("px"))
                    ratio = lh / fs if fs else 0
                except Exception:
                    ratio = -1
                weights.add(r["weight"])
                is_icon = r["sel"] in ("#attach",) or "button" in r["sel"]
                if ratio > 0 and not (1.2 <= ratio <= 1.6) and not is_icon:
                    viol.append({"sel": r["sel"], "ratio": round(ratio, 3)})
                if r["transform"] == "uppercase":
                    try:
                        ls = float(r["letterSpacing"].rstrip("px")); fs2 = float(r["fontSize"].rstrip("px"))
                        if fs2 and (ls / fs2) < 0.05: viol.append({"sel": r["sel"], "uppercase_ls_ratio": round(ls/fs2, 4)})
                    except Exception: pass
            res["g8_typography"] = {"rows_sampled": len(rows), "violations": viol,
                                    "font_weights_seen": sorted(weights),
                                    "pass": not viol and len({w for w in weights if w not in ("normal", "400")}) >= 2}
            res["g8_rows"] = rows
    finally:
        try: reader.cancel()
        except Exception: pass
        proc.terminate()
    with open(OUT, "w", encoding="utf-8") as f: json.dump(res, f, indent=1)
    g5ok = all(g5[str(w)]["pass"] for w in (375, 768)) and g5["forced_overflow_375"]["got_fail"]
    print(f"G5={'PASS' if g5ok else 'FAIL'} G7_regions={res.get('g7_focus_aria',{}).get('landmarks',{}).get('regions')} "
          f"tabwalk={res.get('g7_focus_aria',{}).get('tabwalk_count')} inv={len(res.get('g7_focus_aria',{}).get('tabwalk_invisible_focus',[]))} "
          f"G8={'PASS' if res.get('g8_typography',{}).get('pass') else 'FAIL'} viol={len(res.get('g8_typography',{}).get('violations',[]))}")

if __name__ == "__main__":
    asyncio.run(main())
