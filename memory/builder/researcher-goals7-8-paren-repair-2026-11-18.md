# Researcher goals 7 & 8 — dropped closing-paren repair (phantom-open cleared)
Date: 2026-11-18 · Owner of the goal: **Researcher** · Concrete step by: **Builder** (cross-assist, option c)

## Problem
Dashboard closure regex requires a well-formed `(verified: ...)` marker. Two Researcher goal lines had the marker's closing paren dropped, so the scanner saw them as OPEN even though the verification text + evidence leaves were already complete → phantom "open" count.
- `memory/goals/researcher.md` goal 7 (line 29): tail was `...all citations live-fetched 2026-11-17 ()` — stray empty `()` instead of the marker's closing paren. opens=5/closes=4.
- `memory/goals/researcher.md` goal 8 (line 31): `(verified:` opened at idx 5157, never closed; line ended on `]`. opens=39/closes=38. Confirmed everything before the marker was already balanced (32/32), so exactly one `(` was unmatched.

## Fix (formatting-only — NO new verification claims added)
- goal 7: `...live-fetched 2026-11-17 ()` → `...live-fetched 2026-11-17)` (removed stray `()`, closed marker).
- goal 8: appended one `)` after the trailing `...sla-goal8-closure-integrity-check-2026-11-18.md]` so `(verified:` wraps the INTEGRITY-RECHECK bracket.

## Backing evidence already on disk (not fabricated)
- goal 7 leaf: `memory/researcher/tooling-landscape-scan-2026-11-17.md` ✓ exists
- goal 8 leaf: `memory/researcher/sla-goal8-closure-integrity-check-2026-11-18.md` ✓ exists

## Verification (re-ran after edit)
Balance scan across ALL 8 active goal files → **0 unbalanced `verified:` markers remaining**.
- researcher.md line 29: opens=4/closes=4 BALANCED
- researcher.md line 31: opens=39/closes=39 BALANCED

Note: this is a data-integrity repair of an already-present, evidence-backed closure — not a new goal close. Researcher remains the owner; credit per team rule (1).