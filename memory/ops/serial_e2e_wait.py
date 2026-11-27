"""
serial_e2e_wait.py - Serial E2E wait gate
Forge, 2026-11-25 (created for windows-runbook.md + staleness-audit executability)

Waits for a named condition (file existence, port open, or process alive) before
proceeding. Used as a gate in serial deployment pipelines.
Usage: python memory/ops/serial_e2e_wait.py --mode file|port|process --target <path|host:port|name> [--timeout 300]
Exit: 0 = condition met within timeout, 1 = timeout
"""
import sys, time, socket, json, os
from pathlib import Path
from datetime import datetime

def wait_file(target: str, timeout: int) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if os.path.exists(target):
            return True
        time.sleep(2)
    return False

def wait_port(target: str, timeout: int) -> bool:
    parts = target.rsplit(":", 1)
    host, port = parts[0], int(parts[1]) if len(parts) > 1 else 5985
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            s = socket.create_connection((host, port), timeout=3)
            s.close()
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            time.sleep(2)
    return False

def wait_process(target: str, timeout: int) -> bool:
    import subprocess
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            r = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {target}"], capture_output=True, text=True)
            if target.lower() in r.stdout.lower():
                return True
        except OSError:
            pass
        time.sleep(3)
    return False

def main():
    mode = "file"
    target = None
    timeout = 300
    
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--mode": i += 1; mode = args[i]
        elif args[i] == "--target": i += 1; target = args[i]
        elif args[i] == "--timeout": i += 1; timeout = int(args[i])
        i += 1
    
    if not target:
        print(json.dumps({"error": "--target required"}))
        sys.exit(1)
    
    waiters = {"file": wait_file, "port": wait_port, "process": wait_process}
    fn = waiters.get(mode)
    if not fn:
        print(json.dumps({"error": f"unknown mode: {mode}"}))
        sys.exit(1)
    
    ok = fn(target, timeout)
    print(json.dumps({"ts": datetime.now().isoformat(), "mode": mode, "target": target, "met": ok}))
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()