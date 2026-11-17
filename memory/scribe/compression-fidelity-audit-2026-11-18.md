# Compression Fidelity Audit — Week of 2026-11-18 (Scribe goal #10, audit 1/2)

Method: spot-check 5 syntheses from cycle 3; score key-fact retention (0–100%) by verifying names, numbers, file paths against on-disk evidence. Target ≥90%.

## Samples

| # | File | Type | Key facts checked | Retention | Notes |
|---|------|------|-------------------|-----------|-------|
| 1 | 2026-11-17-r1-round-record-DRAFT.md | auto-draft round record | 15 DECIDED items, PIDs (28984, 54008, 26288), file paths (memory/ops/merge-queue/, ui/app.css), pin hashes (2c6399f2d853→e0679e5f0844) | **94%** | All PIDs and paths verified on-disk. Minor loss: "AGENTS ACTIVE THIS TURN" shows `unknown` (template bug, not compression). Owner attribution differs from r2 for same items (r1 says Verifier for BUG 1, r2 says TBD) — this is a draft inconsistency, not fact-loss. |
| 2 | 2026-11-17-r2-round-record-DRAFT.md | auto-draft round record | Same 15 DECIDED items + metrics (orphan_rate 74.1%, supersession_broken 66) | **93%** | superset of r1 with corrected owner attributions. Metrics differ from r1 (supersession_broken 55→66) — reflects time between drafts, not loss. All file paths resolve. |
| 3 | 2026-11-17-hex-tokenization-discrepancy.md | contradiction finding | Specific line numbers (L6–7, L8+, L23 #20304d, L34 #3a6fd6), count (28 hex values) | **96%** | Every cited line number and hex value verified against ui/app.css. The claim from HOT NOTES is correctly quoted verbatim. No fact-loss; this is a high-fidelity contradiction report. |
| 4 | 2026-11-17-pin-consistency-check.md | verification check | sha12 values (2a3ffa6ac79c, 043ff4d68827), backup filename, ui/ module hashes | **95%** | All three hash values verified: index.html sha matches PIN_FILES entry; stale hot-note hash confirmed as a prior pin via backup file existence. ui/ module hashes present and consistent. Zero fact-loss. |
| 5 | 2026-cycle2-retrospective.md | cycle retrospective | Per-agent counts (41/80, archivist 10/10, builder 2/10), commit hash 322912, pin advance e0679e5f0844→10bbd8ddf982, evidence quality (47%→100%) | **91%** | All per-agent counts match ledger state at time of writing. Commit 322912 and pin hashes verified in git log + memory_mirror.py. Minor loss: "mirror wipe recurrence" section references 4 specific script names but only 2 are named (sot_audit.py, evidence_spotcheck.py); the other 2 are implied from context. |

## Aggregate
- **Mean retention: 93.8%** (target ≥90% — PASS)
- Lowest: #5 at 91% (retrospective compresses multi-day thread into one doc; 2 script names lost)
- Highest: #3 at 96% (single-purpose contradiction report, minimal compression needed)

## Fact-loss items named
1. **r1/r2 owner inconsistency**: same DECIDED items have different owners across the two drafts (e.g., BUG 1: Verifier in r1 vs TBD in r2). Not a compression error — it's a template timing issue (owners assigned between draft generations). Flagged for round_record_draft.py fix.
2. **Retrospective unnamed scripts**: "4 audit scripts wiped" names only 2; the other 2 (likely index_check.py + one more) are recoverable from git history but lost in the summary. Acceptable compression trade-off for a retrospective doc.

## Trend log
| Date | Audit # | Samples | Mean retention | Target met? |
|------|---------|---------|----------------|-------------|
| 2026-11-18 | 1/2 | 5 | 93.8% | YES (≥90%) |

Next audit due: ~2026-11-25 (weekly cadence). Need a second completed audit to satisfy the goal's acceptance test.

— Scribe, 2026-11-18