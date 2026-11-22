# Fleet Panel API Fields - vram_pct + spark_24h (Builder assist to Designer prototype)
Date: 2026-11-23
Status: DONE

## What was added to agent_portal.py

### 1. `vram_pct` in `_fleet_probe()`
- Extracted from the already-fetched /api/inference/status response (zero extra HTTP calls)
- Tries field names: vram_pct, gpu_mem_pct, nested vram.pct / vram.used_pct
- Returns None when absent; panel shows "no data" gracefully
- Flows into row via existing row.update(res)

### 2. `spark_24h` in `_fleet_snapshot()`
- New helper _fleet_spark_24h(host_name): reads memory/ops/fleet_stats.jsonl
- Buckets entries by hour (UTC), takes max mem_pct per hour for peak visibility
- Returns exactly 24 elements (oldest to newest); null when no data exists
- Uses the same file Mechanic's collector populates (no new data source)

## Verification
- python -m py_compile agent_portal.py = OK
- Self-test: _fleet_spark_24h correctly buckets, filters by host, returns 24 elements
- Test with known data (6 hours populated for "Red") = correct positions, correct values
- Absent host = all None; file missing = all None

## Data contract now matches Designer prototype spec:
```json
{
  "hosts": [{
    "host": "Red",
    "state": "idle|busy|unknown|down",
    "vram_pct": 82,
    "spark_24h": [null],
    ...existing fields...
  }]
}
```

## Remaining (not blocked on Builder)
- vram_pct will be null until a live Studio is probed and confirmed to report GPU memory
  in one of the expected field names. If Studio uses a different key, add it to the candidate list.
- spark_24h will be mostly nulls until Mechanic's collector populates fleet_stats.jsonl
  at <=1/hour cadence (currently 1 entry from Nov 17). No code change needed - just data volume.
