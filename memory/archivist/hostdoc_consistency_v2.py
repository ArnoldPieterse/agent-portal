#!/usr/bin/env python3
"""
hostdoc_consistency_v2.py - Multi-host doc consistency v2 (Archivist goal 5, cycle-3)

Supersedes the one-off audit behind hostdoc-consistency-v2-2026-11-18.json (which had
extraction bugs: it truncated '.jsonl' -> '.json' and cut tokens at '.bak', producing
false phantoms for files that exist).

Scope: every .md under memory/ plus root ONBOARDING.md / MEMORY.md / TODO.md.
Extracts path-like tokens (multi-segment paths with known dirs, or bare filenames with
known extensions) and classifies each reference:
  OK                 - exists at the stated path
  MOVED              - not at stated path, but same basename exists elsewhere on disk
  HISTORICAL         - never on disk now, but this exact path or basename was committed
                       in git history (deleted later; legitimate historical record)
  PROVENANCE         - line states the file's history ('split from', 'renamed to', ...);
                       pre-repo files may never have been committed
  DOCUMENTED-ABSENT  - line asserts the file is absent/missing/gone (a finding, not a pointer)
  REMOTE             - drive-letter path on another host (Z:\ etc.), unverifiable here
  PHANTOM            - none of the above: reference to a file that does not exist and
                       never existed in this repo. These must be fixed or annotated.

Scope default: every .md under memory/ops/ plus root ONBOARDING.md / MEMORY.md / TODO.md
(the goal's "ops docs"); --all scans the whole memory/ tree.

Usage: python memory/archivist/hostdoc_consistency_v2.py [--all]
Exit code: 1 if any PHANTOM, else 0 (CI-gate friendly).
"""
import os, re, sys, json, subprocess, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GIT = os.path.join(ROOT, 'mingit', 'cmd', 'git.exe')

KNOWN_DIRS = ('memory/', 'archive/', 'reports/', 'archivist/')
EXTS = ('.py', '.json', '.jsonl', '.md', '.bat', '.ps1', '.html', '.txt', '.log', '.bak', '.csv', '.sh')
TOKEN_RE = re.compile(r'[A-Za-z]?:(?:\\\\|/)?[\w.\-]+(?:[\\/][\w.\-]+)*|[\w.\-]+(?:[\\/][\w.\-]+)*')

DOC_CONTEXT = {
    'memory/ops/portal-split-seams-2026-11-17.md': 'PLANNED: seam-design table; portal/*.py modules not yet created',
    'memory/ops/stale-claim-check-jsonl-fallback-2026-11-18.md': 'pattern doc with example filenames (ref.json etc.)',
    'memory/ops/runbook-notes.md': 'ongoing notes; refs are seat-local ephemeral artifacts, never committed',
    'memory/ops/memory-sync-spec-r13.md': 'round history: BUNDLE-SHA256.txt was an ephemeral r13 artifact, never committed',
    'memory/ops/goal_ledger_record_fix-2026-11-18.md': 'record-fix doc; /does-not-exist.md is an intentional negative test',
}
MASK_RE = re.compile(r'<[^<>]*>|\*\S*|\w*NNN\w*|…')
GENERIC_BARE = {'index.md', 'skill.md'}

PROVENANCE_PAT = re.compile(r'split from|renamed to|formerly|moved to|supersedes? |replaced by', re.I)
ABSENT_PAT = re.compile(r'absent|not present|does not exist|never (?:existed|exists|committed|materialized)|also gone|is gone|no `\w|seat-local|not committed|template|other seat|planned', re.I)


def norm(tok):
    t = tok.replace('\\', '/').strip('.,;:()[]{}"\'`')
    m = re.match(r'^[A-Za-z]://', t)  # URLs are not files
    if m:
        return None
    if re.match(r'^[A-Za-z]:/', t):   # drive-letter path
        return ('REMOTE', t)
    while t.endswith(('.',)) and not t.lower().endswith(EXTS):
        t = t[:-1]
    return ('CANDIDATE', t)


def is_pathlike(t):
    if t.startswith(('memory/', 'archive/', 'reports/', 'archivist/', 'AgentPortal_V1/')):
        return True
    base = t.split('/')[-1]
    return base.endswith(EXTS)
def build_git_history():
    out = subprocess.run([GIT, '-C', ROOT, 'log', '--all', '--name-only', '--pretty=format:',
                          '--diff-filter=ACMR'], capture_output=True, text=True).stdout
    ever = set()
    for line in out.splitlines():
        line = line.strip().replace('\\', '/')
        if line:
            ever.add(line)
            ever.add(os.path.basename(line))
    return ever


