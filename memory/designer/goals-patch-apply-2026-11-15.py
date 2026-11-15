#!/usr/bin/env python3
"""Designer — Goal Velocity dashboard + H2/M3-M6 CSS fix pack (2026-11-15).
Self-contained, IDEMPOTENT patch for agent_portal.py + index.html.

WHY A SCRIPT: the 5-min White->shared SMB mirror clobbers direct writes to the
shared folder with mtime preservation (evidence: memory/verifier/mirror-clobber-
2026-11-15.md, memory/builder/h1-frow-fix-2026-11-15.md). This script must be run
on WHITE'S LIVE PORTAL ROOT (next to the agent_portal.py that PID 19488 runs),
then the portal restarted. It is shipped via memory/designer/ so it survives mirroring.

Usage on White:  python apply_designer_goals_patch.py [dir-with-portal-files]
Re-runs are safe: every hunk is guarded by its done-marker; already-applied hunks skip.
"""
import os, sys, hashlib, re

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:12]

HERE = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
PORTAL = os.path.join(HERE, "agent_portal.py")
INDEX = os.path.join(HERE, "index.html")

applied, skipped, failed = [], [], []

def patch(path, name, guard, anchor, replacement):
    raw = open(path, "rb").read()
    eol = b"\r\n" if raw.count(b"\r\n") > raw.count(b"\n") // 2 else b"\n"
    full = raw.decode("utf-8").replace("\r\n", "\n")
    if guard in full:
        skipped.append(name); return
    n = full.count(anchor)
    if n != 1:
        failed.append((name, "anchor count %d (want 1)" % n)); return
    out = full.replace(anchor, replacement).replace("\n", eol.decode())
    open(path, "wb").write(out.encode("utf-8"))
    applied.append(name)

# ================= BACKEND: agent_portal.py =================
GOALS_FN = '''def _goals_snapshot():
    """Goal Velocity dashboard (2026-11-15, Designer): parses memory/goals/<agent>.md.
    Item format: 'N. text' — done if it contains '(verified:' or '[x]'; blocked = open
    item mentioning 'blocked'. Returns per-agent counts + fleet percentage."""
    gdir = os.path.join(HERE, "memory", "goals")
    try:
        names = {(a.get("name") or "").lower() for a in load_agents().get("agents", [])}
    except Exception:
        names = set()
    agents = []
    try:
        for fn in sorted(os.listdir(gdir)):
            if not fn.endswith(".md") or fn[:-3] == "INDEX":
                continue
            if names and fn[:-3].lower() not in names:
                continue  # skip summary/dated rollup files (all-goals-*, *-agent-goals, etc.)
            txt = open(os.path.join(gdir, fn), encoding="utf-8").read()
            items = re.findall(r"^\\s*\\d+\\.\\s+(.*)$", txt, re.M)
            done = sum(1 for it in items if "(verified:" in it or "[x]" in it)
            open_items = [it for it in items if "(verified:" not in it and "[x]" not in it]
            blocked = sum(1 for it in open_items if "blocked" in it.lower())
            agents.append({"agent": fn[:-3], "total": len(items), "done": done,
                           "open": len(open_items), "blocked": blocked})
    except Exception as e:
        return {"ok": False, "error": str(e), "agents": []}
    total = sum(a["total"] for a in agents)
    done_all = sum(a["done"] for a in agents)
    return {"ok": True, "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "fleet_pct": round(100.0 * done_all / total, 1) if total else 0.0,
            "fleet_done": done_all, "fleet_total": total, "agents": agents}


'''
# B1: insert fresh, OR replace an older unfiltered version in place (self-updating)
_praw = open(PORTAL, "rb").read()
_peol = b"\r\n" if _praw.count(b"\r\n") > _praw.count(b"\n") // 2 else b"\n"
_portal = _praw.decode("utf-8").replace("\r\n", "\n")
if "fn[:-3].lower() not in names" in _portal:
    skipped.append("B1 _goals_snapshot fn")
elif "def _goals_snapshot():" in _portal:
    i, j = _portal.index("def _goals_snapshot():"), _portal.index("def _run_index_check():")
    out = (_portal[:i] + GOALS_FN + _portal[j:]).replace("\n", _peol.decode())
    open(PORTAL, "wb").write(out.encode("utf-8"))
    applied.append("B1b _goals_snapshot fn (replaced old version)")
else:
    patch(PORTAL, "B1 _goals_snapshot fn", "fn[:-3].lower() not in names",
          "def _run_index_check():",
          GOALS_FN + "def _run_index_check():")
