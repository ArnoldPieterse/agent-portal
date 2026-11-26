#!/usr/bin/env python3
"""dispatch_gate.py - Forge goal #3: Dispatch-Correctness Deploy Gate.

Pre-promotion gate for the canary pipeline. Before promoting any change that
touches dispatch logic, this gate runs a conformance audit on synthetic + 
historical data. BLOCKS promotion if conformance < 100%.

Dispatch-logic files (triggers the gate):
  - memory/builder/dispatch_filter.py
  - memory/builder/fleet_mode_writer.py  
  - memory/orchestrator/auto_cycle_planner.py
  - memory/goals/next10.json

Usage:
    python memory/forge/dispatch_gate.py --file <changed_file>
    python memory/forge/dispatch_gate.py --selftest

Exit codes:
  0 = gate passed (conformance 100% or file not dispatch-related)
  1 = gate BLOCKED (conformance < 100%, violation logged)
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

# Files that trigger the dispatch gate when changed
DISPATCH_FILES = {
    "memory/builder/dispatch_filter.py",
    "memory/builder/fleet_mode_writer.py",
    "memory/orchestrator/auto_cycle_planner.py",
    "memory/goals/next10.json",
}

AGENT_FILES = {
    "archivist.md", "builder.md", "designer.md", "forge.md",
    "mechanic.md", "orchestrator.md", "outlet.md", "pixel.md",
    "researcher.md", "scribe.md", "verifier.md"
}


def is_dispatch_file(filepath: str) -> bool:
    """Check if a file path triggers the dispatch gate."""
    normalized = filepath.replace("\\", "/")
    for df in DISPATCH_FILES:
        if normalized.endswith(df) or df in normalized:
            return True
    return False


def run_conformance_audit() -> dict:
    """Run the dispatch conformance check. Returns {pass, violations, details}."""
    if not NEXT10.exists():
        return {"pass": False, "violations": [], "details": "next10.json missing"}

    try:
        n10 = json.loads(NEXT10.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return {"pass": False, "violations": [], "details": f"next10.json parse error: {e}"}

    # Collect reached goals
    evidence_re = re.compile(r"\(verified:.*?\)|\(pointe.*?\)|recorded\s+20\d\d")
    pattern = re.compile(r"^\s*\d+\.\s+\*\*(.+?)\*\*")
    reached_titles = set()
    for fn in AGENT_FILES:
        gf = GOALS_DIR / fn
        if not gf.exists():
            continue
        text = gf.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            m = pattern.match(line)
            if m and evidence_re.search(line):
                reached_titles.add(m.group(1).strip().lower())

    # Check for violations
    violations = []
    agents_data = n10.get("agents", {})
    total_dispatched = 0
    for agent, data in agents_data.items():
        goals = data.get("goals", [])
        for g in goals:
            total_dispatched += 1
            title = g.get("title", "").strip().lower()
            if title and title in reached_titles:
                violations.append({
                    "agent": agent,
                    "goal": g.get("title"),
                    "reason": "already reached (evidence marker present)"
                })

    conformance_pct = round((total_dispatched - len(violations)) / max(total_dispatched, 1) * 100, 2)
    return {
        "pass": len(violations) == 0,
        "violations": violations,
        "details": f"{conformance_pct}% conformance ({total_dispatched - len(violations)}/{total_dispatched} clean)",
        "conformance_pct": conformance_pct,
        "total_dispatched": total_dispatched
    }


def log_gate_event(event: dict):
    """Append to the gate log."""
    GATE_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts": datetime.now(timezone.utc).isoformat(), **event}
    with open(GATE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Dispatch-Correctness Deploy Gate")
    parser.add_argument("--file", help="The file being deployed (to check if gate is needed)")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--force", action="store_true", help="Run gate even if file isn't dispatch-related")
    args = parser.parse_args()

    print("FORGE GATE: Dispatch-Correctness")
    print("-" * 40)

    # Determine if gate is needed
    needs_gate = False
    if args.selftest or args.force:
        needs_gate = True
    elif args.file:
        needs_gate = is_dispatch_file(args.file)
        if not needs_gate:
            print(f"  File '{args.file}' is not dispatch-related. Gate SKIPPED.")
            log_gate_event({"file": args.file, "action": "skipped", "reason": "not-dispatch"})
            sys.exit(0)

    if not needs_gate:
        print("  No file specified and not forced. Gate SKIPPED.")
        sys.exit(0)

    # Run the audit
    result = run_conformance_audit()

    if result["pass"]:
        print(f"  PASS: {result['details']}")
        log_gate_event({"file": args.file, "action": "pass", "details": result["details"]})
        sys.exit(0)
    else:
        print(f"  BLOCKED: {result['details']}")
        for v in result["violations"][:5]:
            print(f"    VIOLATION: {v['agent']}: {v['goal']} ({v['reason']})")
        log_gate_event({
            "file": args.file, 
            "action": "blocked", 
            "details": result["details"],
            "violations": result["violations"][:10]
        })
        print("\n  PROMOTION BLOCKED. Fix dispatch violations and re-run.")
        sys.exit(1)


if __name__ == "__main__":
    main()
