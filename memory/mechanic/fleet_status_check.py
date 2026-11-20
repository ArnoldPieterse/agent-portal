"""
fleet_status_check.py - One-command full fleet status check (Runbook step A)
Part of Mechanic Goal 10: Runbook Automation (top-5)

Usage: python memory/mechanic/fleet_status_check.py [--json] [--timeout 5]

Idempotent. Logs to memory/mechanic/runbook-executions.jsonl. Runtime <60s.
"""
import json, socket, sys, time, pathlib
from datetime import datetime, timezone

# Fleet host config (host: {name, ip, ports_to_check})
FLEET = {
    "white": {"ip": "127.0.0.1", "ports": [8099, 8888], "label": "White (local)"},
    "pale":  {"ip": "IP_PALE", "ports": [8888, 445], "label": "Pale"},
    "black": {"ip": "IP_BLACK", "ports": [8888, 445], "label": "Black"},
    "red":   {"ip": "IP_RED", "ports": [8888, 445], "label": "Red"},
}

LOG_PATH = pathlib.Path("memory/mechanic/runbook-executions.jsonl")
TIMEOUT_DEFAULT = 5  # seconds per probe


def probe_host(ip: str, ports: list, timeout: float) -> dict:
    """TCP-probe each port; return {port: state + latency}"""
    results = {}
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            t0 = time.monotonic()
            rc = sock.connect_ex((ip, port))
            elapsed = (time.monotonic() - t0) * 1000
            if rc == 0:
                results[str(port)] = {"state": "open", "ms": round(elapsed, 1)}
            else:
                results[str(port)] = {"state": "closed(%d)" % rc, "ms": round(elapsed, 1)}
            sock.close()
        except socket.timeout:
            results[str(port)] = {"state": "timeout", "ms": timeout * 1000}
        except Exception as e:
            results[str(port)] = {"state": "error(%s)" % e.__class__.__name__, "ms": None}
    return results


def run_check(timeout: float = TIMEOUT_DEFAULT) -> dict:
    """Full fleet status check. Returns structured result dict."""
    t_start = time.monotonic()
    hosts = {}
    for name, cfg in FLEET.items():
        ports_result = probe_host(cfg["ip"], cfg["ports"], timeout)
        all_open = all(v["state"] == "open" for v in ports_result.values())
        any_open = any(v["state"] == "open" for v in ports_result.values())
        if all_open:
            status = "UP"
        elif any_open:
            status = "DEGRADED"
        else:
            status = "DOWN"
        hosts[name] = {
            "label": cfg["label"],
            "ip": cfg["ip"],
            "status": status,
            "ports": ports_result,
        }
    total_s = round(time.monotonic() - t_start, 2)
    if all(h["status"] == "UP" for h in hosts.values()):
        overall = "HEALTHY"
    elif any(h["status"] != "DOWN" for h in hosts.values()):
        overall = "DEGRADED"
    else:
        overall = "CRITICAL"

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "script": "fleet_status_check.py",
        "overall": overall,
        "hosts": hosts,
        "total_seconds": total_s,
        "within_budget": total_s < 60,
    }


def log_execution(result: dict):
    """Append to runbook-executions.jsonl (idempotent-safe: just appends)."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(result) + "\n")


def main():
    timeout = TIMEOUT_DEFAULT
    output_json = False
    args = sys.argv[1:]
    if "--timeout" in args:
        i = args.index("--timeout")
        timeout = float(args[i + 1])
    if "--json" in args:
        output_json = True

    result = run_check(timeout)
    log_execution(result)

    if output_json:
        print(json.dumps(result, indent=2))
    else:
        print("=" * 50)
        print(" FLEET STATUS CHECK  %s" % result["timestamp"])
        print(" Overall: %s  (%ss)" % (result["overall"], result["total_seconds"]))
        print("=" * 50)
        for name, h in result["hosts"].items():
            icon = {"UP": "[OK]", "DEGRADED": "[WARN]", "DOWN": "[FAIL]"}[h["status"]]
            port_str = " ".join(
                "%s=%s" % (p, "OK" if v["state"] == "open" else "FAIL")
                for p, v in h["ports"].items()
            )
            print(" %s %-20s [%-8s]  %s" % (icon, h["label"], h["status"], port_str))
        print("=" * 50)
        if not result["within_budget"]:
            print(" WARNING: exceeded 60s budget!")

    # Exit code: 0=healthy, 1=degraded, 2=critical
    sys.exit({"HEALTHY": 0, "DEGRADED": 1, "CRITICAL": 2}[result["overall"]])


if __name__ == "__main__":
    main()
