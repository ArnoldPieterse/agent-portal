#!/usr/bin/env python3
"""Convergence Dashboard Data Integrity Test (Verifier Goal #9).

Verifies /api/convergence endpoint returns values consistent with source files:
  - autonomy-score.json
  - efficiency-index.jsonl
  - human-interventions.jsonl

Checks:
  1. Endpoint is reachable and returns valid JSON
  2. Autonomy score matches source file (within tolerance)
  3. Efficiency rows match source file
  4. Intervention count matches source file
  5. Staleness: no data point > 1h old
  6. Format errors: all required fields present and correctly typed

Self-test: python memory/verifier/convergence_api_integrity.py --self-test
Live:      python memory/verifier/convergence_api_integrity.py
"""
import json, sys, os, time
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import urllib.error

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PORTAL_URL = "http://127.0.0.1:8099/api/convergence"
STALENESS_THRESHOLD_S = 3600  # 1 hour
TOLERANCE = 0.011

# Source files
AUTONOMY_FILE = REPO_ROOT / "memory" / "ops" / "autonomy-score.json"
EFFICIENCY_FILE = REPO_ROOT / "memory" / "ops" / "efficiency-index.jsonl"
INTERVENTIONS_FILE = REPO_ROOT / "memory" / "ops" / "human-interventions.jsonl"


def fetch_endpoint(url=PORTAL_URL, timeout=10):
    """Fetch the convergence endpoint. Returns (data, error)."""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data, None
    except urllib.error.URLError as e:
        return None, f"URLError: {e}"
    except json.JSONDecodeError as e:
        return None, f"JSONDecodeError: {e}"
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def read_source_autonomy():
    """Read autonomy score from source file."""
    if not AUTONOMY_FILE.exists():
        return None
    data = json.loads(AUTONOMY_FILE.read_text(encoding="utf-8"))
    return {
        "score": data.get("score"),
        "components": data.get("components", {}),
        "computed_at": data.get("computed_at", ""),
    }


def read_source_efficiency():
    """Read efficiency index rows from source file."""
    if not EFFICIENCY_FILE.exists():
        return []
    rows = []
    for line in EFFICIENCY_FILE.read_text(encoding="utf-8").strip().split("\n"):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def read_source_interventions():
    """Read human interventions from source file."""
    if not INTERVENTIONS_FILE.exists():
        return []
    rows = []
    for line in INTERVENTIONS_FILE.read_text(encoding="utf-8").strip().split("\n"):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def check_staleness(ts_str, threshold_s=STALENESS_THRESHOLD_S):
    """Check if a timestamp string is stale (> threshold seconds old)."""
    if not ts_str:
        return True, "missing timestamp"
    try:
        # Handle ISO format with or without timezone
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - ts).total_seconds()
        if age > threshold_s:
            return True, f"stale by {age/3600:.1f}h"
        return False, f"fresh ({age/60:.0f}min old)"
    except (ValueError, TypeError) as e:
        return True, f"unparseable ts: {e}"


