"""lan_probe.py - Quick LAN reachability probe for all 4 fleet hosts.
Referenced by: runbook-notes.md
Usage: python memory/ops/lan_probe.py [--timeout SECS]
Exit codes: 0=all reachable, 1=some unreachable
"""
import socket, sys, time

HOSTS = {
    "White": ("IP_LAN", 8888),
    "Pale": ("IP_LAN", 8888),
    "Black": ("IP_LAN", 8888),
    "Red": ("IP_LAN", 8888),
}

def probe(ip, port, timeout):
    start = time.monotonic()
    try:
        s = socket.create_connection((ip, port), timeout=timeout)
        s.close()
        return True, (time.monotonic() - start) * 1000
    except Exception:
        return False, None

def main():
    timeout = 3.0
    if "--timeout" in sys.argv:
        idx = sys.argv.index("--timeout")
        if idx + 1 < len(sys.argv):
            timeout = float(sys.argv[idx + 1])
    
    all_ok = True
    print(f"{'Host':<8} {'IP':<16} {'Port':<6} {'Status':<8} {'Latency'}")
    print("-" * 50)
    
    for name, (ip, port) in HOSTS.items():
        ok, latency = probe(ip, port, timeout)
        status = "OK" if ok else "FAIL"
        lat_str = f"{latency:.0f}ms" if latency else "-"
        print(f"{name:<8} {ip:<16} {port:<6} {status:<8} {lat_str}")
        if not ok:
            all_ok = False
    
    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()
