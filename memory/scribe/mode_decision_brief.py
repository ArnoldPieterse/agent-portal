#!/usr/bin/env python3
"""Mode Decision Brief Generator (Scribe goal #2, cycle 15).

For each fleet mode transition, writes a one-paragraph plain-English brief:
- current state before/after
- what triggered the change
- expected duration
- impact on dispatch

Usage: python memory/scribe/mode_decision_brief.py [--test]
Output: memory/synthesis/mode-briefs.md (appended per transition)
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
OPS_DIR = BASE / "memory" / "ops"
SYNTH_DIR = BASE / "memory" / "synthesis"
FLEET_MODE_PATH = OPS_DIR / "fleet-mode.json"
TRANSITIONS_PATH = OPS_DIR / "mode-transitions.jsonl"
DECISION_LOG_PATH = OPS_DIR / "decision-log.jsonl"
OUTPUT_PATH = SYNTH_DIR / "mode-briefs.md"

MODE_DESCRIPTIONS = {
    "WORK": "active goal-pursuit mode where all agents work their open goals",
    "MAINTENANCE": "maintenance mode where agents perform scheduled upkeep tasks instead of new goals",
    "IDLE": "idle mode where agents are paused awaiting new direction or cycle start",
}

TRIGGER_EXPLANATIONS = {
    "goal_completion": "all tracked goals reached 100% completion",
    "cycle_close": "the current work cycle has ended",
    "manual_override": "an operator manually changed the fleet mode",
    "idle_timeout": "no productive activity detected for the configured threshold",
    "new_cycle_start": "a new work cycle was initiated with fresh goals",
    "maintenance_window": "scheduled maintenance window opened",
}


def load_transitions() -> list[dict]:
    """Load mode transitions from all available sources."""
    transitions = []

    # Source 1: mode-transitions.jsonl (primary)
    if TRANSITIONS_PATH.exists():
        try:
            for line in TRANSITIONS_PATH.read_text(encoding="utf-8").strip().split("\n"):
                if line.strip():
                    try:
                        transitions.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        except Exception:
            pass

    # Source 2: decision-log.jsonl entries mentioning mode changes (fallback)
    if not transitions and DECISION_LOG_PATH.exists():
        try:
            for line in DECISION_LOG_PATH.read_text(encoding="utf-8").strip().split("\n"):
                if line.strip():
                    try:
                        d = json.loads(line)
                        text = json.dumps(d).lower()
                        if "mode" in text and ("fleet" in text or "transition" in text):
                            transitions.append(d)
                    except json.JSONDecodeError:
                        pass
        except Exception:
            pass

    return transitions


def load_current_mode() -> dict | None:
    """Load current fleet mode from fleet-mode.json."""
    if FLEET_MODE_PATH.exists():
        try:
            return json.loads(FLEET_MODE_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception):
            pass
    return None


def generate_brief(transition: dict) -> str:
    """Generate a one-paragraph plain-English brief for a mode transition."""
    from_mode = transition.get("from_mode", transition.get("previous", "WORK"))
    to_mode = transition.get("to_mode", transition.get("new_mode", transition.get("mode", "?")))
    timestamp = transition.get("timestamp", transition.get("ts", datetime.now(timezone.utc).isoformat()))
    trigger = transition.get("trigger", transition.get("reason", "unknown"))
    goal_pct = transition.get("goal_pct", transition.get("goals_completed_pct", None))
    duration_hint = transition.get("expected_duration_min", None)

    # Build the narrative
    from_desc = MODE_DESCRIPTIONS.get(from_mode, f"{from_mode} mode")
    to_desc = MODE_DESCRIPTIONS.get(to_mode, f"{to_mode} mode")
    trigger_text = TRIGGER_EXPLANATIONS.get(trigger.lower().replace(" ", "_"), trigger)

    parts = []
    parts.append(f"At {timestamp}, the fleet transitioned from {from_mode} to {to_mode}.")

    # State before
    if goal_pct is not None:
        parts.append(f"Before the change, {goal_pct}% of tracked goals were complete.")
    else:
        parts.append(f"The fleet was in {from_desc}.")

    # Trigger
    parts.append(f"This was triggered because: {trigger_text}.")

    # Expected duration
    if duration_hint:
        parts.append(f"Expected duration in this mode: ~{duration_hint} minutes.")

    # Impact on dispatch
    if to_mode == "WORK":
        parts.append("All agents will resume working their open goals from the next10.json queue.")
    elif to_mode == "MAINTENANCE":
        parts.append("Agents will switch to role-specific maintenance tasks from the idle-rotation table; new goal work is paused.")
    elif to_mode == "IDLE":
        parts.append("All agent activity is suspended until a new cycle or manual reactivation.")

    return " ".join(parts)


def main():
    test_mode = "--test" in sys.argv

    if test_mode:
        # Generate briefs from synthetic test data to verify the script works
        test_transitions = [
            {"from_mode": "WORK", "to_mode": "MAINTENANCE", "timestamp": "2026-11-24T08:00:00Z",
             "trigger": "maintenance_window", "goal_pct": 95.0, "expected_duration_min": 120},
            {"from_mode": "MAINTENANCE", "to_mode": "WORK", "timestamp": "2026-11-24T10:00:00Z",
             "trigger": "new_cycle_start", "goal_pct": 95.0},
            {"from_mode": "WORK", "to_mode": "IDLE", "timestamp": "2026-11-24T18:00:00Z",
             "trigger": "idle_timeout", "goal_pct": 100.0, "expected_duration_min": 480},
        ]
    else:
        test_transitions = load_transitions()

    if not test_transitions:
        # No transitions found - write a status note
        SYNTH_DIR.mkdir(parents=True, exist_ok=True)
        current = load_current_mode()
        mode_str = current.get("mode", "unknown") if current else "no fleet-mode.json found"
        OUTPUT_PATH.write_text(
            f"# Mode Decision Briefs\n\n"
            f"*No transitions recorded yet. Current mode: {mode_str}. "
            f"This file will be populated as mode transitions occur.*\n",
            encoding="utf-8",
        )
        print(f"No transitions found. Wrote status note to {OUTPUT_PATH.relative_to(BASE)}")
        return

    # Generate briefs
    lines = ["# Mode Decision Briefs", ""]
    for i, t in enumerate(test_transitions, 1):
        brief = generate_brief(t)
        from_mode = t.get("from_mode", t.get("previous", "?"))
        to_mode = t.get("to_mode", t.get("new_mode", t.get("mode", "?")))
        ts = t.get("timestamp", t.get("ts", "unknown"))[:19]
        lines.append(f"## Transition {i}: {from_mode} -> {to_mode} ({ts})")
        lines.append("")
        lines.append(brief)
        lines.append("")

    SYNTH_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Mode briefs written to: {OUTPUT_PATH.relative_to(BASE)} ({len(test_transitions)} transitions)")


if __name__ == "__main__":
    main()