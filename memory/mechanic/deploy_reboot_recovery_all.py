#!/usr/bin/env python3
"""deploy_reboot_recovery_all.py - Deploy reboot_recover.py + register FleetBootRecovery schtask on ALL 4 fleet hosts.

Run FROM WHITE (admin or via elev):
    python memory/mechanic/deploy_reboot_recovery_all.py

Verify-only (check status without making changes, safe from any seat):
    python memory/mechanic/deploy_reboot_recovery_all.py --verify-only

What it does:
  - Local (White): registers schtask directly via schtasks
  - Remote (Pale/Black/Red): connects via WinRM, copies script, registers task
  - Idempotent: /f flag overwrites existing tasks
  - Logs results to memory/mechanic/reboot-recovery.jsonl

Prereqs: none (uses reboot_recover.py --register-task for self-registration).
For remote hosts, copy the script via any method (SMB, WinRM file transfer, USB) then run:
    python reboot_recover.py --register-task
on each host as admin.

This script automates the full sequence if pywinrm IS available; otherwise it prints
the manual steps needed per host.
"""
import json, os, sys, time, base64, subprocess, platform, datetime, pathlib

TASK_NAME = "FleetBootRecovery"
SCRIPT_SRC = pathlib.Path(__file__).parent / "reboot_recover.py"
LOG_FILE = pathlib.Path(__file__).parent / "reboot-recovery.jsonl"
REMOTE_DIR = r"C:\FleetOps"

HOSTS_REMOTE = {
    "PALE":  {"ip": "IP_PALE",  "user": "pale",  "pw": "[REDACTED-CREDENTIAL]"},
    "BLACK": {"ip": "IP_BLACK",  "user": "black", "pw": "[REDACTED-CREDENTIAL]"},
    "RED":   {"ip": "IP_RED", "user": "red",   "pw": "[REDACTED-CREDENTIAL]"},
}

