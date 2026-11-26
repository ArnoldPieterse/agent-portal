#!/usr/bin/env python3
"""dispatch_gate.py - Forge goal #3: Dispatch-Correctness Deploy Gate.

Pre-promotion gate for the canary pipeline. Before promoting any change that
touches dispatch logic, this gate runs a conformance audit on synthetic +
historical data and BLOCKS promotion if conformance < 100%.

A "dispatch violation" = next10.json (or injected forecast) dispatches a goal
whose title already carries a reached-marker in its lane goal file. Re-dispatching
a reached goal is stale work -> the gate blocks it.

Dispatch-logic files that trigger the gate when deployed:
  - memory/builder/dispatch_filter.py
  - memory/builder/fleet_mode_writer.py
  - memory/orchestrator/auto_cycle_planner.py
  - memory/goals/next10.json

The gate is skippable ONLY via the explicit --bypass-gate flag (logged as an
override). A non-dispatch file auto-skips (no audit needed); a dispatch file
WITHOUT the flag always runs.

Usage:
    python memory/forge/dispatch_gate.py --file <changed_file>
    python memory/forge/dispatch_gate.py --file <dispatch_file> --bypass-gate
    python memory/forge/dispatch_gate.py --selftest

Exit codes:
  0 = gate passed (conformance 100%, non-dispatch skip, or explicit bypass)
  1 = gate BLOCKED (conformance < 100%, violation logged) / selftest failed
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
GOALS_DIR = BASE / "memory" / "goals"
NEXT10 = GOALS_DIR / "next10.json"
GATE_LOG = BASE / "memory" / "forge" / "dispatch-gate-log.jsonl"

DISPATCH_FILES = {
    "memory/builder/dispatch_filter.py",
    "memory/builder/fleet_mode_writer.py",
    "memory/orchestrator/auto_cycle_planner.py",
    "memory/goals/next10.json",
}

AGENT_FILES = {
    "archivist.md", "builder.md", "designer.md", "forge.md",
    "mechanic.md", "orchestrator.md", "outlet.md", "pixel.md",
    "researcher.md", "scribe.md", "verifier.md",
}

# reached-marker: a goal line that already has evidence of completion
REACHED_MARK = re.compile(r"\(verified:.*?\)|\(pointe.*?\)|recorded\s+20\d\d")
GOAL_LINE = re.compile(r"^\s*\d+\.\s+\*\*(.+?)\*\*")
BOLD = re.compile(r"\*\*(.+?)\*\*")


def norm(s):
    return re.sub(r"\s+", " ", s.strip().lower())


def extract_title(goal_str):
    """Pull the bold title out of a goal string; fall back to the whole string."""
    m = BOLD.search(goal_str or "")
    return (m.group(1) if m else (goal_str or "")).strip()


def is_dispatch_file(filepath):
    normalized = (filepath or "").replace("\\", "/")
    for df in DISPATCH_FILES:
        if normalized.endswith(df) or ("/" + df) in ("/" + normalized):
            return True
    return False


def load_reached_titles():
    """Map norm(title) -> (file, line) for every goal line that has a reached marker."""
    reached = {}
    for fn in AGENT_FILES:
        gf = GOALS_DIR / fn
        if not gf.exists():
            continue
        text = gf.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            m = GOAL_LINE.match(line)
            if m and REACHED_MARK.search(line):
                reached[norm(m.group(1))] = (fn, line.strip()[:90])
    return reached


def _load_next10_list(data):
    """Return the list of dispatch entries from an injected dict OR the live file."""
    if data is None:
        if not NEXT10.exists():
            raise FileNotFoundError("next10.json missing")
        data = json.loads(NEXT10.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if "next10" in data:
        return data["next10"]
    out = []
    for agent, d in (data.get("agents") or {}).items():
        for g in d.get("goals", []):
            gg = dict(g)
            gg.setdefault("agent", agent)
            out.append(gg)
    return out


def run_conformance_audit(data=None):
    """Conformance audit. data=None reads the live next10.json (historical)."""
    try:
        entries = _load_next10_list(data)
    except Exception as e:  # noqa: BLE001
        return {"pass": False, "violations": [], "details": "load error: %s" % e,
                "conformance_pct": 0.0, "total_dispatched": 0}

    reached = load_reached_titles()
    violations = []
    for e in entries:
        title = norm(extract_title(e.get("goal", "")))
        agent = e.get("agent", "?")
        if title and title in reached:
            src_file, src_line = reached[title]
            violations.append({
                "agent": agent,
                "goal": extract_title(e.get("goal", "")),
                "reason": "already reached (re-dispatch of a completed goal)",
                "evidence": "%s: %s" % (src_file, src_line),
            })

    total = len(entries)
    clean = total - len(violations)
    pct = round(clean / max(total, 1) * 100, 2)
    return {
        "pass": len(violations) == 0,
        "violations": violations,
        "details": "%s%% conformance (%d/%d clean)" % (pct, clean, total),
        "conformance_pct": pct,
        "total_dispatched": total,
    }


def decide(file, flags):
    """Decision matrix. Returns: no-file | skipped-not-dispatch | run | bypassed."""
    if not file:
        return "no-file"
    if not is_dispatch_file(file):
        return "skipped-not-dispatch"
    if "--bypass-gate" in flags:
        return "bypassed"
    return "run"


def log_gate_event(event):
    GATE_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts": datetime.now(timezone.utc).isoformat()}
    entry.update(event)
    with open(GATE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def selftest():
    print("FORGE GATE SELFTEST: Dispatch-Correctness (synthetic + historical)")
    print("=" * 60)
    ok = True

    # Part A: BLOCK on a synthetic stale-goal dispatch
    reached = load_reached_titles()
    if not reached:
        print("  [A] FAIL - no reached titles found to build synthetic violation")
        ok = False
    else:
        sample_title = next(iter(reached))
        synthetic = [
            {"agent": "forge", "goal": "**%s** - (re-dispatched, should be blocked)" % sample_title},
            {"agent": "builder", "goal": "**Totally Novel Unreached Goal XYZ-999** - fresh"},
        ]
        res = run_conformance_audit(synthetic)
        a_ok = (res["pass"] is False and len(res["violations"]) == 1
                and norm(res["violations"][0]["goal"]) == sample_title)
        print("  [A] BLOCK synthetic stale-goal: %s" % ("PASS" if a_ok else "FAIL"))
        print("      -> pass=%s violations=%d (%s)" % (res["pass"], len(res["violations"]), res["details"]))
        ok = ok and a_ok

    # Part B: CLEAN change promotes (synthetic all-clean)
    clean_set = [
        {"agent": "builder", "goal": "**Brand New Convergence Gate Alpha** - x"},
        {"agent": "scribe", "goal": "**Brand New Convergence Gate Beta** - y"},
    ]
    res_clean = run_conformance_audit(clean_set)
    b_ok = (res_clean["pass"] is True and len(res_clean["violations"]) == 0)
    print("  [B] CLEAN promotes: %s" % ("PASS" if b_ok else "FAIL"))
    print("      -> pass=%s violations=%d (%s)" % (res_clean["pass"], len(res_clean["violations"]), res_clean["details"]))
    ok = ok and b_ok

    # Part B2: HISTORICAL (live next10.json) informational conformance
    res_live = run_conformance_audit(None)
    print("  [B2] HISTORICAL live next10.json: %s" % res_live["details"])
    for v in res_live["violations"][:5]:
        print("       stale dispatch: [%s] %s :: %s" % (v["agent"], v["goal"], v["evidence"][:70]))

    # Part C: skippable ONLY with explicit flag (decision matrix)
    d1 = decide("memory/forge/smoke_suite.py", set())
    d2 = decide("memory/builder/dispatch_filter.py", set())
    d3 = decide("memory/builder/dispatch_filter.py", {"--bypass-gate"})
    c_ok = (d1 == "skipped-not-dispatch" and d2 == "run" and d3 == "bypassed")
    print("  [C] skippable-only-with-flag: %s" % ("PASS" if c_ok else "FAIL"))
    print("      -> non-dispatch=%r dispatch-noflag=%r dispatch+flag=%r" % (d1, d2, d3))
    ok = ok and c_ok

    log_gate_event({"action": "selftest", "result": "pass" if ok else "fail",
                    "live_conformance_pct": res_live["conformance_pct"],
                    "live_violations": len(res_live["violations"])})

    print("=" * 60)
    print("SELFTEST RESULT:", "ALL PASS (exit 0)" if ok else "FAIL (exit 1)")
    return 0 if ok else 1


def main():
    parser = argparse.ArgumentParser(description="Dispatch-Correctness Deploy Gate")
    parser.add_argument("--file", help="The file being deployed")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--force", action="store_true",
                        help="Run the audit even if the file is not dispatch-related (testing)")
    parser.add_argument("--bypass-gate", action="store_true",
                        help="EXPLICIT override: skip the audit for a dispatch file (logged)")
    args = parser.parse_args()

    if args.selftest:
        sys.exit(selftest())

    flags = set()
    if args.bypass_gate:
        flags.add("--bypass-gate")
    if args.force:
        flags.add("--force")

    decision = decide(args.file, flags)
    print("FORGE GATE: Dispatch-Correctness")
    print("-" * 40)

    if decision == "no-file":
        print("  No file specified. Gate SKIPPED.")
        sys.exit(0)
    if decision == "skipped-not-dispatch":
        print("  File %r is not dispatch-related. Gate SKIPPED (no audit)." % args.file)
        log_gate_event({"file": args.file, "action": "skipped", "reason": "not-dispatch"})
        sys.exit(0)
    if decision == "bypassed":
        print("  File %r IS dispatch-related but --bypass-gate given. OVERRIDDEN." % args.file)
        log_gate_event({"file": args.file, "action": "override", "reason": "explicit-bypass"})
        sys.exit(0)

    # decision == "run"
    if not is_dispatch_file(args.file) and "--force" in flags:
        print("  (forced audit on non-dispatch file %r)" % args.file)
    result = run_conformance_audit()
    if result["pass"]:
        print("  PASS: %s" % result["details"])
        log_gate_event({"file": args.file, "action": "pass", "details": result["details"]})
        sys.exit(0)
    else:
        print("  BLOCKED: %s" % result["details"])
        for v in result["violations"][:5]:
            print("    VIOLATION: [%s] %s (%s)" % (v["agent"], v["goal"], v["reason"]))
        log_gate_event({"file": args.file, "action": "blocked", "details": result["details"],
                        "violations": result["violations"][:10]})
        print("\n  PROMOTION BLOCKED. Fix stale dispatches and re-run (or --bypass-gate to override).")
        sys.exit(1)


if __name__ == "__main__":
    main()
