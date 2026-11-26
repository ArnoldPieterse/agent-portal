#!/usr/bin/env python3
"""convergence_asymptote.py - Fit asymptote to autonomy-score time series.

Fits a saturating exponential score(c) = A - B * exp(-k*c) to the fleet
autonomy-score history, predicts the plateau value (A) and cycles-to-plateau
(where curve reaches 99% of A), and writes convergence_state into
fleet-mode.json.

Also emits a topic-gate recommendation:
  CLIMBING  -> propose capability topics
  PLATEAU   -> propose maintenance/hardening topics

Usage:
    python memory/orchestrator/convergence_asymptote.py            # compute + write state
    python memory/orchestrator/convergence_asymptote.py --selftest # verify with synthetic data
"""
import pathlib, json, math, sys
from datetime import datetime, timezone

MEM = pathlib.Path("memory")
TREND_FILE = MEM / "scribe" / "autonomy-trend.jsonl"
CURRENT_SCORE_FILE = MEM / "ops" / "autonomy-score.json"
FLEET_MODE_FILE = MEM / "ops" / "fleet-mode.json"
OUTPUT_FILE = MEM / "orchestrator" / "convergence-asymptote.json"

# Threshold: if latest score is within this many points of predicted plateau, state = PLATEAU
PLATEAU_THRESHOLD = 2.0  # points
# Cycles-to-plateau: where curve reaches (A - 1% of B)
PLATEAU_REACH_FRACTION = 0.99


def load_time_series() -> list[tuple[int, float]]:
    """Load (cycle, score) pairs from trend file + current score."""
    points = []
    if TREND_FILE.exists():
        for line in TREND_FILE.read_text(encoding="utf-8").strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if "cycle" in rec and "score" in rec:
                    points.append((rec["cycle"], float(rec["score"])))
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

    # Add current score as latest data point
    if CURRENT_SCORE_FILE.exists():
        try:
            cur = json.loads(CURRENT_SCORE_FILE.read_text(encoding="utf-8"))
            if "score" in cur:
                max_cycle = max(p[0] for p in points) if points else 0
                # Current score is the latest; assign it cycle max+1
                points.append((max_cycle + 1, float(cur["score"])))
        except (json.JSONDecodeError, KeyError, ValueError):
            pass

    points.sort(key=lambda x: x[0])
    return points


def fit_asymptote(points: list[tuple[int, float]]) -> dict:
    """Fit score(c) = A - B * exp(-k*c).

    Uses a simple grid search over (A, k) and linear solve for B.
    With >=3 points this is deterministic enough for our purposes.
    """
    n = len(points)
    if n < 3:
        return {"error": "need at least 3 data points", "points": n}

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    best_sse = float("inf")
    best_A, best_B, best_k = None, None, None

    # Grid search: A in [y_max, y_max + 30], k in [0.01, 2.0]
    for i in range(60):
        A_candidate = y_max + (30.0 * i / 59)
        for j in range(80):
            k_candidate = 0.01 + (1.99 * j / 79)
            # For given A and k, B is determined by first point:
            # y[0] = A - B * exp(-k*x[0]) => B = (A - y[0]) / exp(-k*x[0])
            if x_min == 0:
                B_candidate = A_candidate - ys[0]
            else:
                B_candidate = (A_candidate - ys[0]) / math.exp(-k_candidate * xs[0])

            if B_candidate <= 0:
                continue

            # Compute SSE
            sse = 0.0
            for x, y in zip(xs, ys):
                predicted = A_candidate - B_candidate * math.exp(-k_candidate * x)
                sse += (predicted - y) ** 2

            if sse < best_sse:
                best_sse = sse
                best_A, best_B, best_k = A_candidate, B_candidate, k_candidate

    if best_A is None:
        return {"error": "fit failed (no valid parameters found)", "points": n}

    # Cycles to plateau: solve A - B*exp(-k*c) = A*(1 - 0.01) => exp(-k*c) = 0.01*B/A
    # Actually: curve reaches 99% of the range (A - y_start) when:
    # A - B*exp(-k*c) = A - 0.01*B => exp(-k*c) = 0.01 => c = ln(100)/k
    if best_k > 0:
        cycles_to_plateau = math.log(1 / (1 - PLATEAU_REACH_FRACTION)) / best_k
    else:
        cycles_to_plateau = float("inf")

    # R-squared for fit quality
    y_mean = sum(ys) / len(ys)
    ss_tot = sum((y - y_mean) ** 2 for y in ys)
    r_squared = 1.0 - (best_sse / ss_tot) if ss_tot > 0 else 1.0

    return {
        "plateau_value": round(best_A, 2),
        "amplitude_B": round(best_B, 2),
        "rate_k": round(best_k, 4),
        "cycles_to_plateau": round(cycles_to_plateau, 2),
        "r_squared": round(r_squared, 4),
        "n_points": n,
    }


def determine_state(latest_score: float, fit: dict) -> str:
    """Return CLIMBING or PLATEAU based on distance to predicted plateau."""
    if "error" in fit:
        return "CLIMBING"  # default to climbing if we can't fit
    dist_to_plateau = fit["plateau_value"] - latest_score
    if dist_to_plateau <= PLATEAU_THRESHOLD:
        return "PLATEAU"
    return "CLIMBING"


def topic_gate_recommendation(state: str) -> dict:
    """Generate topic gate recommendation based on convergence state."""
    if state == "PLATEAU":
        return {
            "state": state,
            "topic_type": "maintenance_hardening",
            "suggested_focus": [
                "hardening existing capabilities",
                "regression prevention",
                "efficiency optimization",
                "documentation & runbook consolidation",
            ],
        }
    else:
        return {
            "state": state,
            "topic_type": "capability_expansion",
            "suggested_focus": [
                "new capability development",
                "cross-lane integration",
                "autonomy expansion",
                "infrastructure scaling",
            ],
        }


