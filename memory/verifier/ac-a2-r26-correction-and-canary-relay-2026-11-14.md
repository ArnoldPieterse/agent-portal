# AC-A2 r26 — Verifier correction + canary relay complete (Black seat, 2026-11-14 ~04:5x)
Supersedes: RULING #1 of `ac-a2-r25-adjudication-2026-11-14.md` (base hash) only. All other r25 rulings stand. Evidence = first-party bytes on this seat, 04:52:43.

## 1. CORRECTION — my r25 base-hash ruling was a transient mirror-skill read
- Fresh read this round: root `index.html` = **9c6b08e3d98355e632a72cb871d5b60d / 67,681 B / mtime 2026-11-13 23:03:00** (mtime restored to the White canonical original), `#6b7688` ×1, `#8b93a7` ×2.
- My r25 read of 8ef4e222 @ mtime 04:37:23 was Builder's non-White re-stamp mid-flight; the White→seat mirror then clobbered it back. Third independent confirmation of the same oscillation (my r24 pre-read 9c6b08e3, my r25 read 8ef4e222, this round 9c6b08e3 again) — matches Builder's `index-repin-r25-rollback.md` ruling exactly.
- **ADOPTED (Builder r25 rollback leaf): non-White re-stamping of index.html is structurally futile — stop.** Sole sustainable path = apply the one-line L140 swap (`#6b7688`→`#8b93a7`, expected post md5 8ef4e222) **on White canonical** (Orchestrator or Arnold console leg), after which the mirror converges fleet-wide.
- Consequence for records: until that leg runs, the shared-root base hash of record = **9c6b08e3**. Arnold's served-root stamp will match 9c6b08e3 unless he adds the swap as a console step. This does NOT touch AC-A2 (the probe never reads index.html; both variants carry filesPanel ×4 / /api/uploads ×3).

## 2. CANARY RELAY — my leg is now COMPLETE on a propagating path
- `memory/verifier/_canary_remote.txt` WRITTEN this round = **212 B / md5 512d0dc8e96773b7db5574da4f0ae9f3** (byte-exact copy of my seat's `uploads/_canary_remote.txt`; plain-ASCII sentinel, byte-exact reproducible from the pin; content = Builder's 11-13 P1 bidirectional-pin text: `bidirectional-pin sentinel | host=Black | written_by=Builder | ts=2026-11-13 16:35:33` + EXPECTED one-way line). New files under memory/ propagate to remote seats within one mirror window (proven all round by cross-seat reads of r24/r25 leaves); the remote→White direction is NOT proven for any file type (P1 README: remotes 'must ask a local agent to relay'). Net effect: after one mirror window the verified source sits on every remote seat; if it has not landed on White itself, Arnold copies/recreates from any seat — byte-exactness is pinned by md5 either way.
- Structural fact pinning down the chain wording: **per-seat `uploads/` directories are NOT mirrored** (P1 uploads-mirror unshipped; mirror is push-only White→remotes for SYNC_FILES only). My Black `uploads/` = N=1 canary (re-verified this round), but that inventory never reaches White on its own. Researcher r26's "relay leg still outstanding / probe would FAIL" read was his seat's local 3-entry uploads/ — true of HIS seat, not a verdict on White.
- **Therefore Arnold's console step "place canary" remains REQUIRED for probe N=1**: copy the byte-exact source (now at `memory/verifier/_canary_remote.txt` on every seat after one mirror window; pin 512d0dc8 full) into White's local `uploads/`, ensuring White `uploads/` ends with exactly ONE entry.

## 3. AC-A2-2 LIVE — state unchanged, all agent-side preconditions met
| item | state |
|---|---|
| canary artifact byte-exact (212 B / 512d0dc8e96773b7db5574da4f0ae9f3) | ✓ uploads/ on Black + memory/verifier/ relay (new, propagating) |
| probe `memory/mechanic/ac_a2_live_leg_r20.py` byte-exact (2,341 B / 46f529dde45b21276be49a6ce1bd8e15) | ✓ re-verified this round |
| `ac_a2_live_leg_r20_result.json` anywhere on shared tree | **ABSENT** (full-tree walk, 04:5x) → Arnold's probe exec not yet landed |
| expected verdict values (unchanged) | [1] N=1 row (`uploads/_canary_remote.txt`, 212); [2] raw 200 + exactly 212 B, md5 = 512d0dc8 full pin; [3] console clean per Designer r20 criteria (zero red errors; exactly 1 network request after ≥15 s with all panels closed) |

## 4. Lane status — Verifier lane DRAINED
- AC-A2-1 (incl. outside-click clause, Designer ruling), AC-A2-2 static, AC-A2-3, AC-A2-4: CLOSED with evidence (chain: ac-a2-r19.md → reverify → closure-r19 → final-state-r20).
- AC-A2-2 LIVE: every agent-executable precondition is met and pinned. Sole surviving items are Arnold's White-console human legs: (a) place canary → White `uploads/` N=1; (b) `python memory\mechanic\ac_a2_live_leg_r20.py` → result JSON propagates for my acceptance; (c) devtools console-clean pass per Designer r20 (screenshot/text capture as NEW shared file). When (b)+(c) land with the expected values, I accept and the whole AC-A2 gate closes — no further Verifier work owed before then.
- Unreachable-from-any-agent-seat (re-proven this round): White :8099/:8888 egress (timeout from Black; sandbox loopback 10013); White process table (credential-blocked); browser/devtools + node runtime on this seat (node absent — JS remains statically reviewed only). Z: on Black = self-mirror of the Black shared folder (lists files created seconds before the read) — NOT a White view; do not cite it as propagation evidence.

[CONCLUDED] Verifier lane. Owner: Verifier. Basis: md5 recompute + uploads walk + full-tree result-JSON scan at 04:52:43 Black seat; Builder r25 rollback leaf + Researcher r26 convergence check read on disk.
