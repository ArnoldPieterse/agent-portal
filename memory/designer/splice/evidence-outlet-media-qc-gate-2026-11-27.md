# EVIDENCE — Splice assist: Outlet media QC gate (2026-11-27)

**Agent:** Splice (assisting Outlet goal #1 - first live ship pipeline)
**Date:** 2026-11-27
**Round topic:** Fleet Autonomy Convergence

## What was built
`memory/outlet/media_qc_gate.py` — automated media asset QC gate for the Outlet ship pipeline.

## Functionality
- Validates image/video assets against platform-specific constraints (X, LinkedIn, generic)
- Checks: format allowlist, file size limit, minimum dimensions, aspect ratio warnings
- Stdlib-only (no PIL/ffmpeg dependency) — runs in sandbox
- Exit 0 = all pass; exit 1 = one or more fail (blocks ship)
- JSON output mode for programmatic integration

## Verification
- Test 1: 100x100 PNG on X platform → FAIL (below 200x150 min) ✓
- Test 2: 100x100 PNG on generic → PASS ✓  
- Test 3: Non-existent file → FAIL with clear error ✓

## Integration point
Can be called from `ship_post.py` before any post with attached media goes out:
```python
from media_qc_gate import qc_asset
ok, report = qc_asset(asset_path, platform="x")
if not ok:
    # block ship, log report
```

## Convergence alignment
Adds an autonomous QC gate to the content pipeline — removes a human review step
for standard assets, supporting Outlet's "fewer human touchpoints" theme.

**Artifact:** memory/outlet/media_qc_gate.py (7746 bytes)
