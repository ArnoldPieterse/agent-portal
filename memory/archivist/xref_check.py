#!/usr/bin/env python3
"""
Archivist Goal #7 - Cross-Reference Integrity.

Scans the modular memory KB (memory/**/*.md) for cross-reference links and
verifies every one resolves to an existing file. Two reference forms are
checked (the KB's real xref syntax):
  * arrow pointers   :   -> path/to/file.ext
  * pointer refs     :   (pointer: path/to/file.ext)
  * markdown links   :   [text](path/to/file.ext)   (only when target looks like a path)

Modes:
  --check   report broken xrefs, no writes (default)
  --fix     auto-fix: redirect to the unique same-basename file elsewhere in
            the tree if exactly one exists, else quarantine-flag the ref as
            dead with the prefix FLAG. A flagged-dead ref is intentionally
            marked (no longer a silently-dangling live pointer).
  --report  PATH   write a markdown report of the check to PATH

A run is "clean" when 0 *live* broken xrefs remain; refs quarantined with
FLAG are counted separately as flagged-dead (not broken).

Exit code: 0 always (report tool); use stdout JSON summary for automation.
"""
import os, re, sys, json, datetime

ROOT = "memory"
FLAG = "\u26a0missing:"          # dead-ref quarantine marker
EXTS = ("md", "py", "json", "jsonl", "js", "css", "html", "txt", "log",
        "bat", "vbs", "csv")
ext_re = "|".join(EXTS)
ARROW   = re.compile(r'(->\s*)([A-Za-z0-9_./\\-]+\.(?:%s))' % ext_re)
POINTER = re.compile(r'(\(pointer:\s*)([A-Za-z0-9_./\\-]+\.(?:%s))\)' % ext_re)
MDLINK  = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')


def is_pathlike(t):
    t = t.split('#')[0].split('?')[0].strip()
    if not t or t.startswith(('http://', 'https://', 'mailto:', FLAG)):
        return False
    return ('.' in os.path.basename(t) or '/' in t)


def _is_own_output(name):
    """This tool's own report/log artifacts must not be measured (self-contamination)."""
    return name.startswith('xref-check-report-') or name.startswith('xref-fix-log-')


def all_md_files():
    out = []
    for dp, _, fn in os.walk(ROOT):
        for f in fn:
            if f.endswith('.md') and not _is_own_output(f):
                out.append(os.path.join(dp, f))
    return sorted(out)


def _norm(p):
    return os.path.normpath(p).replace('\\', '/')


def resolve(base_dir, target):
    t = target.split('#')[0].split('?')[0].strip().lstrip('./')
    if not t or t.startswith(('http://', 'https://', 'mailto:', FLAG)):
        return None  # external / flagged -> not a local xref
    cands = [_norm(os.path.join(base_dir, t)), _norm(t),
             _norm(os.path.join('memory', t)), _norm(os.path.join(ROOT, t))]
    for c in cands:
        if os.path.exists(c):
            return c
    return None


def iter_refs(fp):
    """yield (line_no, kind, prefix, target, span_start, span_end) for each ref."""
    base = os.path.dirname(fp)
    lines = open(fp, encoding='utf-8', errors='replace').read().splitlines()
    for i, line in enumerate(lines, 1):
        for m in ARROW.finditer(line):
            yield i, 'arrow', m.group(1), m.group(2)
        for m in POINTER.finditer(line):
            yield i, 'pointer', m.group(1), m.group(2)
        for m in MDLINK.finditer(line):
            if is_pathlike(m.group(2)):
                yield i, 'mdlink', '[%s](' % m.group(1), m.group(2)


def broken_refs(fp):
    base = os.path.dirname(fp)
    res = []
    for (i, kind, prefix, target) in iter_refs(fp):
        if resolve(base, target) is None:
            res.append((i, kind, prefix, target))
    return res


def basename_index():
    """basename -> list of normalized paths (for redirect candidates)."""
    idx = {}
    for dp, _, fn in os.walk(ROOT):
        for f in fn:
            if any(f.endswith('.' + e) for e in EXTS):
                idx.setdefault(_norm(os.path.join(dp, f)).split('/')[-1], []).append(
                    _norm(os.path.join(dp, f)))
    return idx


def rel_to(base_dir, abs_target):
    """relative path from base_dir to abs_target (forward slashes)."""
    try:
        r = os.path.relpath(abs_target, base_dir)
    except ValueError:
        return abs_target
    return _norm(r)


def cmd_check(report_path=None):
    bidx = basename_index()
    files = all_md_files()
    total_live = 0
    flagged_dead = 0
    broken_list = []
    for fp in files:
        # count already-flagged dead refs
        txt = open(fp, encoding='utf-8', errors='replace').read()
        flagged_dead += txt.count(FLAG)
        for (i, kind, prefix, target) in iter_refs(fp):
            if resolve(os.path.dirname(fp), target) is None:
                total_live += 1
                broken_list.append((fp, i, kind, target))
    summary = {
        'scanned_files': len(files),
        'broken_live_xrefs': total_live,
        'flagged_dead_refs': flagged_dead,
        'clean': total_live == 0,
    }
    out = ["# Xref Integrity Report", "Generated: %s by memory/archivist/xref_check.py"
           % datetime.datetime.now().isoformat(timespec='seconds'), "",
           "- scanned files: %d" % len(files),
           "- broken live xrefs: %d" % total_live,
           "- flagged-dead (quarantined) refs: %d" % flagged_dead,
           "- status: **%s**" % ("CLEAN (0 broken)" if total_live == 0 else "NOT CLEAN")]
    if broken_list:
        out.append("\n## Broken xrefs")
        for fp, i, kind, target in broken_list:
            out.append("- `%s:%d` [%s] -> %s" % (fp.replace('\\', '/'), i, kind, target))
    text = "\n".join(out) + "\n"
    if report_path:
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        open(report_path, 'w', encoding='utf-8').write(text)
        summary['report'] = report_path
    print(json.dumps(summary, indent=2))
    return summary


