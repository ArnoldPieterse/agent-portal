#!/usr/bin/env python
"""
spf_staleness_monitor.py - Archivist | Fleet Autonomy Convergence (cycle-18+)

Extends the one-time Knowledge SPF audit (goal 9) into a LIVE detector.
The audit ranked agents by citation weight; this monitor finds the concrete
files that are BOTH load-bearing (cited by >=N distinct peer agents) AND going
stale - the actual vectors for cascading autonomy failure: a stale file that
many agents depend on silently degrades every dependent's decisions.

Output: memory/archivist/spf-staleness-report.json (+ --md narrative)
Exit 0 = ran clean (report written); exit 1 = fatal scan error.
"""
import json, re, sys, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]   # repo root (C:\Projects\AgentPortal)
MEM = ROOT / 'memory'
TODAY = dt.date(2026, 11, 25)
STALE_DAYS = 14        # a file older than this is 'stale' for convergence purposes
MIN_DEPENDENTS = 3     # cited by >=3 distinct peer agents => load-bearing
AGENT_DIRS = ['orchestrator','researcher','builder','archivist','verifier',
              'scribe','designer','mechanic','pixel','forge','outlet']

DATE_RE = re.compile(r'(20\d{2})-(\d{2})-(\d{2})')

def file_date(p: Path):
    """Best-effort last-updated date: header 'Last updated'/'Date', else filename, else mtime."""
    try:
        head = p.read_text(encoding='utf-8', errors='ignore')[:1200]
    except Exception:
        head = ''
    for label in ('Last updated', 'Updated', 'Date'):
        m = re.search(label + r'[^0-9]{0,6}(20\d{2}-\d{2}-\d{2})', head)
        if m:
            return _to_date(m.group(1)), 'header'
    m = DATE_RE.search(p.name)
    if m:
        return _to_date(f'{m.group(1)}-{m.group(2)}-{m.group(3)}'), 'filename'
    try:
        return dt.date.fromtimestamp(p.stat().st_mtime), 'mtime'
    except Exception:
        return TODAY, 'unknown'

def _to_date(s):
    y, mo, d = s.split('-')
    return dt.date(int(y), int(mo), int(d))

# A citation of agent B's file from agent A's file: a path token memory/<agent>/...
PATH_TOKEN = re.compile(r'memory[\\/]+([a-z_]+)[\\/]')
ATTRIB = re.compile(r'\b(?:assist|from|via|by)\s+@?([A-Za-z]+)', re.I)

def citing_agent_of(path: Path):
    """Which agent's lane does this file live in (the citer)."""
    parts = path.relative_to(MEM).parts
    if parts and parts[0] in AGENT_DIRS:
        return parts[0]
    return None

def main():
    md_files = list(MEM.rglob('*.md'))
    # per cited-file: set of distinct citing agents (peer, not self)
    dep_map = {}   # relpath -> {citing_agent}
    for f in md_files:
        citer = citing_agent_of(f)
        if citer is None:
            continue
        try:
            text = f.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        cited_agents = set()
        for m in PATH_TOKEN.finditer(text):
            a = m.group(1)
            if a in AGENT_DIRS and a != citer:
                cited_agents.add(a)
        for m in ATTRIB.finditer(text):
            a = m.group(1).lower()
            if a in AGENT_DIRS and a != citer:
                cited_agents.add(a)
    # We need file-level, not agent-level: re-scan to map each path token to its file
    file_deps = {}   # relpath(str) -> set(citing agents)
    for f in md_files:
        citer = citing_agent_of(f)
        if citer is None:
            continue
        try:
            text = f.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        for m in re.finditer(r'memory[\\/]+([a-z_]+)[\\/]([A-Za-z0-9_.\-/\\]+)', text):
            agent, name = m.group(1), m.group(2).strip('.,)')
            if agent not in AGENT_DIRS or agent == citer:
                continue
            target = MEM / agent / name
            if target.exists():
                rel = str(target.relative_to(MEM)).replace('\\', '/')
                file_deps.setdefault(rel, set()).add(citer)
    # Score each cited file
    rows = []
    for rel, agents in file_deps.items():
        p = MEM / rel.replace('/', Path.sep)
        if not p.exists():
            continue
        d, src = file_date(p)
        age = (TODAY - d).days
        n_dep = len(agents)
        stale = age > STALE_DAYS
        load_bearing = n_dep >= MIN_DEPENDENTS
        risk = 'CRITICAL' if (load_bearing and stale) else (
               'WATCH' if load_bearing else ('stale' if stale else 'ok'))
        rows.append({
            'file': rel, 'cited_by_agents': sorted(agents), 'dependents': n_dep,
            'last_updated': str(d), 'date_source': src, 'age_days': age,
            'stale': stale, 'load_bearing': load_bearing, 'risk': risk
        })
    rows.sort(key=lambda r: (r['risk'] != 'CRITICAL', -r['dependents'], -r['age_days']))
    critical = [r for r in rows if r['risk'] == 'CRITICAL']
    watch = [r for r in rows if r['risk'] == 'WATCH']
    report = {
        'generated': str(TODAY), 'stale_threshold_days': STALE_DAYS,
        'min_dependents': MIN_DEPENDENTS, 'files_scanned': len(md_files),
        'cited_files': len(rows), 'critical_count': len(critical),
        'watch_count': len(watch),
        'summary': (f'{len(critical)} load-bearing files are stale (> {STALE_DAYS}d, '
                    f'cited by >= {MIN_DEPENDENTS} peers) = cascading-autonomy risk; '
                    f'{len(watch)} load-bearing but fresh.'),
        'critical': critical[:40], 'watch': watch[:40]
    }
    out = MEM / 'archivist' / 'spf-staleness-report.json'
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'scanned={len(md_files)} cited_files={len(rows)} critical={len(critical)} watch={len(watch)}')
    print('report ->', out.relative_to(ROOT))
    if '--md' in sys.argv:
        write_md(report, MEM / 'archivist' / 'spf-staleness-report.md')
    return 0

def write_md(rep, path):
    L = ['# Staleness-Propagation Risk Monitor',
         f'**Date:** {rep["generated"]} | **Author:** Archivist | **Round:** Fleet Autonomy Convergence',
         '', 'Extends the one-time SPF audit (goal 9) into a live detector: it flags knowledge files that are',
         'both **load-bearing** (cited by >= %d distinct peer agents) and **stale** (> %d days old). A stale file many'
         % (rep['min_dependents'], rep['stale_threshold_days']),
         'agents depend on silently degrades every dependent\'s autonomous decisions - the core cascading-autonomy risk.',
         '', f'Scanned {rep["files_scanned"]} md files; {rep["cited_files"]} are cited by peers. **{rep["critical_count"]} CRITICAL**, {rep["watch_count"]} WATCH.',
         '', '## CRITICAL (load-bearing + stale)', '| file | dependents | last-updated | age(d) |', '|---|---|---|---|']
    for r in rep['critical']:
        L.append(f'| `{r["file"]}` | {r["dependents"]} | {r["last_updated"]} | {r["age_days"]} |')
    if not rep['critical']:
        L.append('| _none_ | - | - | - |')
    L += ['', '## WATCH (load-bearing, fresh)', '| file | dependents | last-updated | age(d) |', '|---|---|---|---|']
    for r in rep['watch'][:20]:
        L.append(f'| `{r["file"]}` | {r["dependents"]} | {r["last_updated"]} | {r["age_days"]} |')
    path.write_text('\n'.join(L), encoding='utf-8')

if __name__ == '__main__':
    sys.exit(main())
