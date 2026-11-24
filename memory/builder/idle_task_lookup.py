#!/usr/bin/env python3
"""idle_task_lookup.py - Deterministic idle-task lookup for the maintenance rotation.

Builds: builder goal 7 (Idle Task Injector, registry half) + mechanic goal 5 (rotation).
Replaces the previous 6-role in-file ROTATION with the JSON registry so all 8 roles
(scribe and mechanic were missing) have >=5 unique tasks.

Registry: memory/ops/maintenance-tasks.json - 8 roles x >=5 tasks, unique ids.
Rotation: task_index = day_of_cycle % len(tasks). Same role + same day always
returns the same task; consecutive days never repeat until the cycle wraps.

Public API (kept compatible with the previous module):
  get_idle_task(role, day_of_cycle=None) -> str   # task description
  lookup(role, day_of_cycle) -> dict              # full task record
  rotation_table(days=7) -> dict                  # role -> [task ids per day]
  validate_registry(reg) -> list[str]             # schema + uniqueness errors

CLI:
  python idle_task_lookup.py <role> [day]         # one lookup (day defaults to today)
  python idle_task_lookup.py --table              # full rotation table (8 roles x 7 days)
  python idle_task_lookup.py --validate           # schema + uniqueness checks, exit 0/1
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
REGISTRY = HERE.parent / "ops" / "maintenance-tasks.json"

REQUIRED_ROLES = {
    "orchestrator", "researcher", "builder", "verifier",
    "designer", "archivist", "scribe", "mechanic",
}
MIN_TASKS = 5


def load_registry(path: Path | str = REGISTRY) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_registry(reg: dict) -> list[str]:
    errs: list[str] = []
    roles = reg.get("roles", {})
    for r in sorted(REQUIRED_ROLES - set(roles)):
        errs.append(f"missing role: {r}")
    seen_ids: set[str] = set()
    for role, tasks in roles.items():
        if len(tasks) < MIN_TASKS:
            errs.append(f"role {role}: only {len(tasks)} tasks (<{MIN_TASKS})")
        for t in tasks:
            tid = t.get("id", "<no-id>")
            if tid in seen_ids:
                errs.append(f"duplicate task id: {tid}")
            seen_ids.add(tid)
            for field in ("description", "command", "expected_output"):
                if not t.get(field):
                    errs.append(f"task {tid}: missing {field}")
    return errs


def lookup(role: str, day_of_cycle: int, path: Path | str = REGISTRY) -> dict:
    """Return the maintenance task record for a role on a given cycle day (0-based)."""
    reg = load_registry(path)
    roles = reg.get("roles", {})
    if role not in roles:
        raise KeyError(f"unknown role {role!r}; known: {sorted(roles)}")
    tasks = roles[role]
    idx = int(day_of_cycle) % len(tasks)
    t = dict(tasks[idx])
    t["role"] = role
    t["day_of_cycle"] = int(day_of_cycle)
    t["task_index"] = idx
    return t


def get_idle_task(role: str, day_of_cycle: int | None = None) -> str:
    """Backward-compatible API: task description string for today (or given day)."""
    if day_of_cycle is None:
        day_of_cycle = today_day_of_cycle()
    return lookup(role.lower(), day_of_cycle)["description"]


def rotation_table(days: int = 7, path: Path | str = REGISTRY) -> dict:
    """Full table: role -> [task id per day for `days` days]."""
    reg = load_registry(path)
    out: dict[str, list[str]] = {}
    for role in sorted(reg.get("roles", {})):
        n = len(reg["roles"][role])
        out[role] = [reg["roles"][role][d % n]["id"] for d in range(days)]
    return out


def today_day_of_cycle() -> int:
    """Cycle anchor: 2026-11-18 (cycle start) -> day index from there."""
    anchor = date(2026, 11, 18)
    return (date.today() - anchor).days % 30


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--validate":
        e = validate_registry(load_registry())
        print("OK: 8 roles, unique ids" if not e else "INVALID:\n  " + "\n  ".join(e))
        sys.exit(0 if not e else 1)
    elif len(sys.argv) >= 2 and sys.argv[1] == "--table":
        tbl = rotation_table()
        for role, ids in tbl.items():
            print(f"{role:13s} " + " ".join(i[:14] for i in ids))
    elif len(sys.argv) >= 2 and sys.argv[1] not in ("--table", "--validate"):
        day = int(sys.argv[2]) if len(sys.argv) > 2 else today_day_of_cycle()
        print(json.dumps(lookup(sys.argv[1], day), indent=2))
    else:
        print(__doc__)
