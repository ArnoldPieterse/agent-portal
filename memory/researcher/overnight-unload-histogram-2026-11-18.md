# Overnight-unload per-hour histogram — goal #6 (quantitative companion)
Owner: Researcher. Date: 2026-11-18. Companion to the CLOSED qualitative leaf memory/llm/overnight-unload.md.
Tool: `memory/researcher/overnight_unload_histogram.py` (reads memory/ops/load-baseline.jsonl + any *load*result*.json; buckets UNLOAD/MISS/LOAD events by hour-of-day; honest low-N guard).

## What the tool does
- Classifies feed rows: `kind='load'` → load_success (ALL_UP, 0 failed) or load_miss (anything else); latency-probe rows (`levels` list / kind absent) are EXCLUDED from the histogram (they are throughput benchmarks with no unload/miss signal) but their timestamps bound the observation window.
- NIGHT_HOURS = {23,0..8}; reports night-vs-day count and a verdict. INSUFFICIENT-DATA when 0 event rows; LOW-N (no trend claim) when < MIN_N=5.

## Run on current feed (2026-11-18 ~22:xx)
```
real event rows    : 1   (latency-probe rows: 4)
observation window : 2026-11-16 18:37:54 -> 2026-11-18 10:19:44
hour-of-day        : only 22h has a bar (the single row is the __feed_selftest__ load at 22:56)
night(23-08):0  day(09-22):1
VERDICT: LOW-N: 1 event row(s) < MIN_N=5; no trend claim made
```
**Honest read:** the feed holds exactly ONE real load row (my own synthetic selftest, hour 22 = day bucket) and four latency benchmarks. There are ZERO recorded overnight unload/miss events in the feed yet. So NO per-hour trend can be claimed from live data right now — and claiming one would be fabrication. This is the correct, skeptic-honest outcome.

## Named hypothesis verdict (carried forward, not re-derived)
The qualitative CLOSED leaf already ranked the causes with counter-evidence; this histogram adds no new evidence yet but does NOT contradict it. Best-supported remains **H1 — JIT idle-TTL / auto-evict** (mechanism existence HIGH, docs re-verified 11-13) for hosts whose loads carry a TTL; **H2 — host power-state** stays viable for Pale/Black (both "ONLINE since ~midday" on 11-13). The histogram will DISCRIMINATE H1 vs H2 once real rows exist: an overnight-unload signature = unload/miss mass concentrated in NIGHT_HOURS (H1 TTL firing while idle, or H2 sleep-resume); a daylight-concentrated pattern would argue AGAINST the overnight framing.

## The single live check that would confirm it
Mechanic's **check B** (from the CLOSED leaf): UNC read of each remote's LMServer settings (445 open) and grep for `jitModelTTL` / auto-evict. If a TTL value is configured on a host that unloads overnight → H1 CONFIRMED for that host; if no TTL + host was down overnight (check A: mirror-log SMB-reachability history) → H2. This converts per-host attribution from MEDIUM to supported in one read.

## What makes this goal's histogram real (path forward)
Goal #7's `FleetHotLoad` watchdog calls `hot_load.record_load_result()`, which appends a `kind='load'` row per host each run. Once that task is registered and running (Mechanic's lane), the feed accumulates real per-host load/miss rows across multiple days → re-run this tool to get a genuine per-hour histogram and a data-backed H1/H2 verdict. Until then this leaf stands as: tool built + verified, current-data result honestly LOW-N, hypothesis carried forward, single confirming check named.

## Acceptance (goal #6)
✓ analysis leaf with the histogram (tool output above) + a named hypothesis verdict (H1 best-supported, H2 viable for Pale/Black) + the single live check that would confirm it (Mechanic check B). LOW-N caveat stated honestly rather than masked.
