"""decision_audit.py — Verify every autonomous decision has a complete audit entry.

Goal: #1 Autonomous Decision Audit Trail Verification
Verify all entries from last 7 days in autonomous-actions.jsonl have all required fields;
flag any unlogged or incomplete decisions by name.

Required fields per spec (autonomous-action-log-spec-2026-11-24.md):
  ts, host, action, trigger, outcome, reversible

Self-test: synthetic entry missing a field is correctly flagged with the field name.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_FILE = REPO_ROOT / "memory" / "ops" / "autonomous-actions.jsonl"
RESULTS_FILE = REPO_ROOT / "memory" / "verifier" / "decision-audit-results.json"

REQUIRED_FIELDS = ["ts", "host", "action", "trigger", "outcome", "reversible"]
WINDOW_DAYS = 7


def load_entries():
    """Load all entries from the autonomous-actions log."""
    if not LOG_FILE.exists():
        return []
    entries = []
    for line in LOG_FILE.read_text(encoding="utf-8").strip().split("\n"):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            entries.append({"_parse_error": True, "_raw": line[:100]})
    return entries


def filter_window(entries, days=WINDOW_DAYS):
    """Filter entries to last N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    in_window = []
    for e in entries:
        ts = e.get("ts", "")
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if dt >= cutoff:
                in_window.append(e)
        except (ValueError, AttributeError):
            # If ts can't be parsed, include it (it's a problem to flag)
            in_window.append(e)
    return in_window


def validate_entry(entry):
    """Check an entry for all required fields. Returns list of missing/invalid fields."""
    issues = []
    if entry.get("_parse_error"):
        return ["_unparseable_json"]
    for field in REQUIRED_FIELDS:
        if field not in entry:
            issues.append(field)
        elif entry[field] is None or entry[field] == "":
            issues.append(f"{field}_(empty)")
    # Type checks
    if "reversible" in entry and not isinstance(entry["reversible"], bool):
        issues.append("reversible_(not_bool)")
    return issues


def audit():
    """Run full audit, return results dict."""
    all_entries = load_entries()
    window_entries = filter_window(all_entries)

    violations = []
    clean_count = 0
    for i, entry in enumerate(window_entries):
        issues = validate_entry(entry)
        if issues:
            violations.append({
                "line": i + 1,
                "ts": entry.get("ts", "<unparseable>"),
                "missing_or_invalid": issues,
                "raw_snippet": str(entry)[:200]
            })
        else:
            clean_count += 1

    return {
        "audit_ts": datetime.now(timezone.utc).isoformat(),
        "window_days": WINDOW_DAYS,
        "log_file": str(LOG_FILE),
        "total_entries_all_time": len(all_entries),
        "entries_in_window": len(window_entries),
        "clean_entries": clean_count,
        "violations": violations,
        "violation_count": len(violations),
        "pass": len(violations) == 0,
    }


def self_test():
    """Synthetic tests proving the validator catches missing fields."""
    print("[SELF-TEST] decision_audit.py")
    results = []

    # T1: Complete entry passes
    good = {"ts": "2026-11-24T10:00:00Z", "host": "White", "action": "restart_portal",
            "trigger": "health_check", "outcome": "success", "reversible": True,
            "detail": "ok", "source_script": "x.py"}
    issues = validate_entry(good)
    ok = len(issues) == 0
    results.append(("T1_complete_entry_passes", ok, f"issues={issues}"))

    # T2: Missing 'trigger' is flagged by name
    missing_trigger = {k: v for k, v in good.items() if k != "trigger"}
    issues = validate_entry(missing_trigger)
    ok = "trigger" in issues
    results.append(("T2_missing_trigger_flagged", ok, f"issues={issues}"))

    # T3: Missing 'reversible' is flagged by name
    missing_rev = {k: v for k, v in good.items() if k != "reversible"}
    issues = validate_entry(missing_rev)
    ok = "reversible" in issues
    results.append(("T3_missing_reversible_flagged", ok, f"issues={issues}"))

    # T4: Empty ts is flagged
    empty_ts = dict(good)
    empty_ts["ts"] = ""
    issues = validate_entry(empty_ts)
    ok = "ts_(empty)" in issues
    results.append(("T4_empty_ts_flagged", ok, f"issues={issues}"))

    # T5: Non-bool reversible is flagged
    bad_rev = dict(good)
    bad_rev["reversible"] = "yes"
    issues = validate_entry(bad_rev)
    ok = "reversible_(not_bool)" in issues
    results.append(("T5_non_bool_reversible_flagged", ok, f"issues={issues}"))

    # T6: Unparseable JSON is flagged
    bad_json = {"_parse_error": True, "_raw": "{bad"}
    issues = validate_entry(bad_json)
    ok = "_unparseable_json" in issues
    results.append(("T6_unparseable_flagged", ok, f"issues={issues}"))

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    for name, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        print(f"  {status} {name}: {detail}")
    print(f"[SELF-TEST] {passed}/{total} passed")
    return passed == total


def main():
    if "--self-test" in sys.argv:
        ok = self_test()
        sys.exit(0 if ok else 1)

    result = audit()

    # Write results
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_FILE.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"[decision_audit] Window: {WINDOW_DAYS} days | Log: {LOG_FILE.name}")
    print(f"  Entries in window: {result['entries_in_window']}")
    print(f"  Clean: {result['clean_entries']}")
    print(f"  Violations: {result['violation_count']}")
    for v in result["violations"][:10]:
        print(f"    LINE {v['line']}: missing/invalid = {v['missing_or_invalid']} (ts={v['ts']})")
    print(f"  RESULT: {'PASS' if result['pass'] else 'FAIL'}")

    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
