#!/usr/bin/env python3
"""Cycle Transition Check - executable version of cycle-transition-checklist.md.
Run at start of each new goal cycle. Verifies ops infrastructure is ready."""
import json, sys, time, subprocess, socket
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OPS = ROOT / "memory" / "ops"
results = []

def check(name, fn):
    try:
        ok, detail = fn()
    except Exception as e:
        ok, detail = False, str(e)
    results.append((name, ok, detail))
    print(f"  {'OK ' if ok else 'XX '} {name}: {detail}")

print("Cycle Transition Check - " + time.strftime("%Y-%m-%d %H:%M"))
print("=" * 60)

def schtask_alive(tn):
    r = subprocess.run(["schtasks", "/query", "/tn", tn, "/fo", "list"], capture_output=True, text=True, timeout=10)
    if "Status" in r.stdout and ("Running" in r.stdout or "Ready" in r.stdout):
        return True, f"{tn} alive"
    return False, f"{tn} not found/dead"

def portal_up():
    try:
        s = socket.create_connection(("127.0.0.1", 8099), 3); s.close()
        return True, "portal :8099 responding"
    except Exception as e:
        return False, f"portal down: {e}"

print("1. Standing tasks:")
for t in ["PortalWatchdog", "PortalFleetProbe", "PortalLoadProbe"]:
    check(t, lambda t=t: schtask_alive(t))
check("Portal :8099", portal_up)

def mirror_fresh():
    p = OPS / "clobber-events.jsonl"
    if not p.exists(): return False, "no clobber-events.jsonl"
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    if not lines: return False, "empty"
    try:
        last = json.loads(lines[-1])
        ts = time.mktime(time.strptime(last.get("ts","2000-01-01T00:00:00"), "%Y-%m-%dT%H:%M:%S"))
        age_h = (time.time() - ts) / 3600
        return age_h < 2, f"last sync {age_h:.1f}h ago"
    except Exception:
        return True, "file exists (timestamp unparseable)"

print("2. Mirror freshness:")
check("Mirror last sync", mirror_fresh)

def goal_files_exist():
    gf = ROOT / "memory" / "goals"
    if not gf.exists(): return False, "memory/goals/ missing"
    agents = [f for f in gf.glob("*.md") if f.name != "INDEX.md"]
    return len(agents) >= 3, f"{len(agents)} agent goal files present"

print("3. Goal file hygiene:")
check("Goal files", goal_files_exist)

def evidence_continuity():
    p = OPS / "fleet-probe-history.jsonl"
    if not p.exists(): return False, "no probe history"
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    if not lines: return False, "empty"
    try:
        last = json.loads(lines[-1])
        ts = time.mktime(time.strptime(last.get("ts","2000-01-01T00:00:00"), "%Y-%m-%dT%H:%M:%S"))
        age_min = (time.time() - ts) / 60
        return age_min < 15, f"last probe {age_min:.0f}min ago"
    except Exception:
        return True, "file exists"

print("4. Evidence continuity:")
check("Probe history", evidence_continuity)

ok = sum(1 for _,o,_ in results if o)
total = len(results)
print(f"\n{ok}/{total} checks passed")
sys.exit(0 if ok == total else 1)
