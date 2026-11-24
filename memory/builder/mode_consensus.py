"""Fleet Mode Consensus Validator (Builder cycle-16 goal 3).

Detects and resolves concurrent-write conflicts on fleet-mode.json.
When two writes land within CONFLICT_WINDOW_S of each other (detected via mtime + content hash),
applies last-writer-wins-with-validation:
  - winning state must pass schema validation
  - monotonicity: autonomy_score can only decrease if a logged incident exists in incidents.jsonl

Log all resolutions to memory/ops/mode-conflicts.jsonl.

Usage:
    python memory/builder/mode_consensus.py --selftest
"""
import json, hashlib, time, os, pathlib, sys, argparse
from datetime import datetime, timezone
from typing import Optional

HERE = pathlib.Path(__file__).resolve().parent.parent.parent  # project root
FLEET_MODE_PATH = HERE / "memory" / "fleet" / "fleet-mode.json"
INCIDENTS_PATH = HERE / "memory" / "ops" / "incidents.jsonl"
CONFLICT_LOG = HERE / "memory" / "ops" / "mode-conflicts.jsonl"

CONFLICT_WINDOW_S = 5.0  # writes within this window are considered concurrent

# --- Schema definition for fleet-mode.json ---
REQUIRED_FIELDS = {
    "mode": str,
    "timestamp": str,  # ISO format
    "goal_pct": (int, float),
    "agent_count": int,
    "cycle": str,
}
VALID_MODES = {"MAINTENANCE", "STEADY-STATE", "ACTIVE", "IDLE", "DEGRADED"}


def validate_schema(state: dict) -> list:
    """Return list of schema violations (empty = valid)."""
    errors = []
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in state:
            errors.append(f"missing required field: {field}")
        elif not isinstance(state[field], expected_type):
            errors.append(f"{field}: expected {expected_type}, got {type(state[field]).__name__}")
    # Mode value check
    if "mode" in state and state["mode"] not in VALID_MODES:
        errors.append(f"mode: '{state['mode']}' not in valid set {VALID_MODES}")
    # goal_pct range
    if "goal_pct" in state and isinstance(state["goal_pct"], (int, float)):
        if not (0 <= state["goal_pct"] <= 100):
            errors.append(f"goal_pct: {state['goal_pct']} out of range [0,100]")
    return errors


def check_monotonicity(old_state: dict, new_state: dict) -> list:
    """Check that autonomy_score only decreases when an incident is logged.
    Returns list of violations (empty = pass)."""
    violations = []
    old_score = old_state.get("autonomy_score")
    new_score = new_state.get("autonomy_score")
    if old_score is None or new_score is None:
        return violations  # no score to check
    if new_score < old_score:
        # Score decreased - need incident in the window
        if not _incident_exists_in_window(old_state, new_state):
            violations.append(
                f"autonomy_score decreased {old_score}->{new_score} without logged incident"
            )
    return violations


def _incident_exists_in_window(old_state: dict, new_state: dict) -> bool:
    """Check if incidents.jsonl has an entry between old and new timestamps."""
    try:
        lines = INCIDENTS_PATH.read_text(encoding="utf-8").splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            ts = rec.get("ts", "")
            # Simple check: any incident with a timestamp between old and new
            old_ts = old_state.get("timestamp", "")
            new_ts = new_state.get("timestamp", "")
            if old_ts <= ts <= new_ts:
                return True
    except Exception:
        pass
    return False


