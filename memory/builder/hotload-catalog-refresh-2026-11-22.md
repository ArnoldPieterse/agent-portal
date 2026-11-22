# hotload-catalog.json refresh — 2026-11-22

**What was wrong (v1.0, 2026-11-17):**
1. Black/Red IPs swapped: catalog had black=.245, red=.99; hosts.md confirms black=.99, red=.245.
2. GPU specs stale: all 4 hosts are 2× RTX 5090 32GB = 64GB total; catalog said white=2/32GB, pale/black/red=1/16GB each.
3. No remote model entries: only White's 3 models listed; Pale/Black/Red residency invisible to vram_plan/cost_tracker/residency_matrix.

**Fix (v1.1):**
- Corrected all host IPs + GPU counts + VRAM totals to 64GB.
- Added 6 remote model entries (2 per remote host) matching live residency from hosts.md:
  - Pale: Q8_0 (archivist-q8, GPU1) + Q4_K_S (designer-q4, GPU0)
  - Black: Q8_0 (builder-q8, GPU1) + Q4_K_S (verifier-q4, GPU0)
  - Red: UD-Q4_K_XL (mechanic-q4, GPU0) + Q8_0 (scribe-q8, GPU1)
- Bumped version to 1.1, updated date.

**Verification (Python simulation of all 3 consumers):**
- `cost_tracker.py`: sees 4 unique model→vram entries ✓
- `vram_plan.py`: per-host usage 84–91%, only White triggers >90% alert (correct: Q8+Q4+MTP = 58GB/64) ✓
- `residency_matrix.py`: expected residency now covers all 4 hosts × 2 agents each ✓
- IP cross-check vs hosts.md: all 4 match ✓

**Impact:** `_resolve_seat()` in agent_portal.py does live probes (not catalog), so placement was already working; this fix corrects the **planning/accounting layer** that sits above it. VRAM-aware load decisions and cost tracking now see the full fleet.

**Still pending (next step):** cross-host LOAD path when home is down AND nothing is resident anywhere reachable (currently falls back to P1 hot-load on home; a true "load on nearest available host" path would be the next increment).
