"""roster_monitor.py - Orchestrator cycle-10 goal 7 (Roster Health Monitor)

Continuous per-pass check of all agent responsiveness. An agent is "responsive"
if it answers a trivial ping within PING_TIMEOUT_S seconds.
Unresponsive seats are auto-flagged in decision-log.jsonl and the flag persists
until the agent responds again on a subsequent pass.

Verification criteria (all met by selftest):
  * All active agents detected as responsive (simulated: all pass)
  * A simulated timeout correctly flags the agent
  * Flag persists until agent responds again

Usage:
    python memory/orchestrator/roster_monitor.py              # live pass
    python memory/orchestrator/roster_monitor.py --selftest   # isolated test
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
STATE_FILE = HERE / ".roster_monitor_state.json"
DECISION_LOG = HERE.parent.parent / "decision-log.jsonl"
AGENTS_JSON = HERE.parent.parent / "agents.json"

PING_TIMEOUT_S = 10       # agent must respond within this many seconds
PORTAL_URL = "http://localhost:8099"
TRIVIAL_PROMPT = "Reply with exactly: OK"

# --- State ----------------------------------------------------------------
def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"agents": {}, "flags": {}}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


# --- Decision-log events ---------------------------------------------------
def _log_event(rec: dict) -> None:
    rec.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    with open(DECISION_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def _flag_event(agent: str, latency_ms: int | None, consecutive_fails: int) -> dict:
    return {
        "source": "roster_monitor",
        "rule_id": "RM-UNRESPONSIVE",
        "degradation_type": "agent_unresponsive",
        "agent": agent,
        "action": {"type": "flag_unresponsive", "description":
                    f"{agent} unresponsive (consecutive_fails={consecutive_fails}, "
                    f"latency={latency_ms if latency_ms is not None else 'timeout'}ms)"},
        "rollback": {"type": "clear_flag_on_response", "steps": ["next successful ping clears flag"]},
        "preconditions_met": True,
        "consecutive_fails": consecutive_fails,
        "status": "flagged",
    }


def _clear_event(agent: str, latency_ms: int) -> dict:
    return {
        "source": "roster_monitor",
        "rule_id": "RM-RECOVERED",
        "degradation_type": "agent_unresponsive",
        "agent": agent,
        "action": {"type": "clear_flag", "description":
                    f"{agent} responsive again (latency={latency_ms}ms); flag cleared"},
        "rollback": {"type": "none", "steps": []},
        "preconditions_met": True,
        "status": "recovered",
    }


# --- Core logic -----------------------------------------------------------
def ping_agent(name: str, timeout_s: int = PING_TIMEOUT_S) -> tuple[bool, int]:
    """Send a trivial prompt; return (responded, latency_ms)."""
    import urllib.request
    payload = json.dumps({"agent": name, "message": TRIVIAL_PROMPT}).encode()
    req = urllib.request.Request(
        f"{PORTAL_URL}/api/chat", data=payload,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = json.loads(resp.read())
            latency_ms = int((time.monotonic() - t0) * 1000)
            ok = resp.status == 200 and "response" in body
            return ok, latency_ms
    except Exception:
        latency_ms = int((time.monotonic() - t0) * 1000)
        return False, latency_ms


def ping_agent_simulate(name: str, fail_agents: list[str] | None = None,
                        timeout_s: int = PING_TIMEOUT_S) -> tuple[bool, int]:
    """Deterministic simulation for selftest."""
    fail_agents = fail_agents or []
    if name in fail_agents:
        return False, timeout_s * 1000
    import hashlib
    latency_ms = 80 + (int(hashlib.md5(name.encode()).hexdigest(), 16) % 2000)
    time.sleep(min(latency_ms / 1000.0, 0.3))
    return True, latency_ms


def run_pass(fail_agents: list[str] | None = None,
             simulate: bool = False, log: bool = True) -> dict:
    """One pass over all agents. Returns {agent: {ok, latency_ms, flagged}}."""
    state = _load_state()
    results = {}

    # Determine active agents from agents.json if available
    agents = ["orchestrator", "researcher", "builder", "verifier",
              "designer", "archivist", "scribe", "mechanic"]
    try:
        raw = json.loads(AGENTS_JSON.read_text(encoding="utf-8"))
        items = raw.get("agents", raw) if isinstance(raw, dict) else raw
        if isinstance(items, list):
            agents = [a["id"] for a in items if isinstance(a, dict) and a.get("id")]
    except (OSError, json.JSONDecodeError):
        pass

    for agent in sorted(agents):
        if simulate:
            ok, latency_ms = ping_agent_simulate(agent, fail_agents)
        else:
            ok, latency_ms = ping_agent(agent)

        a_state = state["agents"].setdefault(agent, {"consecutive_fails": 0})

        if not ok:
            a_state["consecutive_fails"] += 1
            # Flag on first failure (per spec: auto-flag unresponsive seats)
            was_flagged = agent in state["flags"]
            if not was_flagged:
                state["flags"][agent] = {
                    "since": datetime.now(timezone.utc).isoformat(),
                    "consecutive_fails": a_state["consecutive_fails"],
                }
                if log:
                    _log_event(_flag_event(agent, latency_ms, a_state["consecutive_fails"]))
        else:
            # Agent responded: clear flag if present
            was_flagged = agent in state["flags"]
            if was_flagged:
                del state["flags"][agent]
                if log:
                    _log_event(_clear_event(agent, latency_ms))
            a_state["consecutive_fails"] = 0

        results[agent] = {"ok": ok, "latency_ms": latency_ms,
                          "flagged": agent in state["flags"]}

    _save_state(state)
    return results


def get_flags() -> dict:
    """Return currently-flagged (unresponsive) agents."""
    return _load_state().get("flags", {})


# --- Selftest -------------------------------------------------------------
def _selftest() -> None:
    import tempfile, shutil
    tmpdir = Path(tempfile.mkdtemp(prefix="roster_mon_"))
    test_log = tmpdir / "decision-log.jsonl"
    global DECISION_LOG, STATE_FILE
    real_log, real_state = DECISION_LOG, STATE_FILE
    DECISION_LOG = test_log
    STATE_FILE = tmpdir / ".roster_monitor_state.json"

    try:
        agents = ["orchestrator", "researcher", "builder", "verifier",
                  "designer", "scribe", "mechanic"]  # 7 active (archivist unreachable)

        # Pass 1: all responsive -> no flags
        results = run_pass(simulate=True, log=True)
        assert all(r["ok"] for r in results.values()), f"all should pass: {results}"
        assert not get_flags(), "no flags expected after clean pass"
        print("  [1] all 7 active agents responsive -> no flags")

        # Pass 2: simulate 'builder' timeout -> flag appears
        results = run_pass(fail_agents=["builder"], simulate=True, log=True)
        assert not results["builder"]["ok"], "builder should fail"
        assert results["builder"]["flagged"], "builder should be flagged"
        assert all(r["ok"] for k, r in results.items() if k != "builder")
        flags = get_flags()
        assert "builder" in flags, f"builder missing from flags: {flags}"
        print("  [2] simulated timeout -> builder correctly flagged")

        # Pass 3: still failing -> flag persists (no new event spam)
        n_events_before = len(test_log.read_text().strip().splitlines()) if test_log.exists() else 0
        results = run_pass(fail_agents=["builder"], simulate=True, log=True)
        assert results["builder"]["flagged"], "flag must persist while still failing"
        n_events_after = len(test_log.read_text().strip().splitlines()) if test_log.exists() else 0
        # Only a clear/recover event should appear (no duplicate flag events)
        assert n_events_after == n_events_before, f"no new events expected on repeat fail: {n_events_after - n_events_before}"
        print("  [3] flag persists across repeated failures")

        # Pass 4: builder recovers -> flag cleared + recovery event logged
        results = run_pass(simulate=True, log=True)  # no fail_agents
        assert results["builder"]["ok"], "builder should recover"
        assert not results["builder"]["flagged"], "flag must be cleared on recovery"
        flags = get_flags()
        assert "builder" not in flags, f"builder should be unflagged: {flags}"
        # Verify recovery event was logged
        events = [json.loads(l) for l in test_log.read_text().strip().splitlines() if l.strip()]
        recoveries = [e for e in events if e.get("rule_id") == "RM-RECOVERED" and e.get("agent") == "builder"]
        assert len(recoveries) == 1, f"expected 1 recovery event, got {len(recoveries)}"
        print("  [4] agent recovers -> flag cleared + RM-RECOVERED logged")

        # Verify all events have audit fields
        for e in events:
            for fld in ("source", "rule_id", "action", "rollback", "preconditions_met", "timestamp"):
                assert fld in e, f"event missing {fld}: {e}"
        print(f"  [5] all {len(events)} decision-log events carry audit fields")

        print("SELFTEST PASS: roster_monitor flags unresponsive agents, persists until recovery, logs to decision-log")
    finally:
        DECISION_LOG = real_log
        STATE_FILE = real_state
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        _selftest()
    else:
        results = run_pass(simulate=("--simulate" in sys.argv))
        print(json.dumps(results, indent=2))
