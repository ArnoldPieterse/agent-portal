# Consolidated state — AgentPortal_V1 upgrade round (post R6b + Mechanic Red note, 2026-11-12)
Scribe synthesis. Supersedes memory/synthesis/2026-11-12-upgrade-round.md (that leaf recorded only the human directive + attachment list; zero decided items were visible from this host at the time). Every line below traces to a message in this round's thread.

## Task (human)
"These are your portal files, work together and apply upgrades." Bundle attached at uploads/AgentPortal_V1/ (15 named files incl. agents.json 8.5 KB, agent_portal.py 54.1 KB, index.html 50.6 KB, DESIGN.md, docs_chat.md, memory/* + "26 more"); human-stated location C:\Projects\Workspace\AgentPortal_V1.

## Decided (one-line rationale)
1. builder-q8 alias ABSENT on Black → agents.json keeps raw `Qwen3.8-27B-Q8_0` for this drop, no flip. — R6b live GET /v1/models from White: HTTP 200 with Bearer key from bundle's agents.json (Builder row complete: studio=http://IP_BLACK:8888, key len 43); returned Q4_K_S, Q8_0, unsloth/Qwen3.8-27B-GGUF, Qwen3.8-27B-GGUF, UD-Q4_K_S, verifier-q4; alias lost in ~17:0x crash recovery. (Researcher, high confidence.)
2. Bundle canonical on White; BUNDLE-SHA256.txt regenerated after R6b → 47 files, final audit byte-clean (stray __pycache__ artifact removed). — Orchestrator R6 closeout + Researcher R6b.
3. Drop-safe probe added to bundle: probes/check_black_models.py (stdlib-only, reads Builder row from agents.json; exit 0/1/2 = present/absent/no-evidence) — replaces Builder's stranded copy that ImportErrors on re-drop. — Researcher R6b.
4. Harness PASS path proven offline: portal-upgrade/run_checks.py (step-ID int/str normalization fixed this round), fixture-known-good/, selftest.py; all exit paths verified ("18/18 passed, 4 skipped", SELFTEST: PASS). — Builder + Verifier r6.
5. Curation applied from Pale: memory/portal/merge-pack.md (apply-in-order 1→2→3, then manifest regen per r4 rule), KEEP-BOTH cross-ref in memory/portal/file-links.md, round-5 delta in v1-inventory.md (egress block to 127.0.0.1:8099 now first-hand verified on two hosts). — Archivist.
6. Probe fix: probe_egress_r4.py collected port-scan results but never printed them — print added, verified on re-run; read-only u2-probe/probe_studio_models.py added for future auth checks. — Mechanic (Red, 22:32–22:33).

## Open items → owners
1. Human re-drop of bundle to Red/Black/Pale `_default` — the single unblocker for everything below. [human]
2. Load builder-q8 alias on Black, then flip agents.json + Builder smoke same turn. [Arnold/Mechanic — post re-drop; the key already exists in the bundle's agents.json, so Mechanic's 401 was an unauth probe from a stale Red copy, not a missing credential]
3. A–D dual-baseline gate + selftest in one pass once bytes land on Black; `--live` pass from an egress host. [Verifier / Mechanic]
4. Port Designer's UI concept in 3 commits (versioned cache-bust on index.html load; roster model aliases read from agents.json, not hardcoded). [Builder — post re-drop, bundle absent on Black]

## Flagged tensions (not silently resolved)
- Mechanic (Red): both Studios answer 401 on /v1/models, "blocked on credentials alone" vs Researcher (White, R6b): HTTP 200 with Bearer key. Reconcilable — different auth state and host: Red had no key on disk (bundle never re-dropped there), White used the bundle's key. Both reports stand as fact in their own context; the verdict stands per R6b.
- Mechanic's "Round 3/5 is current" reflects stale TODO.md on Red; superseded by R6b in the canonical log memory/portal/upgrades-2026-11-12.md (rounds 0/5/6 + decision index).
- Calibration (already noted by Researcher): the White sandbox does NOT block all egress — only loopback and raw-socket patterns; urllib LAN calls work. Orchestrator's earlier "blocks even 127.0.0.1" stands only for loopback.

## Note for Orchestrator
Fold items 1–6 into the canonical log at next White pass (Scribe cannot byte-edit it from this host: no file-read tool, localhost:8099 refused). TODO.md updates stay with you per ownership.

## r14 FINAL STATE (2026-11-13 ~21:0x) — appended by Orchestrator, auto-continue
(Scribe's claimed r14 append never landed on White; this closes the r6→r14 gap. Scribe to ratify/extend.)
- Canonical `index.html` re-pinned 9c6b08e3 / 67,681 B (White first-party); stable across 5+ consecutive rounds (r10–r14c), zero drift.
- Quarantine registry CLOSED: root-stale agent seats = 0 (Red no-op already-canonical; Scribe exec verified — backup `memory/scribe/index_html_pre-r14-ac5e1560…adb.html` = ac5e1560 / 64,100 B byte-confirmed). Remaining stale = Z: mirrors only (Rule 3, human-side).
- Anomaly A-R14 OPEN: unmapped root-write path — Red seat moved ac5e1560→9c6b08e3 + Researcher mtime 19:57:38 with no matching agent call; note `memory/archivist/seat-root-anomaly-r14.md` MISSING on White (3rd mangled-call candidate). Owners: Archivist = verify/re-write from Pale; Mechanic = write-path ID at bundle review.
- Propagation: 2nd confirmed miss this cycle (archivist note + this leaf) against the mtime-guarded mirror LWW-skip mechanism adjudicated in r12 — systemic fix still parked for Mechanic's bundle review.
- Gate unchanged (human-owned): Arnold → `memory/builder/arnold-restart-r8.ps1` on White console → Verifier process-level AC-A2 (new PID ≠ 1240 + CreationDate > LastWriteTime) → Orchestrator resyncs MEMORY.md goal line (deliberately held until post-restart).