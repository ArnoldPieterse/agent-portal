# Verifier — A6B candidate diff + r21 staging audit (2026-11-14 ~07:09)

Trigger: Designer addressed Verifier by name (diff recon-C vs ec095107, pin the 8-byte delta); Mechanic claimed byte-exact root staging of r21 + canary; pre-run audit is Verifier's lane.

## 1. Candidate files — present on this seat, builder+verifier copies byte-identical
- `memory/builder/index_html_a6_b_candidate_ec095107236a9bdc.html` = `memory/verifier/...ec095107...html` — 69,707 B / md5 `ec095107236a9bdcf514baaf4e9b4abd` (both seats).
- `memory/builder/index_html_a6_b_a11y_candidate_ffa774230d8f354cbcdab640bd080b02.html` = verifier copy — 69,707 B / md5 `ffa774230d8f354cbcdab640bd080b02` (both seats). Confirms Orchestrator sweep #12 byte-identity claim first-party.

## 2. ec095107 vs ffa77423 — EXACT diff (whole-file, line-oriented)
One changed line only; zero net bytes (same length both):```.aev .at{color:#6b7688;flex:none;width:64px}   →   .aev .at{color:#8b93a7;flex:none;width:64px}```
⇒ **ffa77423 = ec095107 + Designer's r45 `.aev .at` contrast token, and nothing else.** The a11y stamp candidate is fully characterized.

## 3. Armed-resetBtn contrast fix — ABSENT from BOTH candidates
Token scan: `#33210a`=0, `_rb.style.color`=0 in ec095107 AND ffa77423 (var(--dim)=28 each). Designer's r46 finding stands: bundle apply set must carry TWO lines — `.aev .at`→#8b93a7 (already inside ffa77423) + `_rb.style.color="#33210a"` (owed; armed resetBtn 2.04:1 → 7.55:1).

## 4. Line-ending fact for Designer's −8 B question
Both candidates are **pure LF** (CRLF=0, LF-only=1,015 lines), incl. the confirm-handler region (LF-only 10 / CRLF 0). So if recon-C was also emitted LF (as claimed), the +8 B delta vs ec095107 is a pure text delta in one replacement region — NOT a CRLF/LF artifact. Exact pinning requires recon-C bytes.

## 5. Recon-C status
`memory/designer/a6b-recon-C-not-candidate-6be6a14d90fd.html` **ABSENT on this seat at 07:09:37** (designer dir listing shows fresh leaves through 06:56 only). Consistent with known per-seat propagation lag; diff owed, fires on arrival — then it is a ≤8 B region diff vs `ec095107` bytes already in tree.

## 6. Mechanic r21 staging audit (pre-run, mine)
- `uploads/_canary_remote.txt` at shared root: **PASS** 212 B / `512d0dc8e96773b7db5574da4f0ae9f3` — byte-exact as claimed.
- `ac_a2_live_leg_r21.py` at shared root: **ABSENT as of 07:09:37**. Full-tree hunt finds the canonical copy intact at `memory/mechanic/ac_a2_live_leg_r21.py` — 4,181 B / `93033c2f6ff8b6e8f39b2caaf69d530c` (pin exact). Root r20 also no longer present (only the drifted memory/mechanic copy, e0327c72/2,344 B — matches my prior sweep drift flag).
- Disposition: artifact exists byte-exact in-tree; Arnold's leg can run from `memory/mechanic/ac_a2_live_leg_r21.py` (offline selftest 6/6 proven on it by Mechanic + earlier by me). If the root copy appears via mirror, re-measure before run. No retyping risk either way.

## Verdict
- Stamped candidate ffa77423 fully diffed and characterized; bundle apply set = add armed-token fix only (`.aev .at` already inside).
- AC-A2 static closure unchanged: sole remaining item = Arnold's White-console legs (r21 run + canary + console-clean capture). No new agent-executable work created by this round.
