"""Autonomy Precision/Recall Tracker — classifies each autonomous action as correct/false-positive/false-negative; produces weekly metric.

Usage:
  python memory/verifier/autonomy_pr_tracker.py --self-test   # run built-in tests
  python memory/verifier/autonomy_pr_tracker.py               # compute current metrics

Design:
- Reads autonomous actions from decision-log.jsonl (or a test fixture)
- Each action is classified:
  * correct (true positive): fault existed, fix was appropriate, system recovered
  * false_positive: no actual fault existed (healthy condition triggered remediation)
  * false_negative: fault existed but was NOT addressed (missed detection)
- Metrics: precision = TP/(TP+FP), recall = TP/(TP+FN), F1 = 2*P*R/(P+R)
- Weekly metric: aggregate over last 7 days of actions

Self-test uses synthetic decision logs to prove correct classification + metric computation.
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
REPO_ROOT = BASE.parent.parent
DECISION_LOG = REPO_ROOT / "decision-log.jsonl"


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def classify_action(entry: dict) -> str:
    """Classify a single autonomous action entry.
    
    Returns: 'correct', 'false_positive', 'false_negative', or 'unknown'
    
    Classification logic:
    - Has 'degradation_type' + 'action' + no 'recovery_confirmed': false_negative (fault not fully addressed)
    - Has 'degradation_type' + 'action' + 'recovery_confirmed': correct (TP)
    - No 'degradation_type' but has 'action': false_positive (acted without fault)
    - Neither: unknown
    """
    has_fault = bool(entry.get("degradation_type"))
    has_action = bool(entry.get("action"))
    recovered = entry.get("recovery_confirmed", False)
    
    if has_fault and has_action and recovered:
        return "correct"
    elif has_fault and has_action and not recovered:
        # Action taken but recovery not confirmed - could be FN (incomplete fix)
        return "false_negative"
    elif has_fault and not has_action:
        # Fault detected but no action taken = missed
        return "false_negative"
    elif not has_fault and has_action:
        # Action taken without fault = false alarm
        return "false_positive"
    else:
        return "unknown"


def compute_metrics(actions: list) -> dict:
    """Compute precision, recall, F1 from classified actions."""
    tp = sum(1 for a in actions if a.get("classification") == "correct")
    fp = sum(1 for a in actions if a.get("classification") == "false_positive")
    fn = sum(1 for a in actions if a.get("classification") == "false_negative")
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "total_actions": len(actions),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
    }


def load_actions(source: Path = None) -> list:
    """Load autonomous actions from decision log or test fixture."""
    path = source or DECISION_LOG
    if not path.exists():
        return []
    
    actions = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            # Only entries with an "action" field are autonomous actions
            if "action" in entry or "degradation_type" in entry:
                actions.append(entry)
    return actions


def run_audit(source: Path = None, window_days: int = 7) -> dict:
    """Run the full precision/recall audit."""
    actions_raw = load_actions(source)
    
    # Classify each action
    for a in actions_raw:
        a["classification"] = classify_action(a)
    
    # Filter to window (if ts present)
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    windowed = []
    for a in actions_raw:
        ts = a.get("ts", "")
        if ts:
            try:
                action_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if action_time >= cutoff:
                    windowed.append(a)
            except (ValueError, TypeError):
                windowed.append(a)  # No valid ts -> include
        else:
            windowed.append(a)  # No ts -> include
    
    metrics = compute_metrics(windowed)
    
    return {
        "ts": now_iso(),
        "window_days": window_days,
        "actions_in_window": len(windowed),
        "metrics": metrics,
        "classifications": [
            {"id": a.get("rule_id", a.get("id", "?")), "type": a.get("degradation_type", "none"), "classification": a["classification"]}
            for a in windowed
        ],
    }


def self_test():
    """Self-test with synthetic data. Returns exit code."""
    import tempfile
    
    print("=== Autonomy Precision/Recall Tracker Self-Test ===")
    passed = 0
    failed = 0
    
    # T1: All correct actions -> precision=1, recall=1
    print("\nT1: All-correct log -> P=1.0 R=1.0 F1=1.0")
    log = [
        {"rule_id": "R1", "degradation_type": "model_oom", "action": {"type": "model_swap"}, "recovery_confirmed": True},
        {"rule_id": "R2", "degradation_type": "agent_unresponsive", "action": {"type": "task_reroute"}, "recovery_confirmed": True},
    ]
    for a in log:
        a["classification"] = classify_action(a)
    m = compute_metrics(log)
    if m["precision"] == 1.0 and m["recall"] == 1.0 and m["f1_score"] == 1.0:
        print(f"  PASS: P={m['precision']} R={m['recall']} F1={m['f1_score']}")
        passed += 1
    else:
        print(f"  FAIL: {m}")
        failed += 1
    
    # T2: Mixed log -> expected metrics
    print("\nT2: Mixed log (2 TP, 1 FP, 1 FN) -> P=0.667 R=0.667")
    log = [
        {"rule_id": "R1", "degradation_type": "model_oom", "action": {"type": "model_swap"}, "recovery_confirmed": True},  # TP
        {"rule_id": "R2", "degradation_type": "agent_unresponsive", "action": {"type": "task_reroute"}, "recovery_confirmed": True},  # TP
        {"rule_id": "R3", "action": {"type": "cleanup"}},  # FP (no degradation_type)
        {"rule_id": "R4", "degradation_type": "disk_space_critical", "action": {"type": "archive"}, "recovery_confirmed": False},  # FN
    ]
    for a in log:
        a["classification"] = classify_action(a)
    m = compute_metrics(log)
    expected_p = round(2/3, 4)  # 2/(2+1)
    expected_r = round(2/3, 4)  # 2/(2+1)
    if abs(m["precision"] - expected_p) < 0.01 and abs(m["recall"] - expected_r) < 0.01:
        print(f"  PASS: P={m['precision']} R={m['recall']} (expected ~{expected_p})")
        passed += 1
    else:
        print(f"  FAIL: {m}")
        failed += 1
    
    # T3: No actions -> default metrics (no division by zero)
    print("\nT3: Empty log -> P=1.0 R=1.0 (default, no crash)")
    m = compute_metrics([])
    if m["precision"] == 1.0 and m["recall"] == 1.0 and m["total_actions"] == 0:
        print(f"  PASS: empty log handled gracefully")
        passed += 1
    else:
        print(f"  FAIL: {m}")
        failed += 1
    
    # T4: Fault detected but no action -> false_negative
    print("\nT4: Fault without action -> classified as false_negative")
    entry = {"rule_id": "R5", "degradation_type": "host_unreachable"}
    cls = classify_action(entry)
    if cls == "false_negative":
        print(f"  PASS: correctly classified as {cls}")
        passed += 1
    else:
        print(f"  FAIL: got {cls}, expected false_negative")
        failed += 1
    
    # T5: No fault but action taken -> false_positive
    print("\nT5: Action without fault -> classified as false_positive")
    entry = {"rule_id": "R6", "action": {"type": "model_swap"}}
    cls = classify_action(entry)
    if cls == "false_positive":
        print(f"  PASS: correctly classified as {cls}")
        passed += 1
    else:
        print(f"  FAIL: got {cls}, expected false_positive")
        failed += 1
    
    # T6: Live run against decision-log (or graceful empty)
    print("\nT6: Live audit run completes without error")
    result = run_audit()
    if "metrics" in result and "ts" in result:
        print(f"  PASS: {result['actions_in_window']} actions, P={result['metrics']['precision']} R={result['metrics']['recall']}")
        passed += 1
    else:
        print(f"  FAIL: unexpected structure: {list(result.keys())}")
        failed += 1
    
    # T7: Window filtering works (old entries excluded)
    print("\nT7: Window filtering excludes old entries")
    old_entry = {"rule_id": "OLD", "degradation_type": "model_oom", "action": {"type": "swap"},
                 "recovery_confirmed": True, "ts": "2020-01-01T00:00:00Z"}
    new_entry = {"rule_id": "NEW", "degradation_type": "model_oom", "action": {"type": "swap"},
                 "recovery_confirmed": True, "ts": now_iso()}
    
    # Write temp log
    tmp = Path(tempfile.mktemp(suffix=".jsonl"))
    with open(tmp, "w") as f:
        f.write(json.dumps(old_entry) + "\n" + json.dumps(new_entry) + "\n")
    
    result = run_audit(source=tmp, window_days=7)
    tmp.unlink(missing_ok=True)
    
    if result["actions_in_window"] == 1:
        print(f"  PASS: only 1 recent action in window (old excluded)")
        passed += 1
    else:
        print(f"  FAIL: expected 1, got {result['actions_in_window']}")
        failed += 1
    
    print(f"\n=== RESULTS: {passed} PASS / {failed} FAIL ===")
    return 0 if failed == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="Autonomy Precision/Recall Tracker")
    parser.add_argument("--self-test", action="store_true", help="Run self-test")
    parser.add_argument("--window", type=int, default=7, help="Window in days (default 7)")
    args = parser.parse_args()
    
    if args.self_test:
        sys.exit(self_test())
    
    result = run_audit(window_days=args.window)
    print(json.dumps(result, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
