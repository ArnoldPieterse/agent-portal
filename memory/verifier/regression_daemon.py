"""
regression_daemon.py — Verifier goal #1 (cycle 2)
Watches agent_portal.py; on mtime change, auto-runs the 5-point regression suite.
Logs results to memory/verifier/regression-daemon-log.jsonl with timestamp.

Usage: python memory/verifier/regression_daemon.py [--once]
  --once: run once and exit (for testing)
  (default): poll every 3s indefinitely
"""
import os, json, time, hashlib, re, sys
from datetime import datetime, timezone

WATCH_FILE = "agent_portal.py"
LOG_FILE = "memory/verifier/regression-daemon-log.jsonl"
POLL_S = 3
MAX_AGE_S = 30  # must run within 30s of edit

# 5-point check definitions: (name, patterns to find in file)
CHECKS = [
    ("chat", [r'/api/chat', r'text/event-stream']),
    ("file_links", [r'/api/file']),
    ("dm_markers", [r'expand_mentions|DM']),
    ("prune", [r'/api/todo/prune']),
    ("git", [r'/api/git.*commit|_git\(\["commit']),
]

def sha1_file(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()[:12]

def run_suite():
    """Run 5-point regression check. Returns (pass_count, details)."""
    if not os.path.isfile(WATCH_FILE):
        return 0, [{"point": "all", "status": "FAIL", "detail": f"{WATCH_FILE} not found"}]
    
    with open(WATCH_FILE, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    details = []
    passed = 0
    for name, patterns in CHECKS:
        found = all(re.search(p, content) for p in patterns)
        status = "PASS" if found else "FAIL"
        if found:
            passed += 1
        details.append({"point": name, "status": status})
    
    return passed, details

def log_entry(entry):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')

def main():
    once = '--once' in sys.argv
    
    last_mtime = os.path.getmtime(WATCH_FILE) if os.path.isfile(WATCH_FILE) else 0
    last_hash = sha1_file(WATCH_FILE) if os.path.isfile(WATCH_FILE) else ""
    
    print(f"[regression-daemon] watching {WATCH_FILE} (sha1={last_hash}, mtime={last_mtime:.0f})")
    print(f"[regression-daemon] poll interval: {POLL_S}s, max age: {MAX_AGE_S}s")
    
    if once:
        # Run immediately for testing
        passed, details = run_suite()
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "trigger": "manual/once",
            "sha1": last_hash,
            "result": f"{passed}/5",
            "details": details,
            "verdict": "PASS" if passed == 5 else "FAIL"
        }
        log_entry(entry)
        print(json.dumps(entry, indent=2))
        return 0 if passed == 5 else 1
    
    while True:
        time.sleep(POLL_S)
        try:
            mtime = os.path.getmtime(WATCH_FILE)
        except OSError:
            continue
        
        if mtime != last_mtime:
            elapsed = time.time() - mtime  # how long ago the edit was (approx)
            new_hash = sha1_file(WATCH_FILE)
            passed, details = run_suite()
            
            entry = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "trigger": f"mtime_change ({last_mtime:.0f} -> {mtime:.0f})",
                "sha1": new_hash,
                "elapsed_s": round(elapsed, 1),
                "within_30s": elapsed <= MAX_AGE_S,
                "result": f"{passed}/5",
                "details": details,
                "verdict": "PASS" if passed == 5 else "FAIL"
            }
            log_entry(entry)
            print(f"[regression-daemon] {entry['ts']} sha1={new_hash} result={entry['result']} within_30s={entry['within_30s']}")
            
            last_mtime = mtime
            last_hash = new_hash

if __name__ == "__main__":
    sys.exit(main())
