"""
verification_coverage.py — Verification Coverage Map Builder (cycle 20)
Owner: Verifier (goal #7). Built by Builder assist 2026-11-27.

Usage:
  python memory/verifier/verification_coverage.py          # build + write JSON
  python memory/verifier/verification_coverage.py --check  # verify target met, exit 0/1

AC: "map covers 100% of tracked files; pct computed correctly; gap list actionable"
"""
import os, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

STALE_HOURS = 48
TARGET_PCT = 90
OUTPUT = Path(__file__).parent / "verification_coverage_map.json"

def get_tracked_files():
    """Enumerate all portal-tracked files."""
    tracked = []
    for f in sorted(Path('.').glob('*.py')):
        if f.is_file():
            tracked.append(f.name)
    ui = Path('ui')
    if ui.exists():
        for f in sorted(ui.rglob('*')):
            if f.is_file() and not f.name.startswith('.'):
                tracked.append(str(f).replace(os.sep, '/'))
    mem = Path('memory')
    if mem.exists():
        for f in sorted(mem.rglob('*.py')):
            if f.is_file():
                tracked.append(str(f).replace(os.sep, '/'))
    return sorted(set(tracked))

def get_scope(filepath):
    """Classify: production / operational / debug / one-off / other."""
    basename = os.path.basename(filepath)
    if basename.startswith('_') or any(k in basename.lower() for k in ('probe', 'debug', 'dbg')):
        return 'debug'
    if re.match(r'^r\d+_', basename) or re.search(r'-r\d+-', basename):
        return 'one-off'
    if filepath.startswith('ui/'):
        return 'production'
    core = {'agent_portal.py', 'agents_schema.py', 'memory_mirror.py', 'goal_ledger.py'}
    if basename in core:
        return 'production'
    op_kw = ['trigger', 'monitor', 'generator', 'scheduler', 'dispatcher',
             'guard', 'census', 'fsm', 'contracts', 'health', 'bus']
    if any(kw in basename.lower() for kw in op_kw):
        return 'production'
    if filepath.startswith('memory/'):
        return 'operational'
    return 'other'

def build_evidence_index():
    """Scan .md files for verification signals referencing code files."""
    signals = {}
    md_files = list(Path('memory').rglob('*.md'))
    md_files += [f for f in Path('.').glob('*.md') if f.is_file()]
    pat = re.compile(r'(PASS|REACHED|verified:|ALL PASS|selftest.*PASS)', re.IGNORECASE)
    for md in md_files:
        try:
            content = md.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        if not pat.search(content):
            continue
        mtime = datetime.fromtimestamp(md.stat().st_mtime, tz=timezone.utc)
        for match in re.finditer(r'[\w/\\.-]+\.(?:py|js|css|html)', content):
            ref = match.group().replace('\\', '/')
            signals.setdefault(os.path.basename(ref), []).append({
                'evidence': str(md).replace(os.sep, '/'),
                'mtime': mtime.isoformat(),
                'ref': ref
            })
    return signals

def build():
    tracked = get_tracked_files()
    evidence = build_evidence_index()
    now = datetime.now(tz=timezone.utc)
    
    results, stats_all, stats_prod = [], {'verified':0,'unverified':0,'stale_verified':0}, {'verified':0,'unverified':0,'stale_verified':0}
    
    for fp in tracked:
        bn = os.path.basename(fp)
        sigs = evidence.get(bn, [])
        if not sigs:
            status = 'unverified'
        else:
            latest = max(sigs, key=lambda s: s['mtime'])
            age_h = (now - datetime.fromisoformat(latest['mtime'])).total_seconds() / 3600
            status = 'stale_verified' if age_h > STALE_HOURS else 'verified'
        
        scope = get_scope(fp)
        stats_all[status] += 1
        if scope in ('production', 'operational'):
            stats_prod[status] += 1
        
        gap = None
        if status == 'unverified':
            if scope == 'production':
                gap = f"Add to regression battery or write evidence leaf referencing {bn}"
            elif scope == 'operational':
                gap = f"Run selftest or --once; log in memory/verifier/"
            else:
                gap = "Out of core scope - mark exempt or add to debug suite"
        
        results.append({'file': fp, 'status': status, 'scope': scope, 
                       'evidence_count': len(sigs), 'gap_action': gap})
    
    total = len(results)
    prod_total = sum(1 for r in results if r['scope'] in ('production','operational'))
    pct_all = round(stats_all['verified']/total*100, 1) if total else 0
    pct_prod = round(stats_prod['verified']/prod_total*100, 1) if prod_total else 0
    gaps = [r for r in results if r['status']=='unverified' and r['scope'] in ('production','operational')]
    
    return {
        'generated': now.isoformat(), 'version': 2,
        'total_tracked': total, 'production_operational_total': prod_total,
        'stats_all': stats_all, 'stats_production_operational': stats_prod,
        'verified_pct_all': pct_all, 'verified_pct_production': pct_prod,
        'target_pct': TARGET_PCT,
        'gap_to_target_production': max(0, round(TARGET_PCT - pct_prod, 1)),
        'stale_threshold_hours': STALE_HOURS,
        'actionable_gap_count': len(gaps),
        'gap_list': gaps[:50],
        'files': results
    }

if __name__ == '__main__':
    if '--check' in sys.argv:
        data = build()
        met = data['verified_pct_production'] >= TARGET_PCT
        print(f"Coverage check: {data['verified_pct_production']}% (target {TARGET_PCT}%) -> {'PASS' if met else 'FAIL'}")
        sys.exit(0 if met else 1)
    else:
        data = build()
        OUTPUT.write_text(json.dumps(data, indent=2), encoding='utf-8')
        print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size} bytes)")
        print(f"  Total: {data['total_tracked']}, Prod+Ops: {data['production_operational_total']}")
        print(f"  Verified (prod): {data['verified_pct_production']}% (target {TARGET_PCT}%)")
        print(f"  Actionable gaps: {data['actionable_gap_count']}")
