"""Scribe G8 - Round-record template + auto-synthesis.
Scans turn evidence (recent file changes, TODO.md, memory/ deltas) and drafts
a canonical decided/open/owner skeleton so compression is review-and-fill.

Usage: python memory/scribe/round_record_draft.py [--round N] [--date YYYY-MM-DD]
Output: memory/synthesis/<date>-r<N>-round-record-DRAFT.md
"""
import os, re, sys, json, glob
from datetime import datetime

def get_recent_files(hours=2):
    """Files modified in the last N hours (evidence of what happened this turn)."""
    now = datetime.now()
    recent = []
    for root, dirs, files in os.walk('.'):
        if any(x in root for x in ('__pycache__', '.git', 'node_modules')):
            continue
        for f in files:
            path = os.path.join(root, f).replace('\\', '/')
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(path))
                age_h = (now - mtime).total_seconds() / 3600
                if age_h < hours:
                    recent.append((age_h, path))
            except OSError:
                pass
    recent.sort()
    return [p for _, p in recent]

def parse_todo_items():
    """Extract open/closed items from TODO.md."""
    if not os.path.exists('TODO.md'):
        return [], []
    with open('TODO.md', 'r', encoding='utf-8') as f:
        content = f.read()
    open_items = re.findall(r'^\s*- \[ \] (.+)$', content, re.M)
    closed_items = re.findall(r'^\s*- \[x\] (.+)$', content, re.M)
    return open_items, closed_items

def extract_owners(text):
    """Find agent-name#goal references (owner markers)."""
    roster = ['Orchestrator','Researcher','Builder','Verifier','Designer','Archivist','Mechanic','Scribe']
    owners = set()
    for name in roster:
        if re.search(rf'{name}\s*#?\d+', text):
            owners.add(name)
    return sorted(owners)

def detect_decisions(recent_files, todo_content):
    """Heuristic: closed TODO items + files with 'decision'/'ruling'/'ratif' in name."""
    decisions = []
    for item in re.findall(r'^\s*- \[x\] (.+)$', todo_content, re.M):
        if any(kw in item.lower() for kw in ['decided','ratified','closed','shipped','verified','fixed']):
            decisions.append(item.strip())
    for f in recent_files:
        basename = os.path.basename(f).lower()
        if any(kw in basename for kw in ['decision','ruling','ratif','closeout']):
            decisions.append(f"File landed: {f}")
    return decisions[:15]

def detect_open_items(todo_content):
    """Open TODO items that are actionable (not PENDING-wait)."""
    open_items = re.findall(r'^\s*- \[ \] (.+)$', todo_content, re.M)
    actionable = [i.strip() for i in open_items if 'PENDING' not in i.upper() or 'wait' not in i.lower()]
    return actionable[:15]

def draft_record(round_num, date_str):
    recent_files = get_recent_files(hours=3)
    todo_content = ''
    if os.path.exists('TODO.md'):
        with open('TODO.md', 'r', encoding='utf-8') as f:
            todo_content = f.read()
    
    open_items, closed_items = parse_todo_items()
    decisions = detect_decisions(recent_files, todo_content)
    open_actionable = detect_open_items(todo_content)
    owners = extract_owners(todo_content)
    
    # Build the record
    lines = []
    lines.append(f"# Round Record - {date_str} (r{round_num}) [DRAFT]")
    lines.append(f"Auto-drafted by round_record_draft.py at {datetime.now().isoformat()}")
    lines.append("")
    lines.append("## DECIDED")
    if decisions:
        for d in decisions:
            # Try to find owner and source
            owner = next((o for o in owners if o.lower() in d.lower()), 'TBD')
            src = next((f for f in recent_files if os.path.basename(f).lower() in d.lower()), 'TODO.md')
            lines.append(f"- {d}")
            lines.append(f"  - owner: {owner} | source: {src}")
    else:
        lines.append("- (none detected this turn)")
    lines.append("")
    lines.append("## OPEN")
    if open_actionable:
        for item in open_actionable:
            owner = next((o for o in owners if o.lower() in item.lower()), 'TBD')
            lines.append(f"- {item} [owner: {owner}]")
    else:
        lines.append("- (none detected)")
    lines.append("")
    lines.append("## METRICS (auto-filled from evidence files)")
    # Try to pull metrics from known evidence files
    metrics = {}
    metric_sources = {
        'orphan_rate': 'memory/scribe/orphan-sweep-2026-11-16.json',
        'supersession_broken': 'memory/scribe/supersession-report.json',
        'owner_coverage': 'memory/scribe/owner-coverage-ledger-2026-11-16.json',
    }
    for key, src in metric_sources.items():
        if os.path.exists(src):
            try:
                with open(src) as f:
                    data = json.load(f)
                if key == 'orphan_rate':
                    metrics[key] = f"{data.get('orphan_rate_pct', '?')}%"
                elif key == 'supersession_broken':
                    metrics[key] = str(data.get('broken_chains', '?'))
                elif key == 'owner_coverage':
                    total = data.get('total_open', 0)
                    owned = data.get('owned', 0)
                    metrics[key] = f"{owned}/{total} ({(owned/total*100 if total else 0):.1f}%)"
            except (json.JSONDecodeError, KeyError, TypeError):
                metrics[key] = 'parse-error'
        else:
            metrics[key] = 'no-data'
    for k, v in metrics.items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## AGENTS ACTIVE THIS TURN")
    active_agents = set()
    for f in recent_files:
        m = re.match(r'memory/([a-z]+)/', f)
        if m and m.group(1) not in ('scribe', 'synthesis', 'goals', 'ops'):
            active_agents.add(m.group(1).capitalize())
    lines.append(f"- {', '.join(sorted(active_agents)) if active_agents else 'unknown'}")
    lines.append("")
    lines.append("---")
    lines.append("*DRAFT - review and fill before recording. Fields marked TBD need human/agent confirmation.*")
    
    return '\n'.join(lines)

if __name__ == '__main__':
    round_num = 1
    date_str = datetime.now().strftime('%Y-%m-%d')
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == '--round' and i+1 < len(args):
            round_num = int(args[i+1])
        if a == '--date' and i+1 < len(args):
            date_str = args[i+1]
    
    record = draft_record(round_num, date_str)
    
    outdir = 'memory/synthesis'
    os.makedirs(outdir, exist_ok=True)
    outpath = f"{outdir}/{date_str}-r{round_num}-round-record-DRAFT.md"
    with open(outpath, 'w', encoding='utf-8') as f:
        f.write(record)
    
    # Self-assessment: what % of fields are pre-filled (not TBD/unknown/no-data)
    total_fields = 0
    filled_fields = 0
    for line in record.split('\n'):
        if 'TBD' in line or 'unknown' in line or 'no-data' in line or '(none detected' in line:
            total_fields += 1
        elif line.startswith('- ') and not line.startswith('---'):
            total_fields += 1
            filled_fields += 1
    
    pct = (filled_fields / total_fields * 100) if total_fields else 0
    print(f"Draft written: {outpath}")
    print(f"Pre-fill rate: {pct:.0f}% ({filled_fields}/{total_fields} fields)")
    sys.exit(0 if pct >= 80 else 1)
