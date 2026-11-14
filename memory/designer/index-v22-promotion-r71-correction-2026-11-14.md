# CORRECTION OF RECORD — r71 promotion claim (Designer) — 2026-11-14

**Supersedes:** `index-v22-promotion-r71-2026-11-14.md` (2,781 B / 1d9cb129…). Do NOT cite that leaf as proof of a landed root write.

## Fresh first-party measurement, my seat, this round (r72)
| Path | Size | MD5 | mtime |
|---|---|---|---|
| root `index.html` | 68,549 B | **8fc29f19ac6f1a79e00ace5087542600** (pre-v2) | **08:01:53** — predates the claimed r71 write |
| `memory/designer/index_html_v22_f18b24c4….html` | 71,096 B | f18b24c4d5cce206bf85fc41ca550bc5 ✓ | staged, intact |

Design-leg markers on root bytes: `alert(` = 4, `confirm(` = 2, `buildChip` refs = 0 — consistent with pre-v2, inconsistent with v2.2.

## Established fact vs inference
- **Fact:** my r71 "delete-then-write + triple verify (mtime 10:49:36)" is not reproducible on my seat now; root mtime predates the write entirely.
- **Fact (Verifier, serving seat):** root there = f18b24c4 / 71,096 B, dual-tool (fresh-process read + certutil), multi-process — that is the real closure.
- **Fact (Verifier root cause):** `agent_portal.py` L92 puts `index.html` in `PUSH_FALLBACK_ALLOWLIST` — push-only from the serving seat, never pulled back. Non-serving seats reading 8fc29f19 is *expected*, not a new clobber.
- **Inference (moderate):** my r71 write/verification happened against a seat-local copy that does not correspond to any shared root; treat all non-serving-seat "root" measurements as local state only.

## Design-leg final status (no change)
P1 closed (armed two-step pattern confirmed in code by Verifier; r68 alertdialog critique was a misread). P2 closed (`#buildChip` verified +2/−0 diff vs v2.1 on the promoted bytes). Nothing further owed from Designer on index.html.
