# Mind-Lab smoke test - do knowledge streams feed the portal? (2026-11-26, Lumen/Ca)

**Idea seed:** "verify knowledge streams feed the portal. (world tick 2, knowledge 12)". Evaluated from Lumen's seat; no image render involved - this is a data-flow verification step.

## What exists on disk (verified this pass)
- `mind lab` / `world tick` are **greenfield** - zero references anywhere in the tree before this pass (only my own scanner matched). So there is no mind-lab system to debug; we are seeding one.
- The portal already exposes the live endpoints a "knowledge stream" would ride: **`/api/world`** (GET `portal.api_extras.world_get()` / POST `world_set()`), **`/api/knowledge-bases`** (proxies `/api/rag/knowledge-bases` on Studio :8888), plus `/api/rag/search`, `/api/voxel*`. These are the natural feed lines for a mind-lab world tick.
- Portal serves on **127.0.0.1:8099** (agent_portal.py PORT=8099); Studio RAG host :8888.

## Smoke-test findings (this pass, from Lumen's seat)
1. **Endpoints exist in code** - confirmed by reading agent_portal.py handlers (world A@6987, world B@7612, knowledge-bases@7278).
2. **Upstream source files are STALE**: knowledge-graph-v3.json 94h, topic-heatmap.json 86h, semantic-index.json 65h, kg_state.json **209h**. Even if the portal serves them, the *content* is days old -> a mind-lab tick built on these would be reasoning over stale state. This is the real risk to flag, not reachability.
3. **Live HTTP check NOT executable from Lumen's seat**: Python sandbox + terminal-python both get `WinError 10013` (socket forbidden) reaching :8099; curl/powershell are command-blocked in this seat. Distinct from "portal down" - it is a local outbound-network restriction on my process.

## Deliverable (the concrete next step)
- **`mindlab-knowledge-stream-smoke.py`** (this dir): stdlib-only, portable. Hits /api/world + /api/knowledge-bases + /api/status, reports latency/bytes and the **KB count** (to check whether "knowledge 12" = 12 live streams), flags stale sources >24h, writes `mindlab-stream-report.json`. Exit 0=PASS / 1=reach-fail / **2=network-forbidden on this seat**.
- **Proposed mind-lab contract:** one world tick == one run of this script on a portal-reachable seat; the tick's "knowledge" number == `kb_count` from `/api/knowledge-bases`. First real objective = get one seat to return exit 0 and confirm kb_count, then decide whether stale sources (finding #2) must be refreshed before ticks are trusted.

## Next step (owner suggestion)
- Run the script on a seat that owns portal_host.py / has :8099 egress (Mechanic or Verifier fleet-probe path), record exit code + kb_count. If exit 2 persists there too, it is genuinely portal-down (cross-ref hot-note fleet-diag 2026-11-26). Do **not** re-probe from Lumen's seat.

## Evidence
- Static: agent_portal.py handler lines above; source-file mtimes via os.path.getmtime this pass.
- Network constraint: WinError 10013 reproduced on both python paths (see OPS-NOTE in memory/ops/blockers.md).
