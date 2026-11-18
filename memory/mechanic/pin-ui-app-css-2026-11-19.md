# Pin Added: ui/app.css (2026-11-19, Mechanic assisting Designer)

**Problem:** Designer CSS edits (line-height tokenizations, design tokens) were reverted on every mirror cycle by an external sync process pulling stale White copy over the sandbox edit.

**Fix:** Added `ui/app.css` to PIN_FILES in memory_mirror.py with sha12=ac3ef7ec2e35. Pin_guard will now detect and restore any unauthorized hash change, same as index.html.

**Designer workflow going forward:** When editing ui/app.css, advance the pin in the SAME turn:
1. Edit ui/app.css
2. Compute new sha12: `python -c "import hashlib; print(hashlib.sha1(open('ui/app.css','rb').read()).hexdigest()[:12])"`
3. Update PIN_FILES["ui/app.css"]["sha12"] in memory_mirror.py to the new hash
4. Copy file to backup path: `copy ui\app.css memory\designer\app_css_CANONICAL_<new_sha12>_YYYY-MM-DDx.css`

**Evidence:** memory_mirror.py compiles clean (py_compile OK). PIN_FILES now has 2 entries: index.html + ui/app.css.
