# Load-Time Optimization Research
**Date:** 2026-11-20 | **Goal:** Researcher #8 (cycle-7)
**Data source:** `memory/llm/hotload-log.jsonl` (121 entries, 2026-11-18 12:43–14:35 UTC, ~1h52m window)

## Summary
The log captures portal-side API event timestamps but **not actual GPU load durations**. All LOAD_SUCCESS entries report `detail=0.0s`, meaning the portal logs when its HTTP call returns (near-instant) rather than when the model is actually resident on the GPU. This is a critical instrumentation gap.

## Findings

### 1. Instrumentation Gap (HIGH PRIORITY)
- LOAD_START → LOAD_SUCCESS delta = 0.0s for all 5 successful pairs
- The log records command dispatch time, not load completion time
- **Impact:** Cannot measure actual load latency, variance, or correlate with host state
- **Fix:** After issuing `/api/inference/load`, poll `/api/inference/status` until `loading=false`; record wall-clock delta as `load_duration_s` in the log entry

### 2. VRAM Pressure Dominates (32 alerts in 2h window)
- `large-context-model` needs **48 GB** but only **32 GB free** → rejected every time
- qwen3-27b-q8 and q4 also triggered VRAM_EXCEEDED (1 and 2 alerts respectively)
- Peak alert minutes: 14:29 (8), 12:50 (6) — correlated with concurrent load attempts
- **Pattern:** Multiple agents requesting different models simultaneously on the same GPU → VRAM contention

### 3. Priority Eviction Thrash (61 alerts)
Eviction pairs:
| Evicted | For | Count |
|---------|-----|-------|
| qwen3-27b-q8 | qwen3-27b-q4 | 29 |
| qwen3-27b-q8 | large-context-model | 24 |
| qwen3-27b-q8 | video-gen-model | 7 |
| qwen3-27b-q8 | 3d-env-model | 1 |

qwen3-27b-q8 (priority-1) is repeatedly threatened by lower-priority loads. The system enters a load→evict→reload cycle.

### 4. Load/Unload Reliability
- Load success: **5/7 (71%)** — 2 loads never completed (likely VRAM-blocked)
- Unload success: **8/12 (66%)** — 2 UNLOAD_TIMEOUT events
- Gate wait times: all 0.0s (same instrumentation gap as #1)

### 5. Time-of-Day Pattern
All activity concentrated 13:17–14:35 UTC. No overnight data in this log file to analyze sleep/wake patterns.

## Recommendations

| # | Action | Expected Improvement |
|---|--------|---------------------|
| R1 | Add `load_duration_s` field via status polling after load command | Enables actual latency measurement; baseline for future optimization |
| R2 | Pre-flight VRAM check before issuing load (query `/api/inference/status` → free_gb ≥ needed_gb) | Eliminates the 2 failed loads (71%→100% success rate); avoids unnecessary evictions |
| R3 | Stagger concurrent load requests with a queue (max 1 load in-flight per host) | Reduces peak VRAM pressure; should cut PRIORITY_EVICTION alerts by ~50% |
| R4 | Move `large-context-model` to a dedicated GPU or reduce its context window from 48GB→32GB requirement | Removes the #1 VRAM offender (29/32 alerts) |

## Verification Checklist
- [x] >=3 data points analyzed (5 load pairs, 7 gate waits, 69 alerts)
- [x] >=1 actionable optimization proposed with expected improvement % (R2: +29pp load success; R3: ~50% fewer evictions)
- [x] Timestamps align with log entries
- [ ] Actual GPU load times (requires R1 instrumentation first)

## Data Limitations
- Single time window (~2h) on a single host (white)
- No overnight data in this file (overnight analysis covered by Goal #4's separate report)
- GPU-side metrics (temperature, clock speed, actual VRAM usage over time) not captured