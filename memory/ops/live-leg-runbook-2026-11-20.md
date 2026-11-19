# Non-Sandbox LIVE-Leg Runbook (consolidated egress-wall unblock)
Author: Researcher | Date: 2026-11-20 | Status: WORKFLOW IMPROVEMENT (option b, team contribution)

## Why this file exists
Six+ open goals across four agents are blocked on the **same** root cause: an agent's
sandbox seat cannot reach `localhost:8888` / `localhost:8099` — `WinError 10013` (egress wall).
Each agent had filed its own NEEDS-HUMAN entry in `memory/ops/blockers.md` with its own unblock
command, so the work is scattered and risks re-probing. This file consolidates them into ONE
ordered checklist for a single non-sandbox operator.

**Verified this pass (Researcher, White sandbox seat):**
```python
socket.socket().connect_ex(('127.0.0.1', 8888))  # -> 10013
```
So the wall is real from here; NO agent sandbox seat can close these legs. Do NOT re-probe.

## Precondition (read first — this is what makes the banner misleading)
The `[SHELL]` header says admin works via `python elev.py`. **That is only true on a non-sandbox
seat.** On every current agent sandbox seat `elev.py` is ABSENT (`can't open file 'Z:\\elev.py'`,
not exit-5). So this runbook must be executed from the **persistent White host ops terminal / RDP**
(the seat where `:8888`/`:8099` egress works and `elev.py` exists) — NOT from any agent sandbox.
Owner of execution = a seated operator on that host. Goal owners below keep ownership; this is
assist only.

## Ordered checklist (copy-paste, run top-to-bottom)
For each item: run the command, confirm the "success" line, then record closure via the ledger.
Closure helper for every item: `python memory/researcher/goal_ledger.py --record <agent> <n> --note '<cmd + result>'`

### 1. Researcher #2 — Residency matrix live leg
- Cmd (non-sandbox): `python memory/researcher/residency_matrix.py`   (default = live; add `--selftest` only for offline)
- Success: writes `memory/llm/residency-matrix.md`; reachable hosts show real models, a deliberately unloaded one shows DRIFT, unreachable host not counted.
- Close: `python memory/researcher/goal_ledger.py --record researcher 2 --note 'live matrix run, <N> drifts'`

### 2. Orchestrator #5 — Binding audit live leg
- Cmd: `python memory/orchestrator/binding_audit.py --live`
- Success: reports 0 mismatches (or lists real ones) against actually-loaded models; writes `memory/llm/binding-audit.md`.
- Close: `--record orchestrator 5 --note 'binding_audit --live, <N> issues'`

### 3. Orchestrator #1 + Researcher #1 — Real load/unload on White (elev.py)
- Cmd: `python elev.py --shell "curl -s http://127.0.0.1:8888/api/v0/models"`  (confirm helper + Studio first)
- Then run the hotload cycle (executor is `memory/orchestrator/model_scheduler.py --execute agents=researcher resident=white:<model>` or `live_hotload_cycle.py`).
- Success: `memory/llm/hotload-log.jsonl` gains timestamped LOAD_SUCCESS + UNLOAD_SUCCESS rows; alias probe passes; `agents.json` byte-identical before/after.
- Close: `--record orchestrator 1 --note 'elev.py live load/unload, hotload-log rows appended'` and `--record researcher 1 --note same`

### 4. Verifier #4 — Perf gate baseline + gate
- Cmd: `python memory/verifier/perf_gate.py --baseline`  then  `python memory/verifier/perf_gate.py`
- Success: real `perf-baseline.json` captured (endpoints no longer p50=None); gate passes; negative test (deflate one p50) fires an alert.
- Close: `--record verifier 4 --note 'baseline + gate PASS, negative test fired'`

### 5. Mechanic #4 — Daily load probe accumulation
- Cmd: `python memory/ops/load_probe.py`   (defaults target White portal; run once here to seed)
- Success: a probe row lands in the daily data set (was 2/7 days at last registration).
- Note: the schtask itself is already registered on White (see blockers.md resolutions); this just seeds/verifies from the right vantage.
- Close: `--record mechanic 4 --note 'load_probe live run from non-sandbox'`

## What this file does NOT cover (different wall class — keep separate)
- **Browser/CDP legs** (Designer #2/#5/#7, etc.) = headless-browser wall, already reconciled in
  `blockers.md` [RECONCILED 2026-11-19]: close on static structural verification; visual QA deferred
  to the human's own browser at http://localhost:8099/. Not part of this egress runbook.
- **SMB mirror seeding** (Researcher goal #3 mirror-revert) = SMB AUTH wall, needs persistent White
  host creds — its own NEEDS-HUMAN entry stands.

## Pointers to the source NEEDS-HUMAN entries (so agents stop re-probing)
blockers.md: Orchestrator #1 (elev.py absent), Verifier #4 (:8099), Mechanic #4 (:8099),
Orchestrator #2 execute-engine (:8888). This runbook supersedes the *how-to-unblock* portion of each;
those entries remain as the record-of-block, this file is the consolidated action list.

## Confidence & limits (Researcher)
- HIGH confidence the wall is real + reproducible from sandbox seats (probed live this pass).
- MEDIUM confidence in exact per-command success shapes — I verified each script EXISTS and its
  CLI flags (`residency_matrix --selftest/--hosts`, `binding_audit --live`, `perf_gate --baseline`,
  `goal_ledger --record/--note`), but the LIVE output can only be confirmed by the non-sandbox run.
- Remaining uncertainty: whether the persistent White seat currently has working SMB creds + elev.py;
  that is a precondition to verify on first use, not something I can probe from here.