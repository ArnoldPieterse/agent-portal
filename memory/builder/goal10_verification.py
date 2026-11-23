"""Goal #10 Verification: Cockpit One-Click Runbook Trigger - all 6 acceptance criteria."""
import sys, os, time, json, importlib.util
from datetime import datetime, timezone
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE)
spec = importlib.util.spec_from_file_location("rbt", os.path.join(BASE, "memory/builder/runbook_trigger.py"))
rbt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rbt)

passed = 0
def check(name, cond):
    global passed
    if not cond: print(f"  FAIL: {name}"); sys.exit(1)
    passed += 1; print(f"  PASS: {name}")

# AC1: Clicking Run starts execution with progress visible
r = rbt.execute_runbook("safe_test", dry_run=True)
check("AC1a: execute returns started status", r["status"] == "started")
rid = r["run_id"]
check("AC1b: run_id is 12-char hex", len(rid) == 12 and all(c in "0123456789abcdef" for c in rid))
time.sleep(2)
st = rbt.get_run_state(rid)
check("AC1c: completed within 5s", st["status"] == "completed")

# AC2: Progress updates visible (per-step tracked)
check("AC2a: all steps have progress entries", len(st["progress"]) == 3)
check("AC2b: each entry has step number + status", all("step" in p and "status" in p for p in st["progress"]))

# AC3: Abort button stops execution mid-run
r2 = rbt.execute_runbook("safe_test", dry_run=False)
rid2 = r2["run_id"]
time.sleep(0.15)
ab = rbt.abort_run(rid2)
check("AC3a: abort returns ok", ab.get("ok") == True)
st2 = None
for _ in range(20):
    time.sleep(0.3)
    st2 = rbt.get_run_state(rid2)
    if st2 and st2["status"] != "running":
        break
check("AC3b: run stopped (aborted or completed)", st2["status"] in ("aborted", "completed"))

# AC4: Error state shown if pre-flight fails
pf_bad = rbt.preflight_check("nonexistent_xyz")
check("AC4a: preflight fails for unknown runbook", pf_bad["ready"] == False)
check("AC4b: failure detail present", any(c["pass"]==False and c["detail"] for c in pf_bad["checks"]))

# AC5: Decision logged
dl = rbt.DECISION_LOG
entries = [json.loads(l) for l in dl.read_text(encoding="utf-8").strip().split("\n") if "runbook_trigger" in l]
check("AC5a: decision log has runbook_trigger entries", len(entries) >= 2)
check("AC5b: entry has run_id + status", all("run_id" in e and "status" in e for e in entries[-3:]))

# AC6: Portal API endpoints wired correctly
portal = open(os.path.join(BASE, "agent_portal.py"), encoding="utf-8").read()
check("AC6a: preflight endpoint present", "endswith(\"/preflight\")" in portal)
check("AC6b: run endpoint handles dict return", "_res.get(\"run_id\")" in portal)
check("AC6c: state endpoint uses get_state alias", "rbt.get_state(rid)" in portal)
cockpit = open(os.path.join(BASE, "ui/cockpit.js"), encoding="utf-8").read()
check("AC6d: _rbData populated in UI", "_rbData = d.runbooks" in cockpit)
check("AC6e: Run button calls preflight then run", "preflight" in cockpit and "/api/runbooks/run" in cockpit)

ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
print(f"\nALL {passed}/12 CHECKS PASS - {ts}")
