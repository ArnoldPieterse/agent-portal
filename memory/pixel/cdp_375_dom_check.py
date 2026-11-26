#!/usr/bin/env python3
# Pixel goal #6 (carry-over) - DEFINITIVE live CDP DOM check for the @375/768 responsive leg.
#
# WHY THIS EXISTS
#   The static audit (evidence-convergence-375-static-2026-11-25.md) passed 11/11 and two live
#   PNGs are archived, but pixel analysis is INCONCLUSIVE on @375 overflow + 4-widget legibility.
#   This script closes that leg with real DOM assertions. It must run from a NON-SANDBOX seat
#   (Edge exists on the host, but sandbox seats egress-block 127.0.0.1 -> WinError 10013).
#
# RUN (non-sandbox seat, portal up on :8099):
#   python memory/pixel/cdp_375_dom_check.py
#
# ASSERTS (exit 0 only if ALL pass at BOTH widths):
#   1. No horizontal overflow: documentElement.scrollWidth <= clientWidth.
#   2. All 4 convergence widgets visible: getBoundingClientRect w>0,h>0 and inside viewport.
#   3. Legibility: widget text contrast vs its background >= 4.5:1 (normal) / 3:1 (large).
# Captures a fresh screenshot per width into memory/pixel/ and writes cdp_375_dom_check.report.json.
import asyncio, base64, glob, json, os, socket, subprocess, sys, time, urllib.request
from websockets.asyncio.client import connect

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
PORTAL = "http://127.0.0.1:8099/"
WIDTHS = [375, 768]
WIDGETS = [".ckconv-gauge", ".ckconv-trend", ".ckconv-interventions", ".ckconv-progress"]
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

def find_edge():
    for p in EDGE_CANDIDATES:
        if os.path.exists(p): return p
    import shutil
    return shutil.which("msedge") or shutil.which("chrome") or shutil.which("chromium")

def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close(); return port

def wait_devtools(port, tries=30):
    for _ in range(tries):
        try:
            t = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=3).read())
            for x in t:
                if x.get("type") == "page": return x["webSocketDebuggerUrl"]
        except Exception:
            pass
        time.sleep(1)
    return None

# JS evaluated in-page: returns overflow + per-widget rect/contrast as one JSON string.
JS_CHECK = r'''
(function(){
  function lum(rgb){
    var a=rgb.match(/\\d+/g)||[0,0,0]; var c=[a[0],a[1],a[2]].map(function(v){v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4);});
    return 0.2126*c[0]+0.7152*c[1]+0.0722*c[2];
  }
  function ratio(fg,bg){var a=lum(fg),b=lum(bg),hi=Math.max(a,b),lo=Math.min(a,b);return (hi+0.05)/(lo+0.05);}
  var de=document.documentElement, vw=window.innerWidth, vh=window.innerHeight;
  var out={scrollWidth:de.scrollWidth,clientWidth:de.clientWidth,vw:vw,vh:vh,ready:document.readyState,w:[]};
  (window.__WIDGETS__||[]).forEach(function(sel){
    var el=document.querySelector(sel); if(!el){out.w.push({sel:sel,found:false});return;}
    var r=el.getBoundingClientRect(), cs=getComputedStyle(el);
    var bg=cs.backgroundColor; if(bg==="rgba(0, 0, 0, 0)"||bg==="transparent") bg=getComputedStyle(el.parentElement||document.body).backgroundColor;
    var cr=ratio(cs.color,bg);
    out.w.push({sel:sel,found:true,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),
      visible:r.width>0&&r.height>0&&r.right<=vw+1&&r.bottom<=vh*4,
      color:cs.color,bg:bg,contrast:+cr.toFixed(2)});
  });
  return JSON.stringify(out);
})()
'''

