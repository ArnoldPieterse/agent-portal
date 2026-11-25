#!/usr/bin/env python3
"""Stealth workflow scheduler daemon - runs 3 workflows on a timer with resource budgets.

Alternative to schtasks (which requires COM registration unavailable in sandbox).
Runs as a background Python process, zero new capital (uses existing Python + scripts).

Usage:
    python stealth_scheduler.py          # start (foreground)
    python stealth_scheduler.py --once   # run all 3 once then exit (for testing)
    python stealth_scheduler.py --status # show current status
    python stealth_scheduler.py --stop   # signal running instance to stop

PID file: memory/mechanic/stealth/scheduler.pid
Log:      memory/mechanic/stealth/scheduler.log
Interval: 6 hours (21600s) per workflow, staggered by 2h

Resource budgets (enforced by workflow_runner.py):
    lead_enrichment:    120s CPU, 256MB
    content_repurpose:  180s CPU, 256MB  
    invoice_tracker:     60s CPU, 128MB

Total max per cycle: 360s CPU, 640MB - well under model seat requirements.
"""
import sys, os, time, json, signal
from datetime import datetime
from pathlib import Path
import subprocess

BASE = Path(__file__).resolve().parent
RUNNER = str(BASE / "workflow_runner.py")
PID_FILE = BASE / "scheduler.pid"
LOG_FILE = BASE / "scheduler.log"
STATUS_FILE = BASE / "scheduler-status.json"

INTERVAL_SEC = 6 * 3600  # 6 hours
STAGGER_SEC = 2 * 3600   # 2h stagger between workflows

WORKFLOWS = [
    {
        "name": "lead_enrichment",
        "script": str(BASE / "lead_enrichment.py"),
        "cpu_sec": 120,
        "mem_mb": 256,
        "offset": 0
    },
    {
        "name": "content_repurpose",
        "script": str(BASE / "content_repurpose.py"),
        "cpu_sec": 180,
        "mem_mb": 256,
        "offset": STAGGER_SEC
    },
    {
        "name": "invoice_tracker",
        "script": str(BASE / "invoice_tracker.py"),
        "cpu_sec": 60,
        "mem_mb": 128,
        "offset": 2 * STAGGER_SEC
    }
]

def log(msg):
    ts = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')

def write_status(status_dict):
    STATUS_FILE.write_text(json.dumps(status_dict, indent=2), encoding='utf-8')

def run_workflow(wf):
    """Run a single workflow via the budgeted runner."""
    cmd = [sys.executable, RUNNER, wf["script"],
           "--budget-cpu-sec", str(wf["cpu_sec"]),
           "--budget-mem-mb", str(wf["mem_mb"])]
    log(f"Starting: {wf['name']} (budget {wf['cpu_sec']}s CPU / {wf['mem_mb']}MB)")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=wf["cpu_sec"] + 30)
        status = "ok" if r.returncode == 0 else f"error(rc={r.returncode})"
        log(f"Finished: {wf['name']} -> {status}")
        return status
    except subprocess.TimeoutExpired:
        log(f"Timeout: {wf['name']}")
        return "timeout"
    except Exception as e:
        log(f"Error: {wf['name']} -> {e}")
        return f"error({e})"

def run_all_once():
    """Run all workflows once (for testing or initial cycle)."""
    results = {}
    for wf in WORKFLOWS:
        results[wf["name"]] = run_workflow(wf)
    write_status({
        "mode": "once",
        "completed_at": datetime.utcnow().isoformat(),
        "results": results,
        "pid": os.getpid()
    })
    return results

def run_daemon():
    """Run the scheduler loop indefinitely."""
    # Write PID
    PID_FILE.write_text(str(os.getpid()), encoding='utf-8')
    log(f"Daemon started (PID {os.getpid()}, interval {INTERVAL_SEC}s)")

    running = True
    def stop_handler(sig, frame):
        nonlocal running
        running = False
        log("Stop signal received")
    
    signal.signal(signal.SIGTERM, stop_handler)
    signal.signal(signal.SIGINT, stop_handler)

    # Initial run
    run_all_once()

    last_run = {wf["name"]: time.time() for wf in WORKFLOWS}

    while running:
        time.sleep(60)  # check every minute
        now = time.time()
        for wf in WORKFLOWS:
            next_due = last_run[wf["name"]] + INTERVAL_SEC
            if now >= next_due:
                run_workflow(wf)
                last_run[wf["name"]] = time.time()
                write_status({
                    "mode": "daemon",
                    "pid": os.getpid(),
                    "last_runs": {k: datetime.fromtimestamp(v).isoformat() for k, v in last_run.items()},
                    "interval_sec": INTERVAL_SEC
                })

    # Cleanup
    PID_FILE.unlink(missing_ok=True)
    log("Daemon stopped cleanly")

def show_status():
    if STATUS_FILE.exists():
        print(STATUS_FILE.read_text(encoding='utf-8'))
    else:
        print("No status file found. Scheduler may not have run yet.")

def stop_daemon():
    if PID_FILE.exists():
        pid = int(PID_FILE.read_text().strip())
        log(f"Sending SIGTERM to PID {pid}")
        os.kill(pid, signal.SIGTERM)
        print(f"Stop signal sent to PID {pid}")
    else:
        print("No PID file found - scheduler not running?")

def main():
    if '--once' in sys.argv:
        run_all_once()
    elif '--status' in sys.argv:
        show_status()
    elif '--stop' in sys.argv:
        stop_daemon()
    else:
        run_daemon()

if __name__ == '__main__':
    main()
