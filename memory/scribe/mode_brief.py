#!/usr/bin/env python3
"""mode_brief.py — auto-generate mode decision briefs for each fleet-mode transition.

Reads memory/ops/mode-transitions.jsonl; appends new briefs to memory/ops/mode-briefs.md (newest first).
Idempotent: skips transitions already briefed (matched by timestamp in the file).

Usage: python memory/scribe/mode_brief.py [--simulate N]
"""
import json, sys, datetime, pathlib, re

TRANSITIONS = pathlib.Path("memory/ops/mode-transitions.jsonl")
BRIEFS      = pathlib.Path("memory/ops/mode-briefs.md")

MODE_DESCRIPTIONS = {
    "WORK": "active goal-pursuit mode where all agents work their open goals",
    "MAINTENANCE": "maintenance mode where agents perform scheduled upkeep tasks instead of new goals",
    "IDLE": "standby mode where no tasks are dispatched and agents await the next cycle",
}

TRIGGER_EXPLANATIONS = {
    "cycle_closeout": "the current work cycle completed its closeout sequence",
    "new_cycle_start": "a new work cycle was initiated with fresh goals",
    "goal_pct_threshold": "the goal-completion percentage crossed the configured threshold",
}


def _load_jsonl(path):
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out


def _explain_trigger(trigger, goal_pct):
    """Return a plain-English explanation of the trigger."""
    if trigger in TRIGGER_EXPLANATIONS:
        return TRIGGER_EXPLANATIONS[trigger]
    # Fallback: parse composite triggers like "goal_pct=30.0,elapsed=0.01h"
    if "=" in trigger and "," in trigger:
        parts = [p.strip() for p in trigger.split(",")]
        desc_parts = []
        for p in parts:
            k, v = p.split("=", 1)
            if k == "goal_pct":
                desc_parts.append(f"goal completion at {v}%")
            elif k == "elapsed":
                desc_parts.append(f"elapsed time {v}")
            else:
                desc_parts.append(f"{k}={v}")
        return " and ".join(desc_parts) + " met the transition criteria"
    return f"the trigger condition \'{trigger}\' was satisfied"


def generate_brief(t):
    """Generate a 4-6 sentence brief for one transition."""
    ts   = t.get("ts", "unknown time")
    frm  = t.get("from_mode", "UNKNOWN")
    to   = t.get("to_mode", "UNKNOWN")
    trig = t.get("trigger", "unspecified")
    pct  = t.get("goal_pct", None)

    s1 = f"At {ts}, the fleet transitioned from {frm} to {to}."
    
    if pct is not None:
        s2 = f"At the time of the change, {pct:.1f}% of tracked goals were complete."
    else:
        s2 = "Goal completion data was not available at the time of transition."

    s3 = f"The trigger was: {_explain_trigger(trig, pct)}."
    
    to_desc = MODE_DESCRIPTIONS.get(to, f"the {to} mode")
    s4 = f"The fleet will remain in {to} ({to_desc}) until the next transition condition is met."

    if to == "WORK":
        s5 = "All agents will resume working their open goals from the next10.json dispatch queue on the next pass cycle."
    elif to == "MAINTENANCE":
        s5 = "Agents will switch to role-specific maintenance tasks from the idle-rotation table; new goal work is paused until re-entry to WORK mode."
    else:
        s5 = "All agents enter standby; no dispatch occurs until a new cycle or explicit wake triggers re-entry."

    return f"## Transition: {frm} \u2192 {to} ({ts})\n\n{s1} {s2} {s3} {s4} {s5}"


def main():
    simulate_n = 0
    if "--simulate" in sys.argv:
        idx = sys.argv.index("--simulate")
        if idx + 1 < len(sys.argv):
            simulate_n = int(sys.argv[idx + 1])

    transitions = _load_jsonl(TRANSITIONS)

    # Load existing briefs to check which timestamps are already covered
    existing_content = BRIEFS.read_text(encoding="utf-8") if BRIEFS.exists() else "# Mode Decision Briefs\n"
    briefed_ts = set(re.findall(r"\(([^)]*\d{4}-\d{2}-\d{2}T[^) ]+)\)", existing_content))

    new_briefs = []
    for t in transitions:
        ts = t.get("ts", "")
        if ts not in briefed_ts:
            new_briefs.append(generate_brief(t))

    if new_briefs:
        # Insert newest first (after header)
        header_end = existing_content.find("\n\n") + 2 if "\n\n" in existing_content else len(existing_content)
        insertion = "\n".join(new_briefs) + "\n"
        existing_content = existing_content[:header_end] + insertion + existing_content[header_end:]
        BRIEFS.write_text(existing_content, encoding="utf-8")
        print(f"[mode_brief] wrote {len(new_briefs)} new brief(s) to {BRIEFS}")
    else:
        print("[mode_brief] all transitions already briefed")

    # Summary
    all_briefs = re.findall(r"^## Transition:", existing_content, re.MULTILINE)
    print(f"Total briefs on file: {len(all_briefs)}")


if __name__ == "__main__":
    main()
