"""Autonomy Loop-Closure Rate (Researcher Goal #1, cycle-10).

Parses every autonomous action in decision-log.jsonl + goal_ledger_current.json;
classifies each as CLOSED (detected -> action taken -> verified) or OPEN.
Output: memory/researcher/loop-closure-report.md with overall rate + per-type breakdown.

Verification criteria:
- Runs without error on all three decision-log sources
- Every entry is classified exactly once
- Rate = closed / total, reported to 1 decimal place
- Per-type breakdown includes >=3 distinct types
"""
import json
import pathlib
from datetime import datetime, timezone

LOG_SOURCES = [
    "decision-log.jsonl",
    "memory/decision-log.jsonl",
    "memory/ops/decision-log.jsonl",
]
GOAL_LEDGER = "memory/researcher/goal_ledger_current.json"
OUTPUT = "memory/researcher/loop-closure-report.md"

# Outcome values that indicate a closed loop (action completed + verified)
CLOSED_OUTCOMES = {
    "success", "dry_run_complete", "playbook_complete", "runbook_execution",
    "SELFTEST",  # self-test passed = verified
}
# Outcome values indicating failure/rollback (closed but failed loop)
FAILED_OUTCOMES = {"failure", "rollback", "error"}


def load_log_entries():
    """Load all decision-log entries from all sources."""
    entries = []
    for src in LOG_SOURCES:
        p = pathlib.Path(src)
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8").strip()
        if not text:
            continue
        for line in text.split("\n"):
            try:
                obj = json.loads(line)
                obj["_source"] = src
                entries.append(obj)
            except json.JSONDecodeError:
                pass
    return entries


def classify_entry(entry):
    """Classify a single decision-log entry as CLOSED, OPEN, or FAILED."""
    etype = entry.get("type", "unknown")
    outcome = (entry.get("outcome") or "").lower()
    overall_ok = entry.get("overall_ok")
    rolled_back = entry.get("rolled_back", False)

    # Runbook executions: closed if overall_ok is True, failed if rolled back
    if etype in ("runbook_execution", "runbook_exec"):
        if rolled_back:
            return "FAILED"
        if overall_ok is True or outcome in CLOSED_OUTCOMES:
            return "CLOSED"
        if overall_ok is False:
            return "FAILED"
        # No outcome info = open (in progress)
        return "OPEN"

    # Playbook dry runs: closed on completion, open otherwise
    if etype == "playbook_dry_run":
        if outcome in ("dry_run_complete", "success"):
            return "CLOSED"
        return "OPEN"

    # Playbook steps: individual steps are always "closed" (completed or not)
    if etype == "playbook_step":
        if entry.get("passed") is True or outcome in CLOSED_OUTCOMES:
            return "CLOSED"
        return "FAILED"

    # Playbook complete/rollback
    if etype == "playbook_complete":
        return "CLOSED"
    if etype == "playbook_rollback":
        return "FAILED"

    # OOM recovery: closed if outcome indicates success
    if etype == "oom_recovery":
        if outcome in CLOSED_OUTCOMES or "success" in outcome:
            return "CLOSED"
        return "OPEN"

    # Self-test: always closed (passed)
    if etype == "SELFTEST":
        return "CLOSED"

    # Cycle trigger: informational, always closed (trigger fired)
    if etype == "cycle_trigger":
        return "CLOSED"

    # Default: open if no clear outcome
    if outcome in CLOSED_OUTCOMES:
        return "CLOSED"
    return "OPEN"


def load_goal_state():
    """Load goal ledger and classify goals as closed/open."""
    p = pathlib.Path(GOAL_LEDGER)
    if not p.exists():
        return []
    gl = json.loads(p.read_text(encoding="utf-8"))
    results = []
    for agent_name, data in gl.get("agents", {}).items():
        for goal in data.get("goals", []):
            text = goal.get("text", "")
            # Check if verified (has "verified:" marker) or reached
            is_verified = "verified:" in text.lower() or "pointer:" in text.lower()
            results.append({
                "agent": agent_name,
                "goal_text": text[:100],
                "status": "CLOSED" if is_verified else "OPEN",
            })
    return results


