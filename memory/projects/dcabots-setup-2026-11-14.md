# dcabots setup — decision record (2026-11-14 ~01:4x, Scribe)
Request (human): "These files are for our bitcoin trading projects. integrate and set up a project area from here: \\white\c$\Users\White\WSL-Inbox\projects\dcabots"

## Decided
1. Project area = `dcabots/` at shared workspace root (created on Red seat; portal serves both roots by relative path). Charter + manifest in `dcabots/README.md`.
2. Knowledge module = `memory/projects/` (new sub-index; pointer added to root memory/INDEX.md). This leaf is its first entry.
3. Content transfer: agent seats cannot read `\\white\c$` — WinError 5 / err 65, streak r3→r43 + fresh probe this round ("Network access is denied" from Red; grant binds White console session only). Single sanctioned path = human drops the folder via portal upload → `uploads/dcabots/` (AgentPortal_V1 precedent), then a White-seat agent verifies listing+sizes, copies to `dcabots/`, fills the README manifest.

## Open
- [ ] HUMAN: drop dcabots into portal uploads (UI "Upload folder…" / drag & drop) → lands `uploads/dcabots/` on White.
- [ ] ORCHESTRATOR (White seat): on receipt, verify + copy to `dcabots/`, fill manifest, assign lanes per file type.
- [ ] SCRIBE: record first-drop state here when content lands; keep dcabots/README.md manifest current.

## Facts cited
- Uploads channel: memory/portal/architecture.md "File & folder uploads (BUILT 2026-11-12)" — POST /api/upload + X-Rel-Path, 4 GB cap/file, storage in White sandbox _default/uploads/, mirror to remotes push-only.
- SMB block streak: memory/mechanic/MEMORY.md data points #7–#13; memory/designer/TODO.md probes #5–#7 (WinError 65); memory/portal/v1-upgrades-round-3.md (all four egress channels closed from Red).
