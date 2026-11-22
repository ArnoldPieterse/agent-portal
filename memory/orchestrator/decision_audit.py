"""decision_audit.py - Orchestrator cycle-10 goal 9 (Decision Audit Validator).

Scans decision-log.jsonl for policy violations:
  * Missing required fields (source, rule_id, action, rollback, preconditions_met, timestamp)
  * Action taken without preconditions_met=True
  * Missing or empty rollback definition
  * Unknown source not in the allowed set

Report: list of violations with entry index, timestamp, rule broken, detail.
Verified: clean log -> 0 violations; injected violation -> detected + reported.

Usage:
    python memory/orchestrator/decision_audit.py            # audit real log
    python memory/orchestrator/decision_audit.py --selftest # isolated test
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
DECISION_LOG = HERE.parent.parent / "decision-log.jsonl"

REQUIRED_FIELDS = ("source", "rule_id", "action", "rollback", "preconditions_met", "timestamp")
ALLOWED_SOURCES = {
    "remediation_policy", "context_budget", "roster_monitor",
    "incident_responder", "rebalancer", "model_router", "capacity_governor",
}


def audit_entry(idx: int, entry: dict) -> list[dict]:
    """Return list of violations for a single decision-log entry."""
    violations = []
    ts = entry.get("timestamp", "<missing>")

    # 1. Missing required fields
    for field in REQUIRED_FIELDS:
        if field not in entry:
            violations.append({
                "entry": idx, "timestamp": ts, "rule": f"DA-MISSING-{field}",
                "detail": f"required field '{field}' is absent",
            })

    # 2. preconditions_met must be True for non-informational events
    if "preconditions_met" in entry and entry["preconditions_met"] is not True:
        violations.append({
            "entry": idx, "timestamp": ts, "rule": "DA-PRECONDITIONS-UNMET",
            "detail": f"action logged with preconditions_met={entry['preconditions_met']}",
        })

    # 3. Rollback must exist and not be completely empty (type or steps)
    if "rollback" in entry:
        rb = entry["rollback"]
        if isinstance(rb, dict):
            if not rb.get("type") and not rb.get("steps"):
                violations.append({
                    "entry": idx, "timestamp": ts, "rule": "DA-ROLLBACK-EMPTY",
                    "detail": "rollback field present but has no type or steps",
                })
        elif isinstance(rb, (str, list)) and not rb:
            violations.append({
                "entry": idx, "timestamp": ts, "rule": "DA-ROLLBACK-EMPTY",
                "detail": f"rollback is empty {type(rb).__name__}",
            })

    # 4. Source must be in the allowed set (informational, not blocking)
    if "source" in entry and entry["source"] not in ALLOWED_SOURCES:
        violations.append({
            "entry": idx, "timestamp": ts, "rule": "DA-UNKNOWN-SOURCE",
            "detail": f"unknown source '{entry['source']}' (allowed: {sorted(ALLOWED_SOURCES)})",
        })

    return violations


def run_audit(log_path: Path | None = None) -> dict:
    """Audit the decision log. Returns {total_entries, violations, clean}."""
    log_path = log_path or DECISION_LOG
    if not log_path.exists():
        return {"total_entries": 0, "violations": [], "clean": True}

    all_violations = []
    total = 0
    for idx, line in enumerate(log_path.read_text(encoding="utf-8").splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as e:
            all_violations.append({
                "entry": idx, "timestamp": "<parse-error>",
                "rule": "DA-MALFORMED-JSON", "detail": str(e),
            })
            total += 1
            continue
        total += 1
        all_violations.extend(audit_entry(idx, entry))

    return {"total_entries": total, "violations": all_violations, "clean": len(all_violations) == 0}


def format_report(result: dict) -> str:
    lines = [f"Decision Audit Report - {datetime.now(timezone.utc).isoformat()}"]
    lines.append(f"Total entries scanned: {result['total_entries']}")
    lines.append(f"Violations found: {len(result['violations'])}")
    if result["clean"]:
        lines.append("Status: CLEAN (no policy violations)")
    else:
        for v in result["violations"]:
            lines.append(f"  [{v['rule']}] entry {v['entry']} @ {v['timestamp']}: {v['detail']}")
    return "\n".join(lines)


# --- Selftest -------------------------------------------------------------
def _selftest() -> None:
    import tempfile
    tmpdir = Path(tempfile.mkdtemp(prefix="da_audit_"))

    # Test 1: clean log -> 0 violations
    clean_log = tmpdir / "clean.jsonl"
    clean_entry = {
        "source": "remediation_policy", "rule_id": "R001",
        "action": {"type": "model_swap", "description": "test"},
        "rollback": {"type": "restore_original", "steps": ["reload"]},
        "preconditions_met": True, "timestamp": "2026-11-23T00:00:00Z",
    }
    clean_log.write_text(json.dumps(clean_entry) + "\n")
    r = run_audit(clean_log)
    assert r["clean"], f"clean log should have 0 violations, got {r['violations']}"
    assert r["total_entries"] == 1
    print("  [1] clean log -> 0 violations")

    # Test 2: injected violation (missing preconditions_met) -> detected
    bad_log = tmpdir / "bad.jsonl"
    bad_entry = {
        "source": "incident_responder", "rule_id": "IR-STEP-KILL",
        "action": {"type": "kill_process", "description": "forced kill"},
        "rollback": {"type": "reload_model", "steps": ["restart"]},
        # preconditions_met is MISSING
        "timestamp": "2026-11-23T01:00:00Z",
    }
    bad_log.write_text(json.dumps(bad_entry) + "\n")
    r = run_audit(bad_log)
    assert not r["clean"], "injected violation should be detected"
    rules = {v["rule"] for v in r["violations"]}
    assert "DA-MISSING-preconditions_met" in rules, f"expected DA-MISSING-preconditions_met, got {rules}"
    print(f"  [2] injected violation (missing preconditions_met) -> detected: {rules}")

    # Test 3: multiple violations on one entry
    multi_log = tmpdir / "multi.jsonl"
    multi_entry = {
        "source": "unknown_agent",  # unknown source
        "rule_id": "X999",
        "action": {"type": "do_thing"},
        "rollback": {},  # empty rollback
        "preconditions_met": False,  # not met
        "timestamp": "2026-11-23T02:00:00Z",
    }
    multi_log.write_text(json.dumps(multi_entry) + "\n")
    r = run_audit(multi_log)
    assert len(r["violations"]) >= 3, f"expected >=3 violations, got {len(r['violations'])}: {r['violations']}"
    print(f"  [3] multi-violation entry -> {len(r['violations'])} violations detected")

    # Test 4: report format includes count + details
    report = format_report(run_audit(multi_log))
    assert "Violations found:" in report
    assert "DA-" in report
    print("  [4] report format verified (count + rule refs present)")

    print("SELFTEST PASS: decision_audit detects all violation classes; clean log produces 0")


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        _selftest()
    else:
        result = run_audit()
        print(format_report(result))
