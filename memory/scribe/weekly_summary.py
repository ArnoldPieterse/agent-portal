import os, re, glob
from datetime import datetime, timedelta
from collections import defaultdict

"""Weekly Fleet Summary Generator - Scribe goal #4
Usage: python memory/scribe/weekly_summary.py [YYYY-MM-DD]
Produces memory/scribe/weekly-YYYY-WW.md with 5 sections."""

def get_week_range(ref_date=None):
    if ref_date is None:
        ref_date = datetime.now()
    start = ref_date - timedelta(days=ref_date.weekday())
    end = start + timedelta(days=7)
    return start, end

def parse_goal_file(path):
    """Extract goals with verified status from a goal file."""
    if not os.path.exists(path):
        return []
    text = open(path, encoding='utf-8').read()
    lines = text.split('\n')
    goals = []
    current_goal = None
    for line in lines:
        m = re.match(r'^(\d+)\.\s+\*\*(.+?)\*\*', line)
        if m:
            if current_goal:
                goals.append(current_goal)
            current_goal = {'num': int(m.group(1)), 'title': m.group(2), 'verified': False, 'verify_date': None}
            vm = re.search(r'\(verified:\s*(\d{4}-\d{2}-\d{2})', line)
            if vm:
                current_goal['verified'] = True
                current_goal['verify_date'] = vm.group(1)
        elif current_goal and not m:
            if not current_goal['verified']:
                vm = re.search(r'\(verified:\s*(\d{4}-\d{2}-\d{2})', line)
                if vm:
                    current_goal['verified'] = True
                    current_goal['verify_date'] = vm.group(1)
            if re.match(r'^\d+\.\s+\*\*', line):
                goals.append(current_goal)
                current_goal = None
    if current_goal:
        goals.append(current_goal)
    return goals

def get_goals_closed_this_week(start, end):
    closed = []
    goal_files = glob.glob('memory/goals/*.md')
    skip = {'index.md', 'scheduled-background.md', 'all-goals-2026-11-13.md',
            '2026-11-13-agent-goals.md', 'cycle2-dependency-map.md',
            'cycle2-kickoff-2026-11-16.md', 'slip_prediction_table.md'}
    for gf in goal_files:
        basename = os.path.basename(gf).lower()
        if basename in skip:
            continue
        stem = basename.replace('.md', '')
        agent = stem.split('-')[0] if '-' in stem else stem
        goals = parse_goal_file(gf)
        for g in goals:
            if g['verified'] and g['verify_date']:
                try:
                    vd = datetime.strptime(g['verify_date'], '%Y-%m-%d')
                    if start <= vd < end:
                        closed.append({'agent': agent, 'goal': g['title'], 'date': g['verify_date'], 'file': gf})
                except ValueError:
                    pass
    return closed

def get_new_blockers(start, end):
    path = 'memory/ops/blockers.md'
    if not os.path.exists(path):
        return []
    text = open(path, encoding='utf-8').read()
    entries = re.findall(r'\[([^\]]*20\d{2}-\d{2}-\d{2}[^\]]*)\]', text)
    new_ones = []
    for e in entries:
        dm = re.search(r'(\d{4}-\d{2}-\d{2})', e)
        if dm:
            try:
                d = datetime.strptime(dm.group(1), '%Y-%m-%d')
                if start <= d < end:
                    new_ones.append(e)
            except ValueError:
                pass
    return new_ones

def get_agent_activity(start, end):
    activity = defaultdict(int)
    for root, dirs, files in os.walk('memory'):
        parts = root.replace('\\', '/').split('/')
        if len(parts) >= 2 and parts[0] == 'memory':
            agent_dir = parts[1]
            if agent_dir in ('scribe', 'builder', 'designer', 'researcher', 'verifier',
                             'mechanic', 'orchestrator', 'archivist'):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        mtime = datetime.fromtimestamp(os.path.getmtime(fp))
                        if start <= mtime < end:
                            activity[agent_dir] += 1
                    except OSError:
                        pass
    return dict(activity)

