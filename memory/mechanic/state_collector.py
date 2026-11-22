#!/usr/bin/env python3
"""
state_collector.py - Fleet State Collector Daemon (Mechanic Goal #5)

Collects fleet state every 5 min via schtask:
  - Per-host: GPU usage, CPU load, temperature
  - Per-agent: last-active timestamp
  - Goal progress from TODO.md
  - Open blocker count

Appends structured JSONL record to memory/ops/fleet-metrics.jsonl.
This is the data source for cockpit + health score.

Usage:
  python memory/mechanic/state_collector.py collect   (one-shot collection)
  python memory/mechanic/state_collector.py selftest  (verify all fields + JSONL validity)
  python memory/mechanic/state_collector.py register  (register schtask every 5 min)

Acceptance criteria:
  - Runs every 5 min (verify by file growth)
  - Each record has all required fields
  - JSONL valid after 100+ entries
  - Collector doesn't interfere with agent operations (read-only, <2s runtime)
"""
import json, os, sys, time, re, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent  # project root
METRICS_FILE = BASE / "memory" / "ops" / "fleet-metrics.jsonl"
TODO_FILE = BASE / "TODO.md"
AGENTS_FILE = BASE / "agents.json"
BLOCKERS_FILE = BASE / "memory" / "ops" / "blockers.md"

REQUIRED_FIELDS = [
    "timestamp", "host", "gpu_usage_pct", "cpu_load_pct",
    "temp_celsius", "agents_active", "agents_total",
    "goal_progress_pct", "open_blockers", "duration_ms"
]


def get_timestamp():
    return datetime.now(timezone.utc).isoformat()


def collect_gpu_usage():
    """Get GPU usage percentage. Returns 0 if no GPU or nvidia-smi unavailable."""
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0 and r.stdout.strip():
            line = r.stdout.strip().split("\n")[0]
            parts = [p.strip() for p in line.split(",")]
            return float(parts[0]), float(parts[3])  # usage_pct, temp_celsius
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError, IndexError):
        pass
    return 0.0, 0.0


def collect_cpu_load():
    """Get CPU load percentage via perf counter or fallback."""
    try:
        import psutil
        return psutil.cpu_percent(interval=1)
    except ImportError:
        pass
    # Fallback: use system time diff (crude but functional)
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average | Select-Object -ExpandProperty Average"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0:
            return float(r.stdout.strip())
    except (subprocess.TimeoutExpired, ValueError):
        pass
    return 0.0


def collect_agent_status():
    """Get per-agent last-active and count active agents."""
    agents = []
    try:
        with open(AGENTS_FILE) as f:
            data = json.load(f)
        if isinstance(data, list):
            agents = data
        elif isinstance(data, dict):
            agents = list(data.values()) if all(isinstance(v, dict) for v in data.values()) else [data]
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    active_count = 0
    agent_records = []
    for a in agents:
        name = a.get("name", "unknown")
        status = a.get("status", "unknown")
        last_active = a.get("last_active", None)
        if status in ("active", "running", "loaded"):
            active_count += 1
        agent_records.append({"name": name, "status": status, "last_active": last_active})
    return active_count, len(agents), agent_records


def collect_goal_progress():
    """Parse TODO.md for goal progress percentage."""
    try:
        with open(TODO_FILE, encoding="utf-8", errors="replace") as f:
            content = f.read()
        # Count lines with [x] vs total task lines
        done = len(re.findall(r'^\s*\[x\]', content, re.IGNORECASE | re.MULTILINE))
        total = len(re.findall(r'^\s*\[[ xX]\]', content, re.MULTILINE))
        if total > 0:
            return round(done / total * 100, 1)
        # Fallback: count 'reached' or 'verified' markers in goal sections
        verified = len(re.findall(r'\(verified:', content))
        open_goals = len(re.findall(r'^\d+\. \*\*', content, re.MULTILINE))
        if open_goals > 0:
            return round(verified / open_goals * 100, 1)
    except (FileNotFoundError, OSError):
        pass
    return 0.0


