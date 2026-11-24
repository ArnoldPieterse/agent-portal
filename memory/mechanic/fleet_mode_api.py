"""Fleet-Mode API Endpoint (Goal 7).

Provides the /api/fleet/mode handler logic:
- Returns {mode, since, goal_pct, next_transition_forecast, pass_budget:{used,total}}
- Caches for 30s (avoids disk read on every poll)
- Graceful handling of missing fleet-mode.json
- Pass budget from pass-budget.json

Usage:
    python memory/mechanic/fleet_mode_api.py            # live endpoint test
    python memory/mechanic/fleet_mode_api.py --selftest # run selftests
"""
import json
import os
import sys
import time
import pathlib
from datetime import datetime, timezone

BASE = pathlib.Path(__file__).resolve().parent.parent.parent
FLEET_MODE_PATH = BASE / 'memory' / 'ops' / 'fleet-mode.json'
PASS_BUDGET_PATH = BASE / 'memory' / 'ops' / 'pass-budget.json'

# Cache
_cache = {'data': None, 'ts': 0.0}
CACHE_TTL_S = 30


def _read_fleet_mode():
    """Read fleet-mode.json from disk."""
    if not FLEET_MODE_PATH.exists():
        return None
    try:
        with open(FLEET_MODE_PATH, encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _read_pass_budget():
    """Read pass-budget.json from disk."""
    if not PASS_BUDGET_PATH.exists():
        return {'used': 0, 'total': 0}
    try:
        with open(PASS_BUDGET_PATH, encoding='utf-8') as f:
            data = json.load(f)
        return {
            'used': data.get('used', 0),
            'total': data.get('total', data.get('budget', 0))
        }
    except (json.JSONDecodeError, OSError):
        return {'used': 0, 'total': 0}


def _compute_next_transition(mode, goal_pct, last_activity):
    """Compute human-readable forecast for next mode transition."""
    if mode == 'WORK':
        return "When all goals are reached (100%)"
    elif mode == 'MAINTENANCE':
        return "After 6h idle -> IDLE"
    elif mode == 'IDLE':
        return "When new goals are set or agents become active -> WORK"
    return "Unknown"


def handle_fleet_mode(force_refresh=False):
    """Main handler for /api/fleet/mode.
    
    Returns a dict matching the API spec:
    {mode, since, goal_pct, next_transition_forecast, pass_budget:{used,total}}
    
    If fleet-mode.json is missing: {mode:"UNKNOWN", error:"file_missing"}
    """
    now = time.time()
    
    # Check cache
    if not force_refresh and _cache['data'] is not None:
        age = now - _cache['ts']
        if age < CACHE_TTL_S:
            return dict(_cache['data'])  # Return copy
    
    # Read from disk
    fm = _read_fleet_mode()
    
    if fm is None:
        result = {'mode': 'UNKNOWN', 'error': 'file_missing'}
    else:
        mode = fm.get('mode', 'UNKNOWN')
        since = fm.get('timestamp', '')
        goal_pct = fm.get('goal_pct', 0.0)
        last_activity = fm.get('last_activity', '')
        
        result = {
            'mode': mode,
            'since': since,
            'goal_pct': goal_pct,
            'next_transition_forecast': _compute_next_transition(mode, goal_pct, last_activity),
            'pass_budget': _read_pass_budget()
        }
    
    # Update cache
    _cache['data'] = result
    _cache['ts'] = now
    
    return result


def invalidate_cache():
    """Force cache invalidation (call on mode change)."""
    _cache['data'] = None
    _cache['ts'] = 0.0


# --- Selftest ---

def selftest():
    import tempfile
    import shutil
    from unittest import mock
    
    passed = 0
    failed = 0
    
    def check(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  PASS: {name}")
        else:
            failed += 1
            print(f"  FAIL: {name}")
    
    # Helper to patch globals
    import contextlib
    @contextlib.contextmanager
    def patch_globals(**kwargs):
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
    
    # --- Test 1: healthy fleet-mode.json ---
    with tempfile.TemporaryDirectory() as td:
        fake_fm = pathlib.Path(td) / 'fleet-mode.json'
        fake_pb = pathlib.Path(td) / 'pass-budget.json'
        fake_fm.write_text(json.dumps({
            'mode': 'WORK',
            'timestamp': '2026-11-24T12:00:00+00:00',
            'goal_pct': 75.0,
            'last_activity': '2026-11-24T11:55:00+00:00'
        }), encoding='utf-8')
        fake_pb.write_text(json.dumps({'used': 142, 'total': 200}), encoding='utf-8')
        
        invalidate_cache()
        with patch_globals(FLEET_MODE_PATH=fake_fm, PASS_BUDGET_PATH=fake_pb):
            r = handle_fleet_mode(force_refresh=True)
            check('healthy: mode=WORK', r['mode'] == 'WORK')
            check('healthy: goal_pct=75.0', r['goal_pct'] == 75.0)
            check('healthy: since present', '2026-11-24' in r['since'])
            check('healthy: forecast mentions goals', 'goals' in r['next_transition_forecast'].lower())
            check('healthy: pass_budget used=142', r['pass_budget']['used'] == 142)
            check('healthy: pass_budget total=200', r['pass_budget']['total'] == 200)
    
    # --- Test 2: missing fleet-mode.json ---
    with tempfile.TemporaryDirectory() as td:
        fake_fm = pathlib.Path(td) / 'nonexistent.json'
        fake_pb = pathlib.Path(td) / 'pb.json'
        
        invalidate_cache()
        with patch_globals(FLEET_MODE_PATH=fake_fm, PASS_BUDGET_PATH=fake_pb):
            r = handle_fleet_mode(force_refresh=True)
            check('missing: mode=UNKNOWN', r['mode'] == 'UNKNOWN')
            check('missing: error=file_missing', r.get('error') == 'file_missing')
    
    # --- Test 3: cache works (same data returned without disk read) ---
    with tempfile.TemporaryDirectory() as td:
        fake_fm = pathlib.Path(td) / 'fleet-mode.json'
        fake_pb = pathlib.Path(td) / 'pb.json'
        fake_fm.write_text(json.dumps({'mode': 'IDLE', 'timestamp': '2026-11-24T10:00:00+00:00', 'goal_pct': 100.0}), encoding='utf-8')
        fake_pb.write_text(json.dumps({'used': 50, 'total': 200}), encoding='utf-8')
        
        invalidate_cache()
        with patch_globals(FLEET_MODE_PATH=fake_fm, PASS_BUDGET_PATH=fake_pb):
            r1 = handle_fleet_mode(force_refresh=True)
            # Now corrupt the file - cache should still return old data
            fake_fm.write_text('CORRUPTED', encoding='utf-8')
            r2 = handle_fleet_mode(force_refresh=False)
            check('cache: same mode from cache', r2['mode'] == 'IDLE')
            check('cache: not affected by corruption', r2['goal_pct'] == 100.0)
            
            # Force refresh should see corruption -> UNKNOWN
            r3 = handle_fleet_mode(force_refresh=True)
            check('cache invalidated: sees corruption', r3['mode'] == 'UNKNOWN')
    
    # --- Test 4: cache TTL expiration ---
    with tempfile.TemporaryDirectory() as td:
        fake_fm = pathlib.Path(td) / 'fleet-mode.json'
        fake_pb = pathlib.Path(td) / 'pb.json'
        fake_fm.write_text(json.dumps({'mode': 'WORK', 'timestamp': 't1', 'goal_pct': 50.0}), encoding='utf-8')
        fake_pb.write_text(json.dumps({'used': 10, 'total': 100}), encoding='utf-8')
        
        invalidate_cache()
        with patch_globals(FLEET_MODE_PATH=fake_fm, PASS_BUDGET_PATH=fake_pb):
            r1 = handle_fleet_mode(force_refresh=True)
            # Simulate cache expiry by backdating
            _cache['ts'] = time.time() - 31
            # Change file
            fake_fm.write_text(json.dumps({'mode': 'IDLE', 'timestamp': 't2', 'goal_pct': 100.0}), encoding='utf-8')
            r2 = handle_fleet_mode(force_refresh=False)
            check('ttl expired: reads new data', r2['mode'] == 'IDLE')
    
    # --- Test 5: MAINTENANCE forecast ---
    with tempfile.TemporaryDirectory() as td:
        fake_fm = pathlib.Path(td) / 'fleet-mode.json'
        fake_pb = pathlib.Path(td) / 'pb.json'
        fake_fm.write_text(json.dumps({'mode': 'MAINTENANCE', 'timestamp': '2026-11-24T12:00:00+00:00', 'goal_pct': 100.0, 'last_activity': '2026-11-24T11:00:00+00:00'}), encoding='utf-8')
        fake_pb.write_text(json.dumps({'used': 0, 'total': 0}), encoding='utf-8')
        
        invalidate_cache()
        with patch_globals(FLEET_MODE_PATH=fake_fm, PASS_BUDGET_PATH=fake_pb):
            r = handle_fleet_mode(force_refresh=True)
            check('MAINTENANCE: mode correct', r['mode'] == 'MAINTENANCE')
            check('MAINTENANCE: forecast mentions 6h', '6h' in r['next_transition_forecast'])
    
    # --- Test 6: IDLE forecast ---
    with tempfile.TemporaryDirectory() as td:
        fake_fm = pathlib.Path(td) / 'fleet-mode.json'
        fake_pb = pathlib.Path(td) / 'pb.json'
        fake_fm.write_text(json.dumps({'mode': 'IDLE', 'timestamp': '2026-11-24T12:00:00+00:00', 'goal_pct': 100.0, 'last_activity': '2026-11-23T12:00:00+00:00'}), encoding='utf-8')
        fake_pb.write_text(json.dumps({'used': 5, 'total': 200}), encoding='utf-8')
        
        invalidate_cache()
        with patch_globals(FLEET_MODE_PATH=fake_fm, PASS_BUDGET_PATH=fake_pb):
            r = handle_fleet_mode(force_refresh=True)
            check('IDLE: mode correct', r['mode'] == 'IDLE')
            check('IDLE: forecast mentions WORK', 'WORK' in r['next_transition_forecast'])
    
    # --- Test 7: pass_budget graceful (missing file) ---
    with tempfile.TemporaryDirectory() as td:
        fake_fm = pathlib.Path(td) / 'fleet-mode.json'
        fake_pb = pathlib.Path(td) / 'nonexistent-pb.json'
        fake_fm.write_text(json.dumps({'mode': 'WORK', 'timestamp': 't', 'goal_pct': 10.0}), encoding='utf-8')
        
        invalidate_cache()
        with patch_globals(FLEET_MODE_PATH=fake_fm, PASS_BUDGET_PATH=fake_pb):
            r = handle_fleet_mode(force_refresh=True)
            check('no budget file: used=0', r['pass_budget']['used'] == 0)
            check('no budget file: total=0', r['pass_budget']['total'] == 0)
    
    # --- Test 8: invalidate_cache works ---
    with tempfile.TemporaryDirectory() as td:
        fake_fm = pathlib.Path(td) / 'fleet-mode.json'
        fake_pb = pathlib.Path(td) / 'pb.json'
        fake_fm.write_text(json.dumps({'mode': 'WORK', 'timestamp': 't1', 'goal_pct': 10.0}), encoding='utf-8')
        fake_pb.write_text(json.dumps({'used': 1, 'total': 10}), encoding='utf-8')
        
        invalidate_cache()
        with patch_globals(FLEET_MODE_PATH=fake_fm, PASS_BUDGET_PATH=fake_pb):
            handle_fleet_mode(force_refresh=True)
            # Change file + invalidate
            fake_fm.write_text(json.dumps({'mode': 'IDLE', 'timestamp': 't2', 'goal_pct': 100.0}), encoding='utf-8')
            invalidate_cache()
            r = handle_fleet_mode(force_refresh=False)
            check('invalidate: reads new state', r['mode'] == 'IDLE')
    
    # --- Test 9: response schema completeness ---
    with tempfile.TemporaryDirectory() as td:
        fake_fm = pathlib.Path(td) / 'fleet-mode.json'
        fake_pb = pathlib.Path(td) / 'pb.json'
        fake_fm.write_text(json.dumps({'mode': 'WORK', 'timestamp': '2026-11-24T12:00:00+00:00', 'goal_pct': 50.0, 'last_activity': '2026-11-24T11:00:00+00:00'}), encoding='utf-8')
        fake_pb.write_text(json.dumps({'used': 100, 'total': 200}), encoding='utf-8')
        
        invalidate_cache()
        with patch_globals(FLEET_MODE_PATH=fake_fm, PASS_BUDGET_PATH=fake_pb):
            r = handle_fleet_mode(force_refresh=True)
            required_keys = {'mode', 'since', 'goal_pct', 'next_transition_forecast', 'pass_budget'}
            check('schema: all required keys present', required_keys.issubset(r.keys()))
            pb_keys = {'used', 'total'}
            check('schema: pass_budget has used+total', pb_keys.issubset(r['pass_budget'].keys()))
    
    # --- Test 10: performance (response < 100ms) ---
    with tempfile.TemporaryDirectory() as td:
        fake_fm = pathlib.Path(td) / 'fleet-mode.json'
        fake_pb = pathlib.Path(td) / 'pb.json'
        fake_fm.write_text(json.dumps({'mode': 'WORK', 'timestamp': 't', 'goal_pct': 50.0}), encoding='utf-8')
        fake_pb.write_text(json.dumps({'used': 50, 'total': 200}), encoding='utf-8')
        
        invalidate_cache()
        with patch_globals(FLEET_MODE_PATH=fake_fm, PASS_BUDGET_PATH=fake_pb):
            t0 = time.time()
            handle_fleet_mode(force_refresh=True)
            disk_ms = (time.time() - t0) * 1000
            
            # Cached should be faster
            t1 = time.time()
            for _ in range(100):
                handle_fleet_mode(force_refresh=False)
            cached_ms_avg = ((time.time() - t1) * 1000) / 100
            
            check('perf: disk read < 100ms', disk_ms < 100)
            check('perf: cached < 1ms avg', cached_ms_avg < 1.0)
    
    # --- Test 11: corrupted JSON handled gracefully ---
    with tempfile.TemporaryDirectory() as td:
        fake_fm = pathlib.Path(td) / 'fleet-mode.json'
        fake_pb = pathlib.Path(td) / 'pb.json'
        fake_fm.write_text('{invalid json here', encoding='utf-8')
        
        invalidate_cache()
        with patch_globals(FLEET_MODE_PATH=fake_fm, PASS_BUDGET_PATH=fake_pb):
            r = handle_fleet_mode(force_refresh=True)
            check('corrupt: mode=UNKNOWN', r['mode'] == 'UNKNOWN')
            check('corrupt: error present', 'error' in r)
    
    # --- Test 12: empty fleet-mode.json (valid JSON but no fields) ---
    with tempfile.TemporaryDirectory() as td:
        fake_fm = pathlib.Path(td) / 'fleet-mode.json'
        fake_pb = pathlib.Path(td) / 'pb.json'
        fake_fm.write_text('{}', encoding='utf-8')
        
        invalidate_cache()
        with patch_globals(FLEET_MODE_PATH=fake_fm, PASS_BUDGET_PATH=fake_pb):
            r = handle_fleet_mode(force_refresh=True)
            check('empty json: mode=UNKNOWN (default)', r['mode'] == 'UNKNOWN')
    
    # Summary
    total = passed + failed
    print(f"\n  Result: {passed}/{total} passed")
    if failed > 0:
        raise SystemExit(1)


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        selftest()
    else:
        r = handle_fleet_mode(force_refresh=True)
        print(json.dumps(r, indent=2))
