"""Productive Pass Gate - verify agent produced file changes or measurement output.

Usage: python memory/orchestrator/productive_pass_gate.py --agent <name> --start-ts <epoch>
       python memory/orchestrator/productive_pass_gate.py --agent <name> --test (synthetic test)

Before marking an auto-loop pass as complete, this gate checks if the agent produced
at least one file change OR measurement output in memory/ since pass start.
If not productive, flags the pass as "wasted" in autoloop.jsonl.

Verification: on a synthetic no-op pass, gate flags productive=false;
on a pass with file write, productive=true; flag appears in JSONL.
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEMORY_DIR = os.path.join(HERE, "memory")
AUTOLOOP_LOG = os.path.join(MEMORY_DIR, "ops", "autoloop.jsonl")


def scan_file_changes_since(start_ts, since_dir=None):
    """Scan memory/ for files modified after start_ts (epoch seconds).
    Returns list of (relpath, mtime) for changed files."""
    if since_dir is None:
        since_dir = MEMORY_DIR
    changes = []
    for root, dirs, files in os.walk(since_dir):
        # Skip .git and hidden dirs
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                mtime = os.path.getmtime(fpath)
                if mtime > start_ts:
                    rel = os.path.relpath(fpath, HERE)
                    changes.append((rel, mtime))
            except OSError:
                pass
    return changes


def check_productive(agent_name, start_ts):
    """Check if agent was productive since start_ts.
    Returns (productive: bool, evidence: list of changed files)."""
    changes = scan_file_changes_since(start_ts)
    # Filter: only count meaningful changes (not just temp/lock files)
    meaningful = [c for c in changes if not any(skip in c[0] for skip in ['.tmp', '.lock', '__pycache__'])]
    productive = len(meaningful) > 0
    return productive, [c[0] for c in meaningful[:10]]


def log_pass(agent_name, start_ts, end_ts=None, productive=None, evidence=None):
    """Append a pass record to autoloop.jsonl."""
    if end_ts is None:
        end_ts = time.time()
    if productive is None or evidence is None:
        productive, evidence = check_productive(agent_name, start_ts)
    
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": agent_name,
        "start_ts": start_ts,
        "end_ts": end_ts,
        "duration_s": round(end_ts - start_ts, 1),
        "productive": productive,
        "evidence_files": evidence[:5],
    }
    
    os.makedirs(os.path.dirname(AUTOLOOP_LOG), exist_ok=True)
    with open(AUTOLOOP_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record) + "\n")
    return record


def run_test():
    """Synthetic test: verify gate works for both productive and non-productive passes."""
    print("=== Productive Pass Gate - Synthetic Test ===")
    results = []
    
    # Test 1: No-op pass (start now, no files changed)
    start_ts = time.time()
    time.sleep(0.1)  # tiny delay to ensure mtime is after start
    productive, evidence = check_productive("test_agent", start_ts)
    t1_pass = not productive and len(evidence) == 0
    results.append(("no_op_flags_wasted", t1_pass, f"productive={productive}, evidence={evidence}"))
    print(f"  Test 1 (no-op -> wasted): {'PASS' if t1_pass else 'FAIL'} - productive={productive}")
    
    # Test 2: Productive pass (write a file, then check)
    start_ts = time.time()
    test_file = os.path.join(MEMORY_DIR, "ops", f"_gate_test_{int(start_ts)}.txt")
    time.sleep(0.1)
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("productivity gate test artifact\n")
    productive, evidence = check_productive("test_agent", start_ts)
    t2_pass = productive and any('_gate_test' in e for e in evidence)
    results.append(("file_write_flags_productive", t2_pass, f"productive={productive}, evidence={evidence[:3]}"))
    print(f"  Test 2 (file write -> productive): {'PASS' if t2_pass else 'FAIL'} - productive={productive}")
    
    # Cleanup test file
    os.remove(test_file)
    
    # Test 3: Log to JSONL
    start_ts = time.time()
    rec = log_pass("test_agent", start_ts, productive=False, evidence=[])
    t3_pass = os.path.exists(AUTOLOOP_LOG) and "productive" in json.loads(open(AUTOLOOP_LOG).readlines()[-1])
    results.append(("jsonl_flag_appears", t3_pass, f"record keys={list(rec.keys())}"))
    print(f"  Test 3 (JSONL flag): {'PASS' if t3_pass else 'FAIL'} - record written")
    
    all_pass = all(r[1] for r in results)
    print(f"\n{'ALL TESTS PASS' if all_pass else 'SOME TESTS FAILED'} ({sum(r[1] for r in results)}/{len(results)})")
    return all_pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Productive Pass Gate")
    parser.add_argument("--agent", required=True, help="Agent name")
    parser.add_argument("--start-ts", type=float, help="Pass start timestamp (epoch)")
    parser.add_argument("--test", action="store_true", help="Run synthetic test")
    args = parser.parse_args()
    
    if args.test:
        sys.exit(0 if run_test() else 1)
    elif args.start_ts:
        productive, evidence = check_productive(args.agent, args.start_ts)
        rec = log_pass(args.agent, args.start_ts, productive=productive, evidence=evidence)
        print(json.dumps(rec, indent=2))
    else:
        parser.print_help()
        sys.exit(1)
