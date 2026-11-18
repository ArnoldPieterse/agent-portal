#!/usr/bin/env python3
"""Evidence Report Generator - Verifier Goal #2.

Usage: python memory/verifier/gen_report.py --cycle N
Produces: memory/verifier/cycle-N-report.md
"""
import re, os, argparse
from datetime import datetime

AGENTS = ['orchestrator','researcher','builder','verifier','designer','archivist','scribe','mechanic']
GOALS_DIR = 'memory/goals'
EVIDENCE_DIR = 'memory/verifier'
STALE_DAYS = 7

def parse_goals(agent):
    path = os.path.join(GOALS_DIR, f'{agent}.md')
    if not os.path.exists(path):
        return []
    text = open(path, encoding='utf-8').read()
    pattern = r'^\s*(\d+)\.\s+\*\*(.+?)\*\*'
    matches = list(re.finditer(pattern, text, re.MULTILINE))
    goals = []
    for i, m in enumerate(matches):
        num = int(m.group(1))
        title = m.group(2).strip()
        start = m.start()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        block = text[start:end]
        verified_match = re.search(r'\(verified:\s*(\d{4}-\d{2}-\d{2})', block)
        closed = bool(verified_match)
        verify_date = verified_match.group(1) if verified_match else None
        ev_ref = None
        ev_match = re.search(r'(?:evidence at|pointer:|evidence:)\s+([\w/.-]+\.(?:md|json|py))', block)
        if ev_match:
            ev_ref = ev_match.group(1)
        goals.append({'num': num, 'title': title, 'closed': closed, 'verify_date': verify_date, 'evidence_ref': ev_ref})
    return goals

def check_evidence_freshness(evidence_ref):
    if not evidence_ref:
        return None
    path = evidence_ref
    if not os.path.exists(path):
        return {'stale': True, 'reason': 'file missing'}
    mtime = os.path.getmtime(path)
    age_days = (datetime.now().timestamp() - mtime) / 86400
    stale = age_days > STALE_DAYS
    return {'stale': stale, 'reason': f'{age_days:.1f} days old' if stale else 'fresh'}

def generate_report(cycle):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    all_data = {}
    total_goals = 0
    total_closed = 0
    stale_claims = []
    for agent in AGENTS:
        goals = parse_goals(agent)
        closed_count = sum(1 for g in goals if g['closed'])
        open_count = len(goals) - closed_count
        agent_stale = []
        for g in goals:
            if g['closed'] and g['evidence_ref']:
                check = check_evidence_freshness(g['evidence_ref'])
                if check and check.get('stale'):
                    agent_stale.append(f"  - Goal {g['num']} ({check['reason']})")
        has_progress = closed_count > 0
        all_pass = not agent_stale
        status = 'PASS' if (all_pass and has_progress) else ('PARTIAL' if has_progress else 'STALE')
        all_data[agent] = {'total': len(goals), 'closed': closed_count, 'open': open_count, 'stale': agent_stale, 'status': status}
        total_goals += len(goals)
        total_closed += closed_count
        stale_claims.extend([f"[{agent}] {s}" for s in agent_stale])
    evidence_rate = (total_closed / total_goals * 100) if total_goals else 0
    lines = [
        f"# Cycle-{cycle} Evidence Report", "",
        f"**Generated:** {now}",
        f"**Scope:** All agent goal files in `{GOALS_DIR}/`", "",
        "## Summary", "",
        "| Metric | Value |", "|--------|-------|",
        f"| Total goals | {total_goals} |",
        f"| Closed (verified) | {total_closed} |",
        f"| Open | {total_goals - total_closed} |",
        f"| Evidence rate | {evidence_rate:.1f}% |",
        f"| Stale claims | {len(stale_claims)} |", "",
        "## Per-Agent Status", "",
        "| Agent | Total | Closed | Open | Status |",
        "|-------|-------|--------|------|--------|",
    ]
    for agent in AGENTS:
        d = all_data[agent]
        lines.append(f"| {agent} | {d['total']} | {d['closed']} | {d['open']} | {d['status']} |")
    if stale_claims:
        lines.extend(["", "## Stale / Missing Evidence", ""])
        for s in stale_claims:
            lines.append(s)
    lines.extend(["", "## Detail", ""])
    for agent in AGENTS:
        goals = parse_goals(agent)
        if not goals:
            lines.append(f"### {agent}")
            lines.append("_(no goal file found)_")
            lines.append("")
            continue
        lines.append(f"### {agent} ({all_data[agent]['status']})")
        lines.append("")
        for g in goals:
            mark = "✅" if g['closed'] else "⬜"
            date_str = f" (verified {g['verify_date']})" if g['verify_date'] else ""
            lines.append(f"- {mark} **{g['num']}.** {g['title']}{date_str}")
        lines.append("")
    report_text = "\n".join(lines)
    out_path = os.path.join(EVIDENCE_DIR, f'cycle-{cycle}-report.md')
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    return out_path, all_data, total_goals, total_closed, evidence_rate, stale_claims

def main():
    parser = argparse.ArgumentParser(description='Generate cycle evidence report')
    parser.add_argument('--cycle', type=int, required=True, help='Cycle number (e.g., 5)')
    args = parser.parse_args()
    out_path, all_data, total_goals, total_closed, evidence_rate, stale_claims = generate_report(args.cycle)
    print(f"Report written to: {out_path}")
    print(f"Total goals: {total_goals}, Closed: {total_closed}, Evidence rate: {evidence_rate:.1f}%, Stale: {len(stale_claims)}")
    for agent in AGENTS:
        d = all_data[agent]
        print(f"  {agent:15s} {d['closed']}/{d['total']} closed  [{d['status']}]")
    exit(0 if not stale_claims else 1)

if __name__ == '__main__':
    main()
