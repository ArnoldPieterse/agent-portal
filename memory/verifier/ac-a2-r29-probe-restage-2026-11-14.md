# AC-A2 r29 — Verifier auto-continue sweep + probe restage (Black seat, 2026-11-14 ~05:5x)
Supersedes nothing; extends `r28-probe-check1-ratification.md` (amended semantics stand). All evidence first-party, this seat.

## 1. Sweep (full-tree walk, this round)
- `ac_a2_live_leg_r20_result.json`: **STILL ABSENT** fleet-wide → Arnold's probe exec has not landed. No console-clean capture file either. AC-A2-2 LIVE gate unchanged.
- Pins HOLD vs r26 record: index.html = 9c6b08e3d98355e632a72cb871d5b60d / 67,681 B (stable on Black; Researcher's 8ef4e222 seat-read is the known cross-seat oscillation — both variants carry filesPanel x4 / /api/uploads x3, AC-A2 unaffected); agent_portal.py = 1b86880c / 80,056 B; memory_mirror.py = e5c4a229 / 10,668 B; canary = 512d0dc8e96773b7db5574da4f0ae9f3 / 212 B (uploads/ + memory/verifier/ relay both byte-exact).
- Seat = Black; loopback :8099 sandbox-refused (allowlist), White process table credential-blocked — relay path stands, re-proven.

## 2. NEW FINDING — my r28 in-place probe edit was mirror-rolled-back
- Shared root `memory/mechanic/ac_a2_live_leg_r20.py` reverted to original **46f529dde45b21276be49a6ce1bd8e15 / 2,341 B** (strict N=1 check[1]). Fourth documented instance of the existing-file-edit rollback pattern. Consequence: running r20 as-is on an UNcleaned White uploads/ (~5,379 files) would deterministically FAIL check[1] — a wasted console round.
- **Restaged as NEW file (new files propagate; edits don't): `memory/mechanic/ac_a2_live_leg_r21.py` = 4,181 B / md5 93033c2f6ff8b6e8f39b2caaf69d530c.** Amended check[1] = 200 + canary row ('uploads/_canary_remote.txt', 212) present, N≥1 (recursive walk semantics per r28 ruling); check[2] tightened to full pin 512d0dc8…; writes `ac_a2_live_leg_r21_result.json`. Verified this seat: py_compile OK + **selftest PASS 6/6** (canary pin checked against the actual on-disk artifact, not a hardcode; 5 verdict cases incl. adversarial).

## 3. Final pass condition (acceptance contract)
| leg | PASS = |
|---|---|
| [1] probe uploads_list | status 200 AND ('uploads/_canary_remote.txt', 212) in rows — N≥1, no destructive clean required |
| [2] probe raw_fetch | status 200 + exactly 212 B + md5 512d0dc8e96773b7db5574da4f0ae9f3 |
| [3] console-clean | per memory/designer/ac-a2-2-console-clean-criteria.md (zero red errors; exactly 1 network request after ≥15 s, all panels closed); capture saved as a NEW shared file |

## 4. Arnold's White-console legs (sole remaining work for the whole AC-A2 gate)
(a) place canary: copy `memory/verifier/_canary_remote.txt` (pin 512d0dc8 full) to White `uploads/_canary_remote.txt` — NO move/remove of the pre-existing uploads/ entries (r28 data-loss ruling); (b) run `python memory\mechanic\ac_a2_live_leg_r21.py` (**NOT r20**); (c) devtools console-clean pass → capture as new shared file.

## 5. Flag for Orchestrator
TODO's "ensure uploads/ ends with exactly ONE entry" spec contradicts Verifier r28 (rejected destructive clean of ~5,379 files incl. un-mirrored git bundle). Update the spec to "canary present, N≥1" or explicitly re-ratify destructive clean — I will REJECT acceptance under a clean that destroys non-mirrored artifacts.

## 6. Lane state
AC-A2-1 / AC-A2-2 static / AC-A2-3 / AC-A2-4: CLOSED (chain r19 → reverify → closure-r19 → final-state-r20). AC-A2-2 LIVE: all agent-side preconditions met and pinned; when legs (b)+(c) land with the values in §3 I accept in one step and the gate closes. No further Verifier work owed before then.

[CONCLUDED] Verifier lane for this round. Owner: Verifier.
