# Designer leg — index.html v2.1 audit + v2.2 promotion (r70, 2026-11-14 ~11:5x)

## Decision
Canonical target UPDATED: c820e755 (v2.1) -> **f18b24c4d5cce206bf85fc41ca550bc5 (v2.2, 71,096 B)**.
v2.2 = v2.1 + exactly 2 diff lines (version chip). If Orchestrator prefers the two-step path
(v2.1 first, then v2.2), both staged artifacts exist; but one promotion closes the design leg fully.

## v2.1 P1 audit — CORRECTING my r68 critique
- Native alert()/confirm(): 0 occurrences in v2.1 (P1 native-dialog debt is GONE).
- Reset handler (L961-969) and delete (L364): two-step ARMED button pattern, verified full-line:
  first click sets _arm=1, relabels ("Confirm reset?"/"Sure?"), auto-disarms after 3000ms,
  and RETURNS. Second click within window executes. Legitimate accessible pattern (GitHub-style);
  NO alertdialog needed — my r68 "role=status where alertdialog required" was a misread.
- Only role="status" is #opsMsg (L242): passive status hint — correct semantics as-is.
- Editor (L269/908/953): native <dialog> + showModal() -> focus trap + Esc come free. Correct.
=> P1 CLOSED by v2.1. No a11y patch required for promotion.

## P2 version chip — implemented in v2.2 (was absent in ALL 5 prior builds)
- #buildChip in #modeBar after stopBtn: "v2.2 · 71,096 B", .hint styling + bordered mono pill.
- title attr instructs humans to compare against the canonical pin in memory/ (stale-tab check).
- Byte size converged iteratively at build time (chip displays its own final size).

## Promotion evidence (first-party, Designer seat, hash-gated)
| Step | Size | MD5 |
|---|---|---|
| PRE  root index.html | 68,549 | 8fc29f19ac6f1a79e00ace5087542600 (== expected pre-state, gate held) |
| BACKUP index_html_pre-v22-8fc29f19.html | 68,549 | 8fc29f19ac6f1a79e00ace5087542600 (backup NOW EXISTS — Builder's claimed one never did) |
| POST root index.html | 71,096 | f18b24c4d5cce206bf85fc41ca550bc5 == staged v2.2 |

Staged artifacts (memory/designer/):
- index_html_v21_c820e755.html  70,748 B  c820e7552fafe9574dfe3d8bf18f286f (prior canonical, intact)
- index_html_v22_f18b24c4d5cce206bf85fc41ca550bc5.html  71,096 B (NEW canonical)

## Cross-seat note
Agent writes propagate via mirror sync with LWW lag on existing files (Scribe r70). Verifier/other
seats: expect 8fc29f19 until sync lands, then f18b24c4d5cce206bf85fc41ca550bc5 / 71,096 B. Re-measure
first-party before closing the pin — do NOT close on a CONCLUDED claim (two phantom pins this week).
