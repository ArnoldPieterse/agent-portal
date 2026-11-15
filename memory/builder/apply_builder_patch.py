#!/usr/bin/env python3
"""apply_builder_patch.py — Builder clobber-proof patches (2026-11-15).

WHY A SCRIPT: the White->shared mirror overwrites newer shared writes and
preserves source mtimes, so direct edits to index.html / agent_portal.py in
the shared tree are reverted within ~5 min. Idempotent scripts under memory/
survive; run this on WHITE before restarting the portal (after Designer's
memory/designer/goals-patch-apply-2026-11-15.py — anchors are independent,
order does not matter).

Usage:  python apply_builder_patch.py [target_root]     # default: cwd

Hunks:
  B1  index.html       H1 .frow collision: scope the dialog form-row rule to
                       `dialog .frow` so Fleet rows keep only L120 padding/border.
  B2  agent_portal.py  register GET /api/provenance (after the /api/ops route).
  B3  agent_portal.py  add _provenance_report_path() + _provenance_snapshot()
                       serving memory/archivist/goal_provenance_report.json
                       (Archivist's provenance audit; regenerate via
                       memory/archivist/goal_provenance.py if stale).

Idempotency: hunk skipped when `new` already present and `old` absent;
fails loudly when neither is found or when `old` is ambiguous (>1 hit).
Self-verify: re-reads both files post-apply, asserts markers, py_compiles the portal.
"""
import os, py_compile, sys, time

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())
INDEX = os.path.join(ROOT, "index.html")
PORTAL = os.path.join(ROOT, "agent_portal.py")

HUNKS = [
    # (file, label, old, new)
    (INDEX, "B1 frow-scope", 
     ".frow{display:flex;gap:10px}.frow>div{flex:1}",
     "dialog .frow{display:flex;gap:10px}dialog .frow>div{flex:1}"),
    (PORTAL, "B2 provenance-route",
     '        elif p == "/api/ops":\n            # Ops panel host tiles (2026-11-15): disk usage + portal uptime.\n            return self._json(200, _ops_snapshot())',
     '        elif p == "/api/ops":\n            # Ops panel host tiles (2026-11-15): disk usage + portal uptime.\n            return self._json(200, _ops_snapshot())\n'
     '        elif p == "/api/provenance":\n            # Provenance audit (2026-11-15): serves Archivist goal-provenance report.\n            return self._json(200, _provenance_snapshot())'),
    (PORTAL, "B3 provenance-helpers",
     "def _git_status():",
     'def _provenance_report_path():\n'
     '    for c in ("memory/archivist/goal_provenance_report.json",\n'
     '              "memory/archivist/goal_provenance.json"):\n'
     '        if os.path.exists(c):\n'
     '            return c\n'
     '    return None\n'
     '\n\n'
     'def _provenance_snapshot():\n'
     '    # Provenance audit (2026-11-15): serve Archivist report verbatim + source/mtime.\n'
     '    path = _provenance_report_path()\n'
     '    if not path:\n'
     '        return {"available": False, "error": "no provenance report in memory/archivist/ (run goal_provenance.py)"}\n'
     '    try:\n'
     '        st = os.stat(path)\n'
     '        with open(path, encoding="utf-8") as f:\n'
     '            data = json.load(f)\n'
     '        return {"available": True, "source": path.replace("\\\\", "/"),\n'
     '                "mtime": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(st.st_mtime)),\n'
     '                "data": data}\n'
     '    except Exception as e:\n'
     '        return {"available": False, "error": str(e)}\n'
     '\n\n'
     'def _git_status():'),
]

VERIFY = [
    (INDEX,  ["dialog .frow{display:flex"]),
    (PORTAL, ['/api/provenance', 'def _provenance_snapshot():']),
]

def main():
    for path in (INDEX, PORTAL):
        if not os.path.exists(path):
            sys.exit(f"FATAL: {path} not found")
    applied = skipped = 0
    for path, label, old, new in HUNKS:
        text = open(path, encoding="utf-8").read()
        n_old = text.count(old)
        if old in text and n_old == 1:
            bak = path + ".bak-builder-" + time.strftime("%H%M%S")
            shutil_copy(path, bak)
            open(path, "w", encoding="utf-8", newline="").write(text.replace(old, new, 1))
            print(f"APPLIED  {label} ({path})")
            applied += 1
        elif old in text:
            sys.exit(f"FATAL: {label}: `old` ambiguous ({n_old} hits) in {path}")
        elif new in text:
            print(f"SKIPPED  {label} (already present)")
            skipped += 1
        else:
            sys.exit(f"FATAL: {label}: neither old nor new found in {path} — baseline drifted")
    # self-verify
    for path, markers in VERIFY:
        text = open(path, encoding="utf-8").read()
        for m in markers:
            if m not in text:
                sys.exit(f"FATAL verify: {m!r} missing from {path}")
    py_compile.compile(PORTAL, doraise=True)
    print(f"OK: {applied} applied, {skipped} skipped; markers verified; agent_portal.py compiles.")

def shutil_copy(src, dst):
    import shutil
    if not os.path.exists(dst):
        shutil.copy2(src, dst)

if __name__ == "__main__":
    main()
