#!/usr/bin/env python3
"""Decision Quality Longitudinal Analysis - per-agent, per-domain trend + regression detection.

Usage: python memory/archivist/decision_quality_trend.py
Reads: memory/archivist/decision-archive-data.jsonl (+ any new decision-quality.jsonl)
Output: memory/archivist/decision-quality-trend.md (human) + .json (machine)

AC: covers >=4 cycles; identifies top improver + top regressing agent; actionable recommendations.
STATUS 2026-11-26: BASELINE ONLY - data covers ~14 days (target >=4 cycles). Re-run when more data exists.
"""
import json, sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

POSITIVE = {'executed','ratified','pass','success','accept-resolve','dry_run_complete','auto-indexed'}
NEGATIVE = {'failure','aborted','failed_at_step_3','reject-resolve','rollback-executed'}

def score(r):
    conf = r.get('confidence', 0.5) or 0.5
    o = r.get('outcome','')
    os_ = 1.0 if o in POSITIVE else (0.0 if o in NEGATIVE else 0.5)
    return conf * 0.4 + os_ * 0.6

def load():
    recs = []
    for f in ['memory/archivist/decision-archive-data.jsonl', 'memory/archivist/decision-quality.jsonl']:
        p = Path(f)
        if p.exists():
            for line in p.read_text(encoding='utf-8').strip().split('\n'):
                if line.strip():
                    try: recs.append(json.loads(line))
                    except: pass
    return recs

def main():
    recs = load()
    if not recs:
        print("No decision data found."); sys.exit(1)
    
    # Bucket by week (proxy for cycle when cycle field absent)
    weekly = defaultdict(list)
    for r in recs:
        d = r.get('date','unknown')
        if d != 'unknown' and len(d) >= 8:
            # ISO week
            try:
                dt = datetime.strptime(d[:10], '%Y-%m-%d')
                wk = f"{dt.isocalendar()[0]}-W{dt.isocalendar()[1]:02d}"
            except:
                wk = 'unknown'
        else:
            wk = 'unknown'
        weekly[wk].append(r)
    
    # Per-owner per-week quality
    owner_weekly = defaultdict(lambda: defaultdict(list))
    for r in recs:
        owner = (r.get('owner','?') or '?').strip().lower()
        if owner in ('?','(unattributed)','system','test_agent'): continue
        wk_key = None
        d = r.get('date','unknown')
        if d != 'unknown' and len(d) >= 8:
            try:
                dt = datetime.strptime(d[:10], '%Y-%m-%d')
                wk_key = f"{dt.isocalendar()[0]}-W{dt.isocalendar()[1]:02d}"
            except: pass
        if wk_key:
            owner_weekly[owner][wk_key].append(r)
    
    # Compute trend (slope) per owner across weeks
    trends = {}
    for owner, weeks in owner_weekly.items():
        week_scores = []
        for wk in sorted(weeks.keys()):
            sc = [score(r) for r in weeks[wk]]
            week_scores.append((wk, sum(sc)/len(sc)))
        if len(week_scores) >= 2:
            # Simple slope (last - first) / n_weeks
            slope = (week_scores[-1][1] - week_scores[0][1]) / (len(week_scores)-1)
            trends[owner] = {'slope': round(slope,4), 'weeks': len(week_scores), 'start': week_scores[0], 'end': week_scores[-1]}
        else:
            trends[owner] = {'slope': None, 'weeks': 1, 'note': 'insufficient data for trend'}
    
    # Report
    n_cycles_estimated = len(weekly) - (1 if 'unknown' in weekly else 0)
    sufficient = n_cycles_estimated >= 4
    
    md = []
    md.append("# Decision Quality Longitudinal Analysis")
    md.append(f"Generated: {datetime.now().isoformat()}")
    md.append(f"Data source: decision-archive-data.jsonl (+ decision-quality.jsonl if present)")
    md.append(f"Cycles/weeks covered: {n_cycles_estimated}")
    md.append(f"AC met (>=4 cycles): {'YES' if sufficient else 'NO - baseline only'}")
    md.append("")
    
    if sufficient:
        improver = max(trends.items(), key=lambda x: x[1]['slope'] or 0)
        regressing = min(trends.items(), key=lambda x: x[1]['slope'] or 0)
        md.append(f"**Top improver:** {improver[0]} (slope={improver[1]['slope']:+.4f}/week)")
        md.append(f"**Top regressing:** {regressing[0]} (slope={regressing[1]['slope']:+.4f}/week)")
        md.append("")
        md.append("## Recommendations")
        md.append(f"- {regressing[0]}: investigate decision quality drop; review recent negative-outcome decisions for pattern.")
    else:
        md.append("## Baseline (insufficient data for trend)")
        md.append(f"Only {n_cycles_estimated} week(s) of data. Re-run when >=4 weeks exist.")
        # Still show per-owner quality as a starting point
        owner_avg = {}
        for owner, weeks in owner_weekly.items():
            all_sc = [score(r) for wk in weeks.values() for r in wk]
            if all_sc:
                owner_avg[owner] = round(sum(all_sc)/len(all_sc), 3)
        md.append("")
        md.append("| Owner | Avg Quality | Decisions |")
        md.append("|-------|-------------|-----------|")
        for o, q in sorted(owner_avg.items(), key=lambda x: -x[1]):
            n = sum(len(v) for v in owner_weekly[o].values())
            md.append(f"| {o} | {q:.3f} | {n} |")
    
    # Save
    Path('memory/archivist/decision-quality-trend.md').write_text('\n'.join(md), encoding='utf-8')
    Path('memory/archivist/decision-quality-trend.json').write_text(
        json.dumps({'trends': trends, 'sufficient': sufficient, 'weeks': n_cycles_estimated}, indent=2), encoding='utf-8')
    print(f"Done. Cycles={n_cycles_estimated}, AC_met={sufficient}")
    print(f"Output: memory/archivist/decision-quality-trend.md")

if __name__ == '__main__':
    main()
