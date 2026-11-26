"""
idle_floor_enforce.py - Idle-Productivity Floor Enforcer (Forge goal #4, cycle 19)

Scheduled check: a role's productive-pass rate < floor for K consecutive passes
triggers an escalation AND verifies the mode flip actually fired (pairs with
orchestrator idle_rebalance).

Contract with orchestrator:
  - This enforcer WRITES an escalation to memory/ops/incidents.jsonl
    (kind='idle_floor_breach') when a role breaches.
  - orchestrator idle_rebalance, on acting, stamps fleet-mode.json with
    {'idle_floor_flip': {'agent': <name>, 'ts': <iso>}}.
  - This enforcer CONFIRMS the flip by reading that stamp and checking it is
    newer than the breach. Until confirmed the escalation stays 'pending'.

Idempotency: an already-escalated role (pending or confirmed) is NOT re-written;
a re-run only re-checks flip status. A fresh breach after the previous one was
confirmed (or after cooldown) escalates again.

Usage:
  python memory/forge/idle_floor_enforce.py --selftest
  python memory/forge/idle_floor_enforce.py --agent <name> [--passes N] [--floor F] [--k K]
  python memory/forge/idle_floor_enforce.py            # scan all agents, last --passes

Exit codes: 0 = no action / confirmed, 2 = breach escalated (flip pending), 3 = flip confirmed.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUTOLOOP = os.path.join(HERE, 'memory', 'ops', 'autoloop.jsonl')
FLEET_MODE = os.path.join(HERE, 'memory', 'ops', 'fleet-mode.json')
INCIDENTS = os.path.join(HERE, 'memory', 'ops', 'incidents.jsonl')
STATE = os.path.join(HERE, 'memory', 'ops', 'idle-floor-state.json')

DEFAULT_FLOOR = 0.5   # min productive-pass rate
DEFAULT_K = 3         # consecutive passes below floor to breach
COOLDOWN_S = 900      # 15 min before the same role may re-escalate after confirm


def _iso(dt):
    return dt.astimezone(timezone.utc).isoformat()


def _parse(ts):
    try:
        return datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None


def load_passes(agent=None, window_h=72):
    """Return list of (dt, productive) per record, optionally filtered by agent."""
    if not os.path.exists(AUTOLOOP):
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_h)
    out = []
    with open(AUTOLOOP, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            dt = _parse(rec.get('timestamp'))
            if not dt or dt < cutoff:
                continue
            ag = str(rec.get('agent', '')).lower()
            if agent and ag != agent.lower():
                continue
            prod = rec.get('productive')
            if isinstance(prod, bool):
                out.append((dt, prod))
    out.sort(key=lambda x: x[0])
    return out


def productive_rate(passes):
    """rate over the most recent K passes of `passes` (already tail-sliced)."""
    if not passes:
        return None
    prods = [p for _, p in passes]
    return sum(1 for p in prods if p) / len(prods)


def evaluate(agent, floor=DEFAULT_FLOOR, k=DEFAULT_K, window_h=72):
    """Return dict describing breach state for one agent."""
    recs = load_passes(agent, window_h)
    if not recs:
        return {'agent': agent, 'ok': True, 'reason': 'no-pass-data', 'passes': 0}
    tail = recs[-k:] if len(recs) >= k else recs
    rate = productive_rate(tail)
    breach = (rate is not None and rate < floor) and len(tail) == k
    return {
        'agent': agent,
        'ok': not breach,
        'breach': breach,
        'passes_evaluated': len(tail),
        'productive_rate': round(rate, 3) if rate is not None else None,
        'floor': floor,
        'k': k,
    }


def _read_state():
    if os.path.exists(STATE):
        try:
            with open(STATE, encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _write_state(state):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)


def _append_incident(kind, agent, detail):
    os.makedirs(os.path.dirname(INCIDENTS), exist_ok=True)
    rec = {'ts': _iso(datetime.now(timezone.utc)), 'kind': kind, 'agent': agent}
    rec.update(detail)
    with open(INCIDENTS, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec) + '\n')


def _flip_stamp():
    """Return (agent, dt) of the idle_floor_flip stamp in fleet-mode.json, or None."""
    if not os.path.exists(FLEET_MODE):
        return None
    try:
        with open(FLEET_MODE, encoding='utf-8') as f:
            fm = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    stamp = fm.get('idle_floor_flip')
    if not isinstance(stamp, dict) or 'agent' not in stamp or 'ts' not in stamp:
        return None
    dt = _parse(stamp['ts'])
    if not dt:
        return None
    return str(stamp['agent']).lower(), dt


def enforce(agent, floor=DEFAULT_FLOOR, k=DEFAULT_K, window_h=72):
    """Enforce floor for one agent. Returns (exit_code, result_dict)."""
    ev = evaluate(agent, floor, k, window_h)
    state = _read_state()
    now = datetime.now(timezone.utc)

    if not ev['breach']:
        # No breach -> no action; clear any stale pending entry for this agent.
        if agent in state and state[agent].get('status') == 'pending':
            del state[agent]
            _write_state(state)
        return 0, {'action': 'none', **ev}

    # Breach: check idempotency against existing state.
    prev = state.get(agent)
    if prev and prev.get('status') in ('pending', 'confirmed'):
        age_s = (now - _parse(prev['escalated_ts'])).total_seconds() if _parse(prev['escalated_ts']) else float('inf')
        # Still within an active escalation window -> do NOT re-escalate.
        if prev.get('status') == 'pending' or age_s < COOLDOWN_S:
            # Re-check flip confirmation only.
            confirmed = _check_flip(agent, prev['escalated_ts'])
            if confirmed:
                state[agent]['status'] = 'confirmed'
                state[agent]['confirmed_ts'] = _iso(now)
                _write_state(state)
                return 3, {'action': 'flip-confirmed', **ev}
            return 2, {'action': 'already-pending', **ev}

    # Fresh escalation.
    escalated_ts = _iso(now)
    _append_incident('idle_floor_breach', agent,
                     {'rate': ev['productive_rate'], 'floor': floor, 'k': k,
                      'passes_evaluated': ev['passes_evaluated']})
    state[agent] = {'status': 'pending', 'escalated_ts': escalated_ts}
    _write_state(state)

    # Immediately check whether the flip already fired (may race ahead).
    if _check_flip(agent, escalated_ts):
        state[agent]['status'] = 'confirmed'
        state[agent]['confirmed_ts'] = _iso(now)
        _write_state(state)
        return 3, {'action': 'escalated+flip-confirmed', **ev}
    return 2, {'action': 'escalated-flip-pending', **ev}


def _check_flip(agent, escalated_ts):
    """True if fleet-mode.json has an idle_floor_flip stamp for `agent` newer than escalated_ts."""
    flip = _flip_stamp()
    if not flip:
        return False
    f_agent, f_dt = flip
    esc_dt = _parse(escalated_ts)
    if f_agent != agent.lower() or not esc_dt:
        return False
    return f_dt >= esc_dt


def scan_all(floor=DEFAULT_FLOOR, k=DEFAULT_K, window_h=72):
    """Evaluate every distinct agent seen in autoloop; enforce each breacher."""
    agents = []
    if os.path.exists(AUTOLOOP):
        with open(AUTOLOOP, encoding='utf-8') as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                a = str(rec.get('agent', '')).strip()
                if a and a not in agents:
                    agents.append(a)
    results = []
    for a in sorted(agents):
        code, res = enforce(a, floor, k, window_h)
        results.append(res)
    return results


def _selftest():
    """Synthetic test of the three acceptance criteria."""
    import shutil
    tmp = os.path.join(HERE, 'memory', 'forge', '_idle_floor_selftest')
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp)
    # Point module paths at a sandbox copy so we never touch live state.
    global AUTOLOOP, FLEET_MODE, INCIDENTS, STATE
    real = (AUTOLOOP, FLEET_MODE, INCIDENTS, STATE)
    AUTOLOOP = os.path.join(tmp, 'autoloop.jsonl')
    FLEET_MODE = os.path.join(tmp, 'fleet-mode.json')
    INCIDENTS = os.path.join(tmp, 'incidents.jsonl')
    STATE = os.path.join(tmp, 'state.json')

    now = datetime.now(timezone.utc)
    def ts(i):
        return _iso(now - timedelta(minutes=i))

    # Agent 'breacher': 3 consecutive non-productive passes (rate 0.0 < 0.5).
    # Agent 'healthy': 3 consecutive productive passes (rate 1.0 >= 0.5).
    lines = []
    for i in range(3, 0, -1):
        lines.append(json.dumps({'timestamp': ts(i * 2), 'agent': 'breacher', 'productive': False}))
        lines.append(json.dumps({'timestamp': ts(i * 2 + 1), 'agent': 'healthy', 'productive': True}))
    with open(AUTOLOOP, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    # fleet-mode.json starts with NO flip stamp.
    with open(FLEET_MODE, 'w', encoding='utf-8') as f:
        json.dump({'mode': 'WORK', 'timestamp': _iso(now)}, f)

    results = []

    # --- Criterion 1a: synthetic breach escalates (flip pending) ---
    code, res = enforce('breacher', floor=0.5, k=3)
    crit1a = (code == 2 and res['action'] in ('escalated-flip-pending',))
    results.append(('breach_escalates_flip_pending', crit1a, f"code={code} action={res.get('action')} rate={res.get('productive_rate')}"))

    # --- Criterion 1b: confirm the flip fires (simulate orchestrator stamp) ---
    # Orchestrator acts AFTER seeing the escalation, so its flip stamp is at/after
    # escalated_ts. Read the real escalated_ts from state and stamp at that instant.
    with open(STATE, encoding='utf-8') as f:
        esc_ts = json.load(f)['breacher']['escalated_ts']
    with open(FLEET_MODE, encoding='utf-8') as f:
        fm = json.load(f)
    fm['idle_floor_flip'] = {'agent': 'breacher', 'ts': esc_ts}
    with open(FLEET_MODE, 'w', encoding='utf-8') as f:
        json.dump(fm, f)
    code2, res2 = enforce('breacher', floor=0.5, k=3)
    crit1b = (code2 == 3 and res2['action'] in ('flip-confirmed', 'escalated+flip-confirmed'))
    results.append(('flip_confirmed_after_stamp', crit1b, f"code={code2} action={res2.get('action')}"))

    # --- Criterion 2: no breach -> no action (healthy agent) ---
    inc_before = open(INCIDENTS, encoding='utf-8').read().strip().splitlines()
    code3, res3 = enforce('healthy', floor=0.5, k=3)
    inc_after = open(INCIDENTS, encoding='utf-8').read().strip().splitlines()
    crit2 = (code3 == 0 and res3['action'] == 'none' and len(inc_after) == len(inc_before))
    results.append(('no_breach_no_action', crit2, f"code={code3} action={res3.get('action')} incidents {len(inc_before)}->{len(inc_after)}"))

    # --- Criterion 3: idempotent (re-run on already-confirmed breacher adds no new incident) ---
    inc_before = open(INCIDENTS, encoding='utf-8').read().strip().splitlines()
    code4, res4 = enforce('breacher', floor=0.5, k=3)
    inc_after = open(INCIDENTS, encoding='utf-8').read().strip().splitlines()
    crit3 = (len(inc_after) == len(inc_before))  # no double escalation
    results.append(('idempotent_no_double_escalation', crit3, f"code={code4} action={res4.get('action')} incidents {len(inc_before)}->{len(inc_after)}"))

    # --- Bonus: scan_all over the sandbox classifies both agents correctly ---
    scan = scan_all(floor=0.5, k=3)
    by_agent = {s['agent']: s for s in scan}
    crit4 = (by_agent.get('breacher', {}).get('breach') is True and
             by_agent.get('healthy', {}).get('ok') is True)
    results.append(('scan_all_classifies_both', crit4, f"breacher.breach={by_agent.get('breacher',{}).get('breach')} healthy.ok={by_agent.get('healthy',{}).get('ok')}"))

    # cleanup + restore
    shutil.rmtree(tmp, ignore_errors=True)
    AUTOLOOP, FLEET_MODE, INCIDENTS, STATE = real

    print('=== idle_floor_enforce.py --selftest ===')
    allpass = True
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
        allpass = allpass and ok
    print(f"RESULT: {'ALL PASS' if allpass else 'FAILURES PRESENT'}")
    return 0 if allpass else 1


def main():
    ap = argparse.ArgumentParser(description='Idle-Productivity Floor Enforcer')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--agent', help='single agent to enforce (else scan all)')
    ap.add_argument('--passes', type=int, default=DEFAULT_K, dest='k')
    ap.add_argument('--floor', type=float, default=DEFAULT_FLOOR)
    ap.add_argument('--window-h', type=int, default=72, dest='window_h')
    args = ap.parse_args()

    if args.selftest:
        sys.exit(_selftest())

    if args.agent:
        code, res = enforce(args.agent, floor=args.floor, k=args.k, window_h=args.window_h)
        print(json.dumps(res, indent=2))
        sys.exit(code)
    else:
        results = scan_all(floor=args.floor, k=args.k, window_h=args.window_h)
        for r in results:
            flag = 'BREACH' if r.get('breach') else 'ok'
            print(f"  {flag:6} {r['agent']:12} rate={r.get('productive_rate')} action={r.get('action')}")
        any_breach = any(r.get('breach') for r in results)
        sys.exit(2 if any_breach else 0)


if __name__ == '__main__':
    main()
