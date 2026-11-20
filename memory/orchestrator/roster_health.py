"""roster_health.py - Daily roster health check for all 8 agents.

Sends a trivial prompt to each agent via /api/chat, verifies response within timeout,
logs pass/fail + latency to memory/orchestrator/roster-health.jsonl.
Alerts (NEEDS-HUMAN) if any agent fails 2 consecutive checks.

Usage:
    python memory/orchestrator/roster_health.py           # live check
    python memory/orchestrator/roster_health.py --simulate  # no network, for testing
"""
import json
import os
import sys
import time
import hashlib
from datetime import datetime
from pathlib import Path

# Config
PORTAL_URL = "http://localhost:8099"
TIMEOUT_S = 30
LOG_FILE = Path(__file__).parent / "roster-health.jsonl"
STATE_FILE = Path(__file__).parent / ".roster_health_state.json"
AGENTS = ["orchestrator", "researcher", "builder", "verifier",
          "designer", "archivist", "scribe", "mechanic"]
TRIVIAL_PROMPT = "Reply with exactly: OK"

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def append_log(entry):
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def check_agent_live(name):
    """Send trivial prompt to agent via portal /api/chat. Returns (ok, latency_ms)."""
    import urllib.request
    payload = json.dumps({"agent": name, "message": TRIVIAL_PROMPT}).encode()
    req = urllib.request.Request(
        f"{PORTAL_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            body = json.loads(resp.read())
            latency_ms = int((time.monotonic() - t0) * 1000)
            ok = resp.status == 200 and "response" in body
            return ok, latency_ms
    except Exception as e:
        latency_ms = int((time.monotonic() - t0) * 1000)
        return False, latency_ms

def check_agent_simulate(name, fail_agents=None):
    """Simulate a check. Optionally force-fail specific agents for testing."""
    fail_agents = fail_agents or []
    if name in fail_agents:
        time.sleep(0.1)  # simulate timeout-ish delay
        return False, TIMEOUT_S * 1000
    latency = 120 + (hash(name) % 800)  # deterministic pseudo-latency 120-920ms
    time.sleep(latency / 1000.0)
    return True, latency

def run_check(simulate=False, fail_agents=None):
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    state = load_state()
    results = []
    alerts = []

    for agent in AGENTS:
        if simulate:
            ok, latency_ms = check_agent_simulate(agent, fail_agents)
        else:
            ok, latency_ms = check_agent_live(agent)

        entry = {
            "ts": ts,
            "agent": agent,
            "ok": ok,
            "latency_ms": latency_ms,
            "mode": "simulate" if simulate else "live",
        }
        results.append(entry)
        append_log(entry)

        # Track consecutive failures in state
        key = agent
        if not ok:
            state[key] = state.get(key, 0) + 1
            if state[key] >= 2 and f"{agent}:2consec" not in [a for a in alerts]:
                alerts.append(f"{agent}:2consec")
        else:
            state[key] = 0

    save_state(state)

    # Alert handling
    if alerts:
        alert_entry = {"ts": ts, "type": "NEEDS-HUMAN", "alerts": alerts, "mode": "simulate" if simulate else "live"}
        append_log(alert_entry)
        print(f"[ALERT] NEEDS-HUMAN: {', '.join(alerts)}")

    # Summary
    passed = sum(1 for r in results if r["ok"])
    total = len(results)
    status = "PASS" if passed == total else f"FAIL ({passed}/{total})"
    print(f"[roster-health] {ts} mode={'simulate' if simulate else 'live'} -> {status}")
    for r in results:
        mark = "+" if r["ok"] else "-"
        print(f"  {mark} {r['agent']:12s} {r['latency_ms']:>6d}ms")

    return 0 if passed == total else 1

def main():
    simulate = "--simulate" in sys.argv
    fail_agents = None
    if "--fail" in sys.argv:
        idx = sys.argv.index("--fail")
        fail_agents = sys.argv[idx + 1].split(",")
    rc = run_check(simulate=simulate, fail_agents=fail_agents)
    sys.exit(rc)

if __name__ == "__main__":
    main()
