## Verification: "hardcoded hex outside :root" claim (2026-11-17)
Claim in hot notes: "27 unique hardcoded hex colors remain in active rules (lines 23–189)"
Actual state of ui/app.css (231 lines):
- All 35 unique hex values are inside :root token definition (lines 6-13) — correct placement.
- Lines 14-231: ZERO hardcoded hex; all rules use var(--token).
Verdict: Claim was FALSE. The remaining-work item "fix hardcoded hex outside :root" is already DONE.
Evidence: python regex scan of ui/app.css, 0 matches for #[0-9a-fA-F](3, 8) after line 13.
