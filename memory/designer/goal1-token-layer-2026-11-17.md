# Designer Goal 1 — Token Layer Progress (2026-11-17)

## What was done this pass
- Audited ui/app.css: found 28 unique hardcoded hex colors outside :root
- Added 25 new semantic tokens to :root (3 existing tokens reused: --line, --ok, --err)
- Replaced ALL 28 hardcoded hex values with var(--token) references
- Result: 0 hardcoded hex colors remain outside :root; 401 total var(-- references

## New tokens added
| Token | Value | Use |
|-------|-------|-----|
| --on-accent | #fff | text on accent buttons |
| --sel-bg | #20304d | selected card background |
| --seg-on | #3a6fd6 | segmented button active state |
| --msg-you-bg | #243b63 | user message bubble bg |
| --msg-you-border | #33507f | user message bubble border |
| --dm-border | #4a3f6b | DM segment border |
| --dm-label | #b79ce0 | DM summary label |
| --muted | #8b93a7 | muted/busy text |
| --link | #6db1ff | link color |
| --link-hover | #9ccaff | link hover + peek header |
| --peek-bg | #141a26 | peek panel background |
| --peek-border | #2c3548 | peek panel border |
| --peek-text | #cdd3e0 | peek text |
| --peek-body | #aab2c5 | peek body mono text |
| --fdot-off | #888 | file dot default |
| --fdot-busy | #ffb454 | file dot busy |
| --fdot-err | #e05252 | file dot error |
| --queue-bg | #0d1117 | queue panel bg |
| --queue-dim | #8b949e | queue dim text |
| --queue-border | #30363d | queue spinner border |
| --queue-accent | #58a6ff | queue spinner accent |
| --queue-text | #c9d1d9 | queue item text |
| --banner-warn-border | #d29922 | interrupt banner border |
| --banner-warn-bg | #2d2000 | interrupt banner bg |
| --banner-warn-text | #e3b341 | interrupt banner text |

## Remaining for full goal 1 closure
- Tokenize hardcoded radii (8px appears multiple times — needs --radius token)
- Tokenize hardcoded durations (animation keyframes use px values, not durations — check)
- Document in memory/portal/design-tokens-live.md
- [data-theme="light"] override block (goal 2 dependency)

## Verification
- grep confirms 0 hex colors outside :root in ui/app.css
- index.html pin unchanged (sha12: 2a3ffa6ac79c) — no clobber risk
- File size: 18613 -> 19451 bytes (+838, token definitions + var() wrappers)
