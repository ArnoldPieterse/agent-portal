# Provenance: created 2026-11-23 (White + assistant) during scheduled-task consolidation.
# Replaces 22 schtasks (Portal*/Fleet*/Mirror*/*Probe/MemoryMirror*) with ONE in-process
# scheduler running inside agent_portal.py. Duplicates merged (see note per job).
# 2026-11-23 consolidation: 20 -> 15 jobs, sorted by interval; then 15 -> 6:
# one job per interval tier, same-tier scripts chained via memory/ops/run_steps.py
# (sequential, per-step timeout, chain continues on failure).
#   dropped  mirror_heal      (dup of memory_mirror - scheduler retry already covers missed runs)
#   dropped  portal_heal_check (dup of portal_guardian.py resident supervision)
#   merged   memory_audit     = decay_score + size_guard + snapshot_diff --diff (3x tree walk/h -> 1)
#   merged   verifier_daily   = perf_gate + slo_enforce (both were daily 07:00)
#   fixed    reboot_recover   dead Z:\ path -> local memory/mechanic/reboot_recover.py
#   relaxed  daily_git_commit 15m -> 1h (per-turn auto-commit covers active periods)
# State: memory/ops/scheduler-state.json | log: memory/ops/scheduler-log.jsonl
"""Portal job scheduler (2026-11-23). One daemon thread, N jobs.
2026-11-23: moved OUT of agent_portal.py into portal_host.py (single host
process) so no schtask/guardian chain is needed; the portal reads status
from disk (status_from_disk) and queues actions via request_action."""
import json, os, subprocess, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
PY  = r"C:\Projects\AgentPortal\Python\pythoncore-3.15-64\python.exe"
PYW = r"C:\Projects\AgentPortal\Python\pythoncore-3.15-64\pythonw.exe"
STATE_F = os.path.join(HERE, "memory", "ops", "scheduler-state.json")
LOG_F   = os.path.join(HERE, "memory", "ops", "scheduler-log.jsonl")
CMD_F   = os.path.join(HERE, "memory", "ops", "scheduler-cmd.json")   # portal -> host action queue
NO_WINDOW = 0x08000000  # CREATE_NO_WINDOW

