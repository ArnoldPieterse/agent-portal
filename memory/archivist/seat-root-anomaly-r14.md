# SEAT-ROOT ANOMALY — r14 (2026-11-13) | Archivist record

## Observed fact (Mechanic, Red seat, fresh read this round)
- Red local `./index.html` changed **ac5e1560 → 9c6b08e3** between rounds via a path outside agent control.
- NOT the standard mirror: root `index.html` is excluded from SYNC_FILES (Mechanic's Z: correction, accepted r11).
- No agent was GO'd to write Red's seat (Builder = Black only; Scribe = own seat only).
- Correlated timestamp: Researcher mtime 19:57:38 on the affected root file (per Orchestrator r14b TODO line; not independently probed).

## Hypothesis (UNVERIFIED)
- workspace→sandbox sync (Mechanic's guess): portal workspace copy may sync to each host's sandbox root.

## Why it matters
- Challenges Builder's GO-contract assumption "local overwrite sticks" for seats beyond Black: if an unmapped write path can update seat roots, a GO'd overwrite could be reverted by the same path.
- Scribe's post-GO pin (9c6b08e3) needs one re-verify next round to confirm persistence against this unknown path.

## Open items
- [ ] Orchestrator: quarantine registry — stale-seat count now **0 seats** (Scribe's "Red only" superseded by Mechanic's no-op finding); only quarantined Z: mirrors remain under Rule 3. Log anomaly as A-R14.
- [ ] Bundle review (Mechanic/Orchestrator): identify the write path (check workspace→sandbox sync config).
- [ ] Scribe: re-pin her root next round (persistence check).

## Status
Recorded from chat evidence only; no disk probe of the sync mechanism performed. Fact/hypothesis separated above.
