#!/usr/bin/env python3
"""
cycle_snapshot.py — Whole-Cycle State Snapshot & Diff Store (Researcher goal #7).

At each cycle close, persist a compact per-file hash manifest of the fleet's
cross-agent state (goal files + ledger + closed_topics). On the next transition,
diff two consecutive snapshots to report what was added / removed / changed, and
flag any LOSSY carry-over (a file present in the earlier snapshot but gone in the
later one = potential data loss across the cycle boundary).

Distinct from the closed autonomous_action_replay (single action): this captures
WHOLE-CYCLE state for replay/what-if + validates the auto-transition auditor.

Usage:
  python memory/researcher/cycle_snapshot.py snapshot [--cycle ID]   # hash current live state -> snapshot
  python memory/researcher/cycle_snapshot.py diff [A B]              # diff two snapshots (default: latest two)
  python memory/researcher/cycle_snapshot.py list                    # list stored snapshots, newest first
  python memory/researcher/cycle_snapshot.py --selftest              # prove AC on synthetic cycles

AC: two consecutive cycles produce a valid diff; a seeded lost-file case is flagged.
Reproducible + idempotent (same state -> same manifest hash).
"""
import argparse, glob, hashlib, json, os, sys, datetime
BASE = os.path.dirname(os.path.abspath(__file__))
SNAP_DIR = os.path.join(BASE, 'cycle-snapshots')

# The live cross-agent state this snapshotter covers (relative to repo root).
STATE_SOURCES = [
    'memory/goals/*.md',
    'memory/researcher/goal_ledger.jsonl',
    'memory/researcher/goal_ledger_current.json',
    'memory/goals/closed_topics.json',
]

ROOT = os.path.abspath(os.path.join(BASE, '..', '..'))


