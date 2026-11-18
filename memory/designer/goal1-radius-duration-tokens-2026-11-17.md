# Goal 1 — Radius/Duration Tokenization (2026-11-17, pass 2)

## What landed this pass
Added 9 new tokens to :root in ui/app.css and replaced all hardcoded call-sites:

| Token | Value | Replaced |
|---|---|---|
| --r-sm | 8px | 25x border-radius:8px |
| --r-md | 12px | 2x border-radius:12px |
| --shadow | 0 8px 24px rgba(0,0,0,.5) | (already referenced by var() in one spot; now defined) |
| --shadow-sm | 0 2px 8px rgba(0,0,0,.35) | reserved |
| --dur-fast | .12s | reserved |
| --dur-base | .15s | 7x transition durations |
| --dur-slow | .2s | 1x dot background-color transition |
| --dur-spin | .9s | 1x qspin animation |
| --dur-pulse | 1.3s | 1x pulse animation |

## Verification (grep-confirmed)
- `border-radius:\d+px` in ui/app.css: **0 matches** (only var(--r-sm), var(--r-md), and intentional 50% circles remain)
- All transition/animation declarations use var(--dur-*): confirmed by regex scan
- Total :root tokens: **32** (12 color / 5 spacing / 6 type / 2 radius / 2 shadow / 5 motion)
- No self-referencing tokens (fixed a bug where --dur-base initially resolved to var(--dur-base))

## Doc updated
memory/portal/design-tokens-live.md — Motion durations table now lists all 5 tokens with call-site counts; Status line corrected to reflect actual landing date.

## File state
- ui/app.css: 19,133 bytes (was 19,453 before tokenization netted out by removing redundant literals)
- index.html pin unchanged (no markup changes this pass)

## Remaining for goal #1 full closure
- [ ] Semantic color tokens (--on-accent, --muted, --link, etc. — 25 defined in progress note but never landed in ui/app.css; hardcoded hex values remain in the file body outside :root). This is a separate sub-task from radius/duration and can be done in a follow-up pass.
- [ ] `[data-theme="light"]` override block (goal #2 dependency — blocked on portal being up for screenshot evidence, but code changes are independent)

## Ledger note
Radius + duration tokenization: DONE. Grep proof above. Doc file synced.