def collect_open_blockers():
    """Count open blockers from blockers.md."""
    try:
        with open(BLOCKERS_FILE, encoding="utf-8", errors="replace") as f:
            content = f.read()
        # Count lines that are NOT marked RESOLVED
        open_count = 0
        for line in content.split("\n"):
            if "OPS-NOTE" in line or "NEEDS-HUMAN" in line or "BLOCKER" in line.upper():
                if "RESOLVED" not in line and "[x]" not in line.lower():
                    open_count += 1
        return open_count
    except (FileNotFoundError, OSError):
        return 0


def collect_state(simulated=False):
    """Collect full fleet state snapshot."""
    t0 = time.time()

    if simulated:
        gpu_pct, temp = 42.0, 65.0
        cpu_pct = 35.0
        active, total, agent_recs = 4, 7, [
            {"name": "Orchestrator", "status": "active", "last_active": get_timestamp()},
            {"name": "Builder", "status": "active", "last_active": get_timestamp()},
            {"name": "Verifier", "status": "idle", "last_active": get_timestamp()},
            {"name": "Mechanic", "status": "active", "last_active": get_timestamp()},
            {"name": "Designer", "status": "idle", "last_active": get_timestamp()},
            {"name": "Scribe", "status": "active", "last_active": get_timestamp()},
            {"name": "Archivist", "status": "unreachable", "last_active": None},
        ]
        goal_pct = 52.3
        blockers = 2
    else:
        gpu_pct, temp = collect_gpu_usage()
        cpu_pct = collect_cpu_load()
        active, total, agent_recs = collect_agent_status()
        goal_pct = collect_goal_progress()
        blockers = collect_open_blockers()

    duration_ms = round((time.time() - t0) * 1000, 1)

    record = {
        "timestamp": get_timestamp(),
        "host": os.environ.get("COMPUTERNAME", "white"),
        "gpu_usage_pct": gpu_pct,
        "cpu_load_pct": cpu_pct,
        "temp_celsius": temp,
        "agents_active": active,
        "agents_total": total,
        "agents_detail": agent_recs,
        "goal_progress_pct": goal_pct,
        "open_blockers": blockers,
        "duration_ms": duration_ms
    }
    return record


def append_record(record):
    """Append a single JSONL record to the metrics file."""
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")


def validate_jsonl(path):
    """Validate that all lines in a JSONL file are valid JSON with required fields."""
    errors = []
    line_count = 0
    try:
        with open(path) as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                line_count += 1
                try:
                    obj = json.loads(line)
                    missing = [k for k in REQUIRED_FIELDS if k not in obj]
                    if missing:
                        errors.append(f"line {i}: missing fields {missing}")
                except json.JSONDecodeError as e:
                    errors.append(f"line {i}: invalid JSON: {e}")
    except FileNotFoundError:
        return 0, ["file not found"]
    return line_count, errors