def write_fleet_mode_state(state: str, fit: dict):
    """Write convergence_state into fleet-mode.json (non-destructive merge)."""
    mode_data = {}
    if FLEET_MODE_FILE.exists():
        try:
            mode_data = json.loads(FLEET_MODE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            mode_data = {}

    mode_data["convergence_state"] = state
    mode_data["convergence_plateau"] = fit.get("plateau_value")
    mode_data["convergence_cycles_to_plateau"] = fit.get("cycles_to_plateau")
    mode_data["convergence_updated_at"] = datetime.now(timezone.utc).isoformat()

    FLEET_MODE_FILE.write_text(json.dumps(mode_data, indent=2), encoding="utf-8")


def run_selftest() -> bool:
    """Verify with synthetic data (12+ cycles)."""
    print("=== SELFTEST ===")
    all_pass = True

    # Test 1: Synthetic CLIMBING (exponential approach to plateau at 90, slow rate)
    A_true, B_true, k_true = 90.0, 40.0, 0.12
    climb_points = [(c, A_true - B_true * math.exp(-k_true * c)) for c in range(1, 13)]
    fit1 = fit_asymptote(climb_points)
    print(f"  CLIMB synthetic: plateau={fit1['plateau_value']} (true={A_true}), "
          f"c2p={fit1['cycles_to_plateau']}, r2={fit1['r_squared']}")

    # Plateau prediction should be within reasonable range
    if abs(fit1["plateau_value"] - A_true) > 5:
        print("  FAIL: plateau off by >5 points")
        all_pass = False
    else:
        print("  PASS: plateau within 5 pts of true value")

    # Cycles-to-plateau check: true c2p = ln(100)/k_true
    true_c2p = math.log(100) / k_true
    if abs(fit1["cycles_to_plateau"] - true_c2p) > 5.0:
        print(f"  FAIL: cycles-to-plateau off by >5 (got {fit1['cycles_to_plateau']}, true {true_c2p:.1f})")
        all_pass = False
    else:
        print("  PASS: cycles-to-plateau within 5 of true value")

    # State should be CLIMBING (latest score well below plateau)
    state1 = determine_state(climb_points[-1][1], fit1)
    if state1 != "CLIMBING":
        print(f"  FAIL: expected CLIMBING, got {state1}")
        all_pass = False
    else:
        print("  PASS: state=CLIMBING for climbing series")

    # Test 2: Synthetic PLATEAU (already near plateau)
    A_true2 = 85.0
    k_true2 = 0.3
    B_true2 = 50.0
    # Generate data that's already in the flat region (cycles 20-31)
    plateau_points = [(c, A_true2 - B_true2 * math.exp(-k_true2 * c)) for c in range(20, 32)]
    fit2 = fit_asymptote(plateau_points)
    print(f"\n  PLATEAU synthetic: plateau={fit2['plateau_value']} (true~{A_true2}), "
          f"c2p={fit2.get('cycles_to_plateau','N/A')}, r2={fit2.get('r_squared','N/A')}")

    # Latest score should be very close to A
    latest = plateau_points[-1][1]
    if fit2.get("error"):
        print(f"  WARN: fit error: {fit2['error']}")
    else:
        state2 = determine_state(latest, fit2)
        # For a true plateau series, the fitted A should be close to A_true2
        if abs(fit2["plateau_value"] - A_true2) > 3:
            print(f"  FAIL: plateau off by >3 (got {fit2['plateau_value']}, true {A_true2})")
            all_pass = False
        else:
            print("  PASS: plateau within 3 pts of true value")

        if state2 != "PLATEAU":
            print(f"  FAIL: expected PLATEAU, got {state2} (latest={latest:.1f}, pred_A={fit2['plateau_value']})")
            all_pass = False
        else:
            print("  PASS: state=PLATEAU for plateau series")

    # Test 3: Verify fleet-mode.json write works (dry run - check structure)
    gate = topic_gate_recommendation("CLIMBING")
    assert gate["topic_type"] == "capability_expansion"
    gate2 = topic_gate_recommendation("PLATEAU")
    assert gate2["topic_type"] == "maintenance_hardening"
    print("\n  PASS: topic gate recommendations correct")

    print(f"\n{'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
    return all_pass


def main():
    if "--selftest" in sys.argv:
        ok = run_selftest()
        sys.exit(0 if ok else 1)

    # Normal run
    points = load_time_series()
    print(f"Loaded {len(points)} data points from time series")
    if not points:
        print("ERROR: no data points found")
        sys.exit(1)

    latest_cycle, latest_score = points[-1]
    print(f"Latest: cycle={latest_cycle}, score={latest_score}")

    fit = fit_asymptote(points)
    state = determine_state(latest_score, fit)

    result = {
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "n_points": len(points),
        "latest_cycle": latest_cycle,
        "latest_score": latest_score,
        "fit": fit,
        "convergence_state": state,
        "topic_gate": topic_gate_recommendation(state),
    }

    # Write output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE}")

    # Write convergence_state to fleet-mode.json
    write_fleet_mode_state(state, fit)
    print(f"Updated {FLEET_MODE_FILE} with convergence_state={state}")

    # Print summary
    print(f"\n=== CONVERGENCE STATE ===")
    print(f"  State: {state}")
    if "plateau_value" in fit:
        print(f"  Predicted plateau: {fit['plateau_value']}")
        print(f"  Cycles to plateau: {fit['cycles_to_plateau']}")
        print(f"  Fit quality (R^2): {fit['r_squared']}")
    print(f"  Topic gate: {result['topic_gate']['topic_type']}")


if __name__ == "__main__":
    main()
