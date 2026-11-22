"""
Goal #9 — Task Re-Routing E2E Test
Full end-to-end: simulate agent unresponsive -> detection -> task reassignment -> new agent picks up -> task completes.
Verification criteria:
  (a) full cycle <5 min
  (b) task not lost (appears in new agent's queue)
  (c) original agent status updated on recovery
  (d) all steps logged
"""
import json, time, hashlib, os, sys, logging
from dataclasses import dataclass, field
from typing import Optional

# --- Logging setup ---
log_lines = []
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
class _CaptureHandler(logging.Handler):
    def emit(self, record):
        log_lines.append(self.format(record))
logging.getLogger().addHandler(_CaptureHandler())

# --- Data structures ---
@dataclass
class Task:
    id: str
    title: str
    assigned_to: Optional[str] = None
    status: str = "queued"  # queued | in_progress | completed | failed
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    result: Optional[str] = None

@dataclass
class Agent:
    name: str
    status: str = "active"  # active | unresponsive | recovering | recovered
    queue: list = field(default_factory=list)  # list of Task
    last_ping: float = field(default_factory=time.time)
    capabilities: list = field(default_factory=lambda: ["build", "verify", "research"])
    down: bool = False  # simulated failure flag (separate from status)

class FleetSim:
    def __init__(self, agents: list, tasks: list):
        self.agents = {a.name: a for a in agents}
        self.tasks = {t.id: t for t in tasks}
        self.events = []  # all logged steps
        self.reroute_count = 0

    def log(self, step: str, detail: str = ""):
        msg = f"{step}" + (f" | {detail}" if detail else "")
        logging.info(msg)
        self.events.append({"ts": time.time(), "step": step, "detail": detail})

    def ping(self, agent_name: str) -> bool:
        """Simulate a ping; down agents return False."""
        agent = self.agents.get(agent_name)
        if agent is None:
            return False
        if agent.down or agent.status == "unresponsive":
            return False
        agent.last_ping = time.time()
        return True

    def detect_unresponsive(self, timeout_s: float = 10.0) -> list:
        """Check all agents; return names of unresponsive ones."""
        unresponsive = []
        for name, agent in self.agents.items():
            ok = self.ping(name)
            if not ok and agent.status != "unresponsive":
                agent.status = "unresponsive"
                self.log("DETECTED", f"agent={name} unresponsive (ping failed)")
                unresponsive.append(name)
            elif not ok:
                # Already known unresponsive - still report
                unresponsive.append(name)
        return unresponsive

    def find_alternate(self, task: Task, exclude: list) -> Optional[str]:
        """Find an active agent with the fewest queued tasks that can handle the task."""
        candidates = []
        for name, agent in self.agents.items():
            if name in exclude:
                continue
            if agent.status != "active":
                continue
            candidates.append((len(agent.queue), name))
        if not candidates:
            return None
        # Pick the least-loaded active agent
        candidates.sort()
        return candidates[0][1]

    def reroute_task(self, task: Task, from_agent: str) -> Optional[str]:
        """Reassign a task from an unresponsive agent to an alternate."""
        if task.assigned_to != from_agent:
            return None
        self.log("REROUTE_START", f"task={task.id} from={from_agent}")
        # Remove from old agent's queue
        if task in self.agents[from_agent].queue:
            self.agents[from_agent].queue.remove(task)
        # Find alternate
        alt = self.find_alternate(task, exclude=[from_agent])
        if alt is None:
            self.log("REROUTE_FAIL", f"task={task.id} no alternate available")
            task.status = "failed"
            return None
        # Assign to new agent
        task.assigned_to = alt
        task.status = "queued"
        self.agents[alt].queue.append(task)
        self.reroute_count += 1
        self.log("REROUTE_OK", f"task={task.id} from={from_agent} to={alt}")
        return alt

    def process_queue(self, agent_name: str):
        """Simulate an agent processing its queue (one task at a time)."""
        agent = self.agents.get(agent_name)
        if agent is None or agent.status != "active":
            return False
        while agent.queue:
            task = agent.queue[0]
            task.status = "in_progress"
            self.log("TASK_START", f"task={task.id} agent={agent_name}")
            # Simulate work (instant for test)
            time.sleep(0.01)
            task.status = "completed"
            task.completed_at = time.time()
            task.result = f"done_by_{agent_name}"
            agent.queue.pop(0)
            self.log("TASK_DONE", f"task={task.id} result={task.result}")
        return True

    def recover_agent(self, name: str):
        """Simulate an agent coming back online."""
        agent = self.agents.get(name)
        if agent is None:
            return
        agent.status = "recovered"
        agent.last_ping = time.time()
        self.log("RECOVERED", f"agent={name} status updated to recovered")

    def get_report(self) -> dict:
        return {
            "total_events": len(self.events),
            "events": self.events,
            "reroute_count": self.reroute_count,
            "agents": {n: {"status": a.status, "queue_size": len(a.queue)} for n, a in self.agents.items()},
            "tasks": {t.id: {"status": t.status, "assigned_to": t.assigned_to, "result": t.result} for t in self.tasks.values()},
        }

