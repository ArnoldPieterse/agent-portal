#!/usr/bin/env python3
"""self_probe.py - server-side endpoint probe for sandbox-blocked verification.

Usage (from host, via elev.py):
    python elev.py --shell "python memory/mechanic/self_probe.py"

Or target a specific URL:
    python elev.py --shell "python memory/mechanic/self_probe.py http://127.0.0.1:8099/api/health"

Writes results to memory/ops/selfprobe-result.json for sandbox-seat consumption.
Exit code: 0 if all checks pass, 1 if any fail.
"""
import urllib.request, json, time, sys, os

BASE = "http://127.0.0.1:8099"
OUT_PATH = os.path.join("memory", "ops", "selfprobe-result.json")

DEFAULT_CHECKS = {
    "root": "/",
    "health": "/api/health",
    "goals": "/api/goals",
}

def probe(name, url, method="GET"):
    """Probe a single URL, return result dict."""
    t0 = time.time()
    try:
        req = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(req, timeout=10) as r:
            body = r.read(4096).decode("utf-8", errors="replace")
            return {
                "status": r.status,
                "ok": 200 <= r.status < 300,
                "ms": round((time.time() - t0) * 1000, 1),
                "body_preview": body[:500],
            }
    except Exception as e:
        return {
            "status": None,
            "ok": False,
            "ms": round((time.time() - t0) * 1000, 1),
            "err": str(e)[:200],
        }

def main():
    # If a specific URL is passed as arg, probe just that
    if len(sys.argv) > 1:
        url = sys.argv[1]
        method = sys.argv[2] if len(sys.argv) > 2 else "GET"
        checks = {"target": (url, method)}
    else:
        checks = {k: (BASE + v, "GET") for k, v in DEFAULT_CHECKS.items()}

    results = {}
    t0 = time.time()
    for name, (url, method) in checks.items():
        results[name] = probe(name, url, method)

    res = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_ms": round((time.time() - t0) * 1000, 1),
        "checks": results,
        "all_ok": all(c["ok"] for c in results.values()),
    }

    # Write to shared file for sandbox seat
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(res, f, indent=2)

    # Also print to stdout
    print(json.dumps(res, indent=2))
    sys.exit(0 if res["all_ok"] else 1)

if __name__ == "__main__":
    main()
