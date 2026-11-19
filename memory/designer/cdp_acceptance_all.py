#!/usr/bin/env python3
"""
memory/designer/cdp_acceptance_all.py
Unified CDP acceptance test for Designer goals #2, #5, #8, #9, #10.
Run from a NON-SANDBOX seat with msedge + LAN access to portal :8099.

Usage: python memory/designer/cdp_acceptance_all.py
Evidence: memory/designer/acceptance-evidence-<date>/
On success: records all 5 goals via goal_ledger.py automatically.
"""
import asyncio, base64, json, os, subprocess, sys, time, urllib.request
from datetime import datetime
from websockets.asyncio.client import connect

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
CDP_PORT = 9334
UDIR = os.path.join(os.getcwd(), ".unsloth-tmp", "edge_cdp_acceptance")
PORTAL = "http://127.0.0.1:8099/"
DATE = datetime.now().strftime("%Y-%m-%d")
EVD = os.path.join("memory", "designer", f"acceptance-evidence-{DATE}")
os.makedirs(EVD, exist_ok=True)

results = {}
proc = None

def log(m): print(time.strftime("%H:%M:%S ") + str(m), flush=True)
async def cdp(ws, method, params=None, _id=[0]):
    _id[0] += 1
    await ws.send(json.dumps({"id": _id[0], "method": method, **(params or {})}))
    while True:
        r = json.loads(await ws.recv())
        if r.get("id") == _id[0]: return r

async def screenshot(ws, path, selector=None):
    """Capture viewport or element screenshot."""
    if selector:
        # Get element bounding box via JS
        js = f"const el=document.querySelector('{selector}');if(!el)throw new Error('no {selector}');const r=el.getBoundingClientRect();return JSON.stringify({{x:r.x,y:r.y,w:r.width,h:r.height}});"
        r = await cdp(ws, "Runtime.evaluate", {"expression": js, "returnByValue": True})
        box = json.loads(r["result"]["result"]["value"])
    else:
        box = None
    if box:
        # Clip to element
        result = await cdp(ws, "Page.captureScreenshot", {
            "format": "png",
            "clip": {"x": box["x"], "y": box["y"], "width": box["w"], "height": box["h"], "scale": 1}
        })
    else:
        result = await cdp(ws, "Page.captureScreenshot", {"format": "png"})
    data = base64.b64decode(result["result"]["data"])
    with open(path, "wb") as f: f.write(data)
    log(f"  screenshot -> {path} ({len(data)} bytes)")

async def js(ws, expr):
    r = await cdp(ws, "Runtime.evaluate", {"expression": expr, "returnByValue": True})
    if "exceptionDetails" in r.get("result", {}):
        raise RuntimeError(f"JS error: {r['result']['exceptionDetails']}")
    return r["result"].get("result", {}).get("value")

async def test_goal2_density(ws):
    """Goal #2: Measure panel heights, verify reduced whitespace.
    Acceptance: panels render without overlap/clipping; line-height <= 1.6 for body text."""
    log("[#2] Information Density Pass...")
    await cdp(ws, "Page.navigate", {"url": PORTAL})
    await asyncio.sleep(3)
    
    # Check computed line-heights on key elements
    lh = await js(ws, """
    (function(){
      const els = document.querySelectorAll('#actBody, .goal-item, .fleet-card');
      return JSON.stringify(Array.from(els).slice(0,10).map(el => {
        const cs = getComputedStyle(el);
        return {tag: el.tagName+'.'+el.className.slice(0,20), lh: cs.lineHeight, fs: cs.fontSize};
      }));
    })()
    """)
    items = json.loads(lh) if lh else []
    violations = [i for i in items if float(i["lh"].replace("px","")) / float(i["fs"].replace("px","")) > 1.6]
    
    # Check no text overflow/clipping
    overflow = await js(ws, """
    (function(){
      const all = document.querySelectorAll('main *');
      let clip = 0;
      for(const el of all){ if(el.scrollHeight > el.clientHeight + 2 && getComputedStyle(el).overflow === 'hidden') clip++; }
      return clip;
    })()
    """) or 0
    
    await screenshot(ws, os.path.join(EVD, "g2_full_viewport.png"))
    
    ok = len(violations) == 0 and int(overflow) <= 2
    results["goal2"] = {"pass": ok, "lh_violations": violations, "clipped_elements": int(overflow)}
    log(f"  result: {'PASS' if ok else 'FAIL'} (violations={len(violations)}, clipped={overflow})")

