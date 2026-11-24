#!/usr/bin/env python3
"""Mode-Aware Dispatch Filter (Builder goal 5, cycle 15).

Given fleet_mode + next10.json, produce the dispatch list.
WORK: only open goals. MAINTENANCE/IDLE: maintenance tasks from the
rotation table. Reached goals are excluded regardless of mode.
"""
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
NEXT10 = BASE / "memory" / "goals" / "next10.json"
ROTATION_MD = BASE / "memory" / "ops" / "idle-maintenance-rotation.md"
GOALS_DIR = BASE / "memory" / "goals"
OUT_DIR = BASE / "memory" / "ops"


def load_rotation():
    """Parse the role x task rotation table -> {role: [task1..task5]}."""
    roles = {}
    if not ROTATION_MD.exists():
        return roles
    for line in ROTATION_MD.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 6 or cells[0] in ("Role", "") or set(cells[0]) <= {"-"}:
            continue
        roles[cells[0].lower()] = cells[1:6]
    return roles


def rotation_task(role, day=None):
    day = day if day is not None else date.today().weekday()
    tasks = load_rotation().get(role.lower())
    return tasks[day % 5] if tasks else None


def load_next10():
    if NEXT10.exists():
        try:
            return json.loads(NEXT10.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"next10": []}


def reached_titles():
    """Titles of goals carrying a (verified: marker in their agent goal file."""
    out = set()
    for f in GOALS_DIR.glob("*.md"):
        if f.name in ("next10.md", "README.md"):
            continue
        txt = f.read_text(encoding="utf-8")
        for m in re.finditer(r"\d+\. \*\*(.+?)\*\*[^\n]*?\(verified:", txt):
            out.add(m.group(1).strip().lower())
    return out


def filter_dispatch(mode, doc, reached=None, day=None):
    mode = (mode or "WORK").upper()
    if reached is None:
        reached = {t.lower() for t in reached} if reached else reached_titles()
    entries = []
    def is_reached(title):
        t = title.lower()
        if t in reached:
            return True
        for r in reached:
            if len(t) >= 20 and (t.startswith(r[:40]) or r.startswith(t[:40])):
                return True
        return False
    if mode == "WORK":
        for e in doc.get("next10", []):
            if e.get("reached"):
                continue
            title = (e.get("title") or e.get("goal", "")).strip()
            if title and not is_reached(title):
                entries.append({"agent": e.get("agent"), "task": title[:120], "kind": "goal"})
    else:
        agents = sorted({e.get("agent") for e in doc.get("next10", []) if e.get("agent")} | set(load_rotation()))
        for ag in agents:
            task = rotation_task(ag, day)
            if task:
                entries.append({"agent": ag, "task": task, "kind": "maintenance"})
    return entries


def main():
    mode = "WORK"
    if "--mode" in sys.argv:
        i = sys.argv.index("--mode")
        if i + 1 < len(sys.argv):
            mode = sys.argv[i + 1].upper()
    doc = load_next10()
    reached = reached_titles()
    entries = filter_dispatch(mode, doc, reached)
    out = OUT_DIR / ("dispatch-list-%s.md" % datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    L = ["# Dispatch List - %s (%s)" % (mode, doc.get("generated", "?")), ""]
    for e in entries:
        L.append("- **%s** [%s]: %s" % (e["agent"], e["kind"], e["task"]))
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("Dispatch list written to: %s (%d entries, mode=%s)" % (out.name, len(entries), mode))


def selftest():
    rot = load_rotation()
    ok = len(rot) >= 5 and all(len(v) == 5 for v in rot.values())
    doc = {"generated": "t", "next10": [
        {"agent": "builder", "title": "Open Goal Alpha"},
        {"agent": "scribe", "title": "Done Goal Beta"},
        {"agent": "mechanic", "title": "Open Goal Gamma"}]}
    w = filter_dispatch("WORK", doc, {"done goal beta"})
    ok &= len(w) == 2 and all(e["kind"] == "goal" for e in w)
    ids = filter_dispatch("IDLE", doc, set())
    ok &= len(ids) == len(rot) and all(e["kind"] == "maintenance" for e in ids)
    day = date.today().weekday() % 5
    exp = {r: v[day] for r, v in rot.items()}
    got = {e["agent"]: e["task"] for e in ids}
    ok &= all(got.get(r) == v for r, v in exp.items())
    print("Result: %s" % ("PASS" if ok else "FAIL"))
    return ok


if __name__ == "__main__":
    import sys as _s
    if "--selftest" in _s.argv:
        sys.exit(0 if selftest() else 1)
    main()
