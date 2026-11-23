#!/usr/bin/env python3
"""schtask_dep_weekly.py - production runner for the weekly scheduled-task
dependency graph (MECHANIC#6, memory/goals/scheduled-background.md).

What it does, end-to-end (no arguments needed):
  1. Captures `schtasks /query /fo CSV /v` into a dated input file.
  2. Finds the most recent previous snapshot in this directory.
  3. Runs schtask_dep_gen.py against it -> new snapshot + NEW/REMOVED diff.
  4. Prints ALERT lines for any added/removed tasks (the production flag
     the goal's verification requires).

Runbook: registered as weekly schtask 'PortalSchtaskDepGen' on White.
Sibling: schtask_dep_gen.py (the parser/diff engine this wraps).
"""
import csv, glob, io, json, os, subprocess, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SNAP_PREFIX = "schtask-snapshot-"

# Fleet-relevance filter: the dependency map tracks the portal/fleet task
# surface, not Windows system tasks. A row is kept if its TaskName matches a
# prefix below or appears in the previous snapshot (so removals of tracked
# tasks are still caught even after they stop matching).
TRACK_PREFIXES = ("Portal", "Mirror", "MemoryMirror", "AgentPortal")
TRACK_EXACT = {"RecoverAll", "VerifierSLO", "GCC", "LlamaRPCWorker"}

def _relevant(name: str, prev_names) -> bool:
    n = name.strip().lstrip("\\").strip('"')
    prev_norm = {p.strip().lstrip("\\").strip('"').lower() for p in prev_names}
    return (any(n.startswith(p) for p in TRACK_PREFIXES)
            or n in TRACK_EXACT
            or n.lower() in prev_norm)

def main() -> int:
    today = datetime.date.today().isoformat()
    inp = os.path.join(HERE, f"{SNAP_PREFIX}{today}-input.csv")
    q = subprocess.run(["schtasks", "/query", "/fo", "CSV", "/v"],
                       capture_output=True, text=True,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if q.returncode != 0:
        print("FATAL: schtasks /query failed:", q.stderr.strip()[:200])
        return 1

    # Newest non-empty, non-test snapshot is the reference. (Alphabetical
    # order once bit us: a synthetic week1-test file sorted last.)
    prevs = [p for p in glob.glob(os.path.join(HERE, SNAP_PREFIX + "*.json"))
             if "test" not in os.path.basename(p).lower()]
    prev = None
    for cand in sorted(prevs, key=os.path.getmtime, reverse=True):
        try:
            n = len(json.load(open(cand, encoding="utf-8")).get("tasks", []))
        except Exception:
            continue
        if n > 0:
            prev = cand
            break
    prev_names = set()
    if prev:
        try:
            psnap = json.load(open(prev, encoding="utf-8"))
            prev_names = {(t if isinstance(t, str) else t.get("name"))
                          for t in psnap.get("tasks", [])}
        except Exception:
            pass

    import csv as _csv
    rows = list(_csv.reader(io.StringIO(q.stdout.lstrip("\ufeff"))))
    hdr = [h.strip().strip('"') for h in rows[0]]
    ni = next((k for k, h in enumerate(hdr) if h.replace(" ", "") == "TaskName"), 0)
    keep = [rows[0]]
    for row in rows[1:]:
        if len(row) > ni and _relevant(row[ni], prev_names):
            keep.append(row)
    with open(inp, "w", encoding="utf-8-sig", newline="") as f:
        _csv.writer(f).writerows(keep)

    cmd = [sys.executable, os.path.join(HERE, "schtask_dep_gen.py"), "--input", inp]
    if prev:
        cmd += ["--prev", prev]
    cmd += ["--output", os.path.join(HERE, f"{SNAP_PREFIX}{today}.json")]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    sys.stdout.write(r.stdout)
    if r.returncode != 0:
        print("FATAL: dep_gen failed:", r.stderr.strip()[:300])
        return r.returncode

    # Surface the diff as ALERT lines (production flagging).
    out_path = cmd[-1]
    try:
        snap = json.load(open(out_path, encoding="utf-8"))
        diff = snap.get("diff") or {}
        added, removed = diff.get("added", []), diff.get("removed", [])
        for t in added:  print(f"ALERT NEW: {t}")
        for t in removed: print(f"ALERT REMOVED: {t}")
        if not added and not removed:
            print("OK: no task additions or removals since previous snapshot")
    except Exception as e:
        print("WARN: could not parse snapshot for diff summary:", e)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