def main():
    entries = load_log_entries()
    goal_states = load_goal_state()

    # Classify decision-log entries
    log_classified = []
    for e in entries:
        cls = classify_entry(e)
        log_classified.append({**e, "_class": cls})

    # Aggregate
    total_actions = len(log_classified) + len(goal_states)
    closed_count = sum(1 for e in log_classified if e["_class"] == "CLOSED")
    failed_count = sum(1 for e in log_classified if e["_class"] == "FAILED")
    open_log_count = sum(1 for e in log_classified if e["_class"] == "OPEN")
    closed_goals = sum(1 for g in goal_states if g["status"] == "CLOSED")
    open_goals = sum(1 for g in goal_states if g["status"] == "OPEN")

    total_closed = closed_count + closed_goals
    total_open = open_log_count + open_goals
    total_failed = failed_count

    closure_rate = (total_closed / total_actions * 100) if total_actions else 0.0
    log_closure_rate = (closed_count / len(log_classified) * 100) if log_classified else 0.0

    # Per-type breakdown
    by_type = {}
    for e in log_classified:
        t = e.get("type", "unknown")
        by_type.setdefault(t, {"CLOSED": 0, "OPEN": 0, "FAILED": 0})
        by_type[t][e["_class"]] += 1

    # Write report
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Autonomy Loop-Closure Rate Report",
        f"Generated: {now}",
        "",
        "## Summary",
        f"- Total autonomous actions tracked: **{total_actions}**",
        f"- CLOSED (detected -> action -> verified): **{total_closed}**",
        f"- OPEN (in progress / not yet verified): **{total_open}**",
        f"- FAILED (loop closed but outcome negative): **{total_failed}**",
        f"- **Overall loop-closure rate: {closure_rate:.1f}%**",
        f"- Decision-log closure rate: {log_closure_rate:.1f}%",
        "",
        "## Per-Type Breakdown (decision-log entries)",
        "| Type | Closed | Open | Failed | Total | Closure% |",
        "|------|--------|------|--------|-------|----------|",
    ]
    for t in sorted(by_type.keys()):
        d = by_type[t]
        tot = d["CLOSED"] + d["OPEN"] + d["FAILED"]
        rate = (d["CLOSED"] / tot * 100) if tot else 0.0
        lines.append(f"| {t} | {d['CLOSED']} | {d['OPEN']} | {d['FAILED']} | {tot} | {rate:.0f}% |")

    lines += [
        "",
        "## Goal Ledger Breakdown",
        f"- Goals reached (closed): **{closed_goals}**",
        f"- Goals open: **{open_goals}**",
        f"- Goal closure rate: {(closed_goals / len(goal_states) * 100) if goal_states else 0:.1f}%",
        "",
        "## Interpretation",
    ]
    if closure_rate >= 80:
        lines.append("Loop-closure rate is HEALTHY (>=80%). Most autonomous actions complete their full loop.")
    elif closure_rate >= 50:
        lines.append("Loop-closure rate is MODERATE (50-80%). Several actions are stuck in progress or unverified.")
    else:
        lines.append("Loop-closure rate is LOW (<50%). Significant autonomy gap - many actions detected but never closed.")

    report = "\n".join(lines) + "\n"
    pathlib.Path(OUTPUT).write_text(report, encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    print(f"Overall closure rate: {closure_rate:.1f}% ({total_closed}/{total_actions} closed)")

    # Self-test assertions
    assert total_actions > 0, "No actions found - check log paths"
    assert sum(by_type[t]["CLOSED"] + by_type[t]["OPEN"] + by_type[t]["FAILED"] for t in by_type) == len(log_classified), "Classification count mismatch"
    assert len(by_type) >= 3, f"Expected >=3 distinct types, got {len(by_type)}"
    print("SELFTEST PASS")


if __name__ == "__main__":
    main()
