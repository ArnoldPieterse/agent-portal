#!/usr/bin/env python3
"""
cycle_timeout_diag.py - Cycle Timeout Auto-Diagnostic (Mechanic Goal #3)

When a cycle exceeds its duration SLA (30m), auto-capture:
  - Process list (top memory consumers)
  - Memory snapshot
  - Last 50 log lines per seat (from model-load.jsonl + probe history)
  - Active passes / current state

Output: memory/ops/incidents/cycle-timeout-<timestamp>.md

Usage:
  python memory/mechanic/cycle_timeout_diag.py check [--cycle-start ISO_TS]
  python memory/mechanic/cycle_timeout_diag.py simulate   (forced timeout for testing)
  python memory/mechanic/cycle_timeout_diag.py selftest

Acceptance criteria:
  - Forced timeout produces complete diagnostic within 30s of breach
  - No human needed to trigger diagnosis
  - Structured incident note written to memory/ops/incidents/
"""
import json, sys, time, os
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(".")
OPS_DIR = BASE / "memory" / "ops"
INCIDENTS_DIR = OPS_DIR / "incidents"
MODEL_LOAD_JSONL = OPS_DIR / "model-load.jsonl"
PROBE_HISTORY = OPS_DIR / "fleet-probe-history.jsonl"
CYCLE_DURATIONS = OPS_DIR / "cycle-durations.jsonl"

CYCLE_BUDGET_MIN = 30  # minutes
DIAG_TIMEOUT_S = 30    # must produce diagnostic within this many seconds of breach


def get_timestamp():
    return datetime.now(timezone.utc).isoformat()


def check_cycle_timeout(cycle_start_iso=None):
    """
    Check if the current cycle has exceeded its budget.
    Returns (is_breached: bool, elapsed_min: float, details: dict)
    """
    now = datetime.now(timezone.utc)
    
    if cycle_start_iso:
        try:
            start = datetime.fromisoformat(cycle_start_iso.replace('Z', '+00:00'))
        except ValueError:
            return False, 0, {"error": f"invalid ISO timestamp: {cycle_start_iso}"}
    else:
        # Try to find last cycle start from cycle-durations.jsonl
        if CYCLE_DURATIONS.exists():
            lines = CYCLE_DURATIONS.read_text(encoding='utf-8').strip().split('\n')
            if lines and lines[-1].strip():
                try:
                    last_entry = json.loads(lines[-1])
                    start_iso = last_entry.get("start") or last_entry.get("ts")
                    if start_iso:
                        start = datetime.fromisoformat(start_iso.replace('Z', '+00:00'))
                    else:
                        start = now - timedelta(minutes=CYCLE_BUDGET_MIN + 1)
                except (json.JSONDecodeError, ValueError):
                    start = now - timedelta(minutes=CYCLE_BUDGET_MIN + 1)
        else:
            # No cycle data - assume not breached
            return False, 0, {"note": "no cycle-durations.jsonl found"}

    elapsed_min = (now - start).total_seconds() / 60.0
    is_breached = elapsed_min > CYCLE_BUDGET_MIN
    
    return is_breached, round(elapsed_min, 1), {
        "cycle_start": start.isoformat(),
        "budget_min": CYCLE_BUDGET_MIN,
        "elapsed_min": round(elapsed_min, 1),
    }


def capture_process_list():
    """Capture top memory-consuming processes."""
    try:
        import subprocess
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 10 Name,Id,@{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}} | Format-Table -AutoSize"],
            capture_output=True, text=True, timeout=10,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        return r.stdout.strip() if r.returncode == 0 else "(process list unavailable)"
    except Exception as e:
        return f"(error: {e})"


def capture_memory_snapshot():
    """Capture system memory snapshot."""
    try:
        import subprocess
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "$os = Get-CimInstance Win32_OperatingSystem; "
             f"[PSCustomObject]@{{TotalMB=[math]::Round($os.TotalVisibleMemorySize/1024,0); "
             f"FreeMB=[math]::Round($os.FreePhysicalMemory/1024,0); "
             f"UsedPct=[math]::Round(100*($os.TotalVisibleMemorySize-$os.FreePhysicalMemory)/$os.TotalVisibleMemorySize,1)}} | ConvertTo-Json"],
            capture_output=True, text=True, timeout=10,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        if r.returncode == 0:
            return json.dumps(json.loads(r.stdout.strip()), indent=2)
        return "(memory snapshot unavailable)"
    except Exception as e:
        return f"(error: {e})"


def capture_last_log_lines(n=50):
    """Capture last N lines from relevant log files."""
    logs = {}
    
    if MODEL_LOAD_JSONL.exists():
        lines = MODEL_LOAD_JSONL.read_text(encoding='utf-8').strip().split('\n')
        logs["model-load.jsonl"] = lines[-n:]
    
    if PROBE_HISTORY.exists():
        lines = PROBE_HISTORY.read_text(encoding='utf-8').strip().split('\n')
        logs["fleet-probe-history.jsonl"] = lines[-n:]
    
    return logs


