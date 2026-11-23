#!/usr/bin/env python3
"""Synthesis Quality Scoring - scores memory/synthesis/ files on clarity, completeness,
actionability, recency. Outputs JSON for /api/synthesis/quality endpoint.

Usage: python memory/scribe/synthesis_quality.py [--json] [--top N]
"""
import os, json, re, sys, argparse
from datetime import datetime, date

SYNTH_DIR = "memory/synthesis"
TODAY = date.today()

def parse_date_from_filename(fname):
    m = re.match(r'(\d{4}-\d{2}-\d{2})', fname)
    if m:
        return datetime.strptime(m.group(1), '%Y-%m-%d').date()
    return None

def score_clarity(text):
    s = 0
    if re.search(r'^# ', text, re.M):
        s += 20
    sections = len(re.findall(r'^## ', text, re.M))
    s += min(sections * 5, 20)
    bullets = len(re.findall(r'^[\s]*[-*\d+]\.?\s', text, re.M))
    s += min(bullets * 3, 15)
    lines = text.split('\n')
    max_wall = cur = 0
    for ln in lines:
        if ln.strip():
            cur += 1
            max_wall = max(max_wall, cur)
        else:
            cur = 0
    if max_wall <= 5: s += 15
    elif max_wall <= 8: s += 10
    elif max_wall <= 12: s += 5
    non_empty = [l for l in lines if l.strip()]
    if non_empty:
        avg_len = sum(len(l) for l in non_empty) / len(non_empty)
        if avg_len < 100: s += 15
        elif avg_len < 150: s += 10
        else: s += 5
    return min(s, 100)

def score_completeness(text):
    s = 0
    if re.search(r'(source|context|background|from|based on)', text, re.I):
        s += 20
    if re.search(r'(decided|ruling|outcome|result|conclusion|verdict|ratif|reject)', text, re.I):
        s += 20
    if re.search(r'(because|rationale|reason|since|therefore|hence|->|\u2192)', text, re.I):
        s += 20
    dates = len(re.findall(r'\d{4}-\d{2}-\d{2}', text))
    s += min(dates * 5, 15)
    agents = set(re.findall(r'(Orchestrator|Researcher|Builder|Verifier|Designer|Archivist|Mechanic|Scribe)', text))
    s += min(len(agents) * 3, 15)
    return min(s, 100)

def score_actionability(text):
    s = 0
    if re.search(r'(open item|next step|action|todo|pending|owner)', text, re.I):
        s += 30
    owner_pat = re.findall(r'(Owner|owner|\u2192|->|:\s*\w+.*(?:check|fix|run|build|test))', text)
    if len(owner_pat) >= 2: s += 25
    elif len(owner_pat) == 1: s += 15
    paths = re.findall(r'(memory/[\w/.-]+|\w+\.py|python\s+\S+)', text)
    if len(paths) >= 3: s += 25
    elif len(paths) >= 1: s += 15
    if re.search(r'(by \d|within \d|SLA|deadline|next round|cycle-\d)', text, re.I):
        s += 20
    return min(s, 100)

def score_recency(fdate):
    if fdate is None:
        return 50
    days_old = (TODAY - fdate).days
    if days_old <= 7: return 100
    elif days_old <= 14: return 80
    elif days_old <= 30: return 60
    elif days_old <= 60: return 30
    else: return 10

def score_file(filepath):
    fname = os.path.basename(filepath)
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()
    clarity = score_clarity(text)
    completeness = score_completeness(text)
    actionability = score_actionability(text)
    fdate = parse_date_from_filename(fname)
    recency = score_recency(fdate)
    total = round((clarity + completeness + actionability + recency) / 4, 1)
    return {
        'file': f'memory/synthesis/{fname}',
        'scores': {'clarity': clarity, 'completeness': completeness,
                   'actionability': actionability, 'recency': recency},
        'total': total,
        'date': str(fdate) if fdate else None,
        'days_old': (TODAY - fdate).days if fdate else None
    }

def run():
    results = []
    for fname in sorted(os.listdir(SYNTH_DIR)):
        if not fname.endswith('.md'):
            continue
        fp = os.path.join(SYNTH_DIR, fname)
        if os.path.isfile(fp):
            results.append(score_file(fp))
    fleet_avg = round(sum(r['total'] for r in results) / len(results), 1) if results else 0
    output = {'generated': str(TODAY), 'file_count': len(results),
              'fleet_avg': fleet_avg, 'scores': results}
    return output

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true', help='output JSON only')
    ap.add_argument('--top', type=int, default=0, help='show top N only')
    args = ap.parse_args()

    output = run()
    out_path = 'memory/synthesis/quality-scores.jsonl'
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)

    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print(f"Scored {output['file_count']} files, fleet avg = {output['fleet_avg']}")
        sorted_r = sorted(output['scores'], key=lambda x: x['total'], reverse=True)
        n = args.top or 5
        print(f"\nTOP {n}:")
        for r in sorted_r[:n]:
            print(f"  {r['total']:5.1f}  {r['file']}")
        print(f"\nBOTTOM {n}:")
        for r in sorted_r[-n:]:
            print(f"  {r['total']:5.1f}  {r['file']}")

if __name__ == '__main__':
    main()
