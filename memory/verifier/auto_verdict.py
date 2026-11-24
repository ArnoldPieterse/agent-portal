#!/usr/bin/env python3
"""
auto_verdict.py - Verifier Auto-Verdict Readiness Assessment (Verifier goal #8)

For each verification script in the verifier lane, score "auto-verdict readiness"
(0-1): can it run unattended and produce an unambiguous pass/fail without
human interpretation?

Scoring criteria:
  * Exit code mapping: does exit 0 = PASS, non-zero = FAIL? (0.3)
  * Unambiguous output: does stdout contain a clear "PASS"/"FAIL" or equivalent? (0.3)
  * No manual interpretation: no interactive prompts, no "review manually" steps? (0.2)
  * Self-contained: can run without external services (or gracefully degrades)? (0.2)

Verified: all current scripts scored; any scoring < 0.8 is listed with specific gaps.
"""

import argparse
import importlib.util
import inspect
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# Scripts to assess (verifier lane .py files that are verification scripts)
VERIFIER_SCRIPTS = [
    "decision_audit.py",
    "failover_verify.py",
    "heal_fp_rate.py",
    "safety_boundary.py",
    "recovery_trend.py",
    "state_consistency.py",
    "convergence_oscillation.py",
    "autonomy_pr_tracker.py",
    "budget_compliance.py",
    "cycle_quality.py",
]


def score_exit_code_mapping(source: str) -> tuple:
    """Score whether the script has clear exit code mapping. Returns (score, detail)."""
    # Look for sys.exit(0) and sys.exit(1) patterns
    has_exit_0 = re.search(r"sys\.exit\(0\)", source) or re.search(r"return 0", source)
    has_nonzero_exit = re.search(r"sys\.exit\((1|2|[a-z_]+)\)", source) or re.search(r"return 1", source)
    
    # Check for conditional exit (pass/fail based on results)
    has_conditional = re.search(r"(if.*(passed|success|ok).*:.*sys\.exit\(0\))|(else.*:.*sys\.exit\(1\))", source, re.DOTALL)
    
    score = 0.0
    if has_exit_0:
        score += 0.15
    if has_nonzero_exit:
        score += 0.10
    if has_conditional:
        score += 0.05
    
    detail = "exit-code mapping present" if score >= 0.2 else "missing or ambiguous exit codes"
    return min(score, 0.3), detail


def score_unambiguous_output(source: str) -> tuple:
    """Score whether output is unambiguous (PASS/FAIL keywords). Returns (score, detail)."""
    has_pass = re.search(r"print\(.*PASS", source) or re.search(r'"PASS"', source)
    has_fail = re.search(r"print\(.*FAIL", source) or re.search(r'"FAIL"', source)
    has_summary = re.search(r"(SUMMARY|RESULT|VERDICT)", source, re.IGNORECASE)
    has_json_output = re.search(r"json\.dump", source)
    
    score = 0.0
    if has_pass:
        score += 0.10
    if has_fail:
        score += 0.10
    if has_summary:
        score += 0.05
    if has_json_output:
        score += 0.05
    
    detail = "unambiguous PASS/FAIL output" if score >= 0.2 else "output may require interpretation"
    return min(score, 0.3), detail


def score_no_manual_interpretation(source: str) -> tuple:
    """Score whether script requires no manual steps. Returns (score, detail)."""
    has_input = re.search(r"input\(.*\)", source) and not re.search(r"#.*input", source)
    has_review_note = re.search(r"(review manually|human review|manual check|needs attention)", source, re.IGNORECASE)
    has_interactive = re.search(r"(getpass|select|choose option)", source, re.IGNORECASE)
    
    score = 0.2  # Base: assume no manual steps
    if has_input:
        score -= 0.10
    if has_review_note:
        score -= 0.05
    if has_interactive:
        score -= 0.10
    
    detail = "no manual interpretation needed" if score >= 0.15 else "may require human review"
    return max(min(score, 0.2), 0.0), detail


