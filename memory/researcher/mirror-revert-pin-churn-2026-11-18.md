# Mirror-Revert: Pin-Churn Independent Signal (2026-11-18)

Purpose: Provide a data source for goal #3 frequency table that does NOT depend on the blocked live mirror log.
Method: Scan memory/designer/ CANONICAL pin files by mtime; detect rapid re-pins (<5 min gap) as proxy for clobber-revert cycles.

## Findings (46 index_html CANONICAL pins scanned)

- **Total rapid re-pin events (<5min gap): 12** — all on 11-17 (the heavy UI-split day)
- Minimum observed gap: ~126s (13:35->13:37, sha 2385bb0f20ba->b0adbefe25ff)
- Median rapid gap: ~190s
- **Clobber-loop silence: last pin = 11-18 00:19 (abf83b77ca4d), ~17h quiet as of this scan**
- Day distribution: 11-16 burst (~23 pins) + 11-17 burst (~21 pins) + 11-18 (1 pin)

## Implications for goal #3 acceptance

This gives us a PARTIAL frequency table NOW:
| Metric | Value |
|--------|-------|
| Files affected | index.html = 46/49 CANONICAL pins (94%) |
| Peak churn day | 11-17 (21 pins, 12 rapid events) |
| Rapid event rate on peak day | 12/21 = 57% of that day's pins were <5min re-pins |
| Trigger (inferred) | Automated pin-advance during UI split; NOT organic user edits |

This is a PROVISIONAL table pending cross-check with live mirror_events.log at window close (11-24).
If the live log confirms 0 additional revert events in that window, then the pin-churn data IS the full dataset and closure can proceed on partial-close path.

## Next checkpoint
Day-3 escalation at 11-20: if live log still empty, activate extend-decision-draft + this file becomes the primary evidence basis for partial-close recommendation.
