"""steady_state_cert.py - Steady-State Re-Certification Loop (Scribe Cycle 26, Goal #3)

Each cycle re-checks steady-state criteria. If any fails, auto-issues a
de-certification event. If all hold N consecutive cycles, raises the certification level.

Steady-state criteria:
  C1: interventions <= BUDGET (same as convergence I1)
  C2: autonomy score >= FLOOR and stable (delta in [-3, +inf])
  C3: no unresolved incidents older than 1 cycle
  C4: all active lanes have evidence-gated goals (no claimed-only)

Certification levels:
  0 = uncertified (initial)
  1 = provisionally certified (N=2 consecutive passes)
  2 = fully certified (N=5 consecutive passes)

State is tracked in memory/scribe/steady-state-cert.jsonl (append-only).
The current level is derived from the last entry.

Output per cycle: {cycle, ts, certified, level, consecutive_passes, failing_criteria[], event}
"""
import pathlib, json, sys
from datetime import datetime, timezone

ROOT = pathlib.Path(".")

# === CONFIGURATION ===
BUDGET_INTERVENTIONS = 3
AUTONOMY_FLOOR = 60.0
STABILITY_DELTA = -3.0     # min allowed drop for C2
LEVEL_1_THRESHOLD = 2      # consecutive passes for level 1
LEVEL_2_THRESHOLD = 5      # consecutive passes for level 2


def load_jsonl(path):
    p = ROOT / path
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8").strip().split("\n")
    results = []
    for line in lines:
        line = line.strip()
        if line:
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return results


def load_json(path):
    p = ROOT / path
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def get_current_cycle():
    interventions = load_jsonl("memory/scribe/intervention-patterns.jsonl")
    if interventions:
        return max(iv.get("cycle", 0) for iv in interventions) + 1
    return 1


def check_C1_interventions():
    """C1: interventions <= BUDGET"""
    interventions = load_jsonl("memory/scribe/intervention-patterns.jsonl")
    latest_cycle = max((iv.get("cycle", 0) for iv in interventions), default=0)
    count = sum(1 for iv in interventions if iv.get("cycle") == latest_cycle)
    return count <= BUDGET_INTERVENTIONS, f"{count} interventions (budget: {BUDGET_INTERVENTIONS})"


def check_C2_score_stable():
    """C2: autonomy score >= FLOOR and stable"""
    score_data = load_json("memory/ops/autonomy-score.json")
    if not score_data:
        return False, "no autonomy score data"
    current = score_data.get("score", 0)
    trend = load_jsonl("memory/scribe/autonomy-trend.jsonl")
    delta = 0.0
    if len(trend) >= 2:
        prior = trend[-2].get("score", current)
        delta = current - prior
    passed = (current >= AUTONOMY_FLOOR) and (delta >= STABILITY_DELTA)
    return passed, f"score={current}, delta={delta:+.1f} (floor={AUTONOMY_FLOOR}, min_delta={STABILITY_DELTA})"


def check_C3_no_stale_incidents():
    """C3: no unresolved incidents older than 1 cycle"""
    incidents = load_jsonl("memory/ops/incidents.jsonl")
    if not incidents:
        return True, "no incidents"
    current_cycle = get_current_cycle()
    stale = [i for i in incidents 
             if not i.get("recovered", False) and i.get("status") != "resolved"
             and i.get("cycle", 0) < current_cycle - 1]
    return len(stale) == 0, f"{len(stale)} stale unresolved incident(s)"


def check_C4_evidence_gated():
    """C4: all active lanes have evidence-gated goals (no claimed-only)"""
    ledger = load_json("goal_ledger.json")
    if not ledger:
        return True, "no ledger data"
    claimed_only_total = sum(
        info.get("claimed_only", 0) 
        for info in ledger.get("agents", {}).values()
    )
    passed = claimed_only_total == 0
    return passed, f"{claimed_only_total} claimed-only goals across fleet"


def get_current_state():
    """Read the last entry from steady-state-cert.jsonl to get current level + consecutive passes."""
    cert_path = ROOT / "memory" / "scribe" / "steady-state-cert.jsonl"
    if not cert_path.exists():
        return {"level": 0, "consecutive_passes": 0}
    entries = load_jsonl("memory/scribe/steady-state-cert.jsonl")
    if not entries:
        return {"level": 0, "consecutive_passes": 0}
    last = entries[-1]
    return {
        "level": last.get("level", 0),
        "consecutive_passes": last.get("consecutive_passes", 0)
    }


def main():
    now_ts = datetime.now(timezone.utc).isoformat()
    cycle = get_current_cycle()
    
    # Check all criteria
    C1_pass, C1_detail = check_C1_interventions()
    C2_pass, C2_detail = check_C2_score_stable()
    C3_pass, C3_detail = check_C3_no_stale_incidents()
    C4_pass, C4_detail = check_C4_evidence_gated()
    
    criteria = {
        "C1_interventions_within_budget": (C1_pass, C1_detail),
        "C2_score_stable": (C2_pass, C2_detail),
        "C3_no_stale_incidents": (C3_pass, C3_detail),
        "C4_evidence_gated": (C4_pass, C4_detail),
    }
    
    failing = [name for name, (passed, _) in criteria.items() if not passed]
    all_pass = len(failing) == 0
    
    # Get current state
    state = get_current_state()
    
    # Update consecutive passes and level
    if all_pass:
        consecutive = state["consecutive_passes"] + 1
    else:
        consecutive = 0
    
    # Determine level (only rises after N consecutive passes)
    new_level = state["level"]
    event = None
    
    if all_pass:
        if consecutive >= LEVEL_2_THRESHOLD and new_level < 2:
            new_level = 2
            event = "CERTIFIED_LEVEL_2"
        elif consecutive >= LEVEL_1_THRESHOLD and new_level < 1:
            new_level = 1
            event = "CERTIFIED_LEVEL_1"
    else:
        # De-certification: drop level, emit event
        if state["level"] > 0:
            new_level = 0
            event = f"DECERTIFIED (failing: {', '.join(failing)})"
    
    certified = new_level > 0
    
    # Emit record
    record = {
        "cycle": cycle,
        "ts": now_ts,
        "certified": certified,
        "level": new_level,
        "consecutive_passes": consecutive,
        "failing_criteria": failing,
        "criteria_detail": {name: detail for name, (_, detail) in criteria.items()},
        "event": event
    }
    
    cert_path = ROOT / "memory" / "scribe" / "steady-state-cert.jsonl"
    with open(cert_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    
    # Report
    status = "CERTIFIED (level {0})".format(new_level) if certified else "NOT CERTIFIED"
    print(f"Cycle {cycle}: {status}")
    for name, (passed, detail) in criteria.items():
        mark = "PASS" if passed else "FAIL"
        print(f"  [{mark}] {name}: {detail}")
    if failing:
        print(f"  Failing: {failing}")
    if event:
        print(f"  EVENT: {event}")
    print(f"Consecutive passes: {consecutive} (L1@{LEVEL_1_THRESHOLD}, L2@{LEVEL_2_THRESHOLD})")
    print(f"Record written to {cert_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