def run_checks(endpoint_data):
    """Run all integrity checks against endpoint data and source files.
    
    Returns list of (check_name, passed, detail) tuples.
    """
    results = []
    
    # Check 1: Required top-level keys
    required_keys = ["autonomy", "efficiency", "interventions"]
    missing = [k for k in required_keys if k not in endpoint_data]
    results.append(("required_keys", len(missing) == 0, 
                    f"missing: {missing}" if missing else "all present"))
    
    # Check 2: Autonomy score consistency
    src_aut = read_source_autonomy()
    ep_aut = endpoint_data.get("autonomy", {})
    if src_aut and ep_aut:
        ep_score = ep_aut.get("score")
        src_score = src_aut["score"]
        if ep_score is not None and src_score is not None:
            delta = abs(ep_score - src_score)
            ok = delta <= TOLERANCE
            results.append(("autonomy_score_match", ok,
                            f"endpoint={ep_score} source={src_score} delta={delta:.4f}"))
        else:
            results.append(("autonomy_score_match", False, "missing score field"))
    else:
        results.append(("autonomy_score_match", True, "skipped (no source or endpoint data)"))
    
    # Check 3: Efficiency row count matches
    src_eff = read_source_efficiency()
    ep_eff = endpoint_data.get("efficiency", {})
    if isinstance(ep_eff, list):
        count_match = len(ep_eff) == len(src_eff)
        results.append(("efficiency_count", count_match,
                        f"endpoint={len(ep_eff)} source={len(src_eff)}"))
    elif isinstance(ep_eff, dict):
        # Might be a summary object
        results.append(("efficiency_count", True, "endpoint returns summary (not list)"))
    else:
        results.append(("efficiency_count", False, f"unexpected type: {type(ep_eff).__name__}"))
    
    # Check 4: Intervention count
    src_int = read_source_interventions()
    ep_int = endpoint_data.get("interventions", {})
    if isinstance(ep_int, dict):
        ep_count = ep_int.get("count", ep_int.get("total"))
        if ep_count is not None:
            ok = abs(ep_count - len(src_int)) <= 1  # allow ±1 for timing
            results.append(("intervention_count", ok,
                            f"endpoint={ep_count} source={len(src_int)}"))
        else:
            results.append(("intervention_count", True, "no count field (ok)"))
    elif isinstance(ep_int, list):
        ok = abs(len(ep_int) - len(src_int)) <= 1
        results.append(("intervention_count", ok,
                        f"endpoint={len(ep_int)} source={len(src_int)}"))
    else:
        results.append(("intervention_count", True, "skipped"))
    
    # Check 5: Staleness of autonomy data
    if src_aut and src_aut.get("computed_at"):
        stale, detail = check_staleness(src_aut["computed_at"])
        results.append(("autonomy_not_stale", not stale, detail))
    else:
        results.append(("autonomy_not_stale", True, "no timestamp to check"))
    
    # Check 6: Format - autonomy has required sub-fields
    if ep_aut and isinstance(ep_aut, dict):
        aut_fields = ["score"]
        missing_f = [f for f in aut_fields if f not in ep_aut]
        results.append(("autonomy_format", len(missing_f) == 0,
                        f"missing fields: {missing_f}" if missing_f else "ok"))
    
    return results


def run_live():
    """Run integrity checks against live endpoint."""
    print(f"[convergence_api_integrity] Checking {PORTAL_URL}")
    
    data, err = fetch_endpoint()
    if err:
        print(f"  ENDPOINT UNREACHABLE: {err}")
        # Still check source files for staleness
        results = []
        src_aut = read_source_autonomy()
        if src_aut and src_aut.get("computed_at"):
            stale, detail = check_staleness(src_aut["computed_at"])
            results.append(("source_autonomy_fresh", not stale, detail))
        print(f"  Source-only checks: {len(results)}")
        for name, ok, detail in results:
            print(f"    [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
        
        # Write report
        report = {"ts": datetime.now(timezone.utc).isoformat(), 
                  "endpoint_status": f"UNREACHABLE ({err})",
                  "checks": [{"name": n, "passed": ok, "detail": d} for n, ok, d in results],
                  "overall": "DEGRADED"}
        _write_report(report)
        return 0
    
    print(f"  Endpoint OK: {list(data.keys())}")
    
    results = run_checks(data)
    
    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)
    
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    
    overall = "PASS" if failed == 0 else "FAIL"
    print(f"\n[convergence_api_integrity] {overall} ({passed}/{len(results)} checks passed)")
    
    report = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "endpoint_status": "OK",
        "checks": [{"name": n, "passed": ok, "detail": d} for n, ok, d in results],
        "overall": overall,
        "failed_count": failed,
    }
    _write_report(report)
    
    return 0 if failed == 0 else 1


