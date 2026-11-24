"""heal_fp_rate.py — Self-Heal False-Positive Rate Measurement.

Goal: #3 Self-Heal FP Rate
Over a rolling 14-day window, measure the ratio of self-heal triggers that were actual repairs
vs false positives (benign transient events). Produce per-task FP rate + recommended threshold
adjustment if FP > 20%.

Data sources:
  - memory/ops/portal-heal-log.jsonl (restart attempts, health checks)
  - memory/ops/guardian-log.jsonl (guardian events)
  - memory/ops/autonomous-actions.jsonl (unified action log)

Classification:
  - ACTUAL_REPAIR: trigger fired AND corrective action succeeded AND system was genuinely broken
  - FALSE_POSITIVE: trigger fired but outcome indicates system was fine / transient event
    (e.g., restart_skipped_cooldown, health_check_ok immediately after, rolled_back)
  - INCONCLUSIVE: insufficient data to classify

Self-test: synthetic entries prove classification logic works correctly.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HEAL_LOGS = [
    REPO_ROOT / "memory" / "ops" / "portal-heal-log.jsonl",
    REPO_ROOT / "memory" / "ops" / "guardian-log.jsonl",
    REPO_ROOT / "memory" / "ops" / "autonomous-actions.jsonl",
]
RESULTS_FILE = REPO_ROOT / "memory" / "verifier" / "heal-fp-rate-results.json"
WINDOW_DAYS = 14
FP_THRESHOLD = 0.20  # Flag if FP rate > 20%


def parse_ts(ts_str):
    """Parse various timestamp formats to datetime."""
    if not ts_str:
        return None
    try:
        ts_str = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        # Try format like "2026-11-23 12:47:24"
        try:
            dt = datetime.strptime(ts_str.strip(), "%Y-%m-%d %H:%M:%S")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None


def load_all_heal_events():
    """Load and normalize all heal-related events from all sources."""
    events = []
    
    # portal-heal-log.jsonl
    p = REPO_ROOT / "memory" / "ops" / "portal-heal-log.jsonl"
    if p.exists():
        for line in p.read_text(encoding="utf-8").strip().split("\n"):
            if not line.strip():
                continue
            try:
                e = json.loads(line)
                dt = parse_ts(e.get("timestamp", ""))
                events.append({
                    "source": "portal-heal-log",
                    "ts": dt,
                    "task": "portal_heal",
                    "event": e.get("event", "unknown"),
                    "data": e
                })
            except json.JSONDecodeError:
                pass
    
    # guardian-log.jsonl
    p = REPO_ROOT / "memory" / "ops" / "guardian-log.jsonl"
    if p.exists():
        for line in p.read_text(encoding="utf-8").strip().split("\n"):
            if not line.strip():
                continue
            try:
                e = json.loads(line)
                dt = parse_ts(e.get("t", ""))
                events.append({
                    "source": "guardian-log",
                    "ts": dt,
                    "task": "guardian",
                    "event": e.get("event", "unknown"),
                    "data": e
                })
            except json.JSONDecodeError:
                pass
    
    # autonomous-actions.jsonl
    p = REPO_ROOT / "memory" / "ops" / "autonomous-actions.jsonl"
    if p.exists():
        for line in p.read_text(encoding="utf-8").strip().split("\n"):
            if not line.strip():
                continue
            try:
                e = json.loads(line)
                dt = parse_ts(e.get("ts", ""))
                events.append({
                    "source": "autonomous-actions",
                    "ts": dt,
                    "task": e.get("action", "unknown"),
                    "event": "action",
                    "data": e
                })
            except json.JSONDecodeError:
                pass
    
    return events


def filter_window(events, days=WINDOW_DAYS):
    """Filter events to last N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return [e for e in events if e["ts"] is not None and e["ts"] >= cutoff]


