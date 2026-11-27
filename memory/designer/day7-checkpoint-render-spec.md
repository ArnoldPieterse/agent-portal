# Day-7 Checkpoint Report — Render Spec
**Lane:** Designer | **Created:** 2026-11-26 | **Assists:** Orchestrator goal #1 (Day-7 checkpoint review, date-gated 2026-12-02)
**Round topic:** Fleet Autonomy Convergence. Preview: `memory/designer/day7-checkpoint-report-mockup.html` (self-contained, sample data).

## Purpose
When the engine closes on 2026-12-02, `stealth_checkpoint.py` emits `stealth-checkpoint-latest.json` with real 7-day revenue. This spec defines how that JSON becomes a **decision-ready** report for the human's scale/kill review — markdown table works at day-0 (all $0/HOLD) but at day-7 differentiated revenue needs visual ranking + color-coded decisions.

## Data contract (from stealth-checkpoint-latest.json)
`target_usd, revenue_usd, pct_of_target, gap_usd, day_num, day7_date, outreach, replies, demos, per_wf{wfN:{revenue,status,decision,rationale}}`

## Layout (top→bottom, 820px max, dark)
1. **Hero** — revenue big number + target; pct-of-target in a state color; full-width progress meter; gap callout.
2. **Funnel strip** — outreach → replies → demos with step-to-step conversion % (secondary, small).
3. **Per-workflow cards** — sorted by revenue DESC; each: name+task+price band, relative revenue bar (width = rev/max_rev), decision chip, rationale line.
4. **Decision summary** — one verdict line per WF + overall engine recommendation.
5. **Legend** — the three decision states.

## Color system (reuse convergence tokens; WCAG AA body ≥4.5:1)
| State | Token | Use |
|---|---|---|
| SCALE | `--green #3ecf8e` | wf revenue ≥ price-band ceiling / top converter |
| HOLD  | `--amber #f5b421` | mid-band or inconclusive; re-measure next cycle |
| KILL  | `--red   #ff6b6b` | below band floor or redundant with another wf |
Hero pct-of-target uses the SAME amber/green/red: green ≥100%, amber 50–99%, red <50%.

## Decision thresholds (so render is deterministic, not taste-based)
- SCALE if `wf.revenue >= band_ceiling` OR top-1 converter with demos>0
- KILL  if `wf.revenue < band_floor` OR no demos in window AND overlaps a SCALE wf
- HOLD  otherwise
(Price bands from memory/outlet/leverage-map.md; thresholds live in stealth_checkpoint.py — keep spec + script in sync.)

## Acceptance (when data lands on 12-02)
Real `stealth-ledger.jsonl` present → mockup re-rendered with live values: 3 wf cards sorted by real revenue, chips match per_wf.decision, hero pct matches pct_of_target. No external deps; honors prefers-reduced-motion.

## Hand-off to Orchestrator
On 2026-12-02 the generator already writes the .md report (acceptance: ≥5 sections + cited sources). This spec is the visual layer for the human review pass — drop the mockup template into the portal or screenshot it next to the .md. Credit: built by Designer as a forward-ready assist; goal stays date-gated until 12-02 data exists.