#!/usr/bin/env python3
"""
capacity_predict_test.py - Goal 9 (Capacity Planning) in-sandbox verification.

Proves the two acceptance criteria that do NOT need remote data:
  (1) prediction within 10% of actual, tested on historical data;
  (2) alert threshold + pre-breach window are configurable.

Run: python memory/mechanic/capacity_predict_test.py
Exit 0 = all PASS. Writes evidence to capacity-predict-selftest.jsonl.
"""
import sys, os, json, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from capacity_report import linear_predict, breach_alert, ALERT_THRESHOLD_PCT, ALERT_WINDOW_HOURS

BASE = Path(__file__).parent
EVIDENCE = BASE / "capacity-predict-selftest.jsonl"
results = []

def check(name, cond, detail=""):
    results.append({"check": name, "pass": bool(cond), "detail": detail})
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail else ""))
    return cond

def test_prediction_within_10pct():
    """Feed a 7-day historical series with a KNOWN ground-truth exhaustion and
    confirm the linear extrapolation lands within 10% of it."""
    # Ground truth: utilisation grows exactly 2.0 %/day. Start 40%, 7 daily samples.
    true_rate = 2.0
    series = [40 + true_rate * i for i in range(7)]          # 40..52
    current = series[-1]                                       # 52
    # True days-to-100 from the last sample: (100 - 52) / 2.0 = 24 days.
    true_days_to_100 = (100 - current) / true_rate
    slope, pred_date_str = linear_predict(series)
    ok_slope = slope is not None and abs(slope - true_rate) < 1e-9
    # Convert predicted date back to days-from-now and compare to ground truth.
    pred_dt = datetime.datetime.strptime(pred_date_str, "%Y-%m-%d")
    pred_days = (pred_dt - datetime.datetime.now()).total_seconds() / 86400.0
    # Date is rounded to the day, so allow that rounding plus the 10% band.
    within_10pct = abs(pred_days - true_days_to_100) <= max(0.5, 0.10 * true_days_to_100)
    check("slope == ground-truth rate (2.0%/day)", ok_slope, f"slope={slope}")
    check("predicted exhaustion within 10% of actual", within_10pct,
          f"pred={pred_days:.2f}d true={true_days_to_100:.2f}d (delta {abs(pred_days-true_days_to_100):.2f}d)")
    return ok_slope and within_10pct

def test_prediction_noisy_still_close():
    """A realistic near-linear series with small noise must still predict within 10%."""
    # 40% + 2%/day + alternating +/-0.3 noise over 7 days.
    noise = [0, 0.3, -0.3, 0.2, -0.2, 0.3, -0.1]
    series = [round(40 + 2.0 * i + noise[i], 2) for i in range(7)]
    current = series[-1]
    slope, pred_date_str = linear_predict(series)
    if slope is None or not pred_date_str:
        check("noisy series yields a prediction", False, "slope/date missing")
        return False
    true_days_to_100 = (100 - current) / 2.0
    pred_dt = datetime.datetime.strptime(pred_date_str, "%Y-%m-%d")
    pred_days = (pred_dt - datetime.datetime.now()).total_seconds() / 86400.0
    within_10pct = abs(pred_days - true_days_to_100) <= max(0.5, 0.10 * true_days_to_100)
    check("noisy series predicted within 10%", within_10pct,
          f"slope={slope:.3f} pred={pred_days:.2f}d true~{true_days_to_100:.2f}d")
    return within_10pct

def test_insufficient_history():
    """Fewer than 3 points must return no prediction (no crash, no false alert)."""
    slope, pred = linear_predict([50, 52])
    check("<3 points -> no prediction", slope is None and pred is None,
          f"slope={slope} pred={pred}")
    return slope is None and pred is None

def test_threshold_configurable():
    """The breach threshold must be honoured when overridden (configurable)."""
    now = datetime.datetime.now()
    far_future = now + datetime.timedelta(hours=720)  # 30 days out -> no window alert
    # Default threshold: current 50% is below 90% -> no alert.
    a_default = breach_alert(far_future, 50.0)
    check("default: 50% < 90% threshold -> no alert", a_default["alert"] is False, str(a_default))
    # Override threshold down to 40%: now 50% >= 40% -> alert fires.
    a_over = breach_alert(far_future, 50.0, threshold=40.0)
    check("override threshold=40%: 50% >= 40% -> alert", a_over["alert"] is True, str(a_over))
    return (a_default["alert"] is False) and (a_over["alert"] is True)

def test_window_configurable():
    """The pre-breach alert window must be honoured when overridden."""
    now = datetime.datetime.now()
    breach_in_30h = now + datetime.timedelta(hours=30)
    # Default 48h window: 30h < 48h -> alert.
    a_def = breach_alert(breach_in_30h, 50.0)
    check("default 48h window: breach in 30h -> alert", a_def["alert"] is True, str(a_def))
    # Override window to 12h: 30h > 12h -> no alert.
    a_narrow = breach_alert(breach_in_30h, 50.0, window_hours=12)
    check("override window=12h: breach in 30h -> no alert", a_narrow["alert"] is False, str(a_narrow))
    return (a_def["alert"] is True) and (a_narrow["alert"] is False)

def test_env_config_loads():
    """Confirm the module exposes the configurable knobs (defaults present)."""
    ok = (ALERT_THRESHOLD_PCT == 90.0) and (ALERT_WINDOW_HOURS == 48)
    check("module exposes default threshold=90 / window=48", ok,
          f"threshold={ALERT_THRESHOLD_PCT} window={ALERT_WINDOW_HOURS}")
    return ok

def main():
    tests = [test_prediction_within_10pct, test_prediction_noisy_still_close,
             test_insufficient_history, test_threshold_configurable,
             test_window_configurable, test_env_config_loads]
    for t in tests:
        try:
            t()
        except Exception as e:
            check(t.__name__, False, f"EXC {type(e).__name__}: {e}")
    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    all_ok = passed == total
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(EVIDENCE, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": stamp, "run": "capacity_predict_test",
                            "passed": passed, "total": total,
                            "verdict": "PASS" if all_ok else "FAIL",
                            "checks": results}) + "\n")
    print(f"\n[capacity_predict_test] {passed}/{total} PASS -> {'PASS' if all_ok else 'FAIL'} (evidence: {EVIDENCE.name})")
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())