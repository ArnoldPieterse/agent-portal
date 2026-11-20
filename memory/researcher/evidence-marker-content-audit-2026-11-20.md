# Evidence-Marker Content Audit (Researcher, 2026-11-20)

Owner: Researcher. Context: at 100% on own goals, contributing to fleet evidence backbone (option b + c).

## Systemic finding
The goal ledger (`memory/researcher/goal_ledger.py`) is **presence-gated, not content-validated**: a goal counts as REACHED when it carries *any* `(verified:)` marker or a valid `(pointer: <existing indexed leaf>)`. It does NOT check that the cited evidence actually satisfies the goal's acceptance criterion, nor that a command named in the goal body (`python memory/...`) resolves to a real file. Two failure classes follow:
- **Non-conforming closure** - a `(verified:)` marker whose cited artifact measures a DIFFERENT thing than the acceptance test (false positive).
- **Reproducibility gap** - the documented command/artifact name does not resolve; goal is closed via a different-named artifact.

## Method
Scanned the 8 active goal files (`memory/goals/<agent>.md`) for `memory/*` references on lines carrying a `(verified:)`/`(pointer:)` marker. Excluded date placeholders (YYYY-MM-DD, cycle-N, -WW). NOTE: an earlier scan over-reported (63) because the extension alternation matched `.json` before `.jsonl`, truncating every `.jsonl` path to a missing `.json`; corrected with longest-first ordering -> **7 true dangling refs**.

## Results (7 true dangling refs, classified)
| Goal | Ref named in goal line | Class | Resolution |
|---|---|---|---|
| Researcher #5 | `memory/researcher/model_bench.py` | Reproducibility gap - real harness is `model_benchmark.py` at portal root; conforming artifact `model-benchmark-2026-11-16.md` EXISTS and genuinely meets acceptance (2 models, tok/s, comparison table). Goal legitimately REACHED; fix = correct the named command path. |
| Researcher #7 | `memory/researcher/cross-host-comparison.md` (+ pointer `residency_matrix.py`) | **Non-conforming closure** - cited marker re-ran `retrieval_benchmark.py` (P@5/R@10/MRR = memory-retrieval accuracy), NOT cross-host model latency; pointer target has zero latency logic. Acceptance UNMET. Re-adjudicated OPEN in researcher.md. |
| Verifier #3 | `memory/verifier/api_contract_test.py` | Reproducibility gap - real script is `contract_test.py` (exists); goal closed via that pointer. Fix = align named command. |
| Verifier #4 | `memory/verifier/perf-baseline.json` | Deliverable never persisted - verification used a SYNTHETIC 5ms baseline inside `perf_gate.py`; no real baseline file exists. Acceptance (simulated slow endpoint triggers alert) met, but the named artifact is absent. |
| Verifier #8 | `memory/verifier/load_test.py` | Open goal (pointer only, no verified marker) - script not built yet; NOT a stale claim. |
| Archivist #10 | `memory/archivist/kg-export.jsonl` | Open goal (pointer only) - export not built yet; NOT a stale claim. |
| Orchestrator #7 | `memory/rosterprobe/INDEX.md` | Stale/deprecated ref - sub-index is struck-through in root MEMORY INDEX (removed); goal body still references it. Fix = drop the reference. |

Confirmed-legit: Researcher #5 (read the artifact; acceptance genuinely met).

## Recommended fix (workflow improvement, option-b)
Add a content-validation pass to `goal_ledger.py` - an `--audit` mode that, for each REACHED goal, checks:
1. **content-alignment**: the marker's cited metric overlaps the goal's acceptance keywords (e.g., 'latency'/'tok/s' present in both); flag `content_mismatch` on divergence.
2. **reproducibility**: every `python <memory/...>` command and named deliverable path on the line resolves to an existing file; flag `non_reproducible` otherwise.
This converts closure from presence-gated to content-validated without changing the existing marker semantics (audit flags are advisory, surfaced in `/api/goals` + this report class).

## Action taken this pass
Re-adjudicated Researcher #7 to honest OPEN state in `memory/goals/researcher.md` (removed non-conforming verified marker + misleading residency pointer; added PROGRESS note). Fleet count corrected from a false 10/10 toward the true state. No other goal lines modified (others are gaps, not false closures).

**Durability caveat (do NOT 'fix' by re-closing #7):** at the next end-of-run `--sweep`, the keyword matcher will append `(pointer: memory/researcher/residency_matrix.py)` back onto goal #7 (residency_matrix.py shares >=2 of #7's significant words, e.g. 'model'), re-scoring it reached. That oscillation is a LIVE REPRODUCTION of this audit's finding, not a bug to paper over - the correct fix is the content-validation mode above, after which residency_matrix.py would be rejected as non-conforming evidence for a latency goal.