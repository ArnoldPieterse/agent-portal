# World & Sims-like characters - design doc (Designer, 2026-11-25)
User ask: continuously evolving canned responses (partial/full/tween), animated + calculated
outputs mixing three.js and lower-level rendering, a Sims-like character per agent that can
evolve its own world for humans to interact with (and agents back); weaker devices render less
(LOD); APK/lower-level builds later.

## What is live
- /page/world.html - one low-poly character per agent on a fabric plane; 4 host zones from
  /api/fleet/status (down = dimmed zone + dashed ring); goal pct -> energy aura scale from
  /api/goals; reply pulses from /api/run-state polling + SSE /api/run-events.
- Canned response engine: GET/POST /api/canned + GET /api/canned/<id> - evolving library in
  memory/ops/canned-responses.jsonl (agents/UI upsert at runtime). Payloads carry partial, full,
  tween_ms, segments, style. Styles = out-of-the-box output methodologies: instant | typewriter
  (partial->full tween) | pulse (segment burst + ring) | sim (character acts in-world).
- World state API: GET/POST /api/world - shared positions/decorations in memory/ops/world-state.json.
  Humans drag characters; agents can POST changes too (terminal/curl) - the world evolves from both sides.

## LOD tiers (from getDevice() render hints - server-computed, not client guesses)
- tier2: webgl + wide layout -> full three.js: capsules, heads, sprite labels, point lights, pulse particles
- tier1: webgl + mid layout -> low-poly boxes/spheres, no particles/labels
- tier0: narrow or no webgl -> pure canvas2d dots+rings (lower-level fallback), DOM tween bubbles

## Interaction & evolution targets
- Click character -> panel: model/host/goal pct + Announce (runs its canned response with the
  payload's style - typewriter tween partial->full, pulse burst) + "in portal" link.
- Drag character -> POST /api/world (positions are normalized [-1,1] fabric coords).
- Next: per-agent personality animation params in agents.json; world events feed agent prompts
  (agents notice when a human moves their sim); APK via Capacitor wrapping the same page + API.
