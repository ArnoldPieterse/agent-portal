#!/usr/bin/env python3
"""Goal #4 (Responsive Layout 768px) acceptance verification.
Two modes:
  --static : parse ui/app.css, assert the 768px block implements the three
             responsive behaviours + flag explicit sub-44px touch targets.
             Runs with NO network egress (safe in sandbox).
  --cdp    : headless Edge live check at 127.0.0.1:8099 (needs browser egress).
Headless Edge via CDP. Checks at 768px:
  A. no page-level horizontal scroll (documentElement.scrollWidth <= viewport)
     (#fleetBody is allowed to scroll internally -> overflow-x:auto, clipped)
  B. sidebar collapsed to icon rail (aside width == 64px)
  C. fleet tab is a horizontal scroller (#fleetBody overflow-x auto/scroll)
  D. touch targets >= 44x44 px on all interactive elements
Writes memory/designer/breakpoint-evidence/goal4-768-<date>.json + screenshots.
"""
import asyncio, base64, json, os, subprocess, sys, time, urllib.request
from datetime import datetime

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
CDP_PORT = 9337
UDIR = os.path.join(os.getcwd(), ".unsloth-tmp", "edge_goal4")
PORTAL = "http://127.0.0.1:8099/"
DATE = datetime.now().strftime("%Y-%m-%d")
EVD = os.path.join("memory", "designer", "breakpoint-evidence")
os.makedirs(EVD, exist_ok=True); os.makedirs(UDIR, exist_ok=True)
from websockets.asyncio.client import connect

def log(m): print(time.strftime("%H:%M:%S ") + str(m), flush=True)
async def cdp(ws, method, params=None, _id=[0]):
    _id[0] += 1; await ws.send(json.dumps({"id": _id[0], "method": method, **(params or {})}))
    while True:
        r = json.loads(await ws.recv())
        if r.get("id") == _id[0]: return r
async def js(ws, expr):
    r = await cdp(ws, "Runtime.evaluate", {"expression": expr, "returnByValue": True})
    if "exceptionDetails" in r.get("result", {}): raise RuntimeError(r["result"]["exceptionDetails"])
    return r["result"].get("result", {}).get("value")
async def shot(ws, path):
    d = base64.b64decode((await cdp(ws, "Page.captureScreenshot", {"format":"png"}))["result"]["data"])
    open(path,"wb").write(d); log(f"  screenshot -> {path} ({len(d)} b)")

CHECK = r"""
(function(){
  const de=document.documentElement;
  const aside=document.querySelector('aside');
  const fleet=document.getElementById('fleetBody')||document.querySelector('#fleetBody');
  const cs=e=>e?getComputedStyle(e):null;
  // interactive elements
  const sel='button,a[href],input,select,textarea,[role=button],[tabindex]';
  let small=[];
  document.querySelectorAll(sel).forEach(el=>{
    if(!el.offsetParent && el.getClientRects().length===0) return; // hidden
    const r=el.getBoundingClientRect();
    if(r.width<=1||r.height<=1) return;
    if(r.width<44||r.height<44){
      small.push({t:(el.tagName+'.'+(el.className&&el.className.toString?el.className.toString().slice(0,30):'')),
                  w:Math.round(r.width),h:Math.round(r.height),txt:(el.textContent||'').trim().slice(0,20)});
    }
  });
  const fleetCs=fleet?cs(fleet):null;
  return JSON.stringify({
    scrollWidth:de.scrollWidth, innerWidth:window.innerWidth,
    pageOverflow: de.scrollWidth > window.innerWidth+2,
    asideW: aside?Math.round(aside.getBoundingClientRect().width):null,
    fleetOvX: fleetCs?fleetCs.overflowX:null,
    fleetScrollable: fleet?(fleet.scrollWidth>fleet.clientWidth+2):null,
    smallTargets: small
  });
})()
"""