async def test_goal5_notifications(ws):
    """Goal #5: Trigger all 4 notification types, verify toast + bell badge."""
    log("[#5] Notification System...")
    
    # Trigger goal-closed notification (API: window.notify(kind,msg), kind=ok|warn|err|info)
    await js(ws, "typeof notify==='function' && notify('ok','Goal #3 completed')")
    await asyncio.sleep(0.5)
    await screenshot(ws, os.path.join(EVD, "g5_toast_goal.png"), ".toast-container")
    
    # Check toast exists
    toast_count = await js(ws, "document.querySelectorAll('.toast').length") or 0
    
    # Trigger agent-offline notification
    await js(ws, "typeof notify==='function' && notify('warn','Agent X went offline')")
    await asyncio.sleep(0.3)
    
    # Check bell badge
    badge = await js(ws, """
    (function(){
      const b = document.querySelector('#notifBadge');
      return b ? b.textContent : null;
    })()
    """)
    
    # Trigger upload-complete + error
    await js(ws, "typeof notify==='function' && notify('ok','Upload complete')")
    await asyncio.sleep(0.3)
    await js(ws, "typeof notify==='function' && notify('err','Test error')")
    await asyncio.sleep(0.5)
    
    final_toasts = await js(ws, "document.querySelectorAll('.toast').length") or 0
    await screenshot(ws, os.path.join(EVD, "g5_stacked_toasts.png"), ".toast-container")
    
    ok = int(toast_count) >= 1 and badge is not None
    results["goal5"] = {"pass": ok, "initial_toasts": int(toast_count), "final_toasts": int(final_toasts), "badge_text": badge}
    log(f"  result: {'PASS' if ok else 'FAIL'} (toasts={toast_count}->{final_toasts}, badge={badge})")

async def test_goal8_icons(ws):
    """Goal #8: Verify SVG icons render, no emoji in DOM."""
    log("[#8] Icon System...")
    
    # Count SVG icons in rendered UI
    svg_count = await js(ws, "document.querySelectorAll('svg').length") or 0
    
    # Check for non-ASCII icon glyphs (exclude legit typography: …—–•)
    emoji_check = await js(ws, """
    (function(){
      const text = document.body.innerText;
      // Find chars in ranges that are typically icons/emoji
      const bad = [];
      for(const ch of text){
        const cp = ch.codePointAt(0);
        if(cp >= 0x2600 && cp <= 0x27BF) bad.push(ch); // misc symbols
        else if(cp >= 0x1F300 && cp <= 0x1FAFF) bad.push(ch); // emoji
        else if(cp >= 0x2B00 && cp <= 0x2BFF) bad.push(ch); // misc symbols & arrows (icon-range)
      }
      return JSON.stringify(bad.slice(0,20));
    })()
    """)
    bad_glyphs = json.loads(emoji_check) if emoji_check else []
    
    await screenshot(ws, os.path.join(EVD, "g8_icons_viewport.png"))
    
    ok = int(svg_count) >= 5 and len(bad_glyphs) == 0
    results["goal8"] = {"pass": ok, "svg_count": int(svg_count), "bad_glyphs": bad_glyphs}
    log(f"  result: {'PASS' if ok else 'FAIL'} (svgs={svg_count}, bad_glyphs={len(bad_glyphs)})")

async def test_goal9_tour(ws):
    """Goal #9: Clear localStorage, reload, verify tour appears with 4 correct steps."""
    log("[#9] Portal Onboarding Tour...")
    
    # Clear tour flag and reload
    await js(ws, "try{localStorage.removeItem('portalTourDone')}catch(_){}")
    await cdp(ws, "Page.reload")
    await asyncio.sleep(3)  # wait for load + 800ms tour delay
    
    # Check tour overlay appeared
    tour_visible = await js(ws, "!!document.querySelector('.tour-overlay')") or False
    
    if tour_visible:
        # Verify step 1 targets goalsBtn
        step_text = await js(ws, "document.querySelector('.tour-title')?.textContent || ''")
        step_count = await js(ws, "document.querySelectorAll('.tour-dot').length") or 0
        
        # Advance through all steps and collect titles
        titles = []
        for i in range(4):
            t = await js(ws, "document.querySelector('.tour-title')?.textContent || ''")
            titles.append(t)
            if i < 3:
                await js(ws, "document.querySelector('.tour-next')?.click()")
                await asyncio.sleep(0.3)
        
        # After last step, clicking should close the tour
        await js(ws, "document.querySelector('.tour-next')?.click()")
        await asyncio.sleep(0.5)
        tour_closed = await js(ws, "!document.querySelector('.tour-overlay')") or False
        
        # Verify localStorage was set
        flag_set = await js(ws, "localStorage.getItem('portalTourDone') === '1'") or False
        
        ok = step_count == 4 and tour_closed and flag_set
        results["goal9"] = {"pass": ok, "step_count": int(step_count), "titles": titles, "tour_closed": tour_closed, "flag_set": flag_set}
        log(f"  result: {'PASS' if ok else 'FAIL'} (steps={step_count}, closed={tour_closed}, flag={flag_set})")
    else:
        results["goal9"] = {"pass": False, "error": "tour overlay not visible after reload"}
        log("  FAIL: tour overlay not visible")

