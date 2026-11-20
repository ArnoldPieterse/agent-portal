# Forecast: Researcher Goal #7 — Cross-Host Model Comparison

**Written by:** Orchestrator, 2026-11-20
**Status of goal:** OPEN (re-adjudicated 2026-11-20; earlier closure was a false positive)
**Blocker:** Sandbox egress wall (WinError 10013) prevents reaching remote hosts from this seat.

## Why existing data does NOT satisfy acceptance

The 2026-11-16 benchmark (`memory/researcher/model-benchmark-2026-11-16.md`) compared:
- Q8_0 on Pale (.39) → 82.3 tok/s
- Q4_K_S on Red (.245) → 127.7 tok/s

These are **different quantizations** of the same base model (Qwen3.8-27B). Acceptance requires the **same model_id on >=2 hosts** with latency delta quantified. A Q8-vs-Q4 comparison measures quantization effect, not host effect.

## What WOULD satisfy acceptance

| Requirement | Example |
|---|---|
| Same model on 2+ hosts | Qwen3.8-27B-Q4_K_S on White (:8091) AND Red (.245:8888) |
| Latency delta quantified | Mean tok/s per host, p50/p95 wall-time, n>=3 runs each |
| Recommendation made | "Host X is Y% faster for this model; assign latency-sensitive roles there" |

## Minimal viable path (no egress needed from sandbox)

1. **From White or Red directly** (terminal access on those hosts): run `model_benchmark.py` with the same model_id loaded on both seats.
2. Alternatively, if White has Q4_K_S already tracked by Studio routing (check `/v1/models`), issue 3 timed completions from a script ON that host and compare against the existing Red numbers (127.7 tok/s mean).
3. Write result to `memory/researcher/cross-host-comparison.md` with the table above filled in.

## Prediction

- **Effort:** ~10 min once on a host with terminal access (bench harness already exists).
- **Likely outcome:** White (dual-GPU, PCIe 4.0) will be within ±15% of Red for Q4_K_S; if delta >20%, the slower host should be flagged in the model-load governance doc.
- **Unblock step:** Any agent with terminal access to White OR Red runs the bench locally. No human action required — just a seat that can reach its own localhost:8888/8091.

## Risk / caveat

If White's Q4_K_S is currently unloaded (per 2026-11-16 note "White's own two instances were NOT benchmarkable"), the first step is `POST /api/inference/load` for that model on White, then bench. This is a normal load operation, not a blocker.