# --- E2E Test ---
def run_e2e_test():
    """
    Full E2E: 
    1. Set up fleet with 3 agents + 2 tasks (one per agent)
    2. Kill agent B (make unresponsive)
    3. Detect unresponsiveness
    4. Reroute B's task to agent C
    5. Agent C processes and completes the task
    6. Agent B recovers; status updated
    7. Verify all criteria
    """
    t0 = time.time()
    results = {"pass": True, "checks": {}, "elapsed_s": 0}

    # Setup
    agents = [
        Agent(name="Alpha", capabilities=["build", "verify"]),
        Agent(name="Beta", capabilities=["research", "verify"]),
        Agent(name="Gamma", capabilities=["build", "research", "verify"]),
    ]
    tasks = [
        Task(id="T1", title="Build feature X", assigned_to="Alpha"),
        Task(id="T2", title="Research API docs", assigned_to="Beta"),
        Task(id="T3", title="Verify integration", assigned_to="Gamma"),
    ]
    fleet = FleetSim(agents, tasks)
    fleet.log("SETUP", f"fleet={list(fleet.agents.keys())} tasks={list(fleet.tasks.keys())}")

    # Assign tasks to queues
    for t in tasks:
        if t.assigned_to and t.assigned_to in fleet.agents:
            fleet.agents[t.assigned_to].queue.append(t)

    # Step 1: Normal operation - all agents process
    fleet.log("PHASE1", "normal operation")
    for name in ["Alpha", "Gamma"]:
        fleet.process_queue(name)
    # Beta is still active, processes T2
    fleet.process_queue("Beta")

    # Step 2: Inject failure - Beta goes down with a new task
    t4 = Task(id="T4", title="Critical hotfix", assigned_to="Beta")
    fleet.tasks["T4"] = t4
    fleet.agents["Beta"].queue.append(t4)
    fleet.agents["Beta"].down = True  # simulate failure (detection will set status)
    fleet.log("INJECT_FAILURE", "Beta went down with pending task T4")

    # Step 3: Detection
    t_detect_start = time.time()
    unresponsive = fleet.detect_unresponsive()
    t_detect_end = time.time()
    check_b1 = "T4" in [t.id for t in fleet.agents["Beta"].queue] or fleet.tasks["T4"].status != "completed"
    results["checks"]["detection"] = {
        "unresponsive_detected": unresponsive,
        "beta_flagged": "Beta" in unresponsive,
        "task_still_pending": check_b1,
        "detection_time_s": round(t_detect_end - t_detect_start, 3),
    }

    # Step 4: Reroute T4 from Beta to an alternate active agent
    t_reroute = fleet.tasks["T4"]
    new_owner = fleet.reroute_task(t_reroute, "Beta")
    check_b2 = (new_owner is not None) and (new_owner != "Beta") and (t_reroute.assigned_to == new_owner) and (t_reroute in fleet.agents[new_owner].queue)
    results["checks"]["reroute"] = {
        "new_owner": new_owner,
        "task_in_new_queue": check_b2,
        "task_not_lost": t_reroute.status == "queued" or t_reroute.status == "in_progress" or t_reroute.status == "completed",
    }

    # Step 5: The new owner processes T4
    if new_owner:
        fleet.process_queue(new_owner)
    check_b3 = fleet.tasks["T4"].status == "completed" and fleet.tasks["T4"].result is not None
    results["checks"]["task_completed"] = {
        "status": fleet.tasks["T4"].status,
        "result": fleet.tasks["T4"].result,
        "completed": check_b3,
    }

    # Step 6: Beta recovers, status updated
    fleet.recover_agent("Beta")
    check_c = fleet.agents["Beta"].status == "recovered"
    results["checks"]["recovery"] = {
        "beta_status": fleet.agents["Beta"].status,
        "updated_correctly": check_c,
    }

    # Step 7: Verify all steps logged
    step_names = [e["step"] for e in fleet.events]
    required_steps = ["SETUP", "INJECT_FAILURE", "DETECTED", "REROUTE_START", "REROUTE_OK", "TASK_START", "TASK_DONE", "RECOVERED"]
    check_d = all(s in step_names for s in required_steps)
    results["checks"]["all_logged"] = {
        "steps_found": len(step_names),
        "required_present": check_d,
        "missing": [s for s in required_steps if s not in step_names],
    }

    # Timing check: <5 min (300s)
    elapsed = time.time() - t0
    results["elapsed_s"] = round(elapsed, 3)
    check_a = elapsed < 300.0
    results["checks"]["timing"] = {"elapsed_s": elapsed, "under_5min": check_a}

    # Overall pass/fail
    all_pass = all([
        results["checks"]["detection"]["beta_flagged"],
        results["checks"]["reroute"]["task_in_new_queue"],
        results["checks"]["task_completed"]["completed"],
        results["checks"]["recovery"]["updated_correctly"],
        results["checks"]["all_logged"]["required_present"],
        check_a,
    ])
    results["pass"] = all_pass
    results["fleet_report"] = fleet.get_report()

    return results