# (name, interval_s, argv, note[, daily_at=(HH,MM)])  -- one-shot jobs only;
# resident daemons live in portal_guardian.py. daily_at pins a job to a wall-clock
# time each day (absorbed from schtasks VerifierPerfGate/VerifierSLO/WinRMRotation,
# removed 2026-11-23).
# Sorted by interval so the /ui/scheduler panel reads top-down: frequent -> rare.
JOBS = [
    # ---- every 5 min ----
    ("cycle_5m",           300,    [PY, os.path.join(HERE, "memory", "ops", "run_steps.py"),
                                   "gap_alarm.py"],
     "consolidated 2026-11-23: gap_alarm (was PortalGapAlarm); memory_mirror moved to cycle_30m 2026-11-23 - hash-first full-tree mirror exceeded the 5-min slot and was rc=124 every run; now incremental via memory/ops/mirror_cache.json"),
    # ---- every 10 min ----
    ("cycle_10m",          600,    [PY, os.path.join(HERE, "memory", "ops", "run_steps.py"),
                                   "fleet_probe.py",
                                   "memory/ops/load_probe.py",
                                   "memory/orchestrator/fleet_mode.py",
                                   "memory/builder/feed_refresh.py"],
     "consolidated 2026-11-23: fleet_probe + load_probe; fleet_mode.py added 2026-11-24 (cycle-15 mode controller refresh so /api/fleet/mode + idle dispatch see fresh state); feed_refresh.py added 2026-11-25 (was never scheduled - cockpit-feed.json sat 35h stale while the coverage gate expected <=5min; it now re-renders the feed from fleet-metrics every 10min)"),
    # ---- every 30 min ----
    ("cycle_30m",          1800,   [PY, os.path.join(HERE, "memory", "ops", "run_steps.py"),
                                   "memory/mechanic/reboot_recover.py",
                                   "memory/verifier/smb_drift_detector.py",
                                   "memory/mechanic/state_collector.py collect",
                                   "memory_mirror.py"],
     "consolidated 2026-11-23: reboot_recover (was FleetBootRecovery; dead Z:\\ path fixed) + smb_drift_detector (was PortalSmbDrift) + state_collector (was FleetStateCollector); memory_mirror added 2026-11-23 LAST (was cycle_5m) so the fast recovery jobs run first even while a cold mirror takes longer. 2026-11-27: RUN_STEP_TIMEOUT=1800 env - the old 900 s step cap killed every mirror run once the tree grew past ~15k files (mirror silently dead 11-25..11-27); the scandir-inventory rewrite made runs fast again, this is the belt-and-braces",
     {"RUN_STEP_TIMEOUT": "1800"}),
    # ---- every hour ----
    ("cycle_1h",           3600,   [PY, os.path.join(HERE, "memory", "ops", "run_steps.py"),
                                   "memory/mechanic/maintenance_window.py",
                                   "memory/archivist/decay_score.py",
                                   "memory/archivist/size_guard.py",
                                   "memory/archivist/snapshot.py --diff",
                                   "memory/builder/state_snapshot.py",
                                   "daily_git_commit.py"],
     "consolidated 2026-11-23: maintenance_window + memory_audit (decay+size_guard+snapshot-diff) + state_snapshot + daily_git_commit LAST so the commit captures this cycle's output"),
    # ---- every 6h: stealth workflow hosting (Mechanic goal #11, 2026-11-25) ----
    ("stealth_workflows",    21600,  [PY, os.path.join(HERE, "memory", "ops", "run_steps.py"),
                                   "memory/mechanic/stealth/workflow_runner.py memory/mechanic/stealth/lead_enrichment.py --budget-cpu-sec 120 --budget-mem-mb 256",
                                   "memory/mechanic/stealth/workflow_runner.py memory/mechanic/stealth/content_repurpose.py --budget-cpu-sec 180 --budget-mem-mb 256",
                                   "memory/mechanic/stealth/workflow_runner.py memory/mechanic/stealth/invoice_tracker.py --budget-cpu-sec 60 --budget-mem-mb 128"],
     "added 2026-11-25 (Mechanic goal #11): resource-budgeted stealth workflows per memory/mechanic/stealth-hosting.md; user-space only, zero model-seat impact; run logs in memory/mechanic/stealth/runs/"),
    # ---- daily, pinned 03:00 (low-activity window) ----
    ("cycle_daily",        86400,  [PY, os.path.join(HERE, "memory", "ops", "run_steps.py"),
                                   "memory/mechanic/backup.py --run",
                                   "memory/mechanic/winrm_rotate.py",
                                   "memory/goals/forecast_engine.py",
                                   "memory/verifier/perf_gate.py",
                                   "memory/verifier/slo_enforce.py"],
     "consolidated 2026-11-23: winrm_rotate (was schtask WinRMRotation 03:00) + forecast_engine (was FleetForecast30) + verifier_daily (perf_gate+slo_enforce, was 07:00); unified to 03:00. backup.py --run added FIRST 2026-11-27 (nightly fleet backup with 7-day rotation -> archive/fleet-backups/, outside memory/ so size_guard stays green; it was never scheduled before - no backup existed after 2026-11-20)", (3, 0)),
    # ---- weekly ----
    ("schtask_dep_weekly", 604800, [PY, os.path.join(HERE, "memory", "ops", "schtask_dep_weekly.py")],
     "was PortalSchtaskDepGen; PortalDepGenCanary dropped (cmd echo no-op)"),
]

_lock = threading.Lock()
_state = {}   # name -> live job state (incl. Popen while running)


