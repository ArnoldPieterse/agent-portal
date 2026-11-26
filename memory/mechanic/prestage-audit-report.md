# Model Pre-staging Audit Report
Run: 2026-11-26T20:30:46.190812+00:00
SLA target: <120s recovery (Verifier goal #2)

## Variant Coverage
| Variant | Hosts | Count | Status |
|---------|-------|-------|--------|
| MTP | white | 1 | **GAP** |
| Q8_0 | black, pale, red, white | 4 | OK |
| UD-Q4_K_S | black, pale, white | 3 | OK |
| UD-Q4_K_XL | red | 1 | **GAP** |

## Agent-to-Variant Map
| Agent | Variant |
|-------|---------|
| Archivist | Q8_0 |
| Builder | Q8_0 |
| Designer | UD-Q4_K_S |
| Forge | Q8_0 |
| Lumen | UD-Q4_K_S |
| Mechanic | UD-Q4_K_S |
| Orchestrator | Q8_0 |
| Outlet | UD-Q4_K_S |
| Pixel | Q8_0 |
| Reel | UD-Q4_K_S |
| Researcher | UD-Q4_K_S |
| Scribe | Q8_0 |
| Splice | UD-Q4_K_S |
| Verifier | UD-Q4_K_S |

## GAPS (single-point-of-failure)
- **MTP** on white only; affects: 
  Risk: SINGLE-POINT-OF-FAILURE: host-down = full reload (120-240s)
  Fix: load MTP on one additional host (120-240s one-time cost)
- **UD-Q4_K_XL** on red only; affects: 
  Risk: SINGLE-POINT-OF-FAILURE: host-down = full reload (120-240s)
  Fix: load UD-Q4_K_XL on one additional host (120-240s one-time cost)

## Verdict: **GAP**

4 model variants across 4 hosts; 2 variant(s) below dual-residency threshold