async def main():
    if not os.path.exists(EDGE):
        log("FATAL: no Edge"); sys.exit(1)
    proc=subprocess.Popen([EDGE,"--headless=new",f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={UDIR}","--no-first-run","--disable-gpu","--window-size=768,900",PORTAL],
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    target=None
    for _ in range(30):
        await asyncio.sleep(1)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list") as r:
                for t in json.loads(r.read()):
                    if t.get("type")=="page" and ("8099" in t.get("url","") or "extension" not in t.get("url","")):
                        target=t["webSocketDebuggerUrl"]; break
        except Exception: pass
        if target: break
    if not target:
        log("FATAL: no CDP target"); proc.terminate(); sys.exit(1)
    async with connect(target) as ws:
        await cdp(ws,"Page.enable"); await cdp(ws,"Runtime.enable")
        await cdp(ws,"Emulation.setDeviceMetricsOverride",{"width":768,"height":900,"deviceScaleFactor":1,"mobile":False})
        await asyncio.sleep(3)
        data=json.loads(await js(ws,CHECK))
        await shot(ws, os.path.join(EVD,f"goal4-768-{DATE}.png"))
    proc.terminate()
    # evaluate
    A = not data.get("pageOverflow", True)
    B = (data.get("asideW") is not None and data.get("asideW") <= 64)
    C = (data.get("fleetOvX") in ("auto","scroll"))
    D = len(data.get("smallTargets",[]))==0
    res={"A_no_page_hscroll":A,"B_sidebar_icon_rail_64px":B,"C_fleet_horizontal_scroller":C,
         "D_touch_targets_ge_44":D, "all_pass": all([A,B,C,D]), "raw":data}
    out=os.path.join(EVD,f"goal4-768-{DATE}.json")
    json.dump(res,open(out,"w"),indent=2)
    log(f"\n{'='*40}")
    for k in ["A_no_page_hscroll","B_sidebar_icon_rail_64px","C_fleet_horizontal_scroller","D_touch_targets_ge_44"]:
        log(f"  {k}: {'PASS' if res[k] else 'FAIL'}")
    if data.get("smallTargets"):
        for s in data["smallTargets"][:10]: log(f"    small: {s}")
    log(f"  ALL PASS: {res['all_pass']}")
    log(f"Evidence: {out}")

def static_check():
    import re
    css = open(os.path.join("ui","app.css"), encoding="utf-8").read()
    m = re.search(r"@media\s*\(max-width:\s*768px\)\s*\{(.*?)\n\s*\}\s*\n\s*@media", css, re.S)
    block = m.group(1) if m else ""
    def has(pat): return bool(re.search(pat, block))
    # A. fleet is the internal horizontal scroller (overflow-x:auto) -> page stays fixed
    a_fleet_scroller = has(r"#fleetBody\{[^}]*overflow-x:auto")
    # B. sidebar icon rail: aside collapsed to a fixed width <=64px
    _ab = re.search(r"aside\{width:(\d+)px", block)
    b_rail = bool(_ab) and int(_ab.group(1)) <= 64
    # C. chat full width -> acard text hidden AND per-card micro-actions hidden (icon rail)
    c_chat_full = has(r"\.acard \.nm\{display:none") and has(r"\.acard button\{display:none")
    # D. touch targets >=44px: only INTERACTIVE selectors matter (matches the live CDP
    #    element set). A rule satisfies if its effective width AND height are >=44
    #    (explicit w/h or min-w/min-h); display:none rules are exempt.
    small=[]
    for sel, body in re.findall(r"([.#][A-Za-z0-9_.\-# ]+?)\{([^}]*)\}", block):
        if "display:none" in body: continue
        interactive = ("button" in sel) or sel.startswith("#send") or sel.startswith("#attach") \
                      or ("input" in sel) or ("[role=button]" in sel)
        if not interactive: continue
        w  = re.search(r"(?:^|;|\{)width\s*:\s*(\d+)px", body);   mw = re.search(r"min-width\s*:\s*(\d+)px", body)
        h  = re.search(r"(?:^|;|\{)height\s*:\s*(\d+)px", body);  mh = re.search(r"min-height\s*:\s*(\d+)px", body)
        wv = int(w.group(1)) if w else (int(mw.group(1)) if mw else None)
        hv = int(h.group(1)) if h else (int(mh.group(1)) if mh else None)
        if wv is not None and hv is not None and (wv<44 or hv<44):
            small.append({"sel":sel,"w":wv,"h":hv})
    d_ok = len(small)==0
    res={"A_fleet_horizontal_scroller":a_fleet_scroller,
         "B_sidebar_icon_rail_64px":b_rail,
         "C_chat_full_width_text_hidden":c_chat_full,
         "D_no_explicit_sub44_touch_targets":d_ok,
         "all_pass": all([a_fleet_scroller,b_rail,c_chat_full,d_ok]),
         "small_targets_flagged":small}
    out=os.path.join(EVD,f"goal4-768-static-{DATE}.json")
    json.dump(res,open(out,"w"),indent=2)
    for k in ["A_fleet_horizontal_scroller","B_sidebar_icon_rail_64px","C_chat_full_width_text_hidden","D_no_explicit_sub44_touch_targets"]:
        log(f"  {k}: {'PASS' if res[k] else 'FAIL'}")
    if small: 
        for s in small: log(f"    flagged: {s}")
    log(f"  ALL PASS(static): {res['all_pass']}")
    log(f"Evidence: {out}")
    return res["all_pass"]

if __name__=="__main__":
    if "--static" in sys.argv:
        static_check()
    else:
        asyncio.run(main())
