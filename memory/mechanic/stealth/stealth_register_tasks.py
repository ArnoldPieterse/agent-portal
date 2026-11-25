#!/usr/bin/env python3
"""Register stealth workflow schtasks on the local host.

Run from a full-privilege context (not sandbox):
    python stealth_register_tasks.py

Creates 3 hourly tasks (6h interval) with resource budgets via workflow_runner.py.
Idempotent: /f flag overwrites existing tasks.
"""
import subprocess, sys, os
from pathlib import Path

HERE = Path(__file__).resolve().parent
PYTHON = sys.executable
RUNNER = str(HERE / "workflow_runner.py")

TASKS = [
    {
        "name": "Stealth_LeadEnrichment",
        "script": str(HERE / "lead_enrichment.py"),
        "cpu_sec": 120,
        "mem_mb": 256
    },
    {
        "name": "Stealth_ContentRepurpose",
        "script": str(HERE / "content_repurpose.py"),
        "cpu_sec": 180,
        "mem_mb": 256
    },
    {
        "name": "Stealth_InvoiceTracker",
        "script": str(HERE / "invoice_tracker.py"),
        "cpu_sec": 60,
        "mem_mb": 128
    }
]

def main():
    ok = 0
    for t in TASKS:
        cmd = [
            "schtasks", "/create",
            "/tn", t["name"],
            "/tr", f'"{PYTHON}" "{RUNNER}" "{t["script"]}" --budget-cpu-sec {t["cpu_sec"]} --budget-mem-mb {t["mem_mb"]}',
            "/sc", "hourly", "/ri", "6",
            "/f"
        ]
        print(f"Creating: {t['name']}")
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            print(f"  OK: {t['name']} registered (hourly x6)")
            ok += 1
        else:
            print(f"  FAILED: {r.stderr.strip() or r.stdout.strip()}")

    print(f"\nResult: {ok}/{len(TASKS)} tasks registered.")
    if ok < len(TASKS):
        sys.exit(1)

if __name__ == "__main__":
    main()
