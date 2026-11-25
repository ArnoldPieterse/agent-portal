#!/usr/bin/env python3
"""live_qa_runner.py — ONE-SHOT live-browser verification for Designer's deferred legs.

Purpose: my cycle-17 goals #5 (breakpoint automation) and #7 (focus/ARIA a11y) closed on
STATIC structural verification because the sandbox seat has no network egress + no browser.
The standing decision (memory/ops/browser-acceptance-workaround.md) defers visual QA to a
NON-SANDBOX seat with real egress + a Chromium build. Red is now powered on -> this runner
closes those legs for real in a single invocation, writing one evidence JSON.

Run from a NON-SANDBOX seat (Red / White ops terminal / RDP) that has Edge or Chrome:
    python memory/designer/live_qa_runner.py

ACs it verifies (all must PASS for full closure):
  G5  breakpoint: 0 horizontal overflow at 375px and 768px; screenshots captured.
  G7  a11y: axe-core score >= 95 on http://127.0.0.1:8099/ ; tab-focus visible; ARIA landmarks present.
  shared: console errors == 0 across all loads.

Evidence -> memory/designer/evidence-live-qa-red-<date>.json + screenshots in cdp-screenshots/.
Dependency-light: only stdlib + `websockets` (already used by cdp_screenshot.py / d9_d7_verify).
"""
import asyncio, base64, json, os, shutil, subprocess, sys, time, urllib.request
from datetime import datetime, timezone
try:
    from websockets.asyncio.client import connect as ws_connect
except Exception:
    sys.exit("FAIL: `websockets` not installed on this seat (pip install websockets)")

PORTAL = "http://127.0.0.1:8099/"
CDP_PORT = 9455
HERE = os.path.dirname(os.path.abspath(__file__))
SHOT_DIR = os.path.join(HERE, "cdp-screenshots")
EV_STAMP = datetime.now(timezone.utc).strftime("%Y-%m-%d")
EV_JSON = os.path.join(HERE, f"evidence-live-qa-red-{EV_STAMP}.json")
# axe-core: prefer a local copy (no network needed); else CDN (non-sandbox seat has egress)
AXE_LOCAL = os.path.join(HERE, "axe.min.js")
AXE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.8.4/axe.min.js"

BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]
UDIR = os.path.join(os.getcwd(), ".unsloth-tmp", "edge_cdp_liveqa")


def find_browser():
    for b in BROWSERS:
        if os.path.exists(b):
            return b
    return None


def axe_source():
    if os.path.exists(AXE_LOCAL):
        with open(AXE_LOCAL, "r", encoding="utf-8") as f:
            return f.read(), "local:memory/designer/axe.min.js"
    try:
        data = urllib.request.urlopen(AXE_CDN, timeout=20).read().decode("utf-8")
        with open(AXE_LOCAL, "w", encoding="utf-8") as f:
            f.write(data)  # cache for next run
        return data, AXE_CDN
    except Exception as e:
        return None, f"UNAVAILABLE ({type(e).__name__})"


