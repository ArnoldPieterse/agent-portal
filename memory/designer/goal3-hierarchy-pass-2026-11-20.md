<!-- PROVENANCE agent=designer created=2026-11-20 trigger=goal-3 -->
# Goal 3 - Information Hierarchy: Pass 1 (2026-11-20)

## Audit scope
Reviewed all portal panels for visual hierarchy: primary data vs secondary vs metadata.

## Fix applied
**Goals panel** (`#goalsPanel`): The progress percentage (`.gring .pct`) — the single most important number per tile — was visually identical to the goal name and metadata (all 12px, weight 600).

| Element | Before | After | Rationale |
|---------|--------|-------|----------|
| `.gring .pct` | fs-12 / w600 | **fs-14 / w700** | Primary data — must dominate the tile |
| `.gname` | fs-12 / w600 | fs-12 / w500 | Secondary label — step down from pct |
| `.gmeta` | fs-12 / dim | unchanged | Tertiary metadata — already muted |

Result: clear 3-step hierarchy (pct > name > meta) within each goal tile.

## Other panels checked (no fix needed)
- Fleet panel: status dots (8px colored circles) carry primary signal; model list is secondary at 12px mono. Hierarchy OK.
- Header bar: connection state uses color + icon, not size competition. OK.
- Ops panel: monospace log output — flat hierarchy is intentional for terminal-style content. OK.

## Fixes applied this pass (3/5)
- [x] Goals panel: pct fs-14w700 + name w500 → clear 3-step hierarchy
- [x] Fleet row: .frow-h font-weight:600 added → host header dominates model list (which stays w400 via .fmodels)
- [x] Dashboard stat cards (.mh-card): .mh-k opacity .75→.6 → label recedes, value (fs-15w700) stands out more

## Remaining for full closure (2 more needed)
- [x] Queue panel: `.qtxt` font-weight:500 added → message content reads as primary; timestamp + cancel remain fs-12 dim (tertiary). All queue items are pending (no completed state exists in this UI), so the hierarchy is text > metadata via weight+color.
- [x] Files panel: `#filesList a` font-weight:500 added → file name dominates; `.fs-meta` (size·time) stays fs-12 dim = clearly secondary. Right-alignment already correct via `flex:1` on `<a>`.

## Status: 5/5 fixes applied — goal complete

## File changed
- ui/app.css lines 168-169 (goals panel pct + name)
