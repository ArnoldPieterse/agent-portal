#!/usr/bin/env python3
"""stealth_ledger_daily.py — engine-ops daily ledger pipeline (Orchestrator lane, assists Scribe G1).

Aggregates memory/builder/stealth/stealth-jobs.log.jsonl into per-day entries in
memory/scribe/stealth-ledger.jsonl so the Day-7 checkpoint (2026-12-02) has real data.

Rules:
- Idempotent per date: re-running recomputes auto fields, keeps the single line for that date.
- Auto fields (staged counts, notes) are overwritten from the log each run.
- Human-confirmed fields (replies, demos, revenue_usd) are NEVER zeroed: kept at max(existing, new).
  (No inbound/revenue source exists yet, so new values for these are always 0.)
- staged per PASS run: detail.batches if present (wf1), else 1.

Usage:
  python stealth_ledger_daily.py            # aggregate log -> ledger (project root cwd)
  python stealth_ledger_daily.py --selftest # synthetic multi-day log, asserts correctness
"""
import ast
import json, sys, tempfile, os, copy
from pathlib import Path

LOG_REL = Path('memory/builder/stealth/stealth-jobs.log.jsonl')
LEDGER_REL = Path('memory/scribe/stealth-ledger.jsonl')
JOBS = ('wf1_ar_followup', 'wf2_weekly_report', 'wf3_reminder_pipeline')


def _staged_for(detail):
    if isinstance(detail, str) and detail.startswith(('{', '[')):
        for loader in (json.loads, ast.literal_eval):  # log writer may emit json OR python repr
            try:
                detail = loader(detail)
                break
            except Exception:
                continue
    if isinstance(detail, dict) and isinstance(detail.get('batches'), int):
        return detail['batches']
    return 1


def aggregate(log_lines):
    """log lines (json dicts {ts, job, status, ...}) -> {date: entry} with auto fields only."""
    by_date = {}
    for raw in log_lines:
        e = json.loads(raw) if isinstance(raw, str) else raw
        ts = e.get('ts', '')
        date = ts[:10]
        job = e.get('job', '')
        status = e.get('status', '')
        if not date or job not in JOBS:
            continue
        d = by_date.setdefault(date, {
            'date': date,
            'outreach_staged': 0, 'replies': 0, 'demos': 0, 'revenue_usd': 0.0,
            'wf1_ar_followup': {'staged': 0, 'replies': 0, 'closed': 0},
            'wf2_weekly_report': {'staged': 0, 'replies': 0, 'closed': 0},
            'wf3_reminder_pipeline': {'staged': 0, 'replies': 0, 'closed': 0},
            '_fails': 0, '_passes': 0,
        })
        if status == 'PASS':
            d['_passes'] += 1
            n = _staged_for(e.get('detail'))
            d['wf1_ar_followup' if job == 'wf1_ar_followup' else job]['staged'] += n
            d['outreach_staged'] += n
        elif status in ('FAIL', 'BUDGET_EXCEEDED', 'INPUT_MISSING'):
            d['_fails'] += 1
    for date, d in by_date.items():
        d['notes'] = (f"auto: {d['_passes']} pass / {d['_fails']} fail job-runs; "
                      f"replies/demos/revenue pending inbound layer")
        d.pop('_fails'); d.pop('_passes')
    return by_date


def merge(ledger_lines, by_date):
    """Merge auto-computed dates into existing ledger lines (idempotent, revenue-safe)."""
    out = {}
    for raw in ledger_lines:
        if not raw.strip():
            continue
        e = json.loads(raw)
        date = e.get('date')
        out[date] = e
    for date, auto in by_date.items():
        prev = copy.deepcopy(out.get(date, {}))
        merged = dict(auto)
        # never zero human-confirmed fields: keep max(existing, auto)
        for k in ('replies', 'demos'):
            merged[k] = max(prev.get(k, 0), auto.get(k, 0))
        merged['revenue_usd'] = max(prev.get('revenue_usd', 0.0), auto.get('revenue_usd', 0.0))
        for wf in JOBS:
            pk = prev.get(wf) or {}
            merged[wf]['replies'] = max(pk.get('replies', 0), merged[wf].get('replies', 0))
            merged[wf]['closed'] = max(pk.get('closed', 0), merged[wf].get('closed', 0))
        prev_note = str(prev.get('notes', ''))
        human_note = prev_note.split(' | auto:')[0] if prev_note else ''
        if human_note and not human_note.startswith('auto:'):
            merged['notes'] = human_note + ' | ' + auto['notes']
        out[date] = merged
    return [out[k] for k in sorted(out)]


