#!/usr/bin/env python3
"""
convergence_gate.py - Unified Fleet Autonomy Convergence Gate (Forge)
Round topic: Fleet Autonomy Convergence.

Chains the four verified Forge gate tools into ONE autonomy decision:
  - consistency_check.py   (cross-host model/config/service parity)
  - drift_detect.py        (gate-pipeline silent-degradation detector)
  - runbook_audit.py       (runbook executability audit)
  - stealth_smoke_gate.py  (WF1-3 pre-deploy smoke gate)

Each child exit code is mapped to a per-gate status, then combined into a
single fleet verdict with ONE process exit code:

    CONVERGED = 0   all gates OK
    DEGRADED  = 2   at least one WARN (e.g. hosts unreachable), no FAIL/ERROR
    DIVERGED  = 1   at least one gate FAILed
    ERROR     = 3   a gate crashed / returned an unmapped code

Modes:
  (default)        live: run each tool in its real mode
  --simulate       run each tool in its selftest/simulate mode (deterministic)
  --selftest       pure logic test of the verdict-combination + exit mapping
                   (no subprocesses, no fleet dependency) - always available
  --json           machine-readable report on stdout

Report: appends one JSON line to memory/forge/convergence-report.jsonl.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT_PATH = os.path.join(HERE, "convergence-report.jsonl")

# Per-gate config: name -> (script, mode_flags for live, mode_flags for simulate)
# A script with no simulate flag simply re-runs in live mode under --simulate.
GATES = {
    "consistency":  {"script": "consistency_check.py",
                     "live": ["--json"], "sim": ["--simulate"]},
    "drift":        {"script": "drift_detect.py",
                     "live": [], "sim": ["--simulate"]},
    "runbook":      {"script": "runbook_audit.py",
                     "live": ["--json"], "sim": None},  # deterministic scan
    "smoke":        {"script": "stealth_smoke_gate.py",
                     "live": [], "sim": ["--selftest"]},
}

# Map a child exit code -> per-gate status. Unknown codes are ERROR.
EXIT_TO_STATUS = {
    # consistency_check: 0=PASS, 2=WARN(unreachable), 1=CRIT, 3=error
    "consistency": {0: "OK", 2: "WARN", 1: "FAIL", 3: "ERROR"},
    # drift_detect: 0=clean, 1=DRIFT, 2=error
    "drift":       {0: "OK", 1: "FAIL", 2: "ERROR"},
    # runbook_audit: 0=no gaps, 1=gaps
    "runbook":     {0: "OK", 1: "FAIL"},
    # stealth_smoke_gate: 0=GATE PASS, 1=GATE FAIL
    "smoke":       {0: "OK", 1: "FAIL"},
}

STATUS_RANK = {"OK": 0, "WARN": 1, "FAIL": 2, "ERROR": 3}


def map_status(gate, exit_code):
    """Map a child exit code to a per-gate status (unmapped -> ERROR)."""
    table = EXIT_TO_STATUS.get(gate, {})
    return table.get(exit_code, "ERROR")


def combine_verdicts(statuses):
    """Pure combination: dict gate->status -> (verdict, exit_code).

    Priority ERROR > FAIL > WARN > OK. Deterministic and unit-testable.
    """
    if not statuses:
        return ("ERROR", 3)
    worst = max(statuses.values(), key=lambda s: STATUS_RANK[s])
    if worst == "ERROR":
        return ("ERROR", 3)
    if worst == "FAIL":
        return ("DIVERGED", 1)
    if worst == "WARN":
        return ("DEGRADED", 2)
    return ("CONVERGED", 0)


def run_gate(name, cfg, simulate):
    """Run one gate as a subprocess; return (status, exit_code, tail)."""
    script = os.path.join(HERE, cfg["script"])
    mode = "sim" if simulate else "live"
    flags = cfg.get(mode) or []
    cmd = [sys.executable, script] + flags
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        code = proc.returncode
        tail = (proc.stdout or "").strip().splitlines()
        tail = tail[-1] if tail else ""
    except subprocess.TimeoutExpired:
        return ("ERROR", -1, "TIMEOUT")
    except Exception as e:  # missing script / spawn failure
        return ("ERROR", -2, f"SPAWN-ERR {e}")
    return (map_status(name, code), code, tail)


def selftest():
    """Deterministic logic test of map_status + combine_verdicts. No subprocess."""
    cases = [
        # (description, statuses, expected_verdict, expected_exit)
        ("all OK", {"consistency": "OK", "drift": "OK",
                    "runbook": "OK", "smoke": "OK"}, "CONVERGED", 0),
        ("one WARN (hosts down)", {"consistency": "WARN", "drift": "OK",
                    "runbook": "OK", "smoke": "OK"}, "DEGRADED", 2),
        ("drift FAIL beats WARN", {"consistency": "WARN", "drift": "FAIL",
                    "runbook": "OK", "smoke": "OK"}, "DIVERGED", 1),
        ("ERROR beats FAIL", {"consistency": "ERROR", "drift": "FAIL",
                    "runbook": "OK", "smoke": "OK"}, "ERROR", 3),
        ("smoke FAIL", {"consistency": "OK", "drift": "OK",
                    "runbook": "OK", "smoke": "FAIL"}, "DIVERGED", 1),
        ("empty -> ERROR", {}, "ERROR", 3),
    ]
    # exit-code mapping spot checks
    map_cases = [
        ("consistency", 0, "OK"), ("consistency", 2, "WARN"),
        ("consistency", 1, "FAIL"), ("consistency", 99, "ERROR"),
        ("drift", 0, "OK"), ("drift", 1, "FAIL"), ("drift", 2, "ERROR"),
        ("runbook", 0, "OK"), ("runbook", 1, "FAIL"),
        ("smoke", 0, "OK"), ("smoke", 1, "FAIL"), ("smoke", 7, "ERROR"),
    ]
    passed = 0
    total = len(cases) + len(map_cases)
    print("=== convergence_gate --selftest ===")
    for desc, st, ev, ee in cases:
        v, ex = combine_verdicts(st)
        ok = (v == ev and ex == ee)
        passed += ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {desc}: got ({v},{ex}) want ({ev},{ee})")
    for gate, code, want in map_cases:
        got = map_status(gate, code)
        ok = (got == want)
        passed += ok
        print(f"  [{'PASS' if ok else 'FAIL'}] map {gate} exit {code}: got {got} want {want}")
    print(f"RESULT: {'ALL PASS' if passed == total else 'FAILURES PRESENT'} "
          f"({passed}/{total})")
    return 0 if passed == total else 1


def main():
    args = sys.argv[1:]
    if "--selftest" in args:
        sys.exit(selftest())

    simulate = "--simulate" in args
    json_mode = "--json" in args
    mode_label = "SIMULATE" if simulate else "LIVE"

    statuses, codes, details = {}, {}, {}
    for name, cfg in GATES.items():
        status, code, tail = run_gate(name, cfg, simulate)
        statuses[name] = status
        codes[name] = code
        details[name] = {"status": status, "exit": code, "note": tail[:300]}

    verdict, exit_code = combine_verdicts(statuses)
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "mode": mode_label,
        "verdict": verdict,
        "exit": exit_code,
        "gates": details,
    }

    if json_mode:
        print(json.dumps(entry, indent=2))
    else:
        print(f"=== Fleet Convergence Gate ({mode_label}) ===")
        print(f"Time: {entry['ts']}")
        for name in GATES:
            d = details[name]
            print(f"  {name:14s} | {d['status']:6s} | exit {d['exit']}"
                  + (f" | {d['note']}" if d['note'] else ""))
        print()
        print(f"  VERDICT: {verdict} (exit {exit_code})")

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
