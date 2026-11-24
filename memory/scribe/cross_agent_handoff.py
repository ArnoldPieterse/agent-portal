#!/usr/bin/env python3
"""Cross-Agent Handoff Summary Generator (Scribe goal #6, cycle 15).

When goals re-route between seats (due to unavailability), generates a context
summary for the receiving agent: what the goal was, prior progress, key files
involved, suggested first step.

Usage: python memory/scribe/hross_agent_handoff.py [--test]
Output: memory/handoffs/{date}-{from}-{to}.md (one file per re-route event)
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
HANDOFFS_DIR = BASE / "memory" / "handoffs"
GOALS_DIR = BASE / "memory" / "goals"


def load_agent_goals(agent: str) -> list[dict]:
    """Load an agent's open goals from their goals file."""
    goals_file = GOALS_DIR / f"{agent}.md"
    if not goals_file.exists():
        return []
    content = goals_file.read_text(encoding="utf-8")
    goals = []
    for line in content.split("\n"):
        # Match numbered goal lines that are NOT marked reached/closed
        import re
        m = re.match(r"^(\d+)\.\s+\*\*(.+?)\*\*", line)
        if m and "REACHED" not in line and "CLOSED" not in line:
            goals.append({"num": int(m.group(1)), "title": m.group(2), "text": line.strip()})
    return goals


def find_key_files(goal_text: str) -> list[str]:
    """Extract file paths mentioned in a goal's text."""
    import re
    paths = re.findall(r"`([^`]+\.py)`|`([^`]+\.md)`|`([^`]+\.json)`", goal_text)
    files = [p[0] or p[1] or p[2] for p in paths if any(p)]
    # Also look for memory/ paths without backticks
    mem_paths = re.findall(r"memory/[\w/\-]+\.[a-z]+", goal_text)
    files.extend(mem_paths)
    return list(dict.fromkeys(files))  # dedupe, preserve order


def generate_handoff(goal: dict, from_agent: str, to_agent: str, reason: str = "unavailability") -> str:
    """Generate a handoff summary for one goal being re-routed."""
    title = goal["title"]
    text = goal["text"]
    key_files = find_key_files(text)
    
    # Suggested first step based on goal type
    if "script" in text.lower() or ".py" in text:
        first_step = f"Read the existing script (if any) and run it to check current state before making changes."
    elif "write" in text.lower() or "memory/" in text:
        first_step = f"Check if the target file already exists; if so, read it to understand prior progress before extending."
    else:
        first_step = f"Read the goal text carefully and identify the primary deliverable; create a skeleton if none exists."
    
    lines = [
        f"### Goal {goal['num']}: {title}",
        "",
        f"**From:** {from_agent}  ",
        f"**To:** {to_agent}  ",
        f"**Reason:** {reason}  ",
        f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "",
        "**Goal text:**",
        f"> {text[:300]}",
        "",
        "**Key files:**",
    ]
    if key_files:
        for f in key_files:
            lines.append(f"- `{f}`")
    else:
        lines.append("- (none explicitly referenced)")
    
    lines += [
        "",
        "**Suggested first step:**",
        f"{first_step}",
        "",
    ]
    return "\n".join(lines)


def write_handoff_file(from_agent: str, to_agent: str, goals: list[dict], reason: str = "unavailability") -> Path:
    """Write a handoff file for a batch of re-routed goals."""
    HANDOFFS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"{date_str}-{from_agent}-{to_agent}.md"
    filepath = HANDOFFS_DIR / filename
    
    header = [
        f"# Handoff: {from_agent} → {to_agent}",
        "",
        f"*Generated {datetime.now(timezone.utc).isoformat()} | Reason: {reason}*  ",
        f"*Goals re-routed: {len(goals)}*",
        "",
    ]
    
    body_parts = [generate_handoff(g, from_agent, to_agent, reason) for g in goals]
    
    filepath.write_text("\n".join(header + ["\n---\n\n"] + ["\n---\n\n".join(body_parts)]), encoding="utf-8")
    return filepath


def main():
    test_mode = "--test" in sys.argv
    
    if test_mode:
        # Simulate re-route of 2 goals from researcher to builder
        simulated_goals = [
            {"num": 1, "title": "Productivity Baseline Measurement",
             "text": "1. **Productivity Baseline Measurement** - `python memory/researcher/idle_productivity.py`: measure per-agent productive-pass rate over last 24h (file changes / total passes from autoloop.jsonl). Write to memory/ops/productivity-baseline.json."},
            {"num": 3, "title": "Mode Duration Tracker",
             "text": "3. **Mode Duration Tracker** - `python memory/researcher/mode_duration.py`: read mode-transitions.jsonl; compute time spent in each mode over last 7 days. Write to memory/ops/mode-durations.json."},
        ]
        from_agent = "researcher"
        to_agent = "builder"
        reason = "model_unavailable (home not_loaded, relocated)"
    else:
        # In production, this would be called by the seat router with actual re-route data
        print("Production mode: pass --from <agent> --to <agent> --goals <n1,n2,...>")
        if "--from" in sys.argv and "--to" in sys.argv:
            from_agent = sys.argv[sys.argv.index("--from") + 1]
            to_agent = sys.argv[sys.argv.index("--to") + 1]
            goals = load_agent_goals(from_agent)
            if not goals:
                print(f"No open goals found for {from_agent}")
                return
        else:
            return
    
    filepath = write_handoff_file(from_agent, to_agent, simulated_goals if test_mode else goals, reason)
    
    # Verification
    content = filepath.read_text(encoding="utf-8")
    n_briefs = content.count("### Goal ")
    has_from = from_agent in content
    has_to = to_agent in content
    
    print(f"Handoff written: {filepath.relative_to(BASE)}")
    print(f"  Goals in handoff: {n_briefs}")
    print(f"  Cites source agent ({from_agent}): {has_from}")
    print(f"  Cites receiving agent ({to_agent}): {has_to}")
    
    if n_briefs >= 2 and has_from and has_to:
        print("  VERIFICATION PASSED")
    else:
        print("  VERIFICATION FAILED")


if __name__ == "__main__":
    main()
