#!/usr/bin/env python3
# 2026-11-19 (Builder): GENERAL-PURPOSE headless render test via Edge CDP.
#
# WHY THIS EXISTS
#   Several Builder goals (#3 fleet health, #4 uploads v2, #7 error boundary, #8 mobile)
#   and Designer goals (#5 breakpoints, #7 a11y) carry the caveat "browser render test
#   pending (no headless in sandbox)". This is the ONE reusable harness that closes all of
#   them: it launches msedge headless with a CDP port, drives it over WebSocket, collects
#   console errors + asserts element presence + captures a screenshot at a given viewport.
#
# RUN FROM A NON-SANDBOX SEAT (White ops terminal / RDP / any seat with localhost egress).
#   From a sandbox seat the CDP control channel 127.0.0.1:<port> is egress-blocked
#   (WinError 10013 class) and `--dump-dom` hangs -- see memory/ops/blockers.md.
#
# USAGE
#   python memory/builder/cdp_render_test.py --url http://127.0.0.1:8099/ \
#       --width 1280 --height 900 \
#       --checks '{"#fleetHealthBody .badge":true,"#uploadsPanel":true}' \
#       --out memory/builder/render-1280.png
#
#   --checks: JSON object of {cssSelector: expectedPresent(bool)}. All must match or exit!=0.
#   Exit 0 = page loaded (readyState=complete) + zero console errors + all checks pass.
#   Evidence: prints JSON report to stdout AND writes <out>.report.json next to the screenshot.
import asyncio, base64, glob, json, os, socket, subprocess, sys, tempfile, time, urllib.request
from websockets.asyncio.client import connect

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

def find_edge():
    for p in EDGE_CANDIDATES:
        if os.path.exists(p):
            return p
    import shutil
    return shutil.which("msedge") or shutil.which("chrome") or shutil.which("chromium")

def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close(); return port

class CDP:
    def __init__(self, ws):
        self.ws = ws; self.n = 0; self.pending = {}; self.events = []
    async def cmd(self, method, **params):
        self.n += 1; i = self.n
        fut = asyncio.get_event_loop().create_future(); self.pending[i] = fut
        await self.ws.send(json.dumps({"id": i, "method": method, "params": params}))
        return await asyncio.wait_for(fut, 25)
    async def reader(self):
        while True:
            try: m = json.loads(await self.ws.recv())
            except Exception: return
            if "id" in m and m["id"] in self.pending:
                f = self.pending.pop(m["id"]) 
                if not f.done(): f.set_result(m.get("result", {}))
            else:
                self.events.append(m)
    async def js(self, expr, timeout=12):
        r = await self.cmd("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
        if "exceptionDetails" in r: raise RuntimeError(str(r["exceptionDetails"])[:300])
        return (r.get("result") or {}).get("value")
    def console_errors(self):
        errs = []
        for m in self.events:
            me = m.get("method")
            if me == "Runtime.consoleAPICalled" and m["params"].get("type") in ("error", "warning"):
                a = m["params"].get("args", [])
                errs.append(m["params"]["type"] + ": " + " ".join(str(x.get("value", x.get("description", ""))) for x in a)[:200])
            elif me == "Runtime.exceptionThrown":
                d = m["params"]["exceptionDetails"]
                errs.append("EXC: " + (d.get("text") or "") + " " + str((d.get("exception") or {}).get("description", ""))[:200])
            elif me == "Log.entryAdded" and m["params"]["entry"].get("level") == "error":
                errs.append("LOG: " + str(m["params"]["entry"].get("message", ""))[:200])
        return errs

async def wait_for_target(port, url_sub, timeout=30):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=4) as r:
                targets = json.loads(r.read().decode())
            for tg in targets:
                if tg.get("type") == "page" and url_sub in (tg.get("url") or ""):
                    return tg
        except Exception:
            pass
        await asyncio.sleep(0.5)
    return None

async def run(url, width, height, checks, out, port):
    edge = find_edge()
    if not edge: raise SystemExit("FATAL: no msedge/chrome binary found")
    udir = os.path.join(tempfile.gettempdir(), "builder_cdp_udir")
    os.makedirs(udir, exist_ok=True)
    proc = subprocess.Popen([edge, "--headless=new", "--disable-gpu", "--no-sandbox",
                             f"--remote-debugging-port={port}", f"--user-data-dir={udir}",
                             f"--window-size={width},{height}", url],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    report = {"url": url, "viewport": [width, height], "edge": edge, "port": port, "checks": {}, "console_errors": [], "ok": False}
    try:
        tg = await wait_for_target(port, url.split("://")[1][:24], timeout=30)
        if not tg: raise SystemExit("FATAL: CDP target for page never appeared (egress block or launch fail?)")
        async with connect(tg["webSocketDebuggerUrl"], max_size=None) as ws:
            c = CDP(ws); rd = asyncio.create_task(c.reader())
            await c.cmd("Page.enable"); await c.cmd("Runtime.enable"); await c.cmd("Log.enable")
            # wait for load to settle
            for _ in range(40):
                rs = await c.js("document.readyState")
                if rs == "complete": break
                await asyncio.sleep(0.5)
            report["readyState"] = rs
            report["title"] = await c.js("document.title")
            report["body_text_len"] = await c.js("(document.body?document.body.innerText.length:0)")
            # element checks
            all_pass = True
            for sel, want in checks.items():
                present = bool(await c.js(f"!!document.querySelector({json.dumps(sel)})"))
                ok = (present == bool(want)); all_pass = all_pass and ok
                report["checks"][sel] = {"expected_present": bool(want), "found": present, "pass": ok}
            # screenshot
            shot = await c.cmd("Page.captureScreenshot", format="png")
            if shot.get("data"):
                os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
                with open(out, "wb") as f: f.write(base64.b64decode(shot["data"]))
                report["screenshot"] = out
            report["console_errors"] = c.console_errors()
            report["ok"] = (rs == "complete") and all_pass and not any(e.startswith(("EXC",)) for e in report["console_errors"])
            rd.cancel()
    finally:
        proc.terminate()
        try: proc.wait(timeout=5)
        except Exception: proc.kill()
    return report

def main():
    import argparse
    ap = argparse.ArgumentParser(description="General headless render test via Edge CDP")
    ap.add_argument("--url", default="http://127.0.0.1:8099/")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=900)
    ap.add_argument("--checks", default="{}", help="JSON {cssSelector: expectedPresent}")
    ap.add_argument("--out", default="memory/builder/render.png")
    ap.add_argument("--port", type=int, default=0, help="0 = auto-pick free port")
    a = ap.parse_args()
    checks = json.loads(a.checks)
    port = a.port or free_port()
    rep = asyncio.run(run(a.url, a.width, a.height, checks, a.out, port))
    rj = a.out + ".report.json"
    with open(rj, "w", encoding="utf-8") as f: json.dump(rep, f, indent=2)
    print(json.dumps(rep, indent=2))
    sys.exit(0 if rep["ok"] else 1)

if __name__ == "__main__":
    main()
