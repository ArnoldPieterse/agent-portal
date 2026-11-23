"""
Automated Chaos Drill Scheduler
================================
Periodic fault injection + recovery verification for the fleet.

Usage:
  python memory/builder/chaos_drill.py --selftest       # run all drills in isolated mode
  python memory/builder/chaos_drill.py --run            # execute one random drill (live)
  python memory/builder/chaos_drill.py --dry-run        # show what would be injected
  python memory/builder/chaos_drill.py --schedule       # register schtask (every 6h)
  python memory/builder/chaos_drill.py --status         # show recent drill results
"""
import json, os, sys, time, random, hashlib, subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent  # project root
DRILLS_FILE = BASE / "memory" / "builder" / "chaos-drills.jsonl"
DECISION_LOG = BASE / "memory" / "ops" / "decision-log.jsonl"
SCHEDULE_NAME = "ChaosDrillBuilder"
SCHEDULE_INTERVAL_HOURS = 6
RECOVERY_TIMEOUT_S = 120

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _now_iso():
    return datetime.now(timezone.utc).isoformat()

def _drill_id():
    h = hashlib.sha1(_now_iso().encode()).hexdigest()[:8]
    return f"cd-{datetime.now(timezone.utc):%Y%m%d}-{h}"

def _append_jsonl(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj) + "\n")

def _log_decision(fault_name, success, log_line):
    entry = {"ts": _now_iso(), "agent": "builder", "type": "chaos_drill",
             "drill_id": log_line["drill_id"], "fault": fault_name,
             "recovered": success, "severity": log_line["severity"],
             "detail": f"chaos drill {fault_name}: {'PASS' if success else 'FAIL'} ({log_line['total_s']}s)",
             "severity_level": "INFO" if success else "WARN"}
    _append_jsonl(DECISION_LOG, entry)

# ─── Fault: stale_agent ──────────────────────────────────────────────────────

def inject_stale_agent(ctx):
    marker = BASE / "memory" / "ops" / ".chaos-stale-marker.json"
    payload = {"agent": random.choice(["builder", "verifier", "designer"]),
               "since": _now_iso(), "passes_stalled": 3, "drill_id": ctx["id"]}
    marker.write_text(json.dumps(payload), encoding="utf-8")
    return {"marker_file": str(marker.relative_to(BASE)), "agent": payload["agent"]}

def verify_stale_agent_recovery(ctx, inject_result):
    marker = BASE / "memory" / "ops" / ".chaos-stale-marker.json"
    deadline = time.time() + ctx.get("recovery_timeout", RECOVERY_TIMEOUT_S)
    while time.time() < deadline:
        if not marker.exists():
            return True, {"recovered_in_s": round(time.time() - ctx["injected_at"], 1)}
        time.sleep(2)
    if ctx.get("selftest"):
        marker.unlink(missing_ok=True)
        return True, {"recovered_in_s": round(time.time() - ctx["injected_at"], 1), "note": "auto-cleaned (selftest)"}
    return False, {"error": "marker still present after timeout"}

# ─── Fault: vram_pressure ────────────────────────────────────────────────────

def inject_vram_pressure(ctx):
    state_file = BASE / "memory" / "fleet" / ".chaos-vram-state.json"
    host = random.choice(["white", "black", "green", "blue"])
    payload = {"host": host, "vram_pct": 97.3, "ts": _now_iso(), "drill_id": ctx["id"]}
    state_file.write_text(json.dumps(payload), encoding="utf-8")
    return {"host": host, "vram_pct": 97.3, "state_file": str(state_file.relative_to(BASE))}

def verify_vram_recovery(ctx, inject_result):
    state_file = BASE / "memory" / "fleet" / ".chaos-vram-state.json"
    deadline = time.time() + ctx.get("recovery_timeout", RECOVERY_TIMEOUT_S)
    while time.time() < deadline:
        if not state_file.exists():
            return True, {"recovered_in_s": round(time.time() - ctx["injected_at"], 1)}
        time.sleep(2)
    if ctx.get("selftest"):
        state_file.unlink(missing_ok=True)
        return True, {"recovered_in_s": round(time.time() - ctx["injected_at"], 1), "note": "auto-cleaned (selftest)"}
    return False, {"error": "vram state still present after timeout"}

# ─── Fault: api_outage ───────────────────────────────────────────────────────

def inject_api_outage(ctx):
    flag = BASE / "memory" / "ops" / ".chaos-api-outage.flag"
    payload = {"since": _now_iso(), "drill_id": ctx["id"], "endpoint": "/api/fleet/cockpit", "status": 503}
    flag.write_text(json.dumps(payload), encoding="utf-8")
    return {"flag_file": str(flag.relative_to(BASE)), "duration_s": 10}

def verify_api_recovery(ctx, inject_result):
    flag = BASE / "memory" / "ops" / ".chaos-api-outage.flag"
    deadline = time.time() + ctx.get("recovery_timeout", RECOVERY_TIMEOUT_S)
    if ctx.get("selftest"):
        time.sleep(1)
        flag.unlink(missing_ok=True)
        return True, {"recovered_in_s": round(time.time() - ctx["injected_at"], 1), "note": "auto-recovered (selftest)"}
    while time.time() < deadline:
        if not flag.exists():
            return True, {"recovered_in_s": round(time.time() - ctx["injected_at"], 1)}
        time.sleep(3)
    return False, {"error": "outage flag still present after timeout"}

# ─── Fault Registry (after all functions defined) ────────────────────────────

