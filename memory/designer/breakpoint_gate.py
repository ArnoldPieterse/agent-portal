#!/usr/bin/env python3
"""breakpoint_gate.py - Pre-deploy responsive gate (Designer Goal 5)

Consolidated, complete version of design_breakpoint_check.py. Launches a headless
Chromium-family browser (Chrome / Edge) over CDP and, for viewport widths 375px and
768px, asserts ALL THREE of:
  1. 0 horizontal overflow  (document.scrollWidth <= viewport width + tol)
  2. 0 console errors       (Runtime.consoleAPICalled type=error / Log.entryAdded level=error / Runtime.exceptionThrown)
  3. key elements visible   (header, agent list, chat column) when --check-elements is set
Takes a PNG screenshot per breakpoint as evidence. Exit 0 = PASS, exit 1 = FAIL.

Usage:
  python memory/designer/breakpoint_gate.py                # live :8099 gate
  python memory/designer/breakpoint_gate.py --url <URL>    # custom target
  python memory/designer/breakpoint_gate.py --selftest     # browser+loopback fixture proof
  python memory/designer/breakpoint_gate.py --logic-test   # browser-free judge() proof

--selftest renders local HTML fixtures (no external egress, but needs a browser +
loopback socket) and proves the acceptance behaviour: clean->PASS, overflow->FAIL,
JS-error->FAIL. --logic-test feeds synthetic measurements into judge() with NO
browser/sockets at all, so the pass/fail judgment is provable even in a fully
sandboxed seat (the Designer seat blocks ALL sockets, errno 10013).

Requires: Chrome/Edge on PATH (or CHROME_PATH env), Python 'websockets' package.
Scheduling: wire as pre-deploy step in TODO.md runbook / cron on a non-sandbox seat.
"""
import argparse, asyncio, base64, json, os, subprocess, sys, tempfile, time
import urllib.request

try:
    import websockets
except ImportError:
    print("FAIL: 'websockets' package not installed. Run: pip install websockets")
    sys.exit(1)

BROWSER_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "chrome", "chromium", "msedge",
]


