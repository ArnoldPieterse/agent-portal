#!/usr/bin/env python3
"""SLA metrics calculator for verification pipeline.

Computes: total goals, verified count, % verified, avg time-to-verify,
% within 24h, oldest unverified claim.

Usage:
    python memory/verifier/sla_metrics.py           # print + write JSON
    python memory/verifier/sla_metrics.py --json    # JSON only (for API)
"""
import re, os, json, sys
from datetime import datetime
from pathlib import Path

CYCLE_START = datetime(2026, 11, 18)  # cycle-5 start per TODO.md
AGENTS = ['builder','designer','mechanic','orchestrator','researcher','scribe','archivist','verifier']

def parse_goal_files():
    """Extract all goals with their verified: timestamps from goal files."""
    results = []
    goals_dir = Path('memory/goals')
    for f in sorted(goals_dir.glob('*.md')):
        if 'archive' in f.name or 'INDEX' in f.name or '-' == f.name[0]:
            continue
        agent = f.stem
        if agent not in AGENTS:
            continue
        text = f.read_text(encoding='utf-8', errors='replace')
        lines = text.split('\n')
        for i, line in enumerate(lines):
            m = re.match(r'^(\d+)\.\s+\*\*(.+?)\*\*', line.strip())
            if not m:
                continue
            goal_num = int(m.group(1))
            goal_title = m.group(2)
            block = ' '.join(lines[i:i+3])
            vm = re.search(r'verified:\s*(\d{4}-\d{2}-\d{2})', block)
            results.append({
                'agent': agent,
                'goal_num': goal_num,
                'title': goal_title,
                'verified_date': vm.group(1) if vm else None,
                'verified': bool(vm)
            })
    return results

def compute_sla(goals):
    """Compute SLA metrics from goal data."""
    verified = [g for g in goals if g['verified']]
    unverified = [g for g in goals if not g['verified']]

    times_hours = []
    within_24h = 0
    for g in verified:
        try:
            v_date = datetime.strptime(g['verified_date'], '%Y-%m-%d')
            delta_h = (v_date - CYCLE_START).total_seconds() / 3600
            times_hours.append(delta_h)
            if delta_h <= 24:
                within_24h += 1
        except ValueError:
            pass

    avg_time = sum(times_hours) / len(times_hours) if times_hours else None
    oldest_unverified = min(unverified, key=lambda g: (g['agent'], g['goal_num'])) if unverified else None

    return {
        'total_goals': len(goals),
        'verified_count': len(verified),
        'unverified_count': len(unverified),
        'pct_verified': round(100 * len(verified) / len(goals), 1) if goals else 0,
        'avg_time_to_verify_hours': round(avg_time, 1) if avg_time is not None else None,
        'pct_within_24h': round(100 * within_24h / len(verified), 1) if verified else 0,
        'oldest_unverified': {
            'agent': oldest_unverified['agent'],
            'goal_num': oldest_unverified['goal_num'],
            'title': oldest_unverified['title'][:80]
        } if oldest_unverified else None,
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M')
    }

if __name__ == '__main__':
    json_only = '--json' in sys.argv
    goals = parse_goal_files()
    sla = compute_sla(goals)
    out_json = json.dumps(sla, indent=2)

    if json_only:
        print(out_json)
    else:
        print("=" * 50)
        print("VERIFICATION SLA METRICS")
        print(f"  Generated: {sla['generated_at']}")
        print("=" * 50)
        print(f"  Total goals:       {sla['total_goals']}")
        print(f"  Verified:          {sla['verified_count']} ({sla['pct_verified']}%)")
        print(f"  Unverified:        {sla['unverified_count']}")
        print(f"  Avg time to verify: {sla['avg_time_to_verify_hours']}h")
        print(f"  Within 24h:        {sla['pct_within_24h']}%")
        if sla['oldest_unverified']:
            ou = sla['oldest_unverified']
            print(f"  Oldest unverified:   {ou['agent']}#{ou['goal_num']} - {ou['title']}")
        print("=" * 50)

    out_path = Path('memory/verifier/sla_metrics.json')
    out_path.write_text(out_json, encoding='utf-8')