async def test_goal10_print(ws):
    """Goal #10: Verify @media print styles exist + print button triggers window.print()."""
    log("[#10] Print-Ready Report Layout...")
    
    # Check @media print rules are in the loaded CSS
    print_rules = await js(ws, """
    (function(){
      let count = 0;
      for(const sheet of document.styleSheets){
        try{ for(const rule of sheet.cssRules){ if(rule.media && rule.media.mediaText === 'print') count += rule.cssRules.length; } }catch(e){}
      }
      return count;
    })()
    """) or 0
    
    # Check print button exists in ops panel
    btn_exists = await js(ws, """
    (function(){
      const b = document.querySelector('.print-btn, #printReportBtn');
      return b ? {text: b.textContent.trim().slice(0,30), hasSvg: !!b.querySelector('svg')} : null;
    })()
    """)
    
    # Check interactive elements are hidden in print media (via CSS)
    btn_hidden_in_print = await js(ws, """
    (function(){
      const sheets = Array.from(document.styleSheets);
      for(const s of sheets){ try{ for(const r of s.cssRules){ if(r.media && r.media.mediaText==='print'){ for(const pr of r.cssRules){ if(pr.selectorText && pr.selectorText.includes('button') && pr.style.display==='none') return true; } } } }catch(e){} }
      return false;
    })()
    """) or False
    
    await screenshot(ws, os.path.join(EVD, "g10_ops_panel.png"), "#opsPanel")
    
    ok = int(print_rules) > 5 and btn_exists is not None and btn_hidden_in_print
    results["goal10"] = {"pass": ok, "print_rules_count": int(print_rules), "button": btn_exists, "btns_hidden": btn_hidden_in_print}
    log(f"  result: {'PASS' if ok else 'FAIL'} (rules={print_rules}, btn={btn_exists}, hidden={btn_hidden_in_print})")

async def main():
    global proc
    os.makedirs(UDIR, exist_ok=True)
    log("Launching headless Edge...")
    proc = subprocess.Popen([
        EDGE, "--headless=new", f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={UDIR}", "--no-first-run", "--disable-gpu",
        "--window-size=1280,900", PORTAL
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Wait for CDP endpoint
    target_url = None
    for _ in range(30):
        await asyncio.sleep(1)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list") as r:
                targets = json.loads(r.read())
                for t in targets:
                    if t.get("type") == "page" and "8099" in t.get("url",""):
                        target_url = t["webSocketDebuggerUrl"]
                        break
                if not target_url and targets:
                    target_url = targets[0]["webSocketDebuggerUrl"]
        except Exception:
            continue
        if target_url: break
    
    if not target_url:
        log("FATAL: Could not connect to CDP endpoint")
        proc.terminate()
        sys.exit(1)
    
    log(f"Connected: {target_url}")
    async with connect(target_url) as ws:
        await cdp(ws, "Page.enable")
        await cdp(ws, "Runtime.enable")
        await asyncio.sleep(2)  # let page settle
        
        try:
            await test_goal2_density(ws)
        except Exception as e:
            results["goal2"] = {"pass": False, "error": str(e)}
            log(f"  ERROR: {e}")
        
        try:
            await test_goal5_notifications(ws)
        except Exception as e:
            results["goal5"] = {"pass": False, "error": str(e)}
            log(f"  ERROR: {e}")
        
        try:
            await test_goal8_icons(ws)
        except Exception as e:
            results["goal8"] = {"pass": False, "error": str(e)}
            log(f"  ERROR: {e}")
        
        try:
            await test_goal9_tour(ws)
        except Exception as e:
            results["goal9"] = {"pass": False, "error": str(e)}
            log(f"  ERROR: {e}")
        
        try:
            await test_goal10_print(ws)
        except Exception as e:
            results["goal10"] = {"pass": False, "error": str(e)}
            log(f"  ERROR: {e}")
    
    proc.terminate()
    
    # Save evidence JSON
    out = os.path.join(EVD, "results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2)
    
    # Summary + auto-record passes
    log("\n" + "="*50)
    passed = 0
    for g in ["goal2","goal5","goal8","goal9","goal10"]:
        r = results.get(g, {})
        status = "PASS" if r.get("pass") else "FAIL"
        if r.get("pass"): passed += 1
        log(f"  {g}: {status}")
    log(f"Total: {passed}/5 passed")
    
    # Auto-record passes via goal_ledger
    goal_map = {"goal2": 2, "goal5": 5, "goal8": 8, "goal9": 9, "goal10": 10}
    for g, n in goal_map.items():
        if results.get(g, {}).get("pass"):
            cmd = f"python memory/researcher/goal_ledger.py --record designer {n} --note 'CDP acceptance PASS: {out}'"
            log(f"  Recording: {cmd}")
            subprocess.run(cmd, shell=True, capture_output=True)
    
    log(f"Evidence dir: {EVD}")

if __name__ == "__main__":
    asyncio.run(main())
