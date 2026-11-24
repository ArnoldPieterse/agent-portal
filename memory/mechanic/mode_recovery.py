#!/usr/bin/env python3
"""Mode State Recovery.

On fleet restart (stale fleet-mode.json mtime >30 min + system uptime <5 min),
reconstruct current mode from goal completion % + last known activity timestamp.
Write reconstructed state with "recovered": true flag.

Usage:
    python memory/mechanic/mode_recovery.py            # live check
    python memory/mechanic/mode_recovery.py --selftest # run selftests
"""
import json
import os
import pathlib
import time
from datetime import datetime, timezone, timedelta

BASE = pathlib.Path(__file__).resolve().parent.parent.parent
FLEET_MODE_PATH = BASE / 'memory' / 'ops' / 'fleet-mode.json'
GOALS_DIR = BASE / 'memory' / 'goals'
STALE_THRESHOLD_S = 1800    # 30 minutes
UPTIME_THRESHOLD_S = 300    # 5 minutes (system uptime for restart detection)


def get_system_uptime() -> float:
    """Get system uptime in seconds. Returns float."""
    import platform
    if platform.system() == 'Windows':
        try:
            import subprocess
            r = subprocess.run(['wmic', 'os', 'get', 'LastBootUpTime'],
                             capture_output=True, text=True, timeout=5)
            lines = r.stdout.strip().split('\n')
            if len(lines) >= 2:
                boot_str = lines[1].strip()
                # Format: YYYYMMDDHHMMSS.fff+zzz
                dt = datetime.strptime(boot_str[:14], '%Y%m%d%H%M%S')
                return (datetime.now() - dt).total_seconds()
        except Exception:
            pass
    # Fallback: use /proc/uptime on Linux, or default to a large value
    try:
        with open('/proc/uptime', 'r') as f:
            return float(f.read().split()[0])
    except (FileNotFoundError, ValueError):
        return 99999.0  # Assume system has been up long enough


def get_goal_completion_pct() -> float:
    """Scan goals directory and compute overall completion percentage."""
    total = 0
    reached = 0
    
    if not GOALS_DIR.exists():
        return 0.0
    
    for f in GOALS_DIR.glob('*.md'):
        if f.name.startswith('_') or f.name == 'INDEX.md':
            continue
        try:
            content = f.read_text(encoding='utf-8')
            # Count goal lines (numbered items with **)
            import re
            goal_lines = re.findall(r'^\d+\.\s+\*\*', content, re.MULTILINE)
            total += len(goal_lines)
            # Count verified markers
            reached += len(re.findall(r'\(verified:', content))
        except (OSError, UnicodeDecodeError):
            continue
    
    if total == 0:
        return 0.0
    return round((reached / total) * 100, 2)


def get_last_activity_timestamp() -> str | None:
    """Get the last activity timestamp from fleet-mode.json or autoloop data."""
    if FLEET_MODE_PATH.exists():
        try:
            data = json.loads(FLEET_MODE_PATH.read_text(encoding='utf-8'))
            return data.get('last_activity') or data.get('timestamp')
        except (json.JSONDecodeError, OSError):
            pass
    # Fallback: check autoloop.jsonl last line
    autoloop = BASE / 'memory' / 'ops' / 'autoloop.jsonl'
    if autoloop.exists():
        try:
            with open(autoloop, 'r', encoding='utf-8') as f:
                lines = [l for l in f if l.strip()]
            if lines:
                entry = json.loads(lines[-1])
                return entry.get('timestamp') or entry.get('ts')
        except (json.JSONDecodeError, OSError):
            pass
    return None


def detect_restart(stale_threshold: float = STALE_THRESHOLD_S,
                   uptime_threshold: float = UPTIME_THRESHOLD_S) -> bool:
    """Detect if a fleet restart just happened.
    
    Conditions: fleet-mode.json mtime > stale_threshold AND system uptime < uptime_threshold.
    If fleet-mode.json doesn't exist, treat as restart (first boot).
    """
    # No file = first boot = needs recovery
    if not FLEET_MODE_PATH.exists():
        return True
    
    mtime = os.path.getmtime(FLEET_MODE_PATH)
    age = time.time() - mtime
    
    if age > stale_threshold:
        uptime = get_system_uptime()
        if uptime < uptime_threshold:
            return True
    
    return False


def reconstruct_mode(goal_pct: float, last_activity: str | None) -> dict:
    """Reconstruct fleet mode from goal state + activity.
    
    Rules:
        - WORK: any open goals (goal_pct < 100)
        - MAINTENANCE: all reached, <6h since last activity
        - IDLE: all reached, >6h since last activity
    """
    now = datetime.now(timezone.utc)
    
    if goal_pct < 100:
        mode = 'WORK'
    else:
        # All goals reached: check time since last activity
        if last_activity:
            try:
                last_dt = datetime.fromisoformat(last_activity)
                elapsed_h = (now - last_dt).total_seconds() / 3600
                mode = 'MAINTENANCE' if elapsed_h < 6 else 'IDLE'
            except (ValueError, TypeError):
                mode = 'WORK'  # Can't determine: default to WORK
        else:
            mode = 'WORK'  # No activity data: default to WORK
    
    return {
        'mode': mode,
        'timestamp': now.isoformat(),
        'goal_pct': goal_pct,
        'last_activity': last_activity or now.isoformat(),
        'recovered': True
    }


