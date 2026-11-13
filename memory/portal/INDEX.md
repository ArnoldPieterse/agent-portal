# PORTAL INDEX — index of indexes for the portal domain (server :8099 + frontend).
Last updated: 2026-11-13. Grep by keyword; open ONE leaf per question. Bug entry list: memory/portal/bugs/INDEX.md (pure index, newest first).

## Entries (keyword -> pointer | use case)
- file-link layer / clickable chips / hover peek / /api/file?raw contract / render-time path rule -> memory/portal/file-links.md   FEATURE doc: one-sentence spec + backend/frontend contracts + the relative-path-only rule (incl. hallucinated-write provenance note)
- file links / sandbox / 404 / Z:\ / folder refs / MIME render -> memory/portal/bugs/file-links-sandbox.md   how agent-built files resolve & open: dual-root resolver, env fix, exact-path echo, real Content-Type
- [SILENT] / [CONCLUDED] / stop button / cast / @delegation / acks / counter / no-output / truncated / auto-continue / AUTO-CONTINUE n/3 / MAX_CALLS 16 / stuck run -> memory/portal/bugs/xtalk-completion.md   group-loop behavior, completion signals, budget & phase rules
- thinking bubble / reset button / busy hint / hard-refresh -> memory/portal/bugs/ui-frontend.md   frontend UI fixes & the hard-refresh rule
- parallel / Promise.all / RLock / serialization / parallel_slots=1 / mount asymmetry / per-host sandbox / DM / private message / [DM @Name] / redaction / lock chip / uploads / workspace->sandbox sync / junctions -> memory/portal/architecture.md   how the portal runs (design notes: DM, uploads, multi-host, sync; Studio serialization verdict)
- fleet / fleet status / per-host models / busy idle unknown / /api/fleet / active-generations / dead host -> memory/portal/fleet-status.md   Fleet Status panel: round-table decision, spec adaptation (on-demand probes), API contract, verification evidence

## Global pointers (shared files)
- -> agent_portal.py   server code: endpoints, _index_block, build_system_prompt, counter lock
- -> index.html        frontend code: cross-talk loop, linkifyFiles, ■ Stop, ↺ Reset
- -> MEMORY.md         hot state;  -> TODO.md  work plan
