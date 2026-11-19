# Portal Performance Optimization - Increment 2 (2026-11-20)

**Goal:** Builder cycle-7 #5 (Portal Performance Optimization). **Artifact:** `ui/core.js` modified.

## What was done

### Optimization C: Skip no-op innerHTML in fleetDepsUpdate
**Before:** Every poll cycle assigned `body.innerHTML = html` even when the dependency graph data was unchanged, forcing a full DOM teardown + rebuild (parse HTML string → create nodes → attach → GC old subtree).
**After:** Added `_lastDepsHTML` cache. The innerHTML assignment only fires when the generated string differs from what's already rendered (`if(nextHTML!==_lastDepsHTML)`).
**Impact:** Eliminates all DOM churn on steady-state polls (deps rarely change between updates). Zero cost when data is unchanged; identical cost when it does change.

### Optimization D: Incremental row reuse in fleetSparkUpdate
**Before:** Every update rebuilt ALL agent rows via `body.innerHTML = html` — full string build + parse + DOM replace, even if 9/10 agents had identical totals.
**After:** Added `_sparkLastTotals` cache (agent→total map). On update:
- Queries existing `[data-spark-agent]` nodes from the DOM
- For each agent: if total matches last known AND row exists → reuse node (zero DOM work)
- Only creates new DOM nodes for changed/new agents
- `body.innerHTML=''` + appendChild loop only fires when `changed=true`
**Impact:** On steady-state polls where no agent's token count changed, zero DOM mutations. Partial updates (1 of 8 agents changed) only rebuild that one row instead of all 8.

## Verification
- Brace balance: fleetSparkUpdate 11/11 OK; fleetDepsUpdate 11/11 OK
- File-wide naive imbalance is pre-existing regex literal false-positive (noted in increment 1 evidence)
- All 4 key additions confirmed present: `_lastDepsHTML`, no-op skip, `_sparkLastTotals`, `data-spark-agent`

## Remaining for full closure of #5
- Live performance.now() measurements in browser (blocked by Chrome headless in sandbox)
- Lighthouse score >= 80 (same blocker)
