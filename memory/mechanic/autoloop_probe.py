#!/usr/bin/env python3
"""Auto-Loop Health Probe.

Verifies the auto-loop is running by checking autoloop.jsonl mtime.
If stale (>5 min during WORK mode): log incident, attempt restart via schtasks,
if restart fails write NEEDS-HUMAN to blockers.md.

Usage:
    python memory/mechanic/autoloop_probe.py            # live check
    python memory/mechanic/autoloop_probe.py --selftest # run selftests
"""
import json
import os
import pathlib
import time
import shutil
from datetime import datetime, timezone

BASE = pathlib.Path(__file__).resolve().parent.parent.parent
AUTOLOOP_PATH = BASE / 'memory' / 'ops' / 'autoloop.jsonl'
INCIDENT_PATH = BASE / 'memory' / 'ops' / 'incidents.md'
BLOCKERS_PATH = BASE / 'memory' / 'ops' / 'blockers.md'
STALE_THRESHOLD_S = 300  # 5 minutes
RESTART_TASK = 'FleetAutoLoop'


def get_autoloop_mtime() -> float | None:
    """Return mtime of autoloop.jsonl or None if missing."""
    if AUTOLOOP_PATH.exists():
        return os.path.getmtime(AUTOLOOP_PATH)
    return None


def check_loop_health(stale_threshold: float = STALE_THRESHOLD_S) -> dict:
    """Check if auto-loop is healthy.
    
    Returns dict with keys:
        status: 'ok' | 'stale' | 'missing'
        age_s: seconds since last write (None if missing)
        threshold_s: the staleness threshold used
    """
    mtime = get_autoloop_mtime()
    now = time.time()
    
    if mtime is None:
        return {'status': 'missing', 'age_s': None, 'threshold_s': stale_threshold}
    
    age = now - mtime
    status = 'ok' if age < stale_threshold else 'stale'
    return {'status': status, 'age_s': round(age, 1), 'threshold_s': stale_threshold}


def log_incident(status: str, age_s: float | None) -> pathlib.Path:
    """Append incident to incidents.md. Returns path."""
    INCIDENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    line = f"\n## [{ts}] AUTOLOOP-PROBE: status={status} age_s={age_s}\n"
    if INCIDENT_PATH.exists():
        with open(INCIDENT_PATH, 'a', encoding='utf-8') as f:
            f.write(line)
    else:
        INCIDENT_PATH.write_text(f"# Incidents Log\n{line}", encoding='utf-8')
    return INCIDENT_PATH


def attempt_restart() -> dict:
    """Attempt to restart the auto-loop scheduled task.
    
    Returns dict with keys: success (bool), method, detail.
    Uses schtasks /run if available; otherwise simulates failure.
    """
    import subprocess
    try:
        r = subprocess.run(
            ['schtasks', '/run', '/tn', RESTART_TASK],
            capture_output=True, text=True, timeout=10
        )
        success = r.returncode == 0
        return {'success': success, 'method': 'schtasks', 'detail': r.stdout.strip() or r.stderr.strip()}
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return {'success': False, 'method': 'schtasks', 'detail': str(e)}


def write_blocker(status: str, age_s: float | None, restart_result: dict) -> pathlib.Path:
    """Write NEEDS-HUMAN entry to blockers.md. Returns path."""
    BLOCKERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    line = (f"\n## [{ts}] NEEDS-HUMAN: autoloop_probe\n"
            f"- status={status} age_s={age_s}\n"
            f"- restart attempted: {restart_result.get('method')} -> success={restart_result.get('success')}\n"
            f"- detail: {restart_result.get('detail', 'n/a')}\n")
    if BLOCKERS_PATH.exists():
        with open(BLOCKERS_PATH, 'a', encoding='utf-8') as f:
            f.write(line)
    else:
        BLOCKERS_PATH.write_text(f"# Blockers Log\n{line}", encoding='utf-8')
    return BLOCKERS_PATH


def run_probe(stale_threshold: float = STALE_THRESHOLD_S) -> dict:
    """Full probe cycle: check, and if stale take recovery actions.
    
    Returns final state dict.
    """
    health = check_loop_health(stale_threshold)
    result = {'health': health, 'actions_taken': []}
    
    if health['status'] == 'ok':
        result['final_status'] = 'HEALTHY'
        return result
    
    # Stale or missing: log incident
    inc_path = log_incident(health['status'], health['age_s'])
    result['actions_taken'].append(f'incident_logged:{inc_path.name}')
    
    # Attempt restart
    rr = attempt_restart()
    result['actions_taken'].append(f'restart_attempted:success={rr["success"]}')
    
    if not rr['success']:
        blk_path = write_blocker(health['status'], health['age_s'], rr)
        result['actions_taken'].append(f'blocker_written:{blk_path.name}')
        result['final_status'] = 'NEEDS_HUMAN'
    else:
        result['final_status'] = 'RESTART_ATTEMPTED'
    
    return result


