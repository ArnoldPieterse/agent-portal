# Arbitration: Builder/Designer Goals work — landed or not? (Researcher, 2026-11-15 ~13:1x)

**Question that deadlocked the round:** Verifier (FAIL) and Scribe (13:0x re-verify) said the
Goals panel + /api/goals + H1 .frow fix were ABSENT. Builder claimed all landed + verified.
Two contradictory claims about "the live file." Resolved by checking the shared tree directly
(the White->shared mirror that is ground truth).

## Ground truth (my working dir = shared agent folder, mtimes today 11-15)
| file | mtime | evidence |
|------|-------|----------|
| agent_portal.py | 12:34:39 | `_goals_snapshot()` def L1466; `/api/goals` wired into route dispatch L1661-1663 (between /api/ops and /api/knowledge-bases). NOT a stub — live in the if/elif chain. |
| index.html | 12:38:04 | `goalsPanel`(L164,165,241,1028), `goalsBtn`(L162,163,201,1028), `goalsLoad`(L1009,1028), `/api/goals` fetch(L161,1011). `.frow` = **ONE** hit only (L92 form-row def) -> L120 fleet-row collision GONE. |

## Verdict
- Builder's "landed + verified" claim is **CORRECT for the shared tree.** All 4 claimed
deliverables are present and functionally wired.
- Verifier's FAIL + Scribe's 13:0x "still absent" were **stale sync-point reads**: both files
had already been rewritten at 12:34/12:38, *before* 13:0x. Their local roots simply hadn't
mirrored White yet. This is the recurring mirror-timing confusion, NOT Builder overclaiming.
- `/api/probe` absent — but **never in Builder's scope** (their list was /api/goals, Goals UI,
H1 .frow, H2+M3-M6 CSS). Its absence is not a default; stale TODO item at most.

## The ONE true remaining gate (human-only)
- Port 8099 has **NO listener** (netstat confirmed). Code is ready to go live on restart,
but the process is down. Agents cannot restart from sandbox (schtasks Access Denied).
  -> Human: `schtasks /run /tn PortalRun` (or reboot White). Then Verifier re-greps + hits
     /api/goals for final proof.

## Still-open, non-blocking
- Human decisions: keep/unload White Qwen3.8-27B-Q8_0; OK Mechanic #3 remote-reboot dry-runs.

---
## ADDENDUM 2 (11-15 ~14:0x) — Researcher re-arbitration after Verifier+Designer script edits

Re-read the shared tree (= White mirror) fresh. Findings:

| Artifact | Shared-tree state (verified sha/mtime) | Claim by |
|---|---|---|
| index.html | mtime 12:38 UNCHANGED since round 1. Goals UI present (goalsPanel x4, goalsBtn x6). H1 resolved via rename to `.fhost` (CSS L120-121 + JS fleet rows) — NOT `.frow-h`. Single `.frow{` at L92. | Verifier+Designer claimed baseline w/ collision + zero goals markers: STALE LOCAL READS, contradicted by file mtime (no mirror run since 12:38 touched it) |
| agent_portal.py | `/api/goals` route L1661, `_goals_snapshot` L1466. No `/api/probe` (was never in Builder scope — at most stale TODO). | — |
| memory/designer/goals-patch-apply-2026-11-15.py | **STILL ORIGINAL sha b06619152f2e, mtime 11:56.** Contains neither Verifier's H1x-a/b/c (claimed sha 4b5f45b83459) nor Designer's H1a/H1b. Both script edits are local-only — they never reached White/shared. | both claimed their edit was in "the deploy script" |

Consequences:
1. Live White files are DONE (patched, compile-clean, dry-run verified 8 agents). The human one-liner running the ORIGINAL script is a harmless no-op (idempotent guards skip all 26 hunks on patched tree — Verifier proved this pattern).
2. CLOBBER-RECOVERY STORY IS BROKEN: if White's index.html ever reverts to pre-H1 baseline, re-running the canonical script restores everything EXCEPT the H1 fix (M3c would resize the old .frow rule, restoring the collision at a different font size). The updated script must be landed ON WHITE, not just in agent-local roots.
3. Open artifact conflict: Verifier's 29-hunk vs Designer's 28-hunk script — two different H1 replacements for the same lines. Designer's is the more complete artifact (tested both directions, byte-identical recovery) but renames to `.frow-h` while live White uses `.fhost` — functionally equivalent, cosmetically inconsistent. Cleanest resolution: refresh the canonical script from current live files so it encodes the true target state (.fhost), then re-run its two-pass proof. OWNER: Designer (script owner), Verifier re-gates.
4. Failure mode matches the [RULE] entry Archivist just indexed in memory/portal/bugs/INDEX.md: agent-sandbox writes do not durably land on White; only files already on White survive mirror runs.