def cmd_fix(log_path):
    bidx = basename_index()
    files = all_md_files()
    actions = []   # (file,line,kind,target,action,detail)
    changed_files = 0
    for fp in files:
        base = os.path.dirname(fp)
        lines = open(fp, encoding='utf-8', errors='replace').read().splitlines()
        new_lines = []
        file_changed = False
        for i, line in enumerate(lines, 1):
            orig = line
            # process each ref kind on this line; rebuild target tokens
            def fix_arrow(m):
                nonlocal file_changed
                t = m.group(2)
                if t.startswith(FLAG) or resolve(base, t): return m.group(0)
                cands = [c for c in bidx.get(t.split('/')[-1], []) if _norm(os.path.join(fp)) != c]
                if len(cands) == 1:
                    newt = rel_to(base, cands[0]); file_changed = True
                    actions.append((fp, i, 'arrow', t, 'redirect', newt))
                    return m.group(1) + newt
                file_changed = True
                actions.append((fp, i, 'arrow', t, 'quarantine', ''))
                return m.group(1) + FLAG + t
            def fix_pointer(m):
                nonlocal file_changed
                t = m.group(2)
                if t.startswith(FLAG) or resolve(base, t): return m.group(0)
                cands = [c for c in bidx.get(t.split('/')[-1], []) if _norm(os.path.join(fp)) != c]
                if len(cands) == 1:
                    newt = rel_to(base, cands[0]); file_changed = True
                    actions.append((fp, i, 'pointer', t, 'redirect', newt))
                    return m.group(1) + newt + ')'
                file_changed = True
                actions.append((fp, i, 'pointer', t, 'quarantine', ''))
                return m.group(1) + FLAG + t + ')'
            line = ARROW.sub(fix_arrow, line)
            line = POINTER.sub(fix_pointer, line)
            # markdown links with path-like missing targets -> quarantine target
            def fix_md(m):
                nonlocal file_changed
                t = m.group(2)
                if not is_pathlike(t) or t.startswith(FLAG): return m.group(0)
                if resolve(base, t): return m.group(0)
                cands = [c for c in bidx.get(t.split('/')[-1], []) if _norm(os.path.join(fp)) != c]
                if len(cands) == 1:
                    newt = rel_to(base, cands[0]); file_changed = True
                    actions.append((fp, i, 'mdlink', t, 'redirect', newt))
                    return '[%s](%s)' % (m.group(1), newt)
                file_changed = True
                actions.append((fp, i, 'mdlink', t, 'quarantine', ''))
                return '[%s](%s%s)' % (m.group(1), FLAG, t)
            line = MDLINK.sub(fix_md, line)
            if line != orig:
                file_changed = True
            new_lines.append(line)
        if file_changed:
            open(fp, 'w', encoding='utf-8').write("\n".join(new_lines) + "\n")
            changed_files += 1
    # write log
    now = datetime.datetime.now().isoformat(timespec='seconds')
    out = ["# Xref Auto-Fix Log", "Generated: %s by memory/archivist/xref_check.py --fix" % now, "",
           "- files changed: %d" % changed_files,
           "- actions taken: %d" % len(actions)]
    redir = sum(1 for a in actions if a[4] == 'redirect')
    quar = sum(1 for a in actions if a[4] == 'quarantine')
    out.append("- redirects: %d   quarantines (flagged-dead): %d" % (redir, quar))
    out.append("")
    for fp, i, kind, target, action, detail in actions:
        if action == 'redirect':
            out.append("- `%s:%d` [%s] REDIRECT %s -> %s" % (fp.replace('\\', '/'), i, kind, target, detail))
        else:
            out.append("- `%s:%d` [%s] QUARANTINE %s  (no unique match; flagged dead)" % (fp.replace('\\', '/'), i, kind, target))
    log = "\n".join(out) + "\n"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    open(log_path, 'w', encoding='utf-8').write(log)
    print(json.dumps({'files_changed': changed_files, 'actions': len(actions),
                      'redirects': redir, 'quarantines': quar, 'log': log_path}, indent=2))


if __name__ == '__main__':
    args = sys.argv[1:]
    if '--fix' in args:
        lp = os.path.join('memory', 'archivist', 'xref-fix-log-%s.md'
                          % datetime.datetime.now().strftime('%Y-%m-%d'))
        cmd_fix(lp)
    else:
        rp = None
        if '--report' in args:
            rp = args[args.index('--report') + 1]
        elif '-r' in args:
            rp = args[args.index('-r') + 1]
        cmd_check(rp)