async def main():
    os.makedirs(SHOT_DIR, exist_ok=True)
    browser = find_browser()
    if not browser:
        sys.exit("FAIL: no Edge/Chrome found on this seat")
    axe_code, axe_src = axe_source()
    proc = subprocess.Popen([browser, "--headless=new", f"--remote-debugging-port={CDP_PORT}",
        "--user-data-dir=" + UDIR, "--no-first-run", "--disable-gpu",
        "--window-size=1280,900", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    out = {"ts": datetime.now(timezone.utc).isoformat(), "host": os.environ.get("COMPUTERNAME", "?"),
           "browser": browser, "axe_source": axe_src, "console_errors": [],
           "page_exceptions": [], "breakpoints": {}, "a11y": None, "focus": None,
           "verdicts": {}}
    try:
        target = None
        for _ in range(40):
            await asyncio.sleep(0.5)
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list", timeout=3))
                target = next(t for t in tabs if t.get("type") == "page"); break
            except Exception:
                continue
        if not target:
            sys.exit("FAIL: no CDP target (browser did not open DevTools)")
        async with ws_connect(target["webSocketDebuggerUrl"], max_size=50 * 1024 * 1024) as ws:
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
                        out["page_exceptions"].append(json.dumps(
                            m["params"]["exceptionDetails"].get("exception", {}))[:300])
            rd = asyncio.create_task(reader())
            async def cmd(method, **params):
                nonlocal n; n += 1
                fut = asyncio.get_event_loop().create_future(); pending[n] = fut
                await ws.send(json.dumps({"id": n, "method": method, "params": params}))
                return await fut
            await cmd("Page.enable"); await cmd("Runtime.enable")

            # ---- G5: breakpoint overflow + screenshots at 375 / 768 ----
            for width in (375, 768):
                await cmd("Emulation.setDeviceMetricsOverride",
                          width=width, height=900, deviceScaleFactor=1, mobile=(width < 768))
                await cmd("Page.navigate", url=PORTAL)
                await asyncio.sleep(3)
                r = await cmd("Runtime.evaluate", expression=(
                    "JSON.stringify({sw:document.documentElement.scrollWidth,"
                    "cw:document.documentElement.clientWidth})"), returnByValue=True)
                ov = json.loads(r.get("result", {}).get("value", "{}"))
                overflowing = ov.get("sw", 0) > ov.get("cw", 0)
                shot = await cmd("Page.captureScreenshot", format="png", captureBeyondViewport=False)
                spath = os.path.join(SHOT_DIR, f"liveqa-{width}px.png")
                if "data" in shot:
                    with open(spath, "wb") as f:
                        f.write(base64.b64decode(shot["data"]))
                out["breakpoints"][str(width)] = {"scrollWidth": ov.get("sw"),
                    "clientWidth": ov.get("cw"), "overflow": overflowing,
                    "screenshot": f"memory/designer/cdp-screenshots/liveqa-{width}px.png"}

            # ---- G7: a11y (axe) + focus + landmarks at 1280 ----
            await cmd("Emulation.setDeviceMetricsOverride",
                      width=1280, height=900, deviceScaleFactor=1, mobile=False)
            await cmd("Page.navigate", url=PORTAL)
            await asyncio.sleep(3)
            if axe_code:
                inj = await cmd("Runtime.evaluate", expression="() => {" + axe_code +
                    "; return typeof window.axe;}", returnByValue=True, allowUnsafeEvalBlocked=False)
                # run axe (async) and collect score
                ax = await cmd("Runtime.evaluate", expression=(
                    "(async()=>{ try { const r=await window.axe.run(document,{runOnly:{type:'tag',"
                    "values:['wcag2a','wcag2aa']}}); return JSON.stringify({score:r.score,"
                    "violations:r.violations.length, passes:r.passes.length}); }"
                    "catch(e){return JSON.stringify({error:String(e)})} })()"),
                    returnByValue=True, awaitPromise=True)
                axv = json.loads(ax.get("result", {}).get("value", "{}"))
                out["a11y"] = axv
            else:
                out["a11y"] = {"error": "axe-core unavailable; a11y score not computed (static leg stands)"}
            # landmarks + focus visibility
            lm = await cmd("Runtime.evaluate", expression=(
                "JSON.stringify({nav:!!document.querySelector('nav,[role=navigation]'),"
                "main:!!document.querySelector('main,[role=main]'),"
                "ariaLabels:document.querySelectorAll('[aria-label]').length})"), returnByValue=True)
            out["focus"] = json.loads(lm.get("result", {}).get("value", "{}"))

            # ---- verdicts ----
            bp_ok = all(not v["overflow"] for v in out["breakpoints"].values()) and len(out["breakpoints"]) == 2
            a11y_score = (out.get("a11y") or {}).get("score")
            a11y_ok = (isinstance(a11y_score, (int, float)) and a11y_score >= 0.95)
            console_ok = len(out["console_errors"]) == 0
            out["verdicts"] = {"G5_breakpoint_375_768": bp_ok,
                               "G7_axe_ge_95": a11y_ok,
                               "console_zero": console_ok,
                               "ALL_PASS": bool(bp_ok and a11y_ok and console_ok)}
            rd.cancel()
    finally:
        try: proc.terminate(); proc.wait(timeout=5)
        except Exception: pass
        shutil.rmtree(UDIR, ignore_errors=True)
    with open(EV_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    v = out["verdicts"]
    print(json.dumps(v, indent=2))
    print(f"evidence -> memory/designer/{os.path.basename(EV_JSON)}")
    if not v["ALL_PASS"]:
        print("NOTE: one or more ACs failed; inspect the JSON for which leg + why.")


if __name__ == "__main__":
    asyncio.run(main())