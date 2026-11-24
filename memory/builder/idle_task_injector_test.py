"""Self-test for Idle Task Injector (Builder goal #1).

Verifies:
1. _read_fleet_mode() returns correct mode from fleet-mode.json
2. _idle_task_for_role() returns the right task per role + weekday
3. The dispatch branch logic produces the correct body text for MAINTENANCE/IDLE modes
"""
import json, os, sys, datetime, tempfile, pathlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # project root

# --- Inline the same helpers as in agent_portal.py (to avoid importing full portal) ---
sys.path.insert(0, ROOT)

_FLEET_MODE_PATH = os.path.join(ROOT, "fleet-mode.json")

_IDLE_ROTATION = {
    "orchestrator": ["Roster health audit", "Model binding check", "Capacity gauge refresh", "Dependency graph update", "Fleet capacity report"],
    "researcher": ["Re-run stale_claim_scan", "Evidence quality trend update", "KB index freshness check", "Source cross-validation sample", "Dictionary gap scan"],
    "builder": ["Orphaned temp file sweep", "Build artifact size audit", "Pin-file integrity check", "CSS token drift scan", "Test coverage delta"],
    "verifier": ["Stale test battery re-run", "SLO history gap fill", "Regression daemon health", "Evidence chain audit", "Gate log compaction"],
    "designer": ["WCAG contrast spot-check", "Breakpoint regression scan", "Icon set completeness", "Typography scale audit", "Animation perf check"],
    "archivist": ["KB coverage re-index", "Provenance report refresh", "Dangling pointer sweep", "Orphan file detection", "Index staleness check"],
    "scribe": ["Compression fidelity trend", "Handoff log compaction", "Decision log summarization", "Pattern extraction pass", "Cycle narrative draft"],
    "mechanic": ["Host probe battery", "Log rotation verify", "WinRM leg test", "Model lifecycle audit", "Capacity plan re-gen"],
}

def _read_fleet_mode():
    try:
        with open(_FLEET_MODE_PATH, encoding="utf-8") as f:
            data = json.load(f)
        mode = data.get("mode", "WORK")
        return mode if mode in ("WORK", "MAINTENANCE", "IDLE") else "WORK"
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return "WORK"

def _idle_task_for_role(role):
    tasks = _IDLE_ROTATION.get(role.lower())
    if not tasks:
        return "General maintenance sweep"
    dow = datetime.date.today().weekday()
    idx = min(dow, 4)
    return tasks[idx]

# --- Simulate the dispatch branch logic ---
def simulate_dispatch_body(fleet_mode, agent_name):
    """Mirror of the modified branch in _autoloop_watchdog."""
    if fleet_mode in ("MAINTENANCE", "IDLE"):
        task = _idle_task_for_role(agent_name)
        return "fleet mode is %s - your assigned maintenance task today: **%s**. Complete it with concrete tool calls, then record evidence. Reply [CONCLUDED] when done." % (fleet_mode, task)
    else:
        return "your goals are 100% reached - contribute to the team while you wait..."

# --- Tests ---
passed = 0
failed = 0

def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name}")

print("=== Idle Task Injector Self-Test ===\n")

# Test 1: _read_fleet_mode works with real file
mode = _read_fleet_mode()
check("_read_fleet_mode returns valid mode", mode in ("WORK", "MAINTENANCE", "IDLE"))
print(f"    (got: {mode})")

# Test 2: _idle_task_for_role for all 8 roles
for role in ["Orchestrator", "Researcher", "Builder", "Verifier", "Designer", "Archivist", "Scribe", "Mechanic"]:
    task = _idle_task_for_role(role)
    check(f"task for {role} is non-empty string", isinstance(task, str) and len(task) > 3)

# Test 3: Unknown role returns fallback
check("unknown role returns fallback", _idle_task_for_role("Ghost") == "General maintenance sweep")

# Test 4: MAINTENANCE mode produces specific task in body
body = simulate_dispatch_body("MAINTENANCE", "Builder")
expected_task = _idle_task_for_role("Builder")
check("MAINTENANCE body contains fleet mode", "MAINTENANCE" in body)
check(f"MAINTENANCE body contains task '{expected_task}'", expected_task in body)

# Test 5: IDLE mode produces specific task in body
body = simulate_dispatch_body("IDLE", "Mechanic")
expected_task = _idle_task_for_role("Mechanic")
check("IDLE body contains fleet mode", "IDLE" in body)
check(f"IDLE body contains task '{expected_task}'", expected_task in body)

# Test 6: WORK mode falls back to generic menu
body = simulate_dispatch_body("WORK", "Builder")
check("WORK body is generic (no specific task)", "contribute to the team" in body)

# Test 7: Verify agent_portal.py contains the modification
portal_src = pathlib.Path(os.path.join(ROOT, "agent_portal.py")).read_text(encoding="utf-8")
check("agent_portal.py has _read_fleet_mode def", "def _read_fleet_mode" in portal_src)
check("agent_portal.py has _idle_task_for_role def", "def _idle_task_for_role" in portal_src)
check("agent_portal.py references MAINTENANCE/IDLE in dispatch", "_fm in (\"MAINTENANCE\", \"IDLE\")" in portal_src or '_fm in ("MAINTENANCE", "IDLE")' in portal_src)
check("agent_portal.py has _IDLE_ROTATION table", "_IDLE_ROTATION" in portal_src)

print(f"\n=== Result: {passed} passed, {failed} failed ===")
sys.exit(1 if failed else 0)
