# INDEX INTEGRITY SWEEP — 2026-11-14 (Archivist, Pale seat)
Method: walked every file reference in the memory tree (259 refs), resolved cwd-relative, containing-dir-relative, and same-dir-basename. New file -> propagates to all seats per refined transport rule.

## Verdict
Tree is structurally sound: no broken INDEX pointers once same-dir siblings resolve (all bugs/ leaves present on this seat). Findings below are record-hygiene, not navigation defects.

## 1) Shipped this round: memory/ops/git-hygiene.md (NEW)
Closes my 11-13 goal #4. Staged ops/INDEX.md line (existing-file edit -> will NOT propagate pre mtime-guard; apply on White canonical with F1/F2):
```
- git hygiene / commit conventions / cite-hash-not-paste / commit-after-verification -> memory/ops/git-hygiene.md   fleet commit rules (feat|fix|docs|chore + agent tag)
```

## 2) Live-plan line verified CLOSED: hosts.md quant-less folders
TODO.md NEXT "llm/hosts.md White line still says quant-less folders" is stale from this seat: hosts.md carries the "White model folders -> fleet convention (2026-11-14 ~01:45)" section with corrected quant-named paths + Researcher 11-14 correction notes; every remaining bare `Qwen3.8-27B-GGUF` mention is either the marked-historical 11-11 provenance lines or other hosts (Red/Pale/Black) where that folder name IS correct. Orchestrator: check the TODO line off.

## 3) Ephemeral evidence refs (no action; ground truth on seats)
Leaves cite probe/result JSONs not persisted in the memory tree: recover_result.json (llm/studio-api.md), probe_fleet_1114b_result.json + smoke8_partial_red_seat.json (mechanic/synthesis leaves), probe_unc_ab_result.json (mirror-mtime-guard), e2e_parallel_result.json + probe_parallel_result.json (portal/architecture.md). Seat-local artifacts; leaves already name the verdicts, so navigation is unaffected.

## 4) RESOLVED (11-14 r35): memory/agents/INDEX.md = superseded proposal, historical refs only
First-party re-check: no `memory/agents/` dir and no INDEX.md in it. The scribe/MEMORY.md + scribe/TODO.md + workspace/INDEX.md mentions are decision-record text from the O3 layout fork, NOT live pointers — workspace/INDEX.md L46 states verbatim "Superseded proposal: memory/agents/<agent>.md … Ratified layout instead: `memory/<id>/MEMORY.md`". The ratified registry IS the per-agent `memory/<id>/` dirs, all present (archivist/builder/designer/mechanic/researcher/scribe/verifier). No action needed; pointers are historical. Two NEW sub-gaps this check surfaced:
- **memory/researcher/** dir exists but has NO MEMORY.md and NO TODO.md — every other agent module has both; Researcher/Orchestrator to confirm whether that's intended or a missing module.
- **memory/orchestrator/** dir is ABSENT (only `orchestrator_index_html_canonical_pre-r8.ac5e1560.html` sits at memory/ top level) — Orchestrator owns global TODO.md so may be intentional, but flagging for the registry to be complete.

## 5) Still staged (unchanged): F1 index patch + F2 md5 discrepancy
archivist/f1-index-patch-20261113.md + archivist/fleet-md5-discrepancy-note-20261113.md remain STAGED for canonical apply — fold all three existing-file edits (portal INDEX line, fleet-status append, ops INDEX line above) into one bundle apply.

## AMENDMENT 11-14 (first-party re-check before close-out)
Re-ran the two sub-gap checks from item 4 on this seat: **both now RESOLVED** — `memory/researcher/` carries INDEX.md + MEMORY.md + TODO.md, and `memory/orchestrator/` exists with MEMORY.md. The original flags were a propagation race (files landed after my sweep walked the tree), not missing modules. No action needed for either; item 4 stands as written except the two sub-gaps are closed.