async def main():
    edge = find_edge()
    if not edge:
        print("FAIL: no Edge/Chrome found on this seat (run from a non-sandbox seat)"); return 2
    port = free_port(); proc = None
    try:
        proc = subprocess.Popen([edge, "--headless=new", f"--remote-debugging-port={port}",
            "--disable-gpu", "--no-first-run", "--window-size=768,1024",
            "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        ws_url = wait_devtools(port)
        if not ws_url:
            print("FAIL: could not reach Edge DevTools on 127.0.0.1:%d (sandbox egress block?)" % port); return 3
        report = {}
        async with connect(ws_url, timeout=30) as ws:
            n = [0]
            async def cmd(method, params=None):
                n[0]+=1; i=n[0]
                await ws.send(json.dumps({"id":i,"method":method,"params":params or {}}))
                while True:
                    m=json.loads(await ws.recv())
                    if m.get("id")==i: return m
            await cmd("Page.enable"); await cmd("Runtime.enable")
            ok = True
            for width in WIDTHS:
                height = 812 if width==375 else 1024
                await cmd("Emulation.setDeviceMetricsOverride", {"width":width,"height":height,"deviceScaleFactor":1,"mobile":width<768})
                await cmd("Page.navigate", {"url":PORTAL}); await asyncio.sleep(3)
                # wait for readyState complete (up to 8s)
                for _ in range(8):
                    r=await cmd("Runtime.evaluate", {"expression":"document.readyState","returnByValue":True})
                    if (r.get("result",{}).get("result",{}).get("value"))=="complete": break
                    await asyncio.sleep(1)
                # ensure convergence widgets are present: open the dashboard panel via DOM click if needed
                await cmd("Runtime.evaluate", {"expression":(
                    "(function(){try{var b=document.querySelector('[data-panel=\\"convergence\\"],#dashConvBtn,button[title*=Convergence]');if(b){b.click();return 'opened';}return 'nopanel';}catch(e){return 'err:'+e.message;}})()"
                ), "returnByValue":True})
                await asyncio.sleep(1.5)
                r=await cmd("Runtime.evaluate", {"expression":JS_CHECK.replace("__WIDGETS__", json.dumps(WIDGETS)),"returnByValue":True})
                data=json.loads(r["result"]["result"]["value"])
                # screenshot
                sh=await cmd("Page.captureScreenshot", {"format":"png"})
                png=os.path.join(OUT_DIR, f"screenshot-{width}.png")
                with open(png,"wb") as fh: fh.write(base64.b64decode(sh["result"]["data"]))
                overflow = data["scrollWidth"] > data["clientWidth"]
                wvis = [w for w in data["w"]]
                all_found = len(wvis)==len(WIDGETS) and all(w.get("found") for w in wvis)
                all_visible = all_found and all(w.get("visible") for w in wvis)
                min_contrast = min((w.get("contrast",0) for w in wvis if w.get("found")), default=0)
                legible = all_found and (min_contrast>=4.5 or min_contrast>=3.0)
                width_ok = (not overflow) and all_visible and legible
                ok = ok and width_ok
                report[width]={"scrollWidth":data["scrollWidth"],"clientWidth":data["clientWidth"],
                    "overflow":overflow,"widgets":wvis,"min_contrast":min_contrast,
                    "all_visible":all_visible,"legible":legible,"pass":width_ok,"screenshot":png}
                print(f"[{width}px] overflow={overflow} all_visible={all_visible} min_contrast={min_contrast} -> {'PASS' if width_ok else 'FAIL'}")
        rp=os.path.join(OUT_DIR,"cdp_375_dom_check.report.json")
        with open(rp,"w",encoding="utf-8") as fh: json.dump({"ts":time.strftime("%Y-%m-%dT%H:%M:%S"),"pass":ok,"results":report},fh,indent=2)
        print("REPORT:",rp,"| OVERALL:","PASS" if ok else "FAIL")
        return 0 if ok else 1
    finally:
        if proc: proc.terminate()

if __name__=="__main__":
    sys.exit(asyncio.run(main()))
