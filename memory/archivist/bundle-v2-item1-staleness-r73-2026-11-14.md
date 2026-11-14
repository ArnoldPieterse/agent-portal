# Archivist r73 — bundle v2 item 1 STALE vs live target v2.2 (first-party, this round)

Seat: Archivist shared-agent root. Method: python hashlib + marker counts on raw bytes, both artifacts read locally.
Supersedes nothing; ADDENDUM to `memory/orchestrator/white-apply-bundle-v2-r45.md` (r55 re-pin) and `memory/synthesis/2026-11-14-final-closeout.md` — new file so it propagates per the r72 transport rule (existing-file edits from agent seats do NOT reach White).

## ESTABLISHED (tool-verified this round)
1. Both stamp candidates present byte-exact on my seat:
   - `memory/designer/index_html_stamp_final_107cbd93.html` = **107cbd9357c85d209c76590bc4101d58 / 69,888 B** (bundle item 1 target)
   - `memory/designer/index_html_v22_f18b24c4d5cce206bf85fc41ca550bc5.html` = **f18b24c4d5cce206bf85fc41ca550bc5 / 71,096 B** (live target per Verifier r71b + Designer r72)
2. Marker diff (raw-byte counts): `#buildChip` = **0 in 107cbd93, 1 in f18b24c4**; all other markers identical (`#filesBtn` 3/3, `#filesPanel` 2/2, `linkifyFiles` 6/6, `/api/uploads` 3/3).
   → v2.2 = bundle stamp + P2 buildChip fix; strictly newer on the design leg. **Stamping 107cbd93 verbatim regresses P2 and fails Verifier's post-apply re-sweep against v2.2 markers.**

## CORRECTION OF RECORD (inter-agent discrepancy)
3. Designer's r72 correction leaf cites "Fact (Verifier, serving seat): root there = f18b24c4 … that is the real closure." Verifier's own latest sweep (r71b) states their seat is **Black**, still 8fc29f19/68,549 B, and explicitly retracts the r70 dual-tool PASS as ephemeral ("clobbered by the next sync, corrected in r71"); the live leg (served-bytes vs disk on PID 23704) is egress-blocked from every agent seat. Three first-party seats measured 8fc29f19 @ mtime 08:01 this round (Verifier/Black, Archivist, Researcher). Per my r72 transport rule (E), an agent-seat write to root index.html cannot reach White.
   → **No agent has verified White's root/served state.** "Landed on serving seat" is unsupported; treat the gate as OPEN until Arnold's pass propagates. Designer's P1/P2 closures hold against the STAGED v2.2 bytes (buildChip confirmed present there), not against the served root.

## ACTION for Arnold's single pass (supersedes bundle item 1 + closeout stamp line)
- Stamp target: **f18b24c4 / 71,096 B** from `memory/designer/index_html_v22_f18b24c4d5cce206bf85fc41ca550bc5.html` (NOT 107cbd93).
- All other bundle items 2–8 unchanged. Post-op re-measure: Verifier + Archivist, both seats (per my r72 section F).

## Unchanged from prior rounds
- My F1 (`f1-index-patch-20261113.md`), F2 (`fleet-md5-discrepancy-note-20261113.md`) and ops/INDEX git-hygiene line remain STAGED and are NOT inside bundle items 1–8 → separate batch, no action owed this round.
