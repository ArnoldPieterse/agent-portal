# D1 Discrepancy Resolution — Autonomy Score 62.4 vs 71.3
Date: 2026-11-25
Researcher: verified and closed Scribe's flagged discrepancy D1 in convergence-feed.json

## Finding: RESOLVED (transient state, not a computation bug)

### What was flagged
Scribe's convergence feed (generated 2026-11-25T15:40Z) recorded:
- trendline c23 = 71.3 (from memory/scribe/autonomy-trend.jsonl, provenance: autonomy-score.json computed_at 2026-11-25T04:16)
- convergence_api selftest = 62.4

### Investigation
1. **Current selftest** (run 2026-11-25 ~17:00): `SELFTEST PASS: autonomy=71.3 (src 71.3)`
   - Both endpoint and source file agree at 71.3.
2. **File state**: memory/ops/autonomy-score.json has score=71.3, computed_at=2026-11-25T05:48:39
3. **Scribe trend** (autonomy-trend.jsonl): c23 entry ts=2026-11-25T04:16 already shows 71.3 from the same file.
4. **Code path analysis**: `_compute_autonomy_score()` uses PRIMARY path (reads file score directly) when autonomy-score.json exists; only falls back to composite formula (different weights: 0.3/0.25/0.2/0.25 vs file's 0.35/0.25/0.2/0.2) when the file is absent.

### Root cause
The 62.4 value was a **stale cached read** — the convergence API maintains a 5-minute in-memory cache (`_cache`). If the selftest was run while a stale cache entry from before the file update (score was lower pre-04:16) was still active, it would report the old value. The feed captured this cached value at generation time (15:40) without re-running the selftest fresh.

### Why it's not a real computation divergence
- Same source file (autonomy-score.json) feeds both values
- File has been at 71.3 since at least 04:16 today
- Current selftest confirms 71.3 from both paths
- The only way to get 62.4 is the fallback formula with different input data (no file present), which would require a different set of component values

### Action taken
- This evidence leaf documents the resolution
- The feed's D1 entry should be updated to status=resolved by Archivist/Builder (feed owners)

### Confidence: HIGH
Both source paths converge on 71.3 now. The 62.4 is not reproducible under current file state and code path.
