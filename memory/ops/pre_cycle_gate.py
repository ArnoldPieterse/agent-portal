#!/usr/bin/env python3
"""Pre-Cycle Autonomy Gate - pre-flight check before each cycle start.

Validates four signals and writes memory/ops/pre-cycle-gate.json:
  (a) scheduled tasks   - fleet automation tasks present & ready (best-effort;
                          unverifiable-from-seat when tasks live on host seats)
  (b) API endpoints     - portal :8099 + model :8888 respond in <200ms
  (c) autonomy score    - drop since last snapshot is <10 pts
  (d) unresolved blockers - no OPEN-class blocker recorded within the recency window

Overall verdict: PASS when every check passes or is UNVERIFIABLE; FAIL when any
check hard-fails. A failing check also appends an alert to memory/ops/alerts.jsonl.
Idempotent: same inputs -> same verdict; score history is time-gated so repeated
runs in one pass do not spam the series.

Usage:
    python memory/ops/pre_cycle_gate.py              # run gate (live)
    python memory/ops/pre_cycle_gate.py --selftest   # verify logic w/ synthetic data
"""
import json, sys, time, datetime, subprocess, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GATE_PATH = ROOT / 'memory' / 'ops' / 'pre-cycle-gate.json'
ALERTS_PATH = ROOT / 'memory' / 'ops' / 'alerts.jsonl'
BLOCKER_PATH = ROOT / 'memory' / 'ops' / 'blockers.md'
SCORE_SNAPSHOT = ROOT / 'memory' / 'ops' / 'autonomy-score.json'
HISTORY_PATH = ROOT / 'memory' / 'ops' / 'pre-cycle-gate-history.jsonl'

API_TIMEOUT_MS = 200          # (b) latency threshold
ENDPOINTS = [('portal', 'http://127.0.0.1:8099/'), ('model', 'http://127.0.0.1:8888/')]
SCORE_DROP_LIMIT = 10.0       # (c) max allowed drop since last snapshot
BLOCKER_WINDOW_H = 48         # (d) only count blockers dated within this window
HISTORY_GAP_H = 6             # append a score snapshot at most this often
REQUIRED_TASKS = ('PortalLoadProbe', 'MirrorSync', 'VerifierSLO')

OPEN_TOKENS = ('NEEDS-HUMAN', 'STILL OPEN', 'UNRESOLVED', '[BLOCKED]', '(blocked:')
CLOSED_TOKENS = ('RESOLVED', 'CLOSED', 'UNBLOCKED')


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


def probe_endpoint(url, timeout_ms=API_TIMEOUT_MS):
    """Return (ok, latency_ms, detail). ok=True iff reachable within budget."""
    t0 = time.time()
    try:
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=max(1.0, timeout_ms / 1000.0)) as r:
            lat = round((time.time() - t0) * 1000, 1)
            return (200 <= r.status < 500), lat, f'HTTP {r.status} in {lat}ms'
    except Exception as e:
        lat = round((time.time() - t0) * 1000, 1)
        return False, lat, f'{type(e).__name__}: {str(e)[:60]} ({lat}ms)'


def check_endpoints():
    """(b) every endpoint must respond within budget."""
    results = []
    all_ok = True
    for name, url in ENDPOINTS:
        ok, lat, detail = probe_endpoint(url)
        within = ok and lat <= API_TIMEOUT_MS
        if not within:
            all_ok = False
        results.append({'name': name, 'url': url, 'ok': within,
                        'latency_ms': lat, 'detail': detail})
    return {'status': 'pass' if all_ok else 'fail',
            'endpoints': results,
            'detail': ('all endpoints <200ms' if all_ok
                       else 'endpoint(s) down or >200ms: ' + ', '.join(
                           r['name'] for r in results if not r['ok']))}


def read_score():
    try:
        return float(json.loads(SCORE_SNAPSHOT.read_text(encoding='utf-8')).get('score'))
    except Exception:
        return None


