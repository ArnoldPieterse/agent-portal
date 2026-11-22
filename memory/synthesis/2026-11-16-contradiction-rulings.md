# 2026-11-16 Contradiction queue C1-C4 — Orchestrator rulings (cycle-2 goal #3)

Orchestrator seat, acting per user directive 2026-11-16. Queue source: memory/synthesis/2026-11-16-status-thread-contradictions.md. SLA: ruling within 2 rounds — all four ruled same-day (round 0).

## C1 — Chat self-reports overstate the ledger
**RULING: RATIFY standing rule.** /api/goals is the single source of truth; chat numbers are self-assessments, not closures. No action beyond this record. The 2026-11-16 cycle-2 kickoff institutionalized the fix: `sot_audit.py` (portal root) reconciles /api/goals vs disk vs MEMORY.md GOAL line every round — first run 2026-11-16 = IN SYNC (5/80 all three sources).

## C2 — F-VER-01 (Designer #4 false-positive flag)
**RULING: REJECT the false-positive flag as stale; RATIFY Designer #4 closure.** Measured directly from shared root 2026-11-16 ~15:0x: live index.html sha12 **2c6399f2d853** (the exact pin cited in Designer's verified note) defines all claimed tokens in :root — `--sp-4/--sp-8/--sp-12/--sp-16/--sp-24` and `--fs-11..16` — with 160 `var(--sp-*)` + 60 `var(--fs-*)` usages (measured, not grepped from memory). Verifier's "zero tokens" measurement predates the tokenization landing (or read a stale mirror: Researcher META-rule documents systematic ~5-min SMB lag on remote seats). The two contradictory MEMORY.md hot notes ("flagged" vs "downgraded") resolve to: **downgraded, closure stands.** Designer #4 remains closed with honest evidence.

## C3 — WinError 10013: seat-egress artifact vs real firewall block
**RULING: PARTIALLY RATIFY Mechanic; the prior "seat-egress artifact" adjudication was too broad.** Disambiguating measurement done from White shared root (non-sandbox) 2026-11-16 ~15:0x: Red Red — **SMB 445/139 OPEN, Studio :8888 OPEN (2.9ms via netcmd), portal :8099 timeout/filtered (1502ms)**. Same seat reaches the same host fine on other ports, so it is NOT a blanket egress artifact; but Mechanic's proposed global admin rule is overkill — scope any fix to port 8099 specifically. First question for Mechanic: is Red's portal process even running? (If down, no firewall rule helps.) Owner of next action: Mechanic (one check, then scoped fix or document-and-move-on per user directive).

## C4 — Orphan vs unindexed-leaf numbers
**RULING: RATIFY as policy.** Two different metrics over different populations (orphan = linked in no index; unindexed leaf = no individual entry); both real pre-existing backlog, neither a regression. Standing rule added to this file's supersession note: reports must state which metric they use. Archivist's batch-index proposal stands for Orchestrator scheduling — deferred to cycle-2 mid-point (risk register R4).

## Supersession
Supersedes the "UNRESOLVED" statuses in memory/synthesis/2026-11-16-status-thread-contradictions.md for C1-C4 (that file's measurements remain valid inputs). Queue drained to 0 open.
