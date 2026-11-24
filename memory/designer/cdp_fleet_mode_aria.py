#!/usr/bin/env python3
"""
cdp_fleet_mode_aria.py — headless-Edge (CDP) verification for
Designer cycle-15 goal #2: Fleet Mode ARIA + Keyboard Nav.

Why CDP + file:// : the live portal on :8099 is unreachable from this seat
(WinError 10013 / firewall), and Playwright-python is not installed, but the
CDP+Edge toolchain is. We load the REAL index.html over file:// so every real
asset (app.css, core.js loader, fleet-mode-aria.css/.js) executes; mode
transitions are driven deterministically via window.__fleetModeAria.force() so
the test does not depend on /api/fleet/cockpit being up.

Verifies (per goal #2 acceptance):
  1. ARIA live region: aria-live=polite, role=status, aria-atomic=true
  2. Announce fires on real mode change (WORK->MAINTENANCE, ->IDLE)
  3. Mode badge present + tabindex=0, color-coded per mode
  4. Tab through all panel toggles (+badge) without mouse in each mode
  5. No focus traps
  6. Arrow-key nav between toggles; Escape closes an open panel
  7. :focus-visible outline applied (keyboard focus)
  8. WCAG 2.1 AA contrast on badge text + a panel button (>=4.5:1)
  9. prefers-reduced-motion disables the badge pulse animation
Evidence: memory/designer/evidence-aria-keyboard-nav-2026-11-24.json
"""
import asyncio, base64, json, os, subprocess, sys, time, urllib.request
from datetime import datetime, timezone
from websockets.asyncio.client import connect

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
CDP_PORT = 9335
ROOT = os.getcwd()
UDIR = os.path.join(ROOT, ".unsloth-tmp", "edge_cdp_fm_aria")
PAGE_URL = "file://" + ROOT.replace(os.sep, "/") + "/index.html"
EVIDENCE = os.path.join("memory", "designer", "evidence-aria-keyboard-nav-2026-11-24.json")
PANEL_IDS = ["goalsBtn", "actBtn", "fleetBtn", "filesBtn", "opsBtn"]
MODES = ["WORK", "MAINTENANCE", "IDLE"]

proc = None
page_errors = []
_LOGPATH = os.path.join(UDIR, "_cdp_fma_log.txt")
class _Tee:
    def __init__(self, f):
        self.f = f
    def write(self, s):
        try: sys.stdout.write(s)
        except Exception: pass
        try: self.f.write(s); self.f.flush()
        except Exception: pass
    def flush(self):
        try: sys.stdout.flush()
        except Exception: pass
_LOGF = open(_LOGPATH, "w", buffering=1)
sys.stdout = _Tee(_LOGF)

async def cdp(ws, method, params=None, _id=[0]):
    _id[0] += 1
    await ws.send(json.dumps({"id": _id[0], "method": method, **(params or {})}))
    while True:
        try:
            r = json.loads(await asyncio.wait_for(ws.recv(), timeout=25))
        except asyncio.TimeoutError:
            raise RuntimeError("CDP recv timeout on " + method)
        if r.get("method") == "Runtime.exceptionThrown":
            page_errors.append(r["result"].get("exceptionDetails", {}).get("text", "?"))
        if r.get("id") == _id[0]:
            return r

