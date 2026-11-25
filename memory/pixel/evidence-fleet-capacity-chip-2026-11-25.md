# Evidence - fleet capacity chip (pixel, 2026-11-25)

Round topic: Fleet Autonomy Convergence (legibility of steady-state fleet capacity).
Hot-note trigger: "Red back online - full fleet seat capacity restored; may need host-status chip/banner update."

## Finding / decision
- ui/fleet_status.js already hardcodes HOSTS=["white","black","red","blue"] and drives each dot from
  hosts[h].reachable on /api/fleet/status. So Red turning green is ALREADY automatic once the probe
  reports it up - no code change needed for "Red online" itself.
- The gap: the strip had an overall GREEN/AMBER/RED badge but NO explicit seat-capacity readout, so
  "full capacity restored" was not legible at a glance.

## Change (small, additive, non-destructive)
- ui/fleet_status.js render(): count reachable hosts (up/total), prepend a `.fs-cap` chip after the
  badge: `N/M up`. Tone = var(--ok) when all up, var(--warn) when one down, var(--err) otherwise.
  role="status" + aria-label "N of M hosts up".
- ui/app.css: added `.fs-cap` (inline-flex chip, height 18px, border via var(--line), radius 9px,
  font-size var(--fs-12), margin-left var(--sp-4)). Tokens only - no hardcoded hex.

## Verification (static; node/browser unavailable in sandbox)
- fleet_status.js: braces 31/31, parens 53/53, backticks even (18). No new hardcoded hex.
- All referenced tokens exist in ui/tokens.css: --sp-4, --line, --fs-12, --ok, --warn, --err.
- Read render() end-to-end: badge -> capacity chip -> per-host dots -> timestamp; order correct.
- Not pinned (only index.html is in PIN_FILES); ui/*.js + app.css edits are safe, no repin required.

## Open / not mine
- Whether to surface fleet capacity PUBLIC-facing (outlet) vs internal ops: Mechanic still clarifying.
  This chip is cockpit/internal-ops only and is NOT blocked on that decision.

Visual check: in the ops panel the strip now reads e.g. "GREEN · 4/4 up · white black red blue";
chip turns amber at 3/4, red below that.
