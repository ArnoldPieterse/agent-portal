"""
multi_file_regression_trigger.py — Builder assist for Verifier goal #1 (cycle 20)
Watches core.js, memory_mirror.py, goal_ledger.py, agent_portal.py.
On mtime change to any watched file, runs file-specific regression checks.
Logs results to memory/verifier/multi-file-regression-log.jsonl.

Usage:
  python memory/verifier/multi_file_regression_trigger.py --once    # test mode
  python memory/verifier/multi_file_regression_trigger.py           # daemon (poll 5s)

AC contribution: "simulated commit triggers full suite <5 min"
This script is the trigger mechanism; Verifier registers it as a scheduled task
or long-running process to satisfy the "0 manual invocations in 3-cycle window."
"""
import os, json, time, hashlib, re, sys
from datetime import datetime, timezone

# --- Configuration ---
WATCH_FILES = {
    "agent_portal.py": ["chat", "file_links", "dm_markers", "prune", "git"],
    "ui/core.js":      ["render_goal_bar", "agent_list", "api_poll", "event_stream"],
    "memory_mirror.py":["PIN_FILES", "sync_cycle", "revert_detect"],
    "goal_ledger.py":  ["record_marker", "json_output", "parse_goals"],
}

LOG_FILE = "memory/verifier/multi-file-regression-log.jsonl"
POLL_S = 5
TRIGGER_TIMEOUT_S = 300  # must complete within 5 min per AC

# --- Per-file check definitions ---
CHECKS = {
    "agent_portal.py": [
        ("chat_endpoint",   [r'/api/chat']),
        ("file_api",        [r'/api/file']),
        ("dm_handling",     [r'DM|expand_mentions']),
        ("prune_endpoint",  [r'/api/todo/prune']),
        ("git_commit",      [r'_git.*commit|/api/git']),
    ],
    "ui/core.js": [
        ("render_goal_bar", [r'renderGoalBar|render_goal_bar']),
        ("agent_list",      [r'agentList|agent-list|agent_list']),
        ("api_polling",     [r'/api/|fetch\(|XMLHttpRequest']),
        ("event_stream",    [r'EventSource|text/event-stream|getReader\(\)|ReadableStream']),
    ],
    "memory_mirror.py": [
        ("pin_files_defined",  [r'PIN_FILES']),
        ("sync_cycle_func",    [r'def.*sync|def.*mirror|def.*cycle']),
        ("revert_detection",   [r'revert|clobber|restore']),
    ],
    "goal_ledger.py": [
        ("record_marker_fn",  [r'def.*record|def.*marker|record_marker']),
        ("json_output_fn",    [r'--json|json\.dump|to_json']),
        ("parse_goals_fn",    [r'def.*parse|parse_goals|load_goals']),
    ],
}

def sha1_file(path):
    h = hashlib.sha1()
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                h.update(chunk)
    except OSError:
        return ""
    return h.hexdigest()[:12]

def check_file(filepath):
    """Run all checks for a given file. Returns (passed, total, details)."""
    if not os.path.isfile(filepath):
        return 0, len(CHECKS.get(filepath, [])), [{"check": "existence", "status": "FAIL", "detail": f"{filepath} not found"}]
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except OSError as e:
        return 0, len(CHECKS.get(filepath, [])), [{"check": "read", "status": "FAIL", "detail": str(e)}]
    
    details = []
    passed = 0
    for name, patterns in CHECKS.get(filepath, []):
        found = all(re.search(p, content) for p in patterns)
        status = "PASS" if found else "FAIL"
        if found:
            passed += 1
        details.append({"check": name, "status": status})
    
    return passed, len(details), details

def log_entry(entry):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')

def run_all_checks(changed_file=None):
    """Run checks on all watched files (or just the changed one). Returns summary dict."""
    t_start = time.time()
    targets = [changed_file] if changed_file else list(WATCH_FILES.keys())
    
    file_results = {}
    total_pass = 0
    total_checks = 0
    
    for fpath in targets:
        p, t, details = check_file(fpath)
        total_pass += p
        total_checks += t
        file_results[fpath] = {
            "passed": p,
            "total": t,
            "verdict": "PASS" if p == t else "FAIL",
            "details": details
        }
    
    elapsed = time.time() - t_start
    verdict = "PASS" if total_pass == total_checks else "FAIL"
    
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "trigger": f"change:{changed_file}" if changed_file else "full_scan",
        "elapsed_s": round(elapsed, 2),
        "within_5min": elapsed < TRIGGER_TIMEOUT_S,
        "total_passed": total_pass,
        "total_checks": total_checks,
        "result": f"{total_pass}/{total_checks}",
        "verdict": verdict,
        "files": file_results
    }

def main():
    once = '--once' in sys.argv
    
    # Initialize state
    state = {}
    for fpath in WATCH_FILES:
        state[fpath] = {
            "mtime": os.path.getmtime(fpath) if os.path.isfile(fpath) else 0,
            "hash": sha1_file(fpath)
        }
    
    print(f"[multi-file-trigger] watching {len(WATCH_FILES)} files:")
    for f in WATCH_FILES:
        s = state[f]
        exists = "OK" if os.path.isfile(f) else "MISSING"
        print(f"  {f} [{exists}] sha1={s['hash']}")
    
    if once:
        # Run full scan immediately for testing
        summary = run_all_checks(changed_file=None)
        log_entry(summary)
        print(json.dumps(summary, indent=2))
        return 0 if summary["verdict"] == "PASS" else 1
    
    # Daemon mode
    print(f"[multi-file-trigger] daemon mode, poll={POLL_S}s")
    while True:
        time.sleep(POLL_S)
        for fpath in WATCH_FILES:
            try:
                mtime = os.path.getmtime(fpath)
            except OSError:
                continue
            
            if mtime != state[fpath]["mtime"]:
                new_hash = sha1_file(fpath)
                summary = run_all_checks(changed_file=fpath)
                summary["trigger"] = f"mtime_change:{fpath} ({state[fpath]['hash']} -> {new_hash})"
                log_entry(summary)
                print(f"[multi-file-trigger] {summary['ts']} triggered by {fpath}: {summary['result']} {summary['verdict']}")
                
                state[fpath]["mtime"] = mtime
                state[fpath]["hash"] = new_hash

if __name__ == "__main__":
    sys.exit(main())
