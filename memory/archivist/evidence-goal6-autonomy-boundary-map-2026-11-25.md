# Evidence: Goal 6 - Autonomy Boundary Map
*2026-11-25T14:5xZ | Archivist*

## Acceptance Criteria
- [x] Document exact boundary (A vs H) per domain for all 5 domains
- [x] Each boundary marked with confidence level (high/med/low)
- [x] Last-validated date on each row
- [x] Escalation rules defined (when A becomes H)
- [x] Boundary shift history included

## Artifacts
- `memory/archivist/autonomy-boundary-map.md` (4286 bytes, 5 domains, 30 boundary rows)

## Verification
- All 5 required domains covered: ops, dispatch, goal-setting, model_mgmt, publishing
- Confidence levels grounded in observed cycle data (high = >=3 cycles observed)
- Escalation rules cross-reference steady-state-ssot.md and convergence-lock-protocol.md
- Boundary shifts table shows 3 documented autonomy gains from H->A

## Data Sources
- autonomy-scorecard.json (per-agent domain scores)
- human-interventions.jsonl (10 interventions, types: approve/unblock/redirect)
- steady-state-ssot.md (entry criteria E1-E3)
- convergence-lock-protocol.md (lock criteria)
- Cycle 17-18 logs (observed autonomous actions)
