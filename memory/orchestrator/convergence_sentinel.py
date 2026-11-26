#!/usr/bin/env python3
"""convergence_sentinel.py - Watch autonomy-score across cycles; auto-open remediation on regression.

Detects a DROP > threshold from the previous cycle (regression, not mere deceleration).
On detection:
  1. Attribute to the responsible lane (component with largest negative delta -> mapped lane).
  2. Auto-open a remediation goal in that lane's goals file.
  3. Write an alert to memory/ops/alerts.jsonl.

Idempotent: will NOT re-open if an alert for this cycle already exists in alerts.jsonl.

Usage:
    python memory/orchestrator/convergence_sentinel.py            # run check
    python memory/orchestrator/convergence_sentinel.py --selftest # verify with synthetic data
"""
import pathlib, json, sys, copy
from datetime import datetime, timezone

MEM = pathlib.Path("memory")
TREND_FILE = MEM / "scribe" / "autonomy-trend.jsonl"
CURRENT_SCORE_FILE = MEM / "ops" / "autonomy-score.json"
ALERTS_FILE = MEM / "ops" / "alerts.jsonl"
GOALS_DIR = MEM / "goals"

# Threshold: a drop of more than this many points is a regression (not mere deceleration)
DROP_THRESHOLD = 5.0

# Component -> responsible lane mapping
COMPONENT_LANE_MAP = {
    "pass_autonomy": "orchestrator",
    "duration_score": "mechanic",
    "rework_score": "builder",
    "trend_score": "scribe",
}


def load_time_series(trend_file: pathlib.Path, current_file: pathlib.Path) -> list[dict]:
    """Load full cycle records from trend file + append current score as latest."""
    records = []
    if trend_file.exists():
        for line in trend_file.read_text(encoding="utf-8").strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if "cycle" in rec and "score" in rec:
                    records.append(rec)
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
    # Append current score as latest point
    if current_file.exists():
        try:
            cur = json.loads(current_file.read_text(encoding="utf-8"))
            if "score" in cur:
                max_cycle = max((r["cycle"] for r in records), default=0)
                prev_score = records[-1]["score"] if records else None
                rec = {
                    "ts": cur.get("computed_at", datetime.now(timezone.utc).isoformat()),
                    "cycle": max_cycle + 1,
                    "score": float(cur["score"]),
                    "delta_from_prev": (float(cur["score"]) - prev_score) if prev_score is not None else None,
                    "component_breakdown": cur.get("components", {}),
                }
                records.append(rec)
        except (json.JSONDecodeError, KeyError, ValueError):
            pass
    records.sort(key=lambda r: r["cycle"])
    return records


def detect_regression(records: list[dict], threshold: float = DROP_THRESHOLD) -> dict | None:
    """Return a regression event dict if latest score dropped > threshold vs previous, else None."""
    if len(records) < 2:
        return None
    prev = records[-2]
    curr = records[-1]
    drop = prev["score"] - curr["score"]
    if drop <= threshold:
        return None
    # Attribution: find component with largest negative delta
    prev_cb = prev.get("component_breakdown", {})
    curr_cb = curr.get("component_breakdown", {})
    worst_component, worst_delta = None, 0.0
    for comp in COMPONENT_LANE_MAP:
        if comp in prev_cb and comp in curr_cb:
            delta = curr_cb[comp] - prev_cb[comp]
            if delta < worst_delta:
                worst_delta = delta
                worst_component = comp
    if worst_component is None:
        worst_component = "pass_autonomy"  # fallback
    lane = COMPONENT_LANE_MAP[worst_component]
    return {
        "cycle": curr["cycle"],
        "prev_cycle": prev["cycle"],
        "prev_score": prev["score"],
        "curr_score": curr["score"],
        "drop": round(drop, 2),
        "threshold": threshold,
        "worst_component": worst_component,
        "component_delta": round(worst_delta, 2),
        "responsible_lane": lane,
    }


def already_alerted(alerts_file: pathlib.Path, cycle: int) -> bool:
    """Check if a convergence_regression alert for this cycle already exists."""
    if not alerts_file.exists():
        return False
    for line in alerts_file.read_text(encoding="utf-8").strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if rec.get("metric") == "convergence_regression" and rec.get("cycle") == cycle:
                return True
        except (json.JSONDecodeError, KeyError):
            continue
    return False


def write_alert(alerts_file: pathlib.Path, event: dict):
    """Append a convergence regression alert to alerts.jsonl."""
    alerts_file.parent.mkdir(parents=True, exist_ok=True)
    alert = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "metric": "convergence_regression",
        "cycle": event["cycle"],
        "severity": "critical",
        "drop_pts": event["drop"],
        "responsible_lane": event["responsible_lane"],
        "worst_component": event["worst_component"],
        "recommended_action": f"Review {event['responsible_lane']} lane for changes in cycle {event['prev_cycle']} that degraded {event['worst_component']}.",
    }
    with alerts_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(alert) + "\n")


