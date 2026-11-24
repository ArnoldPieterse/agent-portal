#!/usr/bin/env python3
"""Productivity Data Pipeline Monitor.

Verifies productivity-baseline.json is written every hour (check mtime).
If gap >90 min: log warning + trigger re-run of idle_productivity.py.
Track success rate over 7 days.

Usage:
    python memory/mechanic/productivity_pipeline.py            # live check
    python memory/mechanic/productivity_pipeline.py --selftest # run selftests
"""
import json
import os
import pathlib
import time
from datetime import datetime, timezone, timedelta

BASE = pathlib.Path(__file__).resolve().parent.parent.parent
BASELINE_PATH = BASE / 'memory' / 'ops' / 'productivity-baseline.json'
WARNING_PATH = BASE / 'memory' / 'ops' / 'pipeline-warnings.jsonl'
HISTORY_PATH = BASE / 'memory' / 'mechanic' / 'pipeline-history.jsonl'
EXPECTED_INTERVAL_S = 3600   # 1 hour
GAP_THRESHOLD_S = 5400       # 90 minutes
RUN_SCRIPT = 'memory/researcher/idle_productivity.py'


def check_baseline_freshness(threshold: float = GAP_THRESHOLD_S) -> dict:
    """Check if productivity-baseline.json is fresh.
    
    Returns dict with keys:
        status: 'fresh' | 'stale' | 'missing'
        age_s: seconds since last write (None if missing)
        threshold_s: the gap threshold used
    """
    if not BASELINE_PATH.exists():
        return {'status': 'missing', 'age_s': None, 'threshold_s': threshold}
    mtime = os.path.getmtime(BASELINE_PATH)
    age = time.time() - mtime
    status = 'fresh' if age < threshold else 'stale'
    return {'status': status, 'age_s': round(age, 1), 'threshold_s': threshold}


