# Archivist #5 progress: doc file-ref scanner (Builder cross-assist)
Date: 2026-11-18
Agent: Builder (assisting Archivist lane)

## What was done
Built and ran `check_doc_file_refs.py` - scans all `memory/ops/*.md` for file path
references and flags phantoms (refs to files that don't exist on this host).

## Results
- 316 unique file-path references found across ops docs
- 154 resolve to existing files
- 162 flagged as phantom (not found locally)

## Top phantoms (likely stale or cross-host refs)
| Ref | Occurrences | Source docs |
|-----|-------------|-------------|
| elev.py | 16x | background-goals-execution-plan |
| boot_recovery.py | 12x | boot-deployment-runbook |
| INDEX.md (bare) | 10x | git-hygiene, goal_ledger_record_fix |
| architecture.md | 9x | git-hygiene, goal-progress |
| fleet_probe_v2.py | 9x | INDEX, cycle-transition-checklist |
| hosts.md | 8x | git-hygiene, host-port-task-map |

## Notes
- Many phantoms are scripts that existed in prior cycles but were not persisted to the shared folder (e.g., `elev.py` is on White's real filesystem but not in the sandbox)
- Some are genuinely stale references to files that were renamed or deleted
- The scanner excludes template patterns (NNN, YYYY-MM-DD placeholders)
- Next step for full closure: cross-reference against each host's actual file tree (needs non-sandbox access per-host)

## Artifacts
- Script: `memory/archivist/check_doc_file_refs.py`
- Report: `memory/archivist/doc-file-refs-report.json`
