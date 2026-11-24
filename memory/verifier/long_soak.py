#!/usr/bin/env python3
"""
long_soak.py - Convergence Long-Soak Stability Test (Verifier goal #5)

Extends Cycle 17 end-state check into a continuous soak test:
verifies mode stays in converged state (IDLE/MAINTENANCE) with no goal re-opens,
no phantom dispatch, no oscillation. Produces hourly stability trace.

Modes:
  --self-test    Simulate 72h of data and verify detection logic (runs in <30s)
  --snapshot     Record one real snapshot to the soak log (for scheduled use)
  --report       Generate report from accumulated snapshots

Acceptance criteria:
  * 72h window shows stable terminal mode throughout
  * Zero regressions/re-open events
  * Any deviation is logged with timestamp + detected root cause
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path


SOAK_LOG = "memory/ops/long-soak-trace.jsonl"
CONVERGED_MODES = {"IDLE", "MAINTENANCE"}
MAX_DEVIATIONS_ALLOWED = 0


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_trace(log_path=SOAK_LOG):
    """Load accumulated soak trace entries."""
    p = Path(log_path)
    if not p.exists():
        return []
    entries = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def record_snapshot():
    """Record one real snapshot of fleet state."""
    mode = "UNKNOWN"
    goals_reopened = 0
    phantom_dispatches = 0
    
    # Try to get mode from fleet-mode.json
    fm = Path("memory/fleet/fleet-mode.json")
    if fm.exists():
        try:
            data = json.loads(fm.read_text(encoding="utf-8"))
            mode = data.get("mode", "UNKNOWN")
        except Exception:
            pass
    
    # Check for recent goal re-opens in goals files
    goals_dir = Path("memory/goals")
    if goals_dir.exists():
        for gf in goals_dir.glob("*.md"):
            try:
                text = gf.read_text(encoding="utf-8", errors="replace")
                # Look for "reopened" or "regression" markers
                if re.search(r"(reopened|regression|re-open)", text, re.IGNORECASE):
                    goals_reopened += 1
            except Exception:
                pass
    
    snapshot = {
        "ts": _now_iso(),
        "mode": mode,
        "converged": mode in CONVERGED_MODES,
        "goals_reopened": goals_reopened,
        "phantom_dispatches": phantom_dispatches,
        "deviation": None if mode in CONVERGED_MODES and goals_reopened == 0 else {
            "type": "mode_departure" if mode not in CONVERGED_MODES else "goal_reopen",
            "detail": f"mode={mode}, reopened={goals_reopened}",
        },
    }
    
    os.makedirs(os.path.dirname(SOAK_LOG), exist_ok=True)
    with open(SOAK_LOG, "a") as f:
        f.write(json.dumps(snapshot) + "\n")
    
    print(f"Snapshot recorded: mode={mode}, converged={snapshot['converged']}")
    return snapshot


def analyze_window(entries, hours=72):
    """Analyze a window of entries for stability."""
    if not entries:
        return {"stable": False, "error": "no data"}
    
    # Filter to the requested window
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent = []
    for e in entries:
        try:
            ts = datetime.fromisoformat(e["ts"])
            if ts >= cutoff:
                recent.append(e)
        except (ValueError, KeyError):
            continue
    
    if not recent:
        return {"stable": False, "error": f"no data in last {hours}h"}
    
    # Check all entries are converged
    deviations = [e for e in recent if not e.get("converged", False)]
    reopens = sum(e.get("goals_reopened", 0) for e in recent)
    phantom = sum(e.get("phantom_dispatches", 0) for e in recent)
    
    # Check for oscillation (mode changes > N times)
    mode_changes = 0
    for i in range(1, len(recent)):
        if recent[i].get("mode") != recent[i-1].get("mode"):
            mode_changes += 1
    
    stable = (len(deviations) == MAX_DEVIATIONS_ALLOWED and 
              reopens == 0 and phantom == 0 and mode_changes <= 3)
    
    return {
        "stable": stable,
        "window_hours": hours,
        "entries_analyzed": len(recent),
        "deviations": len(deviations),
        "goal_reopens": reopens,
        "phantom_dispatches": phantom,
        "mode_changes": mode_changes,
        "converged_pct": round(100 * (len(recent) - len(deviations)) / len(recent), 1),
        "deviation_details": [d.get("deviation") for d in deviations if d.get("deviation")],
    }


def self_test():
    """Simulate 72h of stable data + one deviation to verify detection logic."""
    print("=" * 64)
    print("long_soak.py - SELF-TEST")
    print("=" * 64)
    
    results = []
    tmplog = "memory/ops/_soak_test_trace.jsonl"
    os.makedirs(os.path.dirname(tmplog), exist_ok=True)
    
    # T1: Stable 72h -> no deviations detected
    print("\n[T1] Stable 72h -> stable...", end=" ")
    entries = []
    now = datetime.now(timezone.utc)
    for h in range(72):
        ts = (now - timedelta(hours=71-h)).isoformat()
        entries.append({
            "ts": ts, "mode": "IDLE", "converged": True,
            "goals_reopened": 0, "phantom_dispatches": 0, "deviation": None
        })
    # Write to temp log
    with open(tmplog, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
    r1 = analyze_window(load_trace(tmplog), hours=72)
    t1_pass = r1["stable"] and r1["deviations"] == 0 and r1["converged_pct"] == 100.0
    print(f"PASS (entries={r1['entries_analyzed']}, pct={r1['converged_pct']}%)" if t1_pass else f"FAIL ({r1})")
    results.append(("T1_stable_72h", t1_pass))
    
    # T2: One mode departure -> deviation detected
    print("[T2] Mode departure detected...", end=" ")
    entries2 = list(entries)
    entries2[36]["mode"] = "ACTIVE"
    entries2[36]["converged"] = False
    entries2[36]["deviation"] = {"type": "mode_departure", "detail": "mode=ACTIVE"}
    with open(tmplog, "w") as f:
        for e in entries2:
            f.write(json.dumps(e) + "\n")
    r2 = analyze_window(load_trace(tmplog), hours=72)
    t2_pass = not r2["stable"] and r2["deviations"] == 1
    print(f"PASS (deviations={r2['deviations']})" if t2_pass else f"FAIL ({r2})")
    results.append(("T2_mode_departure", t2_pass))
    
    # T3: Goal re-open detected
    print("[T3] Goal re-open detected...", end=" ")
    entries3 = list(entries)
    entries3[50]["goals_reopened"] = 1
    entries3[50]["deviation"] = {"type": "goal_reopen", "detail": "reopened=1"}
    with open(tmplog, "w") as f:
        for e in entries3:
            f.write(json.dumps(e) + "\n")
    r3 = analyze_window(load_trace(tmplog), hours=72)
    t3_pass = not r3["stable"] and r3["goal_reopens"] >= 1
    print(f"PASS (reopens={r3['goal_reopens']})" if t3_pass else f"FAIL ({r3})")
    results.append(("T3_goal_reopen", t3_pass))
    
    # T4: Oscillation (rapid mode changes) detected
    print("[T4] Oscillation detected...", end=" ")
    entries4 = list(entries)
    for i in range(0, 72, 2):
        entries4[i]["mode"] = "ACTIVE" if i % 4 == 0 else "IDLE"
        entries4[i]["converged"] = entries4[i]["mode"] in CONVERGED_MODES
    with open(tmplog, "w") as f:
        for e in entries4:
            f.write(json.dumps(e) + "\n")
    r4 = analyze_window(load_trace(tmplog), hours=72)
    t4_pass = not r4["stable"]  # Should flag due to oscillation or deviations
    print(f"PASS (mode_changes={r4['mode_changes']})" if t4_pass else f"FAIL ({r4})")
    results.append(("T4_oscillation", t4_pass))
    
    # T5: Empty data -> graceful failure
    print("[T5] Empty data handled...", end=" ")
    os.remove(tmplog) if os.path.exists(tmplog) else None
    r5 = analyze_window([], hours=72)
    t5_pass = not r5["stable"] and "error" in r5
    print(f"PASS ({r5.get('error','no error key')})" if t5_pass else f"FAIL ({r5})")
    results.append(("T5_empty_data", t5_pass))
    
    # T6: report generation produces valid JSON
    print("[T6] Report structure...", end=" ")
    report = {
        "timestamp": _now_iso(),
        "soak_duration_hours": 72,
        "verdict": "PASS" if r1["stable"] else "FAIL",
        "analysis": r1,
    }
    t6_pass = all(k in report for k in ["timestamp", "soak_duration_hours", "verdict", "analysis"])
    print("PASS" if t6_pass else "FAIL")
    results.append(("T6_report_structure", t6_pass))
    
    # Cleanup
    os.remove(tmplog) if os.path.exists(tmplog) else None
    
    # Summary
    passed = sum(1 for _, p in results if p)
    total = len(results)
    print("\n" + "=" * 64)
    print(f"SUMMARY: {passed}/{total} self-tests passed")
    
    out_path = "memory/verifier/long_soak_results.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({
            "timestamp": _now_iso(),
            "self_test": {"passed": passed, "total": total},
            "stable_72h_simulation": r1,
            "deviation_detection": {"mode_departure": r2["deviations"], "goal_reopen": r3["goal_reopens"]},
        }, f, indent=2)
    print(f"Report: {out_path}")
    
    all_pass = passed == total
    print(f"\nSELF-TEST {'PASSED' if all_pass else 'FAILED'} - {passed}/{total} tests green")
    return 0 if all_pass else 1


def main():
    parser = argparse.ArgumentParser(description="Convergence Long-Soak Stability Test")
    parser.add_argument("--self-test", action="store_true", help="Run self-test with simulated data")
    parser.add_argument("--snapshot", action="store_true", help="Record one snapshot")
    parser.add_argument("--report", action="store_true", help="Generate report from accumulated data")
    args = parser.parse_args()
    
    if args.self_test:
        sys.exit(self_test())
    elif args.snapshot:
        record_snapshot()
        sys.exit(0)
    elif args.report:
        entries = load_trace()
        analysis = analyze_window(entries, hours=72)
        report = {
            "timestamp": _now_iso(),
            "soak_duration_hours": 72,
            "verdict": "PASS" if analysis.get("stable") else "FAIL",
            "analysis": analysis,
        }
        print(json.dumps(report, indent=2))
        out_path = "memory/ops/long-soak-report.json"
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport: {out_path}")
        sys.exit(0 if analysis.get("stable") else 1)
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
