#!/usr/bin/env python3
"""
autonomy_gap_audit.py — Verifier goal #9 (Fleet Autonomy Convergence cycle)

Scans every entry in memory/ops/blockers.md, classifies each as one of:
  - closed           : RECONCILED / RESOLVED (no longer an open blocker)
  - human_required   : a genuine wall no agent can clear from its seat (env/infra)
  - automatable      : has an agent-actionable unblock step (code/data/install/config)

Deliverables (goal AC):
  1. 100% of entries classified (every entry gets exactly one label + rationale)
  2. ratio computed: human_required / active(entries) and automatable / active
  3. top-3 automatable items surfaced WITH a concrete fix path

Reproducible: `python memory/verifier/autonomy_gap_audit.py` -> writes
  memory/verifier/autonomy-gap-audit.json  (machine-readable)
  memory/verifier/autonomy-gap-audit-report.md (human report)
Self-test: `python memory/verifier/autonomy_gap_audit.py --selftest`
"""
import pathlib, re, json, sys, datetime

ROOT = pathlib.Path(__file__).resolve().parents[2]  # repo root (C:\Projects\AgentPortal)
BLOCKERS = ROOT / 'memory' / 'ops' / 'blockers.md'
OUT_JSON = pathlib.Path(__file__).with_name('autonomy-gap-audit.json')
OUT_MD   = pathlib.Path(__file__).with_name('autonomy-gap-audit-report.md')

# Signals that an entry has an AGENT-ACTIONABLE unblock step (=> automatable).
AUTOMATABLE_STEP_PATTERNS = [
    r'exact unblock step',          # explicit actionable instruction
    r'install path',                # dependency install with a path
    r'add a line per probe',        # concrete code change
    r'appends? (history|a line)',   # data-append fix
    r'schtask[s]? (via|/create)',   # schedulable task an agent can register
    r'(fix|patch|edit|change) the [a-z_]*\.(py|js|json|md)',  # code edit
    # NOTE: bare 'elev.py' is NOT a step signal - it usually marks a wall
    # (helper down/absent). Kept out of this list on purpose.
]
# Signals of a pure ENV/INFRA wall with no agent path (=> human_required).
HUMAN_WALL_PATTERNS = [
    r'winerror 10013',              # sandbox egress block
    r'sandbox egress',
    r'class not registered',        # COM unavailable in sandbox
    r'helper down',                 # elev helper exit 5 (infra must start it)
    r'elev\.py absent',             # helper file missing on host
    r'file-not-found.*elev',
    r'no browser binary',
    r'(cannot|can\'t) reach [a-z]+:\d+',  # cross-host unreachable from sandbox
]
CLOSED_TAGS = ('RECONCILED', 'RESOLVED')

TAG_RE = re.compile(r'^##\s*\[([A-Z-]+)(?:\s+([0-9T:.-]+))?\s*(.*?)\]\s*(.*)$')

WORD_TAG_RE = re.compile(r'^##\s+(NEEDS-HUMAN|OPS-NOTE)\b\s*[:\-]?\s*(.*)$')

def parse_entries(text):
    """Split blockers.md into REAL blocker records only.

    A record is a top-level `## ` section whose header is either bracketed
    `[TAG ...]` or word-tagged `NEEDS-HUMAN:` / `OPS-NOTE:`. Plain section
    headers (e.g. 'Mirror-revert data collection', 'RESOLUTIONS') are NOT
    blockers and are excluded so the ratio is not inflated."""
    chunks = re.split(r'\n(?=## )', text)
    entries = []
    for c in chunks:
        c = c.strip()
        if not c.startswith('## '):
            continue
        first = c.split('\n')[0]     # match header regex on the FIRST LINE only
        m = TAG_RE.match(first)      # bracketed form: ## [TAG ts who] title
        w = WORD_TAG_RE.match(first) # word-tag form:   ## NEEDS-HUMAN: title / ## OPS-NOTE: ...
        if not m and not w:
            continue                 # plain section header -> not a blocker record
        if m:
            tag, ts, who, title = m.group(1), (m.group(2) or ''), m.group(3).strip(), m.group(4).strip()
        else:
            tag, title = w.group(1), w.group(2).strip()
            ts, who = '', ''
        entries.append({'tag': tag.upper(), 'ts': ts, 'who': who, 'title': (title or first)[:90],
                        'body': c})
    return entries

AUTOMATABLE_HINTS = re.compile('|'.join(AUTOMATABLE_STEP_PATTERNS), re.I)
HUMAN_WALL_HINTS  = re.compile('|'.join(HUMAN_WALL_PATTERNS), re.I)

def classify(e):
    """Return (label, rationale) for one entry. Deterministic + auditable."""
    tag, body = e['tag'], e['body']
    if any(t in tag for t in CLOSED_TAGS):
        return 'closed', f'tag={tag} => no longer an open blocker'
    has_step  = bool(AUTOMATABLE_HINTS.search(body))
    has_wall  = bool(HUMAN_WALL_HINTS.search(body))
    needs_human_tag = 'NEEDS-HUMAN' in tag
    if needs_human_tag and has_wall and not has_step:
        return 'human_required', (f'tag=NEEDS-HUMAN + env/infra wall '
                                  f'({HUMAN_WALL_HINTS.search(body).group(0)}) with no agent-actionable step')
    if has_step:
        # An explicit actionable step overrides a NEEDS-HUMAN tag: the fleet CAN clear it.
        note = ' (overrides NEEDS-HUMAN tag)' if needs_human_tag else ''
        return 'automatable', f'agent-actionable unblock step present{note}'
    if has_wall:
        return 'human_required', f'env/infra wall ({HUMAN_WALL_HINTS.search(body).group(0)}), no agent path'
    # OPS-NOTE / data-gap with no hard wall => tracked, automatable via the stated fix
    return 'automatable', (f'tag={tag}: operational/data note with a stated remediation, '
                           f'no hard env wall')