patch(PORTAL, "B2 /api/goals route", '"/api/goals"',
      '        elif p == "/api/ops":\n            # Ops panel host tiles (2026-11-15): disk usage + portal uptime.\n            return self._json(200, _ops_snapshot())',
      '        elif p == "/api/ops":\n            # Ops panel host tiles (2026-11-15): disk usage + portal uptime.\n            return self._json(200, _ops_snapshot())\n        elif p == "/api/goals":\n            # Goal Velocity dashboard (2026-11-15, Designer): per-agent goal progress.\n            return self._json(200, _goals_snapshot())')

# ================= FRONTEND: index.html =================
I = INDEX
# H2 — contrast AA fixes (verified ratios pre-fix: 3.80 / 4.31 / 3.93 -> all >=5.4 post)
patch(I, "H2a --faint token", "--faint",
      "--focus:#7fb0ff;}",
      "--focus:#7fb0ff;--faint:#8b98ab;}")
patch(I, "H2b .aev .at", "var(--faint);flex:none;width:64px",
      ".aev .at{color:#6b7688;flex:none;width:64px}",
      ".aev .at{color:var(--faint);flex:none;width:64px}")
patch(I, "H2c .think summary", 'font-size:11px;font-style:italic;color:var(--faint)',
      ".think summary{cursor:pointer;font-size:10.5px;font-style:italic;opacity:.75;user-select:none;list-style:none}",
      ".think summary{cursor:pointer;font-size:11px;font-style:italic;color:var(--faint);user-select:none;list-style:none}")
patch(I, "H2d .silentmsg .body", 'font-size:11px;color:var(--faint);font-style:italic',
      ".msg.silentmsg .body{font-size:10.5px;color:var(--dim);opacity:.7;font-style:italic}",
      ".msg.silentmsg .body{font-size:11px;color:var(--faint);font-style:italic}")
# M3 — type scale: kill off-scale 10.5/11.5/12.5px (scale = 11/12/14/16)
patch(I, "M3a .silentpill 10.5->11", ".silentpill{font-size:11px",
      ".silentpill{font-size:10.5px;",
      ".silentpill{font-size:11px;")
patch(I, "M3b .tsec b 10.5->11", ".tsec b{display:block;font-size:11px;",
      ".tsec b{display:block;font-size:10.5px;",
      ".tsec b{display:block;font-size:11px;")
patch(I, "M3c fleet .frow 12.5->12", 'dashed var(--line);font-size:12px}',
      ".frow{padding:7px 0;border-bottom:1px dashed var(--line);font-size:12.5px}",
      ".frow{padding:7px 0;border-bottom:1px dashed var(--line);font-size:12px}")
# M3 — unified panel headers (4 variants -> one look: 8px 14px / 12px / dim)
patch(I, "M3d #fleetHead", '#fleetHead{display:flex;align-items:center;gap:10px;padding:8px 14px;font-size:12px;color:var(--dim)',
      "#fleetHead{display:flex;align-items:center;gap:10px;padding:8px 14px;font-size:13px;border-bottom:1px solid var(--line)}",
      "#fleetHead{display:flex;align-items:center;gap:10px;padding:8px 14px;font-size:12px;color:var(--dim);border-bottom:1px solid var(--line)}")
patch(I, "M3e #opsHead", '#opsHead{display:flex;align-items:center;gap:10px;padding:8px 14px;font-size:12px;color:var(--dim)',
      "#opsHead{display:flex;align-items:center;gap:10px;padding:8px 14px;font-size:13px;border-bottom:1px solid var(--line)}",
      "#opsHead{display:flex;align-items:center;gap:10px;padding:8px 14px;font-size:12px;color:var(--dim);border-bottom:1px solid var(--line)}")
patch(I, "M3f #actHead", '#actHead{display:flex;align-items:center;gap:8px;padding:8px 14px;',
      "#actHead{display:flex;align-items:center;gap:8px;padding:6px 14px;font-size:12px;color:var(--dim)}",
      "#actHead{display:flex;align-items:center;gap:8px;padding:8px 14px;font-size:12px;color:var(--dim);border-bottom:1px solid var(--line)}")
patch(I, "M3g #filesHead", '#filesHead{display:flex;align-items:center;gap:8px;padding:8px 14px;',
      "#filesHead{display:flex;align-items:center;padding:6px 10px;border-bottom:1px solid var(--line)}",
      "#filesHead{display:flex;align-items:center;gap:8px;padding:8px 14px;font-size:12px;color:var(--dim);border-bottom:1px solid var(--line)}")
