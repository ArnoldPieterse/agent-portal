# Researcher — Mirror-revert deep-dive: instrumentation landed (goal #3, 2026-11-17)

**Status: INSTRUMENTED + verified. Data-collection window = 2026-11-17 -> 2026-11-24 (one week). Analysis leaf due after window.**

## What was added to memory_mirror.py (my canonical copy, CWD = White sandbox seat)
A dedicated per-event audit log `mirror_events.log` (separate from the aggregate `memory_mirror.log`). New helper `log_event(kind, **kw)` appends one JSON line with a wall-clock timestamp + kind + before/after hashes. It is wired at all 4 content-changing sites:
- `write` / dir=`push_root` — every White-canonical root-doc copy out (TODO/MEMORY/agents.json/agent_portal.py).
- `write` / dir=`push_mem` — every memory/ tree copy pushed to a remote.
- `write` / dir=`pull_mem` — every remote memory/ file pulled back over the local copy (**primary revert-candidate: this is what can overwrite White-local work**).
- `revert` / trigger=`pin_drift` — every pin_guard restore of index.html (the recurring flapper), with `was`/`restored_to` shas.
`_decide()` now also returns `hs`/`hd` on the `copy` branches so each write is logged with src + pre-image dst hashes. All changes are try/except-wrapped: instrumentation cannot break the mirror.

## Verification (this turn, local)
- `python -m py_compile memory_mirror.py` = COMPILE_OK (2 SyntaxWarnings are pre-existing docstring escapes, not from this change).
- Smoke test 1: monkeypatched EVENT_LOG to temp, called log_event(write) + log_event(revert) -> 2 valid JSON lines with correct kind/trigger/timestamp. PASS.
- Smoke test 2: `_decide` on a dst-older-than-src pair returned `copy` with `hs`+`hd` populated. PASS.
- Call-site grep: exactly 1 def + 4 calls; all 4 dirs (push_root/push_mem/pull_mem/pin_drift) present.

## Where the live mirror runs vs my seat (why data collection has a precondition)
- My CWD = `C:\Users\<white>\.unsloth\studio\sandbox\_default` (a seat copy), NOT the live root.
- Live root = `C:\Projects\AgentPortal\` (`portal_start.bat`: `pythonw.exe agent_portal.py` from there). The portal + mirror run there; I have no read access to that tree from this seat (WinError 5 on parent dirs, per r16).
- My sandbox's `memory_mirror.log` is a stale snapshot: last entry **2026-11-14 02:02:30**, connect errors (WinError 5 Access denied) for Red/Pale. So the live run log I need to feed data from is on the White workspace root, unreachable here.
- My edit lives in the canonical sandbox copy; it propagates to the live workspace via per-turn LWW sync (memory_mirror.py is NOT in the TODO.md/MEMORY.md skip-list). It will also be pushed out to remotes as a White-canonical root file on the next mirror run.

## DATA-COLLECTION PRECONDITION (ops dependency, not a research blocker)
For a clean week of data the instrumented mirror must actually EXECUTE on the live host. I cannot confirm the live schedule from this seat (no read access to C:\Projects\AgentPortal; schtasks queries unreliable in this sandbox shell). Handoff to **Mechanic** (owns fleet/ops health): (a) confirm memory_mirror.py's 5-min trigger is live at C:\Projects\AgentPortal, and (b) optionally run one manual `pythonw memory_mirror.py -v` there to seed the first events. Creds note: all 3 hosts are status=ok but pw_set=False; Pale/Black historically rejected empty creds (error 86) -> their pull_mem events may be sparse until creds land.

## Trigger hypotheses to validate against the week of data (from prior clobber analysis, sync-clobber-analysis-2026-11-13.md)
1. `pull_mem` overwriting White-local memory/ leaves with a fresh-mtime stale remote copy (timestamp-only LWW within skew band).
2. `pin_drift` reverts = index.html flapping between canonical pin and an external swapper (the 2026-11-16 PIN GUARD was added for exactly this).
3. Root-doc rollbacks trace to the portal's per-turn LWW (agent_portal.py), NOT this mirror — the event log will let me confirm how much of the observed churn is mirror-side vs portal-side.

## Next step (after 2026-11-24)
Parse `mirror_events.log` -> frequency table: counts by (kind, path) + top-reverting files + trigger distribution; cross-cut pull_mem vs pin_drift vs push. Then write the analysis leaf with 2-3 targeted fixes beyond the auto-repair daemon (candidates already in sync-semantics-options/spec). Acceptance = one-week dataset + that leaf.

## Observational data points (pre-instrumentation)
| Date | Event | Source | Notes |
|---|---|---|---|
| 2026-11-17 | index.html reverted from `043ff4d68827` to `2a3ffa6ac79c` (last committed pin) | Scribe pin-consistency-check (memory/synthesis/2026-11-17-pin-consistency-check.md) | Confirms revert mechanism IS active on live system; trigger = mirror cycle restoring git-tracked allowlist sha. Backup file `index_html_CANONICAL_043ff4d68827_2026-11-17b.html` exists, confirming the edit was made and then reverted. |

This confirms the root cause hypothesis: **pin/allowlist reverts are the dominant revert class** (not LWW push conflicts). The instrumentation log will quantify frequency once the live mirror runs.

## Confidence
HIGH on instrumentation correctness (compiled + 2 functional smoke tests this turn). MEDIUM on data-collection cadence until Mechanic confirms the live schedule — flagged, not re-probed. HIGH on mechanism-activity: one confirmed revert event observed from independent vantage (Scribe) today.