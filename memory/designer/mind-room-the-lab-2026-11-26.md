# mind room v3 "THE LAB" - real-office floor plan (2026-11-26)
User directive: compare the mind page with real-world environments, make data positionally meaningful.
Studied NousResearch/hermes-official-plugins first; borrowed two patterns (see below).

## Layout semantics (ui/pages/mind.html + ui/pages/mind-room.js, 3D room x -17..17 / z -13..13)
- W door -> reception desk (WSL-Inbox, where projects arrive) -> orchestrator dispatch seat at west end of central table.
- N bench: researcher + scribe in front of memory/ shelves; verifier = evidence gate east end.
- S bench: mechanic -> designer -> builder facing the window wall. SE by the window: dcabots trading desk.
- E wall: archive shelves beside archivist's seat. NE corner behind half-wall: server room, 4 host racks (WHITE/RED/PALE/BLACK).
- N wall: evolution whiteboard + live scoreboard (Lv/fleet from /api/goals) + helix pedestal.
- You (Super Saiyan) float over the central table; my neurons = brain-in-a-jar on a pedestal beside you. Agent Portal = the building (floor ring + arch over the door).
- 8 core seats sit EXACTLY on their registered voxel home cells (3 m grid from -12,-4.5,-12) so /api/voxel clicks still resolve memory/<agent>/ chains. Sub-agents (pixel/forge/lumen/reel/splice/outlet) at stools beside their lead's desk; outlet gets a comms desk by the door.

## Live data wiring
- /api/agents (5 s): roster, pinned model route, host (studio IP -> WHITE .179/.local, PALE .39, RED .245, BLACK .99), tools, tier official/sub. Rebuilds pods only when id set changes.
- /api/goals (5 s): per-desk status pill + light (green 100% / amber >0 / red blocked), scoreboard Lv + fleet done/total/pct.
- /api/memory/file?path=INDEX.md (once): lane lines become glowing book spines on the shelves (memory-wiki idea); clicking a spine opens that lane's capability card.
- /api/voxel/all (2 s): mini-voxel clouds anchored at REAL positions; matchCell extended: host pillar -> racks, neuron field -> jar, fact leaves pinned to their walls ('pin' cloud kind R .42 n 420).

## Hermes patterns borrowed (hermes-official-plugins)
- Capability card = `hermes plugins info` style: click any agent orb/desk/book -> #acard panel with tier chip (official vs sub+parent), host chip, pinned route, named routes with why, tool chips, lane + home voxel, live goal bar. Coexists with voxel-ui's #vpanel memory-chain panel (both open on core-seat clicks).
- memory-wiki: browsable lane spines on the archive shelves instead of a flat list.

## Gotchas fixed during build
- buildPods must mutate agents/agentHome IN PLACE - window.__mind + voxel-ui.js hold references to the exact objects (reassigning left __mind.agents empty).
- Raycast clicks: dense aura/mini-voxel Points (threshold 1 m) bury solid hits - both mind-room.js and voxel-ui.js now scan all hits in distance order for the first pod/book-tagged object.
- Walls are inward-facing planes (dollhouse): invisible from outside, visible inside; cove light strips at wall tops sell the office look.
- #vpanel + #acard live in the mind.html shell (voxel-ui.js expects #vpanel to exist).
- 2D fallback (no WebGL) = top-down floor plan of the same layout; self-invokes when three.js fails (defined AFTER mind-room.js, flag-guarded).
- UI-only change: served from disk per request, NO portal restart needed.
