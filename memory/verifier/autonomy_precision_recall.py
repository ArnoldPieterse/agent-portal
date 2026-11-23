#!/usr/bin/env python3
"""
autonomy_precision_recall.py - Verifier Goal #10 (Cycle 14)
Autonomy Precision/Recall Tracker: classify each autonomous action as
correct / false-positive / false-negative; compute weekly metric.

Usage:
  python memory/verifier/autonomy_precision_recall.py --self-test
  python memory/verifier/autonomy_precision_recall.py [--since-days N]

Input (decision_log.jsonl):
  Each line: {"ts": "...", "agent": "...", "condition": "...",
              "action_taken": true|false, "correct_action": true|false}

Classification per entry:
  TP: action_taken=True AND correct_action=True
  FP: action_taken=True AND correct_action=False
  FN: action_taken=False AND correct_action=True
  TN: action_taken=False AND correct_action=False

Metrics:
  precision = TP / (TP + FP)   [of actions taken, how many were correct]
  recall    = TP / (TP + FN)   [of needed actions, how many were taken]
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
LOG_FILE = BASE.parent.parent / "decision_log.jsonl"  # project root


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_ts(ts_str: str) -> datetime:
    """Parse ISO timestamp string to datetime (UTC)."""
    ts_str = ts_str.strip()
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(ts_str)
    except ValueError:
        # Fallback: assume UTC if no timezone
        return datetime.fromisoformat(ts_str.replace("+00:00", "")).replace(tzinfo=timezone.utc)


def classify(entry: dict) -> str:
    """Classify a single decision-log entry as TP/FP/FN/TN."""
    action = bool(entry.get("action_taken", False))
    correct = bool(entry.get("correct_action", False))

    if action and correct:
        return "TP"
    elif action and not correct:
        return "FP"
    elif not action and correct:
        return "FN"
    else:
        return "TN"


def load_entries(since_days: int = None) -> list:
    """Load decision log entries, optionally filtered by recency."""
    if not LOG_FILE.exists():
        return []

    cutoff = None
    if since_days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)

    entries = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Filter by recency
            if cutoff is not None:
                try:
                    ts = parse_ts(entry.get("ts", ""))
                    if ts < cutoff:
                        continue
                except (ValueError, TypeError):
                    continue  # skip entries with unparseable ts

            entries.append(entry)

    return entries


def compute_metrics(entries: list) -> dict:
    """Compute precision/recall metrics from classified entries."""
    counts = {"TP": 0, "FP": 0, "FN": 0, "TN": 0}
    classifications = []

    for e in entries:
        c = classify(e)
        counts[c] += 1
        classifications.append({
            "ts": e.get("ts", ""),
            "agent": e.get("agent", "unknown"),
            "condition": e.get("condition", ""),
            "classification": c,
        })

    tp, fp = counts["TP"], counts["FP"]
    fn = counts["FN"]

    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    recall = tp / (tp + fn) if (tp + fn) > 0 else None
    f1 = (2 * precision * recall / (precision + recall)) if (precision and recall and (precision + recall) > 0) else None

    return {
        "ts": now_iso(),
        "total_entries": len(entries),
        "counts": counts,
        "precision": round(precision, 4) if precision is not None else None,
        "recall": round(recall, 4) if recall is not None else None,
        "f1": round(f1, 4) if f1 is not None else None,
        "classifications": classifications,
    }


def run_audit(since_days: int = 7) -> dict:
    """Run the precision/recall audit."""
    entries = load_entries(since_days=since_days)
    return compute_metrics(entries)


def self_test() -> int:
    """Self-test with synthetic data. Returns exit code."""
    print("=== Autonomy Precision/Recall Tracker - Self-Test ===")
    passed = 0
    failed = 0

    # T1: All correct actions (TP only) -> precision=1, recall=1
    print("\nT1: Pure TP log -> precision=1.0, recall=1.0")
    entries = [
        {"ts": "2026-11-24T10:00:00Z", "agent": "mech", "condition": "vram_high", "action_taken": True, "correct_action": True},
        {"ts": "2026-11-24T11:00:00Z", "agent": "orch", "condition": "stall", "action_taken": True, "correct_action": True},
    ]
    m = compute_metrics(entries)
    if m["precision"] == 1.0 and m["recall"] == 1.0 and m["counts"]["TP"] == 2:
        print(f"  PASS: precision={m['precision']}, recall={m['recall']}")
        passed += 1
    else:
        print(f"  FAIL: {m}")
        failed += 1

    # T2: One FP (action taken but not needed) -> precision < 1.0
    print("\nT2: TP+FP log -> precision < 1.0")
    entries = [
        {"ts": "2026-11-24T10:00:00Z", "agent": "mech", "condition": "vram_high", "action_taken": True, "correct_action": True},
        {"ts": "2026-11-24T11:00:00Z", "agent": "orch", "condition": "healthy", "action_taken": True, "correct_action": False},
    ]
    m = compute_metrics(entries)
    if abs(m["precision"] - 0.5) < 0.001 and m["counts"]["FP"] == 1:
        print(f"  PASS: precision={m['precision']}, FP=1 (correctly flagged)")
        passed += 1
    else:
        print(f"  FAIL: {m}")
        failed += 1

    # T3: One FN (needed action not taken) -> recall < 1.0
    print("\nT3: TP+FN log -> recall < 1.0")
    entries = [
        {"ts": "2026-11-24T10:00:00Z", "agent": "mech", "condition": "vram_high", "action_taken": True, "correct_action": True},
        {"ts": "2026-11-24T11:00:00Z", "agent": "builder", "condition": "oom_imminent", "action_taken": False, "correct_action": True},
    ]
    m = compute_metrics(entries)
    if abs(m["recall"] - 0.5) < 0.001 and m["counts"]["FN"] == 1:
        print(f"  PASS: recall={m['recall']}, FN=1 (correctly flagged)")
        passed += 1
    else:
        print(f"  FAIL: {m}")
        failed += 1

    # T4: Empty log -> no division by zero, graceful None metrics
    print("\nT4: Empty log -> precision/recall=None (no crash)")
    m = compute_metrics([])
    if m["precision"] is None and m["recall"] is None and m["total_entries"] == 0:
        print(f"  PASS: empty log handled gracefully")
        passed += 1
    else:
        print(f"  FAIL: {m}")
        failed += 1

    # T5: All TN -> precision/recall=None (no actions taken or needed)
    print("\nT5: Pure TN log -> precision/recall=None")
    entries = [
        {"ts": "2026-11-24T10:00:00Z", "agent": "mech", "condition": "healthy", "action_taken": False, "correct_action": False},
    ]
    m = compute_metrics(entries)
    if m["precision"] is None and m["recall"] is None and m["counts"]["TN"] == 1:
        print(f"  PASS: TN-only log handled (no false metrics)")
        passed += 1
    else:
        print(f"  FAIL: {m}")
        failed += 1

    # T6: F1 score computation correct
    print("\nT6: Mixed TP/FP/FN -> F1 computed correctly")
    entries = [
        {"ts": "2026-11-24T10:00:00Z", "agent": "a", "condition": "c1", "action_taken": True, "correct_action": True},   # TP
        {"ts": "2026-11-24T10:01:00Z", "agent": "b", "condition": "c2", "action_taken": True, "correct_action": False},  # FP
        {"ts": "2026-11-24T10:02:00Z", "agent": "c", "condition": "c3", "action_taken": False, "correct_action": True},  # FN
    ]
    m = compute_metrics(entries)
    # precision=1/2=0.5, recall=1/2=0.5, f1=2*0.5*0.5/(0.5+0.5)=0.5
    if abs(m["f1"] - 0.5) < 0.001:
        print(f"  PASS: F1={m['f1']} (precision=recall=0.5 -> f1=0.5)")
        passed += 1
    else:
        print(f"  FAIL: f1={m['f1']}, expected 0.5")
        failed += 1

    # T7: Weekly filter - entries older than 7 days excluded
    print("\nT7: Recency filter (since_days=7) excludes old entries")
    import tempfile, os
    # Create a temp log file with one old + one recent entry
    old_ts = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    recent_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    tmp = Path(tempfile.mktemp(suffix=".jsonl"))
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(json.dumps({"ts": old_ts, "agent": "a", "condition": "x", "action_taken": True, "correct_action": True}) + "\n")
        f.write(json.dumps({"ts": recent_ts, "agent": "b", "condition": "y", "action_taken": True, "correct_action": True}) + "\n")

    # Monkey-patch LOG_FILE to use temp
    global LOG_FILE
    orig_log = LOG_FILE
    LOG_FILE = tmp

    entries_7d = load_entries(since_days=7)
    entries_all = load_entries(since_days=None)

    tmp.unlink(missing_ok=True)
    LOG_FILE = orig_log

    if len(entries_7d) == 1 and len(entries_all) == 2:
        print(f"  PASS: 7-day filter kept {len(entries_7d)}/2, full load kept {len(entries_all)}/2")
        passed += 1
    else:
        print(f"  FAIL: since_days=7 -> {len(entries_7d)}, all -> {len(entries_all)}")
        failed += 1

    print(f"\n=== RESULTS: {passed} PASS / {failed} FAIL ===")
    return 0 if failed == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="Autonomy Precision/Recall Tracker")
    parser.add_argument("--self-test", action="store_true", help="Run built-in self-test")
    parser.add_argument("--since-days", type=int, default=7, help="Window in days (default 7)")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(self_test())

    result = run_audit(since_days=args.since_days)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
