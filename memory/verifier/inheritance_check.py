"""Cross-Cycle Inheritance Validator.

Validates auto-generated v2 goals from the Orchestrator's inheritance engine:
  1. NOT in closed_topics (no re-issuing of already-completed work)
  2. Has valid verification criteria (non-empty, specific, automatable)
  3. References the v1 goal correctly (source file exists, goal number present)

Usage:
  python memory/verifier/inheritance_check.py          # live validation
  python memory/verifier/inheritance_check.py --selftest  # 5 valid + 5 invalid

Output: memory/verifier/inheritance_report.json
"""
import json, os, re, sys, hashlib
from pathlib import Path
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
CLOSED_TOPICS = os.path.join(BASE, "memory", "goals", "closed_topics.json")
INHERITED = os.path.join(BASE, "memory", "orchestrator", "inherited-goals.json")
REPORT = os.path.join(HERE, "inheritance_report.json")


def compute_sig(text: str) -> str:
    return hashlib.sha1(text.lower().strip().encode()).hexdigest()[:16]


def load_closed_topics():
    """Load closed topics and build sig set + text list."""
    if not os.path.exists(CLOSED_TOPICS):
        return set(), []
    with open(CLOSED_TOPICS, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        entries = data.get("topics", [])
    else:
        entries = data
    sigs = set()
    texts = []
    for e in entries:
        if isinstance(e, dict):
            sigs.add(e.get("sig", ""))
            t = e.get("text", "")
            sigs.add(compute_sig(t))
            texts.append(t)
        else:
            t = str(e)
            sigs.add(compute_sig(t))
            texts.append(t)
    return sigs, texts


def check_not_in_closed(goal: dict) -> tuple:
    """Check that goal is NOT in closed_topics. Returns (pass, reason)."""
    title = goal.get("title", "")
    body = goal.get("body", "")
    full = f"{title} {body}"
    sig = compute_sig(full)
    
    sigs, texts = load_closed_topics()
    
    # Direct sig match
    if sig in sigs:
        return False, f"sig {sig} found in closed_topics"
    
    # Check title against closed topic titles (fuzzy: first 50 chars)
    title_50 = title[:50].lower().strip()
    for t in texts:
        if title_50 and title_50 in t.lower():
            return False, f"title '{title[:40]}...' matches closed topic"
    
    return True, "not found in closed_topics"


def check_verification_criteria(goal: dict) -> tuple:
    """Check that goal has valid verification criteria. Returns (pass, reason)."""
    body = goal.get("body", "")
    title = goal.get("title", "")
    full = f"{title} {body}"
    
    # Must contain 'Verified:' or 'verified:' marker
    if not re.search(r'\bverified?:', full, re.I):
        return False, "no 'Verified:' criteria found"
    
    # Extract the criteria text
    m = re.search(r'[Vv]erified?:\s*(.+?)(?:\n|$)', full)
    if not m:
        return False, "'Verified:' marker present but empty criteria"
    
    criteria = m.group(1).strip()
    
    # Must be non-trivial (>20 chars)
    if len(criteria) < 20:
        return False, f"verification criteria too short ({len(criteria)} chars): '{criteria}'"
    
    # Should reference something automatable (file path, command, or measurable quantity)
    auto_markers = re.search(r'(memory/|\.py|\.json|\.md|python |pass|fail|\d+)', criteria)
    if not auto_markers:
        return False, "verification criteria lack automatable reference (no file/cmd/number)"
    
    return True, f"valid criteria ({len(criteria)} chars, automatable)"


def check_v1_reference(goal: dict) -> tuple:
    """Check that goal references v1 correctly. Returns (pass, reason)."""
    body = goal.get("body", "")
    title = goal.get("title", "")
    full = f"{title} {body}"
    
    # Must reference a source file (memory/ path) or goal number
    file_ref = re.search(r'(?:inherited?\s+from|source:|file:?)\s*([\w/\-\.]+\.md)', full, re.I)
    goal_num_ref = re.search(r'goal\s*(\d+)', full, re.I)
    
    if not file_ref and not goal_num_ref:
        return False, "no v1 reference found (need source file or goal number)"
    
    # If a file ref is present, check it exists
    if file_ref:
        ref_path = file_ref.group(1)
        full_path = os.path.join(BASE, ref_path)
        if not os.path.exists(full_path):
            return False, f"referenced source file does not exist: {ref_path}"
    
    # Must mention inheritance context
    if not re.search(r'(inherit|v\d+|continuation|prior|baseline)', full, re.I):
        return False, "no inheritance context marker (inherit/v1/continuation/prior/baseline)"
    
    return True, f"valid v1 ref ({'file:' + file_ref.group(1) if file_ref else 'goal#' + goal_num_ref.group(1)})"


def validate_goal(goal: dict) -> dict:
    """Run all 3 checks on a goal. Returns result dict."""
    r1 = check_not_in_closed(goal)
    r2 = check_verification_criteria(goal)
    r3 = check_v1_reference(goal)
    
    passed = all(r[0] for r in [r1, r2, r3])
    return {
        "title": goal.get("title", "")[:80],
        "passed": passed,
        "checks": {
            "not_in_closed": {"pass": r1[0], "reason": r1[1]},
            "verification_criteria": {"pass": r2[0], "reason": r2[1]},
            "v1_reference": {"pass": r3[0], "reason": r3[1]},
        }
    }


def run_selftest() -> int:
    """5 valid + 5 invalid test cases. Returns exit code (0=pass, 1=fail)."""
    # Build a fake closed_topics context for testing
    # We'll use the real closed_topics.json if it exists, plus synthetic entries
    
    # --- 5 VALID goals ---
    valid_goals = [
        {
            "title": "Convergence Metric Validation (v2)",
            "body": "Inherited from: memory/goals/archive/verifier-2026-11-24-cycle17.md goal 1. Context: v1 established baseline formula check; v2 extends to multi-agent cross-validation. Verified: all metrics recompute within tolerance of source data; python memory/verifier/convergence_metric_validation.py exits 0."
        },
        {
            "title": "Fleet Recovery SLA Test (v2)",
            "body": "Inherit from: memory/goals/archive/mechanic-2026-11-23-cycle8.md goal 3. Prior completion established baseline; this continuation extends scope to cascade scenarios. Verified: 10 simulated incidents all within SLA (detection<300s, single<1800s, cascade<7200s); python memory/verifier/fleet_recovery_sla_test.py self-test 6/6."
        },
        {
            "title": "Cycle Duration Forecast Widget (v2)",
            "body": "Inherited from: memory/goals/archive/designer-2026-11-24-cycle17.md goal 2. Baseline v1 rendered chart; v2 adds prediction gap highlighting. Verified: widget renders actual vs predicted for last 5 cycles; gap >20% highlighted in red; python -c test passes."
        },
        {
            "title": "Seat Health Trend Monitor (v2)",
            "body": "Inherit from: memory/goals/archive/mechanic-2026-11-23-cycle8.md goal 5. Prior v1 tracked binary up/down; v2 adds latency trend detection. Verified: p95 latency trend computed over 3+ probes; degrading state triggered at >50% increase; python memory/verifier/steady_state_transition_test.py passes."
        },
        {
            "title": "Goal Complexity Scorer Regression (v2)",
            "body": "Inherited from: memory/goals/archive/orchestrator-2026-11-24-cycle17.md goal 4. v1 scored 20 goals; v2 extends to 50 and adds cross-validation with actual completion times. Verified: correlation r>0.7 on expanded set; python memory/verifier/complexity_scorer_regression.py self-test 10/10."
        },
    ]
    
    # --- 5 INVALID goals ---
    invalid_goals = [
        {
            "title": "Orphan Remediation Sweep",
            "body": "Run a full scan of memory/ tree: find all files not referenced by any INDEX.md or pointer line. Verified: 0 orphans remain after sweep; python script exits 0.",
            # INVALID: this exact title is in closed_topics (first entry we saw)
        },
        {
            "title": "Knowledge Graph v3 (Temporal + Typed)",
            "body": "Extend cycle-7 graph: add edge types. Verified: 5 edge types present.",
            # INVALID: this title matches a closed topic
        },
        {
            "title": "Some New Goal (v2)",
            "body": "Inherited from: memory/goals/archive/somefile.md goal 9. Context: prior work done. Verified: it works.",
            # INVALID: verification criteria too short / not automatable
        },
        {
            "title": "Broken Reference Goal (v2)",
            "body": "Inherited from: memory/goals/archive/nonexistent-file-xyz.md goal 5. Prior baseline established. Verified: comprehensive test suite passes with 10/10 cases and python command exits cleanly.",
            # INVALID: referenced file does not exist
        },
        {
            "title": "No Inheritance Context (v2)",
            "body": "This goal is about doing something new. Verified: the deliverable exists at memory/verifier/output.json and passes 5/5 self-test cases with python command.",
            # INVALID: no inheritance context marker
        },
    ]
    
    results = []
    all_pass = True
    
    print("=== SELF-TEST: Inheritance Validator ===")
    print(f"\n--- 5 VALID goals (expect PASS) ---")
    for i, g in enumerate(valid_goals, 1):
        r = validate_goal(g)
        status = "PASS" if r["passed"] else "FAIL"
        if not r["passed"]:
            all_pass = False
        results.append({"expected": "valid", "actual": "pass" if r["passed"] else "fail", "title": g["title"][:50], "checks": r["checks"]})
        print(f"  V{i} [{status}] {g['title'][:60]}")
        if not r["passed"]:
            for ck, cv in r["checks"].items():
                if not cv["pass"]:
                    print(f"       FAIL: {ck}: {cv['reason']}")
    
    print(f"\n--- 5 INVALID goals (expect FAIL) ---")
    for i, g in enumerate(invalid_goals, 1):
        r = validate_goal(g)
        status = "PASS" if not r["passed"] else "FAIL"
        if r["passed"]:
            all_pass = False
        results.append({"expected": "invalid", "actual": "pass" if r["passed"] else "fail", "title": g["title"][:50], "checks": r["checks"]})
        print(f"  I{i} [{status}] {g['title'][:60]}")
        if r["passed"]:
            print(f"       UNEXPECTED PASS - should have been rejected")
    
    total = len(results)
    correct = sum(1 for r in results if (r["expected"] == "valid" and r["actual"] == "pass") or (r["expected"] == "invalid" and r["actual"] == "fail"))
    print(f"\n=== RESULT: {correct}/{total} correctly classified ===")
    
    # Write report
    report = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "mode": "selftest",
        "total": total,
        "correct": correct,
        "all_pass": all_pass,
        "results": results,
    }
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Report: {os.path.relpath(REPORT)}")
    
    return 0 if all_pass else 1


