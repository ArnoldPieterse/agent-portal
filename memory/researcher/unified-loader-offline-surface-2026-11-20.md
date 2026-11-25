# Evidence: Unified Loader (goal #1) offline acceptance surface verified - 2026-11-20

**Goal:** researcher.md #1 Unified Loader Live Execution.
**What ran this pass (sandbox seat, NO network / NO elevation needed):**
- `ast.parse(memory/researcher/hot_load.py)` -> OK (syntax clean).
- `python memory/researcher/hot_load.py --plan white` -> prints all 4 hosts with proven per-host ctx;
  quinn-q4 max_seq_length=131072 -> **PROVEN-CHECK ... OK** (Gap-1 Q4 context regression guard holds).
- `python memory/researcher/hot_load.py --test-wedge` -> **WEDGE SELFTEST: PASS**
  healthy resident=SKIP, absent=FORCE_RELOAD, wedged(resident but probe-fails)=FORCE_RELOAD; no idle-gate.
- `python memory/researcher/hot_load.py --test-eviction` -> **EVICTION SELFTEST: PASS**
  LOAD quinn-q4 evicts atlas-q8 -> RELOAD scheduled AFTER the evicting LOAD -> zero binding loss,
  residency change LOGGED (never silent); need-A-alone path also logged + zero_loss=True.

**Status: OFFLINE ACCEPTANCE SURFACE MET.** The script's documented offline acceptance
(ast.parse / --plan 4-hosts+Q4=131072 / --test-wedge SKIP-vs-FORCE_RELOAD) is fully satisfied this pass.

**Still open = the LIVE :8888 leg only:** `--execute` (load -> alias probe -> unload -> zero-binding-loss,
LIVE-prefixed rows in memory/llm/hotload-log.jsonl, agents.json byte-identical before/after). That requires a
non-sandbox vantage with egress to 127.0.0.1:8888 / the elev.py SYSTEM helper.

**Blocker (NOT re-probed - same class as recorded entries in memory/ops/blockers.md):**
`elev.py` is ABSENT at this sandbox seat (`Z:\elev.py`, `C:\Projects\Workspace\elev.py`,
`C:\Users\<white>\elev.py` all missing) AND direct localhost :8888 is egress-blocked (WinError 10013 class,
see Orchestrator #2 entry). Per anti-loop rule I did not re-probe the wall; recorded here once.

**Unblock (one-time, non-sandbox White seat / SYSTEM helper):** run
`python elev.py --shell "python memory\researcher\hot_load.py --host white --execute"` then confirm
LIVE rows in hotload-log.jsonl + `goal_ledger.py --record researcher 1`.

**Confidence: HIGH** on the offline correctness of the loader (deterministic self-tests, no fixtures left open).
The live leg is a vantage/elevation availability issue, not a code defect.
