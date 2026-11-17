"""Scribe #7 - Owner-coverage ledger v2: scan TODO.md for unowned items, suggest owners.
Usage: python memory/scribe/owner_coverage_check.py [--json]
Outputs coverage stats + unowned items with suggested owners.
"""
import os, re, sys, json
from datetime import datetime

ROSTER = ['Orchestrator','Researcher','Builder','Verifier','Designer','Archivist','Mechanic','Scribe']

# Reuse the same signal table as round_record_draft.py
OWNER_SIGNALS = {
    'Orchestrator': ['goal-cycle', 'fleet rule', 'fleet to adopt', 'onboard', 'TODO.md prune',
                     'sequential pass', 'parallel dispatch', 'decision needed (human)',
                     'cycle-2 work', 'decide seams', 'split pending', 'importable entry'],
    'Researcher': ['research', 'source check', 'cross-check', 'confidence', 'web_search',
                   'citation', 'archive', 'ledger sweep', 'goal_ledger'],
    'Builder': ['build', 'implement', 'code', 'script', 'function', 'endpoint', 'api/',
                'module', 'importable', 'split', 'seams', 'canary', 'test file',
                'agent_portal.py', 'portal code', 'bug fix'],
    'Verifier': ['verify', 'probe', 'test run', 'acceptance', 'pass/fail', 'evidence',
                 'post-probe', 'quinn-q4', 'trigger_group_run', 'stall banner',
                 'confirm.*renders', 'live-verify'],
    'Designer': ['css', 'ui/', 'frontend', 'panel', 'breakpoint', 'render', 'hard-refresh',
                 'index.html', 'app.css', 'core.js', 'uploads.js', 'markup'],
    'Archivist': ['supersession', 'coherence pass', 'index_check', 'orphan', 'archive',
                  'knowledge-base', 'retrieval', 'stale reference', 'ip scrub',
                  '192.168', 'tracked files'],
    'Mechanic': ['restart', 'portal pid', 'watchdog', 'reboot', 'ops', 'elev.py',
                 'memorymirrorrun', '_portal_pid.txt', 'load test', 'probe unreachable',
                 'recover_force', 'post-probe.*ok', 'trigger_group_run.log'],
    'Scribe': ['synthesis', 'round record', 'compression', 'narrative', 'drift analysis',
               'chat_history_group', 'contradiction', 'durable_check', 'quality gate',
               'cycle-narrative', 'fidelity score'],
}

def infer_owner(text):
    combined = text.lower()
    # First check for explicit name#goal pattern
    for name in ROSTER:
        if re.search(rf'{name}\s*#?\d+', text, re.I):
            return name, 'explicit'
    # Check for agent name as a word (e.g., "Verifier closes", "Builder H1")
    name_matches = []
    for name in ROSTER:
        if re.search(rf'\b{name}\b', text, re.I):
            name_matches.append(name)
    if len(name_matches) == 1:
        return name_matches[0], 'name-in-text'
    # Then signal-based
    scores = {}
    for agent, signals in OWNER_SIGNALS.items():
        score = sum(1 for sig in signals if re.search(sig, combined))
        if score > 0:
            scores[agent] = score
    if not scores:
        return 'TBD', 'no-signal'
    best = max(scores, key=scores.get)
    sorted_s = sorted(scores.values(), reverse=True)
    if len(sorted_s) > 1 and sorted_s[0] == sorted_s[1]:
        return 'TBD', 'tie'
    return best, f'signal({scores[best]})'

def scan_todo():
    if not os.path.exists('TODO.md'):
        print("ERROR: TODO.md not found")
        sys.exit(1)
    with open('TODO.md', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    open_items = []
    for i, line in enumerate(lines, 1):
        m = re.match(r'^\s*- \[ \] (.+)$', line)
        if m:
            text = m.group(1).strip()
            owner, method = infer_owner(text)
            open_items.append({
                'line': i,
                'text': text[:120],
                'owner': owner,
                'method': method
            })
    
    total = len(open_items)
    owned = sum(1 for x in open_items if x['owner'] != 'TBD')
    unowned = [x for x in open_items if x['owner'] == 'TBD']
    coverage_pct = (owned / total * 100) if total else 0
    
    # Owner breakdown
    breakdown = {}
    for x in open_items:
        if x['owner'] != 'TBD':
            breakdown[x['owner']] = breakdown.get(x['owner'], 0) + 1
    
    return {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'total_open': total,
        'owned': owned,
        'unowned_count': len(unowned),
        'coverage_pct': round(coverage_pct, 1),
        'owner_breakdown': dict(sorted(breakdown.items(), key=lambda x: -x[1])),
        'unowned_items': unowned[:20],  # cap at 20 for readability
    }

if __name__ == '__main__':
    result = scan_todo()
    if '--json' in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        print(f"Owner Coverage: {result['owned']}/{result['total_open']} ({result['coverage_pct']}%)")
        print(f"Unowned: {result['unowned_count']}")
        print(f"Breakdown: {json.dumps(result['owner_breakdown'])}")
        if result['unowned_items']:
            print("\nUnowned items (first 10):")
            for item in result['unowned_items'][:10]:
                print(f"  L{item['line']}: {item['text'][:80]}...")