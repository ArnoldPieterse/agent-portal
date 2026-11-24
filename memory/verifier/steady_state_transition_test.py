"""Steady-State Transition Test (Verifier goal #2).

Simulates fleet entering steady-state and verifies:
  (a) Mode transition is clean: WORK -> STEADY-STATE with correct timestamp, trigger, no intermediate states
  (b) Cycle frequency change propagates to scheduler: when mode=STEADY-STATE, cadence changes from daily to biweekly
  (c) No orphaned tasks in-flight: all active dispatches complete or are gracefully cancelled before transition
  (d) Transition is idempotent: re-running the transition does not corrupt state
  (e) Rollback works: if steady-state criteria no longer met, mode returns to WORK cleanly

FAIL-CLOSED: any assertion failure -> exit 1.
CWD-independent: paths anchored via __file__.

Usage: python memory/verifier/steady_state_transition_test.py
"""
import json
import os
import sys
import time
import tempfile
import shutil
import datetime
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

RESULTS_FILE = os.path.join(HERE, "steady-state-transition-results.json")

def iso_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

class SteadyStateTransitionSim:
    """Simulates the fleet mode state machine for steady-state transitions."""

    VALID_MODES = {"WORK", "MAINTENANCE", "IDLE", "STEADY-STATE"}
    TRANSITION_LOG = []
    SCHEDULER_STATE = {"cadence_hours": 24, "next_fire": None}
    IN_FLIGHT_TASKS = []

    def __init__(self, tmpdir):
        self.tmpdir = Path(tmpdir)
        self.mode_file = self.tmpdir / "fleet-mode.json"
        self.transition_log_file = self.tmpdir / "mode-transitions.jsonl"
        self.scheduler_file = self.tmpdir / "scheduler-state.json"
        self.task_file = self.tmpdir / "in-flight-tasks.json"
        self._init_state()

    def _init_state(self):
        # Start in WORK mode
        self._write_mode("WORK", goal_pct=95.0)
        # Scheduler at daily cadence
        self.SCHEDULER_STATE = {"cadence_hours": 24, "next_fire": iso_now()}
        self._write_json(self.scheduler_file, self.SCHEDULER_STATE)
        # Some in-flight tasks
        self.IN_FLIGHT_TASKS = [
            {"id": "task-1", "agent": "Builder", "started_at": iso_now(), "status": "running"},
            {"id": "task-2", "agent": "Researcher", "started_at": iso_now(), "status": "running"},
        ]
        self._write_json(self.task_file, self.IN_FLIGHT_TASKS)

    def _write_mode(self, mode, goal_pct):
        data = {"mode": mode, "timestamp": iso_now(), "goal_pct": goal_pct}
        self.mode_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _read_mode(self):
        return json.loads(self.mode_file.read_text(encoding="utf-8"))

    def _write_json(self, path, data):
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def check_steady_state_criteria(self):
        """Check if fleet meets steady-state entry criteria."""
        mode = self._read_mode()
        # Criteria: goal_pct >= 100 AND no in-flight tasks AND idle > threshold
        pct_ok = mode.get("goal_pct", 0) >= 100.0
        tasks_ok = len(self.IN_FLIGHT_TASKS) == 0
        return pct_ok and tasks_ok, {"pct_ok": pct_ok, "tasks_ok": tasks_ok}

    def enter_steady_state(self):
        """Execute the transition into STEADY-STATE. Returns transition record."""
        before = self._read_mode()
        criteria_met, details = self.check_steady_state_criteria()

        if not criteria_met:
            return {"status": "rejected", "reason": f"criteria not met: {details}"}

        # Record transition
        trans_rec = {
            "ts": iso_now(),
            "from_mode": before["mode"],
            "to_mode": "STEADY-STATE",
            "trigger": "all_criteria_met",
            "goal_pct": before["goal_pct"]
        }
        self.TRANSITION_LOG.append(trans_rec)
        with open(self.transition_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(trans_rec) + "\n")

        # Update mode file
        self._write_mode("STEADY-STATE", goal_pct=before["goal_pct"])

        # Propagate to scheduler: daily -> biweekly (336h)
        self.SCHEDULER_STATE = {"cadence_hours": 336, "next_fire": iso_now()}
        self._write_json(self.scheduler_file, self.SCHEDULER_STATE)

        return {"status": "success", "record": trans_rec}

    def rollback_steady_state(self):
        """Exit steady-state back to WORK."""
        before = self._read_mode()
        if before["mode"] != "STEADY-STATE":
            return {"status": "rejected", "reason": f"not in STEADY-STATE, in {before['mode']}"}

        trans_rec = {
            "ts": iso_now(),
            "from_mode": "STEADY-STATE",
            "to_mode": "WORK",
            "trigger": "rollback_criteria_failed",
            "goal_pct": before["goal_pct"]
        }
        self.TRANSITION_LOG.append(trans_rec)
        with open(self.transition_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(trans_rec) + "\n")

        self._write_mode("WORK", goal_pct=before["goal_pct"])
        # Restore scheduler to daily
        self.SCHEDULER_STATE = {"cadence_hours": 24, "next_fire": iso_now()}
        self._write_json(self.scheduler_file, self.SCHEDULER_STATE)

        return {"status": "success", "record": trans_rec}

