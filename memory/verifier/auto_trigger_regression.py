#!/usr/bin/env python3
"""Auto-Trigger Regression Battery - Verifier Goal #1 (Fleet Autonomy Convergence cycle)

Watches core.js, memory_mirror.py, and goal_ledger.py for changes.
When a change is detected, runs the full regression suite automatically.
No human prompt required.

Usage:
    python memory/verifier/auto_trigger_regression.py --poll       # single poll cycle (for schtask)
    python memory/verifier/auto_trigger_regression.py --daemon     # continuous watch (5s interval)
    python memory/verifier/auto_trigger_regression.py --simulate   # simulate a file change to test trigger
    python memory/verifier/auto_trigger_regression.py --register   # register as Windows schtask (every 5 min)

Exit codes:
  0 = no change detected OR suite passed
  1 = suite failed (change triggered, tests red)
  2 = trigger fired but suite could not run (infra issue)
"""
import argparse, hashlib, json, os, sys, time, subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
VERIFIER_DIR = Path(__file__).resolve().parent
STATE_FILE = VERIFIER_DIR / "auto_trigger_state.json"
LOG_FILE = VERIFIER_DIR / "auto_trigger_log.jsonl"
REGRESSION_SUITE = VERIFIER_DIR / "regression_suite.py"

# Files to watch (relative to ROOT)
WATCHED_FILES = [
    "ui/core.js",
    "memory_mirror.py",
    "goal_ledger.json",
]

POLL_INTERVAL_S = 5  # daemon mode


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(entry: dict):
    """Append a JSONL log entry."""
    entry["ts"] = _now()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _file_hash(path: Path) -> str | None:
    """SHA256 of file content, or None if missing."""
    if not path.exists():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def get_current_hashes() -> dict:
    """Compute hashes of all watched files."""
    hashes = {}
    for rel in WATCHED_FILES:
        full = ROOT / rel
        hashes[rel] = _file_hash(full)
    return hashes


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"last_hashes": {}, "last_run": None, "trigger_count": 0}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def detect_changes(current: dict, previous: dict) -> list[str]:
    """Return list of files that changed (new or modified)."""
    changed = []
    for rel, h in current.items():
        prev_h = previous.get(rel)
        if h != prev_h:
            changed.append(rel)
    return changed


def run_regression_suite() -> tuple[int, str]:
    """Run the full regression suite; return (exit_code, summary)."""
    if not REGRESSION_SUITE.exists():
        return 2, "regression_suite.py not found"
    try:
        result = subprocess.run(
            [sys.executable, str(REGRESSION_SUITE), "--full"],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=300, cwd=str(ROOT)
        )
        summary = (result.stdout or "")[:500]
        return result.returncode, summary
    except subprocess.TimeoutExpired:
        return 2, "TIMEOUT: suite exceeded 300s"
    except OSError as e:
        return 2, f"OS error running suite: {e}"


def poll_once() -> int:
    """Single poll cycle: check for changes, trigger if needed."""
    state = load_state()
    current = get_current_hashes()
    
    # First run: just record baseline
    if not state["last_hashes"]:
        state["last_hashes"] = current
        state["last_run"] = _now()
        save_state(state)
        _log({"event": "baseline", "hashes": {k: (v[:12] if v else None) for k, v in current.items()}})
        return 0
    
    changed = detect_changes(current, state["last_hashes"])
    
    if not changed:
        state["last_run"] = _now()
        save_state(state)
        return 0
    
    # Change detected - trigger suite
    state["trigger_count"] += 1
    state["last_hashes"] = current
    state["last_run"] = _now()
    save_state(state)
    
    _log({"event": "trigger", "changed": changed, "trigger_num": state["trigger_count"]})
    
    exit_code, summary = run_regression_suite()
    status = "PASS" if exit_code == 0 else ("FAIL" if exit_code == 1 else "ERROR")
    _log({"event": "result", "status": status, "exit_code": exit_code, "summary": summary[:200]})
    
    return exit_code


def simulate_change():
    """Simulate a file change to test the trigger path."""
    target = ROOT / WATCHED_FILES[0]
    if not target.exists():
        print(f"Cannot simulate: {WATCHED_FILES[0]} not found")
        return 1
    
    # Record pre-sim state, then directly run the suite
    _log({"event": "simulate_start", "file": WATCHED_FILES[0]})
    exit_code, summary = run_regression_suite()
    status = "PASS" if exit_code == 0 else ("FAIL" if exit_code == 1 else "ERROR")
    _log({"event": "simulate_result", "status": status, "exit_code": exit_code})
    print(f"Suite result: {status} (exit {exit_code})")
    print(summary[:300])
    return exit_code


def register_schtasks():
    """Prepare schtask registration artifacts."""
    task_name = "VerifierAutoTrigger"
    python_exe = sys.executable
    script = str(VERIFIER_DIR / Path(__file__).name)
    
    # Write a batch wrapper for schtask
    bat_path = VERIFIER_DIR / "auto_trigger_poll.bat"
    log_path = VERIFIER_DIR / "auto_trigger_schtasks.log"
    bat_content = f'@echo off\n"{python_exe}" "{script}" --poll >> "{log_path}" 2>&1\n'
    bat_path.write_text(bat_content, encoding="utf-8")
    
    _log({"event": "register_prepped", "task": task_name, "bat": str(bat_path)})
    print(f"Wrote batch wrapper: {bat_path}")
    print(f"To register (admin): schtasks /create /tn {task_name} /tr \"{bat_path}\" /sc minute /mo 5 /f")
    print("Or via elev.py: python elev.py schtasks /create /tn VerifierAutoTrigger /tr \"%BAT%\" /sc minute /mo 5 /f")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Auto-trigger regression battery")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--poll", action="store_true", help="Single poll cycle")
    group.add_argument("--daemon", action="store_true", help="Continuous watch")
    group.add_argument("--simulate", action="store_true", help="Simulate trigger (test)")
    group.add_argument("--register", action="store_true", help="Prepare schtask registration")
    args = parser.parse_args()
    
    if args.poll:
        sys.exit(poll_once())
    elif args.daemon:
        print(f"Watching {WATCHED_FILES} every {POLL_INTERVAL_S}s (Ctrl+C to stop)")
        while True:
            poll_once()
            time.sleep(POLL_INTERVAL_S)
    elif args.simulate:
        sys.exit(simulate_change())
    elif args.register:
        sys.exit(register_schtasks())


if __name__ == "__main__":
    main()