def find_browser():
    env_path = os.environ.get("CHROME_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path
    for c in BROWSER_CANDIDATES:
        if os.path.isfile(c):
            return c
        if not c.lower().endswith(".exe"):
            try:
                subprocess.run(["where" if os.name == "nt" else "which", c],
                               capture_output=True, check=True)
                return c
            except (OSError, subprocess.CalledProcessError):
                continue
    print("FAIL: No Chrome/Edge browser found on PATH")
    sys.exit(1)


async def send_cmd(ws, method, params=None, _id=[0]):
    _id[0] += 1
    msg = {"id": _id[0], "method": method}
    if params:
        msg["params"] = params
    await ws.send(json.dumps(msg))
    while True:
        try:
            frame = await asyncio.wait_for(ws.recv(), timeout=20)
        except asyncio.TimeoutError:
            raise RuntimeError("CDP recv timed out waiting for %s" % method)
        resp = json.loads(frame)
        for handler, ev_method in getattr(ws, "_bp_handlers", []) or []:
            if resp.get("method") == ev_method and "id" not in resp:
                try:
                    handler(resp.get("params", {}))
                except Exception:
                    pass
        if resp.get("id") == _id[0]:
            return resp


def judge(width, res, tol=2, check_elements=False):
    """Pure decision logic (unit-testable without a browser/sockets).
    Returns (passed: bool, issues: list[str])."""
    issues = []
    if res["scroll_w"] > res["inner_w"] + tol:
        issues.append("horizontal overflow: scrollWidth=%d > innerWidth=%d (+%dpx)"
                      % (res["scroll_w"], res["inner_w"], res["scroll_w"] - res["inner_w"]))
    if res["console_errors"]:
        issues.append("%d console error(s): %s" % (len(res["console_errors"]),
                      "; ".join(res["console_errors"][:3])))
    if check_elements:
        for sel, ok in res["vis"].items():
            if not ok:
                issues.append("missing/invisible: %s" % sel)
    return len(issues) == 0, issues


def logic_test():
    """Browser-free proof of the gate's judgment (no sockets -> runs in a sandboxed
    seat). Feeds synthetic measurement results into judge() and asserts the
    acceptance expectations. Returns True if all hold."""
    print("logic-test: exercising judge() with synthetic measurements (no browser)\n")
    cases = [
        ("clean page -> PASS",
         {"scroll_w": 375, "inner_w": 375, "console_errors": [],
          "vis": {"header": True, "#agentList": True, "#chatCol": True}},
         False, lambda p, i: p and not i),
        ("forced overflow -> FAIL",
         {"scroll_w": 900, "inner_w": 375, "console_errors": [],
          "vis": {"header": True, "#agentList": True, "#chatCol": True}},
         False, lambda p, i: (not p) and any("overflow" in x for x in i)),
        ("JS console error -> FAIL",
         {"scroll_w": 375, "inner_w": 375, "console_errors": ["Uncaught Error: boom"],
          "vis": {"header": True, "#agentList": True, "#chatCol": True}},
         False, lambda p, i: (not p) and any("console error" in x for x in i)),
        ("subpixel rounding within tol -> PASS",
         {"scroll_w": 377, "inner_w": 375, "console_errors": [],
          "vis": {"header": True, "#agentList": True, "#chatCol": True}},
         False, lambda p, i: p),
        ("missing element (check_elements) -> FAIL",
         {"scroll_w": 375, "inner_w": 375, "console_errors": [],
          "vis": {"header": True, "#agentList": False, "#chatCol": True}},
         True, lambda p, i: (not p) and any("#agentList" in x for x in i)),
    ]
    results = []
    for name, res, check_elements, expect in cases:
        passed, issues = judge(375, res, check_elements=check_elements)
        held = bool(expect(passed, issues))
        results.append((name, held))
        print("  [%s] %s   (passed=%s%s)" % ("ok" if held else "MISS", name, passed,
              (", issues=%r" % issues) if issues else ""))
    ok = all(h for _, h in results)
    print("")
    print("LOGIC-TEST %s: %d/%d acceptance expectations held" %
          ("PASS" if ok else "FAIL", sum(h for _, h in results), len(results)))
    return ok


async def run_check(ws, url, width, height):
    await send_cmd(ws, "Emulation.setDeviceMetricsOverride", {
        "width": width, "height": height, "deviceScaleFactor": 1, "mobile": False})
    await send_cmd(ws, "Runtime.enable")
    await send_cmd(ws, "Page.enable")
    await send_cmd(ws, "Log.enable")
    console_errors = []

    def _on_console(ev):
        try:
            if ev.get("type") == "error":
                args = [a.get("value", a.get("description", "")) for a in ev.get("args", [])]
                console_errors.append(" ".join(str(x) for x in args if x) or "console.error()")
        except Exception:
            pass

    def _on_log(ev):
        try:
            if ev.get("level") == "error":
                console_errors.append(ev.get("text", "log error"))
        except Exception:
            pass

    def _on_exc(ev):
        try:
            d = (ev.get("exceptionDetails", {}) or {})
            txt = d.get("text") or "uncaught exception"
            if d.get("exception", {}).get("description"):
                txt = d["exception"]["description"].splitlines()[0]
            console_errors.append(txt)
        except Exception:
            pass

    ws._bp_handlers = [(_on_console, "Runtime.consoleAPICalled"), (_on_log, "Log.entryAdded"),
                       (_on_exc, "Runtime.exceptionThrown")]

    await send_cmd(ws, "Page.navigate", {"url": url})
    deadline = time.time() + 15
    while time.time() < deadline:
        resp = await send_cmd(ws, "Runtime.evaluate", {
            "expression": "document.readyState", "returnByValue": True})
        if resp.get("result", {}).get("result", {}).get("value") == "complete":
            break
        await asyncio.sleep(0.3)
    await asyncio.sleep(0.2)

    m = await send_cmd(ws, "Runtime.evaluate", {
        "expression": "JSON.stringify({sw: document.documentElement.scrollWidth, iw: window.innerWidth})",
        "returnByValue": True})
    dims = json.loads(m.get("result", {}).get("result", {}).get("value", "{}") or "{}")
    scroll_w = int(dims.get("sw", 0))
    inner_w = int(dims.get("iw", width))

    vis = {}
    for sel in ["header", "#agentList", "#chatCol"]:
        v = await send_cmd(ws, "Runtime.evaluate", {
            "expression": "(function(){var e=document.querySelector('%s');return !!(e && e.offsetParent!==null);})()" % sel,
            "returnByValue": True})
        vis[sel] = bool(v.get("result", {}).get("result", {}).get("value", False))

    shot = await send_cmd(ws, "Page.captureScreenshot", {"format": "png"})
    return {"scroll_w": scroll_w, "inner_w": inner_w, "console_errors": console_errors,
            "vis": vis, "screenshot_b64": shot.get("result", {}).get("data", "")}


async def launch_and_connect():
    browser = find_browser()
    port = 9300 + (os.getpid() % 100)
    user_data = tempfile.mkdtemp(prefix="cdp_bp_")
    proc = subprocess.Popen([
        browser, "--headless=new", "--remote-debugging-port=%d" % port,
        "--user-data-dir=%s" % user_data, "--no-sandbox", "--disable-gpu",
        "--window-size=1280,800"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ws_url = None
    deadline = time.time() + 12
    while time.time() < deadline:
        try:
            req = urllib.request.urlopen("http://127.0.0.1:%d/json" % port, timeout=2)
            tabs = json.loads(req.read())
            pages = [x for x in tabs if x.get("type") == "page"
                     and not x.get("url", "").startswith("chrome-extension://")]
            if pages:
                ws_url = pages[0]["webSocketDebuggerUrl"]
                break
        except Exception:
            await asyncio.sleep(0.4)
    if not ws_url:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        raise RuntimeError("browser DevTools endpoint not reachable (socket egress blocked? errno 10013)")
    return proc, ws_url


async def _with_browser(cb):
    proc, ws_url = await launch_and_connect()
    try:
        async with websockets.connect(ws_url, max_size=50 * 1024 * 1024,
                                      open_timeout=10, close_timeout=5) as ws:
            return await cb(ws)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


async def run_live(url, out_dir, check_elements=False):
    os.makedirs(out_dir, exist_ok=True)

    async def cb(ws):
        ok_all = True
        for width in [375, 768]:
            res = await run_check(ws, url, width, 800)
            shot_path = os.path.join(out_dir, "bp-%dpx.png" % width)
            if res["screenshot_b64"]:
                with open(shot_path, "wb") as f:
                    f.write(base64.b64decode(res["screenshot_b64"]))
            passed, issues = judge(width, res, check_elements=check_elements)
            ok_all = ok_all and passed
            print("  %dpx: %s%s -> %s" % (width, "PASS" if passed else "FAIL",
                  (" [" + "; ".join(issues) + "]") if issues else "", shot_path))
        return ok_all

    return await _with_browser(cb)


FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "breakpoint-fixtures")


def _fixture(body):
    return ("<!doctype html><html><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'></head>"
            "<body style='margin:0;font-family:sans-serif'>%s</body></html>" % body)


def write_fixtures():
    os.makedirs(FIXTURE_DIR, exist_ok=True)
    files = {
        "clean.html": _fixture("<div style='width:100%;box-sizing:border-box;padding:16px'>ok</div>"),
        "overflow.html": _fixture("<div style='width:900px;height:40px;background:#fbb'>forced overflow</div>"),
        "consoleerr.html": _fixture("<p>x</p><script>throw new Error('boom-in-selftest');</script>"),
    }
    paths = {}
    for name, html in files.items():
        p = os.path.join(FIXTURE_DIR, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(html)
        paths[name] = p
    return paths


def file_url(path):
    return "file://" + path.replace(os.sep, "/")


async def run_selftest(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    fx = write_fixtures()
    expectations = []

    async def cb(ws):
        res = await run_check(ws, file_url(fx["clean.html"]), 375, 800)
        with open(os.path.join(out_dir, "selftest-clean-375.png"), "wb") as f:
            f.write(base64.b64decode(res["screenshot_b64"]))
        passed, issues = judge(375, res)
        expectations.append(("clean page -> PASS", passed and not res["console_errors"]))
        print("  clean@375: %s%s" % ("PASS" if passed else "FAIL",
              (" [" + "; ".join(issues) + "]") if issues else ""))
        res = await run_check(ws, file_url(fx["overflow.html"]), 375, 800)
        with open(os.path.join(out_dir, "selftest-overflow-375.png"), "wb") as f:
            f.write(base64.b64decode(res["screenshot_b64"]))
        passed, issues = judge(375, res)
        expectations.append(("forced overflow -> FAIL", (not passed) and any("overflow" in i for i in issues)))
        print("  overflow@375: %s%s" % ("PASS" if passed else "FAIL",
              (" [" + "; ".join(issues) + "]") if issues else ""))
        res = await run_check(ws, file_url(fx["consoleerr.html"]), 375, 800)
        with open(os.path.join(out_dir, "selftest-consoleerr-375.png"), "wb") as f:
            f.write(base64.b64decode(res["screenshot_b64"]))
        passed, issues = judge(375, res)
        expectations.append(("JS console error -> FAIL", (not passed) and any("console error" in i for i in issues)))
        print("  consoleerr@375: %s%s" % ("PASS" if passed else "FAIL",
              (" [" + "; ".join(issues) + "]") if issues else ""))
        return None

    await _with_browser(cb)
    all_held = all(h for _, h in expectations)
    print("")
    print("=" * 48)
    for name, held in expectations:
        print("  [%s] %s" % ("ok" if held else "MISS", name))
    print("SELFTEST %s: %d/%d acceptance expectations held" %
          ("PASS" if all_held else "FAIL", sum(h for _, h in expectations), len(expectations)))
    return all_held


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8099")
    parser.add_argument("--out-dir", default=None)
    parser.add_argument("--check-elements", action="store_true",
                        help="also require header/agentList/chatCol visible (live portal only)")
    parser.add_argument("--selftest", action="store_true",
                        help="browser+loopback fixture proof")
    parser.add_argument("--logic-test", action="store_true",
                        help="browser-free judge() proof (no sockets; runs in sandboxed seats)")
    args = parser.parse_args()

    out_dir = args.out_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "breakpoint-evidence")

    if args.logic_test:
        return 0 if logic_test() else 1
    if args.selftest:
        try:
            ok = await run_selftest(out_dir)
        except Exception as e:
            print("FAIL: selftest could not run (browser/socket unavailable): %s" % e)
            print("NOTE: this seat blocks socket access (errno 10013); use --logic-test for a")
            print("      browser-free proof, or run --selftest on a non-sandbox seat.")
            return 2
        return 0 if ok else 1

    try:
        ok = await run_live(args.url, out_dir, check_elements=args.check_elements)
    except Exception as e:
        print("FAIL: could not run live gate: %s" % e)
        print("NOTE: sandbox seats block socket egress (errno 10013); run on a non-sandbox seat,")
        print("      or use --selftest/--logic-test for an offline proof.")
        return 2
    print("")
    print("=" * 48)
    print("GATE %s at 375/768" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
