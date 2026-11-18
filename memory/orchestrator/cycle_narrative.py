#!/usr/bin/env python3
"""Cycle Narrative Auto-Generator (Orchestrator Goal #10, cycle-5).

Usage: python memory/orchestrator/cycle_narrative.py --cycle N

Parses goal files for cycle N (from archive + current), counts goals set/closed,
identifies key wins and slippage, then appends a 2-paragraph narrative to
memory/synthesis/cycle-narrative.md.
"""

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # project root
GOALS_DIR = ROOT / "memory" / "goals"
ARCHIVE_DIR = GOALS_DIR / "archive"
SYNTHESIS_FILE = ROOT / "memory" / "synthesis" / "cycle-narrative.md"

AGENTS = ["orchestrator", "researcher", "builder", "verifier",
          "designer", "archivist", "scribe", "mechanic"]

# Cycle-to-date mapping (inferred from file headers)
CYCLE_DATE_HINTS = {
    1: ["2026-11-13"],
    2: ["2026-11-16"],
    3: ["2026-11-17", "2026-11-18"],
    4: ["2026-11-17", "2026-11-18"],  # cycle-4 draft also dated 11-17/18
    5: ["2026-11-18"],
}


def extract_cycle_from_header(text: str) -> int | None:
    """Try to extract explicit cycle number from file header."""
    m = re.search(r'cycle[-\s]*(\d+)', text[:300], re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def infer_cycle_from_date(date_str: str) -> int | None:
    """Map a date string to a cycle number using known hints."""
    for cycle, dates in CYCLE_DATE_HINTS.items():
        if date_str in dates:
            return cycle
    return None


def find_goal_files_for_cycle(cycle: int) -> list[tuple[str, Path]]:
    """Find all goal files belonging to the given cycle.
    
    Returns list of (agent_name, filepath) tuples.
    """
    results = []
    seen_agents = set()

    # 1. Check archive files
    if ARCHIVE_DIR.is_dir():
        for fname in sorted(ARCHIVE_DIR.iterdir()):
            if not fname.name.endswith(".md"):
                continue
            # Match pattern: <agent>-<date>.md
            m = re.match(r"^(\w+)-2026-(\d{2})-(\d{2})\.md$", fname.name)
            if not m:
                continue
            agent = m.group(1).lower()
            if agent not in AGENTS:
                continue

            with open(fname, encoding="utf-8", errors="replace") as f:
                header = f.read(500)

            # Explicit cycle in header takes precedence
            explicit_cycle = extract_cycle_from_header(header)
            if explicit_cycle is not None:
                if explicit_cycle == cycle and agent not in seen_agents:
                    results.append((agent, fname))
                    seen_agents.add(agent)
                continue  # Don't fall through to date inference

            # Date-based inference (only when no explicit cycle in header)
            date_str = f"2026-{m.group(2)}-{m.group(3)}"
            inferred = infer_cycle_from_date(date_str)
            if inferred == cycle and agent not in seen_agents:
                results.append((agent, fname))
                seen_agents.add(agent)

    # 2. Check current goal files (for active or recently-completed cycles)
    for agent in AGENTS:
        if agent in seen_agents:
            continue
        fp = GOALS_DIR / f"{agent}.md"
        if not fp.exists():
            continue
        with open(fp, encoding="utf-8", errors="replace") as f:
            header = f.read(500)
        explicit_cycle = extract_cycle_from_header(header)
        if explicit_cycle == cycle:
            results.append((agent, fp))

    return results


def parse_goals(filepath: Path) -> dict:
    """Parse a goal file and return stats."""
    with open(filepath, encoding="utf-8", errors="replace") as f:
        text = f.read()

    # Find numbered goals — flexible: matches both "N. **Title**" and "N. Title - desc"
    # Must start at beginning of line (after optional whitespace)
    goal_pattern = re.compile(r"^\s*(\d+)\.\s+(.+?)(?=^\s*\d+\.\s|\Z)", re.MULTILINE | re.DOTALL)
    goals = []
    for m in goal_pattern.finditer(text):
        num = int(m.group(1))
        block = m.group(2).strip()

        # Extract title: first line, strip bold markers if present
        first_line = block.split('\n')[0].strip()
        bm = re.match(r"\*\*(.+?)\*\*", first_line)
        title = bm.group(1).strip() if bm else first_line[:80]

        # Check if verified (has a "verified:" marker in the block)
        verified = bool(re.search(r"\(verified:", block))
        verified_note = ""
        vm = re.search(r"\(verified:\s*([^)]+)\)", block)
        if vm:
            verified_note = vm.group(1).strip()[:120]

        # Skip background-scheduled items (they're not really "open")
        is_bg = bool(re.match(r"\[BG-SCHED", first_line))

        goals.append({
            "num": num,
            "title": title,
            "verified": verified,
            "note": verified_note,
            "background": is_bg,
        })

    # Count: background items count as closed (moved, not failed)
    total = len(goals)
    closed = sum(1 for g in goals if g["verified"] or g["background"])
    open_count = sum(1 for g in goals if not g["verified"] and not g["background"])

    return {
        "total": total,
        "closed": closed,
        "open": open_count,
        "goals": goals,
    }


def generate_narrative(cycle: int, agent_data: dict[str, dict]) -> str:
    """Generate a 2-paragraph narrative for the given cycle."""
    total_goals = sum(d["total"] for d in agent_data.values())
    total_closed = sum(d["closed"] for d in agent_data.values())
    total_open = sum(d["open"] for d in agent_data.values())
    pct = (total_closed / total_goals * 100) if total_goals else 0

    # Paragraph 1: overview + key wins
    p1_parts = []
    p1_parts.append(
        f"Cycle {cycle}: {len(agent_data)} agents \u00d7 {total_goals // max(len(agent_data), 1)} goals each "
        f"({total_goals} total). {total_closed} closed ({pct:.0f}%), {total_open} open."
    )

    # Pick top 3 key wins (verified goals with notes)
    wins = []
    for agent, data in agent_data.items():
        for g in data["goals"]:
            if g["verified"] and g["note"]:
                wins.append((agent, g))
    # Sort by agent name for determinism, take first 3
    wins.sort(key=lambda x: (x[0], x[1]["num"]))
    if wins:
        win_strs = []
        for agent, g in wins[:3]:
            note_short = g["note"][:80]
            win_strs.append(f"{agent} #{g['num']} ({note_short})")
        p1_parts.append("Key wins: " + "; ".join(win_strs) + ".")

    # Paragraph 2: slippage + next-cycle focus
    p2_parts = []
    if total_open > 0:
        open_by_agent = {}
        for agent, data in agent_data.items():
            if data["open"] > 0:
                open_by_agent[agent] = data["open"]
        slip_strs = [f"{a} ({n})" for a, n in sorted(open_by_agent.items())]
        p2_parts.append(
            f"Slippage into next cycle: {total_open} goals remain open \u2014 "
            + ", ".join(slip_strs) + "."
        )
    else:
        p2_parts.append("No slippage: all goals closed within the cycle window.")

    # Next-cycle focus hint
    next_cycle = cycle + 1
    p2_parts.append(
        f"Cycle {next_cycle} should prioritize closing the remaining "
        f"{total_open} open goal(s) and any date-gated background items."
        if total_open > 0 else
        f"Cycle {next_cycle} focus: new features per ratified goal-set."
    )

    return p1_parts[0] + " " + (p1_parts[1] if len(p1_parts) > 1 else "") + "\n\n" + " ".join(p2_parts)


def main():
    parser = argparse.ArgumentParser(description="Generate cycle narrative")
    parser.add_argument("--cycle", type=int, required=True, help="Cycle number")
    parser.add_argument("--dry-run", action="store_true", help="Print narrative without writing")
    args = parser.parse_args()

    cycle = args.cycle
    print(f"[cycle_narrative] Generating narrative for cycle {cycle}...")

    # Find files
    files = find_goal_files_for_cycle(cycle)
    if not files:
        print(f"[cycle_narrative] WARNING: No goal files found for cycle {cycle}")
        sys.exit(1)

    print(f"[cycle_narrative] Found {len(files)} agent files:")
    for agent, fp in files:
        print(f"  {agent}: {fp.name}")

    # Parse each
    agent_data = {}
    for agent, fp in files:
        data = parse_goals(fp)
        agent_data[agent] = data
        status = "ALL CLOSED" if data["open"] == 0 else f"{data['open']} open"
        print(f"  {agent}: {data['closed']}/{data['total']} closed ({status})")

    # Generate narrative
    narrative = generate_narrative(cycle, agent_data)
    print(f"\n=== NARRATIVE ===\n{narrative}\n=================")

    if args.dry_run:
        print("[cycle_narrative] Dry run \u2014 not writing.")
        return

    # Append to synthesis file
    SYNTHESIS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SYNTHESIS_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n## Cycle {cycle} (auto-generated {date.today().isoformat()})\n{narrative}\n")

    print(f"[cycle_narrative] Appended to {SYNTHESIS_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