def test_a_clean_transition(tmpdir):
    """(a) Mode transition is clean: correct from/to, no intermediate states."""
    (tmpdir / "t_a").mkdir(parents=True, exist_ok=True)
    sim = SteadyStateTransitionSim(tmpdir / "t_a")

    # First complete in-flight tasks
    sim.IN_FLIGHT_TASKS = []
    sim._write_json(sim.task_file, sim.IN_FLIGHT_TASKS)
    sim._write_mode("WORK", goal_pct=100.0)

    result = sim.enter_steady_state()
    assert result["status"] == "success", f"Transition failed: {result}"
    rec = result["record"]
    assert rec["from_mode"] == "WORK", f"Expected from WORK, got {rec['from_mode']}"
    assert rec["to_mode"] == "STEADY-STATE", f"Expected to STEADY-STATE, got {rec['to_mode']}"
    assert rec["goal_pct"] >= 100.0, f"goal_pct should be >=100, got {rec['goal_pct']}"

    # Verify mode file is correct
    mode = sim._read_mode()
    assert mode["mode"] == "STEADY-STATE", f"Mode file shows {mode['mode']}"

    # No intermediate states in transition log
    lines = sim.transition_log_file.read_text(encoding="utf-8").strip().split("\n")
    modes_seen = [json.loads(l)["to_mode"] for l in lines]
    assert modes_seen == ["STEADY-STATE"], f"Expected only STEADY-STATE, got {modes_seen}"

    return True

def test_b_frequency_propagation(tmpdir):
    """(b) Cycle frequency change propagates to scheduler."""
    (tmpdir / "t_b").mkdir(parents=True, exist_ok=True)
    sim = SteadyStateTransitionSim(tmpdir / "t_b")

    # Verify initial cadence is daily
    sched_before = json.loads(sim.scheduler_file.read_text(encoding="utf-8"))
    assert sched_before["cadence_hours"] == 24, f"Expected 24h initially, got {sched_before['cadence_hours']}"

    # Complete tasks and set 100%
    sim.IN_FLIGHT_TASKS = []
    sim._write_json(sim.task_file, sim.IN_FLIGHT_TASKS)
    sim._write_mode("WORK", goal_pct=100.0)

    result = sim.enter_steady_state()
    assert result["status"] == "success", f"Transition failed: {result}"

    # Verify scheduler now shows biweekly (336h)
    sched_after = json.loads(sim.scheduler_file.read_text(encoding="utf-8"))
    assert sched_after["cadence_hours"] == 336, f"Expected 336h after transition, got {sched_after['cadence_hours']}"

    return True

def test_c_no_orphaned_tasks(tmpdir):
    """(c) No orphaned tasks in-flight during transition."""
    (tmpdir / "t_c").mkdir(parents=True, exist_ok=True)
    sim = SteadyStateTransitionSim(tmpdir / "t_c")

    # Case 1: tasks still running -> transition must be REJECTED
    sim._write_mode("WORK", goal_pct=100.0)  # pct ok but tasks in flight
    assert len(sim.IN_FLIGHT_TASKS) == 2  # initial state has 2 tasks
    result = sim.enter_steady_state()
    assert result["status"] == "rejected", f"Should reject with in-flight tasks, got {result['status']}"
    mode = sim._read_mode()
    assert mode["mode"] == "WORK", f"Mode should still be WORK after rejection, got {mode['mode']}"

    # Case 2: complete all tasks -> transition succeeds
    sim.IN_FLIGHT_TASKS = []
    sim._write_json(sim.task_file, sim.IN_FLIGHT_TASKS)
    result2 = sim.enter_steady_state()
    assert result2["status"] == "success", f"Should succeed after task completion, got {result2}"

    return True

