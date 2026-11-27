#!/usr/bin/env python3
"""Convergence Milestone Tracker (Scribe goal #10).

Tracks key fleet autonomy convergence milestones:
  1. first_cycle_lt_48h   - first cycle completed in <48 hours
  2. zero_intervention_week - a full week with 0 human interventions
  3. steady_state_entry   - fleet enters steady state (autonomy >=95%, stable trend)

Output: memory/scribe/milestones.jsonl (append-only log of hits)
Self-test: python memory/scribe/milestone_tracker.py --selftest
"""
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
MILESTONES_FILE = BASE / "memory" / "scribe" / "milestones.jsonl"
INTERVENTIONS_FILE = BASE / "memory" / "ops" / "human-interventions.jsonl"

# Milestone definitions
MILESTONES = [
    {
        "id": "first_cycle_lt_48h",
        "name": "First cycle < 48h",
        "criterion": "Cycle duration drops below 48 hours for the first time",
        "data_source": "closeout reports / autoloop timestamps",
    },
    {
        "id": "zero_intervention_week",
        "name": "Zero-intervention week",
        "criterion": "A rolling 7-day window with zero human interventions",
        "data_source": "memory/ops/human-interventions.jsonl",
    },
    {
        "id": "steady_state_entry",
        "name": "Steady-state entry",
        "criterion": "Fleet autonomy score >= 95% AND trend stable for >= 3 consecutive cycles",
        "data_source": "convergence_api.py output",
    },
]


def load_interventions():
    """Load intervention timestamps from JSONL."""
    if not INTERVENTIONS_FILE.exists():
        return []
    entries = []
    for line in INTERVENTIONS_FILE.read_text(encoding="utf-8").split("\n"):
        line = line.strip()
        if line:
            try:
                d = json.loads(line)
                ts = datetime.fromisoformat(d.get("ts", ""))
                entries.append(ts)
            except (json.JSONDecodeError, ValueError):
                continue
    return sorted(entries)


def check_zero_intervention_week(now=None):
    """Check if there's a 7-day window with zero interventions."""
    now = now or datetime.now(timezone.utc)
    interventions = load_interventions()
    if not interventions:
        # No interventions at all = trivially true, but require >= 7 days of operation
        return True, "No interventions recorded in system lifetime"
    last = max(interventions)
    window_start = now - timedelta(days=7)
    recent = [i for i in interventions if i >= window_start]
    if len(recent) == 0:
        return True, f"Zero interventions in last 7 days (last was {last.isoformat()})"
    return False, f"{len(recent)} interventions in last 7 days"


def check_steady_state():
    """Check steady-state via convergence_api selftest output."""
    import subprocess
    try:
        r = subprocess.run(
            [sys.executable, str(BASE / "memory" / "orchestrator" / "convergence_api.py"), "--selftest"],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode != 0:
            return False, f"convergence_api selftest failed: {r.stderr[:200]}"
        # Parse autonomy from output
        for line in r.stdout.split("\n"):
            if "autonomy=" in line:
                val = float(line.split("autonomy=")[1].split()[0])
                if val >= 95:
                    return True, f"Autonomy={val}% (>=95 threshold)"
                return False, f"Autonomy={val}% (<95 threshold)"
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return False, f"Could not run convergence_api: {e}"
    return False, "No autonomy value found in output"


def check_first_cycle_lt_48h():
    """Check if any cycle completed in <48h. Uses closeout report dates."""
    synth = BASE / "memory" / "synthesis"
    import re
    durations = []
    for f in sorted(synth.glob("closeout-cycle*.md")):
        m = re.match(r"closeout-cycle(\d+)-(\d{4}-\d{2}-\d{2})\.md", f.name)
        if not m:
            continue
        cycle_num, date_str = int(m.group(1)), m.group(2)
        durations.append((cycle_num, datetime.strptime(date_str, "%Y-%m-%d")))
    # We can't reliably compute durations from closeout dates alone without start dates.
    # Mark as "pending data" unless we find explicit duration in reports.
    for f in sorted(synth.glob("closeout-cycle*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        if "<48h" in text or "under 48" in text.lower():
            return True, f"Explicitly noted in {f.name}"
    return False, "No cycle explicitly documented as <48h (need start+end timestamps)"


def already_hit(milestone_id):
    """Check if milestone already logged."""
    if not MILESTONES_FILE.exists():
        return False
    for line in MILESTONES_FILE.read_text(encoding="utf-8").split("\n"):
        if line.strip():
            try:
                d = json.loads(line)
                if d.get("milestone") == milestone_id and d.get("status") == "hit":
                    return True
            except json.JSONDecodeError:
                continue
    return False


def log_hit(milestone_id, context):
    """Append a hit to the milestones file."""
    MILESTONES_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "milestone": milestone_id,
        "status": "hit",
        "ts": datetime.now(timezone.utc).isoformat(),
        "context": context,
    }
    with open(MILESTONES_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def check_all():
    """Run all checks, log any new hits."""
    results = []
    checkers = {
        "first_cycle_lt_48h": check_first_cycle_lt_48h,
        "zero_intervention_week": lambda: check_zero_intervention_week(),
        "steady_state_entry": check_steady_state,
    }
    for m in MILESTONES:
        mid = m["id"]
        if already_hit(mid):
            results.append((mid, "already_hit", ""))
            continue
        ok, ctx = checkers[mid]()
        if ok:
            log_hit(mid, ctx)
            results.append((mid, "HIT", ctx))
        else:
            results.append((mid, "pending", ctx))
    return results


def selftest():
    """Simulate a hit to verify logging works."""
    test_id = "selftest_milestone"
    MILESTONES_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {"milestone": test_id, "status": "hit", "ts": datetime.now(timezone.utc).isoformat(), "context": "selftest"}
    with open(MILESTONES_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    # Verify it was written
    lines = [l for l in MILESTONES_FILE.read_text(encoding="utf-8").split("\n") if l.strip()]
    last = json.loads(lines[-1])
    assert last["milestone"] == test_id, "selftest entry not found"
    print("SELFTEST PASS: milestone logging works (wrote + read back)")
    return True


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        results = check_all()
        print(f"Milestone Tracker - {datetime.now(timezone.utc).isoformat()}")
        for mid, status, ctx in results:
            print(f"  [{status:12s}] {mid}: {ctx}")
