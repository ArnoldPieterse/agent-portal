#!/usr/bin/env python3
"""forecast_calibration.py - Track next10.json forecast accuracy per lane; compute Brier score + calibration.

Compares predicted p_reached (from next10.json) against actual outcomes (reached or not)
to measure forecast calibration. Flags miscalibrated lanes and feeds residual back into
dispatch weighting.

Brier score = mean((predicted - actual)^2) where actual is 1 if reached, 0 otherwise.
A perfect forecaster has Brier=0; a random guess averages ~0.25.

Usage:
    python memory/orchestrator/forecast_calibration.py            # compute + write
    python memory/orchestrator/forecast_calibration.py --selftest # verify with synthetic data
"""
import pathlib, json, re, sys
from datetime import datetime, timezone

MEM = pathlib.Path("memory")
NEXT10_FILE = MEM / "goals" / "next10.json"
GOALS_DIR = MEM / "goals"
OUTPUT_FILE = MEM / "ops" / "forecast-calibration.json"


def load_predictions(next10_file: pathlib.Path) -> list[dict]:
    """Load predictions from next10.json. Returns list of {agent, goal_title, p_reached}."""
    if not next10_file.exists():
        return []
    try:
        data = json.loads(next10_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, KeyError):
        return []
    predictions = []
    for item in data.get("next10", []):
        predictions.append({
            "agent": item.get("agent", "unknown"),
            "goal_title": item.get("title", item.get("goal", "")[:60]),
            "p_reached": item.get("p_reached", 0.5),
        })
    return predictions


def check_outcomes(predictions: list[dict], goals_dir: pathlib.Path) -> list[dict]:
    """For each prediction, check if the goal has been reached in the lane's goals file."""
    outcomes = []
    for pred in predictions:
        agent = pred["agent"]
        title = pred["goal_title"]
        gf = goals_dir / f"{agent}.md"
        reached = False
        if gf.exists():
            content = gf.read_text(encoding="utf-8")
            # Check if a goal with this title has a (verified: marker
            # Simplified: check if the title keywords appear on a verified line
            title_words = re.findall(r'[A-Za-z]{4,}', title.lower())
            for line in content.split("\n"):
                if "(verified:" in line:
                    line_lower = line.lower()
                    # If at least 2 significant words from the title appear on a verified line
                    matches = sum(1 for w in title_words if w in line_lower)
                    if len(title_words) > 0 and matches / len(title_words) > 0.5:
                        reached = True
                        break
        outcomes.append({
            **pred,
            "actual": 1 if reached else 0,
            "reached": reached,
        })
    return outcomes


def brier_score(outcomes: list[dict]) -> float:
    """Compute Brier score: mean((predicted - actual)^2)."""
    if not outcomes:
        return 0.0
    sse = sum((o["p_reached"] - o["actual"]) ** 2 for o in outcomes)
    return round(sse / len(outcomes), 4)


def per_lane_brier(outcomes: list[dict]) -> dict:
    """Compute Brier score per lane."""
    lanes = {}
    for o in outcomes:
        agent = o["agent"]
        if agent not in lanes:
            lanes[agent] = []
        lanes[agent].append(o)

    result = {}
    for agent, items in sorted(lanes.items()):
        score = brier_score(items)
        n = len(items)
        hit_rate = sum(i["actual"] for i in items) / n if n > 0 else 0
        avg_predicted = sum(i["p_reached"] for i in items) / n if n > 0 else 0
        result[agent] = {
            "brier": score,
            "n_predictions": n,
            "avg_predicted": round(avg_predicted, 3),
            "actual_hit_rate": round(hit_rate, 3),
            "calibration_gap": round(avg_predicted - hit_rate, 3),
        }
    return result


def flag_miscalibrated(per_lane: dict, threshold: float = 0.15) -> list[dict]:
    """Flag lanes where |calibration_gap| > threshold (systematically over/under-forecasting)."""
    flagged = []
    for agent, data in per_lane.items():
        if abs(data["calibration_gap"]) > threshold:
            direction = "over-forecasting" if data["calibration_gap"] > 0 else "under-forecasting"
            flagged.append({
                "agent": agent,
                "gap": data["calibration_gap"],
                "direction": direction,
                "weight_adjustment": -data["calibration_gap"],  # feed back: reduce weight for over-forecasters
            })
    return flagged