def run(root):
    root = Path(root)
    log_lines = (root / LOG_REL).read_text(encoding='utf-8').splitlines() if (root / LOG_REL).exists() else []
    ledger_path = root / LEDGER_REL
    ledger_lines = ledger_path.read_text(encoding='utf-8').splitlines() if ledger_path.exists() else []
    by_date = aggregate(log_lines)
    entries = merge(ledger_lines, by_date)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text('\n'.join(json.dumps(e) for e in entries) + ('\n' if entries else ''), encoding='utf-8')
    return len(entries), sorted(by_date)


def selftest():
    ok = 0
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / LOG_REL).parent.mkdir(parents=True)
        (root / LEDGER_REL).parent.mkdir(parents=True)
        log = [
            {'ts': '2026-11-25T20:58:06', 'job': 'wf1_ar_followup', 'status': 'PASS', 'detail': {'batches': 3}},
            {'ts': '2026-11-25T20:57:36', 'job': 'wf1_ar_followup', 'status': 'FAIL', 'detail': 'x'},
            {'ts': '2026-11-25T21:00:00', 'job': 'wf1_ar_followup', 'status': 'PASS', 'detail': "{'batches': 2}"},  # python-repr detail
            {'ts': '2026-11-26T07:00:12', 'job': 'wf1_ar_followup', 'status': 'PASS', 'detail': {'batches': 5}},
            {'ts': '2026-11-26T08:00:40', 'job': 'wf3_reminder_pipeline', 'status': 'PASS', 'detail': {}},
            {'ts': '2026-11-26T08:01:00', 'job': 'wf3_reminder_pipeline', 'status': 'FAIL', 'detail': 'y'},
            {'ts': '2026-11-27T09:00:00', 'job': 'wf2_weekly_report', 'status': 'PASS', 'detail': {}},
        ]
        (root / LOG_REL).write_text('\n'.join(json.dumps(x) for x in log), encoding='utf-8')
        # seed a human entry with confirmed revenue on 11-26 that must survive re-runs
        (root / LEDGER_REL).write_text(json.dumps({'date': '2026-11-26', 'outreach_staged': 0, 'replies': 2,
                                                   'demos': 1, 'revenue_usd': 250.0,
                                                   'wf1_ar_followup': {'staged': 0, 'replies': 2, 'closed': 1},
                                                   'wf2_weekly_report': {'staged': 0, 'replies': 0, 'closed': 0},
                                                   'wf3_reminder_pipeline': {'staged': 0, 'replies': 0, 'closed': 0},
                                                   'notes': 'human: first client call'}) + '\n', encoding='utf-8')
        n1, dates = run(td)
        e = {json.loads(l)['date']: json.loads(l) for l in (root / LEDGER_REL).read_text(encoding='utf-8').splitlines()}
        # 1. three dates present
        assert sorted(e) == ['2026-11-25', '2026-11-26', '2026-11-27'] and n1 == 3, (sorted(e), n1); ok += 1
        # 2. staged sums: 25th=3+2(repr)=5, 26th=5+1=6, 27th=1
        assert e['2026-11-25']['outreach_staged'] == 5, e['2026-11-25']; ok += 1
        assert e['2026-11-26']['outreach_staged'] == 6, e['2026-11-26']; ok += 1
        assert e['2026-11-27']['wf2_weekly_report']['staged'] == 1; ok += 1
        # 3. human revenue/replies preserved after auto merge
        assert e['2026-11-26']['revenue_usd'] == 250.0 and e['2026-11-26']['replies'] == 2, e['2026-11-26']; ok += 1
        assert 'human: first client call' in e['2026-11-26']['notes'], e['2026-11-26']['notes']; ok += 1
        # 4. idempotent: second run -> identical file
        snap = (root / LEDGER_REL).read_text(encoding='utf-8')
        run(td)
        assert (root / LEDGER_REL).read_text(encoding='utf-8') == snap; ok += 1
        # 5. per-wf attribution on 26th
        assert e['2026-11-26']['wf3_reminder_pipeline']['staged'] == 1, e['2026-11-26']; ok += 1
    print(f'selftest {ok}/8 PASS')
    return ok == 8


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        sys.exit(0 if selftest() else 1)
    n, dates = run('.')
    print(f'ledger updated: {n} day-entries; auto-dates={dates}')
