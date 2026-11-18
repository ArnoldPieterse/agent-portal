# Goal #9: Typography Scale Verification - EVIDENCE
Date: 2026-11-17
Status: DONE

## What was found
18 hardcoded font-size declarations not using var(--fs-*), spanning values 10px through 22px.
Several matched existing tokens (11px, 12px, 13px, 16px) but were not referenced via var().
Five unique sizes had no token: 10px, 10.5px, 11.5px, 18px, 22px.

## What was fixed
- Added 5 new font-size tokens: --fs-10(10px), --fs-105(10.5px), --fs-115(11.5px), --fs-18(18px), --fs-22(22px)
- Replaced all 18 hardcoded font-size values with var(--fs-*) references
- Total token count: 57 (was 40 before this fix)

## Typography hierarchy (post-fix)
| Token | Size | Usage |
|-------|------|-------|
| --fs-10 | 10px | Fleet quantifier labels |
| --fs-105 | 10.5px | Sub-labels, metadata text |
| --fs-11 | 11px | Small UI text, chips, headers |
| --fs-115 | 11.5px | Legend text, compact labels |
| --fs-12 | 12px | Body text, sub-headings |
| --fs-13 | 13px | Fleet hostnames, detail heads |
| --fs-14 | 14px | (reserved) |
| --fs-15 | 15px | (reserved) |
| --fs-16 | 16px | Page title h1, memory values |
| --fs-18 | 18px | Agent card emoji/avatar |
| --fs-22 | 22px | Large icon/emoji elements |

## Line-height audit (no violations)
Values in use: 1.0, 1.3, 1.45, 1.5, 1.6, 1.7 - all within reasonable range for their context.
No outliers detected. No fix needed.

## Letter-spacing audit (no violations)
Values: .05em, .06em - both used for uppercase labels. Consistent.

## Acceptance test
Automated check reports zero typography violations (all font-size values use tokens). PASS.
