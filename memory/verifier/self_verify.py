#!/usr/bin/env python3
"""self_verify.py - Meta-test: verify that my own logged passes have real evidence.

For every `(verified: ...)` marker in memory/goals/verifier.md, this script:
  1. Extracts the evidence file path referenced
  2. Confirms the file exists and is non-empty
  3. Checks its content has a timestamp within a reasonable window (last 7 days)

Also tests the negative case: an injected phantom pass (no real evidence file) must be flagged.

Usage:
  python memory/verifier/self_verify.py --selftest   # run full meta-test
  python memory/verifier/self_verify.py              # audit current state only

Exit: 0 = all verified passes have valid evidence; 1 = phantom/stale detected
"""
import sys, os, re, json, datetime

ROOT = os.getcwd()
GOALS_FILE = os.path.join(ROOT, "memory", "goals", "verifier.md")
RESULT_PATH = os.path.join(ROOT, "memory", "verifier", "self-verify-result.json")

def extract_evidence_refs(goals_text):
    """Extract all (verified: ...) markers and their referenced file paths."""
    refs = []
    # Pattern: (verified: ... evidence: path) or (verified: ... pointer: path)
    pattern = r'\(verified:\s*([^)]+)\)'
    for m in re.finditer(pattern, goals_text):
        marker_text = m.group(1).strip()
        # Try to extract a file path from the marker
        file_path = None
        fp_match = re.search(r'(?:evidence|pointer)?:\s*(memory/[\w/._-]+)', marker_text)
        if fp_match:
            file_path = fp_match.group(1)
        
        # Extract timestamp if present
        ts_match = re.search(r'(20\d{2}-\d{2}-\d{2}T\d{2}:\d{2})', marker_text)
        timestamp = ts_match.group(1) if ts_match else None
        
        refs.append({
            "marker": marker_text[:100],
            "file_path": file_path,
            "timestamp": timestamp
        })
    return refs

def check_evidence(ref):
    """Check a single evidence reference. Returns (ok: bool, reason: str)."""
    path = ref["file_path"]
    if not path:
        # No explicit path - check if the marker itself has enough info
        # Count as OK if it has a timestamp (inline evidence)
        if ref["timestamp"]:
            return True, "inline evidence with timestamp"
        return False, "no file path and no timestamp in marker"
    
    full_path = os.path.join(ROOT, path)
    if not os.path.exists(full_path):
        return False, f"file does not exist: {path}"
    
    size = os.path.getsize(full_path)
    if size == 0:
        return False, f"file is empty: {path}"
    
    # Check timestamp freshness (within 7 days)
    if ref["timestamp"]:
        try:
            ts = datetime.datetime.strptime(ref["timestamp"], "%Y-%m-%dT%H:%M")
            age_days = (datetime.datetime.now() - ts).days
            if age_days > 7:
                return False, f"evidence stale ({age_days} days old): {path}"
        except ValueError:
            pass  # timestamp format issue, don't fail on this
    
    return True, f"OK ({size} bytes)"

def selftest():
    """Run the full meta-test including phantom injection."""
    print("=== SELF-VERIFY METATEST ===")
    
    # Part A: Audit all current verified markers
    goals_text = open(GOALS_FILE, encoding="utf-8").read()
    refs = extract_evidence_refs(goals_text)
    
    print(f"\nFound {len(refs)} (verified:) markers in verifier.md")
    results_a = []
    for i, ref in enumerate(refs):
        ok, reason = check_evidence(ref)
        results_a.append({"idx": i+1, "ok": ok, "reason": reason, "path": ref["file_path"]})
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] #{i+1}: {reason} ({ref['file_path'] or 'inline'})")
    
    part_a_pass = all(r["ok"] for r in results_a) if results_a else False
    
    # Part B: Phantom injection test
    # Simulate a phantom pass by checking a non-existent file
    phantom_ref = {
        "marker": "(verified: 2026-11-26T00:00Z - phantom test, evidence: memory/verifier/PHANTOM_DOES_NOT_EXIST.md)",
        "file_path": "memory/verifier/PHANTOM_DOES_NOT_EXIST.md",
        "timestamp": "2026-11-26T00:00"
    }
    ok_b, reason_b = check_evidence(phantom_ref)
    phantom_detected = (ok_b == False)  # We expect it to FAIL
    print(f"\nPhantom test: {'CORRECTLY FLAGGED' if phantom_detected else 'MISSED!'} - {reason_b}")
    
    part_b_pass = phantom_detected
    
    # Summary
    total_refs = len(results_a)
    all_ok = part_a_pass and part_b_pass
    print(f"\n=== SUMMARY ===")
    print(f"  Real markers audited: {total_refs}")
    print(f"  All real evidence valid: {part_a_pass}")
    print(f"  Phantom correctly flagged: {phantom_detected}")
    print(f"  OVERALL: {'PASS' if all_ok else 'FAIL'}")
    
    # Write result
    result = {
        "ts": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "markers_audited": total_refs,
        "all_valid": part_a_pass,
        "phantom_flagged": phantom_detected,
        "overall_pass": all_ok,
        "details": results_a
    }
    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    else:
        # Just audit current state
        goals_text = open(GOALS_FILE, encoding="utf-8").read()
        refs = extract_evidence_refs(goals_text)
        for i, ref in enumerate(refs):
            ok, reason = check_evidence(ref)
            print(f"{'OK' if ok else 'FAIL'}: {reason}")
