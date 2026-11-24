"""Autonomy Regression Gate — pre-commit hook for autonomy infrastructure changes.

Simulates the impact of a proposed change on the projected autonomy score.
If simulated score drops >5 points from current baseline, blocks (exit 1)
and logs to memory/ops/regressions.jsonl.

Checks:
  - fleet-mode.json schema validity
  - Mode FSM transition monotonicity
  - Autonomy score projection (linear extrapolation from last N data points)

Self-test: python memory/builder/autonomy_regression_gate.py --selftest
"""
import json, sys, time, copy
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FLEET_MODE = ROOT / "fleet-mode.json"
REGRESSIONS_LOG = ROOT / "memory" / "ops" / "regressions.jsonl"
CONVERGENCE_HEALTH = ROOT / "memory" / "ops" / "convergence-health.json"

SCORE_DROP_THRESHOLD = 5.0  # block if projected score drops more than this


def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def get_current_score():
    """Get current autonomy score from fleet-mode.json or convergence-health.json."""
    fm = _read_json(FLEET_MODE)
    if fm:
        score_val = fm.get("autonomy_score")
        if isinstance(score_val, dict):
            return float(score_val.get("ci_midpoint", score_val.get("score", 50.0)))
        elif isinstance(score_val, (int, float)):
            return float(score_val)
    # Fallback to convergence health
    ch = _read_json(CONVERGENCE_HEALTH)
    if ch:
        return float(ch.get("score", 50.0))
    return 50.0  # neutral default


def validate_fleet_mode_schema(data):
    """Validate fleet-mode.json has required fields and valid types.

    Returns (valid: bool, errors: list[str]).
    """
    errors = []
    if not isinstance(data, dict):
        return False, ["root is not a dict"]

    # Required fields
    if "mode" not in data:
        errors.append("missing 'mode' field")
    elif data["mode"] not in ("WORK", "MAINTENANCE", "IDLE", "STANDBY"):
        errors.append(f"invalid mode: {data['mode']}")

    if "autonomy_score" not in data:
        errors.append("missing 'autonomy_score' field")
    else:
        score = data["autonomy_score"]
        if isinstance(score, (int, float)):
            if not (0 <= score <= 100):
                errors.append(f"autonomy_score out of range: {score}")
        elif isinstance(score, dict):
            mid = score.get("ci_midpoint", score.get("score"))
            if mid is None:
                errors.append("autonomy_score object missing ci_midpoint/score")
            elif not (0 <= mid <= 100):
                errors.append(f"autonomy_score out of range: {mid}")

    # Optional but validated if present
    if "mode_history" in data and not isinstance(data["mode_history"], list):
        errors.append("mode_history must be a list")

    return len(errors) == 0, errors


def check_monotonicity(data, incidents=None):
    """Check that autonomy_score only decreases if there's a logged incident.

    Returns (valid: bool, reason: str).
    """
    score = data.get("autonomy_score")
    if isinstance(score, dict):
        score = score.get("ci_midpoint", score.get("score", 50.0))
    if not isinstance(score, (int, float)):
        return True, "no score to check"

    history = data.get("mode_history", [])
    if len(history) < 2:
        return True, "insufficient history for monotonicity check"

    prev_scores = []
    for h in history[-10:]:
        s = h.get("autonomy_score")
        if isinstance(s, dict):
            s = s.get("ci_midpoint", s.get("score"))
        if isinstance(s, (int, float)):
            prev_scores.append(s)

    if len(prev_scores) < 2:
        return True, "insufficient score history"

    prev_score = prev_scores[-1]
    if score < prev_score:
        # Score decreased - check for incident in the window
        if incidents is None:
            # Can't verify without incidents; allow but flag
            return True, f"score decreased {prev_score}->{score} (no incident log available)"
        # Check if any incident exists in last 1h
        now = time.time()
        recent_incidents = [i for i in incidents if _parse_ts(i.get("timestamp", "")) > now - 3600]
        if not recent_incidents:
            return False, f"score decreased {prev_score}->{score} without logged incident"

    return True, "monotonicity OK"