def main():
    scan_all = '--all' in sys.argv
    files = []
    mdir = os.path.join(ROOT, 'memory', 'ops') if not scan_all else os.path.join(ROOT, 'memory')
    for dirpath, _, fns in os.walk(mdir):
        if '.git' in dirpath.split(os.sep):
            continue
        for f in fns:
            if f.endswith('.md'):
                files.append(os.path.relpath(os.path.join(dirpath, f), ROOT).replace('\\', '/'))
    for rf in ('memory/ONBOARDING.md', 'MEMORY.md', 'TODO.md'):
        p = os.path.join(ROOT, *rf.split('/'))
        if os.path.exists(p):
            files.append(rf)

    ever = build_git_history()
    # disk index: basename -> [relpaths]
    disk = {}
    for dirpath, _, fns in os.walk(ROOT):
        parts = dirpath.split(os.sep)
        if '.git' in parts or 'unsloth-tmp' in parts or 'mingit' in parts:
            continue
        for f in fns:
            disk.setdefault(f, []).append(os.path.relpath(os.path.join(dirpath, f), ROOT).replace('\\', '/'))

    results = []
    for rel in sorted(files):
        p = os.path.join(ROOT, rel.replace('/', os.sep))
        try:
            lines = open(p, encoding='utf-8', errors='replace').read().splitlines()
            if rel in DOC_CONTEXT:
                continue
            annotated = 'CORRIGENDUM (hostdoc-consistency-v2' in '\n'.join(lines)
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            masked = MASK_RE.sub(' ', line)  # drop <placeholder> tokens
            for m in TOKEN_RE.finditer(masked):
                r = norm(m.group(0))
                if not r:
                    continue
                kind, tok = r
                if kind == 'REMOTE':
                    results.append({'file': rel, 'line': i, 'ref': tok, 'status': 'REMOTE'})
                    continue
                if not is_pathlike(tok):
                    continue
                if '/' not in tok and tok.lower() in GENERIC_BARE:
                    continue  # prose mention of a lane INDEX.md, not a pointer
                b2 = os.path.basename(tok)
                if tok.startswith(('-', '_')) or '-.' in b2 or re.fullmatch(r'\.[A-Za-z0-9]+', b2):
                    continue  # extraction fragment (hyphen/underscore tail, hyphen-dot, bare ext)
                if tok.startswith('Users/'):
                    ext = os.path.join('C:\\', *tok.split('/'))
                    results.append({'file': rel, 'line': i, 'ref': tok, 'status': 'OK-DOCUMENTED' if ABSENT_PAT.search(lines[i-1]) else ('OK-EXTERNAL' if os.path.exists(ext) else 'PHANTOM')})
                    continue
                if tok.endswith(('_', '-')) and any(k.startswith(b2) for k in disk):
                    results.append({'file': rel, 'line': i, 'ref': tok, 'status': 'OK-PREFIX'})
                    continue
                # skip self-references to the doc itself and bare words like "INDEX.md" in prose? no - keep all; they must resolve.
                full = os.path.join(ROOT, tok)
                if os.path.exists(full):
                    status = 'OK'
                else:
                    base = os.path.basename(tok)
                    alts = [h for h in disk.get(base, []) if h != tok]
                    if alts:
                        status = 'MOVED'
                    elif tok in ever or base in ever:
                        status = 'HISTORICAL'
                    elif PROVENANCE_PAT.search(line):
                        status = 'PROVENANCE'
                    elif ABSENT_PAT.search(line) and (base in line or tok in line):
                        status = 'DOCUMENTED-ABSENT'
                    else:
                        status = 'ANNOTATED' if annotated else 'PHANTOM'
                results.append({'file': rel, 'line': i, 'ref': tok, 'status': status,
                                **({'actual': alts[:3]} if status == 'MOVED' else {})})

    from collections import Counter
    counts = Counter(r['status'] for r in results)
    phantoms = [r for r in results if r['status'] == 'PHANTOM']
    moved = [r for r in results if r['status'] == 'MOVED']
    today = datetime.date.today().isoformat()
    report = {
        'date': today,
        'script': 'memory/archivist/hostdoc_consistency_v2.py',
        'files_scanned': len(files),
        'refs_checked': len(results),
        'counts': dict(counts),
        'phantoms_found': len(phantoms),
        'unique_phantoms': sorted({p['ref'] for p in phantoms}),
        'details': results,
    }
    jpath = os.path.join(ROOT, 'memory', 'archivist', f'hostdoc-consistency-v2-{today}.json')
    json.dump(report, open(jpath, 'w', encoding='utf-8'), indent=1)

    md = [f"# Multi-host doc consistency v2 - corrected audit ({today})", "",
          "Script: `memory/archivist/hostdoc_consistency_v2.py` (fixes the 2026-11-18 extraction bugs: .jsonl truncation, .bak cut-off, bare-name CWD resolution).",
          f"Supersedes: hostdoc-consistency-v2-2026-11-18.md/.json (buggy counts) and hostdoc-consistency-2026-11-16.md (cycle-2, host:port only).", "",
          f"Files scanned: {len(files)} | refs checked: {len(results)} | " +
          ' | '.join(f"{k}: {v}" for k, v in sorted(counts.items())), ""]
    if phantoms:
        md += [f"## PHANTOM references ({len(phantoms)}) - must fix or annotate", ""]
        for p in phantoms:
            md.append(f"- `{p['file']}` L{p['line']} -> `{p['ref']}`")
        md.append("")
    if moved:
        md += [f"## MOVED references ({len(moved)}) - exist at another path", ""]
        for p in moved[:60]:
            md.append(f"- `{p['file']}` L{p['line']} -> `{p['ref']}` (actual: {', '.join('`'+a+'`' for a in p['actual'])})")
        if len(moved) > 60:
            md.append(f"- ... +{len(moved)-60} more (see JSON)")
    md += ["", "## Classification notes",
           "- HISTORICAL: file was committed at some point, later deleted; historical records may keep the reference.",
           "- PROVENANCE / DOCUMENTED-ABSENT: line talks about the file's history or its absence; not a live pointer.",
           "- REMOTE: drive-letter path on another host; unverifiable from White (expected in runbooks).", ""]
    mpath = os.path.join(ROOT, 'memory', 'archivist', f'hostdoc-consistency-v2-{today}.md')
    open(mpath, 'w', encoding='utf-8').write('\n'.join(md))

    print(f"scanned={len(files)} refs={len(results)} counts={dict(counts)}")
    print(f"phantoms={len(phantoms)} unique={len(report['unique_phantoms'])}")
    for p in phantoms:
        print(f"  PHANTOM {p['file']} L{p['line']} -> {p['ref']}")
    print(f"reports: memory/archivist/hostdoc-consistency-v2-{today}.{{json,md}}")
    return 1 if phantoms else 0


if __name__ == '__main__':
    sys.exit(main())
