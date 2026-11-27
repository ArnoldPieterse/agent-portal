"""
probe_winrm_r17.py - WinRM connectivity probe (r17 revision)
Forge, 2026-11-25 (created for runbook-notes.md executability)

Quick TCP probe of WinRM port across fleet hosts.
Usage: python memory/ops/probe_winrm_r17.py [--port 5985]
Exit: 0 = all reachable, 1 = any unreachable
"""
import sys, socket, json
from datetime import datetime

HOSTS = ["pale", "white", "black"]
TIMEOUT = 4

def probe(host, port):
    try:
        s = socket.create_connection((host, port), timeout=TIMEOUT)
        s.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def main():
    port = 5985
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    
    results = {h: probe(h, port) for h in HOSTS}
    all_ok = all(results.values())
    print(json.dumps({"ts": datetime.now().isoformat(), "port": port, "results": results, "all_ok": all_ok}))
    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()