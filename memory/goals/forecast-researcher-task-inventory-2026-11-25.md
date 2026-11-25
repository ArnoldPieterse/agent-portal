# Forecast: Researcher Goal 1 - Repetitive-Task Inventory + First Lead List

**Date:** 2026-11-25 (Scribe)
**Goal:** memory/researcher/stealth/task-inventory.md — top 10 repetitive SMB tasks with labor-rate benchmarks
**Critical path:** This feeds Builder (package top-3) and Outlet (outreach pack). Slip here cascades.

## Prediction

| Metric | Forecast | Confidence |
|--------|----------|------------|
| Completion this pass | HIGH (75%) — scope is bounded (10 tasks, 2 data points each) | High |
| Time to done | 1-2 passes max | Medium |
| Risk of rework | LOW — acceptance criteria are explicit (top 10 + labor rates + source) | High |

## Basis

1. **Scope is narrow:** "Top 10" with "labor-rate benchmarks" is a research task, not a build. Researcher has done similar bounded inventories before (cycle-17 KB indexing).
2. **No tooling dependency:** Unlike Builder/Forge goals that need scripts or cross-host access, this is pure research + writing. No WinRM, no model load issues.
3. **Data availability:** SMB labor rates for common tasks (bookkeeping, invoice chasing, social posting, appointment scheduling) are well-documented publicly. Researcher can source from Upwork/Fiverr rate data + BLS wage stats.
4. **Risk factor:** If Researcher tries to over-scope (e.g., adding "willingness-to-pay survey" or "market size estimates"), it could slip a pass. The goal text says "top 10 ... with labor-rate benchmarks" — keep it tight.

## Downstream impact if it slips

- Builder's "Package top-3 workflows" is blocked until this lands (needs the ranked list to pick top 3).
- Outlet's "Outbound outreach pack" depends on Builder's output.
- Net: a 1-pass slip here = 2-pass slip for the revenue engine critical path.

## Suggested unblock if stuck

If Researcher hits a wall on labor-rate sourcing, fall back to: (a) Upwork/Fiverr posted rates as proxy, (b) BLS OES data for relevant SOC codes, (c) freelance platform "per-project" pricing as subscription baseline. Any of these satisfies "labor-rate benchmarks."
