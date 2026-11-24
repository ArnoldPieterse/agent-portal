#!/usr/bin/env python3
"""Auto-Loop Restart Guard.

Watchdog that checks if auto-loop produced output in last 5 min.
If not: attempt restart (schtasks /run), wait, check again.
If still dead after 2 attempts: write incident to memory/ops/incidents.md.

Usage:
    python memory/mechanic/loop_guard.py            # live check
    python memory/mechanic/loop_guard.py --selftest # run selftests
"""
import json
import os
import pathlib
import time
from datetime import datetime, timezone

BASE = pathlib.Path(__file__).resolve().parent.parent.parent
AUTOLOOP_PATH = BASE / 'memory' / 'ops' / 'autoloop.jsonl'
INCIDENT_PATH = BASE / 'memory' / 'ops' / 'incidents.md'
STALE_THRESHOLD_S = 300  # 5 minutes
MAX_RESTART_ATTEMPTS = 2
RESTART_TASK = 'FleetAutoLoop'
WAIT_BETWEEN_CHECKS_S = 60  # in production; overridden in selftest


def check_output_recent(threshold: float = STALE_THRESHOLD_S) -> bool:
    """Check if autoloop.jsonl was written within threshold seconds."""
    if not AUTOLOOP_PATH.exists():
        return False
    mtime = os.path.getmtime(AUTOLOOP_PATH)
    return (time.time() - mtime) < threshold


def attempt_restart(attempt_num: int) -> dict:
    """Attempt to restart the scheduled task. Returns result dict."""
    import subprocess
    try:
        r = subprocess.run(
            ['schtasks', '/run', '/tn', RESTART_TASK],
            capture_output=True, text=True, timeout=10
        )
        return {
            'attempt': attempt_num,
            'success': r.returncode == 0,
            'output': (r.stdout + r.stderr).strip()
        }
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return {'attempt': attempt_num, 'success': False, 'output': str(e)}


def write_incident(attempts: list[dict]) -> pathlib.Path:
    """Write incident after all restart attempts failed."""
    INCIDENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    lines = [f"\n## [{ts}] LOOP-GUARD: auto-loop dead after {len(attempts)} restart attempts\n"]
    for a in attempts:
        lines.append(f"- attempt {a['attempt']}: success={a['success']} output={a['output'][:100]}\n")
    if INCIDENT_PATH.exists():
        with open(INCIDENT_PATH, 'a', encoding='utf-8') as f:
            f.writelines(lines)
    else:
        INCIDENT_PATH.write_text(f"# Incidents Log\n{''.join(lines)}", encoding='utf-8')
    return INCIDENT_PATH