def run(next10_file=None, goals_dir=None, output_file=None) -> dict:
    """Main entry."""
    nf = next10_file or NEXT10_FILE
    gd = goals_dir or GOALS_DIR
    of = output_file or OUTPUT_FILE

    predictions = load_predictions(nf)
    if not predictions:
        return {"status": "no_predictions", "detail": f"{nf} not found or empty"}

    outcomes = check_outcomes(predictions, gd)
    overall_brier = brier_score(outcomes)
    per_lane = per_lane_brier(outcomes)
    flagged = flag_miscalibrated(per_lane)

    result = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "status": "ok",
        "n_predictions": len(predictions),
        "n_reached": sum(1 for o in outcomes if o["reached"]),
        "overall_brier": overall_brier,
        "per_lane": per_lane,
        "miscalibrated_lanes": flagged,
        "interpretation": {
            "brier_0": "perfect foresight",
            "brier_0.25": "random guess (coin flip)",
            "brier_1.0": "worst possible (always wrong)",
        },
    }

    of.parent.mkdir(parents=True, exist_ok=True)
    of.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


# ─── SELF-TEST ───────────────────────────────────────────────────────────────────

def selftest():
    import tempfile
    results = []

    # --- Test 1: Known-bad forecaster is flagged ---
    with tempfile.TemporaryDirectory() as tmp:
        nf = pathlib.Path(tmp) / "next10.json"
        gd = pathlib.Path(tmp) / "goals"
        of = pathlib.Path(tmp) / "output.json"
        gd.mkdir()

        # Agent 'good' predicts 0.9 and always reaches (well calibrated)
        # Agent 'bad' predicts 0.9 but never reaches (severely over-forecasting)
        next10_data = {
            "next10": [
                {"agent": "good", "title": "Alpha Goal One", "p_reached": 0.9},
                {"agent": "good", "title": "Beta Goal Two", "p_reached": 0.85},
                {"agent": "bad", "title": "Gamma Goal Three", "p_reached": 0.9},
                {"agent": "bad", "title": "Delta Goal Four", "p_reached": 0.88},
            ]
        }
        nf.write_text(json.dumps(next10_data), encoding="utf-8")

        # good agent: both goals reached (verified markers present)
        (gd / "good.md").write_text(
            "# Good\n1. **Alpha Goal One** - work (verified: done)\n2. **Beta Goal Two** - work (verified: done)\n",
            encoding="utf-8"
        )
        # bad agent: neither goal reached
        (gd / "bad.md").write_text(
            "# Bad\n1. **Gamma Goal Three** - still open\n2. **Delta Goal Four** - still open\n",
            encoding="utf-8"
        )

        result = run(nf, gd, of)
        assert result["status"] == "ok", f"T1: expected ok, got {result['status']}"
        assert result["n_reached"] == 2, f"T1: expected 2 reached, got {result['n_reached']}"

        # 'bad' lane should be flagged as over-forecasting
        per_lane = result["per_lane"]
        assert "bad" in per_lane, f"T1: missing 'bad' lane"
        assert per_lane["bad"]["calibration_gap"] > 0.5, f"T1: bad gap should be >0.5, got {per_lane['bad']['calibration_gap']}"
        flagged_agents = [f["agent"] for f in result["miscalibrated_lanes"]]
        assert "bad" in flagged_agents, f"T1: 'bad' not in flagged lanes: {flagged_agents}"

        # Brier score should be > 0.2 (worse than random) because of the bad forecaster
        assert result["overall_brier"] > 0.15, f"T1: Brier too low for known-bad: {result['overall_brier']}"

        results.append(("T1: known-bad forecaster flagged + Brier score elevated", "PASS"))

    # --- Test 2: Perfect forecaster -> Brier ~0, no flags ---
    with tempfile.TemporaryDirectory() as tmp:
        nf = pathlib.Path(tmp) / "next10.json"
        gd = pathlib.Path(tmp) / "goals"
        of = pathlib.Path(tmp) / "output.json"
        gd.mkdir()

        # All predictions match outcomes perfectly
        next10_data = {
            "next10": [
                {"agent": "perfect", "title": "Goal Alpha Hit", "p_reached": 1.0},
                {"agent": "perfect", "title": "Goal Beta Miss", "p_reached": 0.0},
            ]
        }
        nf.write_text(json.dumps(next10_data), encoding="utf-8")
        (gd / "perfect.md").write_text(
            "# Perfect\n1. **Goal Alpha Hit** - done (verified: yes)\n2. **Goal Beta Miss** - not done\n",
            encoding="utf-8"
        )

        result = run(nf, gd, of)
        assert result["overall_brier"] < 0.01, f"T2: Brier should be ~0 for perfect, got {result['overall_brier']}"
        assert len(result["miscalibrated_lanes"]) == 0, f"T2: no lanes should be flagged, got {result['miscalibrated_lanes']}"

        results.append(("T2: perfect forecaster -> Brier~0, no flags", "PASS"))

    # --- Test 3: Feeding residual raises dispatch precision (weight adjustment) ---
    with tempfile.TemporaryDirectory() as tmp:
        nf = pathlib.Path(tmp) / "next10.json"
        gd = pathlib.Path(tmp) / "goals"
        of = pathlib.Path(tmp) / "output.json"
        gd.mkdir()

        # Over-forecaster: predicts 0.9 but only hits 0/2 -> gap=+0.9, weight_adj=-0.9
        next10_data = {
            "next10": [
                {"agent": "over", "title": "Goal X One", "p_reached": 0.9},
                {"agent": "over", "title": "Goal Y Two", "p_reached": 0.9},
            ]
        }
        nf.write_text(json.dumps(next10_data), encoding="utf-8")
        (gd / "over.md").write_text("# Over\n1. **Goal X One** - open\n2. **Goal Y Two** - open\n", encoding="utf-8")

        result = run(nf, gd, of)
        flagged = result["miscalibrated_lanes"]
        assert len(flagged) == 1 and flagged[0]["agent"] == "over"
        # Weight adjustment should be negative (reduce dispatch weight for over-forecasters)
        assert flagged[0]["weight_adjustment"] < 0, f"T3: weight_adj should be negative, got {flagged[0]['weight_adjustment']}"
        # The residual (negative) means: this lane's goals should be weighted HIGHER
        # in next dispatch because they were under-delivered relative to prediction
        assert flagged[0]["direction"] == "over-forecasting"

        results.append(("T3: miscalibrated lane gets negative weight adjustment (dispatch feedback)", "PASS"))

    # --- Test 4: No predictions -> graceful handling ---
    with tempfile.TemporaryDirectory() as tmp:
        nf = pathlib.Path(tmp) / "next10.json"
        gd = pathlib.Path(tmp) / "goals"
        of = pathlib.Path(tmp) / "output.json"
        gd.mkdir()

        # Empty file
        nf.write_text("{}", encoding="utf-8")

        result = run(nf, gd, of)
        assert result["status"] == "no_predictions", f"T4: expected no_predictions, got {result['status']}"

        results.append(("T4: empty predictions -> graceful 'no_predictions' status", "PASS"))

    # Print results
    all_pass = True
    for name, status in results:
        print(f"  [{status}] {name}")
        if status != "PASS":
            all_pass = False
    print(f"\n{'ALL PASS' if all_pass else 'FAILURES DETECTED'} ({len(results)} tests)")
    return all_pass


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    result = run()
    print(json.dumps({k: result[k] for k in ['status', 'n_predictions', 'n_reached', 'overall_brier'] if k in result}, indent=2))
    if "miscalibrated_lanes" in result:
        print(f"Miscalibrated lanes: {[f['agent'] for f in result['miscalibrated_lanes']]}")
    print(f"\nFull output: {OUTPUT_FILE}")
