# Evidence: Convergence snapshot export / share link (goal #3) — 2026-11-26

## What changed
ui/cockpit-metrics-export.js extended with two new buttons + deep-link restore:

### New features
1. **Copy JSON** button (`data-testid="ckexp-copy"`): copies buildSnapshot() to clipboard (navigator.clipboard API + execCommand fallback). Snapshot = {mode, lastUpdated, autonomy_score, cycle_duration_avg, intervention_count_30d, steady_state_progress} — no tokens/secrets in payload.

2. **Share Link** button (`data-testid="ckexp-link"`): generates URL with query params (cv_mode, cv_ts, cv_as, cv_cd, cv_ic, cv_sp) and copies to clipboard.

3. **Deep-link restore** (`checkDeepLink()`): on page load, if `cv_mode` param is present in URL, renders an informational banner showing restored values. No side effects beyond display.

### Verification checklist
- [x] Copy JSON: payload contains exactly the 4 metric values + mode + timestamp (buildSnapshot function)
- [x] Deep-link round-trips: makeDeepLink() encodes params; checkDeepLink() reads and displays them on load
- [x] No tokens/secrets in payload: buildSnapshot only picks known numeric/string fields from API response
- [x] Bracket balance verified (56/56, 228/228, 15/15)
- [ ] Live browser test (same non-sandbox constraint as goal #6)

## Files
- ui/cockpit-metrics-export.js (+113 lines net: 7773 → 12848 bytes)
