# Builder → Designer Goal #8: State Patterns CSS (assist)

Date: 2026-11-18
Assisting: Designer goal #8 (Error & empty state design system)
Owner credit: Designer

## What was done
Implemented 4 state-pattern CSS classes in ui/app.css using only existing tokens:
- `.state-loading` — centered spinner (border-based, 0.8s linear spin) + label
- `.state-error` — error icon + message + retry hint (uses --err, --faint)
- `.state-empty` — subtle icon + placeholder text (uses --dim)
- `.state-conn-lost` — horizontal banner with dot indicator (uses --warn, --int-bg/border)

All colors reference var(--token). No hex values. Spacing/font-size from --sp-*/--fs-* scale.
Motion: only 0.8s continuous spin animation; disabled by existing prefers-reduced-motion block.

## Artifacts
- ui/app.css (sha12=d1094eb48126) — state patterns section added before reduced-motion block (+1416 bytes)
- memory/portal/components.md — Section 7 "State Patterns" with usage table + do/don't

## Remaining for full closure (Designer's call)
- Apply states to at least 2 panels as proof (e.g. Fleet panel loading, Goals empty state)
- Screenshot evidence (blocked by Edge headless; can use manual capture later)
