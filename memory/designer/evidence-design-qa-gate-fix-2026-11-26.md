# Evidence: design_qa.py gate was CRASHED; fixed + re-ran 2026-11-26

## What was wrong (concrete)
`python memory/designer/design_qa.py` did not run at all on this host. It opened
every `ui/*.css` and `ui/*.js` with a bare `open(...)` -> Python used the platform
**cp1252** codec. Two JS files contain the UTF-8 hourglass glyph U+23F3
(`\xe2\x8f\xb3`) inside loading strings:
- `ui/core.js` @ byte 25369 (`loading '+esc(h.loading.model||"?")+'`)
- `ui/fleet_topology.js` @ byte 4242

Result: `UnicodeDecodeError: 'charmap' codec can't decode byte 0x8f ... position 25369`.
The gate died before emitting a single check, so design-QA coverage was silently zero.

## Fix (design_qa.py)
Added one helper and routed all 7 file reads through it:
```python
def _read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()
```
Replaced every `open(os.path.join(UI_DIR, ...)).read()` -> `_read(...)`. No logic
or threshold changes; only the I/O codec was corrected.

## Verification (this pass)
Ran `python memory/designer/design_qa.py` -> exit 1 (NOT a crash). Output:
`RESULT: 6 passed, 6 failed / 12 total`. The gate now executes all 12 checks and
reports real results instead of dying.

## Surfaced drift (NEW - first time visible since the gate could not run)
These are genuine static-design-system violations now that the gate runs. Not fixed
this pass (several are judgment-carrying / regression-risky; flagged for a focused pass):
1. Typography off-scale in app.css: `10px`, `11px` (canonical scale = 12/14/15/18/24)
2. tokens.css defines orphaned `--fs-11`, `--fs-13`, `--fs-16` (not on canonical scale)
3. Spacing: 13 off-scale `gap:` values (e.g. 3px, 6px, 18px)
4. Interaction: 17 ad-hoc `:hover` rules in app.css (should be centralized)
5. Typography: no `75ch` max-width rule present
6. Visual: 4 un-tokenized hex colors in app.css: #d9a441, #d05656, #7fb3ff, #4caf7d

## Side note (no action taken)
`memory/designer/_edge_profile/` (248 files / 6.5MB) is NOT junk - it is the CDP
browser-gate profile referenced by memory/ops/browser-acceptance-workaround.md and
memory/ops/browser-gate-decision-tree.md. Left in place deliberately.

Artifact: memory/designer/design_qa.py (patched). Runbook: re-run gate after any ui/* edit.