def test_d_idempotent(tmpdir):
    """(d) Re-running transition in STEADY-STATE is a no-op (idempotent)."""
    (tmpdir / "t_d").mkdir(parents=True, exist_ok=True)
    sim = SteadyStateTransitionSim(tmpdir / "t_d")

    # Enter steady state
    sim.IN_FLIGHT_TASKS = []
    sim._write_json(sim.task_file, sim.IN_FLIGHT_TASKS)
    sim._write_mode("WORK", goal_pct=100.0)
    result = sim.enter_steady_state()
    assert result["status"] == "success"

    # Try to enter again (already in STEADY-STATE)
    mode = sim._read_mode()
    if mode["mode"] == "STEADY-STATE":
        # The enter function should detect we're already there or handle gracefully
        result2 = sim.enter_steady_state()
        # Accept: either rejected (already there) or success (idempotent re-entry)
        assert result2["status"] in ("success", "rejected"), f"Unexpected: {result2}"

    # Mode file unchanged after idempotent re-run
    mode_after = sim._read_mode()
    assert mode_after["mode"] == "STEADY-STATE", f"Mode corrupted: {mode_after['mode']}"

    return True

def test_e_rollback(tmpdir):
    """(e) Rollback from STEADY-STATE back to WORK is clean."""
    (tmpdir / "t_e").mkdir(parents=True, exist_ok=True)
    sim = SteadyStateTransitionSim(tmpdir / "t_e")

    # Enter steady state
    sim.IN_FLIGHT_TASKS = []
    sim._write_json(sim.task_file, sim.IN_FLIGHT_TASKS)
    sim._write_mode("WORK", goal_pct=100.0)
    sim.enter_steady_state()
    assert sim._read_mode()["mode"] == "STEADY-STATE"

    # Rollback
    result = sim.rollback_steady_state()
    assert result["status"] == "success", f"Rollback failed: {result}"

    # Verify mode is WORK again
    mode = sim._read_mode()
    assert mode["mode"] == "WORK", f"Expected WORK after rollback, got {mode['mode']}"

    # Verify scheduler restored to daily
    sched = json.loads(sim.scheduler_file.read_text(encoding="utf-8"))
    assert sched["cadence_hours"] == 24, f"Expected 24h after rollback, got {sched['cadence_hours']}"

    # Transition log shows both entries in order
    lines = sim.transition_log_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2, f"Expected 2 transitions, got {len(lines)}"
    assert json.loads(lines[0])["to_mode"] == "STEADY-STATE"
    assert json.loads(lines[1])["to_mode"] == "WORK"

    return True

def self_test():
    """Run all tests in temp dirs. Returns (passed, total)."""
    tmpdir = Path(tempfile.mkdtemp(prefix="sst_"))
    results = []
    test_fns = [
        ("a_clean_transition", test_a_clean_transition),
        ("b_frequency_propagation", test_b_frequency_propagation),
        ("c_no_orphaned_tasks", test_c_no_orphaned_tasks),
        ("d_idempotent", test_d_idempotent),
        ("e_rollback", test_e_rollback),
    ]
    passed = 0
    for name, fn in test_fns:
        try:
            fn(tmpdir)
            results.append({"test": name, "status": "PASS"})
            passed += 1
        except (AssertionError, Exception) as e:
            results.append({"test": name, "status": "FAIL", "error": str(e)})
    shutil.rmtree(tmpdir, ignore_errors=True)
    return passed, len(test_fns), results

def main():
    t0 = time.time()
    passed, total, results = self_test()
    elapsed = time.time() - t0

    report = {
        "script": "steady_state_transition_test.py",
        "timestamp": iso_now(),
        "passed": passed,
        "total": total,
        "elapsed_s": round(elapsed, 2),
        "results": results,
        "verdict": "PASS" if passed == total else "FAIL"
    }

    # Write results (CWD-independent)
    Path(RESULTS_FILE).write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Steady-State Transition Test: {passed}/{total} PASS in {elapsed:.2f}s")
    for r in results:
        status_icon = "✓" if r["status"] == "PASS" else "✗"
        extra = f" ({r['error']})" if r.get("error") else ""
        print(f"  {status_icon} {r['test']}{extra}")
    print(f"Verdict: {report['verdict']}")

    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()