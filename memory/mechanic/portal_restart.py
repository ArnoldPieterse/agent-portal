"""
portal_restart.py - One-command portal restart with health check (Runbook step C)
Part of Mechanic Goal 10: Runbook Automation (top-5)

Usage: python memory/mechanic/portal_restart.py [--force] [--timeout 30]

Idempotent: if portal is already healthy, does nothing and exits 0.
--force: skip health check and always restart.
Logs to memory/mechanic/runbook-executions.jsonl. Runtime <60s.
"""
import json, socket, sys, time, pathlib, subprocess, urllib.request
from datetime import datetime, timezone

PORTAL_PORT = 8099
LOG_PATH = pathlib.Path("memory/mechanic/runbook-executions.jsonl")
HEALTH_TIMEOUT_S = 30


def log_entry(action: str, ok: bool, detail: str):
    """Append one line to runbook-executions.jsonl."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "script": "portal_restart.py",
        "action": action,
        "ok": ok,
        "detail": detail[:200],
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def tcp_check(port: int, timeout: float = 3.0) -> bool:
    """Simple TCP connect check."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        rc = sock.connect_ex(("127.0.0.1", port))
        sock.close()
        return rc == 0
    except Exception:
        return False


def health_check(timeout: float = 5.0) -> tuple:
    """Check portal /api/health. Returns (ok, latency_ms)."""
    try:
        t0 = time.monotonic()
        req = urllib.request.Request(f"http://127.0.0.1:{PORTAL_PORT}/api/health")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = (time.monotonic() - t0) * 1000
            body = json.loads(resp.read())
            return resp.status == 200 and body.get("status") in ("ok", "healthy", None), round(elapsed, 1)
    except Exception:
        return False, None


def stop_portal() -> tuple:
    """Stop portal. Returns (ok, method)."""
    # Method 1: schtask PortalRun (preferred - graceful)
    try:
        r = subprocess.run(
            ["schtasks", "/end", "/tn", "PortalRun"],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0:
            return True, "schtasks_end"
    except Exception:
        pass
    # Method 2: taskkill by port (find PID on :8099)
    try:
        r = subprocess.run(
            ["netstat", "-ano", "|", "findstr", f":{PORTAL_PORT}", "LISTENING"],
            capture_output=True, text=True, timeout=10, shell=True
        )
        lines = r.stdout.strip().splitlines()
        for line in lines:
            parts = line.split()
            if len(parts) >= 5 and "LISTENING" in line:
                pid = parts[-1]
                subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True, timeout=10)
                return True, f"taskkill_{pid}"
    except Exception as e:
        return False, str(e)[:100]
    return False, "no_method_available"


def start_portal() -> tuple:
    """Start portal. Returns (ok, method)."""
    # Method 1: schtask PortalRun
    try:
        r = subprocess.run(
            ["schtasks", "/run", "/tn", "PortalRun"],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0:
            return True, "schtasks_run"
    except Exception:
        pass
    # Method 2: direct python launch (background)
    try:
        subprocess.Popen(
            [sys.executable, "agent_portal.py"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=0x00000008  # DETACHED_PROCESS
        )
        return True, "direct_launch"
    except Exception as e:
        return False, str(e)[:100]


def wait_healthy(timeout_s: float = HEALTH_TIMEOUT_S) -> tuple:
    """Poll until portal is healthy. Returns (ok, elapsed_s)."""
    t0 = time.monotonic()
    while (time.monotonic() - t0) < timeout_s:
        ok, ms = health_check(timeout=3)
        if ok:
            return True, round(time.monotonic() - t0, 1)
        time.sleep(2)
    return False, round(time.monotonic() - t0, 1)


def main():
    force = "--force" in sys.argv
    timeout_idx = sys.argv.index("--timeout") + 1 if "--timeout" in sys.argv else None
    wait_timeout = float(sys.argv[timeout_idx]) if timeout_idx and timeout_idx < len(sys.argv) else HEALTH_TIMEOUT_S

    t_start = time.monotonic()

    # Step 1: Check current health
    if not force:
        ok, ms = health_check()
        if ok:
            elapsed = round(time.monotonic() - t_start, 2)
            log_entry("already_healthy", True, f"portal up ({ms}ms), no action taken")
            print(f"[OK] Portal already healthy ({ms}ms). No restart needed.")
            return 0

    # Step 2: Stop portal
    stop_ok, stop_method = stop_portal()
    if not stop_ok:
        log_entry("stop_failed", False, f"method={stop_method}")
        print(f"[FAIL] Could not stop portal: {stop_method}")
        return 1
    time.sleep(2)  # grace period

    # Step 3: Start portal
    start_ok, start_method = start_portal()
    if not start_ok:
        log_entry("start_failed", False, f"method={start_method}")
        print(f"[FAIL] Could not start portal: {start_method}")
        return 1

    # Step 4: Wait for health
    healthy, elapsed = wait_healthy(timeout_s=wait_timeout)
    total_time = round(time.monotonic() - t_start, 1)
    if healthy:
        log_entry("restart_ok", True, f"stop={stop_method} start={start_method} recovered_in={elapsed}s total={total_time}s")
        print(f"[OK] Portal restarted. Recovered in {elapsed}s (total {total_time}s).")
        return 0
    else:
        log_entry("restart_timeout", False, f"stop={stop_method} start={start_method} not_healthy_after={elapsed}s")
        print(f"[FAIL] Portal not healthy after {elapsed}s. Check logs.")
        return 1


if __name__ == "__main__":
    sys.exit(main())