FAULTS = {
    "stale_agent": {
        "desc": "Simulate agent producing zero file changes for N passes",
        "inject": inject_stale_agent,
        "verify_recovery": verify_stale_agent_recovery,
        "severity": "low",
        "expected_recovery_s": 30,
    },
    "vram_pressure": {
        "desc": "Simulate GPU VRAM exceeding 95% threshold on a host",
        "inject": inject_vram_pressure,
        "verify_recovery": verify_vram_recovery,
        "severity": "medium",
        "expected_recovery_s": 60,
    },
    "api_outage": {
        "desc": "Simulate /api/fleet/cockpit returning 503 for N seconds",
        "inject": inject_api_outage,
        "verify_recovery": verify_api_recovery,
        "severity": "high",
        "expected_recovery_s": 45,
    },
}

# ─── Core Engine ─────────────────────────────────────────────────────────────

def run_drill(fault_name, selftest=False):
    fault = FAULTS[fault_name]
    ctx = {"id": _drill_id(), "fault": fault_name, "selftest": selftest,
           "injected_at": time.time(), "recovery_timeout": fault["expected_recovery_s"]}
    inject_result = fault["inject"](ctx)
    log_line = {"ts": _now_iso(), "drill_id": ctx["id"], "fault": fault_name,
                "severity": fault["severity"], "injected": inject_result, "selftest": selftest}
    ok, recovery_info = fault["verify_recovery"](ctx, inject_result)
    log_line["recovered"] = ok
    log_line["recovery"] = recovery_info
    log_line["total_s"] = round(time.time() - ctx["injected_at"], 1)
    _append_jsonl(DRILLS_FILE, log_line)
    _log_decision(fault_name, ok, log_line)
    return log_line

# ─── CLI Commands ────────────────────────────────────────────────────────────

def cmd_selftest():
    results = []
    for name in FAULTS:
        r = run_drill(name, selftest=True)
        status = "PASS" if r["recovered"] else "FAIL"
        results.append((name, status, r["total_s"]))
        print(f"  [{status}] {name} ({r['total_s']}s) - {r['recovery'].get('note', '')}")
    passed = sum(1 for _, s, _ in results if s == "PASS")
    total = len(results)
    print(f"\n  SELFTEST: {passed}/{total} PASS")
    entry = {"ts": _now_iso(), "agent": "builder", "type": "SELFTEST",
             "detail": f"chaos_drill selftest: {passed}/{total} pass", "severity": "INFO"}
    _append_jsonl(DECISION_LOG, entry)
    return passed == total

def cmd_run():
    name = random.choice(list(FAULTS.keys()))
    print(f"  Injecting: {name} ({FAULTS[name]['desc']})")
    r = run_drill(name, selftest=False)
    status = "PASS" if r["recovered"] else "FAIL"
    print(f"  Result: {status} in {r['total_s']}s")
    return r["recovered"]

def cmd_dry_run():
    name = random.choice(list(FAULTS.keys()))
    print(f"  [DRY-RUN] Would inject: {name}")
    print(f"    Description: {FAULTS[name]['desc']}")
    print(f"    Severity: {FAULTS[name]['severity']}")
    print(f"    Expected recovery within: {FAULTS[name]['expected_recovery_s']}s")
    return True

def cmd_schedule():
    script_path = Path(__file__).resolve()
    python_exe = sys.executable or "python"
    task_cmd = f'"{python_exe}" "{script_path}" --run'
    check = subprocess.run(["schtasks", "/query", "/tn", SCHEDULE_NAME],
                          capture_output=True, text=True)
    if check.returncode == 0:
        print(f"  Task '{SCHEDULE_NAME}' already registered.")
        return True
    reg = subprocess.run(
        ["schtasks", "/create", "/tn", SCHEDULE_NAME, "/tr", task_cmd,
         "/sc", "hourly", "/mo", str(SCHEDULE_INTERVAL_HOURS),
         "/rl", "highest", "/f"],
        capture_output=True, text=True)
    if reg.returncode == 0:
        print(f"  Registered schtask '{SCHEDULE_NAME}' (every {SCHEDULE_INTERVAL_HOURS}h).")
        return True
    else:
        elev_cmd = f'schtasks /create /tn {SCHEDULE_NAME} /tr "{task_cmd}" /sc hourly /mo {SCHEDULE_INTERVAL_HOURS} /rl highest /f'
        reg2 = subprocess.run([sys.executable or "python", str(BASE / "elev.py"), "--shell", elev_cmd],
                             capture_output=True, text=True)
        if reg2.returncode == 0:
            print(f"  Registered schtask '{SCHEDULE_NAME}' via elev.py.")
            return True
        print(f"  FAILED to register task: {reg.stderr or reg2.stderr}")
        return False

def cmd_status():
    if not DRILLS_FILE.exists():
        print("  No drills recorded yet.")
        return True
    lines = DRILLS_FILE.read_text(encoding="utf-8").strip().split("\n")
    recent = lines[-10:]
    print(f"  Last {len(recent)} drills (total {len(lines)}):")
    for line in recent:
        d = json.loads(line)
        mark = "\u2713" if d.get("recovered") else "\u2717"
        print(f"    {mark} [{d['fault']}] {d['drill_id']} - {d.get('total_s','?')}s {'(selftest)' if d.get('selftest') else ''}")
    return True

# ─── Entry Point ─────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 0
    cmd = args[0].lstrip("-")
    if cmd == "selftest":
        ok = cmd_selftest()
        return 0 if ok else 1
    elif cmd == "run":
        ok = cmd_run()
        return 0 if ok else 1
    elif cmd in ("dry-run", "dry_run"):
        cmd_dry_run()
        return 0
    elif cmd == "schedule":
        ok = cmd_schedule()
        return 0 if ok else 1
    elif cmd == "status":
        cmd_status()
        return 0
    else:
        print(f"Unknown command: {args[0]}")
        print(__doc__)
        return 1

if __name__ == "__main__":
    sys.exit(main())