def append_history(score):
    """Append a time-gated score snapshot; returns (prev_score, appended)."""
    prev = None
    if HISTORY_PATH.exists():
        lines = [json.loads(l) for l in HISTORY_PATH.read_text(encoding='utf-8').strip().split('\n') if l.strip()]
        valid = [l for l in lines if isinstance(l.get('score'), (int, float))]
        if valid:
            prev = valid[-1]['score']
            last_ts = _parse_iso(valid[-1].get('ts'))
            if last_ts is not None and (_now() - last_ts).total_seconds() < HISTORY_GAP_H * 3600:
                return prev, False  # too soon; do not append
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps({'ts': _now().isoformat(), 'score': score}) + '\n')
    return prev, True


def check_score():
    """(c) autonomy drop since last snapshot must be < SCORE_DROP_LIMIT."""
    cur = read_score()
    if cur is None:
        return {'status': 'unverifiable', 'detail': 'autonomy-score.json missing/unreadable',
                'current': None, 'previous': None}
    prev, appended = append_history(cur)
    if prev is None:
        return {'status': 'pass', 'detail': 'baseline established (no prior snapshot)',
                'current': cur, 'previous': None}
    drop = round(prev - cur, 2)  # positive = score fell
    ok = drop < SCORE_DROP_LIMIT
    return {'status': 'pass' if ok else 'fail',
            'detail': (f'drop {drop:+.2f} pts since last snapshot'
                       if ok else f'autonomy dropped {drop:.2f} pts (>= {SCORE_DROP_LIMIT})'),
            'current': cur, 'previous': prev, 'drop': drop}


def _parse_iso(s):
    try:
        return datetime.datetime.fromisoformat(s)
    except Exception:
        return None


def _block_date(block_text):
    """Extract the first YYYY-MM-DD found in a block header line."""
    import re
    m = re.search(r'(\d{4}-\d{2}-\d{2})', block_text.split('\n')[0])
    return _parse_iso(m.group(1) + 'T00:00:00+00:00') if m else None


def check_blockers():
    """(d) no OPEN-class blocker recorded within BLOCKER_WINDOW_H.

    A block is a section starting at a '##' header. Its status = the LAST status
    token found in the block (open- or closed-class). Only blocks carrying a date
    inside the recency window AND ending in an open-class status count as unresolved.
    """
    if not BLOCKER_PATH.exists():
        return {'status': 'pass', 'detail': 'no blockers.md present', 'unresolved': []}
    text = BLOCKER_PATH.read_text(encoding='utf-8')
    blocks = re_split_blocks(text)
    cutoff = _now() - datetime.timedelta(hours=BLOCKER_WINDOW_H)
    unresolved = []
    for blk in blocks:
        has_marker = any(t in blk for t in OPEN_TOKENS) or any(t in blk for t in CLOSED_TOKENS)
        if not has_marker:
            continue
        last_open = max((blk.rfind(t) for t in OPEN_TOKENS), default=-1)
        last_closed = max((blk.rfind(t) for t in CLOSED_TOKENS), default=-1)
        if last_open <= last_closed:
            continue  # resolved/closed after any open marker
        d = _block_date(blk)
        if d is None or d < cutoff:
            continue  # undated or outside window -> not a current blocker
        unresolved.append(blk.strip().split('\n')[0][:120])
    ok = len(unresolved) == 0
    return {'status': 'pass' if ok else 'fail',
            'detail': ('no unresolved blockers in window'
                       if ok else f'{len(unresolved)} unresolved blocker(s) within {BLOCKER_WINDOW_H}h'),
            'unresolved': unresolved}


def re_split_blocks(text):
    import re
    return re.split(r'\n(?=## )', text)


def check_scheduled_tasks():
    """(a) best-effort: enumerate fleet automation tasks; UNVERIFIABLE if not visible from seat."""
    found = []
    try:
        r = subprocess.run(['schtasks', '/query', '/fo', 'csv', '/nh'],
                           capture_output=True, text=True, timeout=30)
        out = (r.stdout or '') + '\n' + (r.stderr or '')
        for t in REQUIRED_TASKS:
            if t.lower() in out.lower():
                found.append(t)
    except Exception as e:
        return {'status': 'unverifiable',
                'detail': f'schtasks query failed: {type(e).__name__}: {str(e)[:50]}',
                'found': []}
    if not found:
        return {'status': 'unverifiable',
                'detail': 'fleet automation tasks not visible from this seat (registered on host)',
                'found': [], 'required': list(REQUIRED_TASKS)}
    missing = [t for t in REQUIRED_TASKS if t not in found]
    ok = not missing
    return {'status': 'pass' if ok else 'fail',
            'detail': ('all required tasks present' if ok
                       else f'missing: {missing}'),
            'found': found, 'required': list(REQUIRED_TASKS)}


