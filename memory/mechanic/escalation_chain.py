"""escalation_chain.py - 3-level alert escalation for fleet operations.

Level 1 (auto-retry):   immediate, <5 min window. Retry the failed action up to 3 times with backoff.
Level 2 (agent handoff): if L1 exhausted, log a structured handoff request for another agent.
Level 3 (NEEDS-HUMAN):  if L2 not resolved within 45 min, write NEEDS-HUMAN to blockers.md.

Design: stateless per-invocation; state persisted in escalation_state.json so
repeated watchdog ticks see the same incident across runs.

Usage:
    from escalation_chain import EscalationChain
    ec = EscalationChain("portal_down", source="watchdog")
    ec.fail()  # called on each detection of the failure
    # After 3 fails -> L2 handoff logged
    # After 45 min unresolved -> L3 NEEDS-HUMAN written

Test: python memory/mechanic/escalation_chain.py --selftest
"""
import json, os, time, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, "escalation_state.json")
BLOCKERS_FILE = os.path.join(HERE, "..", "ops", "blockers.md")
LOG_FILE = os.path.join(HERE, "escalation_log.jsonl")

# Thresholds (seconds)
L1_MAX_RETRIES = 3       # retries before escalating to L2
L1_BACKOFF_S = [5, 15, 45]  # backoff between retries
L2_HANDOFF_TIMEOUT_S = 1800  # 30 min for agent handoff to resolve
L3_ESCALATE_TIMEOUT_S = 2700  # 45 min total before NEEDS-HUMAN


def _now():
    return datetime.now(timezone.utc).isoformat()


def _load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def _save_state(state):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_FILE)


def _log_event(event_type, incident_id, level, detail, **extra):
    entry = {"ts": _now(), "type": event_type, "incident": incident_id,
             "level": level, "detail": detail}
    entry.update(extra)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\\n")
    print(f"  [{event_type.upper()}] L{level} {incident_id}: {detail}")


class EscalationChain:
    """Manages a single incident through the 3-level escalation chain."""

    def __init__(self, incident_id: str, source: str = "watchdog"):
        self.incident_id = incident_id
        self.source = source
        self.state = _load_state()

    def _get_incident(self):
        return self.state.get(self.incident_id)

    def _set_incident(self, inc):
        self.state[self.incident_id] = inc
        _save_state(self.state)

    def fail(self) -> int:
        """Record a failure. Returns current level (1, 2, or 3)."""
        inc = self._get_incident()
        if inc is None:
            # New incident - start at Level 1
            inc = {
                "id": self.incident_id,
                "source": self.source,
                "level": 1,
                "fail_count": 0,
                "first_seen": _now(),
                "last_fail": _now(),
                "resolved": False,
            }
            _log_event("incident_open", self.incident_id, 1, f"new incident from {self.source}")

        inc["fail_count"] += 1
        inc["last_fail"] = _now()

        # Level 1 -> Level 2 transition
        if inc["level"] == 1 and inc["fail_count"] > L1_MAX_RETRIES:
            inc["level"] = 2
            inc["l2_started"] = _now()
            _log_event("escalate", self.incident_id, 2,
                       f"L1 exhausted ({inc['fail_count']} fails) -> agent handoff requested")

        # Level 2 -> Level 3 transition (time-based)
        if inc["level"] == 2:
            elapsed = self._elapsed(inc["l2_started"])
            if elapsed > L3_ESCALATE_TIMEOUT_S:
                inc["level"] = 3
                inc["l3_triggered"] = _now()
                self._write_needs_human(inc)
                _log_event("escalate", self.incident_id, 3,
                           f"L2 timeout ({elapsed:.0f}s > {L3_ESCALATE_TIMEOUT_S}s) -> NEEDS-HUMAN")

        self._set_incident(inc)
        return inc["level"]

    def success(self):
        """Record resolution. Clears the incident."""
        inc = self._get_incident()
        if inc is None:
            return
        inc["resolved"] = True
        inc["resolved_at"] = _now()
        _log_event("resolved", self.incident_id, inc["level"],
                   f"incident resolved at L{inc['level']} after {inc['fail_count']} fails")
        # Remove from state (keep log)
        del self.state[self.incident_id]
        _save_state(self.state)

    def status(self) -> dict:
        """Return current status for this incident."""
        inc = self._get_incident()
        if inc is None:
            return {"active": False}
        elapsed = self._elapsed(inc["first_seen"])
        return {
            "active": not inc["resolved"],
            "level": inc["level"],
            "fail_count": inc["fail_count"],
            "age_s": elapsed,
        }

    def _elapsed(self, iso_ts: str) -> float:
        from datetime import datetime as dt
        t = dt.fromisoformat(iso_ts)
        return (datetime.now(timezone.utc) - t).total_seconds()

    def _write_needs_human(self, inc):
        """Append NEEDS-HUMAN entry to blockers.md."""
        entry = f"""
## [NEEDS-HUMAN {_now()}] Escalation L3: {self.incident_id}
**Source:** {self.source}
**Level 1 (auto-retry):** {inc['fail_count']} failures, all retries exhausted.
**Level 2 (agent handoff):** initiated at {inc.get('l2_started', 'n/a')}, not resolved within {L3_ESCALATE_TIMEOUT_S}s.
**Unblock step:** investigate and resolve `{self.incident_id}` manually; then run `python memory/mechanic/escalation_chain.py --resolve {self.incident_id}` to close.
"""
        with open(BLOCKERS_FILE, "a") as f:
            f.write(entry)


