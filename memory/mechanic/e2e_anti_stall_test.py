#!/usr/bin/env python3
"""
e2e_anti_stall_test.py - Full anti-stall chain E2E test (Goal 3).

Executes against a non-critical host (Black or Pale):
  1. Verify target host is UP (TCP probe)
  2. Stop studio service on target via WinRM (simulate host-down)
  3. Wait for remote watchdog (FleetBootRecovery, 5-min interval) to detect + recover
  4. Verify port 8888 comes back up
  5. Verify agent responds (HTTP probe to /api/health or similar)
  6. Record full timeline with timestamps

Acceptance: full cycle <15 min; all log entries in correct order; agent responsive.
Usage: python memory/mechanic/e2e_anti_stall_test.py --host BLACK [--dry-run]
Requires: non-sandbox seat with WinRM + network egress to target host.
"""
import json, os, sys, time, socket, subprocess, datetime, pathlib

LOG = pathlib.Path(__file__).parent / "reboot-recovery.jsonl"
HOSTS = {
    "PALE": ("IP_PALE", 8888),
    "BLACK": ("IP_BLACK", 8888),
}
MAX_CYCLE_S = 900  # 15 min
WATCHDOG_INTERVAL_S = 300  # FleetBootRecovery runs every 5 min


def ts():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def log_entry(entry):
    entry["ts"] = ts()
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"  [{entry.get('step','?')}] {entry.get('msg', json.dumps(entry)[:120])}")


def tcp_check(ip, port, timeout=5):
    t0 = time.monotonic()
    try:
        s = socket.create_connection((ip, port), timeout=timeout)
        ms = (time.monotonic() - t0) * 1000
        s.close()
        return True, round(ms, 1)
    except (socket.timeout, OSError):
        return False, round((time.monotonic() - t0) * 1000, 1)


def winrm_exec(host_key, cmd, args=None):
    """Execute a command on remote host via WinRM/PowerShell remoting. Returns (ok, output)."""
    ip, _ = HOSTS[host_key]
    full_cmd = cmd if not args else f'{cmd} {" ".join(args)}'
    # Try pywinrm first
    try:
        import winrm
        session = winrm.Session(
            f"http://{ip}:5985/wsman",
            auth=(host_key.lower(), ""),
            transport="ntlm",
            operation_timeout_sec=60,
            read_timeout_sec=120,
        )
        r = session.run_cmd(cmd, args or [])
        out = (r.std_out.decode() + r.std_err.decode()).strip()
        return r.status_code == 0, out
    except ImportError:
        pass
    except Exception as e:
        return False, str(e)[:200]
    # Fallback: PowerShell remoting (no extra deps)
    try:
        ps_cmd = f'powershell -NoProfile -Command "Invoke-Command -ComputerName {ip} -ScriptBlock {{ {full_cmd} }}"'
        import subprocess
        r = subprocess.run(ps_cmd, shell=True, capture_output=True, text=True, timeout=120)
        out = (r.stdout + r.stderr).strip()
        return r.returncode == 0, out[:500]
    except Exception as e:
        return False, str(e)[:200]


def stop_studio(host_key):
    """Stop the studio process on remote host (simulate host-down)."""
    ip, port = HOSTS[host_key]
    # First verify it's up
    ok, ms = tcp_check(ip, port)
    if not ok:
        return False, f"Host already down ({ms}ms) - cannot simulate"
    # Kill the process listening on 8888 via PowerShell remoting
    ps = ("$p = Get-NetTCPConnection -LocalPort 8888 -State Listen -ErrorAction SilentlyContinue; "
          "if ($p) { Stop-Process -Id $p.OwningProcess -Force; 'KILLED PID ' + $p.OwningProcess } else { 'NO PROCESS ON 8888' }")
    # Try pywinrm first
    try:
        import winrm
        session = winrm.Session(
            f"http://{ip}:5985/wsman",
            auth=(host_key.lower(), ""),
            transport="ntlm",
            operation_timeout_sec=30,
            read_timeout_sec=60,
        )
        r = session.run_ps(ps)
        out = (r.std_out.decode() + r.std_err.decode()).strip()
        return True, out
    except ImportError:
        pass
    except Exception as e:
        return False, str(e)[:200]
    # Fallback: PowerShell remoting
    try:
        import subprocess
        ps_cmd = f'powershell -NoProfile -Command "Invoke-Command -ComputerName {ip} -ScriptBlock {{ {ps} }}"'
        r = subprocess.run(ps_cmd, shell=True, capture_output=True, text=True, timeout=120)
        out = (r.stdout + r.stderr).strip()
        return r.returncode == 0, out[:500]
    except Exception as e:
        return False, str(e)[:200]


