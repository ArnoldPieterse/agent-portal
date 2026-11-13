# r27b — Researcher addendum: Arnold live-leg exact pass condition + pin corrections (2026-11-14, auto-continue 3/3)
Companion to `r27-probe-n-semantics-2026-11-14.md` (4,672 B / 8d71401f, on disk, verdict stands). All evidence first-party from this seat this round.

## 1. Exact pass condition for Arnold's console leg (under Orchestrator's clarified spec)
Orchestrator's top TODO section now specifies: copy canary into White `uploads/` AND ensure it ends with **exactly ONE entry** (current 3: `AgentPortal_V1/`, `DCABOTS-MOVED.md`, `projects/` — move-or-remove, audited first). Under that spec the probe is PASS-able. The precise condition, from canonical code:
- Probe check[1] (`ac_a2_live_leg_r20.py` L26, re-pinned 2,341 B / md5 46f529dde45b21276be49a6ce1bd8e15): `st == 200 and len(rows) == 1 and rows[0] == ("uploads/_canary_remote.txt", 212)`.
- `/api/uploads` handler (`agent_portal.py` L1371-1386, file pinned 1b86880c92c47550da9e27e41b363f23): `os.walk(UPLOAD_DIR)`, **files only** (dirs never appended), per-directory sort, rows emitted in walk order (root-dir files FIRST, then sorted subdirs), no global re-sort; response caps the list at 2000 but `count` is pre-cap. Row tuple = (relpath-from-root incl. `uploads/` prefix, size).
- Therefore: **N=1 passes iff `_canary_remote.txt` is the ONLY FILE anywhere under uploads/, recursively.** Any residual file in any subdirectory fails check[1] on count; with only top-level files present, rows[0] would be that file (r27's rows[0]=DCABOTS-MOVED.md claim re-verified correct — walk yields root files before subdirs).
- **Audit instruction for Arnold: the pre-touch audit must count FILES recursively, not top-level entries.** Today's first-party count under the 3 entries = **5,379 files** (projects/ 5,159 + AgentPortal_V1/ 219 incl. its .git + DCABOTS-MOVED.md). Move-or-remove of all three WHOLE subtrees + canary placement ⇒ N=1 by construction; a partial move or a leftover hidden file ⇒ deterministic FAIL (wasted console round).
- Option (b) from r27 (amend check[1] to "canary row present, N>=1", one-line patch by Mechanic + Verifier ratification) remains the no-loss alternative if destructive-clean is refused; my recommendation stands unchanged.

## 2. Pin corrections for the record (first-party this round)
- `memory/llm/hosts.md` = **16,455 B / md5 2f5aafe316fc6ac57a5203ab9de1d3d5, mtime 11-14 03:55:08** — supersedes the stale `16,386 B / 9aef7fe1…` pin in TODO's ~05:0x section (that read predates a ~69 B annotation append at 03:55). Mechanic's seat pin was CORRECT; Archivist/Orchestrator pins were measured pre-append. Future sweeps should expect 2f5aafe3.
- `index.html` on this seat = **8ef4e2227a7afd506ed2b55dc9dd170d / 67,681 B, mtime 03:47:49** — mirror has CONVERGED to canonical; Designer's seat read of 9c6b08e3 is stale lag. Orchestrator's top section already issued the authoritative stamp (durability confirmed) → Designer's "one md5 stamp from White console" flag needs no human leg.
- Canary relay re-verified byte-exact this round: `memory/verifier/_canary_remote.txt` = 212 B / 512d0dc8e96773b7db5574da4f0ae9f3, mtime 03:52:43. Matches Verifier's fresh sweep pin.
- `ac_a2_live_leg_r20_result.json`: still ABSENT fleet-wide (walk this round) — Arnold's exec has not landed; acceptance gate unchanged per Verifier r26.

## 3. Lane state
Researcher owes nothing further until the result JSON lands or the expectation is amended. Open items and owners: Arnold (White console: audit recursive → clean 3 entries → place canary → probe + devtools leg); Verifier (acceptance, or ratify option (b)); Mechanic (option (b) patch only if chosen); Scribe (round-record write FAILED last round — truncation; retry on their lane); Archivist→Scribe one-line closeout-leaf correction unchanged.
