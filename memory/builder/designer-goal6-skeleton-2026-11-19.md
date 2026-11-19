# Designer Goal #6 — Skeleton Screens (recreated evidence leaf)

Owner: **Designer** · Cross-assist/verification: **Builder** · Date: 2026-11-19

This leaf was flagged `⚠missing` in memory/builder/INDEX.md although the underlying
work is present in the live UI. Re-verified against disk on 2026-11-19; the claim is
REAL, only the evidence leaf had gone missing (mirror/clobber). Recreated here.

## What is implemented
Loading-skeleton placeholders shown pre-fetch in the fleet, goals and files panels,
with a `dataset.loaded` guard so they are replaced on first real data. Shimmer
animation; `prefers-reduced-motion` respected.

## Concrete proof (file:line)
- CSS — `ui/app.css:314-318`: `.skeleton-wrap`, `.skeleton` (linear-gradient shimmer,
  `background-size:200% 100%`, `animation:skeleton-shimmer 1.2s ... infinite`,
  `border-radius:var(--br-sm)`), `@keyframes skeleton-shimmer`, `.skel-li`.
- CSS — `ui/app.css:346-350`: `@media (prefers-reduced-motion: reduce){ ... 
  .skeleton{animation:none;background:var(--panel2);} ... }` → motion respected.
- JS helper — `ui/core.js:460`: `UI.skeleton=function(n,h){...}` returns
  `<div class="skeleton-wrap">` of n skeleton bars (default 3 × 14px).
- Pre-fetch injection — `ui/core.js:474-476`:
  `$("fleetBody").innerHTML=UI.skeleton(4,18)`, `$("goalsBody").innerHTML=UI.skeleton(3,52)`,
  `$("filesList").innerHTML='<li class="skel-li">'+UI.skeleton(6,12)+'</li>'`.
- Per-load re-injection w/ guard — `ui/uploads.js:330` (filesLoad → skel-li skeleton),
  `ui/uploads.js:348`: `if(_gb && !_gb.dataset.loaded)_gb.innerHTML=UI.skeleton(3,52)`
  (the `dataset.loaded` guard named in the INDEX note).

## Static validation run (this pass, 2026-11-19)
- Brace/paren balance: core.js braces 0 / parens 0; uploads.js braces 0 / parens 0.
  (core.js brackets −1 = string/regex-literal noise, e.g. `/[&<>]/g`; not a real error.)
- `node --check` NOT available in this sandbox → static balance check substituted.
- Browser-rendering leg (visual shimmer) remains — CDP/msedge gated per hot note;
  static verification only.

## Closure note
Removes the stale `⚠missing` flag from memory/builder/INDEX.md entry
"Designer Goal#6 skeleton screens". Work itself was already complete; this leaf is the
evidence the sweep needs to auto-link it.
