#!/usr/bin/env python3
"""
convergence_watch.py - Fleet Convergence State-Transition Watcher (Forge)
Round topic: Fleet Autonomy Convergence.

Runs convergence_gate.py --json, compares the verdict to the last known state
(persisted in memory/forge/.last_verdict), and emits an alert ONLY on a
state transition (e.g. CONVERGED -> DEGRADED). Steady-state re-runs are silent
(exit 0, no output beyond "no change").

This prevents alert fatigue: instead of logging every green pass, it flags
the moment the fleet loses or regains convergence.

Modes:
  (default)     run gate live, compare to last state, alert on transition
  --selftest    deterministic test of transition logic (no subprocess)
  --json        machine-readable output
  --reset       clear .last_verdict and exit 0 (use after a known-good deploy)

Alerts are appended to memory/forge/convergence-alerts.jsonl.
Exit codes:
  0 = no change OR selftest pass
  1 = DIVERGED or ERROR detected (regression alert)
  2 = DEGRADED detected (warning alert, e.g. hosts went down)
"""
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, ".last_verdict")
ALERTS_PATH = os.path.join(HERE, "convergence-alerts.jsonl")

# Transition matrix: (prev, new) -> severity
# Only transitions that matter get an alert. Steady-state = silent.
SEVERITY = {
    ("CONVERGED", "DEGRADED"): 2,   # hosts went down / warn appeared
    ("CONVERGED", "DIVERGED"): 1,   # a gate failed - regression
    ("CONVERGED", "ERROR"):    1,   # a gate crashed
    ("DEGRADED", "DIVERGED"): 1,    # got worse
    ("DEGRADED", "ERROR"):    1,    # got worse
    ("DIVERGED", "CONVERGED"): 0,   # recovered! (info)
    ("DIVERGED", "DEGRADED"): 0,    # improved but not full
    ("ERROR", "CONVERGED"):   0,    # recovered
    ("ERROR", "DEGRADED"):    0,    # partial recovery
}


def read_state():
    """Return last known verdict or None."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return f.read().strip()
    return None


def write_state(verdict):
    with open(STATE_FILE, "w") as f:
        f.write(verdict)


def get_severity(prev, new):
    """Return exit code for a transition; -1 means no alert needed."""
    if prev is None:
        return 0  # first run, just record state
    if prev == new:
        return -1  # steady-state, silent
    return SEVERITY.get((prev, new), 0)


def selftest():
    """Test transition logic without subprocess."""
    cases = [
        # (prev, new, expected_severity_or_-1)
        (None, "CONVERGED", 0),           # first run: record, no alert
        ("CONVERGED", "CONVERGED", -1),   # steady: silent
        ("CONVERGED", "DEGRADED", 2),     # hosts down: warn
        ("CONVERGED", "DIVERGED", 1),     # gate failed: regression
        ("CONVERGED", "ERROR", 1),        # crash: regression
        ("DEGRADED", "DEGRADED", -1),     # steady degraded: silent
        ("DEGRADED", "DIVERGED", 1),      # worse
        ("DIVERGED", "CONVERGED", 0),     # recovered: info
        ("ERROR", "CONVERGED", 0),        # recovered: info
        ("DEGRADED", "CONVERGED", 0),     # recovered to full: info
    ]

    passed = 0
    total = len(cases)
    print("=== convergence_watch --selftest ===")
    for prev, new, expected in cases:
        got = get_severity(prev, new)
        ok = (got == expected)
        passed += ok
        label = f"{prev or 'NONE'} -> {new}"
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}: got {got} want {expected}")
    print(f"RESULT: {'ALL PASS' if passed == total else 'FAILURES PRESENT'} "
          f"({passed}/{total})")
    return 0 if passed == total else 1


def main():
    args = sys.argv[1:]

    if "--selftest" in args:
        sys.exit(selftest())

    if "--reset" in args:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
        print("State reset.")
        sys.exit(0)

    json_mode = "--json" in args

    # Run the convergence gate
    import subprocess
    cmd = [sys.executable, os.path.join(HERE, "convergence_gate.py"), "--json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        verdict = "ERROR"
        detail = "convergence_gate TIMEOUT"
    except Exception as e:
        verdict = "ERROR"
        detail = f"SPAWN-ERR {e}"
    else:
        try:
            report = json.loads(proc.stdout)
            verdict = report["verdict"]
            detail = json.dumps({k: v["status"] for k, v in report.get("gates", {}).items()})
        except (json.JSONDecodeError, KeyError):
            verdict = "ERROR"
            detail = f"unparseable gate output (exit {proc.returncode})"

    prev = read_state()
    severity = get_severity(prev, verdict)
    write_state(verdict)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if severity == -1:
        # Steady-state: silent
        if not json_mode:
            print(f"[watch] {verdict} (no change, steady)")
        sys.exit(0)

    # State transition or first run: record alert
    alert = {
        "ts": ts,
        "prev": prev,
        "new": verdict,
        "severity": severity,
        "detail": detail[:300],
    }
    os.makedirs(os.path.dirname(ALERTS_PATH), exist_ok=True)
    with open(ALERTS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(alert) + "\n")

    if json_mode:
        print(json.dumps(alert, indent=2))
    else:
        arrow = f"{prev or 'NONE'} -> {verdict}"
        tag = "ALERT" if severity > 0 else "INFO"
        print(f"[watch:{tag}] {arrow}")
        print(f"  detail: {detail[:200]}")

    sys.exit(severity)


if __name__ == "__main__":
    main()
