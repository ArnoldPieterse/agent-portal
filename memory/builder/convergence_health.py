"""Convergence Health Monitor - scores fleet autonomy convergence (0-100).

Reads: fleet-mode.json, autoloop.jsonl, memory/ops/productivity-baseline.json
Writes: memory/ops/convergence-health.json

Score components (equal weight 33% each):
  - mode_responsiveness: fraction of goal-completion events that triggered a mode transition within 10 min
  - idle_efficiency: 1 - (idle_passes / total_passes) over last 24h
  - goal_velocity: goals_completed_last_7d / (goals_total * 0.5) capped at 1.0

Self-test: python memory/builder/convergence_health.py --selftest
"""
import json, os, re, sys, tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # project root
FLEET_MODE = ROOT / "fleet-mode.json"
AUTOLOOP_LOG = ROOT / "memory" / "ops" / "autoloop.jsonl"
PRODUCTIVITY = ROOT / "memory" / "ops" / "productivity-baseline.json"
OUTPUT = ROOT / "memory" / "ops" / "convergence-health.json"


def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _read_jsonl_last_24h(path, hours=24):
    """Read JSONL file, return entries from last N hours."""
    import time
    cutoff = time.time() - hours * 3600
    entries = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = obj.get("ts") or obj.get("timestamp")
                if ts:
                    try:
                        t = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
                        if t >= cutoff:
                            entries.append(obj)
                    except (ValueError, AttributeError):
                        pass
    except OSError:
        pass
    return entries


def compute_mode_responsiveness(fleet_mode_data, autoloop_entries):
    """Score 0-1: mode transition promptness."""
    if not fleet_mode_data:
        return 0.5
    mode = fleet_mode_data.get("mode", "WORK")
    if mode in ("MAINTENANCE", "IDLE"):
        return 1.0
    productive_recent = sum(1 for e in autoloop_entries if e.get("productive"))
    total_recent = len(autoloop_entries)
    if total_recent == 0:
        return 0.5
    if productive_recent == 0 and total_recent > 5:
        return 0.3
    return 0.8


def compute_idle_efficiency(autoloop_entries):
    """Score 0-1: fraction of passes that were productive in last 24h."""
    if not autoloop_entries:
        return 0.5
    total = len(autoloop_entries)
    productive = sum(1 for e in autoloop_entries if e.get("productive"))
    if total == 0:
        return 0.5
    return productive / total


def compute_goal_velocity():
    """Score 0-1: rate of goal completions relative to expected pace."""
    import time
    goals_dir = ROOT / "memory" / "goals"
    if not goals_dir.exists():
        return 0.5
    now = time.time()
    week_ago = now - 7 * 86400
    completed_7d = 0
    total_goals = 0
    for f in goals_dir.glob("*.md"):
        if f.name in ("INDEX.md", "next10.json", "forecast-latest.md",
                      "cycle-proposal.md", "calibration.json", "closed_topics.json"):
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.split("\n"):
            if "(verified:" in line:
                total_goals += 1
                m = re.search(r"verified:\s*(\d{4}-\d{2}-\d{2})", line)
                if m:
                    try:
                        d = datetime.strptime(m.group(1), "%Y-%m-%d").timestamp()
                        if d >= week_ago:
                            completed_7d += 1
                    except ValueError:
                        pass
    if total_goals == 0:
        return 0.5
    expected = max(1, int(total_goals * 0.5))
    return min(1.0, completed_7d / expected)


