#!/usr/bin/env python3
"""design_breakpoint_check.py - Pre-deploy responsive gate (Designer Goal 5)

Launches headless Chrome, navigates to the portal, and asserts:
  - 0 horizontal overflow at viewport widths 375px and 768px
Takes screenshots as evidence. Exit 0 = PASS, exit 1 = FAIL.

Usage:
  python memory/designer/design_breakpoint_check.py [--url http://localhost:8099]

Requires: Chrome/Chromium on PATH, Python websockets package.
"""
import argparse, asyncio, base64, json, os, subprocess, sys, tempfile, time
import urllib.request

try:
    import websockets
except ImportError:
    print("FAIL: 'websockets' package not installed. Run: pip install websockets")
    sys.exit(1)

CHROME_CANDIDATES = [
    "chrome", "chromium", "msedge",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]

def find_chrome():
    env_path = os.environ.get("CHROME_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path
    for c in CHROME_CANDIDATES:
        try:
            if os.path.isfile(c): return c
            subprocess.run(["where" if os.name=="nt" else "which", c],
                          capture_output=True, check=True)
            return c
        except (OSError, subprocess.CalledProcessError):
            continue
    print("FAIL: No Chrome/Chromium found on PATH")
    sys.exit(1)

async def send_cmd(ws, method, params=None, _id=[0]):
    _id[0] += 1
    msg = {"id": _id[0], "method": method}
    if params: msg["params"] = params
    await ws.send(json.dumps(msg))
    while True:
        resp = json.loads(await ws.recv())
        if resp.get("id") == _id[0]:
            return resp

async def run_check(ws, url, width, height):
    """Set viewport, navigate, wait for load, check overflow. Return (has_overflow, screenshot_b64)."""
    await send_cmd(ws, "Emulation.setDeviceMetricsOverride", {
        "width": width, "height": height, "deviceScaleFactor": 1, "mobile": False})
    await send_cmd(ws, "Runtime.enable")
    await send_cmd(ws, "Page.enable")
    await send_cmd(ws, "Page.navigate", {"url": url})
    # Wait for load
    deadline = time.time() + 15
    while time.time() < deadline:
        resp = await send_cmd(ws, "Runtime.evaluate", {
            "expression": "document.readyState", "returnByValue": True})
        state = resp.get("result", {}).get("result", {}).get("value", "")
        if state == "complete": break
        await asyncio.sleep(0.3)
    # Check overflow
    ov_resp = await send_cmd(ws, "Runtime.evaluate", {
        "expression": "(document.documentElement.scrollWidth > window.innerWidth)",
        "returnByValue": True})
    has_overflow = ov_resp.get("result", {}).get("result", {}).get("value", False)
    # Screenshot
    shot = await send_cmd(ws, "Page.captureScreenshot", {"format": "png"})
    img_b64 = shot.get("result", {}).get("data", "")
    return has_overflow, img_b64

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8099")
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()

    out_dir = args.out_dir or os.path.join("memory", "designer", "breakpoint-evidence")
    os.makedirs(out_dir, exist_ok=True)

    chrome = find_chrome()
    port = 9222 + (os.getpid() % 100)
    user_data = tempfile.mkdtemp(prefix="cdp_bp_")
    chrome_proc = subprocess.Popen([
        chrome, "--headless=new", "--remote-debugging-port=%d" % port,
        "--user-data-dir=%s" % user_data, "--no-sandbox", "--disable-gpu",
        "--window-size=1280,800"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        # Wait for DevTools endpoint
        ws_url = None
        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                req = urllib.request.urlopen("http://127.0.0.1:%d/json" % port)
                tabs = json.loads(req.read())
                pages = [x for x in tabs if x.get("type") == "page"
                         and not x.get("url", "").startswith("chrome-extension://")]
                if pages: ws_url = pages[0]["webSocketDebuggerUrl"]
                break
            except Exception:
                await asyncio.sleep(0.5)
        if not ws_url:
            print("FAIL: Chrome DevTools endpoint not reachable")
            sys.exit(1)

        async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
            await send_cmd(ws, "Page.enable")
            results = []
            for width in [375, 768]:
                overflow, img_b64 = await run_check(ws, args.url, width, 800)
                shot_path = os.path.join(out_dir, "bp-%dpx.png" % width)
                if img_b64:
                    with open(shot_path, "wb") as f:
                        f.write(base64.b64decode(img_b64))
                results.append({"width": width, "overflow": overflow, "screenshot": shot_path})
                status = "FAIL" if overflow else "PASS"
                print("  %dpx: %s%s" % (width, status, " [horizontal overflow]" if overflow else ""))

            all_pass = all(not r["overflow"] for r in results)
            print("")
            print("=" * 40)
            if all_pass:
                print("PASS: 0 horizontal overflow at both breakpoints")
            else:
                print("FAIL: horizontal overflow detected")
                sys.exit(1)

    finally:
        chrome_proc.terminate()
        try: chrome_proc.wait(timeout=5)
        except: chrome_proc.kill()

if __name__ == "__main__":
    asyncio.run(main())
