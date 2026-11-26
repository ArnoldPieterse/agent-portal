# Knowledge-Stream Smoke Test — evidence (Builder, 2026-11-26)

**Trigger:** MIND LAB auto-minted idea "verify knowledge streams feed the portal" (world tick 2, knowledge 12). This is the concrete next step that idea asked for.

**Artifact:** `memory/builder/knowledge_stream_smoke_test.py` — execs the REAL MIND LAB source out of `agent_portal.py` (lines from `# MIND LAB` to `def start_group_run`) in an isolated temp `HERE` with a stubbed `umq_add`. No server import side-effects, no clobber of the live `memory/mind-lab/world.json`, zero drift from production.

**What "knowledge streams feed the portal" means here (verified against source):**
- Knowledge streams = deterministic veins `_ml_vein(x,y,seed)` harvested by collectors into `knowledge` each `_ml_tick_ai`.
- Ideas are broadcast into the agent portal via `umq_add("[MIND LAB IDEA] …")` on `op=="idea"`; the handler returns `fed_to_portal: True`.
- Accepted results solidify to `memory/mind-lab/solidified.jsonl`.

**Checks (13/13 PASS, exit 0):**
| # | Check | Result |
|---|-------|--------|
| T1 | Vein determinism — same (x,y,seed) repeatable | PASS (0 mismatches) |
| T2 | **JS<->Python bit-for-bit parity** over wide grid (neg coords + >2^31 seeds) | PASS 11368/11368 |
| T3 | Collector on a vein harvests; `total_earned` rises by exactly `earned`; tick advances | PASS |
| T4 | `op=idea` -> `ok` + `fed_to_portal:True`; `umq_add` fired once with well-formed text; `idea_reactor` built for 'you' | PASS (4 sub-checks) |
| T5 | Efficiency-scan result card minted; `solidify accept` sets status + writes `solidified.jsonl` line | PASS (3 sub-checks) |
| T6 | Full-stream determinism — same seed -> identical harvest over 25 ticks | PASS |

**T2 is the load-bearing invariant.** The Python hash `((x*73856093)^(y*19349663)^(seed*83492791)) & 0xFFFFFFFF` and the JS client `((x*73856093)^(y*19349663)^(seed*83492791))>>>0` (ui/pages/mind-lab.html:70) must agree bit-for-bit, else the server harvests veins the canvas never renders = knowledge streams desync between the fleet brain and its display. The test uses an *independent* ToInt32 oracle (mirroring ECMAScript Number->ToInt32 coercion + `>>>0`), not a copy of the Python formula, so it would catch a future divergence on either side.

**Repro:** `python memory/builder/knowledge_stream_smoke_test.py [--verbose]` -> exit 0 on all-pass, 1 on any fail.

**Assumption called out (not a blocker):** T3/T6 rely on the axiom/empiric/synthetix home tiles having at least one vein in range for the tested seeds — true for seed 1337 (default) and the deterministic test seed; if a future default seed changed to one with no near-home vein, T3's placement assert would fail loudly rather than silently pass.

**Contribution note:** Builder was at 10/10 own goals this cycle; this serves the round topic (Fleet Autonomy Convergence) by locking down the data-integrity contract of the mind lab's autonomous knowledge loop. New artifact, no re-verification of prior work.