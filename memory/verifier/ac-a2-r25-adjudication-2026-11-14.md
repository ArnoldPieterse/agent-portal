# AC-A2 r25 adjudication — Verifier, Black seat (fresh disk sweep)
Date: 2026-11-14. Purpose: settle the base-hash + canary contradictions in Scribe's r24 leaf with first-hand bytes.

## RULING (byte-exact, this seat, this round)
1. **index.html shared root = `8ef4e2227a7afd506ed2b55dc9dd170d` / 67,681 B** (mtime 2026-11-14T04:37:23). This is the POST-swap WCAG-AA variant — **Builder's r24 re-stamp HAS propagated.**
   - Content gates PASS: `#6b7688` count = 0, `#8b93a7` count = 3, L140 = `.aev .at{color:#8b93a7;flex:none;width:64px}`, filesPanel x4, /api/uploads x3, ends `</html>`.
   - **Scribe flag A (base-hash contradiction) RESOLVED in Builder's favor.** My earlier r24 read of `9c6b08e3` was a pre-04:37 mirror-skew artifact. **Canonical base hash for the outside-click one-shot = `8ef4e222`** (unambiguous now).
   - Other index.html on disk are unrelated fixtures (portal-upgrade/fixture-known-good 12bbfa10, u4-test-app bd2f1119) — NOT canonical.
2. **Canary PRESENT, N=1**: `uploads/_canary_remote.txt` = 212 B / `512d0dc8e96773b7db5574da4f0ae9f3` (mtime 11-13 16:35), **sole entry in uploads/**. Scribe's "ABSENT at r24" was skew; my r24 report (canary present, N=1) RECONFIRMED.
3. **instances.md = 3,752 B / `d1c1d38e`** — aligned with Archivist's reconcile ruling (use d1c1d38e going forward). No action.
4. **hosts.md = 16,386 B / `9aef7fe1…2522`** — byte-exact to Verifier/Scribe/Orchestrator pins. Stable.
5. **Probe `memory/mechanic/ac_a2_live_leg_r20.py` = 2,341 B / `46f529dd`** — byte-exact. Result JSON ABSENT → live leg NOT yet run.

## AC-A2-2 LIVE status: ALL PRECONDITIONS MET (agent side)
- Canary relayed + N=1 re-pin verified against actual uploads/ inventory ✓
- Probe byte-exact, safe to exec (read-only two GETs vs 127.0.0.1:8099; pass = N=1 row + raw 200/exactly 212 B md5 `512d0dc8`) ✓
- WCAG-AA applied on shared root (`8ef4e222`) ✓
- **SOLE surviving item = Arnold's White-console human legs:** (a) `python memory\mechanic\ac_a2_live_leg_r20.py` → result JSON propagates for my acceptance; (b) console-clean devtools pass (my :8099 egress stays sandbox-refused — boundary holds).
- Portal *served* root on White still needs Arnold's local re-stamp confirmation (my writes reach shared folder only); base hash to match = `8ef4e222`.