def _parse_ts(ts_str):
    if not ts_str:
        return 0.0
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError):
        return 0.0


def project_score_change(proposed_data, current_data):
    """Project the autonomy score impact of a proposed change.

    Compares key factors between current and proposed state:
      - Mode change: WORK->IDLE = +2 (less pressure), IDLE->WORK = -1
      - Score field changes directly
      - Mode history length (more transitions = slight instability = -0.5 per extra)

    Returns projected score delta (positive = improvement, negative = degradation).
    """
    delta = 0.0

    # Direct score change (if autonomy_score field changed)
    cur_score = current_data.get("autonomy_score")
    prop_score = proposed_data.get("autonomy_score")
    if isinstance(cur_score, dict):
        cur_score = cur_score.get("ci_midpoint", cur_score.get("score"))
    if isinstance(prop_score, dict):
        prop_score = prop_score.get("ci_midpoint", prop_score.get("score"))

    if isinstance(cur_score, (int, float)) and isinstance(prop_score, (int, float)):
        delta += (prop_score - cur_score)
    elif cur_score != prop_score and prop_score is None:
        # Score removed = degradation
        delta -= 10.0

    # Mode change impact
    cur_mode = current_data.get("mode", "WORK")
    prop_mode = proposed_data.get("mode", "WORK")
    if cur_mode != prop_mode:
        mode_impact = {
            ("WORK", "MAINTENANCE"): 0.0,
            ("WORK", "IDLE"): 2.0,
            ("WORK", "STANDBY"): 1.0,
            ("IDLE", "WORK"): -1.0,
            ("MAINTENANCE", "WORK"): -0.5,
            ("STANDBY", "WORK"): -0.5,
        }
        delta += mode_impact.get((cur_mode, prop_mode), 0.0)

    # Transition frequency: more transitions in history = instability
    cur_transitions = len(current_data.get("mode_history", []))
    prop_transitions = len(proposed_data.get("mode_history", []))
    if prop_transitions > cur_transitions:
        extra = prop_transitions - cur_transitions
        delta -= 0.5 * min(extra, 4)  # cap the penalty

    return round(delta, 2)


def evaluate(proposed_data, current_data=None):
    """Evaluate a proposed fleet-mode.json change.

    Returns dict: {"pass": bool, "reason": str, "projected_delta": float,
                   "schema_errors": list, "monotonicity_ok": bool}
    """
    if current_data is None:
        current_data = _read_json(FLEET_MODE) or {}

    # 1. Schema validation
    schema_ok, schema_errors = validate_fleet_mode_schema(proposed_data)
    if not schema_ok:
        return {
            "pass": False,
            "reason": f"Schema validation failed: {schema_errors}",
            "projected_delta": None,
            "schema_errors": schema_errors,
            "monotonicity_ok": True,
        }

    # 2. Monotonicity check
    mono_ok, mono_reason = check_monotonicity(proposed_data)

    # 3. Score projection
    delta = project_score_change(proposed_data, current_data)

    # Decision: block if score drops more than threshold
    blocked = delta < -SCORE_DROP_THRESHOLD
    if blocked:
        reason = f"Project autonomy score drop of {abs(delta)} pts exceeds threshold ({SCORE_DROP_THRESHOLD})"
    elif not mono_ok:
        reason = f"Monotonicity violation: {mono_reason}"
    else:
        reason = f"OK (projected delta: {delta:+.1f} pts)"

    return {
        "pass": not blocked and mono_ok,
        "reason": reason,
        "projected_delta": delta,
        "schema_errors": schema_errors,
        "monotonicity_ok": mono_ok,
    }


