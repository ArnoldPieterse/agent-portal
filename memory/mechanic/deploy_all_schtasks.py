#!/usr/bin/env python3
"""deploy_all_schtasks.py - One-shot registration of all Mechanic schtasks.

Run from a NON-SANDBOX White session (elevated or via elev.py):
    python memory/mechanic/deploy_all_schtasks.py

Pre-flight checks, then registers:
  1. PortalLoadProbe   (daily 06:00 - goal #1)
  2. MirrorHeal        (every 15 min - goal #2)
  3. BootRecoverDetect (on start - goal #4)
  4. ChaosDrillMonthly (monthly day 1, 02:00 - goal #8)

Idempotent: skips tasks already registered.
Logs to memory/mechanic/schtasks-deploy-<date>.jsonl
"""
import json, os, subprocess, sys, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent.parent  # project root
LOG_FILE = HERE / "memory" / "mechanic" / f"schtasks-deploy-{datetime.date.today()}.jsonl"

TASKS = [
    {
        "name": "PortalLoadProbe",
        "goal": 1,
        "tr": r'python "%s\memory\ops\loadtest\register_daily_probe.bat"' % str(HERE),
        "schedule": "/sc daily /st 06:00",
        "ru": "SYSTEM",
    },
    {
        "name": "MirrorHeal",
        "goal": 2,
        "tr": r'python "%s\memory\ops\mirror_heal.py"' % str(HERE),
        "schedule": "/sc minute /mo 15",
        "ru": "SYSTEM",
    },
    {
        "name": "BootRecoverDetect",
        "goal": 4,
        "tr": r'python "%s\memory\mechanic\boot_recovery_test.py --auto"' % str(HERE),
        "schedule": "/sc onstart",
        "ru": "SYSTEM",
    },
    {
        "name": "LogRotateDaily",
        "goal": 7,
        "tr": r'python "%s\memory\mechanic\log_rotate.py"' % str(HERE),
        "schedule": "/sc daily /st 03:00",
        "ru": "SYSTEM",
    },
    {
        "name": "ChaosDrillMonthly",
        "goal": 8,
        "tr": r'python "%s\memory\ops\chaos_drill.py --rotate"' % str(HERE),
        "schedule": "/sc month /d 1 /st 02:00",
        "ru": "SYSTEM",
    },
    {
        "name": "ArchivistDecayWeekly",
        "goal": "archivist-3",
        "tr": r'python "%s\memory\archivist\decay_production.py"' % str(HERE),
        "schedule": "/sc week /d MON /st 02:00",
        "ru": "SYSTEM",
    },
    {
        "name": "VerifierSLO",
        "goal": "verifier-8",
        "tr": r'python "%s\memory\verifier\slo_check.py"' % str(HERE),
        "schedule": "/sc daily /st 06:00",
        "ru": "SYSTEM",
    },
]


def log(entry):
    entry["ts"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"  [{entry['status']}] {entry.get('task','preflight')}: {entry.get('detail','')}")


def task_exists(name):
    """Check if a schtask is already registered."""
    r = subprocess.run(
        ["schtasks", "/query", "/tn", name, "/fo", "LIST"],
        capture_output=True, text=True, timeout=10
    )
    return r.returncode == 0


def register_task(task):
    """Register a single schtask. Returns True on success."""
    cmd = [
        "schtasks", "/create", "/tn", task["name"],
        "/tr", task["tr"],
        *task["schedule"].split(),
        "/ru", task["ru"],
        "/f"
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    ok = r.returncode == 0
    log({"task": task["name"], "goal": task["goal"],
         "status": "REGISTERED" if ok else "FAILED",
         "detail": (r.stdout + r.stderr).strip()[:200]})
    return ok


def preflight():
    """Verify schtasks COM works + LAN egress available."""
    # 1. schtasks query
    r = subprocess.run(["schtasks", "/query", "/fo", "CSV"],
                       capture_output=True, text=True, timeout=15)
    if r.returncode != 0:
        log({"status": "FATAL", "detail": f"schtasks COM broken: {r.stderr.strip()[:100]}"})
        return False
    log({"status": "OK", "detail": f"schtasks works ({len(r.stdout.splitlines())} tasks visible)"})

    # 2. LAN egress (try White SMB)
    import socket
    try:
        s = socket.create_connection(("IP_PALE", 445), timeout=3)
        s.close()
        log({"status": "OK", "detail": "LAN egress to .39:445 confirmed"})
    except Exception as e:
        log({"status": "WARN", "detail": f"LAN egress check failed: {e} (tasks may still register)"})

    return True


def main():
    print(f"=== Mechanic schtask deployment ({datetime.date.today()}) ===")
    print(f"Working dir: {HERE}")
    print()

    if not preflight():
        print("\nFATAL: Pre-flight failed. Aborting.")
        sys.exit(1)

    print("\nRegistering tasks:")
    results = []
    for task in TASKS:
        if task_exists(task["name"]):
            log({"task": task["name"], "goal": task["goal"],
                 "status": "SKIPPED", "detail": "already registered"})
            results.append((task["name"], True))
        else:
            ok = register_task(task)
            results.append((task["name"], ok))

    print(f"\nSummary: {sum(1 for _,ok in results if ok)}/{len(results)} tasks ready")
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}: {name}")

    # Post-deploy verification
    print("\nPost-deploy verification (schtasks /query):")
    r = subprocess.run(["schtasks", "/query", "/fo", "CSV"],
                       capture_output=True, text=True, timeout=15)
    for task in TASKS:
        found = task["name"] in r.stdout
        print(f"  {'CONFIRMED' if found else 'MISSING'}: {task['name']}")

    log({"status": "COMPLETE", "detail": f"{sum(1 for _,ok in results if ok)}/{len(results)} tasks registered"})
    print(f"\nLog: {LOG_FILE.relative_to(HERE)}")


if __name__ == "__main__":
    main()