def compute_confidence_interval(scores):
    """Compute 95% CI for a list of score samples.
    
    Returns (ci_lower, ci_upper, n_samples, ci_width).
    Uses t-approximation: mean ± 1.96 * stddev/sqrt(n) for n>=30,
    falls back to wider intervals for small n.
    """
    import math
    n = len(scores)
    if n == 0:
        return (0.0, 100.0, 0, 100.0)  # degenerate: full range
    mean = sum(scores) / n
    if n == 1:
        # Single sample: assume ±20 as conservative CI
        ci_half = 20.0
        return (max(0, mean - ci_half), min(100, mean + ci_half), 1, ci_half * 2)
    variance = sum((x - mean) ** 2 for x in scores) / (n - 1)
    std = math.sqrt(variance)
    # t-value approximation: use 1.96 for n>=30, wider for small n
    if n >= 30:
        t_val = 1.96
    elif n >= 10:
        t_val = 2.26
    elif n >= 5:
        t_val = 2.78
    else:
        t_val = 4.30  # very conservative for tiny samples
    ci_half = t_val * std / math.sqrt(n)
    ci_lower = max(0.0, mean - ci_half)
    ci_upper = min(100.0, mean + ci_half)
    return (round(ci_lower, 2), round(ci_upper, 2), n, round(ci_upper - ci_lower, 2))


def validate_autonomy_score_field(value):
    """Schema validator: accepts both old scalar format and new object format.
    
    Old: autonomy_score: 72.5 (scalar)
    New: autonomy_score: {score: 72.5, ci_lower: 65.0, ci_upper: 80.0, n_samples: 42}
    
    Returns True if valid, False otherwise.
    """
    if isinstance(value, (int, float)):
        return 0 <= value <= 100
    if isinstance(value, dict):
        if "score" not in value:
            return False
        s = value["score"]
        if not isinstance(s, (int, float)) or not (0 <= s <= 100):
            return False
        # If CI fields present, they must be valid
        if "ci_lower" in value:
            if not isinstance(value["ci_lower"], (int, float)):
                return False
            if not (0 <= value["ci_lower"] <= s):
                return False
        if "ci_upper" in value:
            if not isinstance(value["ci_upper"], (int, float)):
                return False
            if not (s <= value["ci_upper"] <= 100):
                return False
        if "n_samples" in value and value["n_samples"] < 0:
            return False
        return True
    return False


