# Researcher r75 — stamp-target correction CONFIRMED first-party (supersedes my r69 item-1 line)

Seat: agent-folder root (mirror of White). Method: python hashlib + raw-byte marker counts, both candidate files read locally. Auto-continue 3/3 fresh sweep.

## Why this leaf exists
My r69 `white-pass-crosscheck` leaf recorded the bundle item-1 stamp target `index_html_stamp_final_107cbd93.html` (107cbd93 / 69,888 B) as byte-exact and "matches bundle item-1 pin exactly." That was true at r69. Archivist r73 + Verifier r74 final-gate-manifest then flagged that **item-1 itself is now STALE**: the live target moved to v2.2 `f18b24c4` / 71,096 B, and stamping 107cbd93 verbatim regresses P2 (`#buildChip`). I had not re-measured against that correction — doing so now.

## FIRST-PARTY marker diff (this seat, raw bytes)
| file | size | #buildChip | #filesBtn | #filesPanel | linkifyFiles | /api/uploads |
|---|---|---|---|---|---|---|
| 107cbd93 (OLD item-1) | 69,888 B | **0** | 3 | 2 | 6 | 3 |
| f18b24c4 (v2.2 LIVE)   | 71,096 B | **1** | 3 | 2 | 6 | 3 |

=> `#buildChip` = 0 in 107cbd93, 1 in f18b24c4; all other markers identical. Independently re-derives Archivist r73's marker diff on my own seat. **Stamping 107cbd93 regresses P2 and fails Verifier's post-apply re-sweep.**

## Implication for the sole human gate (Arnold)
- Correct step-1 target = `memory/designer/index_html_v22_f18b24c4d5cce206bf85fc41ca550bc5.html` (**f18b24c4 / 71,096 B**), NOT the stale bundle item-1 107cbd93. Matches Verifier r74 manifest step 1 exactly.
- Bundle v2 file `white-apply-bundle-v2-r45.md` still pins 107cbd93 in item-1 (I re-measured: bundle md5 0809fd6a / 4,529 B unchanged) — so the on-disk bundle text is NOT self-correcting; the r73/r74 correction lives only in those leaves + this one. If Arnold works strictly from the bundle file, step-1 will use the wrong target.

## Fresh sweep, same round (context)
- Console artifacts `white_realias_result.json` / `ac_a2_live_leg_r20|21_result.json` / `probe_fleet_1114b_result.json`: **ALL ABSENT tree-wide** — no new ground truth; second-seat confirm still not possible from here (egress-blocked, consistent with r30/r71).
- Seat pins: index.html 8fc29f19/68,549 B (pre-v2), agents.json 2d5433db/9,559 B (stale variant), synthesis INDEX 485a6558/2,702 B (pre-r61). All unchanged = propagation lag, not lost writes.

## Conclusion / confidence
- **High** confidence in the marker diff + "item-1 stale" correction (raw-byte re-measure this seat, independently matches Archivist r73).
- Sole gate remains human-owned: stamp f18b24c4 (NOT 107cbd93) + Scribe INDEX apply + queue④ reword + dcabots re-prompt + smoke8. Nothing agent-executable from this seat.

Owner: Researcher. Basis: hashlib + marker counts, Researcher root; cross-cites Archivist r73 + Verifier r74 (independent same-result).