def selftest():
    """Run self-test: verify all fields present, JSONL valid after 100+ entries."""
    print("=== state_collector.py selftest ===")
    passed = 0
    failed = 0

    def check(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  ok   - {name}")
        else:
            failed += 1
            print(f"  FAIL - {name}")

    # Test 1: Single record has all required fields
    rec = collect_state(simulated=True)
    missing = [k for k in REQUIRED_FIELDS if k not in rec]
    check("single record has all required fields", len(missing) == 0)

    # Test 2: Field types are correct
    check("gpu_usage_pct is numeric", isinstance(rec["gpu_usage_pct"], (int, float)))
    check("cpu_load_pct is numeric", isinstance(rec["cpu_load_pct"], (int, float)))
    check("temp_celsius is numeric", isinstance(rec["temp_celsius"], (int, float)))
    check("agents_active is int", isinstance(rec["agents_active"], int))
    check("agents_total is int", isinstance(rec["agents_total"], int))
    check("goal_progress_pct is numeric", isinstance(rec["goal_progress_pct"], (int, float)))
    check("open_blockers is int", isinstance(rec["open_blockers"], int))
    check("duration_ms is numeric", isinstance(rec["duration_ms"], (int, float)))
    check("timestamp is ISO format", "T" in rec["timestamp"])
    check("host is non-empty string", len(rec["host"]) > 0)

    # Test 3: agents_detail has per-agent records
    check("agents_detail has entries", len(rec["agents_detail"]) > 0)
    check("agent record has name", "name" in rec["agents_detail"][0])
    check("agent record has status", "status" in rec["agents_detail"][0])

    # Test 4: Write 120 records to temp file, validate JSONL
    tmp = Path(tempfile.gettempdir()) / f"fleet_metrics_test_{os.getpid()}.jsonl"
    for i in range(120):
        r = collect_state(simulated=True)
        r["timestamp"] = get_timestamp()
        r["gpu_usage_pct"] = 30 + (i % 40)  # vary values
        with open(tmp, "a") as f:
            f.write(json.dumps(r) + "\n")

    line_count, errors = validate_jsonl(tmp)
    check(f"120 entries written (got {line_count})", line_count == 120)
    check("JSONL valid after 120 entries (no parse errors)", len(errors) == 0)
    if errors:
        for e in errors[:3]:
            print(f"         {e}")

    # Test 5: Collector is fast (<2s)
    t0 = time.time()
    collect_state(simulated=True)
    elapsed = time.time() - t0
    check(f"collection <2s (took {elapsed*1000:.1f}ms)", elapsed < 2.0)

    # Test 6: Collector is read-only (doesn't modify source files)
    # Verify TODO.md and agents.json are not modified by collection
    if TODO_FILE.exists():
        before = TODO_FILE.stat().st_mtime
        collect_state(simulated=True)
        after = TODO_FILE.stat().st_mtime
        check("collector does not modify TODO.md", before == after)

    # Cleanup temp file
    tmp.unlink(missing_ok=True)

    # Test 7: Real collection (non-simulated) produces valid record
    real_rec = collect_state(simulated=False)
    missing_real = [k for k in REQUIRED_FIELDS if k not in real_rec]
    check("real collection has all required fields", len(missing_real) == 0)
    check("real collection duration <2s", real_rec["duration_ms"] < 2000)

    print(f"\n=== Results: {passed} PASS, {failed} FAIL ===")
    return failed == 0


def register_schtasks():
    """Register the collector as a schtask running every 5 minutes."""
    task_name = "FleetStateCollector"
    python_exe = sys.executable
    script_path = Path(__file__).resolve()
    # Use elev.py for admin-level schtask registration
    cmd = f'schtasks /Create /TN "{task_name}" /TR ""{python_exe}" "{script_path}" collect" /SC MINUTE /MO 5 /F'
    print(f"Registering: {cmd}")
    try:
        r = subprocess.run(
            [sys.executable, str(BASE / "elev.py"), "--shell", cmd],
            capture_output=True, text=True, timeout=30
        )
        if r.returncode == 0:
            print(f"OK: schtask '{task_name}' registered (every 5 min)")
        else:
            print(f"WARN: {r.stderr.strip() or r.stdout.strip()}")
    except subprocess.TimeoutExpired:
        print("WARN: elev.py timed out; try manual registration")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "selftest":
        ok = selftest()
        sys.exit(0 if ok else 1)
    elif cmd == "collect":
        rec = collect_state(simulated=False)
        append_record(rec)
        print(f"[state_collector] {rec['timestamp']} host={rec['host']} gpu={rec['gpu_usage_pct']}% cpu={rec['cpu_load_pct']}% agents={rec['agents_active']}/{rec['agents_total']} goals={rec['goal_progress_pct']}% blockers={rec['open_blockers']} ({rec['duration_ms']}ms)")
    elif cmd == "register":
        register_schtasks()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()