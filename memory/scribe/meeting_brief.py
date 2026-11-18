#!/usr/bin/env python3
"""Pre-Meeting Brief Generator (Scribe goal #9).

Usage: python memory/scribe/meeting_brief.py [--output PATH] [--decisions N]

Generates a 1-page brief from current fleet state:
  1. Open goals per agent (from memory/goals/*.md)
  2. Active blockers (from memory/ops/blockers.md, unresolved only)
  3. Recent decisions (from memory/scribe/decision_log.md)
  4. Proposed agenda items (derived from above)

Acceptance: script runs; brief includes all 4 sections; <=1 page when printed (~55 lines).
"""
import os, re, sys
from datetime import datetime


def parse_goals(agent_file):
    """Parse a goal file, return list of {num, title, open}."""
    goals = []
    with open(agent_file, 'r', encoding='utf-8') as f:
        content = f.read()

    for m in re.finditer(r'^(\d+)\.\s+\*\*(.+?)\*\*', content, re.MULTILINE):
        num = int(m.group(1))
        title = m.group(2)
        # Get the block for this goal (until next numbered goal or EOF)
        start = m.start()
        rest = content[m.end():]
        next_match = re.search(r'^\d+\.\s+\*\*', rest, re.MULTILINE)
        if next_match:
            block = content[start:start + (m.end() - start) + next_match.start()]
        else:
            block = content[start:]

        is_verified = '(verified:' in block.lower() or '(VERIFIED:' in block
        goals.append({'num': num, 'title': title, 'open': not is_verified})
    return goals


def parse_blockers():
    """Parse unresolved blockers from memory/ops/blockers.md."""
    path = 'memory/ops/blockers.md'
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    blockers = []
    sections = re.split(r'\n## ', content)
    for section in sections[1:]:
        if '[RESOLVED' not in section[:60]:
            title_line = section.split('\n')[0].strip()
            blockers.append(title_line)
    return blockers


def parse_recent_decisions(n=5):
    """Get the n most recent decisions from decision_log.md."""
    path = 'memory/scribe/decision_log.md'
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    entries = []
    for m in re.finditer(r'## (D-\d+)\s*\|\s*(\d{4}-\d{2}-\d{2})\n(.*?)(?=\n## |\Z)', content, re.DOTALL):
        id_ = m.group(1)
        date = m.group(2)
        body = m.group(3)
        dec_match = re.search(r'\*\*decision\*\*:\s*(.+)', body)
        decision_text = dec_match.group(1).strip() if dec_match else ''
        entries.append({'id': id_, 'date': date, 'decision': decision_text})

    entries.sort(key=lambda x: x['date'], reverse=True)
    return entries[:n]


def generate_brief(decisions_n=5):
    """Generate the pre-meeting brief as a string."""
    today = datetime.now().strftime('%Y-%m-%d')

    # 1. Open goals per agent
    agents_dir = 'memory/goals'
    open_goals_by_agent = {}
    total_open = 0
    total_all = 0

    if os.path.exists(agents_dir):
        for f in sorted(os.listdir(agents_dir)):
            if f.endswith('.md') and not f.startswith(('scheduled', 'archive', 'INDEX')):
                agent = f.replace('.md', '')
                goals = parse_goals(os.path.join(agents_dir, f))
                open_g = [g for g in goals if g['open']]
                open_goals_by_agent[agent] = open_g
                total_open += len(open_g)
                total_all += len(goals)

    # 2. Blockers
    blockers = parse_blockers()

    # 3. Recent decisions
    decisions = parse_recent_decisions(decisions_n)

    # 4. Proposed agenda items
    agenda = []
    if total_open > 0:
        active_agents = [a for a, g in open_goals_by_agent.items() if g]
        agenda.append(f"Review {total_open} open goals across {len(active_agents)} agents")
    for b in blockers[:3]:
        agenda.append(f"Blocker: {b[:80]}")
    sorted_agents = sorted(open_goals_by_agent.items(), key=lambda x: len(x[1]), reverse=True)
    if sorted_agents and sorted_agents[0][1]:
        top_agent, top_goals = sorted_agents[0]
        agenda.append(f"Priority lane: {top_agent} ({len(top_goals)} open)")

    # Build output (keep <= 55 lines for 1 page)
    lines = []
    lines.append(f"# Pre-Meeting Brief | {today}")
    lines.append("")
    lines.append("## 1. Open Goals")
    lines.append(f"Total: {total_open}/{total_all} open across {len(open_goals_by_agent)} agents")
    for agent, goals in sorted_agents[:5]:
        if goals:
            titles = ', '.join(g['title'][:40] for g in goals[:3])
            more = f" +{len(goals)-3}" if len(goals) > 3 else ""
            lines.append(f"  - **{agent}** ({len(goals)} open): {titles}{more}")
    lines.append("")

    lines.append("## 2. Active Blockers")
    if blockers:
        for b in blockers[:5]:
            lines.append(f"  - {b[:100]}")
    else:
        lines.append("  None active.")
    lines.append("")

    lines.append("## 3. Recent Decisions")
    for d in decisions:
        lines.append(f"  - [{d['id']} {d['date']}] {d['decision'][:90]}")
    lines.append("")

    lines.append("## 4. Proposed Agenda")
    if agenda:
        for i, item in enumerate(agenda[:6], 1):
            lines.append(f"  {i}. {item}")
    else:
        lines.append("  No items - all goals closed.")
    lines.append("")

    return '\n'.join(lines)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Generate pre-meeting brief')
    parser.add_argument('--output', default='memory/scribe/meeting-brief-latest.md',
                        help='Output file path')
    parser.add_argument('--decisions', type=int, default=5,
                        help='Number of recent decisions to include')
    args = parser.parse_args()

    brief = generate_brief(args.decisions)
    print(brief)

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(brief)
    line_count = brief.count('\n') + 1
    status = 'OK' if line_count <= 55 else 'TOO LONG'
    print(f"\n[written to {args.output}] [lines: {line_count} {status}]", file=sys.stderr)
