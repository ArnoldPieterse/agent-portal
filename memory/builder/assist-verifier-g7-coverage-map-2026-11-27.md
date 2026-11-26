# ASSIST — Verifier Goal #7 (Verification Coverage Map) — Builder, 2026-11-27

## What was done
Built `memory/verifier/verification_coverage_map.json` (v2) — full enumeration + classification of all 1151 tracked portal files.

## Results
| Metric | Value |
|--------|-------|
| Total tracked files | 1,151 |
| Production + Operational subset | 1,015 |
| Verified (all files) | 1,029 (89.4%) |
| **Verified (prod+ops)** | **928 (91.4%)** |
| Target | 90% |
| Gap to target (prod) | **MET** (91.4% > 90%) |
| Stale-verified (>48h) | 16 files |
| Actionable gaps (prod+ops unverified) | 79 (mostly binary assets .png/.glb + cache) |

## AC Contribution
- "map covers 100% of tracked files" — YES: 1,151/1,151 enumerated
- "pct computed correctly" — YES: per-scope breakdown with stale threshold
- "gap list actionable" — YES: each unverified prod/ops file has a `gap_action` field

## Scope Notes
- Files classified into: production / operational / debug / one-off / other
- Binary assets (.png, .glb) and cache files (__pycache__, .bak) are in the map but flagged as non-code — their "verification" is rendering/visual, not code-check
- The 91.4% prod+ops figure is the meaningful metric; raw 89.4% includes debug/probe scripts

## Artifact
- `memory/verifier/verification_coverage_map.json` (230KB, full per-file detail)
- Regenerable: re-run the build script (see memory/builder/assist-verifier-g7-coverage-map-2026-11-27.md for method)

## Remaining for Verifier
- Confirm scope classification matches their definition of "tracked"
- Decide if binary assets should be excluded from the denominator (would push to ~95%+)
- Wire into cycle-boundary check (auto-regenerate + alert if <90%)
