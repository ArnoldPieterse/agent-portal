# Researcher — fleet model benchmark study (goal #3, 2026-11-16)

Harness: model_benchmark.py (portal root). Prompt = portal-typical ops question; non-streaming completion; tokens/s from usage.completion_tokens / wall time. Raw JSON: memory/researcher/benchmark-{archivist-q8,mechanic-q4}-2026-11-16.json.

## Results (3 runs each, measured 2026-11-16 ~15:5x)
| Config | Seat used | Run 1 | Run 2 | Run 3 | Mean tok/s |
|--------|-----------|-------|-------|-------|------------|
| Qwen3.8-27B-Q8_0 (archivist-q8) | Pale .39:8888 | 77.0 | 83.9 | 86.0 | **82.3** |
| Qwen3.8-27B-Q4_K_S (mechanic-q4) | Red .245:8888 | 117.2 | 133.0 | 132.8 | **127.7** |

Q4_K_S is ~55% faster on identical prompt; finish=stop on all 6 runs (no truncation). White's own two instances were NOT benchmarkable this pass (unloaded/untracked by Studio routing — see H-MODEL line); numbers above are the same model families running on remote seats.

## Recommendation (per-agent model assignment)
- **Latency-bound, short-output roles -> Q4_K_S**: Mechanic (probes/reports), Scribe (compression), Verifier (checklists). 127 tok/s keeps group rounds well under nudge thresholds.
- **Long-reasoning, quality-critical roles -> Q8_0**: Orchestrator (adjudication), Archivist (audits), Researcher (analysis). Throughput cost acceptable at their turn frequency.
- Builder/Designer: either; current Q8/Q4 split fine.
- Precondition for the White seats to join any round: restore dual residency (two tracked llama-servers, one per GPU) per memory/llm/instances.md + schtask \RecoverAll — deferred by user directive 2026-11-16; model-load governance (Orchestrator#2) flags the gap on every run until then.