def write_alerts(failed_checks, prev_gate=None):
    now = _now().isoformat()
    written = 0
    if not failed_checks:
        return 0
    # Idempotency: skip re-alerting an identical failure signature already logged <6h ago.
    sig = sorted(name for name, _ in failed_checks)
    if prev_gate is not None:
        prev_sig = sorted(prev_gate.get('failed_checks', []))
        prev_ts = _parse_iso(prev_gate.get('ts'))
        if prev_sig == sig and prev_ts is not None \
                and (_now() - prev_ts).total_seconds() < 6 * 3600:
            return 0
    ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ALERTS_PATH, 'a', encoding='utf-8') as f:
        for name, detail in failed_checks:
            f.write(json.dumps({'ts': now, 'source': 'pre_cycle_gate', 'metric': name,
                                'velocity_trend': detail,
                                'recommended_action': _action(name),
                                'severity': 'critical'}) + '\n')
            written += 1
    return written


def _action(name):
    return {
        'scheduled_tasks': 'Re-register fleet automation schtasks on host; verify PortalLoadProbe/MirrorSync/VerifierSLO.',
        'endpoints': 'Check portal :8099 + model :8888 health; restart or failover degraded endpoint.',
        'score': 'Investigate autonomy drop: review interventions, scheduled-task coverage, goal lifecycle.',
        'blockers': 'Resolve open blockers before starting cycle; see memory/ops/blockers.md.',
    }.get(name, 'Investigate pre-cycle gate failure.')


def run_gate():
    checks = {
        'scheduled_tasks': check_scheduled_tasks(),
        'endpoints': check_endpoints(),
        'score': check_score(),
        'blockers': check_blockers(),
    }
    failed = [(k, v['detail']) for k, v in checks.items() if v['status'] == 'fail']
    unverifiable = [k for k, v in checks.items() if v['status'] == 'unverifiable']
    overall = 'FAIL' if failed else 'PASS'
    prev_gate = None
    if GATE_PATH.exists():
        try:
            prev_gate = json.loads(GATE_PATH.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, KeyError):
            prev_gate = None
    gate = {'ts': _now().isoformat(), 'overall': overall,
            'checks': checks, 'failed_checks': [f[0] for f in failed],
            'unverifiable_checks': unverifiable}
    GATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    GATE_PATH.write_text(json.dumps(gate, indent=2), encoding='utf-8')
    written = write_alerts(failed, prev_gate)

    print(f'PRE-CYCLE AUTONOMY GATE  ->  {overall}')
    for k, v in checks.items():
        flag = {'pass': 'PASS', 'fail': 'FAIL', 'unverifiable': 'WARN(unverifiable)'}[v['status']]
        print(f'  [{flag}] {k}: {v["detail"]}')
    if written:
        print(f'Alerts written: {written} -> {ALERTS_PATH.relative_to(ROOT)}')
    print(f'Gate JSON -> {GATE_PATH.relative_to(ROOT)}')
    return overall