def run_guard(threshold: float = STALE_THRESHOLD_S, wait_s: float = 0) -> dict:
    """Run the guard cycle.
    
    Args:
        threshold: staleness threshold in seconds
        wait_s: time to wait between restart attempts (0 in selftest)
    
    Returns:
        dict with status, attempts list, incident_written flag
    """
    # Initial check
    if check_output_recent(threshold):
        return {'status': 'HEALTHY', 'attempts': [], 'incident_written': False}
    
    # Loop is stale: attempt restarts
    attempts = []
    for i in range(1, MAX_RESTART_ATTEMPTS + 1):
        result = attempt_restart(i)
        attempts.append(result)
        if wait_s > 0:
            time.sleep(wait_s)
        # Re-check after restart
        if check_output_recent(threshold):
            return {'status': 'RECOVERED', 'attempts': attempts, 'incident_written': False}
    
    # All attempts failed: write incident
    inc_path = write_incident(attempts)
    return {'status': 'DEAD', 'attempts': attempts, 'incident_written': True}


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
    
    # --- Test 1: healthy loop -> HEALTHY ---
    with tempfile.TemporaryDirectory() as td:
        fake_loop = pathlib.Path(td) / 'autoloop.jsonl'
        fake_loop.write_text('{}\n', encoding='utf-8')
        os.utime(fake_loop, (time.time(), time.time()))
        
        with patch_globals(AUTOLOOP_PATH=fake_loop):
            res = run_guard()
            check('healthy: status=HEALTHY', res['status'] == 'HEALTHY')
            check('healthy: no attempts', len(res['attempts']) == 0)
    
    # --- Test 2: stale + restart succeeds -> RECOVERED ---
    with tempfile.TemporaryDirectory() as td:
        fake_loop = pathlib.Path(td) / 'autoloop.jsonl'
        old_time = time.time() - 600
        fake_loop.write_text('{}\n', encoding='utf-8')
        os.utime(fake_loop, (old_time, old_time))
        
        # Mock: after restart, file gets new mtime
        call_count = [0]
        def fake_run(*args, **kwargs):
            call_count[0] += 1
            # Simulate that the restart fixes the file
            os.utime(fake_loop, (time.time(), time.time()))
            return mock.Mock(returncode=0, stdout='OK', stderr='')
        
        with patch_globals(AUTOLOOP_PATH=fake_loop), \
             mock.patch('subprocess.run', side_effect=fake_run):
            res = run_guard(wait_s=0)
            check('recovered: status=RECOVERED', res['status'] == 'RECOVERED')
            check('recovered: 1 attempt', len(res['attempts']) == 1)
            check('recovered: no incident', res['incident_written'] is False)
    
    # --- Test 3: stale + all restarts fail -> DEAD + incident ---
    with tempfile.TemporaryDirectory() as td:
        fake_loop = pathlib.Path(td) / 'nonexistent.jsonl'
        fake_inc = pathlib.Path(td) / 'incidents.md'
        
        def fake_run_fail(*args, **kwargs):
            return mock.Mock(returncode=1, stdout='', stderr='Task not found')
        
        with patch_globals(AUTOLOOP_PATH=fake_loop, INCIDENT_PATH=fake_inc), \
             mock.patch('subprocess.run', side_effect=fake_run_fail):
            res = run_guard(wait_s=0)
            check('dead: status=DEAD', res['status'] == 'DEAD')
            check('dead: 2 attempts', len(res['attempts']) == 2)
            check('dead: incident written', res['incident_written'] is True)
            check('dead: incident file exists', fake_inc.exists())
            content = fake_inc.read_text(encoding='utf-8')
            check('dead: incident has LOOP-GUARD', 'LOOP-GUARD' in content)
            check('dead: incident has attempt count', '2 restart attempts' in content)
    
    # --- Test 4: missing file -> treated as stale ---
    with tempfile.TemporaryDirectory() as td:
        fake_missing = pathlib.Path(td) / 'nope.jsonl'
        
        with patch_globals(AUTOLOOP_PATH=fake_missing):
            recent = check_output_recent()
            check('missing: not recent', recent is False)
    
    # --- Test 5: check_output_recent boundary ---
    with tempfile.TemporaryDirectory() as td:
        fake_loop = pathlib.Path(td) / 'autoloop.jsonl'
        fake_loop.write_text('{}\n', encoding='utf-8')
        # Exactly at threshold (slightly over)
        os.utime(fake_loop, (time.time() - 301, time.time() - 301))
        
        with patch_globals(AUTOLOOP_PATH=fake_loop):
            check('boundary: 301s > 300s = not recent', check_output_recent(300) is False)
            # Well under
            os.utime(fake_loop, (time.time() - 100, time.time() - 100))
            check('boundary: 100s < 300s = recent', check_output_recent(300) is True)
    
    # --- Test 6: restart attempt result structure ---
    with mock.patch('subprocess.run') as m:
        m.return_value = mock.Mock(returncode=0, stdout='Started', stderr='')
        r = attempt_restart(1)
        check('restart struct: attempt=1', r['attempt'] == 1)
        check('restart struct: success=True', r['success'] is True)
        check('restart struct: has output', 'Started' in r['output'])
    
    # --- Test 7: restart failure structure ---
    with mock.patch('subprocess.run') as m:
        m.return_value = mock.Mock(returncode=1, stdout='', stderr='Access denied')
        r = attempt_restart(2)
        check('restart fail: success=False', r['success'] is False)
        check('restart fail: attempt=2', r['attempt'] == 2)
    
    # --- Test 8: subprocess exception handling ---
    with mock.patch('subprocess.run') as m:
        m.side_effect = FileNotFoundError('schtasks not found')
        r = attempt_restart(1)
        check('exception: success=False', r['success'] is False)
        check('exception: has error detail', 'not found' in r['output'])
    
    # --- Test 9: incident content accuracy ---
    with tempfile.TemporaryDirectory() as td:
        fake_inc = pathlib.Path(td) / 'incidents.md'
        attempts = [
            {'attempt': 1, 'success': False, 'output': 'err1'},
            {'attempt': 2, 'success': False, 'output': 'err2'},
        ]
        with patch_globals(INCIDENT_PATH=fake_inc):
            write_incident(attempts)
            content = fake_inc.read_text(encoding='utf-8')
            check('incident: has attempt 1', 'attempt 1' in content)
            check('incident: has attempt 2', 'attempt 2' in content)
            check('incident: has err1', 'err1' in content)
            check('incident: has err2', 'err2' in content)
    
    # --- Test 10: second restart succeeds -> RECOVERED with 2 attempts ---
    with tempfile.TemporaryDirectory() as td:
        fake_loop = pathlib.Path(td) / 'autoloop.jsonl'
        fake_loop.write_text('{}\n', encoding='utf-8')
        os.utime(fake_loop, (time.time() - 600, time.time() - 600))
        
        call_count = [0]
        def fake_run_partial(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                # Second attempt fixes it
                os.utime(fake_loop, (time.time(), time.time()))
            return mock.Mock(returncode=0, stdout='OK', stderr='')
        
        with patch_globals(AUTOLOOP_PATH=fake_loop), \
             mock.patch('subprocess.run', side_effect=fake_run_partial):
            res = run_guard(wait_s=0)
            check('partial: status=RECOVERED', res['status'] == 'RECOVERED')
            check('partial: 2 attempts made', len(res['attempts']) == 2)
    
    # --- Test 11: MAX_RESTART_ATTEMPTS constant ---
    check('config: MAX_RESTART_ATTEMPTS=2', MAX_RESTART_ATTEMPTS == 2)
    check('config: STALE_THRESHOLD_S=300', STALE_THRESHOLD_S == 300)
    
    # --- Test 12: run_guard returns proper dict keys ---
    with tempfile.TemporaryDirectory() as td:
        fake_loop = pathlib.Path(td) / 'autoloop.jsonl'
        fake_loop.write_text('{}\n', encoding='utf-8')
        os.utime(fake_loop, (time.time(), time.time()))
        
        with patch_globals(AUTOLOOP_PATH=fake_loop):
            res = run_guard()
            check('dict keys: has status', 'status' in res)
            check('dict keys: has attempts', 'attempts' in res)
            check('dict keys: has incident_written', 'incident_written' in res)
    
    print(f"  Result: {passed}/{total} passed")
    return passed


if __name__ == '__main__':
    import sys
    if '--selftest' in sys.argv:
        selftest()
        sys.exit(0)
    else:
        res = run_guard()
        print(json.dumps(res, indent=2))