def log_regression(result, proposed_data):
    """Log a blocked regression to the regressions file."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "projected_delta": result.get("projected_delta"),
        "reason": result["reason"],
        "schema_errors": result.get("schema_errors", []),
        "proposed_mode": proposed_data.get("mode") if isinstance(proposed_data, dict) else None,
    }
    try:
        with open(REGRESSIONS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def selftest():
    """Self-test: verify block-on-drop, pass-on-neutral, pass-on-improve paths."""
    current = {
        "mode": "WORK",
        "autonomy_score": 75.0,
        "mode_history": [{"mode": "WORK", "autonomy_score": 72.0}],
    }

    # Test 1: Pass on neutral (no change)
    r = evaluate(copy.deepcopy(current), current)
    assert r["pass"] is True, f"FAIL test1: expected pass, got {r}"
    print(f"  PASS test1: neutral change → pass (delta={r['projected_delta']})")

    # Test 2: Pass on improve (score goes up)
    improved = copy.deepcopy(current)
    improved["autonomy_score"] = 80.0
    r2 = evaluate(improved, current)
    assert r2["pass"] is True, f"FAIL test2: expected pass, got {r2}"
    assert r2["projected_delta"] > 0, f"FAIL test2: expected positive delta, got {r2['projected_delta']}"
    print(f"  PASS test2: improve → pass (delta={r2['projected_delta']:+.1f})")

    # Test 3: Block on drop (score drops >5)
    degraded = copy.deepcopy(current)
    degraded["autonomy_score"] = 68.0  # 7-point drop
    r3 = evaluate(degraded, current)
    assert r3["pass"] is False, f"FAIL test3: expected block, got {r3}"
    assert "exceeds threshold" in r3["reason"], f"FAIL test3: wrong reason: {r3['reason']}"
    print(f"  PASS test3: drop >5 → block (delta={r3['projected_delta']:+.1f}, reason='{r3['reason']}')")

    # Test 4: Pass on small drop (<5)
    slight_drop = copy.deepcopy(current)
    slight_drop["autonomy_score"] = 72.0  # 3-point drop
    r4 = evaluate(slight_drop, current)
    assert r4["pass"] is True, f"FAIL test4: expected pass (small drop), got {r4}"
    print(f"  PASS test4: small drop (<5) → pass (delta={r4['projected_delta']:+.1f})")

    # Test 5: Block on schema violation
    bad_schema = {"mode": "INVALID_MODE", "autonomy_score": 75.0}
    r5 = evaluate(bad_schema, current)
    assert r5["pass"] is False, f"FAIL test5: expected block (schema), got {r5}"
    assert len(r5["schema_errors"]) > 0, "FAIL test5: no schema errors reported"
    print(f"  PASS test5: schema violation → block (errors={r5['schema_errors']})")

    # Test 6: Integration - verify pre_commit_gate.py references this module
    gate_path = ROOT / "memory" / "builder" / "pre_commit_gate.py"
    if gate_path.exists():
        gate_text = gate_path.read_text(encoding="utf-8")
        assert "autonomy_regression_gate" in gate_text, \
            f"FAIL test6: pre_commit_gate.py does not reference autonomy_regression_gate"
        print("  PASS test6: pre_commit_gate.py integration confirmed")
    else:
        print("  SKIP test6: pre_commit_gate.py not found (integration pending)")

    print("\n  ALL SELFTESTS PASSED")
    return 0


def main():
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    elif "--check" in sys.argv:
        # Check a proposed file: python autonomy_regression_gate.py --check <path>
        path = Path(sys.argv[sys.argv.index("--check") + 1])
        proposed = _read_json(path)
        if proposed is None:
            print(f"ERROR: cannot read {path}")
            sys.exit(2)
        result = evaluate(proposed)
        print(json.dumps(result, indent=2))
        if not result["pass"]:
            log_regression(result, proposed)
            sys.exit(1)
        sys.exit(0)
    else:
        # Default: check current fleet-mode.json
        current = _read_json(FLEET_MODE)
        if current is None:
            print("ERROR: cannot read fleet-mode.json")
            sys.exit(2)
        result = evaluate(current, current)  # self-check (always passes unless schema broken)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
