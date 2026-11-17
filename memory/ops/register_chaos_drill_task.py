#!/usr/bin/env python3
"""register_chaos_drill_task.py - register the ChaosDrill monthly scheduled task on White.

Run ONCE from a non-sandbox seat (White ops terminal or via elev.py):
    python memory/ops/register_chaos_drill_task.py

Registers schtask 'FleetChaosDrill' to run monthly on the 1st at 03:00, executing chaos_drill.py.
The drill rotates White->Pale->Black->Red each month (state tracked in chaos-drill-state.json).
Idempotent: re-running updates the existing task rather than failing.

Evidence of registration is logged to memory/mechanic/chaos-drill.jsonl.
"""
import subprocess, sys, os, json
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PYTHON = sys.executable
SCRIPT = os.path.join(HERE, "memory", "ops", "chaos_drill.py")
TASK_NAME = "FleetChaosDrill"
LOG_PATH = os.path.join(HERE, "memory", "mechanic", "chaos-drill.jsonl")


def log_event(entry):
    entry["ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    # Build the schtasks command: monthly on 1st at 03:00
    action = f'"{PYTHON}" "{SCRIPT}"'
    cmd = (
        f'schtasks /create /tn {TASK_NAME} '
        f'/tr {action} '
        f'/sc monthly /d 1 /st 03:00 '
        f'/ru SYSTEM '
        f'/f'
    )
    print(f"Running: {cmd}")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode == 0:
        print(f"SUCCESS: schtask '{TASK_NAME}' registered (monthly 1st @ 03:00, SYSTEM)")
        # Verify
        v = subprocess.run(
            f'schtasks /query /tn {TASK_NAME} /fo list',
            shell=True, capture_output=True, text=True,
        )
        print(v.stdout[:500])
        log_event({"type": "registration", "task": TASK_NAME, "schedule": "monthly 1st 03:00",
                   "verdict": "REGISTERED"})
    else:
        err = (r.stderr or r.stdout).strip()
        print(f"FAILED (rc={r.returncode}): {err}")
        log_event({"type": "registration", "task": TASK_NAME, "verdict": "FAIL",
                   "error": err[:200]})
        sys.exit(1)


if __name__ == "__main__":
    main()