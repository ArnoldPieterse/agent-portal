"""pre_commit_gate.py - CI gate for portal edits.
Runs ALL four test suites; exits 1 (block) if ANY fails, 0 (pass) if all green.
Usage: python memory/builder/pre_commit_gate.py [--verbose]
"""
import sys, os, subprocess, time, json

SUITES = [
    ("path-safety", "memory/builder/upload_path_safety.py"),
    ("prune-regression", "memory/builder/prune_regression.py"),
    ("truncation-detect", "verifier/truncation_detect_test.py"),
    ("playbook-tests", "builder/playbook_tests.py"),
]

def run_suite(name, path):
    if not os.path.exists(path):
        return False, f"NOT FOUND: {path}"
    start = time.time()
    try:
        r = subprocess.run(
            [sys.executable, path],
            capture_output=True, text=True, timeout=30
        )
        elapsed = time.time() - start
        if r.returncode == 0:
            return True, f"PASS ({elapsed:.1f}s)"
        else:
            err_tail = (r.stderr or r.stdout).strip().split("\n")[-3:]
            return False, f"FAIL ({elapsed:.1f}s): {' | '.join(err_tail)}"
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT (>30s)"
    except Exception as e:
        return False, f"ERROR: {e}"

def main():
    verbose = "--verbose" in sys.argv
    print("=== PRE-COMMIT GATE ===")
    try:
        size = os.path.getsize("agent_portal.py")
        print(f"Target: agent_portal.py ({size:,} bytes)")
    except FileNotFoundError:
        print("Target: agent_portal.py (NOT FOUND - gate FAILS)")
        sys.exit(1)
    print()
    
    results = []
    for name, path in SUITES:
        passed, detail = run_suite(name, path)
        status = "GREEN" if passed else "RED"
        results.append((name, passed, detail))
        print(f"  [{status}] {name:20s} {detail}")
    
    green = sum(1 for _, p, _ in results if p)
    total = len(results)
    print()
    print(f"=== RESULT: {green}/{total} GREEN ===")
    
    if verbose and green < total:
        print("\nFailing suites:")
        for name, passed, detail in results:
            if not passed:
                print(f"  - {name}: {detail}")
    
    sys.exit(0 if green == total else 1)

if __name__ == "__main__":
    main()
