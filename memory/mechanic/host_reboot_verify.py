"""
host_reboot_verify.py - One-command host reboot + post-boot verification (Runbook step E)
Part of Mechanic Goal 10: Runbook Automation (top-5)

Usage: python memory/mechanic/host_reboot_verify.py <HOST> [--wait 300]

HOST: white|pale|black|red
Idempotent: if host is already up and healthy, skips reboot.
Logs to memory/mechanic/runbook-executions.jsonl. Runtime <60s (excl. boot wait).
"""
import json, socket, sys, time, pathlib, subprocess, urllib.request
from datetime import datetime, timezone

HOSTS = {
    "white": {"ip": "127.0.0.1", "port": 8888},
    "pale":  {"ip": "IP_PALE", "port": 8888},
    "black": {"ip": "IP_BLACK", "port": 8888},
    "red":   {"ip": "IP_RED", "port": 8888},
}
LOG_PATH = pathlib.Path("memory/mechanic/runbook-executions.jsonl")
BOOT_WAIT_S = 300


def log_entry(action: str, ok: bool, detail: str):
    entry = {"ts": datetime.now(timezone.utc).isoformat(), "script": "host_reboot_verify.py", "action": action, "ok": ok, "detail": detail[:200]}
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def tcp_check(ip: str, port: int, timeout: float = 3.0) -> bool:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        rc = sock.connect_ex((ip, port))
        sock.close()
        return rc == 0
    except Exception:
        return False


def verify_models_loaded(ip: str, port: int) -> tuple:
    """Check if Studio is up and has models loaded. Returns (ok, model_count)."""
    try:
        req = urllib.request.Request(f"http://{ip}:{port}/api/v0/models/loaded")
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            return True, len(data.get("models", [data.get("model", "")])) if data else 0
    except Exception:
        return False, 0


def trigger_reboot(host_name: str) -> tuple:
    """Trigger reboot on remote host. Returns (ok, method)."""
    ip = HOSTS[host_name]["ip"]
    # Method 1: PowerShell remoting (preferred for remote hosts)
    if host_name != "white":
        ps_cmd = f'powershell -NoProfile -Command "Invoke-Command -ComputerName {ip} -ScriptBlock {{ Restart-Computer -Force }}"'
        try:
            r = subprocess.run(ps_cmd, shell=True, capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                return True, "powershell_reboot"
        except Exception:
            pass
    # Method 2: schtask on local host
    try:
        r = subprocess.run(["shutdown", "/r", "/t", "5"], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return True, "shutdown_cmd"
    except Exception:
        pass
    # Method 3: WinRM (if pywinrm available)
    try:
        import winrm
        session = winrm.Session(f"http://{ip}:5985/wsman", auth=(host_name, ""), transport="ntlm")
        session.run_cmd("shutdown", ["/r", "/t", "5"])
        return True, "winrm_shutdown"
    except ImportError:
        pass
    except Exception as e:
        return False, str(e)[:100]
    return False, "no_method_available"


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0

    host_name = sys.argv[1].lower()
    if host_name not in HOSTS:
        log_entry("unknown_host", False, f"host '{host_name}' not in {list(HOSTS.keys())}")
        print(f"[FAIL] Unknown host: {host_name}. Options: {list(HOSTS.keys())}")
        return 1

    wait_idx = sys.argv.index("--wait") + 1 if "--wait" in sys.argv else None
    boot_wait = int(sys.argv[wait_idx]) if wait_idx and wait_idx < len(sys.argv) else BOOT_WAIT_S

    ip, port = HOSTS[host_name]["ip"], HOSTS[host_name]["port"]
    t_start = time.monotonic()

    # Step 1: Check if host is already healthy
    if tcp_check(ip, port):
        ok, count = verify_models_loaded(ip, port)
        if ok:
            log_entry("already_healthy", True, f"{host_name} up with {count} model(s), no reboot needed")
            print(f"[OK] {host_name} already healthy ({count} models loaded). No reboot needed.")
            return 0
        # Host is up but no models - might need reboot to trigger boot tasks
        print(f"[INFO] {host_name} is up but no models detected. Proceeding with reboot...")
    else:
        log_entry("host_already_down", False, f"{host_name} not reachable on :{port} before reboot attempt")
        print(f"[WARN] {host_name} already unreachable. Attempting reboot anyway...")

    # Step 2: Trigger reboot
    reboot_ok, method = trigger_reboot(host_name)
    if not reboot_ok:
        log_entry("reboot_failed", False, f"method={method}")
        print(f"[FAIL] Could not trigger reboot: {method}")
        return 1
    print(f"[INFO] Reboot triggered via {method}. Waiting up to {boot_wait}s for recovery...")

    # Step 3: Wait for host to come back
    t0 = time.monotonic()
    while (time.monotonic() - t0) < boot_wait:
        if tcp_check(ip, port, timeout=5):
            break
        time.sleep(10)
    else:
        log_entry("boot_timeout", False, f"{host_name} not back after {boot_wait}s")
        print(f"[FAIL] {host_name} did not come back within {boot_wait}s")
        return 1

    boot_time = round(time.monotonic() - t0, 1)
    print(f"[INFO] {host_name} is back (TCP :{port} open) after {boot_time}s. Verifying models...")

    # Step 4: Verify models loaded
    time.sleep(5)  # grace for model loading
    models_ok, count = verify_models_loaded(ip, port)
    total_time = round(time.monotonic() - t_start, 1)

    if models_ok:
        log_entry("reboot_verify_ok", True, f"{host_name}: reboot via {method}, back in {boot_time}s, {count} models loaded (total {total_time}s)")
        print(f"[OK] {host_name} rebooted and verified. {count} models loaded. Total: {total_time}s")
        return 0
    else:
        log_entry("reboot_verify_fail", False, f"{host_name}: host back but no models detected after reboot")
        print(f"[FAIL] {host_name} is up but models not loaded. Check boot tasks.")
        return 1


if __name__ == "__main__":
    sys.exit(main())