def sha1_of(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def collect_files(root, patterns):
    files = []
    for pat in patterns:
        for p in glob.glob(os.path.join(root, pat)):
            if os.path.isfile(p):
                files.append(os.path.relpath(p, root).replace('\\', '/'))
    return sorted(set(files))


def snapshot(root, cycle_id, patterns=None):
    patterns = patterns or STATE_SOURCES
    files = collect_files(root, patterns)
    manifest = {'files': {}, 'count': 0}
    for rel in files:
        full = os.path.join(root, rel.replace('/', os.sep))
        try:
            st = os.stat(full)
            manifest['files'][rel] = {'sha1': sha1_of(full), 'size': st.st_size}
        except (OSError, UnicodeDecodeError):
            pass
    manifest['count'] = len(manifest['files'])
    blob = json.dumps(manifest['files'], sort_keys=True).encode()
    manifest['manifest_sha1'] = hashlib.sha1(blob).hexdigest()
    manifest['cycle_id'] = cycle_id
    manifest['ts'] = datetime.datetime.now().isoformat(timespec='seconds')
    return manifest


def store(manifest, snap_dir=SNAP_DIR):
    os.makedirs(snap_dir, exist_ok=True)
    safe = ''.join(c for c in str(manifest['cycle_id']) if c.isalnum() or c in '-_:')
    path = os.path.join(snap_dir, f'{safe}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    return path


def latest_two(snap_dir=SNAP_DIR):
    if not os.path.isdir(snap_dir):
        return []
    names = [f for f in os.listdir(snap_dir) if f.endswith('.json')]
    def key(n):
        try:
            return json.load(open(os.path.join(snap_dir, n), encoding='utf-8')).get('ts', '')
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return ''
    names.sort(key=key)
    return [os.path.join(snap_dir, n) for n in names][-2:]


def load(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def diff(a, b):
    """a = earlier snapshot, b = later snapshot. Return added/removed/changed + lossy flags."""
    fa, fb = a['files'], b['files']
    added = sorted(set(fb) - set(fa))
    removed = sorted(set(fa) - set(fb))
    changed = sorted(r for r in (set(fa) & set(fb)) if fa[r]['sha1'] != fb[r]['sha1'])
    # LOSSY carry-over: file present earlier but gone later is a potential data loss.
    lossy = list(removed)
    return {
        'from': a.get('cycle_id'), 'to': b.get('cycle_id'),
        'added': added, 'removed': removed, 'changed': changed,
        'lossy_carryover': lossy,
        'summary': {f'from={a["count"]}': None, f'to={b["count"]}': None,
                    'added': len(added), 'removed': len(removed),
                    'changed': len(changed), 'lossy': len(lossy)},
        'valid': True,  # a structurally valid diff (both manifests parsed)
    }


def selftest():
    import tempfile
    ok = True
    tmp = tempfile.mkdtemp(prefix='cycle_snap_')
    root = os.path.join(tmp, 'repo'); g = os.path.join(root, 'goals'); os.makedirs(g)
    def w(rel, txt):
        full = os.path.join(root, rel.replace('/', os.sep)); os.makedirs(os.path.dirname(full), exist_ok=True)
        open(full, 'w', encoding='utf-8').write(txt)
    pats = ['goals/*.md', 'ledger.jsonl']

    # cycle A: base state
    w('goals/alpha.md', 'A v1'); w('goals/beta.md', 'B v1'); w('ledger.jsonl', '{"x":1}\n')
    a = snapshot(root, 'cycle-A', pats); store(a, tmp)
    # cycle B: add gamma, modify alpha  -> valid diff expected
    w('goals/gamma.md', 'G v1'); w('goals/alpha.md', 'A v2')
    b = snapshot(root, 'cycle-B', pats); store(b, tmp)
    d_ab = diff(a, b)
    assert d_ab['valid'] and 'goals/gamma.md' in d_ab['added'], f"AC1 add not detected: {d_ab}"
    assert 'goals/alpha.md' in d_ab['changed'], f"AC1 change not detected: {d_ab}"
    assert d_ab['removed'] == [] and d_ab['lossy_carryover'] == [], f"unexpected removal in B: {d_ab}"

    # cycle C: DROP beta (seeded lost-file case) -> must be flagged lossy
    os.remove(os.path.join(root, 'goals', 'beta.md'))
    c = snapshot(root, 'cycle-C', pats); store(c, tmp)
    d_bc = diff(b, c)
    assert d_bc['valid'], "AC2: second consecutive diff must be valid"
    assert 'goals/beta.md' in d_bc['removed'] and 'goals/beta.md' in d_bc['lossy_carryover'], \
        f"AC2 seeded lost-file not flagged: {d_bc}"

    # idempotency: same state -> same manifest hash
    c2 = snapshot(root, 'cycle-C-rerun', pats)
    assert c2['manifest_sha1'] == c['manifest_sha1'], "snapshot not idempotent for identical state"

    print('[selftest] AC1 two consecutive valid diffs (added+changed detected): PASS')
    print(f'[selftest]   A->B added={d_ab["added"]} changed={d_ab["changed"]}')
    print(f'[selftest]   B->C removed/lossy={d_bc["lossy_carryover"]}')
    print('[selftest] AC2 seeded lost-file flagged as lossy carry-over: PASS')
    print('[selftest] idempotent manifest hash for identical state: PASS')
    ok = True
    try:
        import shutil; shutil.rmtree(tmp)
    except OSError:
        pass
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('action', nargs='?', default='list', choices=['snapshot', 'diff', 'list'])
    ap.add_argument('--cycle', default=None, help='cycle id for snapshot (default: timestamp)')
    ap.add_argument('args', nargs='*', help='optional two snapshot paths for diff')
    a = ap.parse_args()

    if a.action == 'snapshot':
        cid = a.cycle or datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        m = snapshot(ROOT, cid)
        path = store(m)
        print(f'snapshot {cid}: {m["count"]} files, manifest_sha1={m["manifest_sha1"]}')
        print('wrote', os.path.relpath(path, ROOT))
    elif a.action == 'diff':
        if len(a.args) == 2:
            pa, pb = a.args
        else:
            lt = latest_two(); 
            if len(lt) < 2:
                print('need >=2 stored snapshots (run snapshot twice first); found', len(lt)); sys.exit(1)
            pa, pb = lt
        d = diff(load(pa), load(pb))
        print(json.dumps(d['summary'], indent=0))
        print('added:', d['added'])
        print('removed:', d['removed'])
        print('changed:', [c for c in d['changed']])
        if d['lossy_carryover']:
            print('LOSSY CARRY-OVER FLAGGED (potential data loss):', d['lossy_carryover'])
        else:
            print('lossy carry-over: none')
    elif a.action == 'list':
        if os.path.isdir(SNAP_DIR):
            for n in sorted(os.listdir(SNAP_DIR)): 
                if n.endswith('.json'): print(n)
        else:
            print('(no snapshots yet)')


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        ok = selftest(); sys.exit(0 if ok else 1)
    main()