def log_warning(status: str, age_s: float | None) -> pathlib.Path:
    """Append warning to pipeline-warnings.jsonl. Returns path."""
    WARNING_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'status': status,
        'age_s': age_s,
        'action': 're-run triggered'
    }
    with open(WARNING_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')
    return WARNING_PATH


def trigger_rerun() -> dict:
    """Attempt to re-run idle_productivity.py. Returns result dict."""
    import subprocess
    script_path = BASE / RUN_SCRIPT
    if not script_path.exists():
        return {'success': False, 'detail': f'script not found: {RUN_SCRIPT}'}
    try:
        r = subprocess.run(
            ['python', str(script_path)],
            capture_output=True, text=True, timeout=30
        )
        return {
            'success': r.returncode == 0,
            'detail': (r.stdout + r.stderr).strip()[:200]
        }
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return {'success': False, 'detail': str(e)}


def record_check(status: str, fresh: bool) -> None:
    """Record a check result to history for 7-day success rate."""
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'status': status,
        'fresh': fresh
    }
    with open(HISTORY_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')


def compute_success_rate(days: int = 7) -> dict:
    """Compute success rate over last N days from history.
    
    Returns dict with keys: total_checks, fresh_count, rate (0-1), window_days
    """
    if not HISTORY_PATH.exists():
        return {'total_checks': 0, 'fresh_count': 0, 'rate': 0.0, 'window_days': days}
    
    cutoff = time.time() - (days * 86400)
    total = 0
    fresh = 0
    
    with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                ts = datetime.fromisoformat(entry['timestamp']).timestamp()
                if ts >= cutoff:
                    total += 1
                    if entry.get('fresh', False):
                        fresh += 1
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
    
    rate = fresh / total if total > 0 else 0.0
    return {'total_checks': total, 'fresh_count': fresh, 'rate': round(rate, 4), 'window_days': days}


def run_monitor(threshold: float = GAP_THRESHOLD_S) -> dict:
    """Full monitor cycle.
    
    Returns dict with keys:
        status: 'FRESH' | 'STALE_RERUN_OK' | 'STALE_RERUN_FAIL' | 'MISSING'
        age_s, warning_written, rerun_result, success_rate
    """
    health = check_baseline_freshness(threshold)
    fresh = health['status'] == 'fresh'
    record_check(health['status'], fresh)
    
    result = {
        'status': 'FRESH' if fresh else ('MISSING' if health['status'] == 'missing' else 'STALE'),
        'age_s': health['age_s'],
        'warning_written': False,
        'rerun_result': None,
        'success_rate': compute_success_rate()
    }
    
    if fresh:
        return result
    
    # Stale or missing: log warning + trigger rerun
    log_warning(health['status'], health['age_s'])
    result['warning_written'] = True
    
    rr = trigger_rerun()
    result['rerun_result'] = rr
    
    if rr['success']:
        result['status'] = 'STALE_RERUN_OK'
    else:
        result['status'] = 'STALE_RERUN_FAIL' if health['status'] == 'stale' else 'MISSING'
    
    return result


# === SELFTEST ===
def selftest() -> int:
    import tempfile, unittest.mock as mock
    import contextlib
    
    passed = 0
    total = 0
    
    def check(name, cond):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
            print(f"  PASS: {name}")
        else:
            print(f"  FAIL: {name}")
            raise AssertionError(f"Selftest failed: {name}")
    
    def patch_globals(**kwargs):
        @contextlib.contextmanager
        def _patch():
            saved = {}
            for k, v in kwargs.items():
                saved[k] = globals().get(k)
                globals()[k] = v
            try:
                yield
            finally:
                for k, orig in saved.items():
                    if orig is not None:
                        globals()[k] = orig
                    else:
                        globals().pop(k, None)
        return _patch()
    
    # --- Test 1: fresh baseline ---
    with tempfile.TemporaryDirectory() as td:
        fake_base = pathlib.Path(td) / 'productivity-baseline.json'
        fake_base.write_text('{"agents":{}}\n', encoding='utf-8')
        os.utime(fake_base, (time.time(), time.time()))
        
        with patch_globals(BASELINE_PATH=fake_base):
            h = check_baseline_freshness()
            check('fresh: status=fresh', h['status'] == 'fresh')
            check('fresh: age_s < 10', h['age_s'] < 10)
    
    # --- Test 2: stale baseline (2h old) ---
    with tempfile.TemporaryDirectory() as td:
        fake_base = pathlib.Path(td) / 'productivity-baseline.json'
        fake_base.write_text('{}\n', encoding='utf-8')
        old_time = time.time() - 7200
        os.utime(fake_base, (old_time, old_time))
        
        with patch_globals(BASELINE_PATH=fake_base):
            h = check_baseline_freshness()
            check('stale: status=stale', h['status'] == 'stale')
            check('stale: age_s ~ 7200', 7100 < h['age_s'] < 7300)
    
    # --- Test 3: missing baseline ---
    with tempfile.TemporaryDirectory() as td:
        fake_missing = pathlib.Path(td) / 'nope.json'
        
        with patch_globals(BASELINE_PATH=fake_missing):
            h = check_baseline_freshness()
            check('missing: status=missing', h['status'] == 'missing')
            check('missing: age_s is None', h['age_s'] is None)
    
    # --- Test 4: boundary - just under threshold (89 min) ---
    with tempfile.TemporaryDirectory() as td:
        fake_base = pathlib.Path(td) / 'productivity-baseline.json'
        fake_base.write_text('{}\n', encoding='utf-8')
        os.utime(fake_base, (time.time() - 5340, time.time() - 5340))  # 89 min
        
        with patch_globals(BASELINE_PATH=fake_base):
            h = check_baseline_freshness(threshold=5400)
            check('boundary: 89min < 90min = fresh', h['status'] == 'fresh')
    
    # --- Test 5: boundary - just over threshold (91 min) ---
    with tempfile.TemporaryDirectory() as td:
        fake_base = pathlib.Path(td) / 'productivity-baseline.json'
        fake_base.write_text('{}\n', encoding='utf-8')
        os.utime(fake_base, (time.time() - 5460, time.time() - 5460))  # 91 min
        
        with patch_globals(BASELINE_PATH=fake_base):
            h = check_baseline_freshness(threshold=5400)
            check('boundary: 91min > 90min = stale', h['status'] == 'stale')
    
    # --- Test 6: log_warning writes JSONL ---
    with tempfile.TemporaryDirectory() as td:
        fake_warn = pathlib.Path(td) / 'warnings.jsonl'
        
        with patch_globals(WARNING_PATH=fake_warn):
            p = log_warning('stale', 7200.0)
            check('warn: file created', p.exists())
            content = p.read_text(encoding='utf-8')
            entry = json.loads(content.strip())
            check('warn: has timestamp', 'timestamp' in entry)
            check('warn: status=stale', entry['status'] == 'stale')
            check('warn: age_s correct', entry['age_s'] == 7200.0)
    
    # --- Test 7: log_warning appends ---
    with tempfile.TemporaryDirectory() as td:
        fake_warn = pathlib.Path(td) / 'warnings.jsonl'
        
        with patch_globals(WARNING_PATH=fake_warn):
            log_warning('stale', 7200.0)
            log_warning('missing', None)
            lines = fake_warn.read_text(encoding='utf-8').strip().split('\n')
            check('warn append: 2 lines', len(lines) == 2)
    
    # --- Test 8: trigger_rerun success (mocked) ---
    with tempfile.TemporaryDirectory() as td:
        fake_base_dir = pathlib.Path(td)
        # Create the script path so existence check passes
        script_rel = pathlib.Path(RUN_SCRIPT)
        script_abs = fake_base_dir / script_rel
        script_abs.parent.mkdir(parents=True, exist_ok=True)
        script_abs.write_text('#!/usr/bin/env python3\n', encoding='utf-8')
        
        with patch_globals(BASE=fake_base_dir), mock.patch('subprocess.run') as m:
            m.return_value = mock.Mock(returncode=0, stdout='done', stderr='')
            rr = trigger_rerun()
            check('rerun ok: success=True', rr['success'] is True)
    
    # --- Test 9: trigger_rerun failure (script missing) ---
    with tempfile.TemporaryDirectory() as td:
        fake_base_dir = pathlib.Path(td)
        with patch_globals(BASE=fake_base_dir):
            rr = trigger_rerun()
            check('rerun missing script: success=False', rr['success'] is False)
            check('rerun missing script: has detail', 'not found' in rr['detail'])
    
    # --- Test 10: record_check writes to history ---
    with tempfile.TemporaryDirectory() as td:
        fake_hist = pathlib.Path(td) / 'history.jsonl'
        
        with patch_globals(HISTORY_PATH=fake_hist):
            record_check('fresh', True)
            record_check('stale', False)
            content = fake_hist.read_text(encoding='utf-8').strip().split('\n')
            check('history: 2 entries', len(content) == 2)
            e1 = json.loads(content[0])
            check('history: entry1 fresh=True', e1['fresh'] is True)
    
    # --- Test 11: compute_success_rate with data ---
    with tempfile.TemporaryDirectory() as td:
        fake_hist = pathlib.Path(td) / 'history.jsonl'
        now = datetime.now(timezone.utc)
        entries = []
        for i in range(5):
            entries.append({'timestamp': (now - timedelta(hours=i)).isoformat(), 'status': 'fresh', 'fresh': True})
        entries.append({'timestamp': (now - timedelta(hours=6)).isoformat(), 'status': 'stale', 'fresh': False})
        fake_hist.write_text('\n'.join(json.dumps(e) for e in entries) + '\n', encoding='utf-8')
        
        with patch_globals(HISTORY_PATH=fake_hist):
            sr = compute_success_rate(days=7)
            check('rate: total=6', sr['total_checks'] == 6)
            check('rate: fresh=5', sr['fresh_count'] == 5)
            check('rate: rate~0.833', abs(sr['rate'] - 0.8333) < 0.01)
    
    # --- Test 12: compute_success_rate empty history ---
    with tempfile.TemporaryDirectory() as td:
        fake_hist = pathlib.Path(td) / 'nope.jsonl'
        
        with patch_globals(HISTORY_PATH=fake_hist):
            sr = compute_success_rate(days=7)
            check('rate empty: total=0', sr['total_checks'] == 0)
            check('rate empty: rate=0.0', sr['rate'] == 0.0)
    
    # --- Test 13: run_monitor fresh -> FRESH, no actions ---
    with tempfile.TemporaryDirectory() as td:
        fake_base = pathlib.Path(td) / 'productivity-baseline.json'
        fake_base.write_text('{}\n', encoding='utf-8')
        os.utime(fake_base, (time.time(), time.time()))
        fake_hist = pathlib.Path(td) / 'history.jsonl'
        
        with patch_globals(BASELINE_PATH=fake_base, HISTORY_PATH=fake_hist):
            res = run_monitor()
            check('monitor fresh: status=FRESH', res['status'] == 'FRESH')
            check('monitor fresh: no warning', res['warning_written'] is False)
            check('monitor fresh: no rerun', res['rerun_result'] is None)
    
    # --- Test 14: run_monitor stale -> warning + rerun attempt ---
    with tempfile.TemporaryDirectory() as td:
        fake_base_dir = pathlib.Path(td)
        fake_base = fake_base_dir / 'productivity-baseline.json'
        fake_base.write_text('{}\n', encoding='utf-8')
        os.utime(fake_base, (time.time() - 7200, time.time() - 7200))
        fake_warn = fake_base_dir / 'warnings.jsonl'
        fake_hist = fake_base_dir / 'history.jsonl'
        # Create the rerun script so existence check passes
        script_abs = fake_base_dir / RUN_SCRIPT
        script_abs.parent.mkdir(parents=True, exist_ok=True)
        script_abs.write_text('#!/usr/bin/env python3\n', encoding='utf-8')
        
        with patch_globals(BASE=fake_base_dir, BASELINE_PATH=fake_base, WARNING_PATH=fake_warn, HISTORY_PATH=fake_hist), \
             mock.patch('subprocess.run') as m:
            m.return_value = mock.Mock(returncode=0, stdout='ok', stderr='')
            res = run_monitor()
            check('monitor stale: status=STALE_RERUN_OK', res['status'] == 'STALE_RERUN_OK')
            check('monitor stale: warning written', res['warning_written'] is True)
            check('monitor stale: rerun success', res['rerun_result']['success'] is True)
    
    # --- Test 15: run_monitor missing -> MISSING status ---
    with tempfile.TemporaryDirectory() as td:
        fake_missing = pathlib.Path(td) / 'nope.json'
        fake_warn = pathlib.Path(td) / 'warnings.jsonl'
        fake_hist = pathlib.Path(td) / 'history.jsonl'
        
        with patch_globals(BASELINE_PATH=fake_missing, WARNING_PATH=fake_warn, HISTORY_PATH=fake_hist), \
             mock.patch('subprocess.run') as m:
            m.return_value = mock.Mock(returncode=1, stdout='', stderr='err')
            res = run_monitor()
            check('monitor missing: status=MISSING', res['status'] == 'MISSING')
            check('monitor missing: warning written', res['warning_written'] is True)
    
    # --- Test 16: success_rate in result ---
    with tempfile.TemporaryDirectory() as td:
        fake_base = pathlib.Path(td) / 'productivity-baseline.json'
        fake_base.write_text('{}\n', encoding='utf-8')
        os.utime(fake_base, (time.time(), time.time()))
        fake_hist = pathlib.Path(td) / 'history.jsonl'
        
        with patch_globals(BASELINE_PATH=fake_base, HISTORY_PATH=fake_hist):
            res = run_monitor()
            check('result: has success_rate', 'success_rate' in res)
            check('result: success_rate is dict', isinstance(res['success_rate'], dict))
    
    # --- Test 17: config constants ---
    check('config: EXPECTED_INTERVAL_S=3600', EXPECTED_INTERVAL_S == 3600)
    check('config: GAP_THRESHOLD_S=5400', GAP_THRESHOLD_S == 5400)
    
    print(f"  Result: {passed}/{total} passed")
    return passed


if __name__ == '__main__':
    import sys
    if '--selftest' in sys.argv:
        selftest()
        sys.exit(0)
    else:
        res = run_monitor()
        print(json.dumps(res, indent=2))
