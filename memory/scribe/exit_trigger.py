"""Convergence Exit-Trigger Monitor - detects when the fleet should STOP converging
and switch to maintenance-only (steady-state) mode.

Trigger conditions (either one fires):
  T1: Plateau - autonomy score change < EPSILON for >= PLATEAU_CYCLES consecutive cycles
  T2: Zero interventions - intervention count == 0 for >= ZERO_INTV_CYCLES consecutive cycles

When triggered, emits a "convergence complete -> steady state" event and auto-drafts
a mode-transition narrative.

Output: memory/scribe/exit-trigger.jsonl
  {cycle, fired: bool, trigger: "T1_plateau"|"T2_zero_interventions"|null,
   scores[], deltas[], interventions[], narrative_path}

Schema for Orchestrator's mode system to consume:
  - fired=true means the fleet has reached steady state; switch to maintenance-only
  - trigger names which condition met
  - narrative_path points to the auto-drafted transition doc (for human review)

Parameters (stated, not invented):
  EPSILON = 1.0       (score delta within this = "plateaued")
  PLATEAU_CYCLES = 3  (consecutive cycles needed for T1)
  ZERO_INTV_CYCLES = 3 (consecutive zero-intervention cycles needed for T2)

Data sources:
  - memory/scribe/convergence-kpi.jsonl (primary: cycle, autonomy_score, interventions)
  - memory/scribe/autonomy-trend.jsonl (fallback if KPI file missing a cycle)
"""
import json, pathlib, sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "memory/scribe/exit-trigger.jsonl"
NARRATIVE_DIR = ROOT / "memory/scribe"

# Stated parameters
EPSILON = 1.0
PLATEAU_CYCLES = 3
ZERO_INTV_CYCLES = 3


def load_jsonl(path):
    p = pathlib.Path(path)
    if not p.is_absolute():
        p = ROOT / p
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8").strip().split("\n")
    out = []
    for line in lines:
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def get_cycle_data():
    """Load per-cycle data from convergence-kpi.jsonl, supplemented by autonomy-trend.jsonl."""
    kpi = load_jsonl("memory/scribe/convergence-kpi.jsonl")
    trend = load_jsonl("memory/scribe/autonomy-trend.jsonl")

    # Build {cycle: {score, interventions}}
    data = {}
    for e in kpi:
        c = e.get("cycle")
        if c is not None:
            data[c] = {
                "score": e.get("autonomy_score"),
                "interventions": e.get("interventions", 0)
            }
    # Supplement with trend for any missing scores
    for e in trend:
        c = e.get("cycle")
        if c is not None and c in data and data[c]["score"] is None:
            data[c]["score"] = e.get("score")

    return dict(sorted(data.items()))


def check_plateau(scores):
    """Check if last PLATEAU_CYCLES consecutive deltas are all < EPSILON."""
    if len(scores) < PLATEAU_CYCLES + 1:
        return False, []
    # Need at least PLATEAU_CYCLES deltas (i.e., PLATEAU_CYCLES+1 scores)
    recent = scores[-(PLATEAU_CYCLES + 1):]
    deltas = [recent[i+1] - recent[i] for i in range(len(recent)-1)]
    all_plateaued = all(abs(d) < EPSILON for d in deltas)
    return all_plateaued, deltas


def check_zero_interventions(interventions):
    """Check if last ZERO_INTV_CYCLES consecutive cycles all have 0 interventions."""
    if len(interventions) < ZERO_INTV_CYCLES:
        return False
    recent = interventions[-ZERO_INTV_CYCLES:]
    return all(v == 0 for v in recent)