def wait_for_recovery(ip, port, max_wait_s=MAX_CYCLE_S):
    """Poll port until it comes back. Returns (recovered: bool, elapsed_s)."""
    t0 = time.monotonic()
    while (time.monotonic() - t0) < max_wait_s:
        ok, ms = tcp_check(ip, port, timeout=3)
        if ok:
            return True, round(time.monotonic() - t0, 1), ms
        time.sleep(10)
    return False, round(time.monotonic() - t0, 1), None


def verify_agent_response(ip, port):
    """Verify the agent actually responds (not just port open)."""
    import urllib.request
    try:
        url = f"http://{ip}:{port}/api/health"
        req = urllib.request.urlopen(url, timeout=10)
        body = req.read().decode()[:200]
        return True, body
    except Exception as e:
        # Try root as fallback
        try:
            url = f"http://{ip}:{port}/"
            req = urllib.request.urlopen(url, timeout=10)
            return True, f"HTTP {req.status} (root)"
        except Exception as e2:
            return False, str(e2)[:150]


def main():
    dry = "--dry-run" in sys.argv
    host_key = None
    for arg in sys.argv:
        if arg.startswith("--host="):
            host_key = arg.split("=", 1)[1].upper()
        elif arg.upper() in HOSTS and not arg.startswith("--"):
            host_key = arg.upper()
    if not host_key:
        host_key = "BLACK"  # default non-critical
    
    ip, port = HOSTS[host_key]
    run_id = f"e2e_{host_key.lower()}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"\n{'='*60}")
    print(f"E2E Anti-Stall Test: {host_key} ({ip}:{port})")
    print(f"Run ID: {run_id}")
    print(f"{'='*60}\n")

    # STEP 1: Verify host is UP
    print("STEP 1: Verify target host is UP")
    ok, ms = tcp_check(ip, port)
    log_entry({"run": run_id, "step": "1_verify_up", "host": host_key, "ok": ok, "latency_ms": ms})
    if not ok:
        print(f"  ABORT: {host_key} is already DOWN. Cannot simulate.")
        log_entry({"run": run_id, "step": "ABORT", "reason": "host already down"})
        return

    if dry:
        print("\n[DRY-RUN] Host verified UP. Would proceed with stop+recover cycle.")
        log_entry({"run": run_id, "step": "DRY_RUN_COMPLETE", "verdict": "PASS (dry-run)"})
        return

    # STEP 2: Stop studio (simulate host-down)
    print("\nSTEP 2: Stop studio service (simulate host-down)")
    ok, out = stop_studio(host_key)
    log_entry({"run": run_id, "step": "2_stop_studio", "ok": ok, "output": out[:200]})
    if not ok:
        print(f"  ABORT: could not stop studio: {out}")
        return

    # Verify it's actually down
    time.sleep(3)
    ok_down, _ = tcp_check(ip, port, timeout=3)
    log_entry({"run": run_id, "step": "2b_confirm_down", "down": not ok_down})
    if ok_down:
        print("  WARN: port still up after kill - studio may have auto-restarted")

    # STEP 3: Wait for watchdog recovery
    print(f"\nSTEP 3: Waiting for FleetBootRecovery (interval={WATCHDOG_INTERVAL_S}s, max {MAX_CYCLE_S}s)")
    t_start = time.monotonic()
    recovered, elapsed_s, final_ms = wait_for_recovery(ip, port, MAX_CYCLE_S)
    log_entry({"run": run_id, "step": "3_recover", "recovered": recovered,
               "elapsed_s": elapsed_s, "final_latency_ms": final_ms})

    # STEP 4: Verify agent responds
    print("\nSTEP 4: Verify agent response")
    agent_ok, agent_out = verify_agent_response(ip, port)
    log_entry({"run": run_id, "step": "4_agent_response", "ok": agent_ok, "response": agent_out[:200]})

    # VERDICT
    total_s = round(time.monotonic() - t_start, 1)
    verdict = "PASS" if (recovered and agent_ok and total_s < MAX_CYCLE_S) else "FAIL"
    log_entry({"run": run_id, "step": "VERDICT", "verdict": verdict,
               "total_cycle_s": total_s, "recovery_s": elapsed_s,
               "criteria": {"recovered": recovered, "agent_ok": agent_ok, "under_15min": total_s < MAX_CYCLE_S}})
    print(f"\n{'='*60}")
    print(f"VERDICT: {verdict}")
    print(f"  Total cycle: {total_s}s (limit: {MAX_CYCLE_S}s)")
    print(f"  Recovery time: {elapsed_s}s")
    print(f"  Agent responsive: {agent_ok}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
