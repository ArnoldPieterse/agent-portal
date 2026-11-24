"""Steady-State Detector — Orchestrator cycle-17 goal 5 (2026-11-25).

When 3 consecutive cycles ALL satisfy:
  1. Human interventions < 2 per cycle
  2. Cycle duration CV (coefficient of variation) < 15%
  3. Zero re-work (no goal reopened)

→ declare STEADY-STATE mode, write to fleet-mode.json.

Usage: python memory/orchestrator/steady_state_detector.py [--simulate]
"""
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OPS_DIR = os.path.join(HERE, "memory", "ops")
FLEET_MODE_PATH = os.path.join(OPS_DIR, "fleet-mode.json")
DURATIONS_PATH = os.path.join(OPS_DIR, "cycle-durations.jsonl")
INTERVENTIONS_PATH = os.path.join(OPS_DIR, "human-interventions.jsonl")
REWORK_LOG_PATH = os.path.join(OPS_DIR, "rework-log.jsonl")

# Thresholds
MAX_INTERVENTIONS_PER_CYCLE = 2   # < 2 means at most 1
MAX_DURATION_CV_PCT = 15.0        # coefficient of variation in percent
CONSECUTIVE_CYCLES_REQUIRED = 3


def _read_jsonl(path, max_lines=500):
    """Read a JSONL file, return list of dicts."""
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()[-max_lines:]
        out = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        return out
    except OSError:
        return []


