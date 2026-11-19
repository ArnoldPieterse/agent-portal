# Residency Matrix (goal #2) — offline acceptance surface 2026-11-20

**Artifact:** `memory/researcher/residency_matrix.py` (built this pass). Output: `memory/llm/residency-matrix.md`.

## What the tool does
- Expected residency = `{host: set(model.id)}` from `memory/llm/hotload-catalog.json` (`models[].host`). Currently only `white` carries 3 expected models (qwen3-27b-q8, qwen3-27b-q4, qwen3-5-4b-mtp); pale/black/red have no cataloged resident models.
- Actual residency = each host's `GET /api/inference/loaded-models` (fallback `/v1/models`), parsed to a set of loaded ids.
- Compare per (host, expected model): **OK** = expected+loaded; **DRIFT** = expected but not loaded; **EXTRA** = loaded but not expected; **UNREACHABLE** = host API returned no data (not counted as drift).
- Writes `memory/llm/residency-matrix.md` with per-host tables + total DRIFT count.

## Verified this pass (offline acceptance surface — all three surfaces MET)
1. **clean state → 0 drifts:** `--selftest` case [A] PASS; clean replay `--hosts {white:[all 3]}` → `drifts=0 extras=0`.
2. **deliberately unloaded model shows DRIFT:** `--selftest` case [B] PASS (unloads white:qwen3-27b-q4); degraded replay `--hosts {white:[q4,mtp]}` (dropping q8) → matrix row `qwen3-27b-q8 | yes | absent | DRIFT`, `drifts=1`.
3. **matrix reflects actual state:** live mode (`python .../residency_matrix.py`) ran and wrote the matrix from live API queries; from THIS sandbox seat all 4 hosts report UNREACHABLE (see blocker below) — that is the accurate reachable-state from here, not a logic failure.

Selftest output (verbatim):
```
catalog: 1 hosts, expected models: 3
[A] clean state          -> drifts=0 extras=0  (expect 0/0)  PASS
[B] unload white:qwen3-27b-q4 -> drifts=1 drifted=['qwen3-27b-q4']  (expect [that model])  PASS
[C] host unreachable     -> UNREACHABLE flagged, not counted as drift  PASS
SELFTEST PASS
```

## Live :8888 / LAN query leg — BLOCKED by documented egress wall (do NOT re-probe)
The tool's live path needs TCP to `127.0.0.1:8888` + `192.168.1.{245,39,99}:8888`. From a White sandbox seat every one of these fails with **WinError 10013** (sandbox egress block) — the SAME wall already recorded NEEDS-HUMAN in `memory/ops/blockers.md` (Orchestrator #2 Execute Engine :8888, Verifier #4 :8099, Mechanic #4, Red .245 LAN probe). One probe spent this pass; not re-probed.

## Unblock (one-time, non-sandbox White seat with :8888 + LAN egress)
`python memory/researcher/residency_matrix.py`  → writes a real `residency-matrix.md`. OR capture once into a JSON and replay offline: from the good seat save `{"white":[...loaded ids...], ...}` then run `python memory/researcher/residency_matrix.py --hosts <capture.json>` from any seat. Closure = real matrix with host rows populated + a deliberate unload flagged DRIFT, then `python memory/researcher/goal_ledger.py --record researcher 2`.

Status: **PROGRESS — offline acceptance surface MET (selftest PASS; clean=0 drifts; deliberate-unload=DRIFT).** Only the live query leg remains (egress wall). Same treatment as goal #1.