def score_self_contained(source: str) -> tuple:
    """Score whether script can run without external services or degrades gracefully. Returns (score, detail)."""
    has_try_except = re.search(r"try\s*:", source) and re.search(r"(except|finally)", source)
    has_network = re.search(r"(urllib|requests\.get|socket|http://)", source)
    has_graceful_degradation = re.search(r"(unavailable|skipped|degraded|fallback|graceful)", source, re.IGNORECASE)
    
    score = 0.1
    if has_try_except:
        score += 0.05
    if has_network and has_graceful_degradation:
        score += 0.05  # Uses network but degrades gracefully
    elif not has_network:
        score += 0.05  # No network needed
    
    detail = "self-contained or graceful degradation" if score >= 0.15 else "may require external services"
    return min(score, 0.2), detail


def assess_script(script_path: Path) -> dict:
    """Assess a single script for auto-verdict readiness."""
    result = {
        "script": str(script_path),
        "exists": script_path.exists(),
        "total_score": 0.0,
        "components": {},
        "gaps": [],
    }
    
    if not script_path.exists():
        result["gaps"].append("Script file does not exist")
        return result
    
    try:
        source = script_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        result["gaps"].append(f"Cannot read file: {e}")
        return result
    
    # Score each component
    ec_score, ec_detail = score_exit_code_mapping(source)
    out_score, out_detail = score_unambiguous_output(source)
    manual_score, manual_detail = score_no_manual_interpretation(source)
    sc_score, sc_detail = score_self_contained(source)
    
    result["components"] = {
        "exit_code_mapping": {"score": ec_score, "max": 0.3, "detail": ec_detail},
        "unambiguous_output": {"score": out_score, "max": 0.3, "detail": out_detail},
        "no_manual_interpretation": {"score": manual_score, "max": 0.2, "detail": manual_detail},
        "self_contained": {"score": sc_score, "max": 0.2, "detail": sc_detail},
    }
    
    result["total_score"] = round(ec_score + out_score + manual_score + sc_score, 3)
    
    # Identify gaps for low-scoring components
    threshold = 0.8
    if result["total_score"] < threshold:
        if ec_score < 0.2:
            result["gaps"].append("Exit code mapping incomplete - add sys.exit(0)/sys.exit(1) based on verdict")
        if out_score < 0.2:
            result["gaps"].append("Output not unambiguous - add explicit PASS/FAIL summary line")
        if manual_score < 0.15:
            result["gaps"].append("May require manual interpretation - remove interactive prompts or 'review' notes")
        if sc_score < 0.15:
            result["gaps"].append("External dependency without graceful degradation - add try/except fallback")
    
    return result


def run_assessment(base_dir="."):
    """Assess all verifier scripts."""
    base = Path(base_dir) / "memory" / "verifier"
    results = []
    for script_name in VERIFIER_SCRIPTS:
        sp = base / script_name
        results.append(assess_script(sp))
    
    # Summary
    total = len(results)
    ready = [r for r in results if r["total_score"] >= 0.8]
    not_ready = [r for r in results if r["total_score"] < 0.8]
    avg_score = sum(r["total_score"] for r in results) / total if total else 0
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scripts_assessed": total,
        "ready_count": len(ready),
        "not_ready_count": len(not_ready),
        "average_score": round(avg_score, 3),
        "results": results,
        "needs_refinement": [
            {"script": r["script"], "score": r["total_score"], "gaps": r["gaps"]}
            for r in not_ready
        ],
    }


