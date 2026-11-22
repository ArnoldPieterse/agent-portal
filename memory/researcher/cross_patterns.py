#!/usr/bin/env python3
"""Cross-Agent Pattern Detector.

Parses all agents' goal completions + incident records from the last 3 cycles;
identifies patterns no single agent would see:
  1. Cross-agent topic overlap (coordination risk)
  2. Theme distribution per agent
  3. Throughput comparison
  4. Reopened topics (slip indicators)
  5. Blocker concentration

Usage: python memory/researcher/cross_patterns.py [--json]
Output: memory/goals/cross_patterns_report.md (and optionally JSON to stdout)
"""
import pathlib, re, json, sys
from datetime import datetime
from collections import defaultdict, Counter

AGENTS = ['orchestrator', 'researcher', 'verifier', 'scribe', 'designer', 'builder', 'archivist', 'mechanic']
GOALS_DIR = pathlib.Path('memory/goals')
ARCHIVE_DIR = GOALS_DIR / 'archive'
OPS_DIR = pathlib.Path('memory/ops')


def parse_goal_file(path):
    """Extract goals with precise verification detection."""
    txt = path.read_text(encoding='utf-8', errors='replace')
    goals = []
    for m in re.finditer(r'^\s*(\d+)\.\s+\*\*(.+?)\*\*\s*-\s*(.*)', txt, re.MULTILINE):
        num, title, desc = int(m.group(1)), m.group(2).strip(), m.group(3).strip()
        tail = txt[m.start():m.end() + 200]
        verified = bool(re.search(r'\(verified:|✓\s*REACHED|\*\*reached\*\*', tail, re.IGNORECASE))
        goals.append({'num': num, 'title': title, 'desc': desc[:200], 'verified': verified})
    return goals


def extract_agent_files(agent):
    files = []
    cur = GOALS_DIR / f'{agent}.md'
    if cur.exists():
        files.append(('current', cur))
    for f in sorted(ARCHIVE_DIR.glob(f'{agent}-*')):
        files.append(('archive', f))
    return files


def parse_date(fname):
    m = re.search(r'(\d{4}-\d{2}-\d{2})', fname)
    return m.group(1) if m else None


def collect_goals():
    """Collect all unique goals across agents, deduplicating cumulative archives."""
    seen = set()
    all_goals = []
    for agent in AGENTS:
        for source, fpath in extract_agent_files(agent):
            date = parse_date(fpath.name) or 'current'
            try:
                goals = parse_goal_file(fpath)
            except Exception:
                continue
            for g in goals:
                key = (agent, g['title'].lower()[:50], date)
                if key not in seen:
                    seen.add(key)
                    all_goals.append({**g, 'agent': agent, 'source': source, 'date': date, 'file': str(fpath)})
    return all_goals


def detect_patterns(all_goals):
    """Run all 5 pattern detectors. Returns dict of results."""
    # P1: Cross-agent topic overlap
    title_map = defaultdict(list)
    for g in all_goals:
        key = re.sub(r'[^a-z0-9 ]', '', g['title'].lower()).strip()[:60]
        title_map[key].append(g)
    cross_agent_dupes = {k: v for k, v in title_map.items() if len(set(x['agent'] for x in v)) > 1}

    # P2: Theme distribution per agent
    themes = ['auto', 'monitor', 'recover', 'incident', 'test', 'verify', 'alert', 'log', 'deploy']
    agent_themes = defaultdict(Counter)
    for g in all_goals:
        text = f"{g['title']} {g['desc']}".lower()
        for kw in themes:
            if kw in text:
                agent_themes[g['agent']][kw] += 1

    # P3: Throughput
    agent_v = Counter(); agent_t = Counter()
    for g in all_goals:
        agent_t[g['agent']] += 1
        if g['verified']: agent_v[g['agent']] += 1

    # P4: Reopened topics (same agent + title across multiple distinct dates)
    reopen = []
    for key, items in title_map.items():
        by_agent = defaultdict(set)
        for it in items:
            by_agent[it['agent']].add(it['date'])
        for agent, dates in by_agent.items():
            if len(dates) > 1 and 'current' not in dates:
                reopen.append((key, sorted(dates), agent))

    # P5: Blocker concentration
    blocker_text = ''
    if OPS_DIR.joinpath('blockers.md').exists():
        blocker_text = OPS_DIR.joinpath('blockers.md').read_text(encoding='utf-8', errors='replace')
    blocker_agents = Counter(re.findall(r'@(\w+)', blocker_text))

    return {
        'total': len(all_goals),
        'verified': sum(1 for g in all_goals if g['verified']),
        'open': sum(1 for g in all_goals if not g['verified']),
        'cross_agent_dupes': {k: [x['agent'] for x in v] for k, v in cross_agent_dupes.items()},
        'agent_themes': {a: dict(c.most_common(5)) for a, c in agent_themes.items()},
        'throughput': {a: {'verified': agent_v.get(a,0), 'total': agent_t.get(a,0)} for a in AGENTS},
        'reopened_topics': reopen[:20],
        'blocker_concentration': dict(blocker_agents.most_common()),
    }