def get_key_decisions(start, end):
    path = 'memory/scribe/decision_log.md'
    if not os.path.exists(path):
        return []
    text = open(path, encoding='utf-8').read()
    decisions = []
    for line in text.split('\n'):
        m = re.match(r'^#{1,3}\s+(20\d{2}-\d{2}-\d{2})\s*[-\u2013\u2014]?\s*(.+)', line)
        if m:
            try:
                d = datetime.strptime(m.group(1), '%Y-%m-%d')
                if start <= d < end:
                    decisions.append(f"{m.group(1)}: {m.group(2).strip()}")
            except ValueError:
                pass
    if not decisions:
        for m in re.finditer(r'(20\d{2}-\d{2}-\d{2})\s*[-\u2013\u2014]\s*(.{10,100})', text):
            try:
                d = datetime.strptime(m.group(1), '%Y-%m-%d')
                if start <= d < end:
                    decisions.append(f"{m.group(1)}: {m.group(2).strip()}")
            except ValueError:
                pass
    return decisions[:15]

def get_next_focus():
    path = 'TODO.md'
    if not os.path.exists(path):
        return "No TODO.md found."
    lines = open(path, encoding='utf-8').readlines()
    focus_lines = []
    for line in lines[:25]:
        s = line.strip()
        if s and not s.startswith('<') and not s.startswith('---'):
            focus_lines.append(s)
        if len(focus_lines) >= 6:
            break
    return '\n'.join(focus_lines)

def generate_weekly_summary(ref_date=None):
    start, end = get_week_range(ref_date)
    week_num = start.isocalendar()[1]
    year = start.isocalendar()[0]
    
    closed = get_goals_closed_this_week(start, end)
    blockers = get_new_blockers(start, end)
    activity = get_agent_activity(start, end)
    decisions = get_key_decisions(start, end)
    focus = get_next_focus()
    
    out = []
    out.append(f"# Weekly Fleet Summary - {year}-W{week_num:02d}")
    out.append(f"**Period:** {start.strftime('%Y-%m-%d')} to {(end - timedelta(days=1)).strftime('%Y-%m-%d')}")
    out.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    out.append("")
    
    out.append("## 1. Goals Closed This Week")
    out.append(f"Total: {len(closed)}")
    if closed:
        for c in sorted(closed, key=lambda x: (x['agent'], x['date'])):
            out.append(f"- [{c['agent']}] {c['goal']} ({c['date']})")
    else:
        out.append("- (none recorded this week)")
    out.append("")
    
    out.append("## 2. New Blockers")
    if blockers:
        for b in blockers:
            out.append(f"- {b}")
    else:
        out.append("- (no new blockers this week)")
    out.append("")
    
    out.append("## 3. Agent Activity Stats")
    if activity:
        total = sum(activity.values())
        out.append(f"Total file changes: {total}")
        for agent in sorted(activity, key=lambda a: -activity[a]):
            out.append(f"- {agent}: {activity[agent]} files modified")
    else:
        out.append("- (no activity detected)")
    out.append("")
    
    out.append("## 4. Key Decisions")
    if decisions:
        for d in decisions:
            out.append(f"- {d}")
    else:
        out.append("- (none recorded this week)")
    out.append("")
    
    out.append("## 5. Next Week Focus")
    out.append(focus)
    out.append("")
    
    content = '\n'.join(out)
    filename = f"memory/scribe/weekly-{year}-W{week_num:02d}.md"
    os.makedirs('memory/scribe', exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filename, content

if __name__ == '__main__':
    import sys
    ref = None
    if len(sys.argv) > 1:
        ref = datetime.strptime(sys.argv[1], '%Y-%m-%d')
    fname, content = generate_weekly_summary(ref)
    print(f"Wrote: {fname}")
    print(f"Size: {len(content)} bytes")