def classify_event(event):
    """Classify a heal event as ACTUAL_REPAIR, FALSE_POSITIVE, or INCONCLUSIVE."""
    ev = event.get("event", "")
    data = event.get("data", {})
    source = event.get("source", "")
    
    # Portal heal log classification
    if source == "portal-heal-log":
        if ev == "restart_attempted":
            if data.get("success"):
                return "ACTUAL_REPAIR"  # Restart succeeded → system was broken
            else:
                # Failed restart - check if it was a transient (cooldown suggests rapid re-trigger)
                if data.get("restarts_1h", 0) >= 2:
                    return "FALSE_POSITIVE"  # Rapid re-triggers suggest flapping/transient
                return "INCONCLUSIVE"
        elif ev == "restart_skipped_cooldown":
            # Heal triggered but skipped due to cooldown → likely transient/benign
            return "FALSE_POSITIVE"
        elif ev == "health_check_ok":
            # System is fine — if this follows a heal trigger, the trigger was FP
            return "NO_ACTION_NEEDED"  # Not a heal trigger itself
        else:
            return "INCONCLUSIVE"
    
    # Guardian log classification
    if source == "guardian-log":
        if ev in ("guardian-up", "portal-start", "oom-daemon-start"):
            # These are startup/recovery events — actual repairs if they follow a failure
            return "ACTUAL_REPAIR"
        elif ev == "health_check_ok":
            return "NO_ACTION_NEEDED"
        else:
            return "INCONCLUSIVE"
    
    # Autonomous actions classification
    if source == "autonomous-actions":
        outcome = data.get("outcome", "")
        if outcome == "success":
            return "ACTUAL_REPAIR"
        elif outcome == "rolled_back":
            return "FALSE_POSITIVE"  # Action was rolled back → problem wasn't real
        elif outcome in ("failed", "blocked"):
            return "INCONCLUSIVE"
        else:
            return "INCONCLUSIVE"
    
    return "INCONCLUSIVE"


def compute_fp_rate(events):
    """Compute per-task FP rate from classified events."""
    # Filter to only heal-trigger events (exclude NO_ACTION_NEEDED)
    heal_triggers = [e for e in events if classify_event(e) != "NO_ACTION_NEEDED"]
    
    by_task = defaultdict(lambda: {"total": 0, "actual_repair": 0, "false_positive": 0, "inconclusive": 0})
    
    for e in heal_triggers:
        cls = classify_event(e)
        task = e.get("task", "unknown")
        by_task[task]["total"] += 1
        if cls == "ACTUAL_REPAIR":
            by_task[task]["actual_repair"] += 1
        elif cls == "FALSE_POSITIVE":
            by_task[task]["false_positive"] += 1
        else:
            by_task[task]["inconclusive"] += 1
    
    # Compute FP rate per task (only count classified, exclude inconclusive from denominator)
    results = {}
    for task, counts in sorted(by_task.items()):
        classified = counts["actual_repair"] + counts["false_positive"]
        fp_rate = counts["false_positive"] / classified if classified > 0 else 0.0
        flagged = fp_rate > FP_THRESHOLD and classified >= 3  # Need minimum sample
        
        results[task] = {
            "total_triggers": counts["total"],
            "actual_repair": counts["actual_repair"],
            "false_positive": counts["false_positive"],
            "inconclusive": counts["inconclusive"],
            "classified_total": classified,
            "fp_rate": round(fp_rate, 3),
            "flagged": flagged,
            "recommended_threshold_adjustment": None
        }
        
        if flagged:
            # Suggest increasing detection threshold to reduce FPs
            current_trigger = counts["false_positive"] / counts["total"] if counts["total"] > 0 else 0
            results[task]["recommended_threshold_adjustment"] = (
                f"Increase trigger sensitivity by {int((fp_rate * 100))}% "
                f"(current FP rate {fp_rate:.1%} exceeds {FP_THRESHOLD:.0%} threshold; "
                f"min sample met: {classified} classified events)"
            )
    
    return results