def build_report(patterns):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    r = f"""# Cross-Agent Pattern Report
Generated: {now} | Scope: all cycles, {len(AGENTS)} agents, {patterns['total']} unique goals
Verified: {patterns['verified']} ({patterns['verified']/max(patterns['total'],1)*100:.0f}%), Open: {patterns['open']}

## 1. Cross-Agent Topic Overlap (coordination risk)
"""
    for t, agents in sorted(patterns['cross_agent_dupes'].items(), key=lambda x: -len(x[1]))[:10]:
        r += f"- **{t}** → {', '.join(agents)}\n"
    r += "\n## 2. Theme Distribution per Agent (top themes)\n"
    for agent in AGENTS:
        top = patterns['agent_themes'].get(agent, {})
        if top:
            r += f"- {agent}: {', '.join(f'{k}({v})' for k,v in list(top.items())[:4])}\n"
    r += "\n## 3. Throughput (verified / total)\n"
    for agent in AGENTS:
        t = patterns['throughput'].get(agent, {'verified':0,'total':0})
        pct = f"{t['verified']/max(t['total'],1)*100:.0f}%"
        r += f"- {agent}: {t['verified']}/{t['total']} ({pct})\n"
    r += f"\n## 4. Reopened Topics (slip indicators): {len(patterns['reopened_topics'])} found\n"
    for title, dates, agent in patterns['reopened_topics'][:10]:
        r += f"- **{title}** [{', '.join(dates)}] agent={agent}\n"
    r += "\n## 5. Blocker Concentration\n"
    for agent, cnt in sorted(patterns['blocker_concentration'].items(), key=lambda x:-x[1]):
        r += f"- {agent}: {cnt} mentions\n"
    return r


def self_test():
    """Run assertions to verify the detector works correctly."""
    goals = collect_goals()
    assert len(goals) > 50, f"Expected >50 goals, got {len(goals)}"
    assert all(any(g['agent'] == a for g in goals) for a in AGENTS), "All agents present"
    patterns = detect_patterns(goals)
    assert patterns['total'] == len(goals)
    assert patterns['verified'] + patterns['open'] == patterns['total']
    assert len(patterns['cross_agent_dupes']) >= 1, "Should find cross-agent overlap"
    assert any(v['total'] > 0 for v in patterns['throughput'].values()), "Throughput data present"
    return True


def main():
    json_out = '--json' in sys.argv
    self_test()
    goals = collect_goals()
    patterns = detect_patterns(goals)
    report = build_report(patterns)
    out_path = GOALS_DIR / 'cross_patterns_report.md'
    out_path.write_text(report, encoding='utf-8')
    if json_out:
        print(json.dumps(patterns, indent=2, default=str))
    else:
        print(f"Report written: {out_path} ({out_path.stat().st_size}b)")
        print(f"Self-test: ALL PASS ✓")


if __name__ == '__main__':
    main()