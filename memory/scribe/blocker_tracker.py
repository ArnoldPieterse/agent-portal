"""Blocker Resolution Tracker - Scribe goal #5 (cycle-10)
Parses memory/ops/blockers.md, computes resolution metrics, writes trend report.
Usage: python memory/scribe/blocker_tracker.py
Output: memory/synthesis/blocker-trends.md + blocker-metrics.json
"""
import re, json, pathlib
from datetime import datetime
from collections import defaultdict

def parse_blockers(md_text):
    """Parse memory/ops/blockers.md into structured records."""
    blocks = re.split(r'\n(?=## )', md_text)
    records = []
    
    for block in blocks:
        if not block.startswith('## '):
            continue
        
        header = block.split('\n')[0]
        
        if '[RESOLVED' in header or '**RESOLVED' in block[:200]:
            status = 'resolved'
        elif '[RECONCILED' in header:
            status = 'reconciled'
        elif '[NEEDS-HUMAN' in header:
            status = 'open_needs_human'
        elif '[OPS-NOTE' in header:
            status = 'ops_note'
        else:
            status = 'unknown'
        
        date_match = re.search(r'(20\d{2}-\d{2}-\d{2})', header)
        date_str = date_match.group(1) if date_match else None
        
        agents = ['Orchestrator', 'Researcher', 'Builder', 'Verifier', 'Designer', 'Scribe', 'Mechanic']
        agent = None
        for a in agents:
            if a in header:
                agent = a
                break
        
        class_match = re.search(r'\*\*Class:\*\*\s*(.+)', block)
        blocker_class = class_match.group(1).strip() if class_match else None
        
        title_match = re.search(r'##\s*\[[^\]]+\]\s*(?:\d{4}-\d{2}-\d{2}\s*)?(.+)', header)
        title = title_match.group(1).strip() if title_match else header[3:].strip()
        
        resolved_marker = re.search(r'\*\*RESOLVED\s*(20\d{2}-\d{2}-\d{2})', block)
        resolved_date = None
        if resolved_marker:
            resolved_date = resolved_marker.group(1)
        
        records.append({
            'header': header.strip(),
            'status': status,
            'date_opened': date_str,
            'agent': agent,
            'class': blocker_class,
            'title': title,
            'resolved_date': resolved_date,
        })
    
    return records

def compute_metrics(records):
    """Compute resolution metrics from parsed records."""
    metrics = {
        'total_blockers': len(records),
        'by_status': defaultdict(int),
        'by_agent': defaultdict(int),
        'by_class': defaultdict(int),
        'resolution_times_hours': [],
        'agent_resolution_counts': defaultdict(int),
    }
    
    for r in records:
        metrics['by_status'][r['status']] += 1
        if r['agent']:
            metrics['by_agent'][r['agent']] += 1
        if r['class']:
            short_class = r['class'].split('(')[0].strip().lower()
            metrics['by_class'][short_class] += 1
        
        if r['date_opened'] and r['resolved_date']:
            try:
                d1 = datetime.strptime(r['date_opened'], '%Y-%m-%d')
                d2 = datetime.strptime(r['resolved_date'], '%Y-%m-%d')
                hours = (d2 - d1).total_seconds() / 3600
                metrics['resolution_times_hours'].append({
                    'title': r['title'][:80],
                    'agent': r['agent'],
                    'hours': round(hours, 1)
                })
            except ValueError:
                pass
        
        if r['status'] in ('resolved', 'reconciled') and r['agent']:
            metrics['agent_resolution_counts'][r['agent']] += 1
    
    for key in ['by_status', 'by_agent', 'by_class', 'agent_resolution_counts']:
        metrics[key] = dict(metrics[key])
    
    if metrics['resolution_times_hours']:
        times = [t['hours'] for t in metrics['resolution_times_hours']]
        metrics['avg_resolution_hours'] = round(sum(times) / len(times), 1)
        metrics['min_resolution_hours'] = min(times)
        metrics['max_resolution_hours'] = max(times)
    else:
        metrics['avg_resolution_hours'] = None
    
    return metrics

