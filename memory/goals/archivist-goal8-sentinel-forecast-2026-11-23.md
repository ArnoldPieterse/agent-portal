# Forecast: Archivist Goal 8 — KB Regression Sentinel (kb_sentinel.py)
**Author:** Builder | **Date:** 2026-11-23 | **Confidence:** high

## Current State
- `memory/archivist/kb_sentinel.py` does not yet exist
- Prerequisites are in place:
  - `knowledge-index.json` (Goal 1) — 12,975 facts indexed
  - `auto_quarantine.py` (Goal 2) — freshness scoring + quarantine logic exists
  - `conflict_resolver.py` (Goal 4) — contradiction detection already works (2645 files / 3867 facts / 225 conflicts)
  - `citation_monitor.py` (Cycle-9 Goal 3) — broken citation detection exists
- No existing sentinel/alert infrastructure in memory/archivist/ — this is greenfield

## Implementation Plan (3 components, ~150 LOC total)

### 1. Baseline Capture (~40 LOC)
On first run (or `--baseline` flag), snapshot:
```python
{
  "total_facts": int,          # from knowledge-index.json
  "critical_nodes": [...],     # top-10 by in-degree from knowledge-deps.json
  "resolved_conflicts": [...], # subjects previously flagged then cleared
  "snapshot_hash": str         # sha256 of index for integrity
}
```
Store at `memory/archivist/kb-sentinel-baseline.json`.

### 2. Check Logic (~70 LOC)
Each run compares current state vs baseline:
- **Fact count drop > X%:** `X = 5` (configurable via `--threshold`). Compare `len(current_facts)` to `baseline["total_facts"]`. Alert if drop exceeds threshold.
- **Critical node in-degree change:** Re-compute in-degrees from knowledge-deps.json; flag any top-10 node whose in-degree changed by >= 2 edges.
- **Contradiction reappearance:** Cross-reference current conflict_resolver output against `baseline["resolved_conflicts"]`. If a previously-resolved subject reappears, alert.

### 3. Alert Emission + Dedup (~40 LOC)
- Write alert to `memory/archivist/kb-sentinel-<date>.md` (one file per day, append if multiple alerts same day)
- **Dedup:** Maintain `memory/archivist/kb-sentinel-state.json` with set of active alert keys. If an alert key already exists and condition hasn't changed, skip (no repeat). Clear key when condition resolves.
- Alert format:
```markdown
## ALERT: <condition_type> | <date>
- Condition: fact_count_drop 12975 -> 12100 (-6.7%, threshold 5%)
- Affected: [list of facts/nodes]
- Action: investigate index rebuild or quarantine overflow
```

## Acceptance Criteria Mapping
| AC | How met |
|---|---|
| Deliberate corruption triggers alert | Test: remove 10% of facts from a temp copy, run sentinel → alert emitted |
| Clean state is silent | Test: run on unmodified index → no alert file created, exit 0 |
| Alerts deduped | Test: run twice with same corruption → second run skips (state.json has key) |
| Report at memory/archivist/kb-sentinel-<date>.md | Direct path in code |

## Self-Test Design (`--selftest`)
1. Create temp index with 100 facts → baseline
2. Remove 15 facts → run check → expect fact_count_drop alert
3. Re-run same corruption → expect dedup (no new alert)
4. Restore index → run → expect silent + state cleared
5. Seed a resolved conflict, re-introduce it → expect reappearance alert
6. Verify report file exists with correct format

## Risk Factors
1. **knowledge-deps.json size:** Currently 2MB (1722 edges). In-degree computation is O(E) — trivial at this scale. No risk until >100k edges.
2. **Baseline staleness:** If index is rebuilt (e.g., new cycle), baseline becomes stale. Mitigation: `--rebaseline` flag + auto-detect via snapshot_hash mismatch (warn but don't alert on hash change alone).
3. **conflict_resolver.py coupling:** Sentinel imports its output format. If Goal 4's output schema changes, sentinel breaks. Mitigation: defensive parsing with clear error message.

## Effort Estimate
- Build + selftest: ~30 min (straightforward CRUD + comparison logic)
- schtask registration: reuse `deploy_all_schtasks.py` pattern (daily 06:00 run)
- **Total to verified:** one sitting, no external dependencies beyond existing artifacts

## Suggested Build Sequence
1. Write `kb_sentinel.py` with `--selftest`, `--baseline`, default check modes
2. Run selftest → 6/6 PASS
3. Run `--baseline` on live index to capture initial state
4. Register schtask (daily 06:00) via deploy_all_schtasks.py or manual `schtasks /create`
5. Record closure via goal_ledger.py
