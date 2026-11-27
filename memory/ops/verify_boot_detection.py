#!/usr/bin/env python3
"""verify_boot_detection.py — Companion script for boot-detection-runbook.md.
Verifies the boot-recovery scheduled task is registered and the target script exists.
Exit: 0=OK, 1=task missing or script absent.
"""
import subprocess, sys, json

def main():
    issues = []
    # Check scheduled task exists
    try:
        r = subprocess.run(
            ["schtasks", "/query", "/tn", "BootRecovery"],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode != 0:
            issues.append("Scheduled task 'BootRecovery' not found")
    except Exception as e:
        issues.append(f"Failed to query schtasks: {e}")

    # Check target script exists
    from pathlib import Path
    targets = ["memory/ops/boot_recovery.py", "memory/mechanic/fleet_reload.py"]
    for t in targets:
        if not Path(t).exists():
            issues.append(f"Target script missing: {t}")

    if issues:
        print(json.dumps({"status": "FAIL", "issues": issues}))
        sys.exit(1)
    print(json.dumps({"status": "OK", "task": "BootRecovery registered", "targets_found": targets}))
    sys.exit(0)

if __name__ == "__main__":
    main()