# === SELFTEST ===
def selftest() -> int:
    """Run selftests. Returns pass count; raises on failure."""
    import tempfile, unittest.mock as mock
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
        """Context manager to temporarily patch module-level globals."""
        import contextlib
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
    
    # --- Test 1: healthy loop (file exists, recent mtime) ---
    with tempfile.TemporaryDirectory() as td:
        fake_loop = pathlib.Path(td) / 'autoloop.jsonl'
        fake_loop.write_text('{"ts":"now"}\n', encoding='utf-8')
        # Make it current
        os.utime(fake_loop, (time.time(), time.time()))
        
        with patch_globals(AUTOLOOP_PATH=fake_loop):
            h = check_loop_health()
            check('healthy: status=ok', h['status'] == 'ok')
            check('healthy: age_s < 5', h['age_s'] < 5)
    
    # --- Test 2: stale loop (file exists, old mtime) ---
    with tempfile.TemporaryDirectory() as td:
        fake_loop = pathlib.Path(td) / 'autoloop.jsonl'
        fake_loop.write_text('{"ts":"old"}\n', encoding='utf-8')
        old_time = time.time() - 600  # 10 min ago
        os.utime(fake_loop, (old_time, old_time))
        
        with patch_globals(AUTOLOOP_PATH=fake_loop):
            h = check_loop_health()
            check('stale: status=stale', h['status'] == 'stale')
            check('stale: age_s ~ 600', 590 < h['age_s'] < 610)
    
    # --- Test 3: missing file ---
    with tempfile.TemporaryDirectory() as td:
        fake_missing = pathlib.Path(td) / 'nonexistent.jsonl'
        
        with patch_globals(AUTOLOOP_PATH=fake_missing):
            h = check_loop_health()
            check('missing: status=missing', h['status'] == 'missing')
            check('missing: age_s is None', h['age_s'] is None)
    
    # --- Test 4: custom threshold ---
    with tempfile.TemporaryDirectory() as td:
        fake_loop = pathlib.Path(td) / 'autoloop.jsonl'
        fake_loop.write_text('{}\n', encoding='utf-8')
        old_time = time.time() - 100  # 100s ago
        os.utime(fake_loop, (old_time, old_time))
        
        with patch_globals(AUTOLOOP_PATH=fake_loop):
            h = check_loop_health(stale_threshold=50)  # 50s threshold
            check('custom threshold: 100s > 50s = stale', h['status'] == 'stale')
            h2 = check_loop_health(stale_threshold=200)  # 200s threshold
            check('custom threshold: 100s < 200s = ok', h2['status'] == 'ok')
    
    # --- Test 5: log_incident writes to file ---
    with tempfile.TemporaryDirectory() as td:
        fake_inc = pathlib.Path(td) / 'incidents.md'
        
        with patch_globals(INCIDENT_PATH=fake_inc):
            p = log_incident('stale', 600.0)
            check('incident: file created', p.exists())
            content = p.read_text(encoding='utf-8')
            check('incident: has status', 'status=stale' in content)
            check('incident: has age', 'age_s=600.0' in content)
    
    # --- Test 6: log_incident appends ---
    with tempfile.TemporaryDirectory() as td:
        fake_inc = pathlib.Path(td) / 'incidents.md'
        
        with patch_globals(INCIDENT_PATH=fake_inc):
            log_incident('stale', 600.0)
            log_incident('missing', None)
            content = fake_inc.read_text(encoding='utf-8')
            check('incident append: has 2 entries', content.count('AUTOLOOP-PROBE') == 2)
    
    # --- Test 7: attempt_restart success (mocked) ---
    with mock.patch('subprocess.run') as m:
        m.return_value = mock.Mock(returncode=0, stdout='OK', stderr='')
        rr = attempt_restart()
        check('restart: success=True', rr['success'] is True)
        check('restart: method=schtasks', rr['method'] == 'schtasks')
    
    # --- Test 8: attempt_restart failure (mocked) ---
    with mock.patch('subprocess.run') as m:
        m.return_value = mock.Mock(returncode=1, stdout='', stderr='Task not found')
        rr = attempt_restart()
        check('restart fail: success=False', rr['success'] is False)
        check('restart fail: has detail', 'Task not found' in rr['detail'])
    
    # --- Test 9: write_blocker ---
    with tempfile.TemporaryDirectory() as td:
        fake_blk = pathlib.Path(td) / 'blockers.md'
        rr = {'success': False, 'method': 'schtasks', 'detail': 'not found'}
        
        with patch_globals(BLOCKERS_PATH=fake_blk):
            p = write_blocker('stale', 600.0, rr)
            check('blocker: file created', p.exists())
            content = p.read_text(encoding='utf-8')
            check('blocker: has NEEDS-HUMAN', 'NEEDS-HUMAN' in content)
            check('blocker: has status', 'status=stale' in content)
            check('blocker: has restart info', 'success=False' in content)
    
    # --- Test 10: run_probe healthy (no actions) ---
    with tempfile.TemporaryDirectory() as td:
        fake_loop = pathlib.Path(td) / 'autoloop.jsonl'
        fake_loop.write_text('{}\n', encoding='utf-8')
        os.utime(fake_loop, (time.time(), time.time()))
        
        with patch_globals(AUTOLOOP_PATH=fake_loop):
            res = run_probe()
            check('run_probe healthy: final=HEALTHY', res['final_status'] == 'HEALTHY')
            check('run_probe healthy: no actions', len(res['actions_taken']) == 0)
    
    # --- Test 11: run_probe stale -> incident + restart success ---
    with tempfile.TemporaryDirectory() as td:
        fake_loop = pathlib.Path(td) / 'autoloop.jsonl'
        fake_loop.write_text('{}\n', encoding='utf-8')
        old_time = time.time() - 600
        os.utime(fake_loop, (old_time, old_time))
        fake_inc = pathlib.Path(td) / 'incidents.md'
        
        with patch_globals(AUTOLOOP_PATH=fake_loop), \
             patch_globals(INCIDENT_PATH=fake_inc), \
             mock.patch('subprocess.run') as m:
            m.return_value = mock.Mock(returncode=0, stdout='OK', stderr='')
            res = run_probe()
            check('run_probe stale: final=RESTART_ATTEMPTED', res['final_status'] == 'RESTART_ATTEMPTED')
            check('run_probe stale: incident logged', any('incident' in a for a in res['actions_taken']))
            check('run_probe stale: restart attempted', any('restart' in a for a in res['actions_taken']))
    
    # --- Test 12: run_probe missing -> incident + restart fail -> blocker ---
    with tempfile.TemporaryDirectory() as td:
        fake_loop = pathlib.Path(td) / 'nonexistent.jsonl'
        fake_inc = pathlib.Path(td) / 'incidents.md'
        fake_blk = pathlib.Path(td) / 'blockers.md'
        
        with patch_globals(AUTOLOOP_PATH=fake_loop), \
             patch_globals(INCIDENT_PATH=fake_inc), \
             patch_globals(BLOCKERS_PATH=fake_blk), \
             mock.patch('subprocess.run') as m:
            m.return_value = mock.Mock(returncode=1, stdout='', stderr='Task not found')
            res = run_probe()
            check('run_probe missing: final=NEEDS_HUMAN', res['final_status'] == 'NEEDS_HUMAN')
            check('run_probe missing: blocker written', fake_blk.exists())
            check('run_probe missing: 3 actions', len(res['actions_taken']) == 3)
    
    # --- Test 13: boundary - exactly at threshold is stale (not <) ---
    with tempfile.TemporaryDirectory() as td:
        fake_loop = pathlib.Path(td) / 'autoloop.jsonl'
        fake_loop.write_text('{}\n', encoding='utf-8')
        # Set mtime to exactly 300s ago
        exact_old = time.time() - 300.5
        os.utime(fake_loop, (exact_old, exact_old))
        
        with patch_globals(AUTOLOOP_PATH=fake_loop):
            h = check_loop_health(stale_threshold=300)
            check('boundary: 300.5s > 300s threshold = stale', h['status'] == 'stale')
    
    # --- Test 14: just under threshold is ok ---
    with tempfile.TemporaryDirectory() as td:
        fake_loop = pathlib.Path(td) / 'autoloop.jsonl'
        fake_loop.write_text('{}\n', encoding='utf-8')
        just_recent = time.time() - 299
        os.utime(fake_loop, (just_recent, just_recent))
        
        with patch_globals(AUTOLOOP_PATH=fake_loop):
            h = check_loop_health(stale_threshold=300)
            check('boundary: 299s < 300s threshold = ok', h['status'] == 'ok')
    
    # --- Test 15: get_autoloop_mtime returns None for missing ---
    with tempfile.TemporaryDirectory() as td:
        fake_missing = pathlib.Path(td) / 'nope.jsonl'
        with patch_globals(AUTOLOOP_PATH=fake_missing):
            m = get_autoloop_mtime()
            check('get_mtime: None for missing', m is None)
    
    print(f"  Result: {passed}/{total} passed")
    return passed


if __name__ == '__main__':
    import sys
    if '--selftest' in sys.argv:
        n = selftest()
        sys.exit(0)
    else:
        res = run_probe()
        print(json.dumps(res, indent=2))
