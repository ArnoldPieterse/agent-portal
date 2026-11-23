#!/usr/bin/env python3
"""Fleet-wide cognitive-load audit across all cockpit HTML surfaces.
   Designer assist 2026-11-24 | round topic: Closed-Loop Autonomy & Fleet Cockpit.
   Reuses ui/cockpit-load-audit.py::audit() and reports one line per surface + a rollup.
"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'ui'))
try:
    from cockpit_load_audit import audit  # type: ignore
except Exception:
    # fallback: load by file name without dash
    import importlib.util
    spec = importlib.util.spec_from_file_location('cla', Path(__file__).resolve().parents[2] / 'ui' / 'cockpit-load-audit.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); audit = m.audit

ROOT = Path(__file__).resolve().parents[2]
SURFACES = ['index.html', 'ui/cockpit-provenance.html', 'ui/cockpit-knowledge-impact.html']
rows, fails = [], 0
for s in SURFACES:
    p = ROOT / s
    if not p.exists():
        rows.append({'file': s, 'pass': None, 'note': 'missing'}); continue
    r = audit(str(p)); rows.append(r)
    if not r['pass']: fails += 1
report = {'surfaces': len(SURFACES), 'failed': fails,
          'rollup_pass': fails == 0,
          'rows': rows}
out = Path(__file__).with_name('cockpit-load-audit-fleet-2026-11-24.json')
out.write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
sys.exit(0 if report['rollup_pass'] else 1)
