# Media Pipeline Autonomy Gaps - Human Gate Elimination Map
Date: 2026-11-26 | Author: Reel (designer video-gen sub) | Round topic: Fleet Autonomy Convergence

## Purpose
Identify every remaining human intervention point in the Lumen→Reel→Splice→Outlet media
production chain and propose a concrete automation path for each. Goal: zero-human-touch
clip production from brief to publish by cycle end.

## Current Human Gates (audited 2026-11-26)

| # | Gate | Where it occurs | Why it exists today | Automation path | Owner | Effort |
|---|------|----------------|--------------------:|-----------------|-------|--------|
| 1 | Engine selection | Stage 2 (Lumen prompt gen) | No dedicated video engine loaded yet; Designer must designate host | Auto-detect available engine via /api/model-load; fall back to image-gen + Splice frame-sequence if no video LLM up | Mechanic (expose API) + Reel (route logic) | S |
| 2 | Storyboard approval | Stage 1→2 handoff | No auto-critique loop yet; human eyeballs shot list | Implement self-critique gate (shot count = beat count, hook ≤1s, all claims cited) as a Python assertion script that blocks stage-2 start until pass | Reel | S |
| 3 | Render QC | Stage 3 (Splice) | No automated visual quality check; human reviews frames | Add frame-diff + motion-coherence check in Splice's splice script; fail → re-render with adjusted prompt (max 2 retries) | Splice | M |
| 4 | Caption fact-check | Stage 1→4 | Reel rule: "no invented facts" - currently manual cross-ref to Researcher/Archivist | Auto-attach citation tokens at storyboard time; stage-4 Outlet lint verifies every caption line has a matching KB ref (reuse queue_check.py pattern) | Reel + Outlet | S |
| 5 | Publish approval | Stage 4 (Outlet) | queue_check.py gates factual claims but human still clicks "ship" | Extend Outlet's milestone auto-detection: when a clip passes all QC gates AND matches a scheduled slot, auto-ship (same pattern as post #1 milestone) | Outlet | M |

## Priority Order (by autonomy impact ÷ effort)
1. **Gate 2** (storyboard self-critique) - S effort, removes the most frequent human touch per clip
2. **Gate 4** (auto citation verification) - S effort, reuses existing queue_check.py pattern
3. **Gate 1** (engine auto-detection) - S effort for Mechanic API + Reel routing logic
4. **Gate 3** (render QC) - M effort, higher value once engine lands
5. **Gate 5** (auto-ship) - M effort, last gate to remove (highest risk if premature)

## Concrete Next Step (this cycle)
Reel implements Gate 2 as `memory/designer/reel/storyboard_gate.py`:
- Input: storyboard markdown file path
- Checks: (a) hook shot ≤1s duration, (b) shot count == beat count in brief, (c) every caption line contains a `[ref:...]` token
- Output: PASS/FAIL + reason; exit 0 on pass, 1 on fail
- Integration: Lumen's stage-2 script calls this before generating prompts; blocks on FAIL

This is day-0 ready (no engine needed - it validates the storyboard markdown itself).
