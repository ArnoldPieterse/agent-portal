#!/usr/bin/env python3
"""Dangling-pointer auto-triage + fix for stale_claim_check.py output.

Usage:
    python memory/ops/dangling_pointer_fix.py            # report only (dry-run)
    python memory/ops/dangling_pointer_fix.py --execute  # apply fixes to source files
    python memory/ops/dangling_pointer_fix.py --report   # write dated report file

Categories:
    TEMPLATE       - target contains YYYY-MM-DD placeholder (harmless, skip)
    TEST_ARTIFACT  - target in _conflict_test/ or ghost/ (intentional test targets)
    REAL_DANGLING  - target should exist but doesn't; fuzzy-match for fix

For REAL_DANGLING with a fuzzy match, the fix rewrites the pointer in the
source file to point at the closest existing sibling.
"""
import subprocess, re, os, sys, json, pathlib
from datetime import date
from difflib import get_close_matches

def run_stale_check():
    r = subprocess.run(['python', 'memory/ops/stale_claim_check.py'],
                       capture_output=True, text=True)
    return r.stdout

def parse_missing(stdout):
    refs = []
    for line in stdout.splitlines():
        if '[MISSING]' not in line:
            continue
        parts = line.split(' -> ')
        if len(parts) != 2:
            continue
        src = parts[0].replace('[MISSING] ', '').strip()
        tgt = parts[1].strip()
        refs.append((src, tgt))
    return refs

def categorize(refs):
    cats = {'TEMPLATE': [], 'TEST_ARTIFACT': [], 'REAL_DANGLING': []}
    for src, tgt in refs:
        if 'YYYY-MM-DD' in tgt or 'cycle-N' in tgt.lower():
            cats['TEMPLATE'].append((src, tgt))
        elif '_conflict_test' in tgt or 'ghost/' in tgt or 'nonexistent' in tgt:
            cats['TEST_ARTIFACT'].append((src, tgt))
        else:
            cats['REAL_DANGLING'].append((src, tgt))
    return cats

def fuzzy_fix(src, tgt):
    """Try to find a close match for the missing target. Returns (new_tgt, confidence) or None."""
    d = os.path.dirname(tgt)
    fname = os.path.basename(tgt)
    stem, ext = os.path.splitext(fname)
    
    if not os.path.isdir(d):
        return None
    
    actual = [f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))]
    stems = [os.path.splitext(f)[0] for f in actual]
    
    matches = get_close_matches(stem, stems, n=1, cutoff=0.6)
    if matches:
        new_tgt = os.path.join(d, matches[0] + ext)
        if os.path.exists(new_tgt):
            return (new_tgt, 0.6)
    return None

def apply_fix(src, old_tgt, new_tgt):
    """Replace old_tgt with new_tgt in the source file. Returns True on success."""
    src_path = pathlib.Path(src)
    if not src_path.exists():
        return False
    text = src_path.read_text(encoding='utf-8')
    if old_tgt not in text:
        return False
    new_text = text.replace(old_tgt, new_tgt)
    src_path.write_text(new_text, encoding='utf-8')
    return True

def main():
    execute = '--execute' in sys.argv
    write_report = '--report' in sys.argv
    
    print("DANGLING POINTER FIX  " + date.today().isoformat())
    stdout = run_stale_check()
    refs = parse_missing(stdout)
    cats = categorize(refs)
    
    total = len(refs)
    print(f"Total missing refs: {total}")
    print(f"  TEMPLATE (skip):       {len(cats['TEMPLATE'])}")
    print(f"  TEST_ARTIFACT (skip):  {len(cats['TEST_ARTIFACT'])}")
    print(f"  REAL_DANGLING:         {len(cats['REAL_DANGLING'])}")
    
    fixed = 0
    unfixed = []
    for src, tgt in cats['REAL_DANGLING']:
        result = fuzzy_fix(src, tgt)
        if result:
            new_tgt, conf = result
            action = "FIXED" if execute else "WOULD FIX"
            if execute:
                ok = apply_fix(src, tgt, new_tgt)
                action = "FIXED" if ok else "FAILED"
                if ok:
                    fixed += 1
            print(f"  [{action}] {src}")
            print(f"      - {tgt}")
            print(f"      + {new_tgt}  (conf={conf:.2f})")
        else:
            unfixed.append((src, tgt))
            print(f"  [LOST]     {src} -> {tgt}  (no match)")
    
    if execute:
        print(f"\nApplied {fixed}/{len(cats['REAL_DANGLING'])} fixes. {len(unfixed)} truly lost.")
    else:
        fixable = len(cats['REAL_DANGLING']) - len(unfixed)
        print(f"\nDry-run: {fixable} fixable, {len(unfixed)} lost. Re-run with --execute to apply.")
    
    if write_report:
        report_path = f'memory/ops/dangling-pointer-report-{date.today().isoformat()}.md'
        lines = [f"# Dangling Pointer Report {date.today().isoformat()}",
                 f"Total: {total} | Template: {len(cats['TEMPLATE'])} | Test: {len(cats['TEST_ARTIFACT'])} | Real: {len(cats['REAL_DANGLING'])}",
                 f"Fixed: {fixed} | Lost: {len(unfixed)}", ""]
        for src, tgt in unfixed:
            lines.append(f"- [LOST] {src} -> {tgt}")
        pathlib.Path(report_path).write_text('\n'.join(lines), encoding='utf-8')
        print(f"Report written: {report_path}")

if __name__ == '__main__':
    main()
