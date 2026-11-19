#!/usr/bin/env python3
"""Self-probe for Mechanic Goal 8 (Fleet Status API).

Run ON WHITE (the portal host) to generate live-HTTP acceptance evidence.
The sandbox seat on Red cannot reach :8099 (WinError 10013 / LAN timeout),
so this script runs server-side and writes results to a file the sandbox reads.

Usage (from White, any shell with egress):
    python memory/mechanic/selfprobe_fleet.py

Output: memory/ops/selfprobe-result.json
Acceptance: all_ok == true + fleet_status check has status 200.
"""
import json, time, urllib.request, os, sys

BASE = "http://127.0.0.1:8099"
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "ops", "selfprobe-result.json")

CHECKS = {
    "root": "/",
    "health": "/api/health",
    "goals": "/api/goals",
    "fleet_status": "/api/fleet/status",
}

def probe():
    out = {}
    t0 = time.time()
    for name, path in CHECKS.items():
        try:
            with urllib.request.urlopen(BASE + path, timeout=10) as r:
                body = r.read().decode("utf-8", errors="replace")
                entry = {"status": r.status, "ok": 200 <= r.status < 300, "bytes": len(body)}
                # For fleet_status, include the parsed JSON for verification
                if name == "fleet_status":
                    try:
                        data = json.loads(body)
                        entry["hosts"] = list(data.get("hosts", {}).keys()) if isinstance(data.get("hosts"), dict) else [h.get("host") for h in data.get("hosts", [])]
                        entry["overall_health"] = data.get("overall_health") or data.get("health")
                    except json.JSONDecodeError:
                        entry["json_error"] = True
                out[name] = entry
        except Exception as e:
            out[name] = {"status": None, "ok": False, "err": str(e)[:200]}
    result = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": os.environ.get("COMPUTERNAME", "unknown"),
        "ms": round((time.time() - t0) * 1000),
        "checks": out,
        "all_ok": all(c["ok"] for c in out.values()),
    }
    return result

def main():
    res = probe()
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(res, f, indent=2)
    print(json.dumps(res, indent=2))
    if not res["all_ok"]:
        print("\nWARNING: not all checks passed", file=sys.stderr)
        sys.exit(1)
    print(f"\nAll checks OK. Evidence written to {os.path.normpath(OUT_PATH)}")

if __name__ == "__main__":
    main()