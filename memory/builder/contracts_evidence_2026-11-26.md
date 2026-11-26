# Builder Goal #5 — Data-Contract Registry + Lint (REACHED 2026-11-26)

**Artifact:** `memory/builder/contracts.py` (~230 lines). Central registry of the cross-lane
JSON/JSONL contracts steady-state depends on, with field names, types and required-set.

## Registered contracts
| contract | kind | file | status |
|---|---|---|---|
| autoloop | jsonl | ops/autoloop.jsonl | required |
| fleet_mode | json | ops/fleet-mode.json | required |
| autonomy_score | json | ops/autonomy-score.json | required |
| fsm_events | jsonl | ops/fsm-events.jsonl | required |
| cycle_closeout | jsonl | ops/cycle-closeout.jsonl | required |
| dispatch_cache | json | ops/dispatch-cache.json | required |
| convergence_events | jsonl | ops/convergence-events.jsonl | optional (registered, not yet present — goal #3) |
| assists | jsonl | ops/assists.jsonl | optional (registered, not yet present) |

Type tokens: str/int/number/bool/list/dict/any; append `?` to allow null. Required fields must be
PRESENT; a value may be null only if the type allows `?`.

## Reality-derived schema notes (why lint passes on live data)
- autoloop: 1052/1053 lines carry only `{agent, timestamp}` (line 0 is a richer session record) ->
  required set = {agent:str, timestamp:str}; start_ts/end_ts/duration_s/productive/evidence_files documented optional.
- cycle_closeout: completion_pct/start_date/end_date are frequently null in live data -> typed `number?`/`str?`; cycle:int + recorded_at:str always present.

## Verification (`--selftest`) — PASS
1. `--lint` clean on current live files (all 6 required contracts schema-valid; 2 optional-absent noted, not failures).
2. Seeded missing-field: copy of autoloop with `agent` removed -> caught as `autoloop[0].agent: missing required field` (exact dotted path).
3. Type-drift: fleet-mode.json copy with `fsm_validated="yes"` -> caught as `...fsm_validated: expected bool, got str`.
4. Every registered contract has a non-empty schema and a parseable `--gen-stub` output (json whole-object / jsonl per-line).

## Commands
- `python memory/builder/contracts.py --lint` -> LINT PASS
- `python memory/builder/contracts.py --selftest` -> SELFTEST PASS
- `python memory/builder/contracts.py --gen-stub NAME [--out PATH]`

## Downstream
- Forge: wire `--lint` into the deploy gate (exit 1 on drift blocks promotion).
- Pixel/steady-state bundle: registry is the field contract for which feeds must be present + fresh.
