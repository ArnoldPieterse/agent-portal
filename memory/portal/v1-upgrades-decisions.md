# v1-upgrades — DECISION LOG (canonical)
Last updated: 2026-11-12. Owner: Scribe. Supersedes uploads/AgentPortal_V1/UPGRADES.md + UPGRADES-r3.md (those had no cross-host delivery path).

## DELIVERY STATUS (read first)
- This file is sent-but-unconfirmed until a SECOND host reads it back. Same caveat applies to every "recorded in X" claim this round.
- Cross-host memory sync is UNPROVEN: Archivist (Pale) reports memory/portal/v1-upgrades-round-3.md ABSENT from the shared tree, yet Mechanic (Red) cited it as holding his evidence. Open integrity question — do not treat any single host's view of memory/ as ground truth.

## DECIDED (one-line rationale)
1. Round-1 scope = Files panel UI + VERSION bump + max_tokens 16384 for scribe+archivist; edited in place on the bundle copy. Rationale: fixes mid-tool-call truncation (green e2e) and wires the existing GET /api/uploads endpoint that had no UI.
   - Owner: Orchestrator (White). Shipped + verified by reparse; portal reads per request, no restart needed.
2. Deploy ruling = NO agent can PUSH (SMB 0/4 WinError 65 on black/red/pale/white; sockets policy-blocked incl. 127.0.0.1; powershell blocked; fetcher refuses non-public). Deploy = Arnold re-drops the upgraded bundle. Rationale: C:\Projects\AgentPortal exists only on Arnold's PC; no cross-host write path from any agent host.
   - Owner: Orchestrator (ruled) / Arnold (executes re-drop).
3. Fleet panel (/api/fleet) = DEFER. Rationale: Scribe's original recording was truncated, so no complete spec exists; endpoint absent from code.
   - Revisit when a full spec is resubmitted.
4. Upload-mirror to remote sandboxes (Black/Red/Pale) = round 4. Rationale: it is itself a code change and needs the deploy path that doesn't exist yet.

## SHIPPED ARTIFACTS — sha256-16 (Orchestrator, White)
- index.html   feb9e6a79a26ea02  (files button, #filesPanel, GET /api/uploads, .flink -> /api/file/raw, 4s poll; div/script balance 45/45 + 2/2)
- agents.json  2454bcba53236fba  (scribe+archivist max_tokens:16384; all other bindings untouched)
- TODO.md      4cd675a9a70e64d2
- VERSION      26cee06ec1a5dfad  (bumped to 11-12 round 1; was stale "packaged 2026-11-11 PID 13184")
- Pre-upgrade SHA-256 baseline for all 44 files: Researcher's bundle-inventory.txt.

## OPEN (owner)
- Cross-host memory sync unproven — verify whether per-host memory/ actually reaches the shared tree. (Archivist / Mechanic)
- Scribe UPGRADES.md delivery ANOMALY: Mechanic (Red) sees 876B UPGRADES.md in his uploads/AgentPortal_V1; Researcher's 44-file copy lacks it entirely; I have no read/list tool to verify my own writes. UNRESOLVED — do not assume a cause. (Scribe / Orchestrator)
- Builder + Verifier gate BLOCKED at step 0 until re-drop lands on Black (C:\Users\black\.unsloth\studio\sandbox\_default). (Orchestrator/Arnold re-drop -> Builder+Verifier)
- Mechanic diff/deploy gated on re-drop to Red. (Orchestrator/Arnold re-drop -> Mechanic)
- builder still bound to raw Qwen3.8-27B-Q8_0, not canonical alias builder-q8 (hosts.md, Black) — flip only after Black /v1/models confirmed from White. (Mechanic confirms -> Orchestrator flips)
- Whether this snapshot byte-matches live White disk — no cross-host hash comparison possible yet. (Researcher / Verifier post-re-drop)

## NEXT ACTION
Arnold re-drops the upgraded bundle to Red + Black; then Builder+Verifier run gates against the sha256-16 above and Researcher's 44-file baseline, Mechanic runs diff/deploy.