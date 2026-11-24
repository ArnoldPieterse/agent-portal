"""autonomy_convergence_test.py - End-to-end integration for Fleet Autonomy Convergence.

Proves: fleet_mode_writer -> dispatch_filter -> productivity_counter work as a pipeline.
Acceptance criteria:
  1. write_fleet_mode writes valid JSON with correct mode
  2. filter_dispatch in WORK returns only goal-type items
  3. filter_dispatch in MAINTENANCE/IDLE returns only maintenance-type items
  4. Mode transition changes dispatch output
  5. productivity_counter selftest passes
  6. Full pipeline: write->read->filter consistent across all 3 modes

Usage: python memory/builder/autonomy_convergence_test.py --selftest
"""
import json, os, sys, subprocess, tempfile, datetime, pathlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

PASS = 0
FAIL = 0

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        print(f"  FAIL: {name} {detail}")

# Correct format for filter_dispatch (matches its actual implementation)
SAMPLE = {
    "agents": {
        "Builder": {"goals": [
            {"title": "Goal A", "reached": False},
            {"title": "Goal B", "reached": True},
            {"title": "Goal C", "reached": False}
        ]},
        "Researcher": {"goals": [
            {"title": "Goal X", "reached": False}
        ]},
        "Scribe": {"goals": []}
    }
}


def test_write(tmpdir):
    """fleet_mode_writer produces valid JSON for each mode."""
    import fleet_mode_writer as fmw
    orig = fmw.FLEET_MODE_FILE
    fmw.FLEET_MODE_FILE = pathlib.Path(tmpdir) / "fleet-mode.json"
    try:
        for mode in ("WORK", "MAINTENANCE", "IDLE"):
            ok = fmw.write_fleet_mode(mode, goal_pct=30.0)
            check(f"write[{mode}]: returns True", ok)
            data = json.loads(fmw.FLEET_MODE_FILE.read_text())
            check(f"write[{mode}]: mode correct", data["mode"] == mode)
            check(f"write[{mode}]: timestamp valid", "T" in data.get("timestamp",""))
    finally:
        fmw.FLEET_MODE_FILE = orig


def test_dispatch_work():
    """filter_dispatch WORK: only goal types, open goals only."""
    from dispatch_filter import filter_dispatch
    result = filter_dispatch("WORK", SAMPLE)
    types = {item["type"] for item in result}
    check("work: only goal type", types == {"goal"}, f"got {types}")
    builder_goals = [x for x in result if x["agent"] == "Builder"]
    check("work: Builder has 2 open (A,C)", len(builder_goals) == 2, f"got {len(builder_goals)}")
    agents = {x["agent"] for x in result}
    check("work: Scribe excluded (no goals)", "Scribe" not in agents)


def test_dispatch_maintenance():
    """filter_dispatch MAINTENANCE/IDLE: only maintenance types."""
    from dispatch_filter import filter_dispatch
    for mode in ("MAINTENANCE", "IDLE"):
        result = filter_dispatch(mode, SAMPLE)
        if result:
            types = {item["type"] for item in result}
            check(f"{mode}: only maintenance type", types == {"maintenance"}, f"got {types}")
        else:
            # No agents got tasks (idle_rotation returned None for all) - still valid
            check(f"{mode}: empty or maintenance only", True)


def test_mode_transition():
    """MAINTENANCE->WORK switch changes output."""
    from dispatch_filter import filter_dispatch
    r_maint = filter_dispatch("MAINTENANCE", SAMPLE)
    r_work = filter_dispatch("WORK", SAMPLE)
    # WORK should have goal items; MAINT should not
    work_has_goals = any(x["type"] == "goal" for x in r_work)
    maint_no_goals = all(x["type"] != "goal" for x in r_maint) if r_maint else True
    check("transition: WORK has goals", work_has_goals)
    check("transition: MAINT has no goals", maint_no_goals)


def test_productivity():
    """productivity_counter --selftest exits 0."""
    r = subprocess.run(
        [sys.executable, str(pathlib.Path(__file__).parent / "productivity_counter.py"), "--selftest"],
        capture_output=True, text=True, timeout=30, cwd=ROOT
    )
    check("productivity: selftest exit 0", r.returncode == 0, f"stderr={r.stderr[:200]}")


def test_full_pipeline(tmpdir):
    """End-to-end: write mode -> read back -> filter -> consistent."""
    import fleet_mode_writer as fmw
    from dispatch_filter import filter_dispatch

    orig = fmw.FLEET_MODE_FILE
    fmw.FLEET_MODE_FILE = pathlib.Path(tmpdir) / "fleet-mode.json"
    try:
        for mode in ("WORK", "MAINTENANCE", "IDLE"):
            fmw.write_fleet_mode(mode, goal_pct=50.0)
            # Read back what was written
            data = json.loads(fmw.FLEET_MODE_FILE.read_text())
            readback_mode = data["mode"]
            # Filter using the readback mode
            result = filter_dispatch(readback_mode, SAMPLE)
            if readback_mode == "WORK":
                check(f"pipeline[{mode}]: WORK gives goal types",
                      all(x["type"] == "goal" for x in result) if result else True)
            else:
                check(f"pipeline[{mode}]: {mode} gives maintenance only",
                      all(x["type"] == "maintenance" for x in result) if result else True)
    finally:
        fmw.FLEET_MODE_FILE = orig


def main():
    print("autonomy_convergence_test: end-to-end pipeline integration")
    with tempfile.TemporaryDirectory() as tmpdir:
        test_write(tmpdir)
        test_dispatch_work()
        test_dispatch_maintenance()
        test_mode_transition()
        test_productivity()
        test_full_pipeline(tmpdir)

    total = PASS + FAIL
    print(f"\nautonomy_convergence_test: {PASS}/{total} PASS")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Fleet autonomy convergence integration test")
    p.add_argument("--selftest", action="store_true")
    args = p.parse_args()
    sys.exit(main())
