"""Temporal Reasoning Layer - fleet state on a given date.
Usage: python memory/scribe/timeline.py --date YYYY-MM-DD
Returns JSON: active goals, recent events, agent states (no future events).
"""
import re, os, json, sys
from datetime import datetime

def parse_todo_sections():
    """Extract dated ## sections from TODO.md."""
    try:
        todo = open('TODO.md', encoding='utf-8', errors='replace').read()
    except FileNotFoundError:
        return []
    lines = todo.split('\n')
    sections = []
    current_title = None
    current_body = []
    for line in lines:
        m = re.match(r'^##\s+(.*)', line)
        if m:
            if current_title:
                sections.append((current_title, '\n'.join(current_body)))
            current_title = m.group(1)
            current_body = []
        elif current_title:
            current_body.append(line)
    if current_title:
        sections.append((current_title, '\n'.join(current_body)))
    dated = []
    for title, body in sections:
        m = re.search(r'(\d{4}-\d{2}-\d{2})', title)
        if m:
            d = datetime.strptime(m.group(1), '%Y-%m-%d').date()
            dated.append((d, title, body))
    dated.sort(key=lambda x: x[0], reverse=True)
    return dated

def get_agent_snapshots(target_date):
    """Find closest archive snapshot per agent that is <= target_date."""
    archive_dir = 'memory/goals/archive'
    if not os.path.exists(archive_dir):
        return {}
    snapshots = {}
    for f in os.listdir(archive_dir):
        m = re.match(r'^(\w+)-(\d{4}-\d{2}-\d{2})\.md$', f)
        if m:
            agent, d = m.group(1), datetime.strptime(m.group(2), '%Y-%m-%d').date()
            snapshots.setdefault(agent, []).append((d, f))
    result = {}
    for agent, snaps in snapshots.items():
        valid = [(d, f) for d, f in snaps if d <= target_date]
        if valid:
            valid.sort(reverse=True)
            result[agent] = valid[0]
    return result

def build_timeline(target_date):
    all_sections = parse_todo_sections()
    events = [{'date': d.isoformat(), 'title': title, 'preview': body[:200].strip()}
              for d, title, body in all_sections if d <= target_date][:10]
    agent_snaps = get_agent_snapshots(target_date)
    goal_files = sorted(f.replace('.md','') for f in os.listdir('memory/goals')
                        if re.match(r'^\w+\.md$', f))
    return {
        'date': target_date.isoformat(),
        'events': events,
        'agent_snapshots': {a: {'snapshot_date': d.isoformat(), 'file': f'memory/goals/archive/{f}'}
                            for a, (d, f) in sorted(agent_snaps.items())},
        'goal_files_available': goal_files,
    }

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Fleet state on a given date')
    parser.add_argument('--date', required=True, help='Target date YYYY-MM-DD')
    args = parser.parse_args()
    target = datetime.strptime(args.date, '%Y-%m-%d').date()
    print(json.dumps(build_timeline(target), indent=2))
