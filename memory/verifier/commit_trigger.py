#!/usr/bin/env python3
"""commit_trigger.py — Auto-trigger regression battery on file changes (Verifier goal #1 assist).

Watches: core.js, memory_mirror.py, goal_ledger.py
On change: runs regression_suite.py --static, logs to commit-trigger-log.jsonl.

Usage:
    python memory/verifier/commit_trigger.py          # poll mode (3s interval)
    python memory/verifier/commit_trigger.py --once   # single check + exit
    python memory/verifier/commit_trigger.py --test   # simulate a commit, verify trigger fires

Exit codes: 0 = no changes or suite passed, 1 = suite failed, 2 = error
"""
import hashlib, json, os, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
WATCH_FILES = [
    ROOT / "ui" / "core.js",
    ROOT / "memory_mirror.py",
    ROOT / "goal_ledger.json",
]
SUITE = str(ROOT / "memory" / "verifier" / "regression_suite.py")
LOG = Path(__file__).resolve().parent / "commit-trigger-log.jsonl"
POLL_S = 3
TIMEOUT_S = 300  # 5 min max for suite

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def file_hash(p: Path) -> str:
    if not p.exists():
        return "missing"
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]

def get_state() -> dict:
    return {str(p): file_hash(p) for p in WATCH_FILES}

def load_prev_state() -> dict:
    state_file = LOG.with_suffix(".state.json")
    if state_file.exists():
        return json.loads(state_file.read_text(encoding="utf-8"))
    return {}

def save_state(state: dict):
    state_file = LOG.with_suffix(".state.json")
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

def log_event(event: str, **kw):
    entry = {"ts": now_iso(), "event": event, **kw}
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"[{entry['ts']}] {event}: {kw}", flush=True)

def run_suite() -> dict:
    """Run regression_suite.py --static; return result dict."""
    t0 = time.time()
    try:
        r = subprocess.run(
            [sys.executable, SUITE, "--static"],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=TIMEOUT_S, cwd=str(ROOT)
        )
        elapsed = time.time() - t0
        result = {
            "exit_code": r.returncode,
            "elapsed_s": round(elapsed, 1),
            "within_5min": elapsed < TIMEOUT_S,
            "stdout_tail": r.stdout[-500:] if r.stdout else "",
            "stderr_tail": r.stderr[-300:] if r.stderr else "",
        }
    except subprocess.TimeoutExpired:
        result = {"exit_code": -1, "elapsed_s": TIMEOUT_S, "within_5min": False,
                  "error": "suite timed out at 300s"}
    return result

def check_and_trigger(simulate=False) -> int:
    """One poll cycle. Returns exit code."""
    prev = load_prev_state()
    curr = get_state()

    if simulate:
        # Force a trigger for testing
        changed = [p for p in WATCH_FILES]
        log_event("simulate_commit", files=[str(p.name) for p in changed])
    else:
        changed = [k for k, v in curr.items() if prev.get(k) != v]

    if not changed:
        save_state(curr)
        return 0

    # Files changed — trigger the suite
    log_event("trigger", files=[Path(c).name for c in changed])
    result = run_suite()
    log_event("suite_complete", **result)
    save_state(curr)

    if result.get("exit_code") == 0:
        return 0
    return 1

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="single check and exit")
    ap.add_argument("--test", action="store_true", help="simulate a commit to verify trigger")
    args = ap.parse_args()

    if args.test:
        rc = check_and_trigger(simulate=True)
        sys.exit(rc)

    if args.once:
        rc = check_and_trigger()
        sys.exit(rc)

    # Poll mode
    log_event("daemon_start", poll_s=POLL_S, watch=[p.name for p in WATCH_FILES])
    while True:
        try:
            check_and_trigger()
        except Exception as e:
            log_event("error", error=str(e))
        time.sleep(POLL_S)

if __name__ == "__main__":
    main()