def open_remediation_goal(goals_dir: pathlib.Path, lane: str, event: dict) -> bool:
    """Append a remediation goal to the responsible lane's goals file. Returns True if written."""
    goals_file = goals_dir / f"{lane}.md"
    if not goals_file.exists():
        return False
    content = goals_file.read_text(encoding="utf-8")
    # Idempotency: don't add if this exact remediation is already present
    marker = f"[SENTINEL:{event['cycle']}]"
    if marker in content:
        return False
    goal_line = (
        f"\n> [SENTINEL:{event['cycle']}] **Auto-remediation: {event['worst_component']} regression** "
        f"(dropped {event['drop']}pts cycle {event['prev_cycle']}->{event['cycle']}) - "
        f"Diagnose root cause of {event['worst_component']} degradation; restore to prior level within 1 cycle. "
        f"Output: evidence in memory/{lane}/sentinel-remediation-cycle{event['cycle']}.md."
    )
    goals_file.write_text(content.rstrip() + goal_line + "\n", encoding="utf-8")
    return True


def run(trend_file=None, current_file=None, alerts_file=None, goals_dir=None,
        threshold=DROP_THRESHOLD) -> dict:
    """Main entry. Returns result dict."""
    tf = trend_file or TREND_FILE
    cf = current_file or CURRENT_SCORE_FILE
    af = alerts_file or ALERTS_FILE
    gd = goals_dir or GOALS_DIR
    th = threshold

    records = load_time_series(tf, cf)
    if len(records) < 2:
        return {"status": "insufficient_data", "points": len(records)}

    event = detect_regression(records, th)
    if event is None:
        return {"status": "ok", "latest_cycle": records[-1]["cycle"], "score": records[-1]["score"]}

    # Idempotency check
    if already_alerted(af, event["cycle"]):
        return {"status": "already_alerted", "event": event}

    write_alert(af, event)
    goal_written = open_remediation_goal(gd, event["responsible_lane"], event)
    return {"status": "regression_detected", "event": event, "goal_opened": goal_written}


# ─── SELF-TEST ───────────────────────────────────────────────────────────────────

