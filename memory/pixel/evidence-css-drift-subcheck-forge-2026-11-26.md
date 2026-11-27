# css_drift_subcheck.py - Forge integration-ready module (2026-11-26)

## What
Drop-in CSS drift sub-check for Forge's `drift_detect.py` goal #2.
Exposes `run_css_drift_check() -> dict` returning `{new_orphans: set, total_classes: int, timestamp: str}`.

## Integration (3 lines in detect_drift())
```python
# Check 4: CSS orphan selectors (Pixel)
from memory.pixel.css_drift_subcheck import run_css_drift_check
css = run_css_drift_check()
if css['new_orphans']:
    report['detail'].append(f"CSS DRIFT: {', '.join(sorted(css['new_orphans']))}")
    has_drift = True
```

## Verified
- `python memory/pixel/css_drift_subcheck.py` → exit 0, "PASS: no new orphans (218 classes)"
- Import + call from project root → `new_orphans=0, total=218`, assert clean
- Shares baseline with existing `css_drift_check.py` (same `css_baseline.json`) — no duplicate state

## Files
- memory/pixel/css_drift_subcheck.py (the module, ~90 lines)
- memory/pixel/css_baseline.json (shared baseline, pre-existing)