def self_test():
    """Self-test with synthetic scripts."""
    print("=" * 64)
    print("auto_verdict.py - SELF-TEST")
    print("=" * 64)
    
    import tempfile, shutil
    
    results = []
    tmpdir = tempfile.mkdtemp(prefix="av_test_")
    
    # T1: Perfect script scores >= 0.8
    print("\n[T1] Perfect script scores >= 0.8...", end=" ")
    perfect_src = """
import sys, json
def main():
    passed = True
    if passed:
        print("SUMMARY: PASS")
        print(json.dumps({"result": "PASS"}))
        sys.exit(0)
    else:
        print("SUMMARY: FAIL")
        sys.exit(1)
if __name__ == "__main__":
    main()
"""
    p = Path(tmpdir) / "perfect.py"
    p.write_text(perfect_src)
    r1 = assess_script(p)
    t1_pass = r1["total_score"] >= 0.8
    print(f"PASS (score={r1['total_score']})" if t1_pass else f"FAIL (score={r1['total_score']}, gaps={r1['gaps']})")
    results.append(("T1_perfect_script", t1_pass))
    
    # T2: Poor script scores < 0.8 and has gaps listed
    print("[T2] Poor script scores < 0.8 with gaps...", end=" ")
    poor_src = """
import input
def main():
    x = input("Enter value: ")
    if x == "ok":
        print("maybe pass?")
    else:
        print("review manually")
"""
    p2 = Path(tmpdir) / "poor.py"
    p2.write_text(poor_src)
    r2 = assess_script(p2)
    t2_pass = r2["total_score"] < 0.8 and len(r2["gaps"]) > 0
    print(f"PASS (score={r2['total_score']}, gaps={len(r2['gaps'])})" if t2_pass else f"FAIL (score={r2['total_score']}, gaps={r2['gaps']})")
    results.append(("T2_poor_script_gaps", t2_pass))
    
    # T3: Missing file handled gracefully
    print("[T3] Missing file handled...", end=" ")
    r3 = assess_script(Path(tmpdir) / "nonexistent.py")
    t3_pass = not r3["exists"] and len(r3["gaps"]) > 0
    print("PASS" if t3_pass else f"FAIL ({r3})")
    results.append(("T3_missing_file", t3_pass))
    
    # T4: Report structure complete
    print("[T4] Report structure...", end=" ")
    report = run_assessment(base_dir=tmpdir)
    required = ["timestamp", "scripts_assessed", "ready_count", "not_ready_count", "average_score", "results", "needs_refinement"]
    t4_pass = all(f in report for f in required)
    print("PASS" if t4_pass else "FAIL")
    results.append(("T4_report_structure", t4_pass))
    
    # T5: Network script with graceful degradation scores well
    print("[T5] Network+graceful degradation...", end=" ")
    net_src = """
import sys, json, urllib.request
def main():
    try:
        resp = urllib.request.urlopen("http://127.0.0.1:8099/api/health", timeout=5)
        data = json.loads(resp.read())
    except Exception:
        print("unavailable - check skipped (degraded mode)")
        data = {"status": "unknown"}
    passed = data.get("status") != "error"
    if passed:
        print("SUMMARY: PASS")
        sys.exit(0)
    else:
        print("SUMMARY: FAIL")
        sys.exit(1)
if __name__ == "__main__":
    main()
"""
    p5 = Path(tmpdir) / "net.py"
    p5.write_text(net_src)
    r5 = assess_script(p5)
    t5_pass = r5["total_score"] >= 0.7
    print(f"PASS (score={r5['total_score']})" if t5_pass else f"FAIL (score={r5['total_score']})")
    results.append(("T5_network_graceful", t5_pass))
    
    # T6: All real verifier scripts assessed without crash
    print("[T6] Real scripts assessed...", end=" ")
    try:
        real_report = run_assessment()
        t6_pass = real_report["scripts_assessed"] > 0 and all("total_score" in r for r in real_report["results"])
        print(f"PASS ({real_report['scripts_assessed']} scripts, avg={real_report['average_score']})")
    except Exception as e:
        t6_pass = False
        print(f"FAIL ({e})")
    results.append(("T6_real_scripts", t6_pass))
    
    # Summary
    passed = sum(1 for _, p in results if p)
    total = len(results)
    shutil.rmtree(tmpdir, ignore_errors=True)
    
    print("\n" + "=" * 64)
    print(f"SUMMARY: {passed}/{total} self-tests passed")
    
    # Write report
    out_path = "memory/verifier/auto_verdict_results.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "self_test": {"passed": passed, "total": total},
            "assessment": real_report if t6_pass else None,
        }, f, indent=2)
    print(f"Report: {out_path}")
    
    all_pass = passed == total
    print(f"\nSELF-TEST {'PASSED' if all_pass else 'FAILED'} - {passed}/{total} tests green")
    return 0 if all_pass else 1


def main():
    parser = argparse.ArgumentParser(description="Auto-Verdict Readiness Assessment")
    parser.add_argument("--self-test", action="store_true", help="Run self-test")
    parser.add_argument("--assess", action="store_true", help="Assess all verifier scripts")
    args = parser.parse_args()
    
    if args.self_test:
        sys.exit(self_test())
    elif args.assess:
        report = run_assessment()
        print(json.dumps(report, indent=2))
        out_path = "memory/verifier/auto_verdict_report.json"
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport: {out_path}")
        sys.exit(0 if report["not_ready_count"] == 0 else 1)
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
