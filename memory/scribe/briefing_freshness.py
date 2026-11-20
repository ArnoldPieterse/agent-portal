#!/usr/bin/env python3
"""
Briefing Freshness Monitor (Scribe Goal #3, cycle-8)

Checks all files in memory/scribe/briefings/ against current memory/goals/<agent>.md.
Flags briefings that reference a goal no longer active or miss a newly-added goal.

Output (stdout JSON): [{agent, stale_items[], missing_items[], last_updated}]
"""
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

BRIEFINGS_DIR = Path("memory/scribe/briefings")
GOALS_DIR = Path("memory/goals")

# Known agent names (8 seats)
AGENTS = ["orchestrator", "researcher", "builder", "verifier",
          "designer", "archivist", "mechanic", "scribe"]


def extract_briefing_goals(briefing_text: str) -> list[str]:
    """Extract goal titles from the '## Open Goals' section of a briefing."""
    # Find the Open Goals section
    m = re.search(r'## Open Goals \(\d+\)\s*\n(.*?)(?=\n## |\Z)', briefing_text, re.DOTALL)
    if not m:
        return []
    section = m.group(1)
    # Extract bold titles: - **Goal Title**
    goals = re.findall(r'-\s*\*\*(.+?)\*\*', section)
    return [g.strip() for g in goals if g.strip()]


def extract_active_goals(goals_text: str) -> list[dict]:
    """Extract active (non-verified) goals from a goals file.
    
    Returns list of {number, title} for goals NOT marked as verified.
    A goal is considered verified if its line contains '(verified:' or '(verified :'.
    """
    goals = []
    # Match numbered goals: N. **Title** - description...
    for m in re.finditer(r'^(\d+)\.\s*\*\*(.+?)\*\*', goals_text, re.MULTILINE):
        num = int(m.group(1))
        title = m.group(2).strip()
        # Get the full line/paragraph to check for verified marker
        # Find the end of this goal entry (next numbered goal or end)
        start = m.start()
        next_m = re.search(r'\n\d+\.\s*\*\*', goals_text[m.end():])
        if next_m:
            end = m.end() + next_m.start()
        else:
            end = len(goals_text)
        entry_text = goals_text[start:end]
        # Check if verified
        is_verified = bool(re.search(r'\(verified[:\s]', entry_text))
        if not is_verified:
            goals.append({"number": num, "title": title})
    return goals


def normalize_title(title: str) -> str:
    """Normalize a goal title for fuzzy matching."""
    # Lowercase, remove punctuation, collapse whitespace
    t = title.lower().strip()
    t = re.sub(r'[^a-z0-9\s]', '', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()


def titles_match(briefing_title: str, goal_title: str) -> bool:
    """Check if a briefing goal title matches a goals-file title.
    
    Briefings may truncate titles, so we check if one is a prefix of the other
    or if they share significant overlap.
    """
    bt = normalize_title(briefing_title)
    gt = normalize_title(goal_title)
    if not bt or not gt:
        return False
    # Exact match
    if bt == gt:
        return True
    # Prefix match (briefing may truncate)
    if bt.startswith(gt) or gt.startswith(bt):
        return True
    # Significant overlap: >= 60% of the shorter title's words appear in the longer
    bt_words = set(bt.split())
    gt_words = set(gt.split())
    if not bt_words or not gt_words:
        return False
    overlap = len(bt_words & gt_words)
    shorter = min(len(bt_words), len(gt_words))
    if shorter > 0 and overlap / shorter >= 0.6:
        return True
    return False


def get_file_mtime(path: Path) -> str:
    """Get file modification time as ISO string, or 'unknown' if not found."""
    if path.exists():
        mt = path.stat().st_mtime
        return datetime.fromtimestamp(mt).strftime("%Y-%m-%d %H:%M")
    return "unknown"


def check_agent(agent: str) -> dict:
    """Check freshness of one agent's briefing against their goals file."""
    briefing_path = BRIEFINGS_DIR / f"{agent}-briefing.md"
    goals_path = GOALS_DIR / f"{agent}.md"
    
    result = {
        "agent": agent,
        "stale_items": [],
        "missing_items": [],
        "last_updated": get_file_mtime(briefing_path)
    }
    
    if not briefing_path.exists():
        result["error"] = f"briefing file not found: {briefing_path}"
        return result
    
    if not goals_path.exists():
        result["error"] = f"goals file not found: {goals_path}"
        return result
    
    briefing_text = briefing_path.read_text(encoding="utf-8", errors="replace")
    goals_text = goals_path.read_text(encoding="utf-8", errors="replace")
    
    # Extract goal titles from both sources
    briefing_goals = extract_briefing_goals(briefing_text)
    active_goals = extract_active_goals(goals_text)
    
    # Find stale items: in briefing but no longer in active goals
    for bg in briefing_goals:
        matched = any(titles_match(bg, ag["title"]) for ag in active_goals)
        if not matched:
            result["stale_items"].append(bg)
    
    # Find missing items: in active goals but not in briefing
    for ag in active_goals:
        matched = any(titles_match(ag["title"], bg) for bg in briefing_goals)
        if not matched:
            result["missing_items"].append(f"{ag['number']}. {ag['title']}")
    
    return result


def main():
    results = []
    for agent in AGENTS:
        results.append(check_agent(agent))
    
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
