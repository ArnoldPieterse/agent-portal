# Scribe synthesis — queue ④ source-loss adjudication (recorded 2026-11-14 ~03:3x, Red seat)

Round record for the auto-continue sweep; extends 2026-11-13-r16c-mechanic-bundle-landed.md. Canonical state leaf remains memory/synthesis/2026-11-12-consolidated-state.md (5,477 B / 06611885).

## Finding — the "Red master" is gone from every reachable surface, not merely unreachable
Queue ④'s stated source = Scribe Red master of memory/scribe/ops-r6-synthesis-2026-11-13.md at 10,272 B / md5 13c97dfb (TODO.md lines 16/28/39/42; r15-r16 leaf decision 4). First-hand check from the seat that owned it:
- My sandbox copy of ops-r6-synthesis-2026-11-13.md = **4,281 B / c717497f** — byte-identical to the stale White copy (TODO line 38), NOT the 10,272 B master.
- Full tree scan of my seat: **no file of size 10,272 B anywhere**; no backup named with 13c97dfb; the string appears only in prose references (TODO.md + later leaves).
- Z:\ recorded stale 4,281 B copy at r16 time (TODO line 28); White = 4,281 B / c717497f.

## Content coverage — nothing is actually lost
The claimed master = stale leaf body + the r14 FINAL STATE append I claimed in r14 (which never landed on White; TODO line 52). Both parts are on White:
| part | where on White | pin |
|---|---|---|
| OPS r5/r6 body (decisions 1–5, F1–F4 flags) | memory/scribe/ops-r6-synthesis-2026-11-13.md | 4,281 B / c717497f |
| r14 FINAL STATE | consolidated-state.md section "r14 FINAL STATE" (reconstructed by Orchestrator r14c from the thread) | leaf 5,477 B / 06611885 |

## Adjudication — queue ④ closes as SOURCE-LOST / CONTENT-COVERED
- No byte-exact rebuild from 13c97dfb is possible (source absent from every reachable surface) or needed (all content present per table above).
- **SUPERSEDED mark on ops-r6 NOT applied**: its body is not subsumed by canonical — it is the sole record of OPS r5/r6 decisions + flags F1–F4. The r15-r16 decision 4 SUPERSEDED step was conditional on a rebuild that can no longer happen; this leaf supersedes that step only.
- **Contradiction flagged, not silently resolved**: TODO lines 28/39/42 and the r15-r16 leaf treat 13c97dfb as an existing artifact to pull/relay; first-hand verification from its owning seat shows it does not exist there. No other agent ever independently measured the master on disk — all references trace to my r14 claim, consistent with anomaly A-R14's "mangled-call candidate" pattern (canonical leaf). If a copy exists on Red host disk outside my sandbox, only Arnold/Mechanic console access could confirm; that is no longer blocking.

## Why this new file will reach White
New-file propagation is live: Researcher's memory/researcher/farm-relpath-diagnosis-2026-11-14.md (4,580 B) already landed in my seat this round via the mirror — same mechanism carries this leaf.

## One-shot owed at White (Orchestrator, then tick)
1. TODO.md: reword queue ④ lines 16/28/39/42 from "rebuild from 13c97dfb" to "CLOSED — source lost, content covered (see 2026-11-14-queue4-source-loss-adjudication.md)".
2. memory/synthesis/INDEX.md: add pointer line for this leaf (my own INDEX edit is LWW-unreliable per TODO line 20; do not depend on it).

## Open items after this leaf — all already owned, none Scribe's
- Mechanic: live proxy/browser pass on PID 23704 (HTTP 200 + 212 B canary compare, console clean) = sole gate before AC-A2 fully closed.
- Orchestrator/Designer: token-lock scope adjudication (live dark family vs r60 locked light tokens — migrate page or re-scope lock to mocks); outside-click house-style sign-off (Designer ruled ACCEPT THE VARIANT in memory/designer/ac-a2-1-ruling.md; Verifier concurs).
- Builder: farm.py fix per Researcher's diagnosis (minimal gate lines 569+668, shared rel_display() helper) → Verifier re-run.
- Human/Arnold: dcabots re-prompt, E14 White-console run, arnold-restart ps1 leg(s).
