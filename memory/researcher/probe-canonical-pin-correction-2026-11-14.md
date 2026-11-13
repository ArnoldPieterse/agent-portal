# Researcher — probe canonical pin CORRECTION (2026-11-14, auto-continue 3/3)
Supersedes ONLY my last-round chat pin of `ac_a2_live_leg_r20.py` = e0327c72 as "the amended probe." My r27 SEMANTIC ruling (option (b): N>=1 canary-present) is UNCHANGED and stands. Evidence = first-party bytes + selftest from Researcher seat this round.

## 1. THE MISTAKE I AM CORRECTING
Last round I stated: "I re-pinned the amended probe script... `ac_a2_live_leg_r20.py` = 2,344 B / e0327c72... ✓". That byte-match was TRUE but the LABEL was WRONG. Per Verifier r30 (`memory/verifier/r30-probe-drift-adjudication-2026-11-14.md`, 3,793 B / d03d62d5), e0327c72 is the **INTERMEDIATE VARIANT — do not run** (check[1] amended to N>=1, but check[2] still byte-count only, NO md5 pin). I endorsed an un-runnable artifact. Correcting now.

## 2. FIRST-PARTY VERIFICATION OF THE CANONICAL PROBE (this seat)
- `memory/mechanic/ac_a2_live_leg_r21.py` = **4,181 B / md5 93033c2f6ff8b6e8f39b2caaf69d530c** (byte-exact; matches Verifier r30 designation).
- Content read this round: `CANARY = ("uploads/_canary_remote.txt", 212)`, `CANARY_MD5 = "512d0dc8e96773b7db5574da4f0ae9f3"`.
  - `check_uploads`: `pass = st == 200 and CANARY in rows` -> **N>=1 canary-present membership** = my r27 option (b) verbatim. NOT strict N=1. (My semantic ruling is what the canonical probe encodes.)
  - `check_raw`: `pass = st == 200 and len(body) == 212 and md5 == CANARY_MD5` -> full pin, tightened from prefix.
  - check[3] console-clean explicitly out of scope (browser/devtools leg).
- **Selftest run FROM THIS SEAT**: `python memory\mechanic\ac_a2_live_leg_r21.py --selftest` -> **"SELFTEST PASS: 6/6 assertions (canary pin + 5 verdict cases)"**. Independent corroboration of Verifier's Black-seat 6/6. Selftest reads the on-disk canary artifact and asserts its md5 == CANARY_MD5 (proves relayed canary byte-exact) + exercises 5 verdict cases.

## 3. THE INTERMEDIATE VARIANT CONFIRMED DO-NOT-RUN
- `memory/mechanic/ac_a2_live_leg_r20.py` on disk = **2,344 B / e0327c726d5f83816972bb566a2b9a20** (byte-match to Verifier r30 "intermediate variant"). Do NOT run this. Run r21.

## 4. SECONDARY STALENESS FLAG (not my deliverable)
My r27 leaf §3 pinned root `index.html` = 8ef4e222 / 67,681 B. A **second mirror rollback** since then reverted the workspace root to 9c6b08e3 (Builder + Designer both re-verified this round). Anyone citing r27 §3 for the current root pin is STALE. The actionable item is unchanged: one-line swap applied ON White canonical, then mirror propagates — owned by Builder/Arnold. I do not fix their lane; flagging only because my leaf carries that line.

## 5. STATE + SOLE SURVIVORS (re-verified this round)
- Result JSONs `ac_a2_live_leg_r20_result.json` / `_r21_result.json`: ABSENT (checked mechanic dir + root) -> Arnold's live leg still not landed.
- AC-A2-2 LIVE: every agent-executable precondition met and pinned by two seats now. Sole survivors = Arnold's three White-console human legs: (1) place canary source into White uploads/; (2) run **r21** (`python memory\mechanic\ac_a2_live_leg_r21.py`), NOT r20; (3) devtools console-clean capture per Designer criteria.

[CONCLUDED] Researcher pin corrected: canonical probe = r21 / 93033c2f (selftest 6/6 first-party); my r27 option-(b) semantics unchanged and are what r21 encodes. Nothing further executable from any agent seat.
