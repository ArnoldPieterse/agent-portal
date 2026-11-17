#!/usr/bin/env python3
"""fleet_goal2_capture.py - Designer Goal #2 pixel leg (no-CDP path)

Goal #2 acceptance remaining: 3-resolution screenshots (768/1024/1920) of the fleet
panel proving no overflow/overlap + dark-mode rendering of the panel.

This seat BLOCKS CDP socket egress (breakpoint_gate --selftest times out on the
127.0.0.1 DevTools port, errno 10013). So instead of a websocket-driven CDP session we
use Edge's IN-PROCESS screenshot mode: `msedge --headless=new --screenshot=out.png
file://...` renders and writes the PNG to disk WITHOUT opening a remote-debugging port
for an external client. Each capture is wrapped in a hard timeout so a hang cannot burn
the whole pass.

The fixture (fleet-matrix.html) reproduces the REAL production token layer + fleet panel
CSS (copied verbatim from ui/app.css) with a populated topology, and stamps
scrollWidth/innerWidth into a corner badge on load so overflow is visible in the raster.

Usage:  python memory/designer/fleet_goal2_capture.py
Writes:  memory/designer/breakpoint-evidence/fleet-<W>px.png  (W in 768,1024,1920)
         memory/designer/goal2-fleet-capture-<date>.md  (evidence leaf)
"""
import os, subprocess, sys, datetime, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
EVIDENCE = os.path.join(HERE, "breakpoint-evidence")
os.makedirs(EVIDENCE, exist_ok=True)
MSEDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
WIDTHS = [768, 1024, 1920]
HEIGHT = 800