def capture_active_state():
    """Capture current active state (cycle info, seat states)."""
    state = {}
    
    # Seat matrix if available
    seat_matrix_path = OPS_DIR / "seat-matrix.json"
    if seat_matrix_path.exists():
        try:
            sm = json.loads(seat_matrix_path.read_text(encoding='utf-8'))
            state["seats"] = {k: v.get("state") for k, v in sm.get("seats", {}).items()}
        except (json.JSONDecodeError, ValueError):
            pass
    
    # Heartbeat if available
    hb_path = OPS_DIR / "fleet-heartbeat.json"
    if hb_path.exists():
        try:
            hb = json.loads(hb_path.read_text(encoding='utf-8'))
            state["fleet_score"] = hb.get("fleet_score")
            state["stale_seats"] = [k for k, v in hb.get("seats", {}).items() if v.get("stale")]
        except (json.JSONDecodeError, ValueError):
            pass
    
    return state


def generate_diagnostic(cycle_start_iso=None, forced=False):
    """
    Generate the full cycle timeout diagnostic.
    Returns path to the incident file.
    """
    t0 = time.time()
    
    is_breached, elapsed_min, details = check_cycle_timeout(cycle_start_iso)
    if not is_breached and not forced:
        return None  # No breach, no diagnostic needed
    
    ts_compact = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
    diag_path = INCIDENTS_DIR / f"cycle-timeout-{ts_compact}.md"
    
    # Capture all data
    proc_list = capture_process_list()
    mem_snapshot = capture_memory_snapshot()
    logs = capture_last_log_lines(50)
    active_state = capture_active_state()
    
    elapsed_capture_s = round(time.time() - t0, 2)
    
    # Build the diagnostic markdown
    md = f"""# Cycle Timeout Diagnostic

- **Generated**: {get_timestamp()}
- **Forced**: {'YES (test)' if forced else 'NO'}
- **Cycle start**: {details.get('cycle_start', 'unknown')}
- **Elapsed**: {elapsed_min} min (budget: {CYCLE_BUDGET_MIN} min)
- **Capture time**: {elapsed_capture_s}s

## Process List (top 10 by memory)
```
{proc_list}
```

## Memory Snapshot
```
{mem_snapshot}
```

## Active State
```json
{json.dumps(active_state, indent=2)}
```

## Recent Log Lines
"""
    for source, lines_list in logs.items():
        header = "### {} (last {} lines)".format(source, len(lines_list))
        md += header + "\n" + chr(96)*3 + "\n"
        md += "\n".join(lines_list) + "\n" + chr(96)*3 + "\n\n"

    diag_path.write_text(md, encoding='utf-8')
    
    return str(diag_path), elapsed_capture_s


def selftest():
    """Run self-test for cycle timeout auto-diagnostic."""
    print("=== cycle_timeout_diag.py selftest ===")
    passed = 0
    failed = 0

    def check(name, cond, detail=""):
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  ok   - {name}")
        else:
            failed += 1
            print(f"  FAIL - {name} {detail}")

    # Test 1: No breach detected for recent cycle
    is_breached, elapsed, details = check_cycle_timeout(
        cycle_start_iso=datetime.now(timezone.utc).isoformat()
    )
    check("Recent cycle not breached", not is_breached)

    # Test 2: Breach detected for old cycle (>30m ago)
    old_start = (datetime.now(timezone.utc) - timedelta(minutes=35)).isoformat()
    is_breached2, elapsed2, details2 = check_cycle_timeout(cycle_start_iso=old_start)
    check("Old cycle (35m) detected as breached", is_breached2)
    check("Elapsed time reported correctly (~35m)", 34 <= elapsed2 <= 37, f"got {elapsed2}")

    # Test 3: Forced timeout produces diagnostic
    print("\n  [Generating forced timeout diagnostic...]")
    t_start = time.time()
    result = generate_diagnostic(forced=True)
    elapsed_gen = round(time.time() - t_start, 2)
    
    check("Diagnostic generated", result is not None)
    if result:
        diag_path, capture_s = result
        check(f"Capture completed in {capture_s}s (<{DIAG_TIMEOUT_S}s)", capture_s < DIAG_TIMEOUT_S)
        
        # Verify file content
        content = Path(diag_path).read_text(encoding='utf-8')
        check("Diagnostic has process list section", "Process List" in content)
        check("Diagnostic has memory snapshot", "Memory Snapshot" in content)
        check("Diagnostic has log lines section", "Recent Log Lines" in content)
        check("Diagnostic has active state", "Active State" in content)
        check("Diagnostic marks forced/test", "Forced" in content and "YES" in content)
        print(f"  Diagnostic file: {diag_path}")
    
    # Test 4: No-breach case returns None
    result_none = generate_diagnostic(
        cycle_start_iso=datetime.now(timezone.utc).isoformat()
    )
    check("No breach -> no diagnostic (None)", result_none is None)

    print(f"\n=== Results: {passed} PASS, {failed} FAIL ===")
    return failed == 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd = sys.argv[1].lower()
    
    if cmd == "check":
        cycle_start = None
        if "--cycle-start" in sys.argv:
            idx = sys.argv.index("--cycle-start")
            cycle_start = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        is_breached, elapsed, details = check_cycle_timeout(cycle_start)
        print(json.dumps({"breached": is_breached, "elapsed_min": elapsed, **details}))
        sys.exit(0 if not is_breached else 1)
    elif cmd == "simulate":
        result = generate_diagnostic(forced=True)
        if result:
            path, capture_s = result
            print(json.dumps({"diagnostic": path, "capture_time_s": capture_s}))
        else:
            print(json.dumps({"error": "no diagnostic generated"}))
    elif cmd == "selftest":
        ok = selftest()
        sys.exit(0 if ok else 1)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
