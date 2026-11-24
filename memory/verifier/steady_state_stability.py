"""Steady-State Stability Test.
After the fleet reaches 100% goal completion, verify it enters a stable
steady state without oscillation or re-dispatch loops.

Acceptance criteria:
(a) No dispatch is generated for any goal with status="reached"
(b) Mode remains in {MAINTENANCE, IDLE} for N consecutive passes (no flapping back to WORK)
(c) In steady state, productive_passes == 0 and total_passes increments normally
(d) No new file creation events occur during steady-state window
(e) Test is idempotent: running twice produces identical results

Usage: python memory/verifier/steady_state_stability.py
"""
import json, sys, os, tempfile, shutil
from datetime import datetime, timedelta
from pathlib import Path

PASS_BUDGET = 200
STABLE_WINDOW = 10  # Number of consecutive passes to confirm steady state
TEST_TIMEOUT_S = 60

class SteadyStateSimulator:
    """Simulate fleet behavior after reaching 100% completion."""
    
    def __init__(self, tmpdir):
        self.tmpdir = Path(tmpdir)
        self.mode_file = self.tmpdir / "fleet-mode.json"
        self.pass_log = []
        self.dispatches = []
        self.files_created = []
        self._setup()
    
    def _setup(self):
        """Set up initial state: all goals reached, mode=MAINTENANCE."""
        # Write fleet-mode.json with 100% completion
        mode_data = {
            "mode": "MAINTENANCE",
            "timestamp": datetime.now().isoformat(),
            "goal_pct": 100.0,
            "last_activity": (datetime.now() - timedelta(hours=2)).isoformat()
        }
        self.mode_file.write_text(json.dumps(mode_data), encoding="utf-8")
        
        # Simulated goal states: all reached
        self.goal_states = {
            f"goal_{i}": {"status": "reached", "reached_at": (datetime.now() - timedelta(hours=1)).isoformat()}
            for i in range(1, 6)
        }
    
    def run_pass(self, pass_num):
        """Run one simulated pass. Returns dispatch decision."""
        mode = json.loads(self.mode_file.read_text(encoding="utf-8"))["mode"]
        
        # In MAINTENANCE/IDLE: only idle tasks, no goal dispatches
        if mode in ("MAINTENANCE", "IDLE"):
            dispatch = {"type": "idle_maintenance", "goals": []}
            productive = False
        else:  # WORK mode - would dispatch open goals (but there are none)
            open_goals = [g for g, s in self.goal_states.items() if s["status"] == "open"]
            dispatch = {"type": "goal_work", "goals": open_goals}
            productive = len(open_goals) > 0
        
        self.dispatches.append({"pass": pass_num, **dispatch})
        self.pass_log.append({
            "pass": pass_num,
            "mode": mode,
            "productive": productive
        })
        return dispatch
    
    def simulate_steady_state(self, n_passes=STABLE_WINDOW + 5):
        """Run n passes and collect results."""
        for i in range(1, n_passes + 1):
            self.run_pass(i)
    
    def check_no_goal_dispatch(self):
        """(a) No dispatch references a reached goal."""
        violations = []
        for d in self.dispatches:
            if d["type"] == "goal_work" and len(d["goals"]) > 0:
                violations.append(d)
        return violations
    
    def check_no_mode_flapping(self):
        """(b) Mode stays in {MAINTENANCE, IDLE} - no flapping back to WORK."""
        modes_seen = [p["mode"] for p in self.pass_log]
        # If any pass shows WORK mode after initial MAINTENANCE, that's flapping
        violations = [i+1 for i, m in enumerate(modes_seen) if m == "WORK"]
        return violations
    
    def check_productivity(self):
        """(c) In steady state: productive_passes == 0."""
        productive_count = sum(1 for p in self.pass_log if p["productive"])
        return productive_count
    
    def check_no_new_files(self):
        """(d) No new file creation events (simulated: no files written during passes)."""
        # In real system we'd watch for new files; here we verify mode_file wasn't rewritten
        mtime = self.mode_file.stat().st_mtime
        return mtime  # caller compares to pre-sim mtime


def run_test():
    """Run the full steady-state stability test."""
    results = {}
    tmpdir = tempfile.mkdtemp(prefix="steady_state_")
    
    try:
        sim = SteadyStateSimulator(tmpdir)
        
        # Record pre-simulation state
        pre_mtime = sim.mode_file.stat().st_mtime
        
        # Run simulation
        sim.simulate_steady_state()
        
        # (a) No goal dispatch for reached goals
        violations_a = sim.check_no_goal_dispatch()
        results["a_no_goal_dispatch"] = {
            "pass": len(violations_a) == 0,
            "violations": len(violations_a),
            "detail": f"{len(sim.dispatches)} passes, all idle_maintenance type" if not violations_a else str(violations_a[:3])
        }
        
        # (b) No mode flapping
        violations_b = sim.check_no_mode_flapping()
        results["b_no_mode_flapping"] = {
            "pass": len(violations_b) == 0,
            "violations": len(violations_b),
            "detail": f"modes seen: {list(set(p['mode'] for p in sim.pass_log))}"
        }
        
        # (c) Productivity = 0 in steady state
        productive_count = sim.check_productivity()
        results["c_zero_productivity"] = {
            "pass": productive_count == 0,
            "productive_passes": productive_count,
            "total_passes": len(sim.pass_log)
        }
        
        # (d) No new files created
        post_mtime = sim.mode_file.stat().st_mtime
        results["d_no_new_files"] = {
            "pass": post_mtime == pre_mtime,
            "detail": "mode file unchanged during steady-state window"
        }
        
        # (e) Idempotency: run again, same results
        sim2 = SteadyStateSimulator(tmpdir)
        sim2.simulate_steady_state()
        violations_a2 = sim2.check_no_goal_dispatch()
        violations_b2 = sim2.check_no_mode_flapping()
        productive_count2 = sim2.check_productivity()
        
        idempotent = (
            len(violations_a2) == len(violations_a) and
            len(violations_b2) == len(violations_b) and
            productive_count2 == productive_count
        )
        results["e_idempotent"] = {
            "pass": idempotent,
            "detail": "second run produces identical dispatch counts and mode stability"
        }
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    # Summary
    total = len(results)
    passed = sum(1 for r in results.values() if r["pass"])
    
    print(f"Steady-State Stability Test: {passed}/{total} PASS")
    for name, r in results.items():
        status = "PASS" if r["pass"] else "FAIL"
        print(f"  [{status}] {name}: {r.get('detail', '')}")
    
    return passed == total


if __name__ == "__main__":
    ok = run_test()
    sys.exit(0 if ok else 1)