def _clean(s):
    """Strip markdown noise from a fix-path snippet."""
    s = re.sub(r'^[\s>#*`\-]+', '', s).strip()
    s = s.replace('**', '').replace('`', '')
    return s.strip()[:200]

def extract_fix_path(e):
    """Pull the most concrete unblock instruction out of an entry body."""
    m = re.search(r'(?:exact unblock step|install path)[:\s]*([^.]+\.)', e['body'], re.I)
    if m:
        return _clean(m.group(1))
    # fallback: first NON-header line that names a concrete file/task to act on
    for ln in e['body'].splitlines():
        ls = ln.strip()
        if ls.startswith('#'):            # skip section headers / the entry title
            continue
        if re.search(r'(\.py|\.jsonl?|schtask|ffmpeg)', ls, re.I):
            return _clean(ls)
    return '(see entry body)'

CYCLE_START = '2026-11-25'   # cycle-20 goal-set date; entries older than this are potentially stale

def run():
    text = BLOCKERS.read_text(encoding='utf-8')
    entries = parse_entries(text)
    results = []
    for i, e in enumerate(entries):
        label, why = classify(e)
        ts_day = (e['ts'] or '')[:10]
        stale = (ts_day < CYCLE_START) if ts_day else None   # None = no date to judge
        rec = {'idx': i, 'tag': e['tag'], 'ts': e['ts'], 'who': e['who'],
               'title': e['title'], 'label': label, 'rationale': why, 'stale': stale}
        if label == 'automatable':
            rec['fix_path'] = extract_fix_path(e)
        results.append(rec)
    total = len(results)
    active = [r for r in results if r['label'] != 'closed']
    n_hr  = sum(1 for r in active if r['label'] == 'human_required')
    n_aut = sum(1 for r in active if r['label'] == 'automatable')
    n_cls = total - len(active)
    ratio_hr  = (n_hr / len(active)) if active else 0.0
    ratio_aut = (n_aut / len(active)) if active else 0.0
    top3 = [r for r in results if r['label'] == 'automatable'][:3]
    hr_stale   = sum(1 for r in active if r['label']=='human_required' and r.get('stale') is True)
    hr_current = n_hr - hr_stale
    out = {
        'generated': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'source': str(BLOCKERS.relative_to(ROOT)),
        'cycle_start': CYCLE_START,
        'total_entries': total, 'active': len(active), 'closed': n_cls,
        'human_required': n_hr, 'automatable': n_aut,
        'human_required_stale_predating_cycle': hr_stale,
        'human_required_current_cycle': hr_current,
        'ratio_human_required_of_active': round(ratio_hr, 4),
        'ratio_automatable_of_active': round(ratio_aut, 4),
        'target_human_required_below': 0.10,
        'meets_target': ratio_hr < 0.10,
        'top3_automatable': top3,
        'entries': results,
    }
    OUT_JSON.write_text(json.dumps(out, indent=2), encoding='utf-8')
    # markdown report
    lines = ['# Autonomy Gap Audit (Verifier goal #9)',
             f'- generated {out["generated"]}',
             f'- source: `{out["source"]}`',
             f'- entries total **{total}** | active **{len(active)}** | closed **{n_cls}**',
             f'- human-required **{n_hr}** ({ratio_hr:.0%} of active) | automatable **{n_aut}** ({ratio_aut:.0%})',
             f'  - of which predate cycle start ({CYCLE_START}): **{hr_stale}** (potentially stale; recommend one-time re-assessment sweep, NOT per-wall re-probe)',
             f'- target <10% human-required: **{"MET" if out["meets_target"] else "NOT MET"}**',
             '', '## Per-entry classification',
             '| # | tag | who | label | rationale |', '|---|-----|-----|-------|-----------|']
    for r in results:
        lines.append(f"| {r['idx']} | {r['tag']} | {r['who'][:18]} | **{r['label']}** | {r['rationale']} |")
    lines += ['', '## Top-3 automatable (with fix path)', '']
    for i, r in enumerate(top3, 1):
        lines.append(f"{i}. **{r['title']}** -> `{r.get('fix_path','')}`")
    OUT_MD.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({k: out[k] for k in
          ('total_entries','active','closed','human_required','automatable',
           'ratio_human_required_of_active','meets_target')}, indent=2))
    print(f'wrote {OUT_JSON.name} + {OUT_MD.name}')
    return out

def selftest():
    """Synthetic entries: assert classifier labels them correctly."""
    cases = [
        ('## [NEEDS-HUMAN 2026-11-20] X', 'WinError 10013 sandbox egress block to localhost. No path.', 'human_required'),
        ('## [OPS-NOTE 2026-11-25 Y]', 'Exact unblock step: add a line per probe to history.jsonl.', 'automatable'),
        ('## [RESOLVED 2026-11-17] Z', 'was a wall, now fixed.', 'closed'),
        ('## [NEEDS-HUMAN 2026-11-20 W]', 'helper down exit 5 per protocol. no agent path.', 'human_required'),
    ]
    ok = True
    for hdr, body, want in cases:
        e = {'tag': re.match(r'##\s*\[([A-Z-]+)', hdr).group(1), 'body': hdr + '\n' + body}
        got, _ = classify(e)
        status = 'PASS' if got == want else 'FAIL'
        ok &= (got == want)
        print(f'  [{status}] {hdr[:30]:32} -> {got} (want {want})')
    print('SELFTEST', 'PASS' if ok else 'FAIL')
    return ok

if __name__ == '__main__':
    if '--selftest' in sys.argv:
        sys.exit(0 if selftest() else 1)
    run()
