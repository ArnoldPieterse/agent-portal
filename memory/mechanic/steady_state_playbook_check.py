#!/usr/bin/env python3
"""steady_state_playbook_check.py - Verification for Mechanic cycle-17 goal #2.

Acceptance criteria (memory/goals/mechanic.md):
  (A) All >=4 procedures have complete fields (Trigger + Steps + Rollback).
  (B) The playbook is referenced by fleet-mode.json in steady-state.

Run:  python memory/mechanic/steady_state_playbook_check.py
Exit: 0 all pass, 1 any fail.
"""
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # memory/mechanic
PLAYBOOK = HERE / "steady-state-playbook.md"

# Import the lane's validated writer primitive (same dir).
sys.path.insert(0, str(HERE))
import fleet_mode_infra as fmi  # noqa: E402

passed = failed = 0

def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name}")

print("steady_state_playbook_check.py")

# --- (A) structural completeness -------------------------------------------
text = PLAYBOOK.read_text(encoding="utf-8")
procs = re.findall(r"(?ms)^## Procedure \d+.*?(?=^## |\Z)", text)
check(f">=4 procedures present (found {len(procs)})", len(procs) >= 4)
for i, p in enumerate(procs, 1):
    has_t = bool(re.search(r"\*\*Trigger:\*\*", p))
    has_s = bool(re.search(r"\*\*Steps:\*\*", p))
    has_r = bool(re.search(r"\*\*Rollback:\*\*", p))
    # steps must contain at least one numbered item
    has_step_items = bool(re.search(r"(?m)^\s*1\.\s+", p))
    ok = has_t and has_s and has_r and has_step_items
    check(f"Procedure {i} complete (trigger={has_t} steps={has_s and has_step_items} rollback={has_r})", ok)

# --- (B) referenced by fleet-mode.json in steady-state ---------------------
fixture = HERE / "fixtures" / "steady_state_playbook_check"
shutil.rmtree(fixture, ignore_errors=True)
fixture.mkdir(parents=True, exist_ok=True)
target = fixture / "fleet-mode.json"

# Write a steady-state payload WITHOUT playbook -> primitive must inject the ref.
fmi.atomic_write_fleet_mode(str(target), {
    "mode": "STEADY-STATE",
    "timestamp": "2026-11-25T00:00:00Z",
    "goal_pct": 95.0,
})
back = fmi.read_fleet_mode(str(target))
check("steady-state write accepted (mode=STEADY-STATE)", back.get("mode") == "STEADY-STATE")
check("playbook reference injected into steady-state file", back.get("playbook") == fmi.STEADY_STATE_PLAYBOOK)
ref = Path(back["playbook"])
check(f"referenced playbook exists on disk ({fmi.STEADY_STATE_PLAYBOOK})", ref.exists())

# Non-steady-state write must NOT carry the reference (invariant is mode-scoped).
fmi.atomic_write_fleet_mode(str(target), {
    "mode": "WORK",
    "timestamp": "2026-11-25T00:01:00Z",
    "goal_pct": 40.0,
})
back2 = fmi.read_fleet_mode(str(target))
check("non-steady-state write has no playbook ref", "playbook" not in back2)

shutil.rmtree(fixture, ignore_errors=True)

print(f"\n  Result: {passed}/{passed+failed} passed")
sys.exit(0 if failed == 0 else 1)
