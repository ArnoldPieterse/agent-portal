"""CDP screenshot verification for responsive design breakpoints.
Run from terminal: python memory/designer/cdp_screenshot.py
"""
import asyncio, json, time, os, sys, base64
from websockets import connect
import urllib.request

PORT = 9222
URL = "http://127.0.0.1:8099"
BREAKPOINTS = [320, 768, 1024, 1440]
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cdp-screenshots")
os.makedirs(OUT_DIR, exist_ok=True)


def get_ws_url():
    resp = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json", timeout=5)
    targets = json.loads(resp.read())
    for t in targets:
        if t.get("type") == "page":
            return t["webSocketDebuggerUrl"]
    return None


async def cdp(ws, method, params=None):
    msg = {"id": 1, "method": method}
    if params:
        msg["params"] = params
    await ws.send(json.dumps(msg))
    while True:
        resp = json.loads(await ws.recv())
        if resp.get("id") == 1:
            return resp


async def main():
    # Wait for DevTools (up to 15s)
    ws_url = None
    for attempt in range(15):
        time.sleep(1)
        try:
            ws_url = get_ws_url()
            if ws_url:
                break
        except Exception as e:
            if attempt == 0:
                print(f"Waiting for DevTools... ({e})")

    if not ws_url:
        print("FAIL: Could not connect to Edge DevTools on port 9222")
        print("Make sure Edge was launched with --remote-debugging-port=9222")
        return False

    print(f"Connected. Running {len(BREAKPOINTS)} breakpoints...")
    results = {}

    async with connect(ws_url, timeout=30) as ws:
        await cdp(ws, "Page.enable")
        await cdp(ws, "Runtime.enable")

        for width in BREAKPOINTS:
            height = 900
            await cdp(ws, "Emulation.setDeviceMetricsOverride", {
                "width": width, "height": height,
                "deviceScaleFactor": 1, "mobile": width < 768
            })

            nav = await cdp(ws, "Page.navigate", {"url": URL})
            if "error" in nav:
                print(f"FAIL [{width}px]: navigation error: {nav['error']}")
                results[width] = {"status": "nav_error"}
                continue

            await asyncio.sleep(3)

            overflow_resp = await cdp(ws, "Runtime.evaluate", {
                "expression": (
                    "JSON.stringify({"
                    "scrollWidth: document.documentElement.scrollWidth,"
                    "clientWidth: document.documentElement.clientWidth,"
                    "overflowing: document.documentElement.scrollWidth > document.documentElement.clientWidth"
                    "})"
                ),
                "returnByValue": True
            })

            ov = json.loads(overflow_resp.get("result", {}).get("value", "{}"))

            shot = await cdp(ws, "Page.captureScreenshot", {
                "format": "png",
                "captureBeyondViewport": False
            })

            if "data" in shot:
                path = os.path.join(OUT_DIR, f"breakpoint-{width}px.png")
                with open(path, "wb") as f:
                    f.write(base64.b64decode(shot["data"]))

            results[width] = {
                "status": "ok",
                "overflow": ov.get("overflowing", False),
                "scrollWidth": ov.get("scrollWidth"),
                "clientWidth": ov.get("clientWidth"),
                "screenshot": f"memory/designer/cdp-screenshots/breakpoint-{width}px.png"
            }
            print(f"[{width}px] overflow={ov.get('overflowing')} scrollW={ov.get('scrollWidth')} clientW={ov.get('clientWidth')}")

    all_pass = all(not r.get("overflow", True) for r in results.values() if r["status"] == "ok")
    print(f"\n=== CDP Screenshot Verification ===")
    print(f"All breakpoints pass (no horizontal overflow): {all_pass}")
    for w, r in sorted(results.items()):
        status = "PASS" if not r.get("overflow", True) else "FAIL"
        print(f"  {w}px: {status} (scrollW={r.get('scrollWidth')}, clientW={r.get('clientWidth')})")
    return all_pass


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
