#!/usr/bin/env python3
"""Evidence Quality Scoring (Researcher goal #6, cycle-7).

Scores every `(verified: ...)` marker in memory/goals/*.md on three axes:
  - specificity  (0-40): names a concrete file path / command / endpoint
  - reproducibility (0-35): contains a re-runnable command or explicit pass/output criterion
  - recency    (0-25): dated within the last 7 days of the reference date
Total 0-100. Exposes `score_marker()` + `scan_goals()` for the /api/evidence/quality endpoint.

Usage:
  python memory/researcher/evidence_quality.py            # score all goal files -> JSON + md report
  python memory/researcher/evidence_quality.py --selftest # prove threshold behaviour (vague<30, specific>80)
  python memory/researcher/evidence_quality.py --json     # machine-readable to stdout
"""
import os, re, json, datetime, argparse

TODAY = datetime.date(2026, 11, 20)  # fixed ref date for deterministic scoring in this pass

def _extract_date(text):
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None

def score_marker(marker_text):
    """Score one (verified: ...) marker body on 0-100. Returns dict of subscores + total."""
    t = marker_text.lower()
    spec, repro, rec = 0, 0, 0

    # --- specificity (0-40) ---
    has_path = bool(re.search(r'\.[a-z]{2,5}\b', t)) and bool(
        re.search(r'memory/|\.py|\.json|\.md|\.jsonl|ui/', t))
    has_endpoint = '/api/' in t
    if has_path:
        spec += 25
    if has_endpoint:
        spec += 15
    # named command (python ... / curl ...) also signals specificity
    if re.search(r'\b(python|curl)\s+\S+', t):
        spec = min(40, spec + 10)

    # --- reproducibility (0-35) ---
    rerun = bool(re.search(r'\bpython\s+[\w./]+\.py', t)) or has_endpoint
    explicit = bool(re.search(r'\b(pass|returns?|output|generated|written|built|ran|scored|coverage)\b', t))
    if rerun:
        repro += 20
    if explicit:
        repro += 15

    # --- recency (0-25) ---
    d = _extract_date(marker_text)
    if d is not None:
        age = abs((TODAY - d).days)
        rec = 25 if age <= 7 else (12 if age <= 14 else 0)

    total = spec + repro + rec
    return {
        "specificity": spec, "reproducibility": repro, "recency": rec, "total": total,
        "has_path": has_path, "has_endpoint": has_endpoint,
        "rerunnable_cmd": rerun, "explicit_criterion": explicit,
        "dated": d.isoformat() if d else None,
    }

_GOAL_LINE = re.compile(r'^\s*(\d+)\.\s+\*\*(.+?)\*\*')
_VERIFIED = re.compile(r'\(verified:\s*(.+?)\)\s*$', re.IGNORECASE)

def scan_goals(goals_dir):
    """Return list of per-marker records + fleet summary across memory/goals/*.md."""
    records = []
    for fn in sorted(os.listdir(goals_dir)):
        if not fn.endswith('.md'):
            continue
        agent = fn[:-3]
        path = os.path.join(goals_dir, fn)
        cur_goal = None
        for line in open(path, encoding='utf-8', errors='ignore').read().splitlines():
            gm = _GOAL_LINE.match(line)
            if gm:
                cur_goal = (gm.group(1), gm.group(2).strip())
            vm = _VERIFIED.search(line.strip())
            if vm and cur_goal:
                body = vm.group(1).strip()
                s = score_marker(body)
                records.append({"agent": agent, "goal": cur_goal[0],
                                "title": cur_goal[1][:60], "marker": body[:200], **s})
    totals = [r['total'] for r in records]
    fleet_avg = round(sum(totals)/len(totals), 1) if totals else None
    return {"generated": TODAY.isoformat(), "markers_scored": len(records),
            "fleet_avg": fleet_avg, "records": records}

def _selftest():
    vague = score_marker("it works")
    specific = score_marker("2026-11-20 - python memory/researcher/kb_index.py ran: memory/INDEX-kb.json generated, 1859 files, coverage 100% PASS")
    stale_specific = score_marker("2026-10-01 - python x.py generated report.md")
    ok = vague['total'] < 30 and specific['total'] > 80
    print(json.dumps({"vague": vague, "specific_recent": specific,
                      "specific_stale": stale_specific,
                      "threshold_check": "PASS" if ok else "FAIL",}, indent=2))
    return ok

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    if args.selftest:
        raise SystemExit(0 if _selftest() else 1)

    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(here))  # memory/researcher -> repo root
    goals = os.path.join(root, 'memory', 'goals')
    res = scan_goals(goals)
    if args.json:
        print(json.dumps(res, indent=2))
        return
    out_json = os.path.join(here, 'evidence-quality-2026-11-20.json')
    open(out_json, 'w').write(json.dumps(res, indent=2))
    # markdown report
    lines = ["# Evidence Quality Scoring - 2026-11-20", "",
             f"Markers scored: **{res['markers_scored']}** | Fleet avg: **{res['fleet_avg']}/100**", "",
             "| agent | goal | specificity | repro | recency | total | title |", "|---|---|---|---|---|---|---|"]
    for r in res['records']:
        lines.append(f"| {r['agent']} | #{r['goal']} | {r['specificity']} | {r['reproducibility']} | {r['recency']} | **{r['total']}** | {r['title'][:40]} |")
    report = os.path.join(here, 'evidence-quality-2026-11-20.md')
    open(report, 'w').write('\n'.join(lines) + '\n')
    print(f"{res['markers_scored']} markers scored; fleet avg {res['fleet_avg']}/100")
    print(f"wrote: {os.path.relpath(out_json, root)}\nwrote: {os.path.relpath(report, root)}")

if __name__ == '__main__':
    main()