def draft_narrative(cycle, trigger, scores, deltas, interventions):
    """Auto-draft the mode-transition narrative."""
    ts = datetime.now(timezone.utc).isoformat()
    path = NARRATIVE_DIR / "mode-transition-narrative.md"

    if trigger == "T1_plateau":
        condition_desc = f"Autonomy score plateaued: last {PLATEAU_CYCLES} deltas all < {EPSILON} pts (deltas: {deltas})"
    else:
        condition_desc = f"Zero human interventions for {ZERO_INTV_CYCLES} consecutive cycles"

    narrative = f"""# Mode Transition: Convergence Complete -> Steady State

**Date:** {ts}
**Cycle:** {cycle}
**Trigger:** {trigger}
**Condition met:** {condition_desc}

## Summary

The fleet has reached convergence steady state. The autonomy score has
{'plateaued within ' + str(EPSILON) + ' points for ' + str(PLATEAU_CYCLES) + ' consecutive cycles' if trigger == 'T1_plateau' else 'seen zero human interventions for ' + str(ZERO_INTV_CYCLES) + ' consecutive cycles'},
indicating that active convergence work is complete and the fleet should transition
to maintenance-only mode.

## Score Trajectory
"""
    for i, s in enumerate(scores):
        d = f" (delta: {deltas[i-1]:+.2f})" if i > 0 and i - 1 < len(deltas) else ""
        narrative += f"- Cycle data point {i+1}: {s}{d}\n"

    narrative += f"""
## Interventions
"""
    for i, v in enumerate(interventions):
        narrative += f"- Data point {i+1}: {v} interventions\n"

    narrative += f"""
## Recommended Actions
1. Orchestrator: switch fleet mode to `maintenance-only` (no new convergence goals)
2. Scribe: re-certify steady state per cycle (steady_state_cert.py)
3. Mechanic: reduce monitoring cadence from per-cycle to weekly
4. Human: review this narrative and confirm mode transition (A1 action, SLA 48h)

## Schema Note for Orchestrator Mode System
This event line in exit-trigger.jsonl is the machine-readable trigger.
`fired=true` + `trigger` field is all the mode system needs to act.
"""
    path.write_text(narrative, encoding="utf-8")
    return str(path.relative_to(ROOT))


def run():
    data = get_cycle_data()
    if not data:
        print("No cycle data found. Cannot evaluate exit trigger.")
        # Still emit a non-fired line for the current state
        entry = {
            "cycle": None,
            "fired": False,
            "trigger": None,
            "scores": [],
            "deltas": [],
            "interventions": [],
            "narrative_path": None,
            "ts": datetime.now(timezone.utc).isoformat(),
            "note": "no data available"
        }
        OUT.write_text(json.dumps(entry) + "\n", encoding="utf-8")
        return entry

    cycles = list(data.keys())
    scores = [data[c]["score"] for c in cycles if data[c]["score"] is not None]
    interventions = [data[c]["interventions"] for c in cycles]

    # Compute deltas
    all_deltas = [scores[i+1] - scores[i] for i in range(len(scores)-1)]

    # Check triggers
    plateau_met, recent_deltas = check_plateau(scores)
    zero_intv_met = check_zero_interventions(interventions)

    fired = False
    trigger = None
    narrative_path = None

    if plateau_met:
        fired = True
        trigger = "T1_plateau"
    elif zero_intv_met:
        fired = True
        trigger = "T2_zero_interventions"

    if fired:
        narrative_path = draft_narrative(cycles[-1], trigger, scores, all_deltas, interventions)

    entry = {
        "cycle": cycles[-1],
        "fired": fired,
        "trigger": trigger,
        "scores": scores,
        "deltas": all_deltas,
        "interventions": interventions,
        "narrative_path": narrative_path,
        "ts": datetime.now(timezone.utc).isoformat(),
        "params": {"epsilon": EPSILON, "plateau_cycles": PLATEAU_CYCLES, "zero_intv_cycles": ZERO_INTV_CYCLES}
    }

    # Append to output (one line per evaluation)
    existing = ""
    if OUT.exists():
        existing = OUT.read_text(encoding="utf-8")
    OUT.write_text(existing + json.dumps(entry) + "\n", encoding="utf-8")

    print(f"Cycle {cycles[-1]}: fired={fired}, trigger={trigger}")
    print(f"  Scores: {scores}")
    print(f"  Deltas: {all_deltas}")
    print(f"  Interventions: {interventions}")
    if fired:
        print(f"  Narrative: {narrative_path}")
    return entry


