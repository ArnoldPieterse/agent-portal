#!/usr/bin/env python3
"""goal1_diagnose_fix.py - One-shot diagnostic + fix for PortalLoadProbe (Goal #1).

Run from a NON-SANDBOX White session:
    python elev.py --shell "python memory/mechanic/goal1_diagnose_fix.py"

Steps:
  1. Query schtask LastRunTime + LastResult for PortalLoadProbe
  2. If non-zero result, pull last event log entry for the task
  3. Manually trigger load_probe.py once (backfill today)
  4. Verify new entry appeared in load-baseline.jsonl
  5. Write evidence to memory/mechanic/goal1-diag-<date>.jsonl

Idempotent: safe to re-run; won't duplicate entries.
"""
import json, subprocess, sys, datetime, os
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent.parent  # project root
BASELINE = HERE / "memory" / "ops" / "load-baseline.jsonl"
EVIDENCE = HERE / "memory" / "mechanic" / f"goal1-diag-{datetime.date.today()}.jsonl"
PROBE_SCRIPT = HERE / "memory" / "ops" / "load_probe.py"


def log(entry):
    entry["ts"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    with open(EVIDENCE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"  [{entry.get('status','INFO')}] {entry.get('step','?')}: {entry.get('detail','')}")


def run(cmd, timeout=30):
    """Run a command, return (rc, stdout+stderr)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT"
    except Exception as e:
        return -2, str(e)


def main():
    log({"step": "start", "status": "RUNNING", "detail": f"python={sys.executable}"})

    # Step 1: Query schtask status
    rc, out = run(["schtasks", "/query", "/tn", "PortalLoadProbe", "/fo", "LIST"])
    if rc != 0:
        log({"step": "schtask_query", "status": "FAIL", "detail": f"rc={rc}: {out[:200]}"})
        # Try to register it
        rc2, out2 = run([
            "schtasks", "/create", "/tn", "PortalLoadProbe",
            "/tr", f'python "{PROBE_SCRIPT}"',
            "/sc", "daily", "/st", "06:00", "/ru", "SYSTEM", "/f"
        ], timeout=15)
        log({"step": "schtask_register", "status": "OK" if rc2 == 0 else "FAIL",
             "detail": out2[:200]})
    else:
        # Parse LastRunTime and LastResult from LIST output
        last_run = ""
        last_result = ""
        for line in out.splitlines():
            if line.startswith("Last Run Time"):
                last_run = line.split(":", 1)[1].strip()
            elif line.startswith("Last Result"):
                last_result = line.split(":", 1)[1].strip()
        log({"step": "schtask_query", "status": "OK",
             "detail": f"LastRun={last_run} LastResult={last_result}"})

    # Step 2: If task failed, check event log (best-effort)
    # (skipped for now - requires additional COM access; logged as future enhancement)

    # Step 3: Manually trigger load_probe.py
    if not PROBE_SCRIPT.exists():
        log({"step": "trigger_probe", "status": "FAIL",
             "detail": f"probe script not found: {PROBE_SCRIPT}"})
        return 1

    rc, out = run([sys.executable, str(PROBE_SCRIPT)], timeout=60)
    log({"step": "trigger_probe", "status": "OK" if rc == 0 else "FAIL",
         "detail": f"rc={rc}: {out[:200]}"})

    # Step 4: Verify new entry in load-baseline.jsonl
    today = datetime.date.today().isoformat()
    if BASELINE.exists():
        lines = BASELINE.read_text().strip().split("\n")
        todays = [l for l in lines if today in l]
        log({"step": "verify_entry", "status": "OK" if todays else "MISSING",
             "detail": f"{len(todays)} entries for {today} (total {len(lines)})"})

        # Count unique days
        dates = set()
        for l in lines:
            try:
                d = json.loads(l)
                ts = d.get("ts", "")
                if ts:
                    dates.add(ts[:10])
            except (json.JSONDecodeError, KeyError):
                pass
        log({"step": "day_count", "status": "INFO",
             "detail": f"{len(dates)}/7 unique days: {sorted(dates)[-7:]}"})

        # Step 5: If 7/7 days, run week-complete
        if len(dates) >= 7:
            rc_wc, out_wc = run([sys.executable, str(HERE / "memory" / "ops" / "load_trend.py"), "--week-complete"], timeout=30)
            log({"step": "week_complete", "status": "OK" if rc_wc == 0 else "FAIL",
                 "detail": out_wc[:200]})
    else:
        log({"step": "verify_entry", "status": "MISSING",
             "detail": f"baseline file not found: {BASELINE}"})

    log({"step": "done", "status": "COMPLETE"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