def run_live() -> int:
    """Validate actual inherited-goals.json. Returns exit code."""
    print("=== LIVE: Inheritance Validator ===")
    
    if not os.path.exists(INHERITED):
        print(f"INHERITED FILE MISSING: {os.path.relpath(INHERITED)}")
        report = {"ts": datetime.now(timezone.utc).isoformat(), "mode": "live", "status": "NO_DATA", "goals_found": 0}
        with open(REPORT, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print("No inherited goals to validate. Engine produces empty output.")
        return 0
    
    with open(INHERITED, encoding="utf-8") as f:
        goals = json.load(f)
    
    if not goals:
        print("inherited-goals.json is EMPTY (engine produced no v2 goals).")
        report = {"ts": datetime.now(timezone.utc).isoformat(), "mode": "live", "status": "EMPTY", "goals_found": 0}
        with open(REPORT, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        return 0
    
    results = []
    passed = 0
    for i, g in enumerate(goals, 1):
        r = validate_goal(g)
        results.append(r)
        if r["passed"]:
            passed += 1
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {g.get('title', '?')[:60]}")
        for ck, cv in r["checks"].items():
            if not cv["pass"]:
                print(f"       - {ck}: {cv['reason']}")
    
    report = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "mode": "live",
        "status": "OK",
        "goals_found": len(goals),
        "goals_passed": passed,
        "goals_failed": len(goals) - passed,
        "results": results,
    }
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nRESULT: {passed}/{len(goals)} valid")
    return 0 if passed == len(goals) else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(run_selftest())
    else:
        sys.exit(run_live())