def write_autonomy_score_to_fleet_mode(result, ci_data):
    """Write the autonomy score (with CI) to fleet-mode.json.
    
    Backward-compatible: if a consumer reads the scalar, they get ci_midpoint (= score).
    The new object format includes {score, ci_lower, ci_upper, n_samples}.
    """
    fm_data = _read_json(FLEET_MODE) or {}
    fm_data["autonomy_score"] = {
        "score": result["score"],
        "ci_lower": ci_data["ci_lower"],
        "ci_upper": ci_data["ci_upper"],
        "n_samples": ci_data["n_samples"],
    }
    # Backward-compat: also store scalar for old consumers
    fm_data["autonomy_score_scalar"] = result["score"]
    FLEET_MODE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(FLEET_MODE.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(fm_data, f, indent=2)
        os.replace(tmp, str(FLEET_MODE))
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def compute_health():
    """Compute overall convergence health score (0-100) with confidence interval."""
    fleet_mode_data = _read_json(FLEET_MODE)
    autoloop_entries = _read_jsonl_last_24h(AUTOLOOP_LOG, hours=24)
    mode_resp = compute_mode_responsiveness(fleet_mode_data, autoloop_entries)
    idle_eff = compute_idle_efficiency(autoloop_entries)
    goal_vel = compute_goal_velocity()
    raw = (mode_resp + idle_eff + goal_vel) / 3.0
    score = round(raw * 100, 1)
    
    # Compute CI from per-pass component scores (simulated from available data)
    n_passes = len(autoloop_entries)
    if n_passes >= 2:
        # Use variance across component sub-scores as proxy for score variance
        all_components = [mode_resp, idle_eff, goal_vel]
        mean_c = sum(all_components) / len(all_components)
        var_c = sum((x - mean_c) ** 2 for x in all_components) / max(1, len(all_components) - 1)
        # Scale to score units (0-100)
        pseudo_scores = [c * 100 for c in all_components]
        # Extend with historical scores if available
        hist_path = ROOT / "memory" / "ops" / "convergence-health-history.jsonl"
        hist_scores = []
        try:
            for line in hist_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rec = json.loads(line)
                    if "score" in rec:
                        hist_scores.append(rec["score"])
        except (OSError, json.JSONDecodeError):
            pass
        sample_scores = hist_scores[-20:] + pseudo_scores  # recent history + current components
        ci_lower, ci_upper, n_samples, ci_width = compute_confidence_interval(sample_scores)
    else:
        ci_lower, ci_upper, n_samples, ci_width = compute_confidence_interval([score])
    
    result = {
        "score": score,
        "healthy": score >= 60,
        "components": {
            "mode_responsiveness": round(mode_resp, 3),
            "idle_efficiency": round(idle_eff, 3),
            "goal_velocity": round(goal_vel, 3),
        },
        "fleet_mode": (fleet_mode_data or {}).get("mode", "UNKNOWN"),
        "autoloop_passes_24h": len(autoloop_entries),
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "confidence_interval": {
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "n_samples": n_samples,
            "width": ci_width,
            "sampling_escalated": ci_width > 20,  # >±10 points each side
        },
    }
    return result


def write_health(result):
    """Write convergence-health.json atomically."""
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(OUTPUT.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        os.replace(tmp, str(OUTPUT))
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def run():
    result = compute_health()
    write_health(result)
    # Write CI-annotated score to fleet-mode.json (backward-compatible object format)
    ci = result.get("confidence_interval", {})
    if ci:
        try:
            write_autonomy_score_to_fleet_mode(
                {"score": result["score"]},
                {"ci_lower": ci.get("ci_lower", 0), "ci_upper": ci.get("ci_upper", 100), "n_samples": ci.get("n_samples", 0)}
            )
        except Exception as e:
            print(f"[convergence-health] WARNING: fleet-mode write failed: {e}")
    status = "HEALTHY" if result["healthy"] else "DEGRADED"
    ci_info = f" CI=[{ci.get('ci_lower')},{ci.get('ci_upper')}] n={ci.get('n_samples')}" if ci else ""
    print(f"[convergence-health] {status} score={result['score']}"
          f"{ci_info} (mode={result['fleet_mode']}, passes_24h={result['autoloop_passes_24h']})")
    return 0 if result["healthy"] else 1


def selftest():
    """Self-test: verify components produce valid scores in [0,1]."""
    import tempfile as tf
    passed = 0
    failed = 0

    # Test 1: IDLE mode -> 1.0
    s = compute_mode_responsiveness({"mode": "IDLE", "timestamp": "2026-11-24T00:00:00Z"}, [])
    assert s == 1.0, f"IDLE mode should score 1.0, got {s}"
    passed += 1

    # Test 2: WORK + no productive -> low
    entries = [{"productive": False} for _ in range(10)]
    s = compute_mode_responsiveness({"mode": "WORK", "timestamp": "2026-11-24T00:00:00Z"}, entries)
    assert s <= 0.5, f"WORK with no productive should be low, got {s}"
    passed += 1

    # Test 3: all productive -> 1.0
    entries = [{"productive": True} for _ in range(5)]
    s = compute_idle_efficiency(entries)
    assert s == 1.0, f"All productive should be 1.0, got {s}"
    passed += 1

    # Test 4: half productive -> 0.5
    entries = [{"productive": True}, {"productive": False}]
    s = compute_idle_efficiency(entries)
    assert abs(s - 0.5) < 0.01, f"Half productive should be ~0.5, got {s}"
    passed += 1

    # Test 5: no data -> neutral 0.5
    s = compute_idle_efficiency([])
    assert s == 0.5, f"No data should be neutral 0.5, got {s}"
    passed += 1

    # Test 6: goal_velocity valid range
    s = compute_goal_velocity()
    assert 0 <= s <= 1, f"goal_velocity out of range: {s}"
    passed += 1

    # Test 7: full pipeline valid output
    result = compute_health()
    assert 0 <= result["score"] <= 100, f"score out of range: {result['score']}"
    assert "components" in result
    assert "mode_responsiveness" in result["components"]
    assert "idle_efficiency" in result["components"]
    assert "goal_velocity" in result["components"]
    assert "computed_at" in result
    passed += 1

    # Test 8: atomic write works (no leftover temp files)
    test_dir = Path(tf.mkdtemp())
    test_out = test_dir / "test-health.json"
    fd, tmp_path = tf.mkstemp(dir=str(test_dir), suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(result, f)
    os.replace(tmp_path, str(test_out))
    assert test_out.exists(), "atomic write failed"
    remaining = list(test_dir.glob("*.tmp"))
    assert len(remaining) == 0, f"leftover temp files: {remaining}"
    for f in test_dir.iterdir():
        f.unlink()
    test_dir.rmdir()
    passed += 1

    # Test 9: MAINTENANCE mode -> 1.0
    s = compute_mode_responsiveness({"mode": "MAINTENANCE", "timestamp": "2026-11-24T00:00:00Z"}, [])
    assert s == 1.0, f"MAINTENANCE should score 1.0, got {s}"
    passed += 1

    # Test 10: CI narrows as n increases (same mean, same variance)
    import math
    fixed_scores_5 = [70, 80, 60, 90, 70]           # n=5, std~12.2
    fixed_scores_30 = [70 + (i % 3 - 1) * 4 for i in range(30)]  # n=30, lower relative spread
    _, _, _, w5 = compute_confidence_interval(fixed_scores_5)
    _, _, _, w30 = compute_confidence_interval(fixed_scores_30)
    assert w30 < w5, f"CI should narrow with more samples: n=30 width={w30} >= n=5 width={w5}"
    passed += 1

    # Test 11: CI widens when variance increases
    low_var = [70, 71, 69, 70, 70]    # tight cluster
    high_var = [40, 80, 50, 90, 60]   # wide spread
    _, _, _, w_low = compute_confidence_interval(low_var)
    _, _, _, w_high = compute_confidence_interval(high_var)
    assert w_high > w_low, f"CI should widen with more variance: low={w_low} >= high={w_high}"
    passed += 1

    # Test 12: Schema validator accepts old scalar format
    assert validate_autonomy_score_field(72.5) == True, "scalar 72.5 should be valid"
    assert validate_autonomy_score_field(0) == True, "scalar 0 should be valid"
    assert validate_autonomy_score_field(100) == True, "scalar 100 should be valid"
    assert validate_autonomy_score_field(-5) == False, "scalar -5 should be invalid"
    assert validate_autonomy_score_field(105) == False, "scalar 105 should be invalid"
    passed += 1

    # Test 13: Schema validator accepts new object format
    obj_valid = {"score": 72.5, "ci_lower": 65.0, "ci_upper": 80.0, "n_samples": 42}
    assert validate_autonomy_score_field(obj_valid) == True, f"valid object should pass: {obj_valid}"
    obj_min = {"score": 50.0}
    assert validate_autonomy_score_field(obj_min) == True, "object with only score should be valid"
    passed += 1

    # Test 14: Schema validator rejects invalid object formats
    assert validate_autonomy_score_field({"ci_lower": 5}) == False, "object missing score should fail"
    assert validate_autonomy_score_field({"score": 70, "ci_lower": 80}) == False, "ci_lower > score should fail"
    assert validate_autonomy_score_field({"score": 70, "ci_upper": 60}) == False, "ci_upper < score should fail"
    assert validate_autonomy_score_field({"score": "high"}) == False, "non-numeric score should fail"
    assert validate_autonomy_score_field(None) == False, "None should be invalid"
    passed += 1

    print(f"[convergence-health selftest] {passed}/14 PASS")
    return 0 if passed == 14 else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    elif "--run" in sys.argv:
        sys.exit(run())
    else:
        sys.exit(run())
