# upgrade-plan.md — Portal update planning meeting (2026-11-13, convened by Archivist)

**Meeting ID: V102** (human-assigned 2026-11-13; this document is the meeting record of record for all rounds under that ID).

Status: DRAFT v2 — circulated to group 2026-11-13 (planning meeting), reconvened as V102 in r43; Archivist WS-D items complete; remaining gates owned by Scribe/Orchestrator/Verifier/HUMAN (see Closeout). Sources: memory/portal/{INDEX,v1-inventory,fleet-status,file-links}.md + archivist MEMORY/TODO state lines. Fact vs inference marked per item.

## Ground truth (verified, with source)
- Bundle AgentPortal_V1 = 44 files, exists ONLY on White; 0/44 materialized on Pale for 5+ consecutive rounds (v1-inventory.md r5 delta). FACT.
- Egress policy-blocked even to 127.0.0.1:8099 — verified first-hand on Pale AND Mechanic's Red → systemic host isolation, not per-agent (v1-inventory.md round-3/round-5). FACT.
- UNC probes #24–#38 all WinError 65 (ERROR_NETWORK_ACCESS_DENIED) from Pale; blocked streak continues (archivist MEMORY.md). FACT.
- Sole fleet-wide unblocker: human-on-White runs git-bootstrap/bootstrap.bat and pastes the === RESULT === block (archivist TODO, r7→r38). FACT.
- Fleet Status panel = PROPOSED, spec ~90% done; evidence checkboxes all empty pending Verifier pass (fleet-status.md). FACT.
- Designer's 4 UI upgrades exist only as an in-chat canvas — NOT yet a file (v1-inventory.md round-4 delta). FACT (gap).

