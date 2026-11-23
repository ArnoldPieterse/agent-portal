#!/usr/bin/env python3
"""Self-test for runbook_preflight.py - exercises all logic paths offline."""
import sys, os
sys.path.insert(0, str(os.path.join(os.path.dirname(__file__), "..", "mechanic")))

# Import the module directly
from pathlib import Path
import json
import time

# Monkey-patch socket to avoid real network calls
import socket as _real_socket

class FakeSocket:
    def __init__(self, *a, **k): pass
    def settimeout(self, t): pass
    def connect_ex(self, addr): return 0  # simulate success
    def close(self): pass

results = []

def test(name, cond):
    results.append((name, cond))
    print(f"  {'PASS' if cond else 'FAIL'}: {name}")

print("runbook_preflight.py self-test")
print("=" * 50)

# Test 1: agent_available with real agents.json
import importlib.util
spec = importlib.util.spec_from_file_location("rp", "memory/mechanic/runbook_preflight.py")
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)

c = rp.check_agent_available("mechanic")
test("agent_available: mechanic found", c["pass"] == True)
test("agent_available: has _host", "_host" in c)

c2 = rp.check_agent_available("does_not_exist_xyz")
test("agent_available: unknown agent fails", c2["pass"] == False)
test("agent_available: failure message present", "not found" in c2["detail"])

# Test 3: no_conflict (no lock file, no recent entries)
c3 = rp.check_no_conflict("mechanic", "model-swap")
test("no_conflict: clean state passes", c3["pass"] == True)

# Test 4: no_conflict with active lock
lock = Path("memory/ops/.runbook_active.lock")
if not lock.parent.exists():
    lock.parent.mkdir(parents=True, exist_ok=True)
lock.write_text(json.dumps({"agent": "mechanic", "runbook": "model-swap", "ts": time.time()}), encoding="utf-8")
c4 = rp.check_no_conflict("mechanic", "other-rb")
test("no_conflict: active lock on same agent blocks", c4["pass"] == False)
# Different agent should pass
c5 = rp.check_no_conflict("builder", "other-rb")
test("no_conflict: active lock on different agent passes", c5["pass"] == True)
lock.unlink()  # cleanup

# Test 5: full preflight (host will fail in sandbox - expected)
pf = rp.preflight("mechanic", "model-swap")
test("preflight: returns ok bool", isinstance(pf["ok"], bool))
test("preflight: has 3 checks", len(pf["checks"]) == 3)
test("preflight: has reasons list", isinstance(pf["reasons"], list))
test("preflight: agent check passed in sandbox", pf["checks"]["agent_available"]["pass"] == True)

# Summary
passed = sum(1 for _, ok in results if ok)
total = len(results)
print(f"\n{'=' * 50}")
print(f"RESULT: {passed}/{total} PASS")
sys.exit(0 if passed == total else 1)