def _log(entry):
    try:
        os.makedirs(os.path.dirname(LOG_F), exist_ok=True)
        with open(LOG_F, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def _next_daily(hh, mm, now=None):
    now = time.time() if now is None else now
    t = time.localtime(now)
    target = time.mktime((t.tm_year, t.tm_mon, t.tm_mday, hh, mm, 0, 0, 0, -1))
    return target if target > now else target + 86400


def _init():
    with _lock:
        for job in JOBS:
            name, every, argv, note = job[0], job[1], job[2], job[3]
            daily = job[4] if len(job) > 4 else None
            env_extra = job[5] if len(job) > 5 else None   # 2026-11-27: per-job env override
            if name not in _state:
                _state[name] = {"name": name, "interval": every, "argv": argv, "note": note,
                                "daily": daily, "env": env_extra,
                                "next_run": _next_daily(*daily) if daily else time.time() + 30,
                                "last_run": None, "last_rc": None,
                                "last_err": "", "runs": 0, "paused": False, "running": False,
                                "proc": None}


def _launch(name):
    st = _state[name]
    env = None
    if st.get("env"):
        env = dict(os.environ)
        env.update(st["env"])
    try:
        st["proc"] = subprocess.Popen(st["argv"], cwd=HERE, stdout=subprocess.DEVNULL,
                                      stderr=subprocess.PIPE, creationflags=NO_WINDOW, env=env)
        st["running"] = True
        st["runs"] += 1
        _log({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "job": name, "event": "start", "pid": st["proc"].pid})
    except Exception as e:
        st["running"] = False
        st["last_rc"] = -1
        st["last_err"] = str(e)[:120]
        _log({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "job": name, "event": "launch-fail", "err": st["last_err"]})


def tick():
    now = time.time()
    with _lock:
        for name, st in _state.items():
            # reap finished children
            if st["running"] and st["proc"] is not None:
                rc = st["proc"].poll()
                if rc is not None:
                    try:
                        err = (st["proc"].stderr.read() or b"")[-160:].decode("utf-8", "replace")
                    except Exception:
                        err = ""
                    st["running"] = False
                    st["last_run"] = now
                    st["last_rc"] = rc
                    st["last_err"] = err.strip()[:160]
                    st["proc"] = None
                    _log({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "job": name, "event": "done", "rc": rc})
            # fire due jobs
            if not st["paused"] and not st["running"] and now >= st["next_run"]:
                st["next_run"] = _next_daily(*st["daily"]) if st.get("daily") else now + st["interval"]
                _launch(name)


def run_forever():
    _init()
    _log({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "event": "scheduler-up", "jobs": len(JOBS)})
    while True:
        try:
            tick()
            _drain_commands()   # actions queued by the portal UI (pause/resume/run-now)
            _save_state()
        except Exception as e:
            _log({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "event": "tick-error", "err": str(e)[:120]})
        time.sleep(5)


def _save_state():
    try:
        with _lock:
            data = {k: {kk: vv for kk, vv in v.items() if kk != "proc" and kk != "argv"}
                    for k, v in _state.items()}
        os.makedirs(os.path.dirname(STATE_F), exist_ok=True)
        tmp = STATE_F + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1)
        os.replace(tmp, STATE_F)
    except Exception:
        pass


def status():
    with _lock:
        jobs = []
        for name, st in _state.items():
            jobs.append({"name": name, "interval": st["interval"], "next_run": st["next_run"],
                         "last_run": st["last_run"], "last_rc": st["last_rc"],
                         "last_err": st["last_err"][:160], "runs": st["runs"],
                         "paused": st["paused"], "running": st["running"], "note": st["note"],
                         "daily": list(st["daily"]) if st.get("daily") else None})
    return {"now": time.time(), "jobs": jobs}


def action(name, what):
    with _lock:
        st = _state.get(name)
        if not st:
            raise ValueError("unknown job: %s" % name)
        if what == "run":
            st["next_run"] = 0.0
        elif what == "pause":
            st["paused"] = True
        elif what == "resume":
            st["paused"] = False
            st["next_run"] = _next_daily(*st["daily"]) if st.get("daily") else time.time() + min(st["interval"], 30)
        else:
            raise ValueError("unknown action: %s" % what)
    return status()


def request_action(name, what):
    """Queue an action for the host process (the portal no longer owns the
    scheduler thread). The host's run_forever drains CMD_F within ~5 s."""
    if what not in ("run", "pause", "resume"):
        raise ValueError("unknown action: %s" % what)
    os.makedirs(os.path.dirname(CMD_F), exist_ok=True)
    tmp = CMD_F + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"job": name, "action": what, "t": time.time()}, f)
    os.replace(tmp, CMD_F)
    return {"queued": True, "job": name, "action": what}


def _drain_commands():
    try:
        if not os.path.exists(CMD_F):
            return
        with open(CMD_F, encoding="utf-8") as f:
            cmd = json.load(f)
        os.remove(CMD_F)
        action(cmd["job"], cmd["action"])
        _log({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "event": "cmd-applied",
              "job": cmd.get("job"), "action": cmd.get("action")})
    except Exception as e:
        _log({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "event": "cmd-error", "err": str(e)[:120]})


def status_from_disk():
    """/api/scheduler data for the portal: read from the state file the host
    process saves every tick (fresh within ~5 s; UI polls every 2 s)."""
    try:
        with open(STATE_F, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {"now": time.time(), "jobs": []}
    jobs = []
    for name, st in data.items():
        jobs.append({"name": name, "interval": st.get("interval"), "next_run": st.get("next_run", 0.0),
                     "last_run": st.get("last_run"), "last_rc": st.get("last_rc"),
                     "last_err": (st.get("last_err") or "")[:160], "runs": st.get("runs", 0),
                     "paused": st.get("paused", False), "running": st.get("running", False),
                     "note": st.get("note", ""),
                     "daily": list(st["daily"]) if st.get("daily") else None})
    return {"now": time.time(), "jobs": jobs}
