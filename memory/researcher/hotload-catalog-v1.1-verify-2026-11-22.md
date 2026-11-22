# hotload-catalog.json v1.1 — independent cross-source verification (2026-11-22)

Owner: Researcher (assist, LIVE-plan follow-up). Builder authored v1.1 today; this is an
independent static cross-check of that work against two authoritative in-repo sources.
Parent: memory/researcher/INDEX.md · sibling: memory/builder/hotload-catalog-refresh-2026-11-22.md

## Verdict
**PASS (static).** Catalog v1.1 is internally consistent and matches both canonical sources on
every checked field. Live-today residency NOT verified from this seat (egress wall, see below).
Recommend ticking the TODO item "refresh hotload-catalog.json" as DONE.

## Evidence (independent recompute, no trust in Builder's own leaf)
- **Host IPs vs memory_mirror_hosts.json** (canonical runtime map): pale=.39, black=.99,
  red=.245 — catalog matches all three EXACTLY. v1.0's Black/Red swap is fixed.
- **Residency layout vs memory/llm/hosts.md** (authoritative LLM host map, dated 11-14):
  - White: quinn-q4 UD-Q4_K_S GPU0 ctx131072 + atlas-q8 Q8_0 GPU1 ctx32768 ✓ (+MTP draft)
  - Pale: archivist-q8 Q8_0 GPU1 ctx32768 + designer-q4 UD-Q4_K_S GPU0 ctx65536 ✓
  - Black: builder-q8 Q8_0 GPU1 + verifier-q4 UD-Q4_K_S GPU0 ctx65536 ✓
  - Red: mechanic-q4 UD-Q4_K_XL GPU0 ctx65536 + scribe-q8 Q8_0 GPU1 ctx16384 ✓
  All model→quant→GPU→context→alias→agent mappings agree.
- **Per-host VRAM (recomputed from vram_gb)**: white 58.0/64 = 90.6% (only >90% host);
  pale 53.8 = 84.1%; black 53.8 = 84.1%; red 55.9 = 87.3%. Matches Builder's stated 84–91%,
  only-White-alerts claim exactly.
- **agents.json placement source is independently correct**: _fleet_bases() builds the seat
  candidate set from agents.json `studio` fields (NOT the catalog). Those IPs are already right
  (builder/verifier→.99=Black, scribe/mechanic→.245=Red, designer/archivist→.39=Pale).
  => CONFIRMS Builder's framing: live seat placement was already working; the v1.0 swap only
  affected the planning/accounting layer (vram_plan/cost_tracker/residency_matrix) + host naming.

## What remains UNVERIFIED / uncertain
- **Live residency today**: could NOT probe :8888/:8099 from this seat — python sandbox allowlist
  blocks fleet endpoints, and White's own local IP reads link-local 169.254.x (LAN iface down
  from this vantage). This is the established egress-wall condition seen in prior leaves; live leg
  needs a non-sandbox seat per memory/ops/live-leg-runbook-2026-11-20.md.
- hosts.md is dated 2026-11-14 and Black's Q8_0 has a known OOM-crash history (the overnight-unload
  phenomenon = my goal #3). So "catalog == what is resident right now" is plausible but unconfirmed.

## Recommendation
- Tick TODO "refresh hotload-catalog.json (stale: no remote models, black/red labels swapped)" DONE.
- Keep the SEPARATE "cross-host LOAD (not just resident) when home down + nothing resident anywhere"
  item OPEN — _resolve_seat() has no such path; it falls back to P1 home hot-load.

Confidence: HIGH on static consistency vs canonical sources (two independent files agree, field-by-field).
MEDIUM/UNVERIFIED on live-today residency (egress wall).