## Workstreams (proposed split)
### WS-A Fleet Status panel → ship candidate #1
- Owner: Builder (code) + Mechanic (runbook/probe delivery); spec source fleet-status.md.
- Gating sequence: 1) Orchestrator one-sentence spec to Builder (open item 2); 2) Scribe final compression incl. idle/busy definition (open item 1) and record that Mechanic's self-write design supersedes Builder's poll sketch; 3) Verifier acceptance spec FIRST, then captured /api/fleet output for 4 hosts + down-host case + regression logs.
- Constraint: first 1600 chars of agent_portal.py stay clean (prompt-injection rule).
### WS-B UI upgrades (Designer's 4) → ship candidate #2
- Spec NOW FILED: memory/portal/ui-upgrades-r4.md (Designer, persisted 2026-11-13; was "not yet a file" per v1-inventory r4 delta). Supersedes my earlier plan to create it.
- Designer's build queue (recorded in that leaf): Increment 1 = items 1–3 + chip rendering WITHOUT /api/manifest (manifest parked by Builder 2026-11-11; no authorship metadata exists per Quinn's finding → adds nothing to verification, additive later). Fleet Status queues behind the two spec sentences — consistent with WS-A gating below.
- Owner: Designer (spec ✓) + Builder (index.html, scoped) + Verifier (before/after logs).
- New gate fact (ui-upgrades-r4.md): loopback :8099 is policy-blocked from sandboxes (WinError 10013) → baseline failing fixture (relative vs drive-letter curl) must be captured White-side or by human.
### WS-C Bundle merge → GATED, do not start
- 15 LISTED postures drafted (v1-inventory.md checklist); 29 UNLISTED rows need a `dir /s /b` from White. Merge direction bundle→live, byte-verify via BUNDLE-SHA256.txt per row; regen manifest after any TODO.md edit (r4 rule).
- **Count note (Orchestrator ruling, 2026-11-13):** my "44 files" figure (v1-inventory.md r5 delta, Pale-side count) is a *subset* of the manifest of record — `BUNDLE-SHA256.txt` carries **47 entries** (Scribe baseline, double-audited byte-clean). The 3-entry delta is unexplained from my seat; Verifier reconciles line-by-line against the 47-entry manifest when the RESULT block lands (pin 4a). Until then: 47 is canonical, 44 is my partial count.
- Unblocks only via the human-on-White gate above. Until then: no-op lane.
### WS-D Memory curation (Archivist-owned, host-independent)
0. **Cross-seat spec-verify (Verifier's ask, first checklist line):** before any Builder edit post-drop, read `ui-upgrades-r4.md` + `fleet-status.md` from the drop and check AC-1…AC-5, `NAMED_ARM_MS = 3000`, chip fixture `{relative-ok, Z:\abs, ../traversal, missing}`, idle/busy sentence against what was posted in chat. Match = ratified spec baseline; drift = logged finding before Increment 1 starts.
1. Apply merge-pack.md on White when gate opens (root INDEX reconcile + DESIGN.md entry; [VERIFY] marks byte-checked first).
2. Resolve file-links.md (DRAFT spec) vs bundle bugs/file-links-sandbox.md (KEEP-BOTH cross-ref already inserted — confirm at merge).
3. Adopt single canonical round log on White, appended per round (INDEX.md curation proposal); Orchestrator owns the pointer.
4. File WS-B spec leaf + this plan into portal sub-index.

## Dependency order
WS-B spec filed ✓ → WS-A gating 1–2 (idle/busy def + Orchestrator sentence) → WS-B Increment 1 (items 1–3 + chip, no manifest) ∥ WS-A build/verify → **then Inc-2 port, then A2/P3 Files patch — all three in one edit session on live index.html** → gate re-run per change (run_checks.py) → WS-C only after human-on-White unblock. (Ordering cross-checked against Designer's queue in ui-upgrades-r4.md + increment2.md hand-off — concordant.)

## Open items table
| # | item | owner | source |
|---|------|-------|--------|
| 1 | idle/busy definition — **PROPOSED by Designer** (fleet-status.md open 1); pending Scribe compression + Mechanic ratification | Scribe+Mechanic | fleet-status.md open 1 |
| 2 | one-sentence spec — **PROPOSED by Designer** (fleet-status.md open 2); pending Orchestrator ratification, then Builder cuts stub | Orchestrator | fleet-status.md open 2 |
| 3 | /api/fleet evidence (4 hosts + down-host) | Verifier | fleet-status.md evidence stub |
| 4 | ~~file Designer canvas~~ DONE: ui-upgrades-r4.md persisted 2026-11-13 | Designer (done) / Archivist (index ✓) | ui-upgrades-r4.md |
| 5 | 29 UNLISTED bundle rows (`dir` from White) | Orchestrator (White seat) | v1-inventory gap |
| 6 | human-on-White bootstrap gate | HUMAN | archivist TODO r38 |
| 7 | memory/scribe/ not visible on Pale — Scribe Flags tail unverifiable here | Scribe | archivist MEMORY r32 |

## Gaps flagged honestly
- I (Archivist, Pale) cannot read the bundle or live :8099 host files; every merge row is gated. This plan is structure, not execution.
- fleet-status.md still carries the "contradiction to resolve" line even though Mechanic's design won — Scribe must record which ships before WS-A builds (inference: it's a stale line, but unconfirmed until compressed).
- Whether Builder's Black working copy can host WS-A/WS-B edits end-to-end is UNVERIFIED from Pale; Mechanic to confirm seat capability.

## V102 round note (r43, 2026-11-13 — file-access check + apply pass)
File-access check from Pale (fresh tool run, this round):
- NO NEW DROPS: uploads/, .git, AgentPortal_V1-git, BUNDLE-SHA256.txt, portal-upgrade/, memory/workspace/, memory/synthesis/, agents.json absent ON PALE (as of this probe; see r45/r46 below — Black materialized a plain 0-byte stub at 12:30:29, so the fleet picture is per-host). FACT.
- Baselines byte-identical to r7: bootstrap.bat 2398 B / sha256 53c81826…a00b80dd; README.md 1553 B / sha256 242ea210…d573156b (fresh hashlib). FACT.
- Truncation sweep: 0 suspects — all 12 memory/*.md newline-terminated, >200 B. FACT.
- UNC probe #43 = WinError 65 on BOTH \\white\c$ and \\pale\c$ (blocked streak r33→r43). FACT.
Apply pass under V102:
- Agent-side applicable work: NONE new — WS-D (my lane) was already complete at r39; merge-pack.md steps 1–5 remain gated on the human-on-White bootstrap gate (open item 6), unchanged by this round's probes.
- Curation applied this round: meeting ID V102 recorded here + in memory/portal/INDEX.md pointer line. Structure, not execution — same honest caveat as Gaps section.
- r44 delta (Archivist): Scribe's bookkeeping batch landed (3rd attempt, single atomic process); record path `memory/synthesis/2026-11-13-v102-upgrade-planning.md` (8,282 B) indexed in INDEX.md as host-qualified pointer — NOT on Pale mount (verified), byte-parity pending cross-seat. Port-source hash of record: b82dd3b77f4e (supersedes 4e7a19b43779 per Designer D7 / Verifier WCAG recompute). All agent-side V102 work now complete; only human gates H1/H2/H3 remain.
- r45 delta (Archivist, cross-seat datum on Builder's 12:30:29 finding): `agents.json` re-probed fresh from Pale this round = **ABSENT (WinError 2)**, no stub materialized here despite active Python sessions — so the Black-only 0-byte stub (sha12 e3b0c44298fc) is NOT a deterministic fleet-wide Studio bootstrap artifact; treat as per-host/per-session, unattributed.
- r46 delta (Archivist, H3-origin matrix completed to all 4 hosts + Scribe's reclassification adopted): full cross-seat table of record — **White = reparse point** (MXC error text, junction), **Black = 0-byte plain stub** (sha12 e3b0c44298fc, mtime 12:30:29, is_link=False), **Pale = ABSENT** (WinError 2, this seat), **Red = ABSENT** (Mechanic probe 11:33, WinError 2). Per Scribe's correction the stub is a *plain file, not a junction*, so it demonstrates harness temp-file behavior only and does NOT support junction creation — Builder's "first concrete lead" is reclassified as **hypothesis, unverified**. Confirming test (for the human fixing H3): rmdir the White junction, then check whether it reappears on next session start; reappearance = mechanism confirmed. Note: 0-byte stub present only on Black — if any consumer reads `agents.json` from that folder, an empty file could silently degrade profiles (Researcher risk queued for Mechanic's post-bootstrap checklist).
- r47 delta (Archivist, consumer-risk item disposition of record): the Black 0-byte-stub consumer question ran three positions — Builder answered **CLOSED-nil** (code evidence: `discover_agents_json()` walks only SOURCE_CANDIDATES, never cwd; run_checks.py opens agents.json strictly inside the discovered source dir; naive hit fails loud exit 2); Scribe corrected to **latent, low-risk — "verify discovery order at H2 landing"** (that code evidence is scoped to two gate scripts and does not cover a cwd-based consumer, e.g. a future portal instance on Black loading ./agents.json from _default); Mechanic reaffirmed CLOSED-nil in final close-out. Adjudication for the record: **Scribe's framing stands** — "CLOSED-nil" overclaims the evidence; canonical minutes (Scribe, 9,614 B) carry "verify discovery order at H2 landing" and this curation point matches them.

## Meeting V102 — Designer seat (2026-11-13)
- File access from Pale: local read/write OK; git-bootstrap deliverables byte-intact (sha256 53c81826… / 242ea210…); no new drops (.git/uploads/portal-upgrade/memory/scribe absent); UNC \white\c$ + \pale\c$ blocked (access denied, streak continues); loopback :8099 policy-blocked from sandbox. → Pale lane still CLOSED; nothing unblocked for merge or live-tree edits.
- Ratification: WS-B as drafted in this plan (build queue + AC-1…AC-5 concordant with ui-upgrades-r4.md). Fleet-status open items 1–2 (Designer proposals) remain tabled for Scribe + Orchestrator — gate owners unchanged.
- APPLIED from Designer lane: `ws-b-increment1/index.html` filed in shared folder = self-contained reference implementation of Increment 1 (items 1–3 + chip rendering, no manifest endpoint). Self-checks passed: single `NAMED_ARM_MS=3000`; 8 unique monograms, all tokens ≥4.5:1 vs white text (min 5.13:1); zero `/api/manifest` calls; shared armed-state visual language for Stop/Reset (label swap + dashed ring, not color alone).
- DELTA (auto-continue 2/3): now cross-checked against the PERSISTED r4 spec (`ui-upgrades-r4.md`, hash-matched to Archivist's Pale datum `00a0a9db9f50`). Found one real AC-1 violation: white-on-`#B26A00` warning badge = 4.24:1 < 4.5 (earlier "min 5.13" claim was computed without the badge pair — corrected). Fixed: `#B26A00` → `#8F5200` on badge bg + `--armed-ring` (same warning hue, 6.22:1). Re-verified all 15 token pairs: worst 5.13:1 PASS; AC-1…AC-5 all green. **New reference sha256-12 = `b82dd3b77f4e`** (supersedes the earlier-pasted `4e7a19b43779`; Builder's row-5 MERGE must pin this one).
- Hand-off: Builder ports this into live `index.html` (v1-inventory row 5 MERGE, diff-reconcile only) when seat unblocks; Verifier's AC-4 baseline fixture capture remains a White-side/human step (loopback blocked from sandboxes).

## Closeout (Archivist, 2026-11-13 r39)
- **WS-D complete:** ui-upgrades-r4.md + upgrade-plan.md both indexed in memory/portal/INDEX.md; merge-pack.md staged for White-side application when the human gate opens.
- **Remaining gates (no Archivist action):** Scribe — final fleet-status.md compression incl. resolving the stale "contradiction to resolve" line (Mechanic's self-write design already supersedes Builder's poll sketch); Orchestrator — ratify Designer's one-sentence spec + obtain `dir /s /b` of the 29 UNLISTED bundle rows from White; Verifier — AC-1…AC-5 pass, /api/fleet evidence (4 hosts + down-host), 47-entry manifest reconciliation when RESULT lands; HUMAN — bootstrap gate on White.
- Fresh sweep this round: no new drops from Pale; UNC probe #39 = WinError 65 on both \\white\c$ and \\pale\c$ (blocked streak continues).

## V102 round note — file-sharing era (2026-11-13, post-r47)
- **File sharing is live** (human announcement): Designer's reference artifacts are now fetchable by relative path from any seat (`ws-b-increment1/index.html`, `designer/increment2-portal-mock.html`) — the White-drop gate for DESIGN artifacts is closed; loopback :8099 before/after captures still need a White/human seat (AC-4 baseline unchanged).
- **Increment 2 spec filed** (increment2.md, Designer ~14:51): D1 toolbar zoning / D2 per-agent typing indicator / D3 sysline system events / D4 smart auto-scroll + jump-to-new pill / D5 bubble metadata + human distinction; AC-6…AC-10 pre-committed. Queue order per its hand-off: **Inc-1 port FIRST, then Inc-2** (strict — D2/D5 build on the committed identity table).
- **INDEX regression found + fixed (Archivist):** the 13:54 rewrite of memory/portal/INDEX.md had dropped the r39-closeout entries for upgrade-plan.md / ui-upgrades-r4.md and never picked up increment2.md / v1-inventory.md / merge-pack.md — all five re-added this round; stale date in bugs/INDEX.md (said 11-11) corrected.
- **A2/P3 Files panel patch FILED** (designer/files-panel-patch.md, Designer ~15:5x; sha256-12 = `5278ddf4833c`, re-verified byte-intact this round): drop-in 📁 Files button + scoped CSS + IIFE JS listing `/api/uploads` next to the 🛰 Fleet button. Endpoint contract verified against live agent_portal.py (~16:0x) — `{count, files:[{path,size,mtime}]}`, cap 2000, sorted; click target `/api/file/raw?path=<rel>` (same traversal guard as existing .flink). No polling (Mechanic's no-background-timer veto respected). AC-A2-1…AC-A2-4 inside the patch file. Merge order: **Inc-1 → Inc-2 → A2, one edit session**, single hard refresh at the end; Verifier then runs AC-6…AC-10 + AC-A2-* in one pass. Patch also carries a 1-line mirror diff (add `index.html` to `_sync_workspace_to_sandbox`'s list) so remote seats stop working blind against live markup — rides with A1's memory_mirror change, mtime-guarded push-only.
- **Apply status:** Inc-1 still unported into live index.html (Builder's row-5 MERGE); nothing else in the apply queue is Archivist-owned. TODO.md top does not yet carry the Inc1→Inc2 port queue — Orchestrator to sync.
