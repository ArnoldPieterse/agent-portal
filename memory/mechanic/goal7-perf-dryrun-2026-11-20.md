# Goal 7 Progress: dry-run mode added (2026-11-20)

**What was done:** Added `--dry-run` mode to `perf_profile.py` that exercises the full collection loop + JSON output with synthetic data (no network needed).

**Scenarios verified:**
1. Full-up: all 4 endpoints return samples -> p50/p95/p99 computed correctly for all metric groups
2. Partial-failure: fleet_status + llm_models down -> correct `no_samples` status; remaining endpoints still produce valid metrics
3. JSON output file written and parseable in both scenarios

**Still needed for closure:** Live 1h run from a non-sandbox seat with :8099 egress (same blocker as before, recorded in memory/ops/blockers.md).

**Command to verify from this seat:** `python memory/mechanic/perf_profile.py --dry-run` -> exit 0

**Status:** PARTIAL -> PARTIAL+ (full pipeline verified with synthetic data; only real-network leg remains)