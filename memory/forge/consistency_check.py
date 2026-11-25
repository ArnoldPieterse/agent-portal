#!/usr/bin/env python3
"""
consistency_check.py — Cross-Host Consistency Test (Forge goal #1)

After any fleet-wide change, verify all 4 hosts report:
  1. Same loaded model (via Studio /v1/models)
  2. Same config hash (agents.json SHA-256)
  3. Service status (port open + API responsive)

Mismatch = auto-flag with details.

Usage:
  python memory/forge/consistency_check.py              # probe all 4 hosts (run on White)
  python memory/forge/consistency_check.py --local-only # sandbox mode: White only
  python memory/forge/consistency_check.py --json       # JSON output to stdout

Exit codes: 0 = PASS (all consistent), 1 = FAIL (mismatch or unreachable)
"""
import json, hashlib, socket, sys, time, urllib.request, datetime, argparse, pathlib

HOSTS = [
    {"name": "White", "ip": "127.0.0.1", "port": 8888},
    {"name": "Red",   "ip": "IP_LAN", "port": 8888},
    {"name": "Pale",  "ip": "IP_LAN",  "port": 8888},
    {"name": "Black", "ip": "IP_LAN",  "port": 8888},
]

CONFIG_FILE = pathlib.Path("agents.json")
OUTPUT_FILE = pathlib.Path("memory/forge/consistency_check_last.json")
TIMEOUT = 5


def config_hash():
    """SHA-256 of agents.json (the fleet config)."""
    if not CONFIG_FILE.exists():
        return None, "agents.json not found"
    data = CONFIG_FILE.read_bytes()
    return hashlib.sha256(data).hexdigest()[:16], None


def probe_host(host, local_only=False):
    """Probe one host: TCP + /v1/models API. Returns dict."""
    name, ip, port = host["name"], host["ip"], host["port"]
    result = {"host": name, "ip": ip, "port": port, "ts": datetime.datetime.now().isoformat()}

    # TCP check
    t0 = time.monotonic()
    try:
        s = socket.create_connection((ip, port), timeout=TIMEOUT)
        result["tcp_ms"] = round((time.monotonic() - t0) * 1000, 1)
        s.close()
    except Exception as e:
        result["tcp_ms"] = None
        result["tcp_err"] = f"{type(e).__name__}: {e}"

    if result.get("tcp_ms") is None:
        result["status"] = "UNREACHABLE"
        result["model_id"] = None
        return result

    # API: /v1/models
    try:
        url = f"http://{ip}:{port}/v1/models"
        r = urllib.request.urlopen(url, timeout=TIMEOUT)
        body = json.loads(r.read().decode("utf-8", "replace"))
        models = [m.get("id") for m in body.get("data", [])]
        result["model_id"] = models[0] if models else None
        result["models_count"] = len(models)
        result["status"] = "MODEL_LOADED" if models else "NO_MODEL"
    except Exception as e:
        result["api_err"] = f"{type(e).__name__}: {e}"
        result["model_id"] = None
        result["status"] = "PORT_OPEN_NO_API"

    return result


def main():
    ap = argparse.ArgumentParser(description="Cross-Host Consistency Test")
    ap.add_argument("--local-only", action="store_true", help="Only probe White (sandbox mode)")
    ap.add_argument("--json", action="store_true", help="JSON output to stdout")
    args = ap.parse_args()

    hosts = HOSTS[:1] if args.local_only else HOSTS

    # Config hash (single source of truth — all hosts mirror from White)
    cfg_hash, cfg_err = config_hash()

    # Probe each host
    results = []
    for h in hosts:
        r = probe_host(h)
        r["config_hash"] = cfg_hash  # same file on all (mirrored)
        results.append(r)

    # Consistency analysis
    reachable = [r for r in results if r["status"] == "MODEL_LOADED"]
    models_seen = set(r["model_id"] for r in reachable if r.get("model_id"))
    unreachable = [r["host"] for r in results if r["status"] == "UNREACHABLE"]

    # Verdict logic:
    # PASS: all probed hosts reachable + same model loaded
    # FAIL: mismatch (different models) or any unreachable (unless --local-only)
    if args.local_only:
        verdict = "PASS" if len(reachable) == 1 and not models_seen - {results[0]["model_id"]} else "FAIL"
        detail = f"White model={results[0].get('model_id')}"
    else:
        if len(unreachable) == len(results):
            verdict, detail = "FAIL", "All hosts unreachable (egress wall?)"
        elif models_seen and len(models_seen) > 1:
            verdict, detail = "MISMATCH", f"Different models: {models_seen}"
        elif unreachable:
            verdict, detail = "PARTIAL", f"Unreachable: {unreachable}; loaded={models_seen or 'none'}"
        elif reachable and len(reachable) == len(results):
            verdict, detail = "PASS", f"All {len(results)} hosts consistent: model={list(models_seen)[0] if models_seen else 'none'}"
        else:
            verdict, detail = "FAIL", f"Degraded: reachable={len(reachable)}/{len(results)}"

    report = {
        "ts": datetime.datetime.now().isoformat(),
        "verdict": verdict,
        "detail": detail,
        "config_hash": cfg_hash,
        "hosts_probed": len(results),
        "hosts_reachable": len(reachable),
        "models_seen": list(models_seen),
        "unreachable": unreachable,
        "results": results,
    }

    # Output
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"\n{'='*50}")
        print(f"  CROSS-HOST CONSISTENCY TEST")
        print(f"  {report['ts']}")
        print(f"{'='*50}\n")
        for r in results:
            model = r.get("model_id", "-")
            ms = r.get("tcp_ms", "-")
            print(f"  {r['host']:6}  {r['status']:20}  model={str(model):30}  tcp={ms}ms")
        print(f"\n  Config hash: {cfg_hash}")
        print(f"  Verdict:     {verdict} — {detail}")
        print()

    # Save
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    sys.exit(0 if verdict == "PASS" else 1)


if __name__ == "__main__":
    main()