def fixture_html():
    # Real token layer + fleet panel rules copied verbatim from ui/app.css (2026-11-18).
    return """<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content='width=device-width,initial-scale=1'>
<title>Fleet panel - goal #2 capture</title>
<style>
:root{--bg:#0e1116;--panel:#151a22;--panel2:#1b2230;--line:#2a3342;--text:#e8edf4;--dim:#9aa7b8;
--acc:#4f8cff;--ok:#3ddc84;--warn:#ff9f43;--err:#ff6b6b;--focus:#7fb0ff;--faint:#8b98ab;
--sp-4:4px;--sp-8:8px;--sp-12:12px;--sp-16:16px;--sp-24:24px;
--fs-11:11px;--fs-12:12px;--fs-13:13px;--fs-14:14px;--fs-15:15px;--fs-16:16px}
*{box-sizing:border-box}
body{margin:0;font-size:var(--fs-14);line-height:1.45;font-family:system-ui,Segoe UI,Roboto,sans-serif;
background:var(--bg);color:var(--text);height:100vh;display:flex;flex-direction:column}
header{display:flex;align-items:center;gap:var(--sp-12);padding:var(--sp-8) var(--sp-16);
border-bottom:1px solid var(--line);background:var(--panel)}
header h1{font-size:var(--fs-15);margin:0;font-weight:600}
#status{margin-left:auto;display:flex;align-items:center;gap:var(--sp-8);color:var(--dim);font-size:var(--fs-12)}
.dot{width:8px;height:8px;border-radius:50%;background:var(--ok)}
main{flex:1;display:flex;min-height:0}
aside{width:250px;border-right:1px solid var(--line);background:var(--panel);display:flex;flex-direction:column;min-height:0}
aside .ah{display:flex;align-items:center;padding:var(--sp-8) var(--sp-12);font-size:var(--fs-12);color:var(--dim);text-transform:uppercase;letter-spacing:.06em}
#agentList{flex:1;overflow-y:auto;padding:var(--sp-4) var(--sp-8)}
.acard{display:flex;align-items:center;gap:var(--sp-8);padding:var(--sp-8);border-radius:8px;
cursor:pointer;border:1px solid transparent;margin-bottom:var(--sp-4);background:var(--panel2)}
.acard.sel{border-color:var(--acc);background:#20304d}
.acard .em{font-size:18px;width:26px;text-align:center}
.acard .nm{flex:1;min-width:0}
.acard .nm b{display:block;font-size:var(--fs-13);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#chatCol{flex:1;display:flex;flex-direction:column;min-width:0}
#fleetPanel{display:flex;border-bottom:1px solid var(--line);background:var(--panel);max-height:280px;flex-direction:column}
#fleetHead{display:flex;align-items:center;gap:var(--sp-8);padding:var(--sp-8) var(--sp-16);font-size:var(--fs-12);color:var(--dim);border-bottom:1px solid var(--line)}
#fleetBody{overflow-y:auto;padding:var(--sp-8) var(--sp-16)}
.frow-h{padding:var(--sp-8) 0;border-bottom:1px dashed var(--line);font-size:var(--fs-12)}
.frow-h:last-child{border-bottom:none}
.fdot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:var(--sp-8);background:#888}
.fdot.busy{background:#ffb454}.fdot.idle{background:var(--ok)}.fdot.unknown{background:#e05252}
.fmodels{color:var(--text);margin:3px 0 0 var(--sp-16);font-family:ui-monospace,Consolas,monospace;font-size:var(--fs-12)}
#fleetTopo{max-width:860px}
.ft-wrap{position:relative;width:100%;min-height:240px;font-family:system-ui,Segoe UI,Roboto,sans-serif}
.ft-svg{width:100%;height:auto;display:block;background:var(--bg);border:1px solid var(--line);border-radius:12px}
.legend{display:flex;gap:18px;font-size:11.5px;color:var(--dim);margin-top:12px;flex-wrap:wrap}
.legend i{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:middle}
#probe{position:fixed;right:8px;bottom:8px;z-index:99;background:rgba(0,0,0,.72);color:#7CFC00;
font-family:ui-monospace,Consolas,monospace;font-size:11px;padding:4px 8px;border-radius:6px}
@media (max-width:768px){aside{width:180px}}
</style></head>
<body>
<header><h1>Agent Portal - Fleet</h1><div id=status><span class=dot></span>connected</div></header>
<main>
  <aside><div class=ah>Agents</div><ul id=agentList style='list-style:none;margin:0;padding:4px 8px'>
    <li class='acard sel'><span class=em>&#129302;</span><span class=nm><b>Orchestrator</b></span></li>
    <li class=acard><span class=em>&#128269;</span><span class=nm><b>Researcher</b></span></li>
    <li class=acard><span class=em>&#128736;</span><span class=nm><b>Builder</b></span></li>
    <li class=acard><span class=em>&#9989;</span><span class=nm><b>Verifier</b></span></li>
  </ul></aside>
  <div id=chatCol>
    <div id=fleetPanel>
      <div id=fleetHead>FLEET TOPOLOGY &nbsp;&middot;&nbsp; 4 hosts</div>
      <div id=fleetBody>
        <div class='frow-h'><span class='fdot idle'></span>White (primary) &mdash; idle
          <div class=fmodels>claude-sonnet-4 / gpt-5</div></div>
        <div class='frow-h'><span class='fdot busy'></span>Red (mirror) &mdash; busy
          <div class=fmodels>claude-opus-4</div></div>
        <div id=fleetTopo><div class=ft-wrap>
          <svg class=ft-svg viewBox='0 0 860 240' preserveAspectRatio=xMidYMid meet>
            <rect x=1 y=1 width=858 height=238 fill=none/>
            <g font-family='system-ui,Segoe UI,sans-serif' font-size='13'>
              <circle cx=90 cy=120 r=26 fill='#1b2230' stroke='#4f8cff'/>
              <text x=90 y=124 fill='#e8edf4' text-anchor=middle>W</text>
              <line x1=116 y1=120 x2=250 y2=70 stroke='#2a3342' stroke-width='1.5'/>
              <line x1=116 y1=120 x2=250 y2=120 stroke='#2a3342' stroke-width='1.5'/>
              <line x1=116 y1=120 x2=250 y2=170 stroke='#2a3342' stroke-width='1.5'/>
              <circle cx=300 cy=70 r=24 fill='#1b2230' stroke='#3ddc84'/>
              <text x=300 y=74 fill='#e8edf4' text-anchor=middle>R</text>
              <circle cx=300 cy=120 r=24 fill='#1b2230' stroke='#ff9f43'/>
              <text x=300 y=124 fill='#e8edf4' text-anchor=middle>B</text>
              <circle cx=300 cy=170 r=24 fill='#1b2230' stroke='#3ddc84'/>
              <text x=300 y=174 fill='#e8edf4' text-anchor=middle>V</text>
              <line x1=324 y1=70 x2=560 y2=120 stroke='#2a3342' stroke-width='1.5'/>
              <line x1=324 y1=120 x2=560 y2=120 stroke='#2a3342' stroke-width='1.5'/>
              <line x1=324 y1=170 x2=560 y2=120 stroke='#2a3342' stroke-width='1.5'/>
              <rect x=560 y=96 width=200 height=48 rx=10 fill='#151a22' stroke='#2a3342'/>
              <text x=660 y=116 fill='#e8edf4' text-anchor=middle>portal :8099</text>
              <text x=660 y=132 fill='#9aa7b8' text-anchor=middle font-size='11'>mirror sync + git net</text>
            </g>
          </svg>
        </div>
        <div class=legend><span><i style='background:#4f8cff'></i>primary</span>
          <span><i style='background:#3ddc84'></i>idle/ok</span>
          <span><i style='background:#ff9f43'></i>busy</span></div>
      </div>
    </div>
  </div>
</main>
<div id=probe>sw=? iw=?</div>
<script>window.addEventListener('load',function(){var d=document.documentElement;
document.getElementById('probe').textContent='sw='+d.scrollWidth+' iw='+window.innerWidth;});</script>
</body></html>"""

