# AC-A2 r30 — Verifier: probe drift adjudicated, canonical probe designated (Black seat, 2026-11-14 ~05:5x)
Supersedes the "r20 edited in place / pin 803c6473" Applied section of `r28-probe-check1-ratification.md` ONLY. All r28 rulings stand (N≥1 semantics ratified; option (b) destructive-clean rejected). Evidence = first-party bytes this round.

## 1. PROBE DRIFT — three variants now on record for ac_a2_live_leg_r20.py
| variant | size / md5 | status |
|---|---|---|
| Mechanic r20 original (strict N=1) | 2,341 B / 46f529dde45b21276be49a6ce1bd8e15 | SUPERSEDED (pins: Mechanic white-rename-closeout; my r26 leaf) |
| my r28 in-place edit (check[1] amended + check[2] md5-tightened) | 2,822 B / 803c6473f3262b02499c1abdd6dee705 | NO LONGER ON DISK — provenance of replacement unresolvable from agent seats (White disk unreachable; existing-file edits LWW-fragile per r25 precedent) |
| current on-disk r20.py (mtime 05:12) | 2,344 B / e0327c726d5f83816972bb566a2b9a20 | INTERMEDIATE VARIANT: check[1] amended to N≥1 canary-present (expect string cites "per r27"), but check[2] still byte-count only, NO md5 pin. **NOT CANONICAL — do not run.** |

## 2. CANONICAL PROBE DESIGNATED — ac_a2_live_leg_r21.py
- `memory/mechanic/ac_a2_live_leg_r21.py` = **4,181 B / md5 93033c2f6ff8b6e8f39b2caaf69d530c** (LF), docstring: "Verifier r29 restage… supersedes ac_a2_live_leg_r20.py semantics per Verifier ruling memory/verifier/r28-probe-check1-ratification.md" (ruling verified present on disk this round — citation chain intact).
- Semantics = my r28 ratification exactly: [1] PASS = 200 AND ('uploads/_canary_remote.txt', 212) in rows (N≥1); [2] PASS = 200 AND exactly 212 B AND md5 == 512d0dc8e96773b7db5574da4f0ae9f3 (full pin); [3] console-clean leg out of scope (browser/devtools).
- **First-party selftest this round: `python memory\mechanic\ac_a2_live_leg_r21.py --selftest` → "SELFTEST PASS: 6/6 assertions (canary pin + 5 verdict cases)"** — offline, no network; canary pin self-check reads the on-disk artifact and matches.
- Writes `ac_a2_live_leg_r21_result.json` next to itself. New file → propagates White-bound per refined line; if not present on White at run time, hand-copy from any seat and verify md5 93033c2f6ff8b6e8f39b2caaf69d530c / 4,181 B first.

## 3. PRECONDITIONS — re-verified this round (all agent-side items still met)
- canary source `memory/verifier/_canary_remote.txt` = 212 B / 512d0dc8e96773b7db5574da4f0ae9f3 ✓; Black seat uploads/ N=1 same pin ✓.
- result JSONs (`ac_a2_live_leg_r20_result.json` / `ac_a2_live_leg_r21_result.json`): full-tree walk = ABSENT → Arnold's probe exec still not landed.
- console-clean capture: absent (only Designer criteria file) → leg (c) not landed.

## 4. ACCEPTANCE CRITERIA — restated, unchanged in substance
When BOTH land: (a) `ac_a2_live_leg_r21_result.json` with verdict PASS (checks per §2); (b) devtools console-clean evidence per `memory/designer/ac-a2-2-console-clean-criteria.md` (zero red errors; exactly 1 /api/uploads request after ≥15 s with all panels closed), captured as a NEW shared file → **I accept in one step and AC-A2-2 LIVE closes.**
Arnold console legs (updated): (1) place canary source into White uploads/ (existence suffices per r28 — N=1 moot); (2) run r21, not r20; (3) devtools pass + capture.

## Lane state
AC-A2-1 / 2-static / 3 / 4: CLOSED (r19→r26 chain). AC-A2-2 LIVE: every agent-executable precondition met and pinned; sole survivors = Arnold's three White-console human legs. No further Verifier work owed before (a)+(b) land.

[CONCLUDED] Verifier lane. Owner: Verifier. Basis: certutil md5 recompute of all four probe/canary artifacts + full-tree result-JSON scan + first-party r21 selftest at 05:5x Black seat; r28 ruling read on disk.
