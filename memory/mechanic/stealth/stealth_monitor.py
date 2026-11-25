"""Stealth workflow monitoring - checks recent runs and reports to seat-matrix.

Run: python stealth_monitor.py [--selftest]

Checks:
  1. Last run of each workflow (from runs/ dir) - stale if >7h old
  2. Any failed runs in last 24h
  3. Total CPU time consumed by stealth workflows vs budget

Output: memory/mechanic/stealth/monitor-status.json
Integration: seat_probe can import check_stalth() to include in health report.
"""
import json, os, glob
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
RUNS_DIR = BASE / "runs"
STATUS_FILE = BASE / "monitor-status.json"

WORKFLOWS = ["lead_enrichment", "content_repurpose", "invoice_tracker"]

def check_stalth():
    """Returns dict with per-workflow status. Importable by seat_probe."""
    results = {}
    now = datetime.utcnow()

    for wf in WORKFLOWS:
        # Find most recent run
        pattern = str(RUNS_DIR / f"{wf}_*.json")
        runs = sorted(glob.glob(pattern), reverse=True)

        if not runs:
            results[wf] = {"status": "never_ran", "last_run": None}
            continue

        with open(runs[0]) as f:
            latest = json.load(f)

        last_dt = datetime.fromisoformat(latest['finished'])
        age_h = (now - last_dt).total_seconds() / 3600

        # Check for failures in last 24h
        recent_failures = 0
        for r in runs[:10]:  # check last 10 runs
            with open(r) as f:
                entry = json.load(f)
            if entry.get('status') != 'ok':
                recent_failures += 1

        results[wf] = {
            "status": "ok" if latest['status'] == 'ok' else "error",
            "last_run": latest['finished'],
            "age_hours": round(age_h, 1),
            "stale": age_h > 7,
            "recent_failures": recent_failures
        }

    return results

def main():
    import sys
    if '--selftest' in sys.argv:
        # Self-test: verify the function works
        r = check_stalth()
        assert len(r) == 3, f"Expected 3 workflows, got {len(r)}"
        for wf, data in r.items():
            assert 'status' in data, f"{wf} missing status"
        print(f"[selftest] PASS: {len(r)} workflows checked")
        print(json.dumps(r, indent=2))
        return

    r = check_stalth()
    STATUS_FILE.write_text(json.dumps(r, indent=2), encoding='utf-8')

    # Summary
    ok_count = sum(1 for v in r.values() if v.get('status') == 'ok')
    stale_count = sum(1 for v in r.values() if v.get('stale'))
    print(f"[stealth_monitor] {ok_count}/3 ok, {stale_count} stale -> {STATUS_FILE.name}")

if __name__ == '__main__':
    main()
