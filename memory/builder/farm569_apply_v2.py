#!/usr/bin/env python3
"""
farm569_apply_v2.py (v2: fixed canonical path) — apply the farm.py:569 cross-drive os.path.relpath fix.

BUG (reproduced on Black seat, py 3.13.18):
    os.path.relpath(target, start) raises
        ValueError: path is on mount 'D:', start on mount 'Z:'
    when target and start are on different Windows drives. This makes the
    dcabots self-test exit non-zero even though all 29 engine/logic tests pass.

FIX (strict superset, zero behavior change when no error):
    def safe_relpath(target, start):
        try:
            return os.path.relpath(target, start)
        except ValueError:
            return os.path.abspath(target)   # cross-drive: relpath undefined
    and replace every `os.path.relpath(` call site with `safe_relpath(`.

SAFETY:
  * DRY-RUN BY DEFAULT — prints exactly what would change, writes nothing.
  * Pass --apply to write. A timestamped backup (farm.py.bak-<ts>) is written first.
  * Idempotent: a second run reports "already applied" and changes nothing; it
    NEVER rewrites the helper's own internal os.path.relpath call (no recursion).
  * py_compile check after apply; aborts loudly on syntax error.
  * Pattern-based (not line-number hardcoded), so it survives line drift.

USAGE (on the host that has the real farm.py, e.g. White console):
    python farm569_apply.py projects/dcabots/farm.py            # dry-run
    python farm569_apply.py projects/dcabots/farm.py --apply    # apply + backup
    python farm569_apply.py                                      # auto-locate, dry-run
"""
import os, sys, re, shutil, time, py_compile

HELPER = '''
def safe_relpath(target, start):
    """os.path.relpath that falls back to an absolute path across drives.
    Windows relpath is undefined (ValueError) when target and start sit on
    different mount points; an absolute path is the sane cross-drive answer."""
    try:
        return os.path.relpath(target, start)
    except ValueError:
        return os.path.abspath(target)
'''


def _helper_span(lines):
    """Return (start_idx, end_idx) of the safe_relpath function body, or None.
    end_idx is exclusive: first line after the def that starts at column 0."""
    hstart = next((i for i, ln in enumerate(lines)
                   if re.match(r'def safe_relpath\(', ln)), None)
    if hstart is None:
        return None
    hend = len(lines)
    for j in range(hstart + 1, len(lines)):
        if lines[j].strip() and lines[j][0] not in ' \t':
            hend = j
            break
    return (hstart, hend)


def locate(explicit=None):
    if explicit:
        return explicit
    candidates = [
        # v2 FIX: real canonical path is double-dcabots (project dir / package dir).
        'projects/dcabots/dcabots/farm.py',
        r'Z:\projects\dcabots\dcabots\farm.py',
        r'Z:\dcabots\dcabots\farm.py',
        # legacy single-dcabots kept as fallback only:
        'projects/dcabots/farm.py',
        r'Z:\projects\dcabots\farm.py',
        r'Z:\dcabots\farm.py',
        'farm.py',
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def main():
    do_apply = '--apply' in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    path = locate(args[0] if args else None)
    if not path or not os.path.isfile(path):
        print('FARM_NOT_FOUND: no farm.py reachable from this seat.')
        print('Run this on the host that has the real source (White console), e.g.:')
        print('  python farm569_apply.py projects/dcabots/farm.py --apply')
        return 3
    print('target :', os.path.abspath(path))
    with open(path, 'r', encoding='utf-8', newline='') as f:
        src = f.read()
    lines = src.split('\n')

    span = _helper_span(lines)                 # (start,end) of helper body or None
    already_helper = span is not None
    all_sites = [i for i, ln in enumerate(lines) if 'os.path.relpath(' in ln]
    sites = [i + 1 for i in all_sites
             if not (span and span[0] <= i < span[1])]   # buggy sites = outside helper

    print(f'helper present? {already_helper}   '
          f'os.path.relpath( call sites: {len(sites)} at lines {sites}')

    if already_helper and not sites:
        try:
            py_compile.compile(path, doraise=True); ok = True
        except Exception as ex:
            ok = False
        print('ALREADY_APPLIED: no buggy call sites outside the helper. No file written.')
        print('py_compile:', 'PASS' if ok else f'FAIL {ex}')
        return 0 if ok else 2
    if not sites and not already_helper:
        print('NO os.path.relpath( call site found - context differs from the prep note.')
        print('Do NOT insert an unused helper. Inspect the file manually.')
        return 2

    # Build new source: replace ONLY call sites outside the helper body, then insert
    # the helper if it is not already there.
    nl = list(lines)
    for i in all_sites:
        if not (span and span[0] <= i < span[1]):
            nl[i] = nl[i].replace('os.path.relpath(', 'safe_relpath(')
    changed = [f'  L{i+1}: os.path.relpath( -> safe_relpath(' for i in all_sites
               if not (span and span[0] <= i < span[1])]
    if not already_helper:
        imp_idx = max([i for i, ln in enumerate(nl)
                       if re.match(r'^(import |from )', ln)], default=-1)
        block = [l for l in HELPER.rstrip('\n').split('\n')]
        if imp_idx >= 0:
            nl[imp_idx + 1:imp_idx + 1] = [''] + block
            changed.append(f'  inserted safe_relpath helper after line {imp_idx + 1}')
        else:
            nl = block + [''] + nl
            changed.append('  inserted safe_relpath helper at top')
    new_src = '\n'.join(nl)

    if not do_apply:
        print('\nDRY-RUN (no files written). Would change:')
        for c in changed:
            print(c)
        print('\nRe-run with --apply to write. A timestamped backup will be created.')
        return 0

    ts = time.strftime('%Y%m%d-%H%M%S')
    bak = path + f'.bak-{ts}'
    shutil.copy2(path, bak)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(new_src)
    try:
        py_compile.compile(path, doraise=True); compile_ok = True; e = None
    except Exception as ex:
        compile_ok = False; e = ex
    print('\nAPPLIED. backup:', os.path.abspath(bak))
    for c in changed:
        print(c)
    print('py_compile:', 'PASS' if compile_ok else f'FAIL {e}')

    # Verify no *buggy* call sites remain (exclude the helper's own body).
    with open(path, 'r', encoding='utf-8', newline='') as f:
        newlines = f.read().split('\n')
    fspan = _helper_span(newlines)
    residual = [i + 1 for i, ln in enumerate(newlines)
                if 'os.path.relpath(' in ln
                and not (fspan and fspan[0] <= i < fspan[1])]
    print('residual buggy os.path.relpath( lines (helper body excluded):', residual or 'none')
    return 0 if (compile_ok and not residual) else 2


if __name__ == '__main__':
    sys.exit(main())
