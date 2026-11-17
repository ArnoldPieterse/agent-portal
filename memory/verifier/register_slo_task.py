#!/usr/bin/env python3
"""One-shot: register + verify the daily SLO scheduled task on White.
Run from a NON-SANDBOX White seat (ops terminal / RDP) with admin:
    python memory/verifier/register_slo_task.py
What it does:
  1. Registers schtask 'VerifierSLO' (daily 06:00, runs slo_enforce.py)
  2. Fires slo_enforce.py once immediately to confirm end-to-end works
  3. Writes evidence to memory/verifier/slo-task-registered.json
Exit 0 = success; non-zero = failure (see stderr).
"""
import subprocess, json, datetime, sys, os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SLO_SCRIPT = os.path.join(SCRIPT_DIR, "slo_enforce.py")
EVIDENCE = os.path.join(SCRIPT_DIR, "slo-task-registered.json")
TASK_NAME = "VerifierSLO"

def run(cmd, **kw):
    print(f"$ {cmd}")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)
    if r.stdout: print(r.stdout.strip())
    if r.stderr: print(r.stderr.strip(), file=sys.stderr)
    return r

def main():
    # 1. Register the task
    python = sys.executable
    tr_cmd = f'"{python}" "{SLO_SCRIPT}"'
    reg_cmd = (f'schtasks /create /tn {TASK_NAME} /tr "{tr_cmd}" '
               f'/sc daily /st 06:00 /rl highest /f')
    r = run(reg_cmd)
    if r.returncode != 0:
        print("FAIL: schtask registration failed", file=sys.stderr)
        sys.exit(1)

    # 2. Fire once to verify end-to-end
    r2 = run(f'"{python}" "{SLO_SCRIPT}"')
    if r2.returncode != 0:
        print("FAIL: slo_enforce.py execution failed", file=sys.stderr)
        sys.exit(2)

    # 3. Write evidence
    ev = {
        "registered_at": datetime.datetime.now().isoformat(),
        "task_name": TASK_NAME,
        "trigger": "daily 06:00",
        "script": SLO_SCRIPT,
        "first_run_output": r2.stdout.strip() if r2.stdout else "(no stdout)",
        "first_run_rc": r2.returncode
    }
    with open(EVIDENCE, "w", encoding="utf-8") as f:
        json.dump(ev, f, indent=2)
    print(f"\nOK: task registered + first run succeeded. Evidence -> {EVIDENCE}")
    print("Next: wait 2 days for automated runs, then close goal #2.")

if __name__ == "__main__":
    main()
