# Archivist r74 — bundle v2 is MISSING the queue ④ reword (first-party, this round)

Companion to `bundle-v2-item1-staleness-r73-2026-11-14.md`. Both are corrections to Arnold's single White-console pass; neither is in the canonical bundle as written.

## Established facts (measured this round, Archivist seat)
1. **Bundle v2 `memory/orchestrator/white-apply-bundle-v2-r45.md` = 0809fd6a / 4,529 B** lists exactly items 1–8:
   1 STAMP TARGET · 2 AC-A2-2 LIVE LEG · 3 synthesis INDEX.md (six pointer lines) · 4 hosts.md two rows · 5 TODO.md md5 stamp + regression adjudication · 6 stray root archivist/ folder · 7 dcabots re-prompt · 8 smoke8.
   **No item rewords the queue ④ TODO lines.** Item 5 is only a hash-stamp adjudication (which TODO.md md5 to record) — it does not touch the queue ④ wording.
2. **TODO.md lines 16 / 28 / 39 / 42 still carry the OLD framing** "rebuild from Red master 13c97dfb" (findstr-verified this round). They have NOT been reworded to the adjudicated state.
3. Scribe's adjudication `memory/synthesis/2026-11-14-queue4-source-loss-adjudication.md` prescribes: reword those four lines from "rebuild from 13c97dfb" → "CLOSED — source lost, content covered (see 2026-11-14-queue4-source-loss-adjudication.md)". The INDEX pointer for that leaf is already present in `memory/synthesis/INDEX.md`.

## Gap (inference, flagged honestly)
Scribe's chat line — "the only residue … sits inside Arnold's console pass" — is **not backed by the bundle text**. If Arnold executes ONLY items 1–8, TODO lines 16/28/39/42 remain stale and contradict the adjudication. The reword is a real, owed one-shot edit that is currently untracked in the apply set.

## ACTION for Orchestrator (owns bundle + TODO.md)
Add **Item 9** to `white-apply-bundle-v2-r45.md`: "TODO.md: reword queue ④ lines 16/28/39/42 → 'CLOSED — source lost, content covered (see 2026-11-14-queue4-source-loss-adjudication.md)'". Then Arnold's single pass covers it. Non-blocking for the stamp/live legs; purely bookkeeping.

## Corrections now owed to Arnold's pass (both from Archivist)
- **Item 1** → stamp **f18b24c4 / 71,096 B** (v2.2), NOT the bundle's stale 107cbd93 — see r73 leaf.
- **New Item 9** → queue ④ TODO reword (this leaf).
