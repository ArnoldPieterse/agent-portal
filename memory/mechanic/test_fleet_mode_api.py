"""Self-test for /api/fleet/mode endpoint (Mechanic cycle-15 goal 7).
Verifies:
1. Missing fleet-mode.json -> {mode:"UNKNOWN", error:"file_missing"}
2. Valid fleet-mode.json -> correct mode, since, goal_pct, pass_budget
3. Cache: second call within TTL returns same object (same ts)
4. Parse error in fleet-mode.json -> {mode:"UNKNOWN", error:"parse_error"}
5. Response time < 100ms
"""
import json, os, sys, time, tempfile, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))

# We test the function directly by importing it from agent_portal
sys.path.insert(0, ROOT)

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

# Import the module (it starts a server, but we only need the function)
# Instead of importing (which would start the server), we'll exec just the function
import importlib.util

# Read agent_portal.py and extract _fleet_mode_snapshot + its deps
src = open(os.path.join(ROOT, "agent_portal.py"), encoding="utf-8").read()

# We need: time, json, os, HERE, _FLEET_MODE_TTL, _fleet_mode_cache, _fleet_mode_snapshot
# Let's test with a temp dir as HERE
tmpdir = tempfile.mkdtemp(prefix="fleet_mode_test_")
os.makedirs(os.path.join(tmpdir, "memory", "ops"), exist_ok=True)
os.makedirs(os.path.join(tmpdir, "memory", "goals"), exist_ok=True)

# Create namespace for exec
ns = {"time": time, "json": json, "os": os, "HERE": tmpdir}

# Extract the function block
start = src.index("# --- Fleet Mode API")
end = src.index("def _decisions_snapshot():")
func_src = src[start:end]
exec(func_src, ns)

_fleet_mode_snapshot = ns["_fleet_mode_snapshot"]
_fleet_mode_cache = ns["_fleet_mode_cache"]

print("Test 1: Missing fleet-mode.json")
_fleet_mode_cache.update(data=None, ts=0)
t0 = time.time()
r = _fleet_mode_snapshot()
elapsed = (time.time() - t0) * 1000
check("mode is UNKNOWN", r["mode"] == "UNKNOWN")
check("error is file_missing", r.get("error") == "file_missing")
check("response < 100ms", elapsed < 100)

print("\nTest 2: Valid fleet-mode.json")
fm_data = {"mode": "WORK", "timestamp": "2026-11-24T14:00:00+00:00", "goal_pct": 75.5, "agent": "orchestrator"}
with open(os.path.join(tmpdir, "fleet-mode.json"), "w") as f:
    json.dump(fm_data, f)
budget = {"used": 142, "total": 200}
with open(os.path.join(tmpdir, "memory", "ops", "pass-budget.json"), "w") as f:
    json.dump(budget, f)
# Create a forecast file
forecast_data = {"next_transition_forecast": "MAINTENANCE at 18:00"}
with open(os.path.join(tmpdir, "memory", "goals", "next10.json"), "w") as f:
    json.dump(forecast_data, f)

_fleet_mode_cache.update(data=None, ts=0)
r = _fleet_mode_snapshot()
check("mode is WORK", r["mode"] == "WORK")
check("since matches timestamp", r["since"] == "2026-11-24T14:00:00+00:00")
check("goal_pct is 75.5", r["goal_pct"] == 75.5)
check("pass_budget.used is 142", r["pass_budget"]["used"] == 142)
check("pass_budget.total is 200", r["pass_budget"]["total"] == 200)
check("forecast present", r.get("next_transition_forecast") is not None)

print("\nTest 3: Cache (second call within TTL)")
r2 = _fleet_mode_snapshot()
check("same data returned from cache", r2 is r or r2 == r)
# Verify it's the cached object (same dict identity if truly cached)
ts_after_first = ns["_fleet_mode_cache"]["ts"]
time.sleep(0.1)  # small delay to ensure time has advanced
r3 = _fleet_mode_snapshot()
check("cache ts unchanged (still cached)", ns["_fleet_mode_cache"]["ts"] == ts_after_first)

print("\nTest 4: Parse error")
_fleet_mode_cache.update(data=None, ts=0)
with open(os.path.join(tmpdir, "fleet-mode.json"), "w") as f:
    f.write("{invalid json here")
r = _fleet_mode_snapshot()
check("mode is UNKNOWN on parse error", r["mode"] == "UNKNOWN")
check("error is parse_error", r.get("error") == "parse_error")

print("\nTest 5: Missing pass-budget.json (graceful default)")
_fleet_mode_cache.update(data=None, ts=0)
with open(os.path.join(tmpdir, "fleet-mode.json"), "w") as f:
    json.dump(fm_data, f)
os.remove(os.path.join(tmpdir, "memory", "ops", "pass-budget.json"))
r = _fleet_mode_snapshot()
check("mode still WORK", r["mode"] == "WORK")
check("budget defaults to {0, 200}", r["pass_budget"] == {"used": 0, "total": 200})

print("\nTest 6: Response time with valid data < 100ms")
_fleet_mode_cache.update(data=None, ts=0)
with open(os.path.join(tmpdir, "fleet-mode.json"), "w") as f:
    json.dump(fm_data, f)
t0 = time.time()
r = _fleet_mode_snapshot()
elapsed = (time.time() - t0) * 1000
check(f"response in {elapsed:.1f}ms < 100ms", elapsed < 100)

# Cleanup
shutil.rmtree(tmpdir, ignore_errors=True)

print(f"\n{'='*40}")
print(f"RESULT: {passed}/{passed+failed} PASS")
if failed:
    sys.exit(1)
else:
    print("ALL TESTS PASSED")
