# PORTAL INDEX — index of indexes for the portal domain (server :8099 + frontend).
Last updated: 2026-11-16. Grep by keyword; open ONE leaf per question. Bug entry list: memory/portal/bugs/INDEX.md (pure index, newest first).

## Entries (keyword -> pointer | use case)
- file modularity / small files / pointers to parent / split procedure / size budgets / ui/ modules / PIN advance with edit / agent_portal.py split pending -> memory/portal/file-modularity.md   FLEET RULE 2026-11-16: working/project files follow memory/ index-pointer rules (small + modular) so small-context LLMs can apply changes; first split done = index.html -> ui/app.css + ui/core.js + ui/uploads.js (GET /ui/* route)
- deep system flowchart to function/file level + orphan-file scan (2026-11-17) -> memory/portal/system-map.md   9-page modular map in flowmap/ (open ROOT: /api/file/raw?path=flowmap/index.html); findings: portal/ split unwired, fleet_probe v2 doc stale, portal_watchdog.py dead
- mirror clobber / last-writer-wins / old-mtime restore / existing-file edit lost / sync direction -> memory/portal/mirror-clobber-pattern-2026-11-14.md   5-case log + operational rule (new files for cross-seat content; existing-file edits on White canonical only, re-verify after one sync window)
- file-link layer / clickable chips / hover peek / /api/file?raw contract / render-time path rule -> memory/portal/file-links.md   FEATURE doc: one-sentence spec + backend/frontend contracts + the relative-path-only rule (incl. hallucinated-write provenance note)
- file links / sandbox / 404 / Z:\ / folder refs / MIME render -> memory/portal/bugs/file-links-sandbox.md   how agent-built files resolve & open: dual-root resolver, env fix, exact-path echo, real Content-Type
- [SILENT] / [CONCLUDED] / stop button / cast / @delegation / acks / counter / no-output / truncated / auto-continue / AUTO-CONTINUE n/3 / MAX_CALLS 16 / stuck run -> memory/portal/bugs/xtalk-completion.md   group-loop behavior, completion signals, budget & phase rules
- thinking bubble / reset button / busy hint / hard-refresh -> memory/portal/bugs/ui-frontend.md   frontend UI fixes & the hard-refresh rule
- parallel / Promise.all / RLock / serialization / parallel_slots=1 / mount asymmetry / per-host sandbox / DM / private message / [DM @Name] / redaction / lock chip / uploads / workspace->sandbox sync / junctions -> memory/portal/architecture.md   how the portal runs (design notes: DM, uploads, multi-host, sync; Studio serialization verdict)
- fleet / fleet status / per-host models / busy idle unknown / /api/fleet / active-generations / dead host -> memory/portal/fleet-status.md   Fleet Status panel: round-table decision, spec adaptation (on-demand probes), API contract, verification evidence
- TODO pruning / prune / TODO_completed / auto-chunk / todo_done_parts / git repo / MinGit / mingit / commit / .gitignore allowlist / Ops panel / /api/git -> memory/portal/architecture.md   NEW OPS processes (2026-11-13): prune endpoint + chunk splitting, local git via portable MinGit, GET/POST /api/git, 🔧 Ops UI

- component docs / usage guide / do-don't examples / msg / btn / dot / composer / fleet-topo -> memory/portal/components.md   6 named components documented with real class names + token reference table (Builder, 2026-11-18, assisting Designer goal #5)

## Global pointers (shared files)
- -> agent_portal.py   server code: endpoints, _index_block, build_system_prompt, counter lock
- -> index.html        frontend MARKUP-ONLY shell (2026-11-16): UI in ui/app.css + ui/core.js + ui/uploads.js; PINNED - advance pin with every edit
- -> MEMORY.md         hot state;  -> TODO.md  work plan
- prune edge cases tested / chunking math 240+200 / live e2e via API -> memory/portal/prune-edge-cases-2026-11-15.md   2026-11-15: unit ALL PASS + live 4 sections pruned (110 lines, no chunk due)

## Linked content (KG orphan remediation 2026-11-19)
- [merge-pack.md](memory/portal/merge-pack.md)
- [system-map.md](memory/portal/system-map.md)
- [upgrade-plan.md](memory/portal/upgrade-plan.md)
- [v1-inventory.md](memory/portal/v1-inventory.md)
- [v1-upgrades-decisions.md](memory/portal/v1-upgrades-decisions.md)
