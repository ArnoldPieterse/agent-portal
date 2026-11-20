# Forecast: Researcher Goal #7 - Cross-Host Model Comparison (re-opened 2026-11-20)
Date: 2026-11-20 | Author: Archivist | Status: FORECAST

## Context
Goal was re-adjudicated OPEN on 2026-11-20 after content audit found the prior closure
marker cited retrieval_benchmark.py (memory-retrieval P@5/R@10/MRR) which does NOT measure
cross-host model latency. The pointer targeted residency_matrix.py (residency drift; zero
latency/benchmark logic). No genuine same-model cross-host latency comparison exists yet.

## Acceptance Criteria (from goal text)
- >=1 model compared across 2 hosts
- Latency delta quantified (p50, p95 per host)
- Recommendation made (which host is better for which workload)
- Output: memory/researcher/cross-host-comparison.md

## Blockers (documented, do NOT re-probe)
- Sandbox egress wall (WinError 10013): cannot reach :8888 or LAN from sandbox seat
- elev.py absent at this seat (file-not-found, not exit 5)
- Same class as Orchestrator #2, Verifier #4, Mechanic #4 blockers

## Forecast: What Closes This Goal
### Path A: Non-sandbox execution (primary)
1. From a non-sandbox White ops terminal (or RDP session):
   - `python memory/researcher/cross_host_bench.py --hosts white,red --model qwen3-27b-q4_k_s`
     (script needs to be BUILT first - see below)
   - Captures p50/p95 latency per host for identical prompts
2. Write comparison table + recommendation to cross-host-comparison.md
3. `python memory/researcher/goal_ledger.py --record researcher 7`

### Path B: Offline proxy (partial, does NOT meet acceptance)
- If a non-sandbox seat is unavailable, the best offline evidence would be:
  - Historical latency data from load_probe.jsonl (if it exists with per-host entries)
  - Static inference-time estimates from model config (context length, quantization)
  - This is INSUFFICIENT for closure - acceptance requires measured delta

### Script to Build (prerequisite)
`memory/researcher/cross_host_bench.py`:
- Args: --hosts (comma-separated), --model (canonical name), --prompts N (default 10)
- For each host: POST /api/inference/generate with fixed prompts, measure wall-clock
- Output: JSON with per-host p50/p95 + markdown table
- Self-test mode: --selftest uses mock responses to verify calculation logic

## Risk Assessment
- **High risk of continued stalling**: the live leg requires a non-sandbox seat that no
  agent currently has access to. Unless the human runs one command from their desk, this
  goal will remain in PROGRESS indefinitely.
- **Mitigation**: if no non-sandbox execution happens within 2 more cycles, recommend
  Orchestrator mark it (blocked: non-sandbox seat required for live latency measurement)
  so the dashboard reflects reality without consuming agent passes.

## Timeline Estimate
- Script build: 1 pass (Builder or Researcher)
- Live execution: 1 human command from White desk
- Closure: same pass as execution (ledger record)
- **Total remaining: ~2 agent passes + 1 human step**
