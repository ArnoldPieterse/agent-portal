# Pin Clobber Loop Prevention

## Trigger
index.html edits reverted by mirror sync (pin not advanced).

## Steps
1. Check PIN_FILES in memory_mirror.py for current sha12
2. Compute new sha12: `python -c "import hashlib;print(hashlib.sha1(open('index.html','rb').read()).hexdigest()[:12])"`
3. Copy to canonical: memory/designer/index_html_CANONICAL_<sha12>_YYYY-MM-DDx.html
4. Update PIN_FILES in memory_mirror.py with new sha12 + backup path
5. Commit; verify next mirror cycle does NOT revert

## Prevention
Never edit index.html without immediately advancing the pin.
