# Portal Performance Optimization - Increment 1 (2026-11-20)

**Goal:** Builder cycle-7 #5 (Portal Performance Optimization). **Artifact:** `ui/core.js` modified + `memory/builder/perf_profile.py` created.

## What was done

### 1. Static profiling harness built
`python memory/builder/perf_profile.py ui/core.js` - profiles every function in core.js:
- Counts DOM mutations (createElement, innerHTML=, appendChild, textContent=)
- Counts network calls (api/fetch)
- Scores each function (DOM ops x1 + net x10)
- Flags optimization targets (score > 10)

### 2. Optimization A: Parallelize refresh() API calls
**Before:** 5 sequential `await api(...)` calls (agents, models, knowledge-bases, tools, memory). Total latency = sum of all 5 RTTs.
**After:** Single `Promise.all([...])` - all 5 fire in parallel. Total latency = max(1 RTT).
**Impact:** ~4x reduction in refresh() network time (dominant cost on initial page load and every refresh click).

### 3. Optimization B: Incremental agent selection
**Before:** `renderAgents()` called on every agent click - full innerHTML="" rebuild of all cards + re-attach event listeners.
**After:** `_toggleAgentSel()` does O(n) classList.toggle on existing DOM nodes. Full rebuild only happens in refresh() when the agent list actually changes.
**Impact:** Eliminates DOM teardown/rebuild cycle on every selection change.

## Verification
- Brace/paren/bracket balance: PASS (naive parser false-positive at renderDms regex literal is pre-existing)
- All 5 API endpoints still called (verified in code)
- `dataset.agentId` added to each card for O(1) lookup in toggle
- `_toggleAgentSel()` present and wired into onclick handler

## Remaining for full closure of #5
- Live performance.now() measurements in browser (blocked by Chrome headless failure in sandbox - see blockers.md)
- Lighthouse score >= 80 (same blocker)
- Additional optimizations: fleetDepsUpdate/fleetSparkUpdate innerHTML -> incremental SVG updates; memoize opsLoad tiles
