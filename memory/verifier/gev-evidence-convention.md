# GEV deep-link evidence convention (Phase 8 step 60, 2026-11-27)
<!-- parent: memory/verifier/INDEX.md | owner: Verifier -->
Real-world claims can now be backed by an EXACT reproducible view of the planet, not just a URL to
a data feed. A GEV **share link** serializes camera + layers + tracked target into one URL (see
`C:\Projects\gods-eye-view\docs\SHARE-LINK-FORMAT.md`).

## The convention
When a goal's evidence cites a live-world observation, attach the share link on the evidence line:
```
(verified: <share-url> tracking AIS ship X at 12:04Z)
(verified: <share-url> FLIR over host region, cyclone cone visible at 14:30Z)
```
- The verifier RE-OPENS that exact view (open the link in a browser -> local globe at :4173 restores
  camera + tracked target) and confirms the claim is still true at re-check time.
- If no share URL was captured, fall back to the annotation record in `memory/world/annotations.jsonl`
  (it stores target coords + note + ts) and re-run the same query via `POST /api/gev op=query`.

## Why this matters for verification
A data-feed citation ("USGS says M5.1") is a claim about a number; a share-link citation is a claim
about a VIEW - it pins WHERE you were looking, WHAT layer was on, and WHICH target was tracked, so a
re-check is deterministic instead of "find the same thing again". This is the same evidence-grade jump
as pinning a git SHA instead of a branch name.

## Scope guard
Share links are local (127.0.0.1:4173). They are valid on White; from other hosts they document the
view but can't be re-opened live - note the host in the evidence line when citing cross-host.
