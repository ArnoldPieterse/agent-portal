#!/usr/bin/env python3
"""dispatch_filter.py - Canonical per-agent dispatch decision (cycle-15 verifier G4).

Reference implementation of the auto-loop's task-selection rules, kept importable so
the fuzzer (memory/verifier/dispatch_fuzzer.py) can drive it with 100 random configs.
Rules (mirror agent_portal._autoloop pass builder):
  1. queued human message      -> kind "queued" (handled FIRST)
  2. open goals exist           -> kind "goal": text lists ONLY the open goals
  3. all reached + MAINT/IDLE   -> kind "maintenance": role's daily rotation task
                                   (memory/ops/idle-maintenance-rotation-2026-11-24.md)
  4. otherwise                  -> kind "generic" (contribute-to-team menu)
Invariants the fuzzer asserts on every config:
  * a REACHED goal title never appears in any dispatch text
  * MAINT/IDLE with all goals reached always yields the exact rotation-table task
"""
import os, re, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ROTATION_FILE = os.path.join(ROOT, "memory", "ops", "idle-maintenance-rotation-2026-11-24.md")
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]

_cache = {"ts": 0.0, "tasks": {}}

def parse_rotation_table(path=ROTATION_FILE):
    """role(lower) -> [5 task strings], one per Mon..Fri column."""
    tasks = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"^\|\s*([A-Za-z]+)\s*\|(.+)\|\s*$", line.strip())
                if not m or m.group(1).lower() == "role":
                    continue
                cells = [c.strip() for c in m.group(2).split("|") if c.strip()]
                if len(cells) >= 5:
                    tasks[m.group(1).lower()] = cells[:5]
    except OSError:
        pass
    return tasks

def rotation_table(force=False):
    now = time.time()
    if force or now - _cache["ts"] > 3600 or not _cache["tasks"]:
        t = parse_rotation_table()
        if t:
            _cache.update(ts=now, tasks=t)
    return _cache["tasks"]

def rotation_task(role, wday=None):
    """'task (Day)' for the role's daily slot; None if the role has no row."""
    row = rotation_table().get(str(role).lower())
    if not row:
        return None
    idx = (time.localtime().tm_wday if wday is None else wday) % 5
    return "%s (%s)" % (row[idx], DAYS[idx])

def dispatch(agent_name, open_goals=(), reached_goals=(), mode=None,
             queued=False, wday=None):
    """Pure decision: returns {kind, text}. No file writes, no side effects."""
    if queued:
        return {"kind": "queued",
                "text": ("a queued human message is waiting and will be injected below - handle it "
                         "FIRST, then take ONE concrete step on your open goals.")}
    og = list(open_goals or [])
    if og:
        glines = "\n".join("- %s" % g for g in og)
        return {"kind": "goal",
                "text": ("Work your oldest open goal TO COMPLETION this pass. Your open goals:\n%s\n"
                         "Iterate tool calls until its verification criteria are genuinely met, then "
                         "mark it reached in memory/goals/%s.md with a timestamped evidence line." % (glines, str(agent_name).lower()))}
    mode_u = str(mode or "").upper()
    rot = rotation_task(agent_name, wday=wday)
    if rot and mode_u in ("MAINTENANCE", "IDLE"):
        return {"kind": "maintenance",
                "text": ("your goals are 100%% reached and the fleet is in %s mode - do this ONE "
                         "role-specific maintenance task (rotated daily): %s." % (mode_u, rot))}
    return {"kind": "generic",
            "text": ("your goals are 100%% reached - contribute to the team while you wait - pick ONE of: "
                     "(a) write a prediction/forecast for another agent's open goal, (b) draft a solution "
                     "or workflow improvement into memory/ops/, (c) verify and close one stale evidence "
                     "claim in the ledger, (d) do one concrete step on another agent's oldest open goal.")}

if __name__ == "__main__":
    import json
    print(json.dumps({"rotation_rows": len(rotation_table()),
                      "sample": dispatch("archivist", open_goals=["demo goal"], mode="WORK")}, indent=2))