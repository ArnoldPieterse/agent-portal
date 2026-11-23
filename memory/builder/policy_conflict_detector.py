"""
Policy Conflict Detector
========================
Finds overlapping rules with different/contradictory actions in remediation policies.

Usage:
  python memory/builder/policy_conflict_detector.py --selftest
  python memory/builder/policy_conflict_detector.py --check [policy_file]
  python memory/builder/policy_conflict_detector.py --report
"""
import json, sys
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent.parent.parent
DEFAULT_POLICY = BASE / "memory" / "ops" / "remediation-policy.json"
REPORT_FILE = BASE / "memory" / "builder" / "policy-conflicts-report.json"


def load_policy(path=None):
    p = Path(path) if path else DEFAULT_POLICY
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def conditions_overlap(c1, c2):
    """Check if two condition dicts could match the same state simultaneously."""
    if not c1 or not c2:
        return False
    f1, f2 = c1.get("field", ""), c2.get("field", "")
    v1, v2 = c1.get("value"), c2.get("value")
    op1, op2 = c1.get("op", ""), c2.get("op", "")

    # Different fields: check if they're in the same "domain" (prefix match)
    prefix1 = f1.split(".")[0] if "." in f1 else f1
    prefix2 = f2.split(".")[0] if "." in f2 else f2
    if prefix1 != prefix2:
        return False

    # Same field or same domain - check numeric overlap
    if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
        if f1 == f2:
            # Exact same field: check if ranges overlap
            if op1 in (">=", ">") and op2 in ("<=", "<"):
                return v1 < v2  # e.g., >=50 and <=80 overlap
            elif op1 in ("<=", "<") and op2 in (">=", ">"):
                return v2 < v1
            elif op1 == op2:
                return True  # same direction, always could co-fire
        else:
            # Different fields in same domain: only overlap if they measure the same thing
            # (suffix match after domain prefix) - e.g. host.vram_pct vs host.vram_pct
            suffix1 = f1.split(".")[-1] if "." in f1 else f1
            suffix2 = f2.split(".")[-1] if "." in f2 else f2
            return suffix1 == suffix2
    return False


def actions_conflict(a1, a2):
    """Check if two actions are contradictory. Returns (conflicts: bool, severity: str)."""
    t1 = a1.get("type", "").lower()
    t2 = a2.get("type", "").lower()

    # Direct opposites - high severity
    opposite_pairs = {
        ("model_swap", "model_reload"),
        ("scale_up", "scale_down"),
        ("evict_agent", "load_model"),
        ("circuit_break_open", "circuit_break_close"),
        ("kill_process", "restart_service"),
    }
    if (t1, t2) in opposite_pairs or (t2, t1) in opposite_pairs:
        return True, "high"

    # Same type but different parameters that conflict - high severity
    if t1 == t2:
        p1 = a1.get("parameters", {})
        p2 = a2.get("parameters", {})
        for key in set(p1.keys()) & set(p2.keys()):
            if isinstance(p1[key], str) and isinstance(p2[key], str) and p1[key] != p2[key]:
                return True, "high"

    # Different action types on overlapping conditions - medium (ambiguous precedence)
    if t1 != t2:
        return True, "medium"

    return False, None


def preconditions_conflict(pc1, pc2):
    """Check if preconditions are mutually exclusive."""
    for p in (pc1 or []):
        for q in (pc2 or []):
            # Simple negation check: "no_X" vs "X"
            norm_p = p.lower().strip()
            norm_q = q.lower().strip()
            if "no_" in norm_p and norm_p.replace("no_", "") in norm_q:
                return True
            if "no_" in norm_q and norm_q.replace("no_", "") in norm_p:
                return True
    return False


def detect_conflicts(policy):
    """Find all conflicts in a policy dict."""
    rules = policy.get("rules", [])
    conflicts = []

    for i in range(len(rules)):
        for j in range(i + 1, len(rules)):
            r1, r2 = rules[i], rules[j]
            c1 = r1.get("condition", {})
            c2 = r2.get("condition", {})
            a1 = r1.get("action", {})
            a2 = r2.get("action", {})

            overlap = conditions_overlap(c1, c2)
            action_conflict, action_sev = actions_conflict(a1, a2)
            precond_conflict = preconditions_conflict(r1.get("preconditions"), r2.get("preconditions"))

            if overlap and (action_conflict or precond_conflict):
                if action_conflict:
                    sev = action_sev or "medium"
                    detail = f"{r1.get('degradation_type','?')} vs {r2.get('degradation_type','?')}: overlapping conditions, actions '{a1.get('type','?')}' vs '{a2.get('type','?')}'"
                    if sev == "high":
                        detail += " (contradictory)"
                else:
                    sev = "medium"
                    detail = f"{r1.get('degradation_type','?')} vs {r2.get('degradation_type','?')}: overlapping conditions, conflicting preconditions"
                conflicts.append({
                    "rule_a": r1.get("id", f"R{i}"),
                    "rule_b": r2.get("id", f"R{j}"),
                    "type": "action_conflict" if action_conflict else "precondition_conflict",
                    "severity": sev,
                    "detail": detail,
                    "actions": [a1.get("type"), a2.get("type")],
                })

    # Also check for duplicate degradation types with different actions
    by_type = {}
    for r in rules:
        dt = r.get("degradation_type", "")
        if dt not in by_type:
            by_type[dt] = []
        by_type[dt].append(r)

    for dt, group in by_type.items():
        if len(group) > 1:
            action_types = set(r.get("action", {}).get("type", "") for r in group)
            if len(action_types) > 1:
                conflicts.append({
                    "rule_a": group[0].get("id"),
                    "rule_b": group[-1].get("id"),
                    "type": "duplicate_degradation_type",
                    "severity": "high",
                    "detail": f"Multiple rules for '{dt}' prescribe different actions: {list(action_types)}",
                    "actions": list(action_types),
                })

    return conflicts


