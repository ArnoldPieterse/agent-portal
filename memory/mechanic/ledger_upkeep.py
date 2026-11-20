"""Regenerate mechanic's entry in goal-ledger-current.json from the live goals file."""
import json, re, datetime, os

goals_file = 'memory/goals/mechanic.md'
ledger_file = 'memory/mechanic/goal-ledger-current.json'

text = open(goals_file, encoding='utf-8').read()

# Parse numbered goals (each starts with N. **Title**)
goals = []
current = None
for line in text.split('\n'):
    m = re.match(r'^(\d+)\.\s+\*\*(.+?)\*\*', line)
    if m:
        if current:
            goals.append(current)
        current = {'num': int(m.group(1)), 'title': m.group(2), 'text': line.strip()}
    elif current and line.strip():
        current['text'] += '\n' + line.strip()
if current:
    goals.append(current)

for g in goals:
    t = g['text']
    if '(verified:' in t:
        g['status'] = 'reached'
    else:
        g['status'] = 'open'

reached = sum(1 for g in goals if g['status'] == 'reached')
open_count = len(goals) - reached

# Load existing ledger
ledger = json.load(open(ledger_file, encoding='utf-8'))

# Update mechanic entry
ledger['agents']['mechanic'] = {
    'file': goals_file.replace('\\', '\\'),
    'total': len(goals),
    'reached': reached,
    'claimed_only': 0,
    'open': open_count,
    'pct_reached': round(100 * reached / len(goals)) if goals else 0,
    'goals': [
        {
            'text': g['text'][:500] + ('...' if len(g['text']) > 500 else ''),
            'status': g['status'],
            'checked': False,
            'evidence': g['status'] == 'reached',
            'form': 'numbered',
            'evidence_via': 'marker' if g['status'] == 'reached' else None
        }
        for g in goals
    ],
    'next_cycle_carry_forward': []
}

# Update fleet totals
all_agents = ledger['agents']
fleet_total = sum(a['total'] for a in all_agents.values())
fleet_reached = sum(a['reached'] for a in all_agents.values())
ledger['fleet_total_goals'] = fleet_total
ledger['fleet_reached'] = fleet_reached
ledger['fleet_pct_reached'] = round(100 * fleet_reached / fleet_total) if fleet_total else 0
ledger['generated'] = datetime.date.today().isoformat()

json.dump(ledger, open(ledger_file, 'w', encoding='utf-8'), indent=2)
print(f'Updated {ledger_file}')
print(f'Mechanic: {reached}/{len(goals)} reached ({open_count} open)')
for g in goals:
    print(f"  [{g['status']:8}] {g['num']}. {g['title'][:70]}")
print(f'Fleet: {fleet_reached}/{fleet_total} ({ledger["fleet_pct_reached"]}%)')
