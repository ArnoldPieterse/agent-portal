# dcabots intake — thread synthesis (2026-11-14, Scribe)
Sources: group chat 2026-11-14 (Researcher, Builder, Verifier, Designer, Archivist, Mechanic messages) + on-disk state checked at Red seat this round.

## Task (human)
"These files are for our bitcoin trading projects — integrate and set up a project area from `\\white\c$\Users\White\WSL-Inbox\projects\dcabots`"

## Decided (one-line rationale)
- D1 No agent seat can pull `\\white\c$` — five independent reproductions this thread (Builder@black err 5; Verifier@black err 5 ×2 incl. `\\White\C$`; Designer@pale WinError 65/5; Archivist@pale err 5 + no stored cmdkey; Mechanic@red err 5) → transfer must originate on White or via portal upload.
- D2 Working channels: (a) portal upload → `uploads/`, then `python dcabots\intake.py uploads\<name>.zip` (code-verified by Verifier: POST /api/upload, X-Rel-Path header, 4 GB cap); (b) White-local copy into the White sandbox (mirror path proven; Archivist confirmed destination = seat sandbox `_default`). Channel "xcopy to White workspace → 5-min mirror" FAILed verification: memory_mirror.py pushes only the git-tracked allowlist + memory/ (Verifier; Mechanic concurs) — a fresh untracked folder will not propagate.
- D3 Project facts from Researcher's local copy (`uploads\dcabots`, since retired): self-hosted DCA bot, Binance USDT spot; snapshot last activity 2026-10-14; E14 stalled at 89/440 responses (cache-resumable); stage-3 final report + E15 verdict never run; 29/29 engine self-tests pass on their host; mirror missing `webapp.py` + `requirements.txt` (both exist on White `C:\projects\dcabots`); no API keys in mirror (pattern-scanned clean).
- D4 `dcabots/intake.py` v3 (Builder@black) = PASS per Verifier: dir/zip import, idempotent re-run, zip-slip refusal, empty-source handling; every manifest sha256 independently recomputed and matched.

## Contradictions (flagged — NOT resolved by this synthesis)
- C1 CONTENT EXISTENCE: Researcher reports 330 files / 197 MB integrated at `projects/dcabots/` on their seat (byte-for-byte verified; uploads copy retired) — vs Verifier "no source files exist on any agent seat" and Designer/Archivist/Mechanic scaffolds with manifests "awaiting ingest". On-disk check at Red this round: `projects/dcabots/` holds only INTEGRATION.md; `uploads/` has no dcabots. Likely explanation: Researcher's tree sits in one seat's sandbox and the mirror does not push untracked folders (D2). UNVERIFIED which seat holds it — needs one check from that seat / White console before anyone declares content integrated.
- C2 TWO ROOTS: top-level `dcabots/` (Scribe charter README @Red ~01:4x; Builder intake harness @black) vs `projects/dcabots/` (Researcher content claim + Designer hub index.html @pale + Mechanic INTEGRATION.md @red). Per-seat copies have diverged (intake.py/.gitignore not mirrored to Red — consistent with D2). Recommendation pending Orchestrator ratification: canonical = `projects/dcabots/` (majority usage + named as the White-sandbox target in INTEGRATION.md); fold Scribe charter README into it. NOTE: this contradicts Scribe's own earlier decision record (`memory/projects/dcabots-setup-2026-11-14.md` chose top-level `dcabots/`) — flagged here, not silently overridden.

## Open items (owner → action)
- O1 HUMAN or White console: move the real tree — portal zip upload to `uploads/` (channel a), or on White copy `C:\Users\<white>\WSL-Inbox\projects\dcabots` → sandbox `projects\dcabots` (channel b). Content is NOT yet in any verifiable shared location.
- O2 Orchestrator: resolve C1 (which seat holds the 330-file tree; is it already at the canonical target?) and C2 (ratify one root); add dcabots line to TODO.md live plan (Researcher's standing ask, unaddressed in-thread).
- O3 Builder: fix `dcabots/farm.py:569` cross-drive `os.path.relpath` bug (self-test exits non-zero on multi-drive hosts) — from whichever seat holds the tree.
- O4 Verifier: re-run self-test suite from canonical path after O3; acceptance gate per Mechanic's INTEGRATION.md = file count + bytes vs source, /api/manifest check.
- O5 Researcher: resume E14 (89/440, cache-resumable) → stage-3 final report + E15 verdict.
- O6 Fetch `webapp.py` + `requirements.txt` from White `C:\projects\dcabots` into the canonical area (missing from mirror).

## Artifact inventory (per-seat, as of this synthesis)
- Red: `dcabots/README.md` (Scribe charter), `projects/dcabots/INTEGRATION.md` (Mechanic), `memory/projects/{INDEX.md, dcabots-setup-2026-11-14.md, dcabots.md}`.
- black: `dcabots/{README.md, .gitignore, intake.py v3}` (Builder; Verifier PASS).
- pale: `projects/dcabots/{README.md, index.html hub, code/ config/ data/ docs/}` (Designer), `memory/archivist/dcabots-intake-2026-11-14.md` (Archivist).
- Researcher seat (unconfirmed): `projects/dcabots/` 330 files / 197 MB (claim — see C1).
