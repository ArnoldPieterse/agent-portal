#!/usr/bin/env python3
"""Runbook Executability Audit - Forge
Scans memory/ops/*.md for runbooks, checks if a corresponding executable script exists.
Exit codes: 0 = all runbooks have executables, 1 = gaps found (report printed), 2 = error.

Usage: python memory/forge/runbook_audit.py [--json]
"""
import pathlib, re, json, sys

ROOT = pathlib.Path('.')
OPS = ROOT / 'memory' / 'ops'
ARCHIVIST = ROOT / 'memory' / 'archivist'

# Known runbook-to-script mappings (explicit)
KNOWN_MAP = {
    'autonomous-remediation-loop-runbook-2026-11-24.md': 'memory/ops/remediation_loop_healthcheck.py',
    'boot-deployment-runbook.md': 'memory/ops/verify_boot_deployment.py',
    'boot-detection-runbook.md': 'memory/ops/verify_boot_detection.py',
    'citation-phantom-triage-runbook.md': 'memory/ops/verify_claims.py',
    'live-leg-runbook-2026-11-20.md': 'memory/ops/live_leg_preflight.py',
    'memory-tree-runbook.md': 'memory/archivist/orphan_remediation.py',  # multi-script runbook
    'runbook-cockpit-feed-refresh-deploy-2026-11-24.md': 'memory/ops/cockpit_coverage_check.py',
    'windows-runbook.md': 'memory/ops/reboot_recovery_check.py',
}

# Files that are NOT runbooks (reports, notes, specs)
NON_RUNBOOK = {
    'runbook-notes.md',           # free-form notes
    'runbook-staleness-audit-2026-11-24.md',  # audit results doc
    'INDEX.md',                   # pointer map
}

def is_runbook(fname):
    """Heuristic: has 'runbook' in name, or contains step-by-step commands."""
    if fname in NON_RUNBOOK:
        return False
    if 'runbook' in fname.lower():
        return True
    # Also flag files with explicit "Step 1:" / numbered procedure patterns
    p = OPS / fname
    if p.exists() and p.stat().st_size < 20000:
        text = p.read_text(encoding='utf-8', errors='replace')
        if re.search(r'(?:^\s*#+ ?Step \d+|^- `python )', text, re.M):
            return True
    return False

def find_script_for_runbook(fname):
    """Find executable script corresponding to a runbook."""
    # 1. Check explicit map
    if fname in KNOWN_MAP:
        target = pathlib.Path(KNOWN_MAP[fname])
        return str(target) if target.exists() else None
    
    # 2. Fuzzy match: strip 'runbook', '-YYYY-MM-DD', '.md' from name, look for .py
    base = fname.replace('.md', '').replace('-runbook', '').replace('runbook-', '')
    # Remove date suffixes
    base = re.sub(r'-\d{4}-\d{2}-\d{2}', '', base)
    words = [w for w in base.split('-') if len(w) > 2]
    
    candidates = []
    search_dirs = [OPS, ARCHIVIST, ROOT / 'memory' / 'forge']
    for d in search_dirs:
        if not d.exists():
            continue
        for py in d.glob('*.py'):
            stem_words = set(py.stem.lower().split('_'))
            # Match if >=50% of runbook words appear in script name
            overlap = sum(1 for w in words if any(w in sw or sw in w for sw in stem_words))
            if words and overlap / len(words) >= 0.5:
                candidates.append(str(py))
    
    return candidates[0] if candidates else None

def main():
    json_mode = '--json' in sys.argv
    
    runbooks = sorted(f.name for f in OPS.glob('*.md') if is_runbook(f.name))
    results = []
    
    for rb in runbooks:
        script = find_script_for_runbook(rb)
        status = 'OK' if script else 'GAP'
        results.append({
            'runbook': rb,
            'script': script or None,
            'status': status,
        })
    
    gaps = [r for r in results if r['status'] == 'GAP']
    
    if json_mode:
        print(json.dumps({'total_runbooks': len(runbooks), 'with_scripts': len(results)-len(gaps),
                          'gaps': len(gaps), 'results': results}, indent=2))
    else:
        print(f"=== Runbook Executability Audit ===")
        print(f"Total runbooks found: {len(runbooks)}")
        print(f"With executable scripts: {len(results) - len(gaps)}")
        print(f"GAPS (no script): {len(gaps)}")
        print()
        for r in results:
            icon = '✓' if r['status'] == 'OK' else '✗'
            print(f"  {icon} {r['runbook']}")
            if r['script']:
                print(f"      -> {r['script']}")
            else:
                print(f"      -> NO SCRIPT (needs conversion)")
    
    # Exit code: 0 if no gaps, 1 if gaps exist
    sys.exit(1 if gaps else 0)

if __name__ == '__main__':
    main()
