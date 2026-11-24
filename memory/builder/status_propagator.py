#!/usr/bin/env python3
"""Goal Status Propagator (Builder goal 7, cycle 15).

When a goal is marked reached (detected via goal_ledger evidence markers in
memory/goals/<agent>.md), propagate the status to:
  (a) next10.json      - entry flagged "reached": true + fleet counters refreshed
  (b) dispatch cache   - memory/ops/dispatch-cache.json regenerated for current mode
  (c) fleet-mode       - recalculation triggered via memory/orchestrator/fleet_mode.py
Verified: marking a goal reached updates all 3 targets within one pass.
"""
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
GOALS_DIR = BASE / "memory" / "goals"
NEXT10 = GOALS_DIR / "next10.json"
FLEET_MODE = BASE / "memory" / "ops" / "fleet-mode.json"
DISPATCH_CACHE = BASE / "memory" / "ops" / "dispatch-cache.json"
FLEET_MODE_PY = BASE / "memory" / "orchestrator" / "fleet_mode.py"
AGENTS = ["orchestrator", "researcher", "builder", "archivist",
          "scribe", "verifier", "designer", "mechanic"]

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dispatch_filter import filter_dispatch  # noqa: E402


TITLE_RE = re.compile(r"^\s*(?:[-*]\s*\[[ xX]\s*)?(\d+)\.\s*(.+)$")


def detect_reached():
    """Scan goal files for evidence markers -> {agent: [reached goal texts]}."""
    out = {}
    for ag in AGENTS:
        f = GOALS_DIR / (ag + ".md")
        if not f.exists():
            continue
        hits = []
        for line in f.read_text(encoding="utf-8").splitlines():
            m = TITLE_RE.match(line)
            if not m:
                continue
            body = m.group(2).strip()
            if "(verified:" in line or re.search(r"(\u2014|--)\s*recorded\b", line, re.I):
                hits.append(body)
        if hits:
            out[ag] = hits
    return out


def _clean(body):
    body = re.sub(r"^\d+\.\s*", "", body).strip()
    m = re.match(r"^\*\*(.+?)\*\*", body)
    if m:
        return m.group(1).lower()
    return body.split(" - ")[0].strip().lower()


def _is_reached(title, reached_bodies):
    t = title.lower().strip()
    for body in reached_bodies:
        b = body.lower()
        core = _clean(body)
        if t == core or (len(t) >= 8 and t in b):
            return True
        if len(t) >= 20 and (t.startswith(core[:40]) or core.startswith(t[:40])):
            return True
    return False


def propagate_next10(reached):
    if not NEXT10.exists():
        return 0
    doc = json.loads(NEXT10.read_text(encoding="utf-8"))
    changed = 0
    all_bodies = [b for v in reached.values() for b in v]
    for e in doc.get("next10", []):
        title = (e.get("title") or e.get("goal", ""))[:60]
        bodies = reached.get(e.get("agent"), all_bodies)
        if _is_reached(title, bodies) and not e.get("reached"):
            e["reached"] = True
            changed += 1
    open_n = sum(1 for e in doc.get("next10", []) if not e.get("reached"))
    if "fleet" in doc:
        doc["fleet"]["open_next10"] = open_n
    doc["propagated_at"] = datetime.now(timezone.utc).isoformat()
    NEXT10.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    return changed


def propagate_dispatch_cache(reached):
    mode = "WORK"
    if FLEET_MODE.exists():
        try:
            mode = json.loads(FLEET_MODE.read_text(encoding="utf-8")).get("mode", "WORK")
        except Exception:
            pass
    doc = {"next10": []}
    if NEXT10.exists():
        doc = json.loads(NEXT10.read_text(encoding="utf-8"))
    entries = filter_dispatch(mode, doc, set())
    DISPATCH_CACHE.write_text(json.dumps(
        {"generated": datetime.now(timezone.utc).isoformat(), "mode": mode,
         "entries": entries}, indent=1), encoding="utf-8")
    return len(entries)


def trigger_fleet_mode():
    r = subprocess.run([sys.executable, str(FLEET_MODE_PY)], capture_output=True,
                       text=True, timeout=60, cwd=str(BASE))
    return r.returncode == 0 and FLEET_MODE.exists()


def propagate():
    reached = detect_reached()
    a = propagate_next10(reached)
    b = propagate_dispatch_cache(reached)
    c = trigger_fleet_mode()
    return {"next10_flagged": a, "dispatch_entries": b, "fleet_mode_ok": c}


def main():
    res = propagate()
    print("Propagated: next10 flagged=%d, dispatch entries=%d, fleet-mode ok=%s"
          % (res["next10_flagged"], res["dispatch_entries"], res["fleet_mode_ok"]))




def selftest():
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="sp_"))
    goals = tmp / "goals"; goals.mkdir()
    (goals / "scribe.md").write_text(
        "1. **Done Goal Alpha** - work (verified: 2026-11-24 - done)\n"
        "2. **Open Goal Beta** - pending\n", encoding="utf-8")
    n10 = tmp / "next10.json"
    n10.write_text(json.dumps({"fleet": {}, "next10": [
        {"agent": "scribe", "title": "Done Goal Alpha"},
        {"agent": "scribe", "title": "Open Goal Beta"}]}), encoding="utf-8")
    fm = tmp / "fleet-mode.json"
    fm.write_text(json.dumps({"mode": "WORK"}), encoding="utf-8")
    stub = tmp / "fm.py"; stub.write_text("import sys; sys.exit(0)", encoding="utf-8")
    dc = tmp / "dispatch-cache.json"
    g = sys.modules[__name__]
    g.GOALS_DIR, g.NEXT10, g.FLEET_MODE, g.DISPATCH_CACHE, g.FLEET_MODE_PY = (
        goals, n10, fm, dc, stub)
    res = propagate()
    doc = json.loads(n10.read_text(encoding="utf-8"))
    flags = [e.get("reached") for e in doc["next10"]]
    ok = (res["fleet_mode_ok"] is True and flags[0] is True and flags[1] in (None, False)
          and dc.exists() and res["dispatch_entries"] >= 1)
    print("Result: %s" % ("PASS" if ok else "FAIL"))
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    main()
