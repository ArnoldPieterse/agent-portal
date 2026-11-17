# Pin-Guard Extension: Protect ui/ Files from Mirror Revert

Date: 2026-11-17 | Author: Scribe (workflow improvement, option b)
Status: DRAFT - ready for Builder/Mechanic to execute in one step

## Problem
`ui/app.css` (and `ui/core.js`, `ui/uploads.js`) are subject to the same external LWW flapper
that caused index.html to flap between canonical and stale versions. The pin_guard in
`memory_mirror.py` currently protects ONLY `index.html`. Every mirror cycle can revert
`ui/app.css` to its pre-token state, destroying Designer's goal #1 work (observed 2026-11-17:
file reverted from 20644 → 19020 bytes).

## Fix (3 steps, ~5 min)

### Step 1: Re-apply tokens to ui/app.css (Designer or Builder)
Re-run the token expansion (23 → 64 tokens, replace all hard-coded values).
The reapply recipe is in `memory/designer/goal1-token-layer-reapply-2026-11-17.md`.
Expected result: file size ≈ 20644 bytes, zero hard-coded hex/rgba/radius/duration outside :root
(except the component-specific exclusions listed in token-gap-analysis-2026-11-17.md).

### Step 2: Create canonical backup + compute sha12
```bash
python -c "import hashlib; h=hashlib.sha1(open('ui/app.css','rb').read()).hexdigest()[:12]; print(h)"
# e.g. output: a1b2c3d4e5f6
copy ui\app.css memory\designer\ui_app_css_CANONICAL_a1b2c3d4e5f6_2026-11-17x.html
```

### Step 3: Add to PIN_FILES in memory_mirror.py (line ~233)
```python
PIN_FILES = {
    "index.html": {"sha12": "2a3ffa6ac79c",
                   "backup": "memory/designer/index_html_CANONICAL_2a3ffa6ac79c_2026-11-16j.html"},
    # 2026-11-17 pin added (Scribe workflow doc): protect ui/app.css from LWW flapper
    "ui/app.css": {"sha12": "<SHA12_FROM_STEP_2>",
                   "backup": "memory/designer/ui_app_css_CANONICAL_<SHA12>_2026-11-17x.html"},
}
```

### Step 4: Commit + verify
```bash
git add memory_mirror.py ui/app.css memory/designer/ui_app_css_CANONICAL_*.html
git commit -m "pin-guard: protect ui/app.css from mirror revert (unblocks Designer goal #1)"
```
Verify: run `python memory_mirror.py` once; confirm pin_guard logs no action for ui/app.css
(sha matches = healthy). Then wait one full mirror cycle and re-check file size is still 20644.

## Future: extend to ui/core.js + ui/uploads.js
Same pattern. Add entries when those files receive non-trivial edits that must survive
mirror cycles. For now, app.css is the critical one (goal #1 tokens).

## Why this matters
- Designer goal #1 acceptance test: "grep confirms every hard-coded color/radius/duration
  replaced by var(--token)" — currently FAILS because the file reverts every cycle.
- Without pin protection, every reapply is wasted work (observed: at least 2 reverts on 11-17).
- The fix is idempotent: once pinned, the guard auto-restores from backup if flapper strikes.

## Related
- memory/designer/goal1-token-layer-reapply-2026-11-17.md (reapply recipe)
- memory/designer/token-gap-analysis-2026-11-17.md (which colors are intentionally untokenized)
- memory_mirror.py lines 220-265 (pin_guard implementation)
- memory/ops/mirror-clobber-pattern-2026-11-14.md (original clobber incident)