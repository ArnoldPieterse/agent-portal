#!/usr/bin/env python3
# Provenance: created 2026-11-23 (White + assistant). Replaces the schtask/guardian
# chain (PortalRun -> wscript -> cmd -> portal_guardian.py) with ONE host process.
"""Portal host (2026-11-23): one process, launched directly on the host as
pythonw.exe, that runs everything the old scheduled-task chain ran:

  * all 6 scheduled jobs   - portal_scheduler.run_forever() in a thread
                             (same state/log files: memory/ops/scheduler-*.json*)
  * the portal server      - spawns pythonw agent_portal.py, health-checks
                             :8099 every 20 s, respawns if dead/stale
  * the OOM daemon         - spawns oom_recovery.py watch, respawns if dead

Why: periodic schtasks kept flashing console windows and stealing focus
(wscript/cmd/conhost chain). Everything here is NO_WINDOW; the only Task
Scheduler entry left is PortalRun as a LOGON-ONLY one-shot launcher for THIS
script (no stop timer, no periodic trigger) - so reboots/logons heal with
zero human step, and steady state has zero scheduler involvement.

Launch:  pythonw.exe C:\Projects\AgentPortal\portal_host.py   (single-instance)
Log:     memory/ops/host-log.jsonl | pid file: memory/ops/host.pid
"""
import json, os, subprocess, sys, threading, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
PY  = r"C:\Projects\AgentPortal\Python\pythoncore-3.15-64\python.exe"
PYW = r"C:\Projects\AgentPortal\Python\pythoncore-3.15-64\pythonw.exe"
NO_WINDOW = 0x08000000          # CREATE_NO_WINDOW - never a console, never focus
PORTAL_PORT = 8099
PID_F = os.path.join(HERE, "memory", "ops", "host.pid")
LOG_F = os.path.join(HERE, "memory", "ops", "host-log.jsonl")


def _log(event, **kw):
    try:
        e = {"t": time.strftime("%Y-%m-%d %H:%M:%S"), "event": event}
        e.update(kw)
        os.makedirs(os.path.dirname(LOG_F), exist_ok=True)
        with open(LOG_F, "a", encoding="utf-8") as f:
            f.write(json.dumps(e) + "\n")
    except Exception:
        pass


def _proc_cmdlines():
    """{pid: commandline} for python/pythonw processes.
    wmic.exe is GONE on this Windows build (removed 24H2) - the old guardian's
    wmic scans silently failed; use PowerShell Get-CimInstance instead."""
    ps = ("Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | "
          "ForEach-Object { Write-Output ('{0}|{1}' -f $_.ProcessId, ($_.CommandLine -replace '\\r\\n', ' ')) }")
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                             capture_output=True, text=True, timeout=25).stdout
    except Exception as e:
        _log("procscan-fail", err=str(e)[:100])
        return {}
    procs = {}
    for line in out.splitlines():
        if "|" not in line:
            continue
        pid_s, cl = line.split("|", 1)
        try:
            procs[int(pid_s.strip())] = cl.strip()
        except ValueError:
            pass
    return procs


def _pids_matching(*needles):
    me = os.getpid()
    out = []
    for pid, cl in _proc_cmdlines().items():
        if pid == me:
            continue
        low = (cl or "").lower()
        if all(n.lower() in low for n in needles):
            out.append(pid)
    return out


def _kill(pid):
    try:
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, timeout=15)
    except Exception:
        pass


def _spawn(argv, what):
    p = subprocess.Popen(argv, cwd=HERE, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, creationflags=NO_WINDOW)
    _log("spawned", what=what, pid=p.pid, argv=" ".join(argv))
    return p


def portal_loop():
    """Keep agent_portal.py alive: any HTTP answer = up; no answer = kill stale + respawn."""
    url = "http://127.0.0.1:%d/" % PORTAL_PORT
    while True:
        try:
            alive = False
            try:
                urllib.request.urlopen(url, timeout=4)
                alive = True
            except urllib.error.HTTPError:
                alive = True          # server answered (any status) -> process is up
            except Exception:
                alive = False
            if not alive:
                for pid in _pids_matching("agent_portal.py"):
                    _kill(pid)
                    _log("killed-stale-portal", pid=pid)
                # pythonw.exe in this build does not execute user code (verified 2026-11-23):
                # console python + NO_WINDOW gives the same windowless result.
                _spawn([PY, os.path.join(HERE, "agent_portal.py")], "portal")
            else:
                time.sleep(20)
        except Exception as e:
            _log("portal-loop-error", err=str(e)[:120])
            time.sleep(20)


