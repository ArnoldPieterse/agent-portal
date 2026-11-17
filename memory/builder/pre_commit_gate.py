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

# --- Performance budget config ---
PERF_BUDGET_BYTES = 120 * 1024  # 120KB total minified CSS+JS in ui/
UI_DIR = "ui"

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

def _minify_css(text):
    """Simple CSS minification: strip comments, collapse whitespace."""
    import re
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s*([{}:;,>])\s*', r'\1', text)
    return text.strip()

def _minify_js(text):
    """Simple JS minification: strip comments, collapse whitespace."""
    import re
    # Remove block comments (but not URLs like http://)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    # Remove single-line comments (naive - may miss edge cases but good enough for budget check)
    text = re.sub(r'(?<!:)//[^\n]*', '', text)
    # Collapse whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()

def check_perf_budget():
    """Check that ui/ CSS+JS bundle (minified) stays under PERF_BUDGET_BYTES.
    Returns (passed: bool, report: str)."""
    import re
    if not os.path.isdir(UI_DIR):
        return False, f"DIR NOT FOUND: {UI_DIR}/"
    
    files = []
    for fname in sorted(os.listdir(UI_DIR)):
        if fname.endswith(('.css', '.js')):
            fpath = os.path.join(UI_DIR, fname)
            if os.path.isfile(fpath):
                files.append(fpath)
    
    if not files:
        return False, f"NO CSS/JS FILES in {UI_DIR}/"
    
    total_minified = 0
    per_file = []
    for fpath in files:
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            raw = f.read()
        if fpath.endswith('.css'):
            minified = _minify_css(raw)
        else:
            minified = _minify_js(raw)
        msize = len(minified.encode('utf-8'))
        total_minified += msize
        per_file.append((fpath, len(raw.encode('utf-8')), msize))
    
    passed = total_minified <= PERF_BUDGET_BYTES
    overage = total_minified - PERF_BUDGET_BYTES
    budget_pct = (total_minified / PERF_BUDGET_BYTES) * 100
    
    # Find largest contributor
    per_file.sort(key=lambda x: x[2], reverse=True)
    top_file, top_raw, top_min = per_file[0]
    
    lines = []
    lines.append(f"  Bundle: {total_minified:,} / {PERF_BUDGET_BYTES:,} bytes minified ({budget_pct:.1f}% of budget)")
    for fpath, raw_sz, min_sz in per_file:
        pct_of_total = (min_sz / total_minified) * 100 if total_minified else 0
        lines.append(f"    {fpath}: {raw_sz:,} raw -> {min_sz:,} min ({pct_of_total:.0f}% of bundle)")
    
    if not passed:
        lines.append(f"  OVER BUDGET by {overage:,} bytes. Largest file: {top_file} ({top_min:,}B minified)")
    
    return passed, "\n".join(lines)


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
    
    # Performance budget check
    perf_passed, perf_report = check_perf_budget()
    perf_status = "GREEN" if perf_passed else "RED"
    results.append(("perf-budget", perf_passed, "OK" if perf_passed else "OVER BUDGET"))
    print(f"  [{perf_status}] perf-budget          {perf_report.splitlines()[0]}")
    if verbose or not perf_passed:
        for line in perf_report.splitlines()[1:]:
            print(f"                 {line}")
    
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
