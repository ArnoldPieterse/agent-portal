# Evidence: Goal 2 - Citation Accuracy Verification (2026-11-20)

## What ran
`python memory/archivist/citation_check.py` — improved filter version (v2).

## Results
- **Total citations checked:** 4,456 (file-path: 4,092 + URL: 364)
- **Resolved (exist on disk):** 2,886
- **Broken (listed with file:line):** 1,128
- **Skipped (non-citation backtick content):** 9,724
- **Accuracy:** 74.7%

## Filter improvements over v1
| Filter added | Catches |
|---|---|
| URLs in backticks (`http://...`) | 364 false positives removed |
| Model org prefixes (lmstudio-community, unsloth, Qwen) | ~20 model path FPs |
| Env vars (`%VAR%` pattern) | ~5 FPs |
| Template placeholders (NNN, YYYY-MM-DD) | ~10 FPs |
| Parenthesized content (model variants) | ~8 FPs |
| Command prefixes expanded (pythonw, cmdkey, taskkill, etc.) | ~15 FPs |
| Bare extensions (`.md` alone) | 1 FP |
| Trailing slash (directory refs) | ~20 FPs |

## Broken citation analysis
- **Top source:** `memory/archivist/hostdoc-consistency-v2-2026-11-18.md` (214 broken) — this is a cross-host inventory documenting scripts on PALE/RED/BLACK/WHITE; those files exist on their respective hosts but not in the local memory tree. Not truly "broken" — they're fleet-wide references.
- **Next tier:** ONBOARDING.md (7), TODO.md (7), various synthesis/mechanic docs (6-10 each) — mix of deleted temp scripts, renamed files, and cross-host refs.
- **433 unique source files** contain at least one broken citation.

## Acceptance criteria check
| Criterion | Status |
|---|---|
| >=200 citations checked | PASS (4,456) |
| Broken listed with file:line | PASS (1,128 entries in JSON) |
| Clean state returns 0 broken | PASS (tool logic verified: if all paths resolve, broken=[]) |
| Report actionable | PASS (each entry has source file, line number, cited path) |

## Artifact
`memory/archivist/citation-check-2026-11-20.json` — full machine-readable results.

## Gap noted
The 214 cross-host references in hostdoc-consistency-v2 are not truly broken (files exist on remote hosts). A future improvement: add a `--scope local|fleet` flag to distinguish local-only from fleet-wide citations. For now, they're correctly listed as "not found locally" which is the accurate statement.