def generate_report(metrics, records):
    """Generate the markdown report."""
    lines = []
    lines.append("# Blocker Resolution Trends")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    
    lines.append("## Summary")
    lines.append(f"- **Total blockers tracked:** {metrics['total_blockers']}")
    status_summary = ", ".join(f"{k}: {v}" for k, v in sorted(metrics['by_status'].items()))
    lines.append(f"- **Status breakdown:** {status_summary}")
    if metrics.get('avg_resolution_hours') is not None:
        lines.append(f"- **Avg resolution time (dated pairs):** {metrics['avg_resolution_hours']}h")
        lines.append(f"- **Range:** {metrics['min_resolution_hours']}h - {metrics['max_resolution_hours']}h")
    else:
        lines.append("- **Resolution times:** Insufficient date pairs to compute")
    lines.append("")
    
    lines.append("## Blockers by Agent")
    for agent, count in sorted(metrics['by_agent'].items(), key=lambda x: -x[1]):
        resolved = metrics['agent_resolution_counts'].get(agent, 0)
        lines.append(f"- **{agent}:** {count} total, {resolved} resolved/reconciled")
    lines.append("")
    
    lines.append("## Blocker Classes (top 10)")
    for cls, count in sorted(metrics['by_class'].items(), key=lambda x: -x[1])[:10]:
        lines.append(f"- `{cls}`: {count}")
    lines.append("")
    
    open_blockers = [r for r in records if r['status'] == 'open_needs_human']
    lines.append("## Currently Open (NEEDS-HUMAN)")
    if open_blockers:
        for r in open_blockers:
            agent_tag = f" ({r['agent']})" if r['agent'] else ""
            date_tag = f" [{r['date_opened']}]" if r['date_opened'] else ""
            lines.append(f"- {r['title'][:100]}{agent_tag}{date_tag}")
    else:
        lines.append("- None")
    lines.append("")
    
    if metrics['resolution_times_hours']:
        lines.append("## Resolved Blockers (with timing)")
        for t in sorted(metrics['resolution_times_hours'], key=lambda x: x['hours']):
            lines.append(f"- {t['hours']}h | {t['agent']} | {t['title']}")
        lines.append("")
    
    lines.append("## Insights & Recommendations")
    insights = []
    
    if metrics['by_class']:
        top_class = max(metrics['by_class'].items(), key=lambda x: x[1])
        insights.append(f"Most frequent blocker class: **{top_class[0]}** ({top_class[1]} occurrences). "
                       f"Consider a standing runbook or automation for this pattern.")
    
    open_by_agent = defaultdict(int)
    for r in records:
        if r['status'] == 'open_needs_human' and r['agent']:
            open_by_agent[r['agent']] += 1
    if open_by_agent:
        top_open = max(open_by_agent.items(), key=lambda x: x[1])
        insights.append(f"**{top_open[0]}** has the most open blockers ({top_open[1]}). "
                       f"Focus unblocking effort there first.")
    
    if metrics.get('avg_resolution_hours') is not None:
        if metrics['avg_resolution_hours'] < 48:
            insights.append("Resolution times are trending well (<2 days average). Maintain current cadence.")
        else:
            insights.append(f"Average resolution time is {metrics['avg_resolution_hours']}h. "
                           f"Target: reduce to <48h by prioritizing oldest open blockers first.")
    
    if not insights:
        insights.append("Insufficient data for trend analysis. Continue tracking.")
    
    for i, ins in enumerate(insights, 1):
        lines.append(f"{i}. {ins}")
    
    return "\n".join(lines)

def main():
    md_path = pathlib.Path("memory/ops/blockers.md")
    if not md_path.exists():
        print("ERROR: memory/ops/blockers.md not found")
        return 1
    
    text = md_path.read_text()
    records = parse_blockers(text)
    metrics = compute_metrics(records)
    report = generate_report(metrics, records)
    
    out_dir = pathlib.Path("memory/synthesis")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "blocker-trends.md").write_text(report)
    (out_dir / "blocker-metrics.json").write_text(json.dumps(metrics, indent=2))
    
    print(f"Parsed {len(records)} blocker records")
    print(f"Status: {metrics['by_status']}")
    print(f"Avg resolution: {metrics.get('avg_resolution_hours')}h")
    print("Output: memory/synthesis/blocker-trends.md")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
