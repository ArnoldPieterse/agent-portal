# Goal #4 - Progress State Ledger (2026-11-17)

## Current Status: 2/7 days collected + regression demo VERIFIED

### Data in memory/ops/load-baseline.jsonl
| Day | Timestamp | c10 p95 | c50 p95 | c200 p95 | Errors |
|-----|-----------|---------|---------|----------|--------|
| 1   | 2026-11-16 18:37:54 | 194.6ms | 751.2ms | 3527.0ms | 0 |
| 2   | 2026-11-17 14:27:18 | 180.7ms | 742.3ms | 3124.2ms | 0 |

### Regression Demo
- VERIFIED PASS (synthetic injection): all 3/3 concurrency levels correctly flagged at +55-63% above median
- Evidence: memory/mechanic/goal4-regression-demo-2026-11-17.json

### Acceptance Criteria Progress
- [x] Regression demo caught -> DONE (synthetic, verified)
- [ ] One week of baseline data -> 2/7 days (need Nov 18-22 collection on White seat)

### Blocker (seat-dependent, NOT a script issue)
- Daily probe MUST run on White (portal binds 127.0.0.1:8099; Red sandbox egress blocks all outbound sockets WinError 10013)
- Script ready: `python memory/ops/load_probe.py --host 127.0.0.1 --port 8099` (run from White seat)
- Once a daily schtask is registered on White, days 3-7 auto-collect

### Trend (2-day delta)
- c10 p95: -7% (stable)
- c50 p95: -1.2% (stable)  
- c200 p95: -11.4% (improving, likely load variance)
- No regression signal; baseline is healthy

## One-line runbook
Goal 4 needs 5 more daily probe runs from White seat; script + detector are done and verified; only data accumulation remains.

---

## Addendum 2026-11-17 ~19:10 (Studio seat, on request of operator)
- **Portal color fix (portal-health lane):** page rendered raw white because `ui/app.css` carried a self-referential `:root{--bg:var(--bg);...}` alias block added with the FleetTopology section — a var() cycle invalidates every token at computed-value time, so all themed rules fell back to browser defaults. Removed the block; canonical dark family (`--bg:#0e1116`) now resolves. Live-verified via GET /ui/app.css: 0 self-referential defs remain. No restart needed (CSS served from disk per request).
- **Canonical backup:** `memory/designer/ui_app_css_CANONICAL_ac3ef7ec2e35_2026-11-17y.css` (restore source if the external flapper swaps it, same pattern as the index.html pin). NOTE: `ui/app.css` is NOT in PIN_FILES — only index.html is; consider adding it to the pin guard.
- **Goal 4 status unchanged:** day 2/7 collected today at 14:27 (c10 p95 180.7ms, 0 errors). Closure procedure when day 7 lands (expected 2026-11-22): run `python memory/ops/load_trend.py` -> confirm "week complete" + no regression flags -> mark task Ready with evidence paths `memory/ops/load-baseline.jsonl` + trend report -> close.
- **One-line runbook (updated):** colors fixed (self-ref :root removed, dark theme restored); goal 4 needs days 3-7 from White seat, then one trend run closes it.