def _read_json(path):
    """Read a JSON file, return {} on failure."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _get_cycle_durations():
    """Return list of {cycle:int, duration_h:float} sorted by cycle."""
    entries = _read_jsonl(DURATIONS_PATH)
    out = []
    for e in entries:
        try:
            out.append({"cycle": int(e.get("cycle", 0)), "duration_h": float(e.get("duration_hours", 0))})
        except (ValueError, TypeError):
            continue
    return sorted(out, key=lambda x: x["cycle"])


def _get_interventions_per_cycle():
    """Return {cycle:int, count:int}."""
    entries = _read_jsonl(INTERVENTIONS_PATH)
    counts = {}
    for e in entries:
        try:
            c = int(e.get("cycle", 0))
        except (ValueError, TypeError):
            continue
        counts[c] = counts.get(c, 0) + 1
    return counts


def _get_rework_count_for_cycle(cycle):
    """Count reworked goals in a given cycle from rework-log.jsonl."""
    entries = _read_jsonl(REWORK_LOG_PATH)
    count = 0
    for e in entries:
        if int(e.get("cycle", -1)) == cycle:
            count += 1
    return count


def check_criteria(cycle):
    """Check all 3 steady-state criteria for a given cycle.
    Returns (all_pass: bool, details: dict).
    """
    # Criterion 1: interventions < MAX_INTERVENTIONS_PER_CYCLE
    int_counts = _get_interventions_per_cycle()
    n_interventions = int_counts.get(cycle, 0)
    crit1 = n_interventions < MAX_INTERVENTIONS_PER_CYCLE

    # Criterion 2: duration variance (CV) < 15% — computed over the window of 3 cycles ending at `cycle`
    durations = _get_cycle_durations()
    cycle_nums = [d["cycle"] for d in durations]
    if cycle in cycle_nums:
        idx = cycle_nums.index(cycle)
        # Get up to 3 cycles ending at this one
        window = durations[max(0, idx - 2):idx + 1]
    else:
        window = durations[-3:]

    vals = [d["duration_h"] for d in window if d["duration_h"] > 0]
    if len(vals) >= 2:
        mean_v = statistics.mean(vals)
        stdev_v = statistics.stdev(vals) if len(vals) >= 2 else 0.0
        cv_pct = (stdev_v / mean_v * 100) if mean_v > 0 else 0.0
    elif len(vals) == 1:
        cv_pct = 0.0
    else:
        cv_pct = 0.0  # no data, assume pass

    crit2 = cv_pct < MAX_DURATION_CV_PCT

    # Criterion 3: zero rework
    n_rework = _get_rework_count_for_cycle(cycle)
    crit3 = n_rework == 0

    all_pass = crit1 and crit2 and crit3
    details = {
        "cycle": cycle,
        "interventions": n_interventions,
        "intervention_ok": crit1,
        "duration_cv_pct": round(cv_pct, 2),
        "duration_ok": crit2,
        "rework_count": n_rework,
        "rework_ok": crit3,
        "all_pass": all_pass,
    }
    return all_pass, details


def detect_steady_state():
    """Run detection over the last N cycles. Returns (is_steady, report)."""
    durations = _get_cycle_durations()
    if len(durations) < CONSECUTIVE_CYCLES_REQUIRED:
        return False, {"error": f"need >= {CONSECUTIVE_CYCLES_REQUIRED} cycles, have {len(durations)}"}

    # Take last 3 cycles
    recent = durations[-CONSECUTIVE_CYCLES_REQUIRED:]
    results = []
    all_three_pass = True
    for d in recent:
        passed, details = check_criteria(d["cycle"])
        results.append(details)
        if not passed:
            all_three_pass = False

    is_steady = all_three_pass
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cycles_checked": [d["cycle"] for d in recent],
        "details": results,
        "steady_state": is_steady,
    }
    return is_steady, report


def write_fleet_mode(mode="STEADY-STATE", extra=None):
    """Update fleet-mode.json with the new mode."""
    current = _read_json(FLEET_MODE_PATH)
    if not current:
        current = {"mode": "WORK", "timestamp": datetime.now(timezone.utc).isoformat()}

    current["mode"] = mode
    current["timestamp"] = datetime.now(timezone.utc).isoformat()
    if extra:
        current.update(extra)

    with open(FLEET_MODE_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)
    return current


def run(simulate=False):
    """Main entry. If simulate=True, test with synthetic data."""
    if simulate:
        return _run_simulate()

    is_steady, report = detect_steady_state()
    print(json.dumps(report, indent=2))

    if is_steady:
        write_fleet_mode("STEADY-STATE", {"steady_state_since": report["timestamp"], "cycles_in_steady_state": 3})
        print(f"\n>>> STEADY-STATE DECLARED. fleet-mode.json updated.")
    else:
        # Ensure mode is not stuck in STEADY-STATE if we've exited
        current = _read_json(FLEET_MODE_PATH)
        if current.get("mode") == "STEADY-STATE":
            write_fleet_mode("WORK", {"steady_state_exited_at": report["timestamp"]})
            print("\n>>> STEADY-STATE EXITED. fleet-mode.json reset to WORK.")

    return is_steady, report


def _run_simulate():
    """Simulate 3 consecutive good cycles and verify detection triggers."""
    import tempfile, shutil

    # Use a temp directory structure for simulation
    tmp = tempfile.mkdtemp(prefix="ss_detect_")
    try:
        ops_tmp = os.path.join(tmp, "memory", "ops")
        os.makedirs(ops_tmp)

        # Patch paths for simulation
        global DURATIONS_PATH, INTERVENTIONS_PATH, REWORK_LOG_PATH, FLEET_MODE_PATH
        orig_paths = (DURATIONS_PATH, INTERVENTIONS_PATH, REWORK_LOG_PATH, FLEET_MODE_PATH)
        DURATIONS_PATH = os.path.join(ops_tmp, "cycle-durations.jsonl")
        INTERVENTIONS_PATH = os.path.join(ops_tmp, "human-interventions.jsonl")
        REWORK_LOG_PATH = os.path.join(ops_tmp, "rework-log.jsonl")
        FLEET_MODE_PATH = os.path.join(ops_tmp, "fleet-mode.json")

        # Create 3 cycles with low intervention, stable duration, zero rework
        durations = [
            {"cycle": 14, "duration_hours": 24.0},
            {"cycle": 15, "duration_hours": 25.0},
            {"cycle": 16, "duration_hours": 24.5},
        ]
        with open(DURATIONS_PATH, "w") as f:
            for d in durations:
                f.write(json.dumps(d) + "\n")

        # Interventions: at most 1 per cycle (satisfies <2)
        interventions = [
            {"cycle": 14, "type": "approve", "ts": "2026-11-23T10:00:00Z"},
            {"cycle": 15, "type": "unblock", "ts": "2026-11-23T14:00:00Z"},
        ]
        with open(INTERVENTIONS_PATH, "w") as f:
            for i in interventions:
                f.write(json.dumps(i) + "\n")

        # No rework
        open(REWORK_LOG_PATH, "w").close()

        # Initial fleet-mode
        with open(FLEET_MODE_PATH, "w") as f:
            json.dump({"mode": "WORK", "timestamp": "2026-11-23T00:00:00Z"}, f)

        # Run detection
        is_steady, report = detect_steady_state()
        assert is_steady, f"Expected steady-state but got: {json.dumps(report, indent=2)}"
        assert report["steady_state"] is True
        for d in report["details"]:
            assert d["all_pass"], f"Cycle {d['cycle']} should pass all criteria: {d}"

        # Write fleet mode
        write_fleet_mode("STEADY-STATE", {"steady_state_since": report["timestamp"]})
        fm = _read_json(FLEET_MODE_PATH)
        assert fm["mode"] == "STEADY-STATE", f"fleet-mode.json not updated: {fm}"

        # Test negative case: add 2 interventions to cycle 16 → should NOT be steady (count=2, not <2)
        with open(INTERVENTIONS_PATH, "a") as f:
            f.write(json.dumps({"cycle": 16, "type": "redirect", "ts": "2026-11-24T10:00:00Z"}) + "\n")
            f.write(json.dumps({"cycle": 16, "type": "unblock", "ts": "2026-11-24T12:00:00Z"}) + "\n")

        is_steady2, report2 = detect_steady_state()
        assert not is_steady2, f"Expected NOT steady-state with 2 interventions in cycle 16"

        print("SIMULATION PASS:")
        print(f"  - 3 good cycles → STEADY-STATE detected: {is_steady}")
        print(f"  - fleet-mode.json mode = {fm['mode']}")
        print(f"  - Negative case (2 interventions) → not steady: {not is_steady2}")
        print("SELFTEST PASS")
        return True

    finally:
        # Restore original paths
        DURATIONS_PATH, INTERVENTIONS_PATH, REWORK_LOG_PATH, FLEET_MODE_PATH = orig_paths
        shutil.rmtree(tmp, ignore_errors=True)


def selftest():
    """Run simulation-based self-test."""
    ok = _run_simulate()
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    if "--simulate" in sys.argv:
        _run_simulate()
    elif "--selftest" in sys.argv:
        selftest()
    else:
        run()
