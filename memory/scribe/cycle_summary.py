"""Cycle Auto-Summary Generator (Scribe Goal #1).
At end of each cycle, auto-generate a structured summary:
- goals completed (by agent)
- blockers encountered + resolution time
- key decisions made
- open items carried forward
Output: memory/scribe/cycle-summary-<cycle>.md (<2KB for typical cycle)

Usage: python memory/scribe/cycle_summary.py [--cycle N] [--dry-run]
"""
import pathlib, re, json, sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).parent.parent.parent  # project root
GOALS_DIR = ROOT / "memory" / "goals"
SCRIBE_DIR = ROOT / "memory" / "scribe"
OPS_BLOCKERS = ROOT / "memory" / "ops" / "blockers.md"

def parse_goals(agent: str, text: str):
    """Extract goals with status from a goal file."""
    goals = []
    # Split by numbered goals
    for m in re.finditer(r'^(\d+)\. \*\*(.+?)\*\*', text, re.MULTILINE):
        num = int(m.group(1))
        title = m.group(2)
        # Find section until next goal or end
        start = m.start()
        nxt = re.search(rf'^{num+1}\. \*\*', text[m.end():], re.MULTILINE)
        section_end = m.end() + nxt.start() if nxt else len(text)
        section = text[start:section_end]
        reached = '[REACHED' in section
        # Extract timestamp if present
        ts_match = re.search(r'\[REACHED ([^\]]+)\]', section)
        ts = ts_match.group(1) if ts_match else None
        goals.append({"num": num, "title": title, "reached": reached, "ts": ts})
    return goals

def get_agents():
    """Find all agent goal files."""
    agents = {}
    for f in GOALS_DIR.glob("*.md"):
        name = f.stem
        if name.startswith(("cycle", "designer-", "researcher-", "mechanic-", 
                           "scribe-goal", "testy")) and not re.match(r'^[a-z]+$', name):
            continue
        # Only single-word agent names
        if re.match(r'^[a-z]+$', name):
            agents[name] = f
    return agents

def get_blockers(cycle_date: str = None):
    """Extract blockers from ops/blockers.md."""
    if not OPS_BLOCKERS.exists():
        return []
    text = OPS_BLOCKERS.read_text(encoding='utf-8')
    blockers = []
    # Look for OPS-NOTE entries or blocker sections
    for m in re.finditer(r'(?:###|##)\s+(.+?)(?=\n(?:###|##|\Z))', text, re.MULTILINE):
        section = m.group(0)
        if 'blocker' in section.lower() or 'OPS-NOTE' in section:
            blockers.append(section.strip()[:200])
    # Also look for simple bullet points with dates
    for line in text.split('\n'):
        if line.startswith('- ') and ('blocker' in line.lower() or 'BLOCKED' in line):
            blockers.append(line.strip()[:150])
    return blockers[:5]  # Cap at 5

def get_open_items(agent: str, goals: list):
    """Get open (not reached) goal titles."""
    return [g["title"] for g in goals if not g["reached"]]

def generate_summary(cycle_num: int = None):
    """Generate the cycle summary."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    agents = get_agents()
    
    completed = {}  # agent -> list of (num, title)
    open_items = {}  # agent -> list of titles
    
    for agent, f in sorted(agents.items()):
        text = f.read_text(encoding='utf-8')
        goals = parse_goals(agent, text)
        reached = [(g["num"], g["title"]) for g in goals if g["reached"]]
        open_g = get_open_items(agent, goals)
        if reached:
            completed[agent] = reached
        if open_g:
            open_items[agent] = open_g
    
    total_completed = sum(len(v) for v in completed.values())
    total_open = sum(len(v) for v in open_items.values())
    
    # Build markdown
    lines = [f"# Cycle Summary - {now}", ""]
    
    # Goals completed
    lines.append(f"## Completed ({total_completed} goals)")
    if completed:
        for agent, items in sorted(completed.items()):
            titles = ", ".join(f"#{n} {t}" for n, t in items[:5])
            more = f" +{len(items)-5} more" if len(items) > 5 else ""
            lines.append(f"- **{agent}**: {titles}{more}")
    else:
        lines.append("- (none this cycle)")
    lines.append("")
    
    # Blockers
    blockers = get_blockers()
    lines.append(f"## Blockers ({len(blockers)})")
    if blockers:
        for b in blockers:
            lines.append(f"- {b[:120]}")
    else:
        lines.append("- (none active)")
    lines.append("")
    
    # Open items carried forward
    lines.append(f"## Carried Forward ({total_open} open)")
    if open_items:
        for agent, items in sorted(open_items.items()):
            titles = ", ".join(items[:3])
            more = f" +{len(items)-3} more" if len(items) > 3 else ""
            lines.append(f"- **{agent}**: {titles}{more}")
    else:
        lines.append("- (all goals reached)")
    lines.append("")
    
    summary = "\n".join(lines)
    
    # Size check
    size = len(summary.encode('utf-8'))
    if size > 2048:
        # Trim: reduce open items to 2 per agent, blockers to 3
        lines2 = [f"# Cycle Summary - {now}", ""]
        lines2.append(f"## Completed ({total_completed})")
        for agent, items in sorted(completed.items()):
            titles = ", ".join(f"#{n} {t}" for n, t in items[:3])
            more = f"+{len(items)-3}" if len(items) > 3 else ""
            lines2.append(f"- {agent}: {titles}{more}")
        lines2.append("")
        lines2.append(f"## Blockers ({len(blockers)})")
        for b in blockers[:3]:
            lines2.append(f"- {b[:100]}")
        if not blockers:
            lines2.append("- none")
        lines2.append("")
        lines2.append(f"## Carried Forward ({total_open})")
        for agent, items in sorted(open_items.items()):
            titles = ", ".join(items[:2])
            more = f"+{len(items)-2}" if len(items) > 2 else ""
            lines2.append(f"- {agent}: {titles}{more}")
        summary = "\n".join(lines2)
    
    return summary, size

def main():
    dry_run = '--dry-run' in sys.argv
    cycle_arg = None
    if '--cycle' in sys.argv:
        idx = sys.argv.index('--cycle')
        if idx + 1 < len(sys.argv):
            cycle_arg = sys.argv[idx + 1]
    
    summary, size = generate_summary()
    
    print(summary)
    print(f"\n--- Size: {size} bytes ({'OK' if size <= 2048 else 'OVER LIMIT'}) ---")
    
    if not dry_run:
        out = SCRIBE_DIR / f"cycle-summary-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md"
        out.write_text(summary, encoding='utf-8')
        print(f"Written to: {out.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