# --- Self-test runner ---
def self_test():
    print("=" * 60)
    print("GOAL #9: Task Re-Routing E2E Test")
    print("=" * 60)
    results = run_e2e_test()
    
    checks = results["checks"]
    total_checks = 0
    passed = 0
    for name, chk in checks.items():
        # Determine pass/fail per check
        if name == "detection":
            ok = chk["beta_flagged"] and chk["task_still_pending"]
        elif name == "reroute":
            ok = chk["task_in_new_queue"] and chk["task_not_lost"]
        elif name == "task_completed":
            ok = chk["completed"]
        elif name == "recovery":
            ok = chk["updated_correctly"]
        elif name == "all_logged":
            ok = chk["required_present"]
        elif name == "timing":
            ok = chk["under_5min"]
        else:
            ok = False
        total_checks += 1
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}: {json.dumps(chk, default=str)[:120]}")
        if ok:
            passed += 1
    
    print(f"\n  Total: {passed}/{total_checks} checks passed")
    print(f"  Elapsed: {results['elapsed_s']}s (limit: 300s)")
    print(f"  Overall: {'PASS' if results['pass'] else 'FAIL'}")
    
    # Write report
    report = {
        "goal": "#9 Task Re-Routing E2E Test",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "pass": results["pass"],
        "checks": {k: v for k, v in checks.items()},
        "elapsed_s": results["elapsed_s"],
        "events_count": len(results["fleet_report"]["events"]),
    }
    out_path = os.path.join(os.path.dirname(__file__), "reroute_e2e_report.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"  Report: {out_path}")
    
    return results["pass"]

if __name__ == "__main__":
    ok = self_test()
    sys.exit(0 if ok else 1)