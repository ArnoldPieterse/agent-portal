# End-to-end check of the per-host load-queue state exposed by /api/fleet (2026-11-22).
# Runs in its OWN process: imports agent_portal, fakes _studio_recover (no real loads),
# fires two concurrent reloads on the same host and asserts the queue state + the exact
# /api/fleet row payload while a load is in flight. Safe: read-only probes only.
import sys, time, threading
sys.path.insert(0, r"C:\Projects\Workspace")
import agent_portal as ap

BASE = ap.STUDIO.rstrip("/")
agent = {"name": "Orchestrator", "studio": "", "model_id": "atlas-q8"}

def fake_recover(agent, reason):
    time.sleep(8.0)   # stand-in for a real model load (longer than the probe window)
    return True, "fake load"
ap._studio_recover = fake_recover

results = {}
def run(key):
    ok, detail = ap._queued_model_load(agent, reason="reload", wait_s=90)
    results[key] = (ok, detail)

t0 = time.time()
th_a = threading.Thread(target=run, args=("A",)); th_a.start()
time.sleep(0.7)
with ap._LOADQ_LOCK:
    act = dict(ap._HOST_LOAD_ACTIVE.get(BASE) or {})
    wait = ap._HOST_LOAD_WAITERS.get(BASE, 0)
assert act and act["agent"] == "Orchestrator", "active load not registered: %r" % act
assert wait == 1, "expected 1 waiter (the runner), got %d" % wait

th_b = threading.Thread(target=run, args=("B",)); th_b.start()
time.sleep(0.7)
with ap._LOADQ_LOCK:
    wait2 = ap._HOST_LOAD_WAITERS.get(BASE, 0)
assert wait2 == 2, "expected 2 waiters (runner + queued), got %d" % wait2

# the exact payload the Fleet tab consumes, mid-load
snap = ap._fleet_snapshot()
row = [h for h in snap["hosts"] if h["base"] == BASE][0]
assert row["loading"] and row["loading"]["agent"] == "Orchestrator", row["loading"]
assert row["queued"] == 1, "row.queued should be 1 mid-load, got %r" % row["queued"]
print("mid-load /api/fleet row: loading=%r queued=%r" % (row["loading"], row["queued"]))

th_a.join(60); th_b.join(60)
assert results.get("A", (False,))[0] and results.get("B", (False,))[0], results
with ap._LOADQ_LOCK:
    assert not ap._HOST_LOAD_ACTIVE.get(BASE), "active not cleared after loads"
    assert ap._HOST_LOAD_WAITERS.get(BASE, 0) == 0, "waiters not zeroed"
snap2 = ap._fleet_snapshot()
row2 = [h for h in snap2["hosts"] if h["base"] == BASE][0]
assert row2["loading"] is None and row2["queued"] == 0, (row2["loading"], row2["queued"])
print("PASS: load queue state tracked end-to-end (active -> queued -> cleared); /api/fleet rows correct")
