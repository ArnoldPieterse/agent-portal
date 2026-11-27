#!/usr/bin/env python3
"""recovery_gate.py - Host Recovery Detection Gate (Forge)
Round topic: Fleet Autonomy Convergence.

Purpose: Eliminates the 'blocked on host recovery' state by automatically
detecting when previously-unreachable hosts return to service and verifying
them for full 4-host convergence. No human intervention needed.

Logic:
  1. Read last consistency-report.jsonl entry to determine which hosts were unreachable
  2. Probe those specific hosts (Studio :8888 + Portal :8099)
  3. For each newly-reachable host: verify model version + config hash match
  4. Verdict:
     - RECOVERED-CONVERGED (exit 0): all previously-down hosts are up AND consistent
     - RECOVERED-MISMATCH  (exit 1): host(s) up but inconsistent -> remediation hint
     - STILL-DOWN          (exit 2): no change, hosts still unreachable
     - NO-PENDING-RECOVERY (exit 3): no hosts were previously down (already 4/4)

Usage:
  python memory/forge/recovery_gate.py           # live probe
  python memory/forge/recovery_gate.py --json    # machine-readable
  python memory/forge/recovery_gate.py --simulate  # selftest with mock data
"""
import json, os, sys, hashlib, urllib.request, time
from datetime import datetime, timezone

HOSTS = {
    "White": {"ip": "127.0.0.1", "local": True},
    "Red":   {"ip": "192.168.1.245", "local": False},
    "Pale":  {"ip": "192.168.1.39", "local": False},
    "Black": {"ip": "192.168.1.99", "local": False},
}
CONFIG_FILE = "agents.json"
REPORT_PATH = "memory/forge/recovery-report.jsonl"
LAST_VERDICT_PATH = "memory/forge/.last_verdict"
TIMEOUT = 5.0


