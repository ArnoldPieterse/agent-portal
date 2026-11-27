#!/usr/bin/env python3
"""SIM (Self-Improvement Memory) updater + health checker for Scribe lane.

Source: arxiv 2611.18856v1 — Self-Improvement Memory Enables Continual Recursive Self-Improvement
Usage:
  python memory/scribe/sim_update.py --add <problem> <rationale> <predicted> <observed> <provenance>
  python memory/scribe/sim_update.py --check
  python memory/scribe/sim_update.py --list

The paper's key insight: SIM entries must be appended AFTER each decision (only the chosen
candidate is recorded), predictions are checked post-hoc, and entries with identical
root-cause text are merged without dropping histories.
"""
import argparse, json, re, sys, datetime
from pathlib import Path

SIM_PATH = Path(__file__).parent / "sim.md"
LOG_PATH = Path(__file__).parent / "sim_log.jsonl"

def parse_sim():
    """Parse sim.md into structured entries."""
    if not SIM_PATH.exists():
        return []
    text = SIM_PATH.read_text(encoding="utf-8")
    problems = []
    current_problem = None
    for line in text.split("\n"):
        m = re.match(r"^## Problem: (\S+)", line)
        if m:
            current_problem = {"name": m.group(1), "attempts": [], "decision_rule": None}
            problems.append(current_problem)
            continue
        if current_problem is None:
            continue
        am = re.match(r"^- a(\d+) \(([^)]+)\): (.+)", line)
        if am:
            current_problem["attempts"].append({
                "id": int(am.group(1)),
                "date": am.group(2),
                "summary": am.group(3).strip()
            })
            continue
        dr = re.match(r"^- \*\*Decision rule\*\*: (.+)", line)
        if dr:
            current_problem["decision_rule"] = dr.group(1).strip()
    return problems

def add_attempt(problem_name, rationale, predicted, observed, provenance):
    """Append a new attempt to the given problem group in sim.md."""
    text = SIM_PATH.read_text(encoding="utf-8")
    today = datetime.date.today().isoformat()
    
    # Find the problem section
    pattern = rf"(## Problem: {re.escape(problem_name)}\n)"
    m = re.search(pattern, text)
    if not m:
        # Create new problem section before the last "## Problem:" or at end
        new_section = f"\n## Problem: {problem_name}\n- a1 ({today}): New entry\n  - rationale: {rationale}\n  - predicted: {predicted}\n  - observed: {observed}\n  - provenance: {provenance}\n"
        text += new_section
    else:
        # Find next "## Problem:" or end to determine insertion point
        rest = text[m.end():]
        next_problem = re.search(r"^## Problem:", rest, re.MULTILINE)
        insert_at = m.end() + (next_problem.start() if next_problem else len(rest))
        
        # Count existing attempts
        section_text = text[m.end():insert_at]
        attempt_count = len(re.findall(r"^- a\d+ \(", section_text, re.MULTILINE))
        new_id = attempt_count + 1
        
        entry = f"- a{new_id} ({today}): {rationale[:80]}\n  - rationale: {rationale}\n  - predicted: {predicted}\n  - observed: {observed}\n  - provenance: {provenance}\n"
        text = text[:insert_at] + entry + text[insert_at:]
    
    SIM_PATH.write_text(text, encoding="utf-8")
    
    # Log to JSONL for machine-readable history
    log_entry = {
        "ts": datetime.datetime.now().isoformat(),
        "problem": problem_name,
        "rationale": rationale,
        "predicted": predicted,
        "observed": observed,
        "provenance": provenance
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    print(f"OK: added attempt to '{problem_name}' (now {attempt_count+1} attempts)")

def health_check():
    """Validate SIM structure per paper requirements."""
    problems = parse_sim()
    issues = []
    stats = {"problems": len(problems), "total_attempts": 0, "pending_observed": 0}
    
    for p in problems:
        n = len(p["attempts"])
        stats["total_attempts"] += n
        
        # Rule: every group with >=2 attempts must have a decision rule
        if n >= 2 and not p.get("decision_rule"):
            issues.append(f"MISSING-RULE: '{p['name']}' has {n} attempts but no decision rule")
        
        # Flag groups with >5 attempts (rule may need revision)
        if n > 5:
            issues.append(f"HIGH-ATTEMPTS: '{p['name']}' has {n} attempts — consider revising decision rule")
    
    # Check for PENDING observed outcomes (predictions not yet validated)
    text = SIM_PATH.read_text(encoding="utf-8") if SIM_PATH.exists() else ""
    pending_count = text.count("observed: PENDING")
    stats["pending_observed"] = pending_count
    if pending_count > 0:
        issues.append(f"PENDING: {pending_count} attempt(s) have unvalidated predictions — check them")
    
    print(f"SIM Health Check: {stats['problems']} problems, {stats['total_attempts']} attempts, {stats['pending_observed']} pending")
    if issues:
        print("Issues:")
        for i in issues:
            print(f"  - {i}")
    else:
        print("All checks PASS")
    return len(issues) == 0

def list_problems():
    """List all problem groups with attempt counts."""
    problems = parse_sim()
    print(f"SIM: {len(problems)} problem groups, {sum(len(p['attempts']) for p in problems)} total attempts\n")
    for p in problems:
        rule = "✓" if p.get("decision_rule") else "✗"
        print(f"  [{rule}] {p['name']} ({len(p['attempts'])} attempts)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="SIM updater for Scribe lane")
    sub = ap.add_subparsers(dest="cmd")
    
    add_p = sub.add_parser("add", help="Add a new attempt to a problem group")
    add_p.add_argument("problem")
    add_p.add_argument("rationale")
    add_p.add_argument("predicted")
    add_p.add_argument("observed")
    add_p.add_argument("provenance")
    
    sub.add_parser("check", help="Run health check")
    sub.add_parser("list", help="List problem groups")
    
    args = ap.parse_args()
    if args.cmd == "add":
        add_attempt(args.problem, args.rationale, args.predicted, args.observed, args.provenance)
    elif args.cmd == "check":
        ok = health_check()
        sys.exit(0 if ok else 1)
    elif args.cmd == "list":
        list_problems()
    else:
        ap.print_help()
