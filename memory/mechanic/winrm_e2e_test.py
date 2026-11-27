"""
winrm_e2e_test.py - WinRM end-to-end connectivity test
Mechanic, 2026-11-25 (stub created by Forge for runbook executability)

Tests WinRM chain: local -> each remote host. Reports per-host status.
Usage: python memory/mechanic/winrm_e2e_test.py [--hosts h1,h2,h3]
Exit: 0 = all reachable, 1 = any unreachable
"""
import sys, json, socket
from pathlib import Path
from datetime import datetime

DEFAULT_HOSTS = ["pale", "white", "black"]
WINRM_PORT = 5985
TIMEOUT = 5

def probe(host: str, port: int = WINRM_PORT) -> dict:
    result = {"host": host, "reachable": False, "latency_ms": None, "error": None}
    try:
        import time
        t0 = time.monotonic()
        sock = socket.create_connection((host, port), timeout=TIMEOUT)
        result["latency_ms"] = round((time.monotonic() - t0) * 1000, 1)
        sock.close()
        result["reachable"] = True
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        result["error"] = str(e)
    return result

def main():
    hosts = DEFAULT_HOSTS
    if "--hosts" in sys.argv:
        idx = sys.argv.index("--hosts")
        hosts = sys.argv[idx + 1].split(",")
    
    results = [probe(h) for h in hosts]
    all_ok = all(r["reachable"] for r in results)
    
    print(json.dumps({"timestamp": datetime.now().isoformat(), "results": results, "all_ok": all_ok}, indent=2))
    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()