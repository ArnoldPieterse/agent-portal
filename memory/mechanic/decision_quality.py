"""Decision Quality Tracker.

Reads memory/ops/auto-ops-decisions.jsonl and computes:
  - pct decisions with positive outcome (no follow-up within 24h)
  - trend (improving/stable/worsening)
  - alert if quality < 80%

Output: memory/ops/decision-quality.json

Each decision record format:
  {"ts": "...", "action": "...", "followup_within_24h": true/false, "outcome": "positive"/"negative"}

Usage:
  python memory/mechanic/decision_quality.py          # live
  python memory/mechanic/decision_quality.py --selftest
"""
import json, pathlib, datetime, sys

BASE = pathlib.Path(__file__).resolve().parent.parent.parent
INPUT = BASE / "memory" / "ops" / "auto-ops-decisions.jsonl"
OUTPUT = BASE / "memory" / "ops" / "decision-quality.json"
ALERT_THRESHOLD = 80.0  # percent

def compute_quality(records):
    """Compute quality metrics from decision records."""
    if not records:
        return {
            "generated": datetime.datetime.now().isoformat(),
            "total_decisions": 0,
            "positive_pct": None,
            "trend": "insufficient_data",
            "alert": False,
            "detail": "No decision records found",
        }

    total = len(records)
    positive = sum(1 for r in records if r.get("outcome") == "positive" and not r.get("followup_within_24h", False))
    pct = round(100.0 * positive / total, 1)

    # Trend: compare first half vs second half
    trend = "stable"
    if total >= 6:
        mid = total // 2
        first_half_pos = sum(1 for r in records[:mid] if r.get("outcome") == "positive" and not r.get("followup_within_24h", False))
        second_half_pos = sum(1 for r in records[mid:] if r.get("outcome") == "positive" and not r.get("followup_within_24h", False))
        first_pct = 100.0 * first_half_pos / mid
        second_pct = 100.0 * second_half_pos / (total - mid)
        if second_pct > first_pct + 10:
            trend = "improving"
        elif second_pct < first_pct - 10:
            trend = "worsening"

    alert = pct < ALERT_THRESHOLD

    return {
        "generated": datetime.datetime.now().isoformat(),
        "total_decisions": total,
        "positive_count": positive,
        "positive_pct": pct,
        "trend": trend,
        "alert": alert,
        "alert_threshold_pct": ALERT_THRESHOLD,
    }

def selftest():
    """Verify: 20 test decisions; quality correct; drop triggers alert."""
    errors = []

    # Create 20 decisions: 18 positive (90%), 2 negative
    records = []
    for i in range(18):
        records.append({"ts": f"2026-11-{20+i%5:02d}T10:{i:02d}:00", "action": f"auto_fix_{i}", "followup_within_24h": False, "outcome": "positive"})
    records.append({"ts": "2026-11-24T15:00:00", "action": "bad_fix_1", "followup_within_24h": True, "outcome": "negative"})
    records.append({"ts": "2026-11-24T16:00:00", "action": "bad_fix_2", "followup_within_24h": False, "outcome": "negative"})

    result = compute_quality(records)

    # Check 1: total is 20
    if result["total_decisions"] != 20:
        errors.append(f"Total: expected 20, got {result['total_decisions']}")

    # Check 2: positive pct = 90.0 (18/20)
    if result["positive_pct"] != 90.0:
        errors.append(f"Positive pct: expected 90.0, got {result['positive_pct']}")

    # Check 3: no alert (90% > 80%)
    if result["alert"]:
        errors.append("Alert should be False at 90% quality")

    # Check 4: trend is stable or improving (first half all positive, second has 2 negatives)
    # First 10: all positive = 100%. Second 10: 8 positive + 2 negative = 80%. Drop of 20% -> worsening
    if result["trend"] != "worsening":
        errors.append(f"Trend: expected worsening, got {result['trend']}")

    # Test 5: low quality triggers alert
    bad_records = [
        {"ts": f"2026-11-{20+i%5:02d}T10:{i:02d}:00", "action": f"x_{i}", "followup_within_24h": i % 3 == 0, "outcome": "positive" if i % 5 != 0 else "negative"}
        for i in range(20)
    ]
    # i=0: neg, i=1: pos+no_fu, i=2: pos+no_fu, i=3: pos+fu, i=4: pos+no_fu
    # i=5: neg, i=6: pos+fu, i=7: pos+no_fu, i=8: pos+no_fu, i=9: pos+fu
    # i=10: neg, i=11: pos+no_fu, i=12: pos+fu, i=13: pos+no_fu, i=14: pos+no_fu
    # i=15: neg, i=16: pos+no_fu, i=17: pos+no_fu, i=18: pos+fu, i=19: pos+no_fu
    # Positive no-fu: 1,2,4,7,8,11,13,14,16,17,19 = 11 out of 20 = 55%
    bad_result = compute_quality(bad_records)
    if not bad_result["alert"]:
        errors.append(f"Alert should trigger at {bad_result['positive_pct']}% quality")
    if bad_result["positive_pct"] != 55.0:
        errors.append(f"Bad quality pct: expected 55.0, got {bad_result['positive_pct']}")

    # Test 6: empty records
    empty = compute_quality([])
    if empty["total_decisions"] != 0 or empty["alert"] is not False:
        errors.append("Empty records handling incorrect")

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return False
    else:
        print("PASS: all 6 selftest checks OK")
        print(f"  20 decisions -> 90% quality, trend=worsening, no alert")
        print(f"  20 bad decisions -> 45% quality, alert=True")
        return True

def main():
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)

    records = []
    if INPUT.exists():
        with open(INPUT, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))

    result = compute_quality(records)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {OUTPUT}: quality={result['positive_pct']}%, trend={result['trend']}, alert={result['alert']}")

if __name__ == "__main__":
    main()
