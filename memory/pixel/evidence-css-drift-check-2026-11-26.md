# CSS Drift Check - Forge Gate Pipeline Contribution (2026-11-26)

## What
`memory/pixel/css_drift_check.py` - baseline+delta CSS selector linter that detects
NEW unreferenced selectors (dead code drift) in ui/app.css after any UI change.

## How it works
1. First run: writes `memory/pixel/css_baseline.json` with all 218 current CSS classes
   (90 known orphans from dynamic class construction - pre-existing, not flagged).
2. Subsequent runs: compares current CSS class set against baseline + HTML/JS references.
   Only NEW unreferenced selectors trigger exit 1 (drift detected).
3. Informational: reports classes REMOVED since baseline (intentional cleanup = OK).

## Verification
- Ran second-pass logic inline: 218/218 classes match, 0 new orphans, PASS.
- Script is self-contained (stdlib only), 84 lines, no external deps.
- Exit codes: 0=pass, 1=new drift detected.

## Gate hook for Forge
Add to `drift_detect.py` as a sub-check triggered when `ui/app.css` is in the changed-files
set of any commit:
```python
# In drift_detect.py, after file-change detection:
if "ui/app.css" in changed_files:
    r = run(["python", "memory/pixel/css_drift_check.py"])
    if r.returncode != 0:
        flags.append("css-drift: new orphan selectors detected")
```

## Scope honesty
- Catches dead CSS from removed/renamed UI elements (the common drift mode).
- Does NOT catch: duplicate rules, specificity conflicts, unused media queries, or
  selector typos that never matched anything (those need a browser DOM check).
- The 90 baseline orphans are false positives from dynamic class construction
  (template literals, string concatenation) - acceptable for a drift detector
  since we only flag NEW additions.

## Files
- memory/pixel/css_drift_check.py (84L, executable gate script)
- memory/pixel/css_baseline.json (baseline snapshot, 218 classes + 90 known orphans)
