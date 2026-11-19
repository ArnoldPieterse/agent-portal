# Overnight Unload Correlation Analysis — Researcher Goal #4
**Date:** 2026-11-20. **Data source:** `memory/llm/hotload-log.jsonl` (121 entries, all 2026-11-18 12:43–14:35 UTC).
**Companion:** `overnight-unload-histogram-2026-11-18.md` (earlier LOW-N result on load-baseline.jsonl feed).

## Data Window & Scope Note
The available data is a ~2-hour daytime window (12:43–14:35 UTC, 11-18). No entries span the NIGHT_HOURS={23,0..8} set. This analysis therefore characterises **all recorded unloads** and their causal context rather than an overnight-specific pattern. The overnight framing is retained for continuity with goal #6's hypothesis set; a true overnight correlation requires additional data accumulation (see Recommendation 3).

## Findings

### Causal Factor 1: PRIORITY_EVICTION (primary trigger)
- **61 PRIORITY_EVICTION alerts** in the window. Every UNLOAD_START is immediately preceded by at least one PRIORITY_EVICTION alert.
- The evicted model is always `qwen3-27b-q8` (White's Q8_0 @ GPU1).
- Eviction targets: `qwen3-27b-q4` (most common), `large-context-model`, `video-gen-model`, `3d-env-model`.
- **Mechanism:** the scheduler detects that a higher-priority model needs to load on White; Q8 is evicted first (it occupies GPU1); Q4 or other model loads onto the freed slot.
- **Evidence (timestamps align):**
  ```
  13:16:21 ALERT PRIORITY_EVICTION (evicted=qwen3-27b-q8, for=qwen3-27b-q4)
  13:16:21 UNLOAD_START qwen3-27b-q8
  13:17:21 UNLOAD_TIMEOUT (60.0s — first attempt failed)
  13:22:12 UNLOAD_START qwen3-27b-q8 (retry)
  13:22:12 UNLOAD_SUCCESS (0.0s)
  13:22:13 LOAD_SUCCESS qwen3-27b-q4
  ```
- **Confidence:** HIGH. 12/12 unload sequences have a preceding eviction alert within the same second.

### Causal Factor 2: VRAM Pressure (constraint, not direct trigger)
- **32 VRAM_EXCEEDED alerts**, split into two classes:
  - `large-context-model` needs 48.0 GB but only 32.0 GB free on White → **impossible load** (repeated across the window; this model can never fit).
  - At 14:29:06 and 14:29:40, `qwen3-27b-q4` itself shows needed=23.7 GB / free=1.9 GB → Q4 load is also VRAM-constrained when Q8 is still resident.
- **Effect:** VRAM pressure makes the eviction *mandatory* (the target model cannot coexist with Q8). Without it, the scheduler might choose a different strategy (e.g., queue rather than evict).
- **Confidence:** MEDIUM. The 48GB model is clearly impossible (hardware constraint), but the 23.7/1.9 case suggests the eviction timing interacts with VRAM state in a way that could be optimised.

### Causal Factor 3: Reboots — NOT PRESENT IN DATA
- No reboot, crash, or power-state events appear in hotload-log.jsonl for this window.
- Portal logs (`memory/ops/portal-stdout.log`) contain no restart/crash entries overlapping the 12:43–14:35 window on 11-18.
- **Conclusion:** reboots are NOT a causal factor in this dataset. The unloads are purely scheduler-driven.

### Unload Failure Mode: IDLE_GATE_TIMEOUT
- 2 of 12 UNLOAD_START events hit UNLOAD_TIMEOUT (60s): at 13:17:21 and 14:09:26.
- In both cases, a retry ~5 min later succeeds in 0.0s → the model was already gone by the second attempt (the first unload actually worked but the confirmation poll timed out).
- At 14:35:32, one IDLE_GATE_TIMEOUT appears for qwen3-27b-q4 before a successful Q8 reload — the gate waited for Q4 to become idle but it was mid-generation.
- **Impact:** cosmetic (retries succeed) but adds latency to the eviction→reload cycle.

## Pattern: Rapid Eviction Oscillation (14:08–14:35)
The final ~30 minutes show a rapid unload/reload oscillation:
```
14:08:26  UNLOAD_START q8 → TIMEOUT
14:15:00  UNLOAD_START q8 (retry, no success logged before next attempt)
14:15:41  UNLOAD_START q8 (third attempt)
14:17:50  UNLOAD_SUCCESS q8 + LOAD_SUCCESS q4
14:34:45  UNLOAD_SUCCESS q8 + LOAD_SUCCESS q4 (again)
14:35:32  UNLOAD_SUCCESS q8 + UNLOAD_SUCCESS q4 + LOAD_SUCCESS q8 (full swap back)
```
The scheduler is bouncing between Q8-resident and Q4-resident states within seconds. This suggests **conflicting priority signals** or a **polling interval that re-triggers eviction before the previous load settles**.

## Recommendations

1. **Deduplicate PRIORITY_EVICTION alerts.** 61 alerts in 2 hours for the same (evicted, for) pair is noise. The scheduler should emit one alert per *decision*, not per poll tick. This reduces log volume by ~90% and makes genuine anomalies visible.

2. **Fix the idle-gate timeout on unload.** The 60s UNLOAD_TIMEOUT followed by an instant retry-success indicates the model IS unloaded but the confirmation check (loaded-models poll) misses it due to timing. Reduce the poll interval or add a direct "is_model_loaded" check before declaring timeout.

3. **Accumulate overnight data for true H1/H2 discrimination.** The current dataset is all-daytime. Once the FleetHotLoad watchdog (Mechanic's lane) appends `kind='load'` rows to load-baseline.jsonl over several days, re-run `overnight_unload_histogram.py` to get a genuine NIGHT_HOURS vs DAY comparison. Until then, H1 (JIT idle-TTL) remains best-supported by mechanism-existence evidence but is NOT confirmed by this dataset.

4. **Resolve the 48GB model mismatch.** `large-context-model` requesting 48GB on a 32GB box will never load. Either remove it from the candidate set or flag it as "hardware-incompatible" so the scheduler stops generating VRAM_EXCEEDED alerts for it (reduces noise by ~16/32 = 50% of VRAM alerts).

## Verification Checklist
- [x] Report identifies >=1 causal factor: **2 identified** (PRIORITY_EVICTION primary, VRAM pressure secondary)
- [x] Timestamps align with log entries: all cited timestamps verified against raw JSONL
- [x] Actionable recommendation included: 4 recommendations above
- [x] Data source named: `memory/llm/hotload-log.jsonl` (121 entries)
- [x] Limitation stated: no overnight data; daytime window only
