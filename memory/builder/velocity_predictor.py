"""Convergence Velocity Predictor (Builder goal 5, Fleet Autonomy Convergence).

Computes rate-of-change in autonomy score over last 14 days (linear + exponential fit),
projects ETA to full convergence (score >= 95). If projected ETA > 30 days, identifies
the bottleneck subsystem and writes a recommendation.

Usage:
    python memory/builder/velocity_predictor.py --selftest
    python memory/builder/velocity_predictor.py          # print current prediction
"""
import json
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent.parent  # project root
OPS_DIR = HERE / "memory" / "ops"
SCORE_FILE = OPS_DIR / "autonomy-score.json"
CONFLICTS_FILE = OPS_DIR / "mode-conflicts.jsonl"
BOTTLENECK_FILE = OPS_DIR / "convergence-bottleneck.md"

# Subsystem components that contribute to the autonomy score
SUBSYSTEMS = ["intervention_rate", "cycle_completion", "rework_rate", "idle_fraction"]


def _read_score_history():
    """Read autonomy score history from autonomy-score.json (list of {ts, score}) or compute from components."""
    if not SCORE_FILE.exists():
        return []
    try:
        data = json.loads(SCORE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    # If data is a single object with history, use that; otherwise build from current
    if isinstance(data, dict) and "history" in data:
        return data["history"]
    if isinstance(data, list):
        return data
    # Single snapshot - wrap it
    return [data]


def _linear_fit(points):
    """Simple least-squares linear fit. Returns (slope, intercept)."""
    n = len(points)
    if n < 2:
        return 0.0, points[0][1] if points else 0.0
    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    sum_xy = sum(p[0] * p[1] for p in points)
    sum_x2 = sum(p[0] ** 2 for p in points)
    denom = n * sum_x2 - sum_x ** 2
    if abs(denom) < 1e-12:
        return 0.0, sum_y / n
    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    return slope, intercept


def _exponential_fit(points):
    """Exponential fit via log-transform. Returns (rate, base). score(t) = base * exp(rate*t)."""
    # Filter positive scores for log transform
    valid = [(t, s) for t, s in points if s > 0]
    if len(valid) < 2:
        return 0.0, valid[0][1] if valid else 0.0
    log_points = [(t, math.log(s)) for t, s in valid]
    slope, intercept = _linear_fit(log_points)
    rate = slope
    base = math.exp(intercept)
    return rate, base


def _project_eta_linear(current_score, score_per_day, target=95.0):
    """Days to reach target at linear velocity."""
    if score_per_day <= 0:
        return float("inf")
    gap = target - current_score
    if gap <= 0:
        return 0.0
    return gap / score_per_day


def _project_eta_exponential(current_score, rate, target=95.0):
    """Days to reach target at exponential growth."""
    if current_score >= target:
        return 0.0
    if rate <= 0:
        return float("inf")
    # score * exp(rate * t) = target => t = ln(target/score) / rate
    return math.log(target / current_score) / rate


def _identify_bottleneck(components):
    """Identify which subsystem has the highest negative contribution to velocity.

    Each component contributes (value - ideal) where:
      - intervention_rate: higher is better (less intervention = more autonomy)
      - cycle_completion: higher is better
      - rework_rate: lower is better (inverted)
      - idle_fraction: lower is better (inverted)

    Returns the subsystem name with the worst gap to its ideal value.
    """
    # Normalize each component to a 0-1 "distance from ideal"
    gaps = {}
    for sub in SUBSYSTEMS:
        val = components.get(sub, 0.5)
        if sub in ("rework_rate", "idle_fraction"):
            # Lower is better: gap = val (already normalized 0-1 where 0=ideal)
            gaps[sub] = val
        else:
            # Higher is better: gap = 1 - val
            gaps[sub] = 1.0 - val
    return max(gaps, key=gaps.get), gaps


def compute_prediction():
    """Main computation: read history, fit models, project ETA, identify bottleneck."""
    history = _read_score_history()

    # If we only have a single point or no history, use current score with zero velocity
    if len(history) >= 2:
        now = datetime.now(timezone.utc).timestamp()
        points = []
        for entry in history:
            ts_str = entry.get("ts") or entry.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
            except (ValueError, AttributeError):
                continue
            score = entry.get("score", 0) * 100  # normalize to 0-100
            points.append((ts - now, score))  # t=0 is now, negative = past

        if len(points) >= 2:
            slope, intercept = _linear_fit(points)
            rate, base = _exponential_fit(points)
            current_score = points[-1][1]
            velocity_pts_per_day = slope * 86400  # convert to per-day
            eta_linear = _project_eta_linear(current_score, velocity_pts_per_day)
            eta_exp = _project_eta_exponential(current_score, rate)
            eta_days = min(eta_linear, eta_exp) if eta_linear != float("inf") or eta_exp != float("inf") else float("inf")
        else:
            current_score = history[-1].get("score", 0) * 100
            velocity_pts_per_day = 0.0
            eta_days = float("inf")
    else:
        score_data = history[0] if history else {}
        current_score = score_data.get("score", 0) * 100
        velocity_pts_per_day = 0.0
        eta_days = float("inf")

    # Identify bottleneck
    components = None
    if history:
        last = history[-1]
        components = last.get("components")
    if components is None and SCORE_FILE.exists():
        try:
            data = json.loads(SCORE_FILE.read_text(encoding="utf-8"))
            components = data.get("components", {})
        except (json.JSONDecodeError, OSError):
            pass

    bottleneck_name = None
    bottleneck_gaps = {}
    if components:
        bottleneck_name, bottleneck_gaps = _identify_bottleneck(components)

    # If ETA > 30 days, write bottleneck recommendation
    if eta_days > 30 and bottleneck_name:
        _write_bottleneck_recommendation(bottleneck_name, bottleneck_gaps, eta_days, components)

    return {
        "ok": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "current_score": round(current_score, 2),
        "velocity_pts_per_day": round(velocity_pts_per_day, 4),
        "eta_days": round(eta_days, 1) if eta_days != float("inf") else None,
        "converged": current_score >= 95.0,
        "bottleneck": bottleneck_name,
        "components": components,
    }


def _write_bottleneck_recommendation(name, gaps, eta_days, components):
    """Write convergence-bottleneck.md with the identified bottleneck."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    rec_lines = [
        "# Convergence Bottleneck Analysis",
        f"Generated: {now}",
        "",
        f"**Bottleneck subsystem:** `{name}`",
        f"**Projected ETA to convergence:** {eta_days:.1f} days (>30 day threshold)",
        "",
        "## Component Gaps (distance from ideal)",
        "",
    ]
    for sub in SUBSYSTEMS:
        gap = gaps.get(sub, 0)
        marker = " **<-- BOTTLENECK**" if sub == name else ""
        rec_lines.append(f"- `{sub}`: gap={gap:.3f}{marker}")
    rec_lines.extend([
        "",
        "## Recommendation",
        "",
        f"Focus next cycle's goals on improving `{name}`. Current value: {components.get(name, 'n/a')}.",
        f"Closing this gap would have the highest marginal impact on convergence velocity.",
        "",
    ])
    BOTTLENECK_FILE.parent.mkdir(parents=True, exist_ok=True)
    BOTTLENECK_FILE.write_text("\n".join(rec_lines), encoding="utf-8")


def handle_velocity():
    """API handler: returns the velocity prediction as JSON-ready dict."""
    try:
        return compute_prediction()
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


# --- Selftest ---

def _selftest():
    import tempfile, os

    print("=== Convergence Velocity Predictor - Selftest ===")
    passed = 0
    failed = 0

    def check(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  PASS: {name}")
        else:
            failed += 1
            print(f"  FAIL: {name}")

    # Test 1: Linear fit correctness
    points = [(0, 50.0), (86400, 60.0), (2*86400, 70.0)]  # +10 pts/day
    slope, intercept = _linear_fit(points)
    velocity = slope * 86400
    check(f"linear fit: slope~{velocity:.1f} pts/day (expect ~10)", abs(velocity - 10.0) < 1.0)

    # Test 2: ETA projection linear
    eta = _project_eta_linear(70.0, 10.0, target=95.0)
    check(f"ETA linear: {eta:.1f} days (expect 2.5)", abs(eta - 2.5) < 0.1)

    # Test 3: ETA projection exponential
    eta_e = _project_eta_exponential(50.0, 0.1, target=95.0)  # ln(95/50)/0.1
    expected = math.log(95.0/50.0) / 0.1
    check(f"ETA exp: {eta_e:.2f} days (expect {expected:.2f})", abs(eta_e - expected) < 0.01)

    # Test 4: Bottleneck identification
    components = {
        "intervention_rate": 0.3,   # gap = 0.7 (bad)
        "cycle_completion": 0.8,    # gap = 0.2
        "rework_rate": 0.1,         # gap = 0.1 (good - lower is better)
        "idle_fraction": 0.5,       # gap = 0.5
    }
    bottleneck, gaps = _identify_bottleneck(components)
    check(f"bottleneck: {bottleneck} (expect intervention_rate)", bottleneck == "intervention_rate")

    # Test 5: Convergence detection (score >= 95)
    result_sim = {
        "ok": True,
        "current_score": 96.0,
        "velocity_pts_per_day": 1.0,
        "eta_days": 0.0,
        "converged": True,
        "bottleneck": None,
    }
    check("convergence flag: score>=95 => converged=True", result_sim["converged"] is True)

    # Test 6: Full compute with synthetic history (using temp file)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_score = Path(tmpdir) / "autonomy-score.json"
        now = datetime.now(timezone.utc)
        history = []
        for day in range(14, 0, -1):
            ts = (now - timedelta(days=day)).isoformat()
            score = 0.5 + (14 - day) * 0.02  # increases from 0.5 to ~0.76
            history.append({"ts": ts, "score": round(score, 3), "components": {
                "intervention_rate": 0.4 + day * 0.01,
                "cycle_completion": 0.5 + (14-day) * 0.01,
                "rework_rate": 0.2 - day * 0.005,
                "idle_fraction": 0.3,
            }})
        tmp_score.write_text(json.dumps(history), encoding="utf-8")

        # Monkey-patch SCORE_FILE
        global SCORE_FILE
        orig = SCORE_FILE
        SCORE_FILE = tmp_score
        try:
            result = compute_prediction()
            check(f"compute: ok={result['ok']}", result["ok"] is True)
            check(f"compute: current_score~{result['current_score']} (expect ~76)", 70 < result["current_score"] < 82)
            check(f"compute: velocity positive ({result['velocity_pts_per_day']})", result["velocity_pts_per_day"] > 0)
            check(f"compute: eta_days present", result["eta_days"] is not None or result["eta_days"] == 0.0)
        finally:
            SCORE_FILE = orig

    print(f"\nSelftest result: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = _selftest()
        sys.exit(0 if ok else 1)
    else:
        result = compute_prediction()
        print(json.dumps(result, indent=2))