def resolve_incident(incident_id: str):
    """External resolution (called after human fixes the issue)."""
    ec = EscalationChain(incident_id)
    ec.success()


def selftest():
    """Run a simulated escalation cycle to verify all 3 levels fire correctly."""
    import tempfile, shutil

    # Use temp files for test isolation
    global STATE_FILE, BLOCKERS_FILE, LOG_FILE
    tmpdir = tempfile.mkdtemp(prefix="esc_test_")
    orig_state, orig_blockers, orig_log = STATE_FILE, BLOCKERS_FILE, LOG_FILE
    STATE_FILE = os.path.join(tmpdir, "state.json")
    BLOCKERS_FILE = os.path.join(tmpdir, "blockers.md")
    LOG_FILE = os.path.join(tmpdir, "log.jsonl")

    results = []
    try:
        # Test 1: New incident starts at Level 1
        ec = EscalationChain("test_portal_down", source="selftest")
        level = ec.fail()  # fail_count=1
        results.append(("L1 new incident -> level 1", level == 1))

        # Test 2: Fails accumulate, still L1 under threshold (3 max)
        ec = EscalationChain("test_portal_down")
        level = ec.fail()  # fail_count=2
        results.append(("L1 second fail -> still level 1", level == 1))

        # Test 3: 3rd fail - still at threshold, not yet exceeded
        ec = EscalationChain("test_portal_down")
        level = ec.fail()  # fail_count=3, NOT > 3
        results.append(("L1 third fail -> still level 1", level == 1))

        # Test 4: 4th fail - exceeds L1_MAX_RETRIES -> escalates to L2
        ec = EscalationChain("test_portal_down")
        level = ec.fail()  # fail_count=4, > 3 -> L2
        results.append(("L1->L2 after 4th fail", level == 2))

        # Test 5: Simulate time passage for L3 (manipulate state)
        state = _load_state()
        inc = state["test_portal_down"]
        # Set l2_started to 50 min ago
        from datetime import timedelta
        old_ts = (datetime.now(timezone.utc) - timedelta(seconds=3000)).isoformat()
        inc["l2_started"] = old_ts
        _save_state(state)

        ec = EscalationChain("test_portal_down")
        level = ec.fail()  # fail_count=5, level already 2, elapsed > 45min -> L3
        results.append(("L2->L3 after 45min timeout", level == 3))

        # Test 6: NEEDS-HUMAN written to blockers file
        blockers_content = open(BLOCKERS_FILE).read() if os.path.exists(BLOCKERS_FILE) else ""
        results.append(("NEEDS-HUMAN in blockers.md", "NEEDS-HUMAN" in blockers_content and "test_portal_down" in blockers_content))

        # Test 7: Resolution clears the incident
        ec = EscalationChain("test_portal_down")
        ec.success()
        status = ec.status()
        results.append(("Resolution clears state", status["active"] == False))

        # Test 8: Log file has entries for all levels
        log_lines = [l for l in open(LOG_FILE).read().strip().split("\\n") if l.strip()] if os.path.exists(LOG_FILE) else []
        types = [json.loads(l)["type"] for l in log_lines]
        results.append(("Log has incident_open + escalate + resolved",
                        "incident_open" in types and "escalate" in types and "resolved" in types))

    finally:
        STATE_FILE, BLOCKERS_FILE, LOG_FILE = orig_state, orig_blockers, orig_log
        shutil.rmtree(tmpdir, ignore_errors=True)

    # Report
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"\\n{'='*50}")
    print(f"ESCALATION CHAIN SELFTEST: {passed}/{total} PASS")
    for name, ok in results:
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {name}")
    print(f"{'='*50}")
    return passed == total


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    elif "--resolve" in sys.argv:
        idx = sys.argv.index("--resolve")
        if idx + 1 < len(sys.argv):
            resolve_incident(sys.argv[idx + 1])
            print(f"Resolved incident: {sys.argv[idx+1]}")
        else:
            print("Usage: --resolve <incident_id>")
            sys.exit(1)
    else:
        print(__doc__)