def self_test():
    """Synthetic tests proving classification + FP rate computation."""
    print("[SELF-TEST] heal_fp_rate.py")
    results = []
    
    # T1: Successful restart → ACTUAL_REPAIR
    e = {"source": "portal-heal-log", "ts": datetime.now(timezone.utc), "task": "portal_heal",
         "event": "restart_attempted", "data": {"success": True, "duration_s": 5.0}}
    ok = classify_event(e) == "ACTUAL_REPAIR"
    results.append(("T1_successful_restart_is_repair", ok, f"got={classify_event(e)}"))
    
    # T2: Restart skipped cooldown → FALSE_POSITIVE
    e = {"source": "portal-heal-log", "ts": datetime.now(timezone.utc), "task": "portal_heal",
         "event": "restart_skipped_cooldown", "data": {}}
    ok = classify_event(e) == "FALSE_POSITIVE"
    results.append(("T2_cooldown_skip_is_fp", ok, f"got={classify_event(e)}"))
    
    # T3: Rolled-back action → FALSE_POSITIVE
    e = {"source": "autonomous-actions", "ts": datetime.now(timezone.utc), "task": "deploy_canary",
         "event": "action", "data": {"outcome": "rolled_back"}}
    ok = classify_event(e) == "FALSE_POSITIVE"
    results.append(("T3_rollback_is_fp", ok, f"got={classify_event(e)}"))
    
    # T4: Health check OK → NO_ACTION_NEEDED (not a heal trigger)
    e = {"source": "portal-heal-log", "ts": datetime.now(timezone.utc), "task": "portal_heal",
         "event": "health_check_ok", "data": {"response_ms": 10.0}}
    ok = classify_event(e) == "NO_ACTION_NEEDED"
    results.append(("T4_health_ok_not_trigger", ok, f"got={classify_event(e)}"))
    
    # T5: FP rate computation with known data
    synthetic_events = [
        {"source": "portal-heal-log", "ts": datetime.now(timezone.utc), "task": "test_task",
         "event": "restart_attempted", "data": {"success": True}},  # repair
        {"source": "portal-heal-log", "ts": datetime.now(timezone.utc), "task": "test_task",
         "event": "restart_skipped_cooldown", "data": {}},  # FP
        {"source": "portal-heal-log", "ts": datetime.now(timezone.utc), "task": "test_task",
         "event": "restart_skipped_cooldown", "data": {}},  # FP
        {"source": "portal-heal-log", "ts": datetime.now(timezone.utc), "task": "test_task",
         "event": "restart_skipped_cooldown", "data": {}},  # FP
    ]
    rates = compute_fp_rate(synthetic_events)
    ok = rates["test_task"]["fp_rate"] == round(3/4, 3) and rates["test_task"]["flagged"] == True
    results.append(("T5_fp_rate_correct_and_flagged", ok,
                    f"rate={rates['test_task']['fp_rate']}, flagged={rates['test_task']['flagged']}"))
    
    # T6: Low FP rate not flagged
    synthetic_events2 = [
        {"source": "portal-heal-log", "ts": datetime.now(timezone.utc), "task": "good_task",
         "event": "restart_attempted", "data": {"success": True}},  # repair
        {"source": "portal-heal-log", "ts": datetime.now(timezone.utc), "task": "good_task",
         "event": "restart_attempted", "data": {"success": True}},  # repair
        {"source": "portal-heal-log", "ts": datetime.now(timezone.utc), "task": "good_task",
         "event": "restart_skipped_cooldown", "data": {}},  # FP (1/3 = 33%)
    ]
    rates2 = compute_fp_rate(synthetic_events2)
    ok = rates2["good_task"]["fp_rate"] == round(1/3, 3) and rates2["good_task"]["flagged"] == True
    results.append(("T6_1of3_fp_flagged", ok, f"rate={rates2['good_task']['fp_rate']}"))
    
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    for name, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        print(f"  {status} {name}: {detail}")
    print(f"[SELF-TEST] {passed}/{total} passed")
    
    # Write results
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    out = {
        "test_ts": datetime.now(timezone.utc).isoformat(),
        "self_test": {"passed": passed, "total": total},
    }
    RESULTS_FILE.write_text(json.dumps(out, indent=2), encoding="utf-8")
    
    return passed == total


def main():
    if "--self-test" in sys.argv:
        ok = self_test()
        sys.exit(0 if ok else 1)
    
    # Live mode
    print(f"[heal_fp_rate] Window: {WINDOW_DAYS} days")
    all_events = load_all_heal_events()
    window_events = filter_window(all_events)
    
    print(f"  Total heal-related events loaded: {len(all_events)}")
    print(f"  Events in {WINDOW_DAYS}d window: {len(window_events)}")
    
    rates = compute_fp_rate(window_events)
    
    if not rates:
        print("  No heal triggers found in window (new system or no issues)")
        print("  RESULT: PASS (vacuous — no data to flag)")
    else:
        any_flagged = False
        for task, info in rates.items():
            flag_str = " ** FLAGGED **" if info["flagged"] else ""
            print(f"  Task '{task}': {info['total_triggers']} triggers, "
                  f"{info['actual_repair']} repairs, {info['false_positive']} FPs, "
                  f"{info['inconclusive']} inconclusive | FP rate: {info['fp_rate']:.1%}{flag_str}")
            if info["flagged"]:
                any_flagged = True
                print(f"    Recommended: {info['recommended_threshold_adjustment']}")
        
        # PASS if no tasks are flagged (all within threshold)
        print(f"  RESULT: {'FAIL' if any_flagged else 'PASS'}")
    
    # Write full results
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    out = {
        "audit_ts": datetime.now(timezone.utc).isoformat(),
        "window_days": WINDOW_DAYS,
        "total_events_loaded": len(all_events),
        "events_in_window": len(window_events),
        "per_task_rates": rates,
        "any_flagged": any(r["flagged"] for r in rates.values()) if rates else False,
        "pass": not any(r["flagged"] for r in rates.values()) if rates else True,
    }
    RESULTS_FILE.write_text(json.dumps(out, indent=2), encoding="utf-8")
    
    sys.exit(0 if out["pass"] else 1)


if __name__ == "__main__":
    main()
