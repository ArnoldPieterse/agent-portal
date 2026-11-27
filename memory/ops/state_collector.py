"""state_collector.py - Collects fleet state snapshot from all 4 hosts.
Referenced by: data-freshness-escalation-protocol-2026-11-24.md
Writes: memory/ops/fleet-state-snapshot.json
Usage: python memory/ops/state_collector.py [--output PATH]
"""
import json, sys, pathlib
from datetime import datetime

HOSTS = {
    "White": {"ip": "IP_LAN", "port": 8888},
    "Pale": {"ip": "IP_LAN", "port": 8888},
    "Black": {"ip": "IP_LAN", "port": 8888},
    "Red": {"ip": "IP_LAN", "port": 8888},
}

def probe_host(name, cfg):
    """Probe a single host for state info."""
    import urllib.request
    url = f"http://{cfg['ip']}:{cfg['port']}/api/state"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e), "host": name}

def main():
    out_path = pathlib.Path("memory/ops/fleet-state-snapshot.json")
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            out_path = pathlib.Path(sys.argv[idx + 1])
    
    snapshot = {
        "collected_at": datetime.utcnow().isoformat() + "Z",
        "hosts": {}
    }
    
    for name, cfg in HOSTS.items():
        snapshot["hosts"][name] = probe_host(name, cfg)
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(f"Snapshot written to {out_path}")
    sys.exit(0)

if __name__ == "__main__":
    main()