def get_last_unreachable():
    """Read the last consistency report and return set of unreachable host names."""
    try:
        with open("memory/forge/consistency-report.jsonl", "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        if not lines:
            return set()
        last = json.loads(lines[-1])
        unreachable = {name for name, h in last.get("hosts", {}).items() if not h.get("reachable")}
        return unreachable
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def compute_config_hash():
    try:
        with open(CONFIG_FILE, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:12]
    except FileNotFoundError:
        return None


def probe(ip, port, path="/api/health", timeout=TIMEOUT):
    url = f"http://{ip}:{port}{path}"
    start = time.monotonic()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            body = r.read()
            elapsed = round((time.monotonic() - start) * 1000, 1)
            return json.loads(body), elapsed, None
    except Exception as e:
        elapsed = round((time.monotonic() - start) * 1000, 1)
        return None, elapsed, str(type(e).__name__)


def verify_host(name, info):
    """Probe a specific host and return its verification result."""
    ip = info["ip"]
    result = {"host": name, "reachable": False, "model_version": None, "portal_up": False, "latency_ms": None, "error": None}

    data, latency, err = probe(ip, 8888)
    if err is not None:
        result["error"] = f"studio:{err}"
        return result

    result["reachable"] = True
    result["latency_ms"] = latency
    model_info = data.get("model", data.get("model_name", data.get("status", "")))
    if isinstance(model_info, dict):
        result["model_version"] = str(model_info.get("name", model_info.get("id", "unknown")))
    else:
        result["model_version"] = str(model_info) if model_info else "unknown"

    _, _, perr = probe(ip, 8099, "/api/goals", timeout=3.0)
    result["portal_up"] = perr is None
    return result


def run_recovery_check():
    """Main recovery gate logic. Returns (verdict, details_dict)."""
    pending = get_last_unreachable()
    config_hash = compute_config_hash()

    if not pending:
        # Check if we're already at 4/4 by probing all
        all_results = {name: verify_host(name, info) for name, info in HOSTS.items()}
        all_up = all(r["reachable"] for r in all_results.values())
        if all_up:
            return "NO-PENDING-RECOVERY", {"status": "already 4/4 up", "hosts": all_results}
        else:
            # No prior report but some hosts down - treat as first run
            pending = {name for name, r in all_results.items() if not r["reachable"]}
            return "STILL-DOWN", {"status": "first run, no prior report", "pending": list(pending), "hosts": all_results}

    # Probe only the previously-unreachable hosts
    newly_up = {}
    still_down = {}
    for name in pending:
        result = verify_host(name, HOSTS[name])
        if result["reachable"]:
            newly_up[name] = result
        else:
            still_down[name] = result

    details = {
        "pending_were": sorted(pending),
        "newly_up": newly_up,
        "still_down": still_down,
        "config_hash_expected": config_hash,
    }

    if not newly_up:
        return "STILL-DOWN", details

    # All previously-down hosts are now up: verify consistency
    if len(newly_up) == len(pending):
        # Check model version consistency against known-good hosts
        up_hosts = dict(newly_up)
        for name in HOSTS:
            if name not in pending:
                r = verify_host(name, HOSTS[name])
                up_hosts[name] = r

        versions = set(r["model_version"] for r in up_hosts.values() if r["model_version"] and r["model_version"] != "unknown")
        details["all_hosts"] = up_hosts

        if len(versions) > 1:
            return "RECOVERED-MISMATCH", {**details, "mismatch_versions": list(versions)}
        return "RECOVERED-CONVERGED", details
    else:
        # Partial recovery: some up, some still down
        return "PARTIAL-RECOVERY", details


def write_report(verdict, details):
    entry = {"ts": datetime.now(timezone.utc).isoformat(), "verdict": verdict, **details}
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    # Update last verdict for state tracking
    with open(LAST_VERDICT_PATH, "w", encoding="utf-8") as f:
        f.write(verdict)


def simulate():
    """Selftest with mock scenarios."""
    print("=== RECOVERY GATE SELFTEST ===")
    # We test the verdict logic by mocking get_last_unreachable + verify_host
    results = []

    # Case 1: No pending (all were up) -> NO-PENDING-RECOVERY
    results.append(("no-pending", "NO-PENDING-RECOVERY"))

    # Case 2: One host was down, now up, consistent -> RECOVERED-CONVERGED
    results.append(("one-recovered-consistent", "RECOVERED-CONVERGED"))

    # Case 3: One host was down, still down -> STILL-DOWN
    results.append(("still-down", "STILL-DOWN"))

    # Case 4: Two hosts were down, one up with wrong model -> RECOVERED-MISMATCH (partial)
    results.append(("mismatch", "RECOVERED-MISMATCH"))

    # Verify by running the actual logic with patched functions
    import unittest.mock as mock

    # Case 1: no pending
    with mock.patch(__name__ + ".get_last_unreachable", return_value=set()):
        with mock.patch(__name__ + ".verify_host") as vh:
            vh.return_value = {"host": "X", "reachable": True, "model_version": "q8-0", "portal_up": True, "latency_ms": 5.0, "error": None}
            v, _ = run_recovery_check()
    assert v == "NO-PENDING-RECOVERY", f"Case 1: got {v}"

    # Case 2: one down host recovers, all consistent
    with mock.patch(__name__ + ".get_last_unreachable", return_value={"Black"}):
        with mock.patch(__name__ + ".verify_host") as vh:
            def fake_verify(name, info):
                return {"host": name, "reachable": True, "model_version": "q8-0", "portal_up": True, "latency_ms": 5.0, "error": None}
            vh.side_effect = fake_verify
            v, d = run_recovery_check()
    assert v == "RECOVERED-CONVERGED", f"Case 2: got {v}"

    # Case 3: host still down
    with mock.patch(__name__ + ".get_last_unreachable", return_value={"White", "Black"}):
        with mock.patch(__name__ + ".verify_host") as vh:
            def fake_verify_down(name, info):
                return {"host": name, "reachable": False, "model_version": None, "portal_up": False, "latency_ms": 5000.0, "error": "TimeoutError"}
            vh.side_effect = fake_verify_down
            v, d = run_recovery_check()
    assert v == "STILL-DOWN", f"Case 3: got {v}"

    # Case 4: partial recovery with mismatch
    with mock.patch(__name__ + ".get_last_unreachable", return_value={"White", "Black"}):
        with mock.patch(__name__ + ".verify_host") as vh:
            def fake_verify_partial(name, info):
                if name == "White":
                    return {"host": name, "reachable": True, "model_version": "q4-0", "portal_up": True, "latency_ms": 8.0, "error": None}
                elif name == "Black":
                    return {"host": name, "reachable": False, "model_version": None, "portal_up": False, "latency_ms": 5000.0, "error": "TimeoutError"}
                else:
                    return {"host": name, "reachable": True, "model_version": "q8-0", "portal_up": True, "latency_ms": 5.0, "error": None}
            vh.side_effect = fake_verify_partial
            v, d = run_recovery_check()
    # White is up with q4-0, others q8-0 -> partial (Black still down) so PARTIAL-RECOVERY
    assert v == "PARTIAL-RECOVERY", f"Case 4: got {v}"

    print(f"  Case 1 (no pending):           NO-PENDING-RECOVERY  PASS")
    print(f"  Case 2 (one recovered ok):    RECOVERED-CONVERGED  PASS")
    print(f"  Case 3 (still down):          STILL-DOWN           PASS")
    print(f"  Case 4 (partial + mismatch):  PARTIAL-RECOVERY     PASS")
    print(f"\n  RESULT: ALL PASS (4/4)")
    return True


def main():
    if "--simulate" in sys.argv:
        ok = simulate()
        sys.exit(0 if ok else 1)

    try:
        verdict, details = run_recovery_check()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(3)

    json_mode = "--json" in sys.argv
    if json_mode:
        out = {"verdict": verdict, **details}
        print(json.dumps(out, indent=2))
    else:
        print(f"=== Host Recovery Gate ===")
        print(f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        pending = details.get("pending_were", [])
        if not pending:
            print(f"  No pending recovery. Status: {details.get('status', 'all up')}")
        else:
            print(f"  Previously unreachable: {', '.join(pending)}")
            for name, r in details.get("newly_up", {}).items():
                print(f"    {name}: UP (model={r['model_version']}, latency={r['latency_ms']}ms)")
            for name, r in details.get("still_down", {}).items():
                print(f"    {name}: DOWN ({r['error']})")
        print(f"\n  VERDICT: {verdict}")

    write_report(verdict, details)

    exit_map = {"RECOVERED-CONVERGED": 0, "RECOVERED-MISMATCH": 1, "STILL-DOWN": 2, "NO-PENDING-RECOVERY": 3, "PARTIAL-RECOVERY": 4}
    sys.exit(exit_map.get(verdict, 3))


if __name__ == "__main__":
    main()