# M4 — mode bar hierarchy: group panel toggles, divider before Reset/Stop, Stop on --err
patch(I, "M4a .toggles CSS", ".toggles{display:inline-flex;gap:6px}",
      ".fs-empty{padding:10px;color:var(--dim)}",
      ".fs-empty{padding:10px;color:var(--dim)}\n.toggles{display:inline-flex;gap:6px}\n.vdiv{width:1px;height:18px;background:var(--line);margin:0 4px}")
patch(I, "M4b wrap toggles open", '<span class="toggles">',
      '      <button id="actBtn" title="Activity timeline',
      '      <span class="toggles"><button id="actBtn" title="Activity timeline')
patch(I, "M4c close toggles + divider", '</span><span class="vdiv"></span>',
      'TODO sections into TODO_completed.md">🔧 Ops</button>',
      'TODO sections into TODO_completed.md">🔧 Ops</button></span><span class="vdiv"></span>')
patch(I, "M4d stopBtn color", 'style="color:var(--err)"',
      'style="color:#ff8f8f"',
      'style="color:var(--err)"')
# M5 — unified panel body paddings (fleet/ops/act -> 8px 14px)
patch(I, "M5a #fleetBody", "#fleetBody{overflow-y:auto;padding:8px 14px}",
      "#fleetBody{overflow-y:auto;padding:6px 14px}",
      "#fleetBody{overflow-y:auto;padding:8px 14px}")
patch(I, "M5b #opsBody", "#opsBody{overflow-y:auto;padding:8px 14px}",
      "#opsBody{overflow-y:auto;padding:6px 14px 10px}",
      "#opsBody{overflow-y:auto;padding:8px 14px}")
patch(I, "M5c #actBody", "padding:8px 14px;font:12px/1.7",
      "#actBody{overflow-y:auto;padding:4px 14px 10px;font:11.5px/1.7 ui-monospace,Consolas,monospace}",
      "#actBody{overflow-y:auto;padding:8px 14px;font:12px/1.7 ui-monospace,Consolas,monospace}")
# M6 — kill nested scroll in Ops (.opsbox inside scrolling #opsBody)
patch(I, "M6 .opsbox", "max-height:none;overflow:visible",
      ".opsbox{font:11.5px/1.6 ui-monospace,Consolas,monospace;white-space:pre-wrap;color:var(--dim);max-height:84px;overflow-y:auto;background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:4px 8px;margin-top:6px}",
      ".opsbox{font:12px/1.6 ui-monospace,Consolas,monospace;white-space:pre-wrap;color:var(--dim);max-height:none;overflow:visible;background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:4px 8px;margin-top:6px}")
# Motion spec — 150-200ms on interactive elements only (was: zero transitions)
patch(I, "MOT motion hunk", "Motion spec (2026-11-15",
      ".fs-empty{padding:10px;color:var(--dim)}",
      ".fs-empty{padding:10px;color:var(--dim)}\n/* Motion spec (2026-11-15, Designer): 150-200ms on interactive elements only */\n#modeBar button,.seg button,.btn,#send{transition:border-color .15s,color .15s,background-color .15s,opacity .15s}\n.dot{transition:background-color .2s}\n.flink{transition:color .15s,border-bottom-color .15s}")
# Goal Velocity panel — CSS + HTML + JS
GOALS_CSS = """/* Goal Velocity dashboard (2026-11-15, Designer): /api/goals -> per-agent SVG rings */
#goalsBtn{background:none;border:1px solid var(--line);color:var(--dim);border-radius:8px;padding:4px 10px;cursor:pointer;font-size:12px}
#goalsBtn:hover,#goalsBtn.on{border-color:var(--acc);color:var(--text)}
#goalsPanel{display:none;border-bottom:1px solid var(--line);background:var(--panel);max-height:300px;flex-direction:column}
#goalsPanel.open{display:flex}
#goalsHead{display:flex;align-items:center;gap:8px;padding:8px 14px;font-size:12px;color:var(--dim);border-bottom:1px solid var(--line)}
#goalsBody{overflow-y:auto;padding:8px 14px;display:flex;flex-wrap:wrap;gap:10px}
.gtile{display:flex;align-items:center;gap:10px;background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:8px 12px;min-width:170px}
.gring{position:relative;width:44px;height:44px;flex:none}
.gring svg{transform:rotate(-90deg)}
.gring .pct{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600}
.gname{font-size:12px;font-weight:600}
.gmeta{font-size:11px;color:var(--dim)}
.gblock{color:var(--warn);font-size:11px}"""
patch(I, "G1 goals CSS", "#goalsBody",
      ".fs-empty{padding:10px;color:var(--dim)}",
      ".fs-empty{padding:10px;color:var(--dim)}\n" + GOALS_CSS)
