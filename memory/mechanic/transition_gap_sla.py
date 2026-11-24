"""Transition Gap SLA Tracker.

Measures time from goal_pct=100 (all goals verified) to new cycle goals being set.
Target: <4h. Flags if >4h.

Output: memory/ops/transition-gaps.jsonl (one entry per transition)
Summary: memory/ops/transition-gaps-summary.json

Usage:
  python memory/mechanic/transition_gap_sla.py          # live (reads cycle markers)
  python memory/mechanic/transition_gap_sla.py --selftest
"""
import json, pathlib, datetime, sys

BASE = pathlib.Path(__file__).resolve().parent.parent.parent
OUTPUT_JSONL = BASE / "memory" / "ops" / "transition-gaps.jsonl"
OUTPUT_SUMMARY = BASE / "memory" / "ops" / "transition-gaps-summary.json"
TARGET_HOURS = 4.0

def compute_gap_hours(ts_start, ts_end):
    """Compute hours between two ISO timestamps."""
    t1 = datetime.datetime.fromisoformat(ts_start)
    t2 = datetime.datetime.fromisoformat(ts_end)
    return (t2 - t1).total_seconds() / 3600.0

def record_transition(cycle_from, cycle_to, ts_complete, ts_new_goals):
    """Record a single transition gap."""
    gap_h = compute_gap_hours(ts_complete, ts_new_goals)
    entry = {
        "cycle_from": cycle_from,
        "cycle_to": cycle_to,
        "ts_complete": ts_complete,
        "ts_new_goals": ts_new_goals,
        "gap_hours": round(gap_h, 2),
        "within_sla": gap_h <= TARGET_HOURS,
        "flagged": gap_h > TARGET_HOURS,
    }
    OUTPUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry

def summary_from_entries(entries):
    """Compute summary from transition entries."""
    if not entries:
        return {"total_transitions": 0, "mean_gap_hours": None, "sla_compliance_pct": None, "flagged_count": 0}
    
    gaps = [e["gap_hours"] for e in entries]
    flagged = sum(1 for e in entries if e["flagged"])
    compliant = len(entries) - flagged
    return {
        "total_transitions": len(entries),
        "mean_gap_hours": round(sum(gaps) / len(gaps), 2),
        "max_gap_hours": max(gaps),
        "min_gap_hours": min(gaps),
        "sla_target_hours": TARGET_HOURS,
        "sla_compliance_pct": round(100.0 * compliant / len(entries), 1),
        "flagged_count": flagged,
    }

def selftest():
    """Verify: 3 simulated transitions; gap>4h correctly flagged."""
    errors = []

    # Simulate 3 transitions
    t1_complete = "2026-11-20T14:00:00"
    t1_new = "2026-11-20T16:30:00"   # 2.5h -> within SLA
    
    t2_complete = "2026-11-21T10:00:00"
    t2_new = "2026-11-21T14:30:00"   # 4.5h -> OVER SLA
    
    t3_complete = "2026-11-22T09:00:00"
    t3_new = "2026-11-22T09:45:00"   # 0.75h -> well within SLA

    entries = []
    
    # Test 1: within SLA
    e1 = record_transition(15, 16, t1_complete, t1_new)
    entries.append(e1)
    if e1["gap_hours"] != 2.5:
        errors.append(f"Gap 1: expected 2.5h, got {e1['gap_hours']}")
    if e1["flagged"]:
        errors.append("Transition 1 should NOT be flagged (2.5h < 4h)")
    if not e1["within_sla"]:
        errors.append("Transition 1 should be within SLA")

    # Test 2: over SLA
    e2 = record_transition(16, 17, t2_complete, t2_new)
    entries.append(e2)
    if e2["gap_hours"] != 4.5:
        errors.append(f"Gap 2: expected 4.5h, got {e2['gap_hours']}")
    if not e2["flagged"]:
        errors.append("Transition 2 SHOULD be flagged (4.5h > 4h)")
    if e2["within_sla"]:
        errors.append("Transition 2 should NOT be within SLA")

    # Test 3: well within SLA
    e3 = record_transition(17, 18, t3_complete, t3_new)
    entries.append(e3)
    if e3["gap_hours"] != 0.75:
        errors.append(f"Gap 3: expected 0.75h, got {e3['gap_hours']}")
    if e3["flagged"]:
        errors.append("Transition 3 should NOT be flagged (0.75h < 4h)")

    # Test 4: summary computation
    s = summary_from_entries(entries)
    if s["total_transitions"] != 3:
        errors.append(f"Summary total: expected 3, got {s['total_transitions']}")
    if s["flagged_count"] != 1:
        errors.append(f"Flagged count: expected 1, got {s['flagged_count']}")
    if s["sla_compliance_pct"] != 66.7:
        errors.append(f"SLA compliance: expected 66.7%, got {s['sla_compliance_pct']}")
    # mean = (2.5 + 4.5 + 0.75) / 3 = 7.75/3 = 2.58
    if abs(s["mean_gap_hours"] - 2.58) > 0.01:
        errors.append(f"Mean gap: expected ~2.58, got {s['mean_gap_hours']}")

    # Test 5: empty summary
    es = summary_from_entries([])
    if es["total_transitions"] != 0 or es["sla_compliance_pct"] is not None:
        errors.append("Empty summary handling incorrect")

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return False
    else:
        print("PASS: all 5 selftest checks OK")
        print(f"  3 transitions: 2.5h(PASS), 4.5h(FLAGGED), 0.75h(PASS)")
        print(f"  Summary: mean=2.58h, compliance=66.7%, flagged=1")
        return True

def main():
    if "--selftest" in sys.argv:
        ok = selftest()
        # Clean up test entries from jsonl (they were appended during selftest)
        if OUTPUT_JSONL.exists():
            lines = OUTPUT_JSONL.read_text(encoding="utf-8").strip().split("\n")
            # Keep only non-selftest entries (those with real cycle numbers > 18)
            real = [l for l in lines if l and json.loads(l)["cycle_from"] > 18]
            if real:
                OUTPUT_JSONL.write_text("\n".join(real) + "\n", encoding="utf-8")
            else:
                OUTPUT_JSONL.unlink()
        sys.exit(0 if ok else 1)

    # Live mode: read existing entries and write summary
    entries = []
    if OUTPUT_JSONL.exists():
        with open(OUTPUT_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))

    s = summary_from_entries(entries)
    s["generated"] = datetime.datetime.now().isoformat()
    OUTPUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_SUMMARY, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2)
    print(f"Wrote {OUTPUT_SUMMARY}: {s['total_transitions']} transitions, compliance={s.get('sla_compliance_pct','N/A')}%")

if __name__ == "__main__":
    main()