def cmd_selftest():
    print("Policy Conflict Detector - selftest")

    # Test 1: Load real policy
    policy = load_policy()
    if policy is None:
        print("  [SKIP] No remediation-policy.json found")
        return True
    rules = policy.get("rules", [])
    print(f"  Loaded {len(rules)} rules from remediation-policy.json")

    # Test 2: Run detection
    conflicts = detect_conflicts(policy)
    print(f"  Detected {len(conflicts)} conflict(s)")
    for c in conflicts:
        print(f"    [{c['severity']}] {c['rule_a']} vs {c['rule_b']}: {c['detail']}")

    # Test 3: Verify no false positives with non-overlapping rules
    test_policy = {"rules": [
        {"id": "T1", "degradation_type": "oom", "condition": {"field": "host.vram_pct", "op": ">=", "value": 98}, "action": {"type": "model_swap"}, "preconditions": []},
        {"id": "T2", "degradation_type": "cpu_spike", "condition": {"field": "host.cpu_pct", "op": ">", "value": 95}, "action": {"type": "scale_down"}, "preconditions": []},
    ]}
    tc = detect_conflicts(test_policy)
    assert len(tc) == 0, f"Expected 0 conflicts for non-overlapping rules, got {len(tc)}"
    print("  [PASS] No false positives on non-overlapping rules")

    # Test 4: Verify detection of true conflict
    conflict_policy = {"rules": [
        {"id": "C1", "degradation_type": "vram_high", "condition": {"field": "host.vram_pct", "op": ">=", "value": 95}, "action": {"type": "model_swap"}, "preconditions": ["no_other_oom"]},
        {"id": "C2", "degradation_type": "vram_critical", "condition": {"field": "host.vram_pct", "op": ">=", "value": 90}, "action": {"type": "evict_agent"}, "preconditions": []},
    ]}
    cc = detect_conflicts(conflict_policy)
    assert len(cc) >= 1, f"Expected >=1 conflict for overlapping contradictory rules, got {len(cc)}"
    print(f"  [PASS] Correctly detected {len(cc)} intentional conflict(s)")

    # Test 5: Write report
    report = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "policy_file": str(DEFAULT_POLICY),
        "rules_analyzed": len(rules),
        "conflicts_found": len(conflicts),
        "conflicts": conflicts,
        "status": "CLEAN" if not conflicts else "CONFLICTS_FOUND",
    }
    REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"  [PASS] Report written: {REPORT_FILE.name} ({len(conflicts)} conflicts)")

    print("\n  SELFTEST: ALL PASS")
    return True


def cmd_check(policy_path=None):
    policy = load_policy(policy_path)
    if not policy:
        print(f"No policy found at {policy_path or DEFAULT_POLICY}")
        return False
    rules = policy.get("rules", [])
    conflicts = detect_conflicts(policy)
    print(f"Policy: {len(rules)} rules analyzed")
    if not conflicts:
        print("  Status: CLEAN - no conflicts detected")
    else:
        print(f"  Status: {len(conflicts)} CONFLICT(S) FOUND")
        for c in conflicts:
            print(f"    [{c['severity'].upper()}] {c['rule_a']} vs {c['rule_b']}: {c['detail']}")
    return len(conflicts) == 0


def cmd_report():
    if REPORT_FILE.exists():
        data = json.loads(REPORT_FILE.read_text(encoding="utf-8"))
        print(f"Last check: {data['generated']}")
        print(f"Rules analyzed: {data['rules_analyzed']}")
        print(f"Conflicts: {data['conflicts_found']} (status: {data['status']})")
        for c in data.get("conflicts", []):
            print(f"  [{c['severity']}] {c['rule_a']} vs {c['rule_b']}: {c['detail']}")
    else:
        print("No report yet. Run --check first.")


def main():
    if "--selftest" in sys.argv:
        ok = cmd_selftest()
    elif "--check" in sys.argv:
        idx = sys.argv.index("--check")
        path = sys.argv[idx + 1] if idx + 1 < len(sys.argv) and not sys.argv[idx + 1].startswith("--") else None
        ok = cmd_check(path)
    elif "--report" in sys.argv:
        cmd_report()
        return
    else:
        print(__doc__)
        return
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