def oom_loop():
    # 'watch' is a one-shot detect->recover command (exits by design) - run it
    # periodically, do NOT treat it as a daemon. 5-min cadence.
    while True:
        try:
            r = subprocess.run([PY, os.path.join(HERE, "memory", "mechanic", "oom_recovery.py"), "watch"],
                               cwd=HERE, capture_output=True, text=True, timeout=120,
                               creationflags=NO_WINDOW)
            out = (r.stdout or "").strip().splitlines()
            last = out[-1][:160] if out else ""
            if r.returncode != 0 or '"action": "none"' not in last:
                _log("oom-watch", rc=r.returncode, last=last)
        except Exception as e:
            _log("oom-loop-error", err=str(e)[:120])
        time.sleep(300)


def _ensure_launcher():
    """Self-heal the boot chain (2026-11-23; fixed 2026-11-24): after a reboot the portal
    did NOT start because the logon launcher was missing entirely (no PortalRun schtask,
    and the Startup folder itself was gone). The host re-creates/repairs the hidden-window
    VBS launcher if it is absent or stale. 2026-11-24 fix: this previously wrote to a
    non-existent 'StartMenu' folder (created on the spot, never read by Windows), so the
    self-heal silently never worked; it now manages the canonical portal_host.vbs in the
    real 'Start Menu' Startup folder and is re-run every 5 min from the main loop."""
    try:
        # Do NOT trust USERPROFILE: this host's tool processes run with
        # USERPROFILE=C:\Projects\AgentPortal (verified 2026-11-23), which would plant the
        # launcher where Windows never looks. 'White' is the only profile on this machine.
        prof = __import__("os").path.expanduser("~")
        d = os.path.join(prof, "AppData", "Roaming", "Microsoft", "Windows",
                         "Start Menu", "Programs", "Startup")
        f = os.path.join(d, "portal_host.vbs")
        vbs = ("' PortalRun logon launcher (2026-11-23). Starts the single host process windowlessly.\r\n"
               "' pythonw.exe in this build does not execute user code -> console python, window style 0.\r\n"
               'Set sh = CreateObject("WScript.Shell")\r\n'
               'sh.CurrentDirectory = "%s"\r\n'
               'sh.Run """%s"" ""%s""", 0, False\r\n' % (HERE, PY, os.path.join(HERE, "portal_host.py")))
        try:
            cur = open(f, encoding="ascii").read()
        except Exception:
            cur = None
        if cur is not None and cur.rstrip("\r\n") == vbs.rstrip("\r\n"):
            return
        os.makedirs(d, exist_ok=True)
        with open(f, "w", encoding="ascii") as fh:
            fh.write(vbs)
        _log("launcher-restored", path=f, stale=cur is not None)
    except Exception as e:
        _log("launcher-restore-fail", err=str(e)[:120])


def main():
    _log("host-start", pid=os.getpid())
    if "--selftest" in sys.argv:
        import portal_scheduler
        print("import ok; jobs:", len(portal_scheduler.JOBS))
        procs = _proc_cmdlines()
        print("procscan ok, python procs seen:", len(procs))
        return
    # single instance: if another portal_host is already running, exit quietly
    others = _pids_matching("portal_host.py")
    if others:
        _log("exit-duplicate", existing=others)
        return
    try:
        os.makedirs(os.path.dirname(PID_F), exist_ok=True)
        with open(PID_F, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
    except Exception:
        pass
    _log("host-up", pid=os.getpid(), py=sys.version.split()[0])
    _ensure_launcher()   # self-heal boot chain: re-create logon launcher if missing

    import portal_scheduler
    threading.Thread(target=portal_scheduler.run_forever, daemon=True).start()   # all 6 jobs
    threading.Thread(target=portal_loop, daemon=True).start()
    threading.Thread(target=oom_loop, daemon=True).start()

    _last_heal = time.time()
    while True:
        try:
            time.sleep(30)
        except KeyboardInterrupt:   # stdin-EOF style interrupts: keep running
            continue
        if time.time() - _last_heal > 300:   # re-check logon launcher every 5 min (self-heal)
            _ensure_launcher()
            _last_heal = time.time()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        _log("host-exit", reason="keyboard-interrupt")
    except Exception as e:          # never die silently - leave a trace in host-log
        _log("host-crash", err=str(e)[:200])
        raise
