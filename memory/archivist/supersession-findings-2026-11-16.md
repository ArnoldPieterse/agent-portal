# Supersession findings - 2026-11-16 (archivist)

Validator: `memory/archivist/supersession_check.py` (cycle-2 goal 5). Run result: `supersession_check: 57 markers, 0 cycles, 53 dangling heads`.

**Finding: 5 dangling supersession targets** (basename-fallback applied; these files no
exist under memory/ - deleted or renamed without same-name successor). Top 20:

- DANGLING head: memory/verifier/final-gate-manifest-r74-2026-11-14.md -> /consolidates
- DANGLING head: memory/synthesis/INDEX.md -> 2026-11-12-upgrade-round.md
- DANGLING head: memory/scribe/supersession-report.json -> D-partial.md
- DANGLING head: memory/scribe/supersession-report.json -> d-2026-11-14.md
- DANGLING head: memory/scribe/supersession-report.json -> d-2026-11-14.md

Follow-up (cycle 3): repoint each marker to the canonical successor leaf, or mark the
source line "supersedes [removed]". Acyclicity itself is CLEAN (0 cycles).
