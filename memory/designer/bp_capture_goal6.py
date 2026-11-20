#!/usr/bin/env python3
"""CDP breakpoint capture for Goal 6 (Responsive Design Hardening).
Launches headless Edge, captures screenshots at 320/768/1024/1440px,
checks for horizontal overflow at each width.
"""
import asyncio, base64, json, os, subprocess, sys, time, urllib.request
from datetime import datetime

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
CDP_PORT = 9335
UDIR = os.path.join(os.getcwd(), ".unsloth-tmp", "edge_bp_capture")
PORTAL = "http://127.0.0.1:8099/"
DATE = datetime.now().strftime("%Y-%m-%d")
EVD = os.path.join("memory", "designer", "breakpoint-evidence")
os.makedirs(EVD, exist_ok=True)
os.makedirs(UDIR, exist_ok=True)

from websockets.asyncio.client import connect

def log(m): print(time.strftime("%H:%M:%S ") + str(m), flush=True)

async def cdp(ws, method, params=None, _id=[0]):
    _id[0] += 1
    await ws.send(json.dumps({"id": _id[0], "method": method, **(params or {})}))
    while True:
        r = json.loads(await ws.recv())
        if r.get("id") == _id[0]: return r

async def js(ws, expr):
    r = await cdp(ws, "Runtime.evaluate", {"expression": expr, "returnByValue": True})
    if "exceptionDetails" in r.get("result", {}):
        raise RuntimeError(f"JS error: {r['result']['exceptionDetails']}")
    return r["result"].get("result", {}).get("value")

async def screenshot(ws, path):
    result = await cdp(ws, "Page.captureScreenshot", {"format": "png"})
    data = base64.b64decode(result["result"]["data"])
    with open(path, "wb") as f: f.write(data)
    log(f"  screenshot -> {path} ({len(data)} bytes)")

async def main():
    if not os.path.exists(EDGE):
        log(f"FATAL: Edge not found at {EDGE}")
        sys.exit(1)
    
    log(f"Launching headless Edge...")
    proc = subprocess.Popen([
        EDGE, "--headless=new", f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={UDIR}", "--no-first-run", "--disable-gpu",
        "--window-size=1440,900", PORTAL
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    target_url = None
    for _ in range(30):
        await asyncio.sleep(1)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list") as r:
                targets = json.loads(r.read())
                for t in targets:
                    if t.get("type") == "page" and "8099" in t.get("url", ""):
                        target_url = t["webSocketDebuggerUrl"]
                        break
                if not target_url and targets:
                    non_ext = [t for t in targets if t.get("type") == "page" and "extension" not in t.get("url","")]
                    if non_ext:
                        target_url = non_ext[0]["webSocketDebuggerUrl"]
        except Exception:
            continue
        if target_url: break
    
    if not target_url:
        log("FATAL: Could not connect to CDP endpoint")
        proc.terminate()
        sys.exit(1)
    
    log(f"Connected: {target_url}")
    breakpoints = [320, 768, 1024, 1440]
    results = {}
    
    async with connect(target_url) as ws:
        await cdp(ws, "Page.enable")
        await cdp(ws, "Runtime.enable")
        await asyncio.sleep(3)
        
        for bp in breakpoints:
            log(f"\n[Breakpoint {bp}px]")
            await cdp(ws, "Emulation.setDeviceMetricsOverride", {
                "width": bp, "height": 900, "deviceScaleFactor": 1, "mobile": bp <= 480
            })
            await asyncio.sleep(1)
            
            overflow = await js(ws, """
            (function(){
              const de = document.documentElement;
              return JSON.stringify({scrollWidth: de.scrollWidth, innerWidth: window.innerWidth, overflow: de.scrollWidth > window.innerWidth + 2});
            })()
            """)
            info = json.loads(overflow) if overflow else {}
            
            shot_path = os.path.join(EVD, f"bp-{bp}px-{DATE}.png")
            await screenshot(ws, shot_path)
            
            ok = not info.get("overflow", False)
            results[str(bp)] = {"pass": ok, **info}
            log(f"  overflow={info.get('overflow')} (sw={info.get('scrollWidth')}, iw={info.get('innerWidth')}) -> {'PASS' if ok else 'FAIL'}")
    
    proc.terminate()
    out = os.path.join(EVD, f"breakpoint-results-{DATE}.json")
    with open(out, "w") as f: json.dump(results, f, indent=2)
    
    all_pass = all(r["pass"] for r in results.values())
    log(f"\n{'='*40}")
    log(f"TOTAL: {sum(1 for r in results.values() if r['pass'])}/{len(results)} breakpoints PASS")
    log(f"Evidence: {out}")

if __name__ == "__main__":
    asyncio.run(main())
