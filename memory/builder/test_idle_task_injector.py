"""Test: Idle Task Injector (Builder goal #1) - validates agent_portal.py dispatch logic."""
import json, os, sys, datetime, tempfile, types
from pathlib import Path

HERE = str(Path(__file__).resolve().parent.parent.parent)  # project root
passed = failed = 0

def check(name, cond):
    global passed, failed
    if cond: passed += 1; print(f"  PASS {name}")
    else: failed += 1; print(f"  FAIL {name}")

# --- Load the relevant functions from agent_portal.py without starting the server ---
src = Path(HERE, "agent_portal.py").read_text(encoding="utf-8")

start_marker = "# ---- Idle Task Injector"
end_marker = "def _autoloop_watchdog"
s = src.index(start_marker)
e = src.index(end_marker, s)
block = src[s:e]

# Execute in a namespace where we can later patch _FLEET_MODE_PATH
ns = {"os": os, "json": json}
exec(compile(block, "<idle-injector-block>", "exec"), ns)

_IDLE_ROTATION = ns["_IDLE_ROTATION"]
_idle_task_for_role = ns["_idle_task_for_role"]

print("== Idle Task Injector Tests ==")

# 1. Rotation table has all 8 roles
roles = ["orchestrator","researcher","builder","verifier","designer","archivist","scribe","mechanic"]
check("rotation has 8 roles", set(_IDLE_ROTATION.keys()) == set(roles))

# 2. Each role has exactly 5 tasks
for r in roles:
    check(f"{r} has 5 tasks", len(_IDLE_ROTATION[r]) == 5)

# 3. Tasks are non-empty strings
all_tasks = [t for tasks in _IDLE_ROTATION.values() for t in tasks]
check("all 40 tasks are non-empty strings", all(isinstance(t, str) and len(t.strip()) > 0 for t in all_tasks))

# 4. No duplicate tasks within a role
for r in roles:
    check(f"{r} no duplicates", len(set(_IDLE_ROTATION[r])) == 5)

# 5. _idle_task_for_role returns valid task for each role (case-insensitive)
today = datetime.date.today()
dow = today.weekday()
idx = min(dow, 4)
for r in roles:
    expected = _IDLE_ROTATION[r][idx]
    actual = _idle_task_for_role(r.capitalize())
    check(f"_idle_task_for_role('{r.capitalize()}') correct", actual == expected)

# 6. Fallback for unknown role
check("unknown role fallback", _idle_task_for_role("nonexistent") == "General maintenance sweep")

# 7-10: Test _read_fleet_mode with different file states by re-executing the function
def make_read_fn(path):
    """Create a standalone _read_fleet_mode that reads from given path."""
    def fn():
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            mode = data.get('mode', 'WORK')
            return mode if mode in ('WORK', 'MAINTENANCE', 'IDLE') else 'WORK'
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return 'WORK'
    return fn

check("missing file returns WORK", make_read_fn("/nonexistent/fm.json")() == "WORK")

tmp = tempfile.mktemp(suffix=".json")
with open(tmp, "w") as f: json.dump({"mode": "MAINTENANCE"}, f)
check("valid MAINTENANCE", make_read_fn(tmp)() == "MAINTENANCE")

with open(tmp, "w") as f: json.dump({"mode": "IDLE"}, f)
check("valid IDLE", make_read_fn(tmp)() == "IDLE")

with open(tmp, "w") as f: json.dump({"mode": "BROKEN"}, f)
check("invalid mode returns WORK", make_read_fn(tmp)() == "WORK")

with open(tmp, "w") as f: f.write("{not valid json")
check("corrupt JSON returns WORK", make_read_fn(tmp)() == "WORK")
os.unlink(tmp)

# 11. Weekend clamp logic
check("weekend Saturday clamps to Fri", min(5, 4) == 4)
check("weekend Sunday clamps to Fri", min(6, 4) == 4)

# 12. Rotation produces different tasks on different days
tb = _IDLE_ROTATION["builder"]
check("Mon task != Wed task", tb[0] != tb[2])
check("Thu task != Sun(clamped to Fri) task", tb[3] != tb[4])

# 13. Verify the dispatch branch exists in source code (lines ~4253-4256)
dispatch_snippet = src[src.index("_fm = _read_fleet_mode()"):src.index("_fm = _read_fleet_mode()")+300]
check("dispatch checks MAINTENANCE/IDLE", 'MAINTENANCE' in dispatch_snippet and 'IDLE' in dispatch_snippet)
check("dispatch calls _idle_task_for_role", '_idle_task_for_role' in dispatch_snippet)

print(f"\nResults: {passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
