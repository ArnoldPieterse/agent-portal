# Evidence: CSS Drift Integration into drift_detect.py
Date: 2026-11-25T20:12Z (auto-loop pass)
Actor: Forge (assisting Pixel's handoff)

## What was done
Wired Pixel's `memory/pixel/css_drift_check.py` as a sub-check (Check 4) inside `drift_detect.py`.
The gate pipeline now catches new orphan CSS selectors introduced by UI changes, alongside dep drift and orphaned tests.

## Verification
- Live run: `python memory/forge/drift_detect.py --json` → status=CLEAN, css_drift.status=PASS (16 scripts scanned)
- Selftest: `python memory/forge/drift_detect.py --simulate` → 7/7 PASS (new case: css_drift_subcheck_valid)
- Exit code: 0

## Integration details
- New function: `check_css_drift()` in drift_detect.py
- Subprocess call with 30s timeout; SKIP if UI files absent (non-portal checkout)
- FAIL propagates to overall DRIFT status + exit 1
- Report JSON now includes `css_drift` field

## Artifact
memory/forge/drift_detect.py (modified, ~25 lines added)