patch(I, "G2 goals button", 'id="goalsBtn"',
      '      <span class="toggles"><button id="actBtn" title="Activity timeline',
      '      <span class="toggles"><button id="goalsBtn" title="Goal velocity: per-agent progress rings from memory/goals/">🎯 Goals</button><button id="actBtn" title="Activity timeline')
GOALS_HTML = """    <div id="goalsPanel">
      <div id="goalsHead"><span>Goal velocity · live parse of memory/goals/</span><span id="goalsStat" class="hint">loading…</span></div>
      <div id="goalsBody"></div>
    </div>
"""
patch(I, "G3 goals panel div", 'id="goalsPanel"',
      '    <div id="msgs">',
      GOALS_HTML + '    <div id="msgs">')
GOALS_JS = """// ---- Goals panel (2026-11-15, Designer): Goal Velocity dashboard ----
async function goalsLoad(){
  try{
    const o=await (await fetch("/api/goals")).json();
    if(!o.ok){ $("goalsStat").textContent="⚠ "+(o.error||"error"); return; }
    const C=119.38; let html="";
    for(const a of o.agents){
      const pct=a.total?Math.round(100*a.done/a.total):0;
      const off=(C*(1-pct/100)).toFixed(1);
      html+='<div class="gtile"><div class="gring"><svg width="44" height="44" viewBox="0 0 44 44">'
        +'<circle cx="22" cy="22" r="19" fill="none" stroke="var(--line)" stroke-width="4"/>'
        +'<circle cx="22" cy="22" r="19" fill="none" stroke="'+(pct>=100?'var(--ok)':'var(--acc)')+'" stroke-width="4" stroke-linecap="round" stroke-dasharray="'+C+'" stroke-dashoffset="'+off+'"/>'
        +'</svg><span class="pct">'+pct+'%</span></div>'
        +'<div><div class="gname">'+a.agent+'</div><div class="gmeta">'+a.done+'/'+a.total+' done · '+a.open+' open'
        +(a.blocked?' · <span class="gblock">⚠ '+a.blocked+' blocked</span>':'')+'</div></div></div>';
    }
    $("goalsBody").innerHTML=html||'<div class="hint">no goal files</div>';
    $("goalsStat").textContent=o.fleet_done+"/"+o.fleet_total+" · fleet "+(o.fleet_pct||0)+"%";
  }catch(e){ $("goalsStat").textContent="⚠ "+e; }
}
$("goalsBtn").onclick=()=>{ const open=$("goalsPanel").classList.toggle("open"); $("goalsBtn").classList.toggle("on",open); if(open)goalsLoad(); };
"""
patch(I, "G4 goals JS", 'function goalsLoad',
      '$("filesBtn").onclick=()=>{const open=$("filesPanel").classList.toggle("open");$("filesBtn").classList.toggle("on",open);if(open)filesLoad();};',
      '$("filesBtn").onclick=()=>{const open=$("filesPanel").classList.toggle("open");$("filesBtn").classList.toggle("on",open);if(open)filesLoad();};\n' + GOALS_JS)

# ================= VERIFY =================
print("=== Designer patch 2026-11-15 (Goal Velocity + H2/M3-M6/motion) ===")
print("applied: %d" % len(applied))
for a in applied: print("  +", a)
print("skipped (already present): %d" % len(skipped))
for s in skipped: print("  =", s)
if failed:
    print("FAILED HUNKS:")
    for f, why in failed: print("  !", f, "-", why)
import py_compile
try:
    py_compile.compile(PORTAL, doraise=True)
    print("py_compile agent_portal.py: OK")
except Exception as e:
    print("py_compile FAILED:", e); failed.append(("compile", str(e)))
html = open(INDEX, encoding="utf-8").read()
checks = {
    "CSS braces balanced": html.count("{") == html.count("}"),
    "goalsPanel present": 'id="goalsPanel"' in html,
    "--faint token": "--faint:#8b98ab" in html,
    ".toggles group": '<span class="toggles">' in html,
    "transitions present": html.count("transition:") >= 3,
    "no off-scale 10.5px": "10.5px" not in html,
    "no off-scale 12.5px": "12.5px" not in html,
    "no #ff8f8f literal": "#ff8f8f" not in html,
}
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
    if not v: failed.append((k, "check failed"))
print("sha256 portal:", sha(PORTAL), " index:", sha(INDEX))
sys.exit(1 if failed else 0)