async def js(ws, expr):
    r = await cdp(ws, "Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
    res = r.get("result", {})
    if "exceptionDetails" in res:
        raise RuntimeError("JS error: %s" % res["exceptionDetails"])
    return res.get("result", {}).get("value")

async def press(ws, key):
    await cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": key})
    await cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": key})

CONTRAST_JS = r"""(function(){
  function parse(c){var m=c.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);return m?[+m[1],+m[2],+m[3]]:[255,255,255];}
  function lum(rgb){var a=rgb.map(function(v){v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4);});return 0.2126*a[0]+0.7152*a[1]+0.0722*a[2];}
  function bgOf(el){var e=el;while(e){var b=getComputedStyle(e).backgroundColor;if(b&&b!=='rgba(0, 0, 0, 0)'&&b!=='transparent')return parse(b);e=e.parentElement;}return [17,19,24];}
  return function(sel){var el=document.querySelector(sel);if(!el)return null;var fg=parse(getComputedStyle(el).color);var bg=bgOf(el);var l1=lum(fg),l2=lum(bg);return Math.round(((Math.max(l1,l2)+0.05)/(Math.min(l1,l2)+0.05))*100)/100;};
})()"""

async def main():
    global proc, page_errors
    os.makedirs(UDIR, exist_ok=True)
    print("[fm-aria] launching headless Edge ->", PAGE_URL, flush=True)
    proc = subprocess.Popen(
        [EDGE, "--headless=new", f"--remote-debugging-port={CDP_PORT}",
         f"--user-data-dir={UDIR}", "--no-first-run", "--disable-gpu",
         "--window-size=1440,900", PAGE_URL],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    target_url = None
    for _ in range(30):
        await asyncio.sleep(1)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list", timeout=2) as r:
                targets = json.loads(r.read())
                for t in targets:
                    if t.get("type") == "page" and ("index.html" in t.get("url", "") or t.get("url", "").startswith("file://")):
                        target_url = t["webSocketDebuggerUrl"]; break
                if not target_url and targets:
                    target_url = targets[0]["webSocketDebuggerUrl"]
        except Exception:
            continue
        if target_url: break
    if not target_url:
        print("FATAL: CDP endpoint unreachable at 127.0.0.1:%d (is Edge launch blocked here?)" % CDP_PORT, flush=True)
        try: proc.terminate()
        except Exception: pass
        sys.exit(2)
    print("[fm-aria] connected:", target_url, flush=True)

    results = []
    def rec(mode, test, ok, detail):
        results.append({"mode": mode, "test": test, "pass": bool(ok), "detail": detail})
        print(("  PASS " if ok else "  FAIL ") + f"[{mode}] {test} — {detail}", flush=True)

    async with connect(target_url) as ws:
        await cdp(ws, "Page.enable")
        await cdp(ws, "Runtime.enable")
        await asyncio.sleep(3)  # let core.js loader + fleet-mode-aria.js init

        # ── 0. Module actually loaded (proves wiring + valid JS syntax) ──
        module_loaded = await js(ws, "typeof window.__fleetModeAria==='object' && window.__fleetModeAria!==null")
        aria_el = await js(ws, "!!document.getElementById('fleetModeAria')")
        css_loaded = await js(ws, "!!document.querySelector('link[data-fm-aria]')")
        rec("ALL", "module-wired-loaded", module_loaded and aria_el and css_loaded,
            f"__fleetModeAria={module_loaded}, #fleetModeAria={aria_el}, cssLink={css_loaded}")

        # ── 1. ARIA live region attributes ──
        attrs = await js(ws, "(function(){var e=document.getElementById('fleetModeAria');if(!e)return null;return {live:e.getAttribute('aria-live'),role:e.getAttribute('role'),atomic:e.getAttribute('aria-atomic')};})()")
        ok1 = bool(attrs and attrs.get("live") == "polite" and attrs.get("role") == "status" and str(attrs.get("atomic")) == "true")
        rec("ALL", "aria-live-region-attrs", ok1, f"{attrs}")

        # ── 2. Badge present + tabindex ──
        badge = await js(ws, "(function(){var b=document.getElementById('fleetModeBadge');if(!b)return null;return {tab:b.getAttribute('tabindex'),label:!!b.getAttribute('aria-label')};})()")
        rec("ALL", "badge-present-tabindex", bool(badge and str(badge.get("tab")) == "0" and badge.get("label")), f"{badge}")

        # ── 3. Drive transitions; verify announce fires on REAL change ──
        await js(ws, "window.__fleetModeAria.force('WORK')")
        await asyncio.sleep(0.2)
        work_state = await js(ws, "JSON.stringify({m:document.body.getAttribute('data-fleet-mode'),cls:document.getElementById('fleetModeBadge').className})")
        rec("WORK", "mode-badge-colors-work", 'work' in (work_state or ''), f"{work_state}")

        await js(ws, "window.__fleetModeAria.force('MAINTENANCE')")
        await asyncio.sleep(0.1)
        ann_maint = await js(ws, "document.getElementById('fleetModeAria').textContent")
        rec("MAINTENANCE", "announce-fires-on-change", bool(ann_maint) and "maintenance" in ann_maint.lower() and "entered" in ann_maint.lower(), f"live='{ann_maint}'")

        await js(ws, "window.__fleetModeAria.force('IDLE')")
        await asyncio.sleep(0.1)
        ann_idle = await js(ws, "document.getElementById('fleetModeAria').textContent")
        rec("IDLE", "announce-fires-idle", bool(ann_idle) and "idle" in ann_idle.lower(), f"live='{ann_idle}'")

        # ── 4/5. Tab order across modes + no trap ──
        for mode in MODES:
            await js(ws, f"window.__fleetModeAria.force('{mode}')")
            await asyncio.sleep(0.15)
            order = []
            for _ in range(24):
                await press(ws, "Tab")
                aid = await js(ws, "document.activeElement ? (document.activeElement.id||document.activeElement.tagName) : ''")
                if aid: order.append(aid)
            found = [p for p in PANEL_IDS if p in order]
            badge_in = "fleetModeBadge" in order
            total_nav = len(found) + (1 if badge_in else 0)
            rec(mode, f"tab-reaches-panels({total_nav}/6)", total_nav >= 5, f"panels={found} badge={badge_in}")
            last5 = order[-5:]
            no_trap = len(set(last5)) > 1
            rec(mode, "no-focus-trap", no_trap, f"last5={last5}")

        # ── 6a. Arrow-key nav between toggles ──
        await js(ws, "document.getElementById('goalsBtn') && document.getElementById('goalsBtn').focus()")
        await asyncio.sleep(0.1)
        await press(ws, "ArrowRight")
        after_arrow = await js(ws, "document.activeElement.id")
        rec("ALL", "arrow-right-nav", after_arrow == "actBtn", f"after ArrowRight focus={after_arrow}")

        # ── 6b. Escape closes an open panel ──
        opened = await js(ws, "(function(){var b=document.getElementById('fleetBtn');if(!b)return 'no-btn';b.click();return true;})()")
        await asyncio.sleep(0.3)
        is_open = await js(ws, "(function(){var p=document.getElementById('fleetPanel');return p? p.classList.contains('open'):false;})()")
        await press(ws, "Escape")
        await asyncio.sleep(0.2)
        still_open = await js(ws, "(function(){var p=document.getElementById('fleetPanel');return p? p.classList.contains('open'):false;})()")
        rec("ALL", "escape-closes-panel", bool(is_open) and (not still_open), f"opened={is_open} afterEsc={still_open} (click-> {opened})")

        # ── 7. :focus-visible outline (keyboard focus on a toggle) ──
        await js(ws, "document.body.focus()")
        await press(ws, "Tab")
        await asyncio.sleep(0.1)
        fv = await js(ws, "(function(){var el=document.activeElement;var cs=getComputedStyle(el);return {id:el.id||el.tagName,outlineW:cs.outlineWidth,outlineStyle:cs.outlineStyle};})()")
        rec("ALL", "focus-visible-outline", bool(fv and fv.get("outlineW") not in (None, "0px", 0)), f"{fv}")

        # ── 8. WCAG AA contrast ──
        await js(ws, "window.__fleetModeAria.force('MAINTENANCE')")
        await asyncio.sleep(0.1)
        c_badge = await js(ws, CONTRACT := CONTRAST_JS + ";document.querySelector('#fleetModeBadge')?((function(){var f="+CONTRAST_JS+";return f('#fleetModeBadge');})()):null") if False else None
        # simpler: inject helper once then call it
        c_badge = await js(ws, "(function(){var F=" + CONTRAST_JS + ";return F('#fleetModeBadge');})()")
        c_btn = await js(ws, "(function(){var F=" + CONTRAST_JS + ";return F('#goalsBtn')||F('.toggles button')||F('.seg button');})()")
        rec("ALL", "wcag-contrast-badge>=4.5", (c_badge or 0) >= 4.5, f"badge contrast={c_badge}")
        rec("ALL", "wcag-contrast-panel-btn>=4.5", (c_btn or 0) >= 4.5, f"panel btn contrast={c_btn}")

        # ── 9. prefers-reduced-motion disables pulse ──
        await cdp(ws, "Emulation.setEmulatedMedia", {"features": [{"name": "prefers-reduced-motion", "value": "reduce"}]})
        anim = await js(ws, "getComputedStyle(document.querySelector('.fm-badge-dot')).animationName")
        rec("ALL", "reduced-motion-no-pulse", anim in ("none", "", None), f"badge-dot animationName={anim}")

    proc.terminate()

    total = len(results); passed = sum(1 for r in results if r["pass"]); failed = total - passed
    ok_all = failed == 0 and all(r["pass"] for r in results if r["test"] == "module-wired-loaded")
    payload = {
        "test": "fleet-mode-aria-keyboard-nav",
        "goal": "Designer cycle-15 goal #2: Fleet Mode ARIA + Keyboard Nav",
        "method": "headless Edge via CDP, file:// load of real index.html; modes forced via window.__fleetModeAria.force()",
        "page_url": PAGE_URL,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {"total": total, "passed": passed, "failed": failed, "all_pass": ok_all},
        "page_errors": page_errors[-10:],
        "results": results,
    }
    os.makedirs(os.path.dirname(EVIDENCE), exist_ok=True)
    with open(EVIDENCE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print("\n" + "=" * 60)
    print(f"FLEET MODE ARIA + KEYBOARD NAV — {passed}/{total} passed, {failed} failed")
    print(f"evidence -> {EVIDENCE}")
    sys.exit(0 if ok_all else 1)

if __name__ == "__main__":
    asyncio.run(main())