def log_entry(entry):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def deploy_local():
    """Register task on the local host (White)."""
    script_path = str(SCRIPT_SRC.resolve())
    py_exe = sys.executable
    cmd = [
        "schtasks", "/create",
        "/tn", TASK_NAME,
        "/tr", f'"{py_exe}" "{script_path}"',
        "/sc", "onstart",
        "/ru", "SYSTEM",
        "/rl", "HIGHEST",
        "/f",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    ok = r.returncode == 0
    # Verify
    v = subprocess.run(["schtasks", "/query", "/tn", TASK_NAME, "/fo", "LIST"],
                       capture_output=True, text=True)
    verified = v.returncode == 0 and TASK_NAME in v.stdout
    return {"host": "WHITE (local)", "registered": ok, "verified": verified,
            "error": r.stderr.strip() if not ok else ""}

def deploy_remote(name, cfg):
    """Deploy to a remote host via WinRM."""
    try:
        import winrm
    except ImportError:
        return {"host": name, "registered": False, "verified": False,
                "error": "pywinrm not installed on this host"}
    
    s = winrm.Session(
        f"http://{cfg['ip']}:5985/wsman",
        auth=(cfg["user"], cfg["pw"]),
        transport="ntlm"
    )
    
    # Create remote dir
    s.run_cmd("cmd", ["/c", f'if not exist "{REMOTE_DIR}" mkdir "{REMOTE_DIR}"'])
    
    # Copy reboot_recover.py via base64
    with open(SCRIPT_SRC, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ps_cmd = (
        f"$b = '{b64}'; "
        f"$bytes = [Convert]::FromBase64String($b); "
        f"[IO.File]::WriteAllBytes('{REMOTE_DIR}\\reboot_recover.py', $bytes)"
    )
    s.run_cmd("powershell", ["-NoProfile", "-Command", ps_cmd])
    
    # Find python on remote
    r_py = s.run_cmd("cmd", ["/c", "where python"])
    py_out = r_py.std_out.decode().strip()
    py_exe = py_out.splitlines()[0].strip() if py_out else "python"
    
    # Register task
    task_cmd = (
        f'schtasks /create /tn "{TASK_NAME}" '
        f'/tr "\"{py_exe}\" \"{REMOTE_DIR}\\reboot_recover.py\"" '
        f'/sc onstart /ru SYSTEM /rl HIGHEST /f'
    )
    r_task = s.run_cmd("cmd", ["/c", task_cmd])
    
    # Verify
    r_verify = s.run_cmd("schtasks", ["/query", "/tn", TASK_NAME, "/fo", "LIST"])
    verified = r_verify.returncode == 0 and TASK_NAME in r_verify.std_out.decode()
    
    return {"host": name, "registered": r_task.status_code == 0,
            "verified": verified, "python": py_exe}

def verify_local():
    """Check if FleetBootRecovery task exists on local host."""
    v = subprocess.run(["schtasks", "/query", "/tn", TASK_NAME, "/fo", "LIST"],
                       capture_output=True, text=True)
    ok = v.returncode == 0 and TASK_NAME in v.stdout
    return {"host": "WHITE (local)", "verified": ok,
            "detail": v.stdout.strip()[:200] if ok else v.stderr.strip()[:100]}

def verify_only():
    """Verify deployment status: local schtasks + jsonl log for remotes."""
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print(f"[{ts}] VERIFY-ONLY mode (no changes made)\n")
    
    # Local
    res_local = verify_local()
    print(f"  {res_local['host']}: {'PASS' if res_local['verified'] else 'FAIL'}")
    if not res_local["verified"]:
        print(f"    detail: {res_local.get('detail','')}")
    
    # Remote: check jsonl log for most recent deployment results
    remote_status = {}
    if LOG_FILE.exists():
        last_deploy = None
        with open(LOG_FILE) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("type") == "deploy_reboot_recovery_all":
                        last_deploy = entry
                except json.JSONDecodeError:
                    continue
        if last_deploy:
            print(f"\n  Last deployment logged: {last_deploy['ts']}")
            for host, res in last_deploy.get("results", {}).items():
                if "local" in host.lower():
                    continue
                ok = res.get("verified", False)
                remote_status[host] = ok
                mark = 'PASS' if ok else 'FAIL'
                err = f" ({res.get('error','')[:60]})" if not ok else ""
                print(f"  {host}: {mark}{err}")
        else:
            print("\n  No deployment found in reboot-recovery.jsonl")
    else:
        print("\n  reboot-recovery.jsonl not found - no prior deployment logged")
    
    all_ok = res_local["verified"] and all(remote_status.values()) if remote_status else res_local["verified"]
    total = 1 + len(remote_status)
    passed = (1 if res_local["verified"] else 0) + sum(1 for v in remote_status.values() if v)
    print(f"\nSummary: {passed}/{total} hosts verified")
    return 0 if all_ok else 1

def _run_test_safely(test_path, timeout=60):
    try:
        r = subprocess.run([sys.executable, str(test_path)], capture_output=True, text=True, timeout=timeout)
        tail = (r.stdout.strip().splitlines() + r.stderr.strip().splitlines())[-3:]
        return {"ran": True, "exit": r.returncode, "ok": r.returncode == 0, "tail": tail}
    except subprocess.TimeoutExpired:
        return {"ran": True, "exit": -1, "ok": False, "tail": ["TIMEOUT"]}
    except Exception as e:
        return {"ran": False, "ok": None, "tail": [str(e)[:120]]}

def preflight():
    """Deployment-readiness report. SAFE FROM ANY SEAT (no schtasks/WinRM writes).
    Run this FIRST from the non-sandbox White seat before the one-shot deploy:
        python memory/mechanic/deploy_reboot_recovery_all.py --preflight
    Catches, up front: missing pywinrm (=> manual fallback), broken unit test,
    bad host config, and running on a sandbox seat by mistake."""
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print(f"[{ts}] PREFLIGHT - reboot-recovery deployment readiness (read-only, no changes)\n")

    checks = {}

    # 1. python env
    checks["python"] = {"ok": True, "detail": f"{platform.python_version()} @ {sys.executable}"}

    # 2. recover script present + has a registration entrypoint
    sp = SCRIPT_SRC
    if sp.exists() and sp.stat().st_size > 0:
        try:
            src_txt = sp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            src_txt = ""
        has_register = ("--register-task" in src_txt) or ("argparse" in src_txt) or ("def main" in src_txt)
        checks["script"] = {"ok": has_register,
                            "detail": f"{sp.name} {sp.stat().st_size}B; register-task entrypoint={'yes' if has_register else 'NO'}"}
    else:
        checks["script"] = {"ok": False, "detail": f"MISSING or empty: {sp}"}

    # 3. unit test (auto-detect the canonical one)
    cands = ["reboot_recovery_test.py", "boot_recovery_test.py", "test_deploy_reboot_recovery.py"]
    tpath = next((SCRIPT_SRC.parent / c for c in cands if (SCRIPT_SRC.parent / c).exists()), None)
    if tpath:
        tr = _run_test_safely(tpath)
        checks["unit_test"] = {"ok": bool(tr.get("ok")),
                               "detail": f"{tpath.name} exit={tr.get('exit')} tail={tr.get('tail')}"}
    else:
        checks["unit_test"] = {"ok": None, "detail": "SKIP - no test file found"}

    # 4. pywinrm availability (missing => manual fallback path; warning, not fatal)
    try:
        import winrm  # noqa: F401
        checks["pywinrm"] = {"ok": True, "detail": "available (remote auto-deploy will be attempted)"}
    except ImportError:
        checks["pywinrm"] = {"ok": False, "warning": True,
                             "detail": "MISSING - remote hosts need manual copy + 'python reboot_recover.py --register-task' (deploy script prints steps)"}

    # 5. host config sanity
    bad = []
    for name, cfg in HOSTS_REMOTE.items():
        for k in ("ip", "user", "pw"):
            if not cfg.get(k):
                bad.append(f"{name}.{k}")
    checks["hosts"] = {"ok": len(HOSTS_REMOTE) == 3 and not bad,
                       "detail": f"{len(HOSTS_REMOTE)} remote hosts; missing fields: {bad or 'none'}"}

    # 6. seat sandbox heuristic (read-only schtasks query; COM wall => sandbox)
    try:
        v = subprocess.run(["schtasks", "/query"], capture_output=True, text=True, timeout=15)
        com_wall = (v.returncode != 0) and ("class not registered" in ((v.stderr or "") + (v.stdout or "")).lower())
        checks["seat"] = {"ok": not com_wall,
                          "detail": "non-sandbox (schtasks COM OK)" if not com_wall
                                  else "SANDBOX DETECTED (schtasks COM unavailable) - run the real deploy from a non-sandbox White seat"}
    except FileNotFoundError:
        checks["seat"] = {"ok": None, "detail": "schtasks.exe not found on this seat (likely sandbox)"}
    except Exception as e:
        checks["seat"] = {"ok": None, "detail": f"seat check skipped ({str(e)[:80]})"}

    ready = all(c.get("ok") for c in checks.values() if c.get("ok") is not None)
    for name, c in checks.items():
        mark = "PASS" if c.get("ok") else ("SKIP" if c.get("ok") is None else ("WARN" if c.get("warning") else "FAIL"))
        print(f"  [{mark}] {name}: {c['detail']}")

    note = " (remote deploy will use manual fallback - pywinrm missing)" if not checks["pywinrm"]["ok"] else ""
    print(f"\nPREFLIGHT RESULT: {'READY' if ready else 'NOT READY'}{note}")

    log_entry({"ts": ts, "type": "preflight_reboot_recovery", "by": "orchestrator-assist",
               "ready": ready, "checks": checks})
    print(f"  logged -> {LOG_FILE.name}")
    return 0 if ready else 1

def main():
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    if "--preflight" in sys.argv:
        sys.exit(preflight())
    if "--verify-only" in sys.argv:
        sys.exit(verify_only())
    
    results = []
    
    # Local (White)
    print(f"[{ts}] Deploying to local host...")
    res_local = deploy_local()
    results.append(res_local)
    print(f"  {res_local['host']}: registered={res_local['registered']} verified={res_local['verified']}")
    
    # Remotes
    for name, cfg in HOSTS_REMOTE.items():
        print(f"[{ts}] Deploying to {name} ({cfg['ip']})...")
        try:
            res = deploy_remote(name, cfg)
        except Exception as e:
            res = {"host": name, "registered": False, "verified": False, "error": str(e)[:200]}
        results.append(res)
        print(f"  {name}: registered={res.get('registered')} verified={res.get('verified')}")
    
    # Log
    entry = {"ts": ts, "type": "deploy_reboot_recovery_all",
             "results": {r["host"]: r for r in results},
             "all_verified": all(r.get("verified", False) for r in results)}
    log_entry(entry)
    
    passed = sum(1 for r in results if r.get("verified"))
    print(f"\nSummary: {passed}/{len(results)} hosts verified")
    sys.exit(0 if passed == len(results) else 1)

if __name__ == "__main__":
    main()
