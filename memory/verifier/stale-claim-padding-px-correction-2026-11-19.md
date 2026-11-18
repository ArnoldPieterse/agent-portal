# Stale Claim Correction: "0 hardcoded px remain in app.css"

Date: 2026-11-19
Verifier: Verifier (auto-loop pass)
Severity: LOW (progress note, not acceptance-test blocker)

## Finding

HOT NOTES entry states: "Designer Goal #2 (Information Density Pass) complete: all padding/margin tokenized, 0 hardcoded px remain in app.css."

**This is INCORRECT.** Precise parse of ui/app.css (semicolon-split declarations, filtering only padding*/margin* properties, stripping var() before checking for px) yields exactly **4 hardcoded px values**:

| Line | Property | Value | Context |
|------|----------|-------|---------|
| 266  | padding  | `var(--sp-1) 5px` | `code` element (micro-spacing) |
| 269  | margin-right | `5px` | (inline micro-gap) |
| 295  | padding  | `var(--sp-1) 7px` | `.ft-chip` tooltip chip |
| 492  | padding  | `var(--sp-2) 0 var(--sp-2) 78px` | `.hl-chips` layout offset |

## Corroborating Source

Orchestrator's progress note on Goal 1 (same pass) already identified these exact 4 values:
> "Remaining hardcoded px = 4 deliberate values only: L266/L269 (5px micro), L295 (7px micro), L492 (78px layout offset)."

Builder's assist note on Goal 2 claiming "grep shows 0 remaining hardcoded px in padding/margin props" is the stale claim — likely a grep that matched whole lines rather than isolating individual declarations (multi-declaration lines contain border:1px which inflates or deflates counts depending on pattern).

## Impact

- Goal 1 acceptance test (hex colors = 0) is UNAFFECTED and still PASS.
- Goal 2 acceptance test (before/after screenshots) requires a browser regardless; the 4 px values do not block it.
- These 4 values are micro-spacing or layout offsets that may be intentionally non-tokenized. Orchestrator's note calls them "deliberate."

## Recommendation

1. Correct the HOT NOTES entry to say "4 deliberate hardcoded px remain (micro/layout offsets); all other padding/margin tokenized."
2. If full tokenization is desired, add --sp-5 and --sp-7 tokens; 78px is a layout offset best left as-is or given a named token like --hl-offset.

## Reproduction

```python
import re
content = open('ui/app.css').read()
for i, line in enumerate(content.split('\n'), 1):
    for d in line.split(';'):
        m = re.match(r'^(padding|margin)(-(top|right|bottom|left))?\s*:\s*(.+)$', d.strip())
        if m:
            cleaned = re.sub(r'var\([^)]*\)', '', m.group(4))
            if re.findall(r'\d+px', cleaned):
                print(f"L{i} {m.group(1)}: {re.findall(r'\\d+px', cleaned)}")
```
Output: 4 lines (L266, L269, L295, L492).
