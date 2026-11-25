#!/usr/bin/env python3
# gate_health.py - Self-monitoring for the gate pipeline.
# Goal #4: checks that all scheduled gate tasks ran within expected interval;
#          if a task is dead, auto-restarts it and logs incident.
#
# Usage:
#   python memory/forge/gate_health.py [--interval-min N] [--no-restart]
#
# Exit codes: 0 = all gates healthy, 1 = one or more stale/dead gates detected.
import sys, os, json, time, subprocess, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_MD = os.path.join(ROOT, "memory", "forge", "log.md")
INCIDENTS = os.path.join(ROOT, "memory", "ops", "incidents.jsonl")
RESULTS_JSONL = os.path.join(ROOT, "memory", "forge", "smoke-results.jsonl")
ELEV = os.path.join(ROOT, "elev.py")

# Expected intervals (minutes) per gate task
GATE_TASKS = {
    "ForgeSmokeSuite": {
        "interval_min": 15,
        "evidence_file": RESULTS_JSONL,
        "restart_cmd": "schtasks /run /tn ForgeSmokeSuite",
        "create_cmd": 'schtasks /create /tn ForgeSmokeSuite /tr "\"python C:\\Projects\\AgentPortal\\memory\\forge\\smoke_suite.py --no-remediate\"" /sc minute /mo 15 /ru SYSTEM /rl HIGHEST',
    },
}


def now_iso():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(msg):
    line = "| " + now_iso() + " | gate_health: " + msg + " |"
    print(line, flush=True)
    try:
        with open(LOG_MD, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def write_incident(entry):
    os.makedirs(os.path.dirname(INCIDENTS), exist_ok=True)
    with open(INCIDENTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def get_last_run_ts(evidence_file):
    """Get the timestamp of the last successful run from a JSONL evidence file."""
    if not os.path.exists(evidence_file):
        return None
    last_line = None
    with open(evidence_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                last_line = line
    if not last_line:
        return None
    try:
        entry = json.loads(last_line)
        ts_str = entry.get("ts", "")
        # Parse "YYYY-MM-DD HH:MM:SS" format
        dt = datetime.datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        return dt
    except (ValueError, KeyError):
        return None


def check_schtasks_exists(task_name):
    """Check if a scheduled task exists via schtasks /query."""
    try:
        r = subprocess.run(
            ["schtasks", "/query", "/tn", task_name],
            capture_output=True, text=True, timeout=10
        )
        return r.returncode == 0
    except Exception:
        return None  # unknown (elev needed)


def restart_task(task_def):
    """Attempt to restart a dead gate task. Returns (success, method)."""
    name = list(task_def.keys())[0] if isinstance(task_def, dict) else task_def
    # Try schtasks /run first (task exists but stale)
    try:
        r = subprocess.run(
            ["schtasks", "/run", "/tn", name],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0:
            return True, "schtasks /run"
    except Exception:
        pass
    # Try creating the task (it was deleted)
    try:
        r = subprocess.run(
            ["schtasks", "/create", "/tn", name,
             "/tr", 'python C:\\Projects\\AgentPortal\\memory\\forge\\smoke_suite.py --no-remediate',
             "/sc", "minute", "/mo", "15", "/ru", "SYSTEM", "/rl", "HIGHEST"],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0:
            return True, "schtasks /create (recreated)"
    except Exception:
        pass
    # Try elev.py
    try:
        r = subprocess.run(
            [sys.executable, ELEV, "--shell", task_def["restart_cmd"]],
            capture_output=True, text=True, timeout=30
        )
        if r.returncode == 0:
            return True, "elev.py"
    except Exception:
        pass
    return False, "all methods failed"


def main():
    no_restart = "--no-restart" in sys.argv
    interval_override = None
    if "--interval-min" in sys.argv:
        idx = sys.argv.index("--interval-min")
        if idx + 1 < len(sys.argv):
            try:
                interval_override = int(sys.argv[idx + 1])
            except ValueError:
                pass

    print("=== Gate Pipeline Health Check: %s ===" % now_iso())
    stale_tasks = []

    for task_name, task_def in GATE_TASKS.items():
        expected_interval = interval_override or task_def["interval_min"]
        evidence_file = task_def["evidence_file"]

        # Check last run from evidence file
        last_ts = get_last_run_ts(evidence_file)
        if last_ts is None:
            status = "NO_EVIDENCE"
            age_min = None
        else:
            age_min = (datetime.datetime.now() - last_ts).total_seconds() / 60.0
            if age_min > expected_interval * 2:
                status = "STALE"
            elif age_min > expected_interval:
                status = "DEGRADED"
            else:
                status = "HEALTHY"

        # Check if schtasks entry exists (may need elev)
        task_exists = check_schtasks_exists(task_name)

        print("  %-20s status=%-10s age=%s task_registered=%s" % (
            task_name, status,
            "%.1f min" % age_min if age_min is not None else "N/A",
            task_exists))

        if status in ("STALE", "NO_EVIDENCE"):
            stale_tasks.append((task_name, status, task_def))

    # Remediate stale tasks
    if stale_tasks and not no_restart:
        print("\n--- Remediating %d stale gate(s) ---" % len(stale_tasks))
        for name, status, task_def in stale_tasks:
            print("  Restarting: %s (%s)" % (name, status))
            ok, method = restart_task(task_def)
            if ok:
                log("%s RESTARTED via %s" % (name, method))
            else:
                log("%s RESTART FAILED (all methods exhausted)" % name)
                write_incident({
                    "ts": now_iso(),
                    "type": "gate_task_dead",
                    "task": name,
                    "status": status,
                    "restart_attempted": True,
                    "restart_result": "FAILED"
                })
    elif stale_tasks:
        for name, status, _ in stale_tasks:
            write_incident({
                "ts": now_iso(),
                "type": "gate_task_stale",
                "task": name,
                "status": status,
                "restart_attempted": False
            })

    if not stale_tasks:
        print("\nAll gates healthy.")
        log("ALL GATES HEALTHY")
        sys.exit(0)
    else:
        print("\n%d gate(s) need attention." % len(stale_tasks))
        log("%d STALE GATE(S): %s" % (len(stale_tasks), [t[0] for t in stale_tasks]))
        sys.exit(1)


if __name__ == "__main__":
    main()
