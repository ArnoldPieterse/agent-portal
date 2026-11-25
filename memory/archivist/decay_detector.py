#!/usr/bin/env python
"""Autonomy Decay Detector - rolling 3-cycle window.
Usage: python memory/archivist/decay_detector.py [--window 3] [--json]
Output: prints signal levels + composite score; --json emits machine-readable dict.
Exit: always 0 (informational, not a gate).
"""
import json, pathlib, sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
WINDOW = 3

def load_interventions():
    p = ROOT / "memory/ops/human-interventions.jsonl"
    if not p.exists(): return []
    return [json.loads(line) for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]

def load_cycle_closeouts():
    p = ROOT / "memory/ops/cycle-closeout.jsonl"
    if not p.exists(): return []
    return [json.loads(line) for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]

def get_max_cycle(interventions, closeouts):
    cycles = [i.get("cycle", 0) for i in interventions] + [c.get("cycle", 0) for c in closeouts]
    return max(cycles) if cycles else 0

def window_cycles(max_cycle, n=WINDOW):
    return set(range(max(1, max_cycle - n + 1), max_cycle + 1))

def compute_s1(interventions, cyc_window):
    esc_cycles = set()
    for iv in interventions:
        if iv.get("cycle") in cyc_window and iv.get("type") in ("redirect", "unblock"):
            esc_cycles.add(iv["cycle"])
    total = len(cyc_window) or 1
    return len(esc_cycles) / total

def compute_s2(cyc_window):
    fix_count = 0
    for f in ROOT.glob("memory/**/evidence-*-fix-*"):
        fix_count += 1
    for f in ROOT.glob("memory/**/*-reverify-*"):
        fix_count += 1
    total_goals_est = 10 * len(cyc_window)
    return min(1.0, fix_count / max(1, total_goals_est))

def compute_s3(interventions, cyc_window):
    count = sum(1 for iv in interventions if iv.get("cycle") in cyc_window)
    total = len(cyc_window) or 1
    return count / total

def normalize(value, red_threshold):
    return min(1.0, value / red_threshold)

def level(value, green_max, amber_max):
    if value <= green_max: return "GREEN"
    if value <= amber_max: return "AMBER"
    return "RED"

def main():
    global WINDOW
    if "--window" in sys.argv:
        i = sys.argv.index("--window")
        WINDOW = int(sys.argv[i+1])
    interventions = load_interventions()
    closeouts = load_cycle_closeouts()
    max_cyc = get_max_cycle(interventions, closeouts)
    cyc_win = window_cycles(max_cyc, WINDOW)
    s1 = compute_s1(interventions, cyc_win)
    s2 = compute_s2(cyc_win)
    s3 = compute_s3(interventions, cyc_win)
    s1_level = level(s1, 0.25, 0.50)
    s2_level = level(s2, 0.20, 0.40)
    s3_level = level(s3, 0.50, 1.50)
    composite = 0.4 * normalize(s1, 0.50) + 0.3 * normalize(s2, 0.40) + 0.3 * normalize(s3, 1.50)
    result = {
        "window_cycles": sorted(cyc_win),
        "signals": {
            "S1_escalation_rate": {"value": round(s1, 3), "level": s1_level},
            "S2_rework_rate": {"value": round(s2, 3), "level": s2_level},
            "S3_intervention_freq": {"value": round(s3, 3), "level": s3_level},
        },
        "composite_decay_score": round(composite, 3),
        "interpretation": (
            "CRITICAL" if composite > 0.75 else
            "CAUTION" if composite > 0.50 else
            "WATCH" if composite > 0.25 else
            "HEALTHY"
        ),
    }
    if "--json" in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        print(f"Window: cycles {result['window_cycles']}")
        for k, v in result["signals"].items():
            print(f"  {k}: {v['value']:.3f} [{v['level']}]")
        print(f"  Composite: {composite:.3f} -> {result['interpretation']}")

if __name__ == "__main__":
    main()
