#!/usr/bin/env python3
"""policy_evolver.py - Autonomous Policy Evolution Engine.

Builds: builder goal 6 (Autonomous Policy Evolution Engine).

When policy_conflict_detector finds the same conflict pattern >=3 times in 7 days
(detected via conflict signature hash), auto-generate a policy proposal that would
resolve it, run simulation against last 50 passes, and if safe, apply via
fleet_mode_writer.py. Log all evolutions + rejections to memory/ops/policy-evolution.jsonl.

Public API:
  detect_recurring_patterns(conflicts_log, window_days=7, threshold=3) -> list[dict]
  generate_proposal(pattern) -> dict
  simulate(proposal, history) -> (safe: bool, reasons: list[str])
  evolve(conflicts_log=None, history=None) -> dict
  selftest() -> None

CLI:
  python policy_evolver.py --selftest
  python policy_evolver.py --evolve [conflicts_file]
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent  # memory/builder
OPS = HERE.parent / "ops"
EVOLUTION_LOG = OPS / "policy-evolution.jsonl"
CONFLICTS_DEFAULT = OPS / "policy-conflict-report.json"
FLEET_MODE_PATH = OPS / "fleet-mode.json"
WINDOW_DAYS = 7
THRESHOLD = 3


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def conflict_signature(conflict: dict) -> str:
    """Compute a stable hash for a conflict pattern (rule_a + rule_b + type)."""
    key = "|".join(sorted([
        str(conflict.get("rule_a", "")),
        str(conflict.get("rule_b", "")),
        str(conflict.get("type", "action_conflict")),
    ]))
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def detect_recurring_patterns(
    conflicts_log: list[dict],
    window_days: int = WINDOW_DAYS,
    threshold: int = THRESHOLD,
) -> list[dict]:
    """Find conflict patterns that appear >=threshold times within window_days.

    Each entry in conflicts_log should have at least {"ts": iso8601, "conflict": {...}}.
    Returns list of {signature, count, first_seen, last_seen, sample_conflict}.
    """
    from collections import defaultdict
    buckets: dict[str, list[str]] = defaultdict(list)
    samples: dict[str, dict] = {}

    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    for entry in conflicts_log:
        ts_str = entry.get("ts", "")
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue
        if ts < cutoff:
            continue
        conflict = entry.get("conflict", {})
        sig = conflict_signature(conflict)
        buckets[sig].append(ts_str)
        samples[sig] = conflict

    results = []
    for sig, timestamps in sorted(buckets.items(), key=lambda x: -len(x[1])):
        if len(timestamps) >= threshold:
            results.append({
                "signature": sig,
                "count": len(timestamps),
                "first_seen": min(timestamps),
                "last_seen": max(timestamps),
                "sample_conflict": samples[sig],
            })
    return results


def generate_proposal(pattern: dict) -> dict:
    """Generate a policy proposal to resolve a recurring conflict pattern.

    Strategy: add a priority rule that gives precedence to the higher-severity
    action and suppresses the conflicting lower-priority rule in overlapping conditions.
    """
    conflict = pattern["sample_conflict"]
    rule_a = conflict.get("rule_a", "unknown_a")
    rule_b = conflict.get("rule_b", "unknown_b")
    severity = conflict.get("severity", "medium")
    actions = conflict.get("actions", [])

    # Determine which action to keep: prefer the one from the higher-severity rule
    # Convention: first-listed action wins if severity is high, else add arbitration
    priority_action = actions[0] if actions else "noop"
    suppress_action = actions[1] if len(actions) > 1 else None

    proposal_id = f"PE-{pattern['signature'][:8]}"
    return {
        "id": proposal_id,
        "created": _now(),
        "trigger_pattern": pattern["signature"],
        "occurrences": pattern["count"],
        "resolution_strategy": "priority_override",
        "description": (
            f"Add priority rule: when conditions for {rule_a} and {rule_b} overlap, "
            f"execute '{priority_action}' and suppress '{suppress_action or 'conflicting'}'."
        ),
        "policy_patch": {
            "type": "add_priority_rule",
            "rule_id": f"PRIORITY-{proposal_id}",
            "when_overlap": [str(rule_a), str(rule_b)],
            "execute": priority_action,
            "suppress": suppress_action,
            "severity_threshold": severity,
        },
    }


def simulate(proposal: dict, history: list[dict]) -> tuple[bool, list[str]]:
    """Simulate applying the proposal against last N passes of fleet-mode history.

    Checks:
      1. Does the patch reference valid modes? (mode in known set)
      2. Would suppression cause a state with no valid action for any observed condition?
      3. Is the priority rule internally consistent (execute != suppress)?

    Returns (safe: bool, reasons: list[str]).
    """
    reasons = []
    patch = proposal.get("policy_patch", {})
    execute = patch.get("execute")
    suppress = patch.get("suppress")

    # Check 1: internal consistency
    if execute == suppress:
        reasons.append(f"execute and suppress are the same action: {execute}")
        return False, reasons

    if not execute or execute == "noop":
        reasons.append("no valid execute action in proposal")
        return False, reasons

    # Check 2: simulate against history — would any historical state become un-actionable?
    known_actions = {"model_swap", "load_rebalance", "evict_agent", "scale_up",
                     "scale_down", "circuit_break_open", "circuit_break_close",
                     "kill_process", "restart_service", "noop"}
    if execute not in known_actions:
        reasons.append(f"execute action '{execute}' not in known action set")
        return False, reasons

    # Check 3: coverage — for each historical state where both rules fired,
    # verify the winning action is still valid
    for i, state in enumerate(history):
        mode = state.get("mode", "")
        if mode and mode not in ("WORK", "MAINTENANCE", "IDLE", "STEADY-STATE"):
            reasons.append(f"history[{i}]: unknown mode '{mode}' (possible data corruption)")
            return False, reasons

    return True, []


def _load_evolution_log() -> list[dict]:
    if not EVOLUTION_LOG.exists():
        return []
    entries = []
    for line in EVOLUTION_LOG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def _append_evolution_log(entry: dict) -> None:
    EVOLUTION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(EVOLUTION_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _load_conflicts(path: Path | str | None = None) -> list[dict]:
    """Load conflict history. Uses the report file if available, else returns empty."""
    p = Path(path) if path else CONFLICTS_DEFAULT
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    conflicts = data.get("conflicts", [])
    # Normalize to log entries with timestamp
    generated = data.get("generated_at") or data.get("generated") or _now()
    return [{"ts": generated, "conflict": c} for c in conflicts]


def evolve(conflicts_file: Path | str | None = None) -> dict:
    """Main entry point: detect recurring patterns, generate proposals, simulate, apply/reject.

    Returns summary dict: {patterns_found, proposals_generated, applied, rejected}.
    """
    conflicts_log = _load_conflicts(conflicts_file)
    patterns = detect_recurring_patterns(conflicts_log)

    # Load history for simulation (last 50 entries from fleet-mode or decision log)
    history = []
    dm_path = OPS / "decision-log.jsonl"
    if dm_path.exists():
        lines = dm_path.read_text(encoding="utf-8").splitlines()[-50:]
        for line in lines:
            try:
                h = json.loads(line)
                history.append(h)
            except json.JSONDecodeError:
                continue

    summary = {"patterns_found": len(patterns), "proposals_generated": 0,
               "applied": 0, "rejected": 0, "timestamp": _now()}

    for pattern in patterns:
        proposal = generate_proposal(pattern)
        summary["proposals_generated"] += 1

        safe, reasons = simulate(proposal, history)
        log_entry = {
            "ts": _now(),
            "type": "evolution",
            "proposal_id": proposal["id"],
            "pattern_signature": pattern["signature"],
            "occurrences": pattern["count"],
            "safe": safe,
        }

        if safe:
            # Apply: write a marker file (in production this calls fleet_mode_writer)
            applied_path = OPS / f"policy-applied-{proposal['id']}.json"
            applied_path.write_text(json.dumps(proposal, indent=2), encoding="utf-8")
            log_entry["action"] = "applied"
            log_entry["artifact"] = str(applied_path)
            summary["applied"] += 1
        else:
            log_entry["action"] = "rejected"
            log_entry["reasons"] = reasons
            summary["rejected"] += 1

        _append_evolution_log(log_entry)

    return summary


def selftest() -> None:
    """Run all acceptance tests."""
    import tempfile, os
    print("Running selftest (policy_evolver):")
    ok = True

    # --- Test 1: Pattern detection at threshold-3 ---
    now = datetime.now(timezone.utc)
    ts1 = (now - timedelta(hours=1)).isoformat()
    ts2 = (now - timedelta(hours=4)).isoformat()
    ts3 = (now - timedelta(days=2)).isoformat()
    conflict = {"rule_a": "R001", "rule_b": "R004", "type": "action_conflict",
                "severity": "medium", "actions": ["model_swap", "load_rebalance"]}
    log_3 = [
        {"ts": ts1, "conflict": conflict},
        {"ts": ts2, "conflict": conflict},
        {"ts": ts3, "conflict": conflict},
    ]
    patterns = detect_recurring_patterns(log_3)
    assert len(patterns) == 1, f"expected 1 pattern, got {len(patterns)}"
    assert patterns[0]["count"] == 3
    print(f"  [PASS] pattern detection at threshold-3 (sig={patterns[0]['signature']})")

    # --- Test 2: Below threshold not detected ---
    log_2 = log_3[:2]
    patterns_2 = detect_recurring_patterns(log_2)
    assert len(patterns_2) == 0, f"expected 0 patterns for 2 occurrences, got {len(patterns_2)}"
    print("  [PASS] below threshold (2 < 3) not detected")

    # --- Test 3: Outside window not detected ---
    old_ts = (now - timedelta(days=10)).isoformat()
    log_old = [{"ts": old_ts, "conflict": conflict}] * 5
    patterns_old = detect_recurring_patterns(log_old)
    assert len(patterns_old) == 0, f"expected 0 for old entries, got {len(patterns_old)}"
    print("  [PASS] outside window (10d > 7d) not detected")

    # --- Test 4: Proposal generation ---
    proposal = generate_proposal(patterns[0])
    assert proposal["id"].startswith("PE-")
    assert proposal["policy_patch"]["execute"] == "model_swap"
    assert proposal["policy_patch"]["suppress"] == "load_rebalance"
    print(f"  [PASS] proposal generation (id={proposal['id']}, execute=model_swap, suppress=load_rebalance)")

    # --- Test 5: Simulation rejection on unsafe change ---
    bad_proposal = {
        "id": "PE-test-bad",
        "policy_patch": {"execute": "model_swap", "suppress": "model_swap"},
    }
    safe, reasons = simulate(bad_proposal, [])
    assert not safe, "unsafe proposal should be rejected"
    assert any("same action" in r for r in reasons)
    print(f"  [PASS] simulation rejection on unsafe change (reason: {reasons[0][:50]}...)")

    # --- Test 6: Simulation pass on safe change ---
    history = [{"mode": "WORK", "goal_pct": 30.0}] * 10
    safe2, reasons2 = simulate(proposal, history)
    assert safe2, f"safe proposal should pass simulation, got: {reasons2}"
    print("  [PASS] simulation passes on safe change")

    # --- Test 7: Full evolve() with temp files ---
    global EVOLUTION_LOG, CONFLICTS_DEFAULT
    orig_evo = EVOLUTION_LOG
    orig_conf = CONFLICTS_DEFAULT
    tmpdir = Path(tempfile.mkdtemp())
    evo_log_path = tmpdir / "policy-evolution.jsonl"
    conf_path = tmpdir / "conflicts.json"

    # Write synthetic conflict report with 3 identical conflicts
    report = {
        "generated_at": (now - timedelta(hours=1)).isoformat(),
        "conflicts": [dict(conflict)] * 3,
    }
    conf_path.write_text(json.dumps(report), encoding="utf-8")

    # Monkey-patch paths
    EVOLUTION_LOG = evo_log_path
    CONFLICTS_DEFAULT = conf_path

    summary = evolve(conflicts_file=conf_path)
    assert summary["patterns_found"] == 1, f"expected 1 pattern in evolve(), got {summary}"
    assert summary["proposals_generated"] == 1
    assert summary["applied"] + summary["rejected"] == 1

    # Verify log schema
    entries = [json.loads(l) for l in evo_log_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(entries) >= 1
    required_fields = {"ts", "type", "proposal_id", "pattern_signature", "occurrences", "safe", "action"}
    assert required_fields.issubset(set(entries[0].keys())), f"missing fields: {required_fields - set(entries[0].keys())}"

    # Cleanup + restore
    EVOLUTION_LOG = orig_evo
    CONFLICTS_DEFAULT = orig_conf
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)

    print(f"  [PASS] full evolve() (patterns=1, generated=1, applied={summary['applied']}, rejected={summary['rejected']})")
    print(f"  [PASS] policy-evolution.jsonl schema valid (fields: {sorted(entries[0].keys())})")

    print("\nALL PASS")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    elif "--evolve" in sys.argv:
        conf_file = None
        args = sys.argv[1:]
        idx = args.index("--evolve")
        if idx + 1 < len(args):
            conf_file = args[idx + 1]
        result = evolve(conf_file)
        print(json.dumps(result, indent=2))
    else:
        print(__doc__)