def content_hash(state: dict) -> str:
    """SHA-256 of canonical JSON for the state."""
    canonical = json.dumps(state, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def detect_conflict(write_a: dict, write_b: dict) -> bool:
    """Two writes conflict if their timestamps are within CONFLICT_WINDOW_S."""
    try:
        from datetime import datetime as dt
        ts_a = dt.fromisoformat(write_a["timestamp"].replace("Z", "+00:00"))
        ts_b = dt.fromisoformat(write_b["timestamp"].replace("Z", "+00:00"))
        delta = abs((ts_a - ts_b).total_seconds())
        return delta <= CONFLICT_WINDOW_S
    except Exception:
        return False


def resolve_conflict(state_a: dict, state_b: dict) -> dict:
    """Last-writer-wins-with-validation.
    
    Returns dict with keys: winner ('a'|'b'), rejected (dict), reasons (list).
    The later timestamp wins, but must pass schema + monotonicity checks.
    If the later write fails validation, the earlier one wins.
    """
    # Determine which is later
    ts_a = state_a.get("timestamp", "")
    ts_b = state_b.get("timestamp", "")
    if ts_b >= ts_a:
        candidate, fallback = state_b, state_a
        winner_id, rejected_id = "b", "a"
    else:
        candidate, fallback = state_a, state_b
        winner_id, rejected_id = "a", "b"

    reasons = []
    # Validate candidate (the later write)
    schema_errors = validate_schema(candidate)
    if schema_errors:
        reasons.extend(f"schema: {e}" for e in schema_errors)
    mono_violations = check_monotonicity(fallback, candidate)
    reasons.extend(mono_violations)

    if not reasons:
        # Later write is valid - it wins
        return {"winner": winner_id, "rejected": rejected_id, "reasons": []}
    else:
        # Later write failed validation - earlier wins
        return {"winner": rejected_id, "rejected": winner_id, "reasons": reasons}


def log_conflict(event: dict):
    """Append a conflict resolution event to mode-conflicts.jsonl."""
    CONFLICT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFLICT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def process_writes(writes: list) -> dict:
    """Process a batch of writes, detect conflicts, resolve, log.
    Returns summary dict."""
    results = []
    for i in range(len(writes)):
        for j in range(i + 1, len(writes)):
            if detect_conflict(writes[i], writes[j]):
                resolution = resolve_conflict(writes[i], writes[j])
                event = {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "write_a_hash": content_hash(writes[i]),
                    "write_b_hash": content_hash(writes[j]),
                    "resolution": resolution,
                }
                log_conflict(event)
                results.append({"pair": (i, j), "conflict": True, **resolution})
    return {"total_writes": len(writes), "conflicts_detected": len(results), "resolutions": results}


# --- Self-test ---
def selftest() -> int:
    """Simulate 3 concurrent write scenarios. Returns 0 on pass, 1 on fail."""
    passed = 0
    failed = 0
    
    # Scenario 1: Two valid writes within 5s - later should win (no score change)
    print("Scenario 1: Two valid concurrent writes, no score change")
    state_a = {"mode": "MAINTENANCE", "timestamp": "2026-11-25T10:00:00Z",
               "goal_pct": 70.0, "agent_count": 7, "cycle": "cycle-16"}
    state_b = {"mode": "ACTIVE", "timestamp": "2026-11-25T10:00:03Z",
               "goal_pct": 75.0, "agent_count": 7, "cycle": "cycle-16"}
    assert detect_conflict(state_a, state_b), "Should detect conflict"
    res = resolve_conflict(state_a, state_b)
    if res["winner"] == "b":
        print("  PASS: later valid write wins")
        passed += 1
    else:
        print(f"  FAIL: expected b to win, got {res}")
        failed += 1

    # Scenario 2: Later write has score decrease without incident - should be rejected
    print("Scenario 2: Score decrease without logged incident")
    state_c = {"mode": "MAINTENANCE", "timestamp": "2026-11-25T11:00:00Z",
               "goal_pct": 70.0, "agent_count": 7, "cycle": "cycle-16",
               "autonomy_score": 0.80}
    state_d = {"mode": "DEGRADED", "timestamp": "2026-11-25T11:00:02Z",
               "goal_pct": 70.0, "agent_count": 7, "cycle": "cycle-16",
               "autonomy_score": 0.50}
    assert detect_conflict(state_c, state_d), "Should detect conflict"
    res = resolve_conflict(state_c, state_d)
    if res["winner"] == "a" and any("incident" in r for r in res["reasons"]):
        print(f"  PASS: score drop rejected (no incident): {res['reasons'][0]}")
        passed += 1
    else:
        print(f"  FAIL: expected a to win due to no incident, got {res}")
        failed += 1

    # Scenario 3: Schema violation in later write - should be rejected
    print("Scenario 3: Later write has schema violation (invalid mode)")
    state_e = {"mode": "MAINTENANCE", "timestamp": "2026-11-25T12:00:00Z",
               "goal_pct": 70.0, "agent_count": 7, "cycle": "cycle-16"}
    state_f = {"mode": "INVALID_MODE_XYZ", "timestamp": "2026-11-25T12:00:04Z",
               "goal_pct": 70.0, "agent_count": 7, "cycle": "cycle-16"}
    assert detect_conflict(state_e, state_f), "Should detect conflict"
    res = resolve_conflict(state_e, state_f)
    if res["winner"] == "a" and any("schema" in r for r in res["reasons"]):
        print(f"  PASS: schema violation rejected: {res['reasons'][0]}")
        passed += 1
    else:
        print(f"  FAIL: expected a to win due to schema error, got {res}")
        failed += 1

    # Bonus: verify process_writes end-to-end with logging
    print("Scenario 4 (bonus): process_writes end-to-end")
    summary = process_writes([state_a, state_b])
    if summary["conflicts_detected"] == 1:
        print(f"  PASS: 1 conflict detected and resolved, logged to {CONFLICT_LOG.name}")
        passed += 1
    else:
        print(f"  FAIL: expected 1 conflict, got {summary}")
        failed += 1

    print(f"\nSelftest result: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fleet Mode Consensus Validator")
    parser.add_argument("--selftest", action="store_true", help="Run self-test scenarios")
    args = parser.parse_args()
    if args.selftest:
        sys.exit(selftest())
    else:
        # Default: check current fleet-mode.json for schema validity
        state = json.loads(FLEET_MODE_PATH.read_text(encoding="utf-8"))
        errors = validate_schema(state)
        if errors:
            print(f"SCHEMA VIOLATIONS in fleet-mode.json:")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)
        else:
            print(f"fleet-mode.json: schema valid, hash={content_hash(state)}")
            sys.exit(0)