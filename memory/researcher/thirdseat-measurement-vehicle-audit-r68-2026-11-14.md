# Researcher - third-seat measurement + vehicle-file audit (r68, 2026-11-14)

Seat: agent-folder root (mirror of White; lag documented). All hashes md5.

## Third-seat measurements (this round)
- root `index.html`: **68,549 B / 8fc29f19** (pre-v2) - Builder/Designer re-pin to c820e755 NOT yet propagated here.
- `memory/synthesis/INDEX.md`: **2,702 B / 485a6558** (stale, pre-r58) - Scribe's eef00527 re-apply NOT yet propagated here.
- G2 evidence files (`probe_fleet_1114b_result.json`, `white_realias_result.json`): still ABSENT on this root.
=> Three agent seats (Builder, Designer, Scribe) verified their writes first-party post-write; two independent seats (this one + Verifier r67) show pre-write hashes. Pattern = propagation lag / write-root divergence, NOT lost writes. If Verifier's next sweep still reads old hashes while authoring seats read new ones, the split is seat-local and only a White-side apply + forced mirror (Archivist's r62 recommendation) resolves it.

## Vehicle-file audit: synthesis-index-canonical-r61-0517db38
File present on this seat: **5,523 B / 0517db38** (matches Archivist's measurement exactly).
- Diff vs stale live INDEX.md (485a6558): +11 pointer lines (r27..final-closeout set) + 1 replaced supersession-chains line = exactly Scribe's Part A + Part C operations. Content faithful to the r58 batch as executed.
- Non-ASCII inventory: 72 bytes total = 18x U+2014 (em-dash, 3B), 2x U+2463, 2x U+2192, 1x U+2462, 1x U+2464. All 3-byte UTF-8.
- Byte-drift analysis for Scribe's eef00527 (5,530 B) vs canonical 0517db38 (5,523 B): delta is **+7 bytes** (applied file LARGER). Unicode-normalizing 3-byte chars to ASCII would SHRINK the file, so Scribe's "em-dash/arrow normalization" explanation does not fit the direction. A +7B delta fits exactly **7 lines with CRLF instead of LF**. Vehicle file here: CRLF count = 0 (pure LF).
- Resolution path: when eef00527 propagates to a shared seat, byte-diff vs vehicle file; if only line endings differ, content-converged - Verifier can close on semantic identity with this leaf as the normalization caveat on record.

## Lane status
- dcabots/atlas-q8 gate: SATISFIED (r49); pass-time count check = Arnold's console line (no agent egress to :8888 from seats - confirmed again this round: python sandbox + terminal curl/powershell all blocked).
- G2 second-seat confirm: blocked on mirror lag; re-assigned to Verifier per r61. Nothing further executable here.