def selftest():
    import tempfile, os
    results = []

    # --- Test 1: Synthetic 8pt drop -> exactly one alert + one remediation goal ---
    with tempfile.TemporaryDirectory() as tmp:
        tf = pathlib.Path(tmp) / "trend.jsonl"
        cf = pathlib.Path(tmp) / "current.json"
        af = pathlib.Path(tmp) / "alerts.jsonl"
        gd = pathlib.Path(tmp) / "goals"
        gd.mkdir()

        # 3 cycles: 70 -> 75 -> 67 (8pt drop from 75)
        records = [
            {"cycle": 1, "score": 70.0, "component_breakdown": {"pass_autonomy": 60, "duration_score": 80, "rework_score": 90, "trend_score": 50}},
            {"cycle": 2, "score": 75.0, "component_breakdown": {"pass_autonomy": 65, "duration_score": 82, "rework_score": 92, "trend_score": 50}},
            {"cycle": 3, "score": 67.0, "component_breakdown": {"pass_autonomy": 48, "duration_score": 81, "rework_score": 91, "trend_score": 50}},
        ]
        tf.write_text("\n".join(json.dumps(r) for r in records[:2]), encoding="utf-8")
        # Current score = cycle 3
        cf.write_text(json.dumps({"score": 67.0, "components": records[2]["component_breakdown"]}), encoding="utf-8")
        # Create a lane goals file for the expected responsible lane (pass_autonomy -> orchestrator)
        (gd / "orchestrator.md").write_text("# Orchestrator Goals\n\n1. **Existing goal** - test\n", encoding="utf-8")

        result = run(tf, cf, af, gd, threshold=5.0)
        assert result["status"] == "regression_detected", f"T1: expected regression_detected, got {result['status']}"
        ev = result["event"]
        assert ev["drop"] == 8.0, f"T1: expected drop=8.0, got {ev['drop']}"
        assert ev["responsible_lane"] == "orchestrator", f"T1: expected orchestrator, got {ev['responsible_lane']}"
        assert result["goal_opened"] is True, f"T1: expected goal_opened=True"

        # Verify alert written (exactly 1)
        alerts = [json.loads(l) for l in af.read_text(encoding="utf-8").strip().split("\n") if l.strip()]
        reg_alerts = [a for a in alerts if a.get("metric") == "convergence_regression"]
        assert len(reg_alerts) == 1, f"T1: expected 1 alert, got {len(reg_alerts)}"

        # Verify goal appended (exactly 1 sentinel marker)
        goal_content = (gd / "orchestrator.md").read_text(encoding="utf-8")
        assert goal_content.count("[SENTINEL:3]") == 1, f"T1: expected exactly 1 sentinel marker"

        # Idempotency: re-run should NOT duplicate
        result2 = run(tf, cf, af, gd, threshold=5.0)
        assert result2["status"] == "already_alerted", f"T1 idempotent: expected already_alerted, got {result2['status']}"
        alerts2 = [json.loads(l) for l in af.read_text(encoding="utf-8").strip().split("\n") if l.strip()]
        reg_alerts2 = [a for a in alerts2 if a.get("metric") == "convergence_regression"]
        assert len(reg_alerts2) == 1, f"T1 idempotent: expected still 1 alert, got {len(reg_alerts2)}"

        results.append(("T1: 8pt drop -> 1 alert + 1 goal + idempotent", "PASS"))

    # --- Test 2: Steady/accelerating series -> no alert ---
    with tempfile.TemporaryDirectory() as tmp:
        tf = pathlib.Path(tmp) / "trend.jsonl"
        cf = pathlib.Path(tmp) / "current.json"
        af = pathlib.Path(tmp) / "alerts.jsonl"
        gd = pathlib.Path(tmp) / "goals"
        gd.mkdir()

        # Accelerating: 60 -> 65 -> 72
        records = [
            {"cycle": 1, "score": 60.0, "component_breakdown": {"pass_autonomy": 50, "duration_score": 75, "rework_score": 88, "trend_score": 50}},
            {"cycle": 2, "score": 65.0, "component_breakdown": {"pass_autonomy": 55, "duration_score": 78, "rework_score": 90, "trend_score": 50}},
        ]
        tf.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
        cf.write_text(json.dumps({"score": 72.0, "components": {"pass_autonomy": 62, "duration_score": 80, "rework_score": 92, "trend_score": 50}}), encoding="utf-8")

        result = run(tf, cf, af, gd, threshold=5.0)
        assert result["status"] == "ok", f"T2: expected ok, got {result['status']}"
        # No alert file created or empty
        if af.exists():
            content = af.read_text(encoding="utf-8").strip()
            assert content == "" or "convergence_regression" not in content, f"T2: unexpected alert"

        results.append(("T2: accelerating series -> no alert", "PASS"))

    # --- Test 3: Attribution correctness (duration_score drop -> mechanic) ---
    with tempfile.TemporaryDirectory() as tmp:
        tf = pathlib.Path(tmp) / "trend.jsonl"
        cf = pathlib.Path(tmp) / "current.json"
        af = pathlib.Path(tmp) / "alerts.jsonl"
        gd = pathlib.Path(tmp) / "goals"
        gd.mkdir()

        # Drop driven by duration_score: 80 -> 65 (15pt component drop)
        records = [
            {"cycle": 1, "score": 72.0, "component_breakdown": {"pass_autonomy": 64, "duration_score": 80, "rework_score": 92, "trend_score": 50}},
        ]
        tf.write_text(json.dumps(records[0]), encoding="utf-8")
        cf.write_text(json.dumps({"score": 64.0, "components": {"pass_autonomy": 63, "duration_score": 65, "rework_score": 91, "trend_score": 50}}), encoding="utf-8")
        (gd / "mechanic.md").write_text("# Mechanic Goals\n\n1. **Existing** - test\n", encoding="utf-8")

        result = run(tf, cf, af, gd, threshold=5.0)
        assert result["status"] == "regression_detected", f"T3: expected regression_detected, got {result['status']}"
        assert result["event"]["responsible_lane"] == "mechanic", f"T3: expected mechanic, got {result['event']['responsible_lane']}"
        assert result["event"]["worst_component"] == "duration_score", f"T3: expected duration_score, got {result['event']['worst_component']}"

        results.append(("T3: duration_score drop -> mechanic attribution", "PASS"))

    # --- Test 4: Small drop (below threshold) -> no alert ---
    with tempfile.TemporaryDirectory() as tmp:
        tf = pathlib.Path(tmp) / "trend.jsonl"
        cf = pathlib.Path(tmp) / "current.json"
        af = pathlib.Path(tmp) / "alerts.jsonl"
        gd = pathlib.Path(tmp) / "goals"
        gd.mkdir()

        # 72 -> 69 (3pt drop, below 5pt threshold)
        records = [
            {"cycle": 1, "score": 72.0, "component_breakdown": {"pass_autonomy": 64, "duration_score": 80, "rework_score": 92, "trend_score": 50}},
        ]
        tf.write_text(json.dumps(records[0]), encoding="utf-8")
        cf.write_text(json.dumps({"score": 69.0, "components": {"pass_autonomy": 62, "duration_score": 79, "rework_score": 91, "trend_score": 50}}), encoding="utf-8")

        result = run(tf, cf, af, gd, threshold=5.0)
        assert result["status"] == "ok", f"T4: expected ok (below threshold), got {result['status']}"

        results.append(("T4: 3pt drop (below threshold) -> no alert", "PASS"))

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
    print(json.dumps(result, indent=2))
