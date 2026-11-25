# api-index.md - Agent Portal API call index, linked to memory modules
<!-- parent: memory/portal/INDEX.md | sibling: architecture.md, file-modularity.md | owner: Archivist (A) -->
<!-- 2026-11-25: full inventory after "move all calculations to the API host" directive.
     Every call gets an index number (#) and a link to the memory module it best fits (M-CODE key).
     New endpoints MUST be appended here before they ship (append-only keeps codes stable). -->

## How to read
`# | METHOD path | what it does | memory link` - memory link = M-CODE key of the module that owns the
data/decision this call serves (see MEMORY.md legend: L=portal, D=fleet, H=llm, I=mechanic,
J=ops, K=orchestrator, E=goals, A=archivist, S=synthesis, U=workspace, M=projects).

## Fleet & hosts (D)
#  GET /api/fleet                per-host models + busy/idle/unknown      D
#  GET /api/fleet/status         reachability+latency+disk strip (NEW)    D
#  GET /api/fleet/topology       nodes=hosts, edges=model families (NEW)  D
#  GET /api/fleet/cockpit        one-call full fleet picture              D
#  GET /api/fleet/mode           autonomy mode get                        K
#  GET /api/net/fleet            fleet network map                        I
#  POST /api/net/probe           run probe on host                        I
#  POST /api/net/latency         latency matrix                           I
#  POST /api/net/dns             dns resolution check                     I
#  POST /api/net/http            http reachability check                  I
#  GET /api/perf                 endpoint timing ring buffer              I
#  GET /api/health               portal liveness (portal_heal.py)         I
#  GET /api/health/fleet         fleet health snapshot                    I
#  GET /api/memory-health        memory tree integrity stats              A

## Models & compute (H)
#  GET /api/models               proxy Studio /v1/models                  H
#  GET /api/models/status        per-model load status                    H
#  POST /api/scan-models         rescan local model dirs                  H
#  GET /api/gpu/requests         dual-GPU request queue                   H
#  POST /api/gpu/request         log dual-GPU load request (NEW)          H
#  GET /api/tools                agent tool registry                      H

## Chat & run engine (L core, K dispatch)
#  POST /api/chat                solo/cross-talk SSE stream               L
#  POST /api/group-run           start group run                          K
#  POST /api/run-stop            stop run                                 K
#  GET  /api/run-events          SSE run event stream                     L
#  GET  /api/run-state           busy/phase/stalled HUD                   L
#  POST /api/run-state           client run-state push                    L
#  GET  /api/history             chat history (group backend-owned)       U
#  POST /api/history             solo history save                        U
#  GET  /api/user-messages       human message queue                      K
#  POST /api/user-messages       enqueue human message                    K
#  POST /api/user-messages/check agent drain check                        K
#  GET  /api/autoloop            auto-loop streak budget                  K

## Agents (K)
#  GET  /api/agents              roster                                   K
#  POST /api/agents              create agent                             K
#  PUT  /api/agents/{id}         update agent fields                      K
#  DELETE /api/agents/{id}       remove agent                             K
#  GET  /api/scheduler           in-process scheduler status              I
#  POST /api/scheduler           schedule job                             I

## Goals & evolution (E)
#  GET  /api/goals               goal ledger snapshot                     E
#  GET  /api/goals/forecast      forecast engine output                   E
#  GET  /api/goals/history       git-based progress curve                 Ec
#  GET  /api/goals/topic         topic goals                              E
#  POST /api/goals/topic         update topic goal                        E
#  GET  /api/goals/next10.json   next-10-cycles forecast (NEW, was 404)   E
#  GET  /api/goals/onepager/{id} per-agent one-pager download             E
#  GET  /api/convergence         convergence metrics                      E
#  GET  /api/evolution/stats     evolution counters                       G

## Memory & knowledge (A, H)
#  GET  /api/memory              memory tree listing                      A
#  GET  /api/memory/file         read one memory file (traversal-guarded) A
#  POST /api/memory              write memory file                        A
#  GET  /api/knowledge-bases     RAG knowledge bases                      H
#  GET  /api/provenance          decision provenance chain                S

## Ops, git & pipeline (J, I, M)
#  GET  /api/ops                 ops snapshot                             I
#  GET  /api/git                 repo status/log                          I
#  POST /api/git                 git action (init/commit/push)            I
#  POST /api/todo/prune          prune with index_check gate              A
#  GET  /api/decisions           decision log                             Sa
#  GET  /api/merge-queue         cross-project merge queue                M
#  POST /api/merge               perform merge                            M
#  GET  /api/reqs                request/approval queue                   K
#  POST /api/reqs                submit request                           K
#  POST /api/reqs/approve        approve request                          K

## Files & uploads (U)
#  GET  /api/file                file browser entry                       U
#  GET  /api/file/raw            raw file bytes                           U
#  GET  /api/uploads             upload listing                           U
#  POST /api/upload              multipart upload                         U

## Device, auth & manifest (NEW 2026-11-25)
#  GET  /api/device              capability schema + registered devices   J
#  POST /api/device              register device probe -> render hints    J
#  GET  /api/login               profile/auth status (Google OAuth)       J
#  GET  /api/login/callback      OAuth code exchange + cookie             J
#  GET  /api/manifest            portal architecture manifest             L

## UI functions -> API map (current html, 2026-11-25 scan)
<!-- ui/*.js modules: key client functions and the calls they drive. Computations that
     lived only in JS are now served by the API host (marked NEW). -->
- ui/core.js (64 fns): chat send/stream, panel routing, git+merge UI -> /api/chat, /api/git, /api/merge, /api/merge-queue, /api/ops, /api/reqs, /api/todo/prune, /api/file, /api/agents/{id}
- ui/uploads.js (53 fns): agent editor (openEditor/save), goals panel, GPU button -> /api/goals*, /api/gpu/request (NEW route), /api/group-run, /api/memory-health, /api/run-events, /api/uploads
- ui/fleet_status.js: status strip render -> /api/fleet/status (NEW - was 404)
- ui/cockpit-topology.js: TopologyGraph canvas -> /api/fleet/topology (NEW - was 404)
- ui/cockpit-forecast.js: ForecastPanel timeline -> /api/goals/next10.json (NEW - was 404)
- ui/fleet_topology.js (19 fns): FleetTopology panel -> /api/fleet
- ui/fleet_health.js: health grid -> /api/health/fleet
- ui/scheduler.js: scheduler view -> /api/scheduler GET+POST
- ui/cockpit.js + cockpit-*.js (10 modules, ~90 fns): bars/rings/heatmaps = presentation only; data via /api/fleet/cockpit (var API) - kept client-side by design (render math, not process work)

## World & canned responses (added 2026-11-25 - Sims-like world + evolving response library)
| # | call | purpose | best fit |
|---|------|---------|----------|
| 73 | GET /api/canned | list of evolving canned-response library + known styles | C |
| 74 | GET /api/canned/<id> | partial/full/tween_ms/segments/style payload for one response | C |
| 75 | POST /api/canned | upsert a canned response - the library evolves at runtime | C |
| 76 | GET /api/world | shared world state: character positions + decorations | D |
| 77 | POST /api/world | merge position/decoration changes (humans drag, agents evolve) | D |
- ui/pages/world.html (page): three.js Sims-like world - one character per agent, host zones from /api/fleet/status, goal energy from /api/goals, live pulses from /api/run-state + SSE /api/run-events, LOD tiers from getDevice() render hints (tier2 full three.js / tier1 low-poly / tier0 canvas2d), canned-response tweening via /api/canned/<id>, world mutation via /api/world
- ui/pages/evolve.html (page): the self-evolve template this world was spawned from