def write_recovered_state(state: dict) -> pathlib.Path:
    """Write the recovered state to fleet-mode.json."""
    FLEET_MODE_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Atomic write: temp + rename
    tmp = FLEET_MODE_PATH.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
    os.replace(str(tmp), str(FLEET_MODE_PATH))
    return FLEET_MODE_PATH


def run_recovery() -> dict:
    """Full recovery cycle. Returns result dict."""
    if not detect_restart():
        return {'action': 'no_recovery_needed', 'reason': 'fleet-mode.json is fresh or system not recently booted'}
    
    goal_pct = get_goal_completion_pct()
    last_activity = get_last_activity_timestamp()
    state = reconstruct_mode(goal_pct, last_activity)
    path = write_recovered_state(state)
    
    return {
        'action': 'recovered',
        'mode': state['mode'],
        'goal_pct': goal_pct,
        'written_to': str(path),
        'state': state
    }


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
    
    # --- Test 1: reconstruct_mode WORK (open goals) ---
    state = reconstruct_mode(50.0, None)
    check('reconstruct: 50% -> WORK', state['mode'] == 'WORK')
    check('reconstruct: has recovered flag', state['recovered'] is True)
    check('reconstruct: goal_pct preserved', state['goal_pct'] == 50.0)
    
    # --- Test 2: reconstruct_mode MAINTENANCE (all done, recent) ---
    recent = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    state = reconstruct_mode(100.0, recent)
    check('reconstruct: 100% + 1h -> MAINTENANCE', state['mode'] == 'MAINTENANCE')
    
    # --- Test 3: reconstruct_mode IDLE (all done, old) ---
    old = (datetime.now(timezone.utc) - timedelta(hours=7)).isoformat()
    state = reconstruct_mode(100.0, old)
    check('reconstruct: 100% + 7h -> IDLE', state['mode'] == 'IDLE')
    
    # --- Test 4: boundary - exactly 6h -> MAINTENANCE (not >6h) ---
    six_h = (datetime.now(timezone.utc) - timedelta(hours=5, minutes=59)).isoformat()
    state = reconstruct_mode(100.0, six_h)
    check('reconstruct: ~6h -> MAINTENANCE', state['mode'] == 'MAINTENANCE')
    
    # --- Test 5: boundary - just over 6h -> IDLE ---
    just_over = (datetime.now(timezone.utc) - timedelta(hours=6, minutes=1)).isoformat()
    state = reconstruct_mode(100.0, just_over)
    check('reconstruct: 6h1m -> IDLE', state['mode'] == 'IDLE')
    
    # --- Test 6: no last_activity with 100% -> WORK (can't determine) ---
    state = reconstruct_mode(100.0, None)
    check('reconstruct: 100% + no activity -> WORK', state['mode'] == 'WORK')
    
    # --- Test 7: invalid timestamp -> WORK fallback ---
    state = reconstruct_mode(100.0, 'not-a-timestamp')
    check('reconstruct: bad timestamp -> WORK', state['mode'] == 'WORK')
    
    # --- Test 8: detect_restart - no file = restart ---
    with tempfile.TemporaryDirectory() as td:
        fake_fm = pathlib.Path(td) / 'fleet-mode.json'
        with patch_globals(FLEET_MODE_PATH=fake_fm):
            check('detect: missing file = restart', detect_restart() is True)
    
    # --- Test 9: detect_restart - fresh file, old system = no restart ---
    with tempfile.TemporaryDirectory() as td:
        fake_fm = pathlib.Path(td) / 'fleet-mode.json'
        fake_fm.write_text('{}\n', encoding='utf-8')
        os.utime(fake_fm, (time.time(), time.time()))  # fresh
        
        with patch_globals(FLEET_MODE_PATH=fake_fm), \
             patch_globals(get_system_uptime=lambda: 99999.0):
            check('detect: fresh file + old system = no restart', detect_restart() is False)
    
    # --- Test 10: detect_restart - stale file + recent boot = restart ---
    with tempfile.TemporaryDirectory() as td:
        fake_fm = pathlib.Path(td) / 'fleet-mode.json'
        fake_fm.write_text('{}\n', encoding='utf-8')
        os.utime(fake_fm, (time.time() - 3600, time.time() - 3600))  # 1h old
        
        with patch_globals(FLEET_MODE_PATH=fake_fm), \
             patch_globals(get_system_uptime=lambda: 120.0):
            check('detect: stale file + recent boot = restart', detect_restart() is True)
    
    # --- Test 11: detect_restart - stale file + old system = no restart ---
    with tempfile.TemporaryDirectory() as td:
        fake_fm = pathlib.Path(td) / 'fleet-mode.json'
        fake_fm.write_text('{}\n', encoding='utf-8')
        os.utime(fake_fm, (time.time() - 3600, time.time() - 3600))  # 1h old
        
        with patch_globals(FLEET_MODE_PATH=fake_fm), \
             patch_globals(get_system_uptime=lambda: 99999.0):
            check('detect: stale file + old system = no restart', detect_restart() is False)
    
    # --- Test 12: write_recovered_state creates valid JSON ---
    with tempfile.TemporaryDirectory() as td:
        fake_fm = pathlib.Path(td) / 'fleet-mode.json'
        state = {'mode': 'WORK', 'timestamp': '2026-11-24T00:00:00+00:00',
                 'goal_pct': 50.0, 'last_activity': None, 'recovered': True}
        
        with patch_globals(FLEET_MODE_PATH=fake_fm):
            p = write_recovered_state(state)
            check('write: file exists', p.exists())
            data = json.loads(p.read_text(encoding='utf-8'))
            check('write: mode correct', data['mode'] == 'WORK')
            check('write: recovered flag', data['recovered'] is True)
    
    # --- Test 13: write_recovered_state atomic (no temp left) ---
    with tempfile.TemporaryDirectory() as td:
        fake_fm = pathlib.Path(td) / 'fleet-mode.json'
        state = {'mode': 'IDLE', 'timestamp': 'x', 'goal_pct': 100.0, 'recovered': True}
        
        with patch_globals(FLEET_MODE_PATH=fake_fm):
            write_recovered_state(state)
            tmp_exists = fake_fm.with_suffix('.json.tmp').exists()
            check('write atomic: no temp file left', not tmp_exists)
    
    # --- Test 14: run_recovery - no restart needed ---
    with tempfile.TemporaryDirectory() as td:
        fake_fm = pathlib.Path(td) / 'fleet-mode.json'
        fake_fm.write_text('{}\n', encoding='utf-8')
        os.utime(fake_fm, (time.time(), time.time()))
        
        with patch_globals(FLEET_MODE_PATH=fake_fm), \
             patch_globals(get_system_uptime=lambda: 99999.0):
            res = run_recovery()
            check('run: no recovery needed', res['action'] == 'no_recovery_needed')
    
    # --- Test 15: run_recovery - full recovery cycle ---
    with tempfile.TemporaryDirectory() as td:
        fake_fm = pathlib.Path(td) / 'fleet-mode.json'
        # File doesn't exist yet = restart detected
        
        with patch_globals(FLEET_MODE_PATH=fake_fm, GOALS_DIR=pathlib.Path(td)):
            res = run_recovery()
            check('run: action=recovered', res['action'] == 'recovered')
            check('run: has mode', 'mode' in res)
            check('run: file written', fake_fm.exists())
            data = json.loads(fake_fm.read_text(encoding='utf-8'))
            check('run: recovered flag in file', data['recovered'] is True)
    
    # --- Test 16: get_goal_completion_pct with no goals dir ---
    with tempfile.TemporaryDirectory() as td:
        with patch_globals(GOALS_DIR=pathlib.Path(td) / 'nonexistent'):
            pct = get_goal_completion_pct()
            check('goals: missing dir -> 0.0', pct == 0.0)
    
    # --- Test 17: get_goal_completion_pct with goals file ---
    with tempfile.TemporaryDirectory() as td:
        fake_goals = pathlib.Path(td) / 'test.md'
        fake_goals.write_text(
            "# Test Goals\n\n"
            "1. **Goal One** - text (verified: 2026-11-24)\n"
            "2. **Goal Two** - text\n"
            "3. **Goal Three** - text (verified: 2026-11-24)\n",
            encoding='utf-8'
        )
        with patch_globals(GOALS_DIR=pathlib.Path(td)):
            pct = get_goal_completion_pct()
            check('goals: 2/3 reached = 66.67%', abs(pct - 66.67) < 0.1)
    
    # --- Test 18: state schema completeness ---
    state = reconstruct_mode(75.0, '2026-11-24T10:00:00+00:00')
    check('schema: has mode', 'mode' in state)
    check('schema: has timestamp', 'timestamp' in state)
    check('schema: has goal_pct', 'goal_pct' in state)
    check('schema: has last_activity', 'last_activity' in state)
    check('schema: has recovered', 'recovered' in state)
    
    # --- Test 19: timestamp is valid ISO-8601 ---
    from datetime import datetime as dt2
    ts = state['timestamp']
    parsed = dt2.fromisoformat(ts)
    check('schema: timestamp parseable', parsed is not None)
    
    # --- Test 20: config constants ---
    check('config: STALE_THRESHOLD_S=1800', STALE_THRESHOLD_S == 1800)
    check('config: UPTIME_THRESHOLD_S=300', UPTIME_THRESHOLD_S == 300)
    
    print(f"  Result: {passed}/{total} passed")
    return passed


if __name__ == '__main__':
    import sys
    if '--selftest' in sys.argv:
        selftest()
        sys.exit(0)
    else:
        res = run_recovery()
        print(json.dumps(res, indent=2))