def main():
    fx = os.path.join(HERE, "fleet-matrix.html")
    with open(fx, "w", encoding="utf-8") as f:
        f.write(fixture_html())
    fx_url = "file://" + fx.replace(os.sep, "/")
    print("fixture:", fx)
    # WORKING RECIPE (2026-11-18, Edge 157): OLD `--headless` (NOT --headless=new,
    # which emits no PNG in this build) + a writable per-width --user-data-dir
    # ("Missing headless user data directory" otherwise). In-process: no CDP port.
    results = []
    for w in WIDTHS:
        out = os.path.join(EVIDENCE, "fleet-%dpx.png" % w)
        if os.path.exists(out):
            os.remove(out)
        # Match the proven invocation: let Edge CREATE a non-existent profile dir
        # (pre-creating an empty one made it emit no PNG). Retry on flakiness.
        ok, dt, kb, note = False, 0.0, 0, ""
        for attempt in range(3):
            udd = os.path.join(HERE, "_edge_ud_%d_%d" % (w, attempt))
            if os.path.isdir(udd):
                shutil.rmtree(udd, ignore_errors=True)
            cmd = [MSEDGE, "--headless", "--disable-gpu", "--no-sandbox",
                   "--user-data-dir=" + udd,
                   "--hide-scrollbars", "--force-device-scale-factor=1",
                   "--window-size=%d,%d" % (w, HEIGHT),
                   "--virtual-time-budget=5000",
                   "--screenshot=" + out, fx_url]
            print("\n[%dpx attempt %d] --headless ... --screenshot=fleet-%dpx.png" % (w, attempt+1, w))
            t0 = datetime.datetime.now()
            try:
                subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                dt = (datetime.datetime.now() - t0).total_seconds()
                if os.path.exists(out) and os.path.getsize(out) > 2000:
                    ok, kb = True, round(os.path.getsize(out)/1024, 1)
                    break
            except subprocess.TimeoutExpired:
                note = "TIMEOUT(60s) attempt %d" % (attempt+1)
            except Exception as e:
                note = repr(e)
        results.append((w, ok, dt, kb, note))
        print("    -> %s in %.1fs (%s KB)%s" % ("PNG OK" if ok else "NO PNG", dt,
              kb or 0, ("  ["+note+"]") if note and not ok else ""))

    # evidence leaf
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    md = os.path.join(HERE, "goal2-fleet-capture-%s.md" % date)
    with open(md, "w", encoding="utf-8") as f:
        f.write("# Goal #2 fleet panel - 3-resolution capture (in-process msedge, no CDP)\n\n"
                "Date: %s\nSeat: Designer sandbox (CDP socket egress blocked; using in-process --screenshot)\n"
                "Fixture: memory/designer/fleet-matrix.html (real token layer + fleet CSS from ui/app.css)\n\n"
                "| width | PNG produced | time(s) | KB | note |\n|---|---|---|---|---|\n" % date)
        for w, ok, dt, kb, note in results:
            f.write("| %d | %s | %.1f | %s | %s |\n" % (w, "YES" if ok else "NO", dt, kb or 0,
                     note.replace("|", "/")[:200]))
        all_ok = all(r[1] for r in results)
        f.write("\n## Verdict\n%s: %d/%d widths captured.\n" %
                ("PASS" if all_ok else "PARTIAL", sum(1 for r in results if r[1]), len(results)))
    print("\nevidence leaf:", md)
    return 0 if all(r[1] for r in results) else 2

if __name__ == "__main__":
    sys.exit(main())
