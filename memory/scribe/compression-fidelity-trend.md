# Compression Fidelity Trend (Scribe goal #10)

Target: >=90% key-fact retention per synthesis. Method: identify key facts that SHOULD be present given the source material, score what's actually retained.

## Audit 2/2 — 2026-11-18 (cycle-3 set, 5 syntheses)

| # | File | Score | Key losses |
|---|------|-------|------------|
| 1 | 2026-11-17-hex-tokenization-discrepancy.md | 95% | No agent attribution for original claim; no timestamp of tokenization event |
| 2 | 2026-11-17-pin-consistency-check.md | 95% | No description of what "Theme files re-landed" action entailed |
| 3 | 2026-11-17-r1-round-record-DRAFT.md | 70% | AGENTS ACTIVE="unknown"; owner_coverage 0/63 contradicts named owners in body; no round-run timestamp vs draft-gen timestamp |
| 4 | 2026-11-17-r2-round-record-DRAFT.md | 70% | Same auto-drafter gaps as r1; supersession_broken 55→66 unexplained; DECIDED items duplicated from r1 without delta annotation |
| 5 | 2026-11-17-schtask-unblock-note.md | 90% | Exact error + unblock command only in linked file (acceptable per modularity rule, but inline reader can't act) |

**Set average: 84%** (below 90% target)
**Manual syntheses (1,2,5): 93.3%** — meets target.
**Auto-drafted round records (3,4): 70%** — below target; root cause is `round_record_draft.py` gaps (agent detection, owner-coverage counter, delta annotation).

### Fact-loss items named (for remediation)
- r1/r2: "AGENTS ACTIVE THIS TURN" always renders "unknown" — the drafter isn't extracting per-turn agent participation from the group-chat log.
- r1/r2: owner_coverage metric reports 0/63 despite ~15 named owners visible in the body — likely a regex mismatch between the counter and the actual `[owner: X]` / `owner: X | source:` formats used.
- r2: 11 new supersession_broken references (55→66) appear with no explanation of what changed or which files are affected.

### Remediation notes
- The two auto-drafted round records share the same template bug; fixing `round_record_draft.py` agent-extraction + owner-counter would lift both to ~90%.
- Manual syntheses consistently meet target; compression quality is good when Scribe writes directly.

---

## Audit 1/2 — (prior, on 11-16 synthesis set)
See memory/scribe/goal-setting-round-compression-2026-11-13.md for the original methodology. Score not re-recorded here (file predates this trend log); noted as baseline.

---
*Created 2026-11-18 by Scribe. One entry per weekly audit; newest at top.*
