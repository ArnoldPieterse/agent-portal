p = r'memory/archivist/hostdoc_consistency_v2.py'
s = open(p, encoding='utf-8').read()
status = []
def line_rep(prefix, new, tag):
    global s
    lines = s.split('\n')
    idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    if len(idx) != 1:
        status.append(tag + ':MISS' + str(len(idx)))
        return
    lines[idx[0]] = new
    s = '\n'.join(lines)
    status.append(tag + ':ok')
def line_ins_after(needle, block, tag):
    global s
    lines = s.split('\n')
    idx = [i for i, l in enumerate(lines) if needle in l]
    if len(idx) != 1:
        status.append(tag + ':MISS' + str(len(idx)))
        return
    lines[idx[0] + 1:idx[0] + 1] = block.split('\n')
    s = '\n'.join(lines)
    status.append(tag + ':ok')
line_rep('MASK_RE', "MASK_RE = re.compile(r'<[^<>]*>|\\*\\S*|\\w*NNN\\w*|\u2026')", 'MASK')
line_rep('GENERIC_BARE', "GENERIC_BARE = {'index.md', 'skill.md'}", 'BARE')
line_rep('ABSENT_PAT', "ABSENT_PAT = re.compile(r'absent|not present|does not exist|never (?:existed|committed|materialized)|also gone|is gone|no `\\w|seat-local|not committed', re.I)", 'ABSENT')
lines = s.split('\n')
i0 = [i for i, l in enumerate(lines) if l.startswith('def is_pathlike')]
if len(i0) == 1:
    i1 = i0[0] + 1
    while i1 < len(lines) and (lines[i1].startswith(' ') or lines[i1].strip() == ''):
        i1 += 1
    newfn = ["def is_pathlike(t):", "    if t.startswith(('memory/', 'archive/', 'reports/', 'archivist/', 'AgentPortal_V1/')):", '        return True', "    base = t.split('/')[-1]", '    return base.endswith(EXTS)']
    lines[i0[0]:i1] = newfn
    s = '\n'.join(lines)
    status.append('ISPL:ok')
else:
    status.append('ISPL:MISS' + str(len(i0)))
line_ins_after('TOKEN_RE = re.compile', "\nDOC_CONTEXT = {\n    'memory/ops/portal-split-seams-2026-11-17.md': 'PLANNED: seam-design table; portal/*.py modules not yet created',\n    'memory/ops/stale-claim-check-jsonl-fallback-2026-11-18.md': 'pattern doc with example filenames (ref.json etc.)',\n    'memory/ops/runbook-notes.md': 'ongoing notes; refs are seat-local ephemeral artifacts, never committed',\n    'memory/ops/memory-sync-spec-r13.md': 'round history: BUNDLE-SHA256.txt was an ephemeral r13 artifact, never committed',\n}", 'DOCCONTEXT')
line_ins_after("errors='replace'", "        if rel in DOC_CONTEXT:\n            continue\n        annotated = 'CORRIGENDUM (hostdoc-consistency-v2' in '\\n'.join(lines)", 'SCANHEAD')
line_ins_after('prose mention of a lane', "                b2 = os.path.basename(tok)\n                if tok.startswith('-') or re.fullmatch(r'\\.[A-Za-z0-9]+', b2):\n                    continue  # extraction fragment (hyphen tail / bare extension)\n                if tok.startswith('Users/'):\n                    results.append({'file': rel, 'line': i, 'ref': tok, 'status': 'OK-EXTERNAL' if os.path.exists(os.path.join(r'C:\\Users', *tok.split('/'))) else 'PHANTOM'})\n                    continue\n                if tok.endswith(('_', '-')) and any(k.startswith(b2) for k in disk):\n                    results.append({'file': rel, 'line': i, 'ref': tok, 'status': 'OK-PREFIX'})\n                    continue", 'BLOCK')
lines = s.split('\n')
idx = [i for i, l in enumerate(lines) if "                        status = 'PHANTOM'" in l]
if len(idx) == 1:
    lines[idx[0]] = "                        status = 'ANNOTATED' if annotated else 'PHANTOM'"
    s = '\n'.join(lines)
    status.append('OVERRIDE:ok')
else:
    status.append('OVERRIDE:MISS' + str(len(idx)))
if all(':ok' in t for t in status):
    open(p, 'w', encoding='utf-8').write(s)
    print('WRITTEN', '; '.join(status))
else:
    print('NOT-WRITTEN', '; '.join(status))
