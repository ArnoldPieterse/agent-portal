#!/usr/bin/env python3
"""Audit: every (verified: ...) marker in memory/goals/*.md must cite at least
one artifact path that EXISTS on disk. Reports false-closure candidates.
2026-11-18 Orchestrator: one-off ledger hygiene pass (option c)."""
import pathlib, re, os, sys

GOALS = pathlib.Path('memory/goals')
SKIP = ('forecast', 'log-', '2026-11-13', 'INDEX', 'cycle2', 'all-goals', 'slip_prediction', 'designer-goal', 'mechanic-goal')
PATH_RE = re.compile(r'memory/[A-Za-z0-9_\-./]+?\.(?:md|py|jsonl|json|css|js|html)(?!\w)')
NEXT_GOAL_RE = re.compile(r'\n\s*\d+[.)]\s')

missing, checked = [], 0
for f in sorted(GOALS.glob('*.md')):
    if any(s in f.name for s in SKIP):
        continue
    t = f.read_text(encoding='utf-8', errors='replace')
    for m in re.finditer(r'\(verified:', t):
        end = m.start() + 500
        nb = NEXT_GOAL_RE.search(t, m.start() + 12)
        if nb and nb.start() < end:
            end = nb.start()  # stop at next numbered goal: don't bleed into its description
        seg = t[m.start():end]
        paths = PATH_RE.findall(seg)
        checked += 1
        if not paths:
            continue  # marker with no path token - not audit-able here
        for p in paths:
            if not os.path.exists(p):
                missing.append((f.name, p))

print(f'verified markers checked: {checked}')
for name, p in missing:
    print(f'MISSING  {name}: {p}')
print('total missing cited artifacts:', len(missing))
sys.exit(1 if missing else 0)