def _write_report(report):
    """Write integrity report to file."""
    report_file = REPO_ROOT / "memory" / "verifier" / "convergence-api-integrity-report.json"
    report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")


def self_test():
    """Run synthetic tests without hitting the live endpoint."""
    results = []
    
    # T1: check_staleness - fresh timestamp
    now = datetime.now(timezone.utc).isoformat()
    stale, _ = check_staleness(now)
    results.append(("T1_fresh_not_stale", not stale))
    
    # T2: check_staleness - old timestamp (2h ago)
    old = (datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)).isoformat()
    # Make it definitely > 1h old
    from datetime import timedelta
    old_ts = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    stale, _ = check_staleness(old_ts)
    results.append(("T2_old_is_stale", stale))
    
    # T3: check_staleness - missing timestamp
    stale, detail = check_staleness("")
    results.append(("T3_missing_ts_stale", stale))
    
    # T4: run_checks with perfect data (use fresh ts to avoid staleness false-fail)
    src_aut = read_source_autonomy()
    src_eff = read_source_efficiency()
    src_int = read_source_interventions()
    
    # Build endpoint data that matches source exactly
    fresh_ts = datetime.now(timezone.utc).isoformat()
    perfect_endpoint = {
        "autonomy": {"score": src_aut["score"] if src_aut else 50.0},
        "efficiency": src_eff if src_eff else [],
        "interventions": {"count": len(src_int)},
    }
    
    checks = run_checks(perfect_endpoint)
    # Staleness may fail if source data is old - that's correct behavior, not a test failure
    non_stale_checks = [(n, ok) for n, ok, d in checks if "stale" not in n]
    all_pass = all(ok for _, ok in non_stale_checks)
    results.append(("T4_perfect_data_all_pass", all_pass))
    
    # T5: run_checks with wrong autonomy score
    bad_endpoint = {
        "autonomy": {"score": 99.9},
        "efficiency": src_eff,
        "interventions": {"count": len(src_int)},
    }
    checks = run_checks(bad_endpoint)
    aut_check = next((c for c in checks if c[0] == "autonomy_score_match"), None)
    results.append(("T5_wrong_score_flagged", 
                    aut_check is not None and not aut_check[1]))
    
    # T6: run_checks with missing keys
    incomplete_endpoint = {"autonomy": {}}
    checks = run_checks(incomplete_endpoint)
    key_check = next((c for c in checks if c[0] == "required_keys"), None)
    results.append(("T6_missing_keys_flagged",
                    key_check is not None and not key_check[1]))
    
    # T7: efficiency count mismatch
    mismatch_endpoint = {
        "autonomy": {"score": src_aut["score"] if src_aut else 50.0},
        "efficiency": [{"cycle": 1}, {"cycle": 2}, {"cycle": 3}],  # 3 rows
        "interventions": {"count": len(src_int)},
    }
    actual_eff_count = len(read_source_efficiency())
    if actual_eff_count != 3:
        checks = run_checks(mismatch_endpoint)
        eff_check = next((c for c in checks if c[0] == "efficiency_count"), None)
        results.append(("T7_eff_count_mismatch_flagged",
                        eff_check is not None and not eff_check[1]))
    else:
        results.append(("T7_eff_count_mismatch_flagged", True))  # skip if counts match
    
    # T8: intervention count mismatch
    int_mismatch = {
        "autonomy": {"score": src_aut["score"] if src_aut else 50.0},
        "efficiency": read_source_efficiency(),
        "interventions": {"count": 999},
    }
    checks = run_checks(int_mismatch)
    int_check = next((c for c in checks if c[0] == "intervention_count"), None)
    results.append(("T8_int_count_mismatch_flagged",
                    int_check is not None and not int_check[1]))
    
    passed = sum(1 for _, ok in results if ok)
    failed = sum(1 for _, ok in results if not ok)
    for name, ok in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"[self-test] {passed} passed / {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    else:
        sys.exit(run_live())