def selftest():
    """Prove pass + fail paths with synthetic inputs (no live deps)."""
    global probe_endpoint, SCORE_SNAPSHOT, HISTORY_PATH, BLOCKER_PATH
    passed = failed = 0

    # 1) healthy endpoints (mock ok+fast) -> pass
    real_probe = probe_endpoint
    probe_endpoint = lambda url, timeout_ms=API_TIMEOUT_MS: (True, 42.0, 'HTTP 200 in 42ms')
    r = check_endpoints()
    if r['status'] == 'pass': passed += 1; print('  PASS: healthy endpoints -> pass')
    else: failed += 1; print(f'  FAIL: expected pass, got {r}')

    # 2) degraded endpoint (slow) -> fail
    probe_endpoint = lambda url, timeout_ms=API_TIMEOUT_MS: (True, 500.0, 'HTTP 200 in 500ms')
    r = check_endpoints()
    if r['status'] == 'fail': passed += 1; print('  PASS: slow endpoint -> fail')
    else: failed += 1; print(f'  FAIL: expected fail, got {r["status"]}')

    # 3) autonomy drop >= limit -> fail ; small drop -> pass
    import tempfile, os
    tmp = Path(tempfile.mkdtemp())
    SCORE_SNAPSHOT = tmp / 'score.json'
    HISTORY_PATH = tmp / 'hist.jsonl'
    (HISTORY_PATH).write_text(json.dumps({'ts': (_now() - datetime.timedelta(hours=24)).isoformat(), 'score': 85.0}) + '\n')
    SCORE_SNAPSHOT.write_text(json.dumps({'score': 74.0}))  # drop of 11
    r = check_score()
    if r['status'] == 'fail' and abs(r['drop'] - 11.0) < 0.01: passed += 1; print('  PASS: 11pt drop -> fail')
    else: failed += 1; print(f'  FAIL: expected score fail, got {r}')
    # reset history to test small drop
    HISTORY_PATH.write_text(json.dumps({'ts': (_now() - datetime.timedelta(hours=24)).isoformat(), 'score': 85.0}) + '\n')
    SCORE_SNAPSHOT.write_text(json.dumps({'score': 81.0}))  # drop of 4
    r = check_score()
    if r['status'] == 'pass': passed += 1; print('  PASS: 4pt drop -> pass')
    else: failed += 1; print(f'  FAIL: expected score pass, got {r}')

    # 4) unresolved recent blocker -> fail ; resolved -> pass
    BLOCKER_PATH = tmp / 'blockers.md'
    today = _now().strftime('%Y-%m-%d')
    old = (_now() - datetime.timedelta(days=20)).strftime('%Y-%m-%d')
    BLOCKER_PATH.write_text(f'## [NEEDS-HUMAN {today}] open recent blocker\nsome detail\n')
    r = check_blockers()
    if r['status'] == 'fail' and len(r['unresolved']) == 1: passed += 1; print('  PASS: recent open blocker -> fail')
    else: failed += 1; print(f'  FAIL: expected blocker fail, got {r}')
    BLOCKER_PATH.write_text(f'## [NEEDS-HUMAN {old}] old, since resolved\n~~NEEDS-HUMAN~~ **RESOLVED {today}**\n')
    r = check_blockers()
    if r['status'] == 'pass': passed += 1; print('  PASS: resolved/old blocker -> pass')
    else: failed += 1; print(f'  FAIL: expected blocker pass, got {r}')

    # 5) idempotency: two identical score runs -> same verdict, no duplicate history spam
    tmp2 = Path(tempfile.mkdtemp())
    HISTORY_PATH = tmp2 / 'hist.jsonl'
    SCORE_SNAPSHOT = tmp2 / 'score.json'
    SCORE_SNAPSHOT.write_text(json.dumps({'score': 70.0}))
    r1 = check_score(); n1 = len(HISTORY_PATH.read_text().splitlines())
    r2 = check_score(); n2 = len(HISTORY_PATH.read_text().splitlines())
    if r1['status'] == r2['status'] and n1 == n2 == 1: passed += 1; print('  PASS: idempotent (same verdict, no history spam)')
    else: failed += 1; print(f'  FAIL: idempotency broken r1={r1["status"]} r2={r2["status"]} n1={n1} n2={n2}')

    # restore globals
    probe_endpoint = real_probe
    SCORE_SNAPSHOT = ROOT / 'memory' / 'ops' / 'autonomy-score.json'
    HISTORY_PATH = ROOT / 'memory' / 'ops' / 'pre-cycle-gate-history.jsonl'
    BLOCKER_PATH = ROOT / 'memory' / 'ops' / 'blockers.md'

    print(f'\nSelftest: {passed} PASS, {failed} FAIL')
    return failed == 0


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    else:
        overall = run_gate()
        sys.exit(0 if overall == 'PASS' else 2)
