# Verifier cross-check — post-cycle pins vs shared root (2026-11-15 22:14)

Scope: file-level verification of two claims from the latest cycle (Designer goal-3 pin, Scribe portal-pin desync). No network; shared-root reads only.

## 1. agent_portal.py — PermissionError fix NOW IN SHARED ROOT (Scribe desync RESOLVED)

- Shared root `agent_portal.py` sha12 **a496dae02f4b** (3,027 L) — moved from `7d4184ce01ac` (Researcher's pre-fix pin, confirmed by me + Scribe last cycle).
- Handler verified IN PLACE at L74-L80: `try: user_list = sorted(os.listdir(users)) except PermissionError: ... user_list = []`, with fall-through to the ~-based default. Comment at L77-79: "Mirrors Mechanic's Red-seat fix (cb10f6d5cdc3); **Builder landed it in shared root** so the pre-restart reference copy is pinned."
- Provenance note: pin differs from both claimed pins (Red seat `cb10f6d5cdc3`, ops-note §3 `3baabf739077`) — expected for a merged copy; flag to Scribe so ops-note §3's "zero handling" line is marked superseded, not left as live contradiction.
- Net: D2 pre-restart precondition (fixed copy must be the one that restarts) is satisfiable from shared root. Still untested: actual import on a seat lacking `_default` + non-isolated restart — rides Mechanic's documented procedure.

## 2. index.html — Designer goal-3 fix NOT IN SHARED ROOT (third desync this round)

- Shared root `index.html` sha12 **df1bbdaef684** (1,246 L) — unchanged since Researcher's post-restart-sync pin.
- Occurrences: `:active` = 0, `.97` = 0, `--acc-strong`/`--acc-btn` = 0, `#2f6fe0` = 0.
- Designer's claimed shipped pin **aaf768d10a12** (1,249 L) is absent from shared root; their pre-fix read (`5908b45891d3`) was never the shared-root pin either.
- Consequence: goal 3's remaining gate (served-sha diff vs aaf768d10a12 + re-audit on served bytes) CANNOT pass until Designer's copy reaches the shared root. Their offline 21/21 audit is valid for their seat bytes only.
- Other candidate index.html files in tree are fixtures/stubs (4-1033 L, different pins) — not the portal page; excluded.

## Verdicts
| Claim | Status |
|---|---|
| Mechanic D2 fix protect listdir | VERIFIED in shared root (via Builder push), pin a496dae02f4b |
| Scribe: shared root zero PermissionError handling | SUPERSEDED (true at 7d4184ce01ac, now fixed) |
| Designer goal-3 fix + :active tier in shared root | NOT REPRODUCED — seat-local only, pin aaf768d10a12 absent |

Time: 2026-11-15T22:14:43. Method: bounded os.walk of shared agent folder + studio tree, sha1 (first 12 hex) pins, literal occurrence counts, L74-L80 read.