def run_synthetic_test():
    """Test with synthetic plateau data to verify T1 fires exactly once."""
    print("\n=== SYNTHETIC TEST ===")

    # Case 1: Plateau (scores within epsilon for 3+ cycles)
    test_data_plateau = {
        10: {"score": 70.0, "interventions": 2},
        11: {"score": 70.4, "interventions": 1},
        12: {"score": 70.8, "interventions": 0},
        13: {"score": 71.1, "interventions": 0},
    }
    # Deltas: +0.4, +0.4, +0.3 -> all < 1.0 -> PLATEAU FIRES

    # Case 2: Still improving (one delta > epsilon)
    test_data_improving = {
        10: {"score": 70.0, "interventions": 2},
        11: {"score": 70.4, "interventions": 1},
        12: {"score": 70.8, "interventions": 0},
        13: {"score": 72.5, "interventions": 0},
    }
    # Deltas: +0.4, +0.4, +1.7 -> last delta > 1.0 -> NO PLATEAU

    # Case 3: Zero interventions for 3 cycles
    test_data_zero = {
        10: {"score": 68.0, "interventions": 3},
        11: {"score": 70.5, "interventions": 1},
        12: {"score": 71.0, "interventions": 0},
        13: {"score": 72.8, "interventions": 0},
        14: {"score": 74.9, "interventions": 0},
    }
    # Last 3 interventions: [0, 0, 0] -> T2 FIRES (but T1 also fires since deltas < 1.0... wait)
    # Deltas: +2.5, +0.5, +1.8, +2.1 -> NOT all < 1.0 -> T1 does NOT fire
    # But last 3 interventions are [0,0,0] -> T2 fires

    results = []

    # Test plateau
    scores_p = [v["score"] for v in test_data_plateau.values()]
    intv_p = [v["interventions"] for v in test_data_plateau.values()]
    p1, d1 = check_plateau(scores_p)
    z1 = check_zero_interventions(intv_p)
    fired1 = p1 or z1
    results.append(("plateau", fired1, "T1_plateau" if p1 else ("T2_zero_interventions" if z1 else None)))

    # Test improving
    scores_i = [v["score"] for v in test_data_improving.values()]
    intv_i = [v["interventions"] for v in test_data_improving.values()]
    p2, d2 = check_plateau(scores_i)
    z2 = check_zero_interventions(intv_i)
    fired2 = p2 or z2
    results.append(("improving", fired2, "T1_plateau" if p2 else ("T2_zero_interventions" if z2 else None)))

    # Test zero interventions
    scores_z = [v["score"] for v in test_data_zero.values()]
    intv_z = [v["interventions"] for v in test_data_zero.values()]
    p3, d3 = check_plateau(scores_z)
    z3 = check_zero_interventions(intv_z)
    fired3 = p3 or z3
    results.append(("zero_intv", fired3, "T1_plateau" if p3 else ("T2_zero_interventions" if z3 else None)))

    # Assertions
    assert results[0][1] == True and results[0][2] == "T1_plateau", f"FAIL: plateau case -> {results[0]}"
    assert results[1][1] == False, f"FAIL: improving case should NOT fire -> {results[1]}"
    assert results[2][1] == True and results[2][2] == "T2_zero_interventions", f"FAIL: zero_intv case -> {results[2]}"

    print(f"  Plateau test: fired={results[0][1]}, trigger={results[0][2]} PASS")
    print(f"  Improving test: fired={results[1][1]} (expected False) PASS")
    print(f"  Zero-intv test: fired={results[2][1]}, trigger={results[2][2]} PASS")
    print("  ALL SYNTHETIC TESTS PASS")
    return True


if __name__ == "__main__":
    if "--test" in sys.argv:
        ok = run_synthetic_test()
        sys.exit(0 if ok else 1)
    else:
        entry = run()
        print(f"\nWrote to {OUT}")
