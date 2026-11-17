#!/usr/bin/env python3
"""register_mirror_heal_task.py - register the MirrorHeal scheduled task on White.

Run ONCE from a non-sandbox seat (White ops terminal or via elev.py):
    python memory/ops/register_mirror_heal_task.py

Registers schtask 'MirrorHeal' to run every 15 minutes, executing mirror_heal.py.
Idempotent: re-running updates the existing task rather than failing.

Recreated 2026-11-17 after mirror revert.
"""
import subprocess, sys, os

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PYTHON = sys.executable
SCRIPT = os.path.join(HERE, "memory", "ops", "mirror_heal.py")
TASK_NAME = "MirrorHeal"


def main():
    # Build the schtasks command
    action = f'"{PYTHON}" "{SCRIPT}"'
    cmd = (
        f'schtasks /create /tn {TASK_NAME} '
        f'/tr {action} '
        f'/sc minute /mo 15 '
        f'/ru SYSTEM '
        f'/f'
    )
    print(f"Running: {cmd}")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode == 0:
        print(f"SUCCESS: schtask '{TASK_NAME}' registered (every 15 min, SYSTEM)")
        # Verify
        v = subprocess.run(f'schtasks /query /tn {TASK_NAME} /fo list', shell=True,
                           capture_output=True, text=True)
        print(v.stdout[:500])
    else:
        print(f"FAILED (rc={r.returncode}): {r.stderr or r.stdout}")
        sys.exit(1)


if __name__ == "__main__":
    main()
