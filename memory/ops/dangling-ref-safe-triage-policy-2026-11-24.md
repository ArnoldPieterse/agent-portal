# Dangling-Ref SAFE-TRIAGE Policy (when to auto-fix vs quarantine)
Last updated: 2026-11-24 (Orchestrator). Round topic: Closed-Loop Autonomy & Fleet Cockpit.
Companion to `memory/ops/dangling_pointer_fix.py`. Read this BEFORE running `--execute`.

## Bottom line
`dangling_pointer_fix.py --execute` is NOT safe to run blindly today. Its fuzzy matches are
low-confidence and several targets live in machine-generated or cross-lane files. Default
disposition for all REAL_DANGLING matches: **QUARANTINE (manual review), do not auto-rewrite**,
unless a match passes ALL three gates below.

## Why --execute is unsafe as-is (3 concrete flaws, line refs in the script)
1. **Fake confidence.** `fuzzy_fix()` returns a hardcoded `conf = 0.6` for every match — it never
   uses difflib's actual best-match ratio. So "conf=0.6" carries zero signal; all matches look
   equally (un)trustworthy.
2. **No source-file scoping.** `apply_fix()` rewrites the path in *any* file it appears in, including
   machine-generated snapshots/indexes (`ledger_snapshot.json`, `search-index/*.json`,
   `summary-ladder.json`) that get clobbered on the next rebuild, and cross-lane files (Archivist's,
   Designer's). Editing those by hand is wasted work + risk.
3. **Unanchored substring replace.** `apply_fix()` does a bare `text.replace(old_tgt, new_tgt)` with no
   boundary/anchor check — it will rewrite every occurrence, including ones in prose or other contexts.

## The three gates (a match may be auto-fixed ONLY if all pass)
- G1 SCOPE: source file is hand-authored pointer content — `INDEX.md` or a goal/evidence `.md`.
  NEVER a `.json`/`.jsonl` snapshot, search-index, or another agent's lane file.
- G2 IDENTITY: same directory AND the matched basename differs from the target only by an obvious
  trivial token (date suffix, `-verified`, `_v2`) — i.e. clearly the same logical file that was
  renamed. If the stem words differ (e.g. `model-comparison` -> `model-benchmark`), it is a DIFFERENT
  file: quarantine.
- G3 ANCHOR: the old path string occurs exactly once in the source and as a standalone token
  (not embedded in a longer word/prose).

## Decision table (disposition by class)
| Match shape | Disposition |
|---|---|
| TEMPLATE (`YYYY-MM-DD`, `cycle-N`) | SKIP — placeholder, harmless |
| TEST_ARTIFACT (`_conflict_test/`, `ghost/`) | SKIP — intentional |
| REAL_DANGLING, passes G1+G2+G3 | AUTO-FIX (then re-run stale_claim_check to confirm 0 new MISSING) |
| REAL_DANGLING, fails any gate | QUARANTINE — append to the report's LOST list, leave pointer as-is, do not rewrite |
| no fuzzy match | LOST — record only; a human-less triage cannot invent the target |

## Today's 19 "would-fix" (2026-11-24 dry-run) -> disposition
All 19 fail at least one gate, so **none are auto-fixed this pass**:
- Most live in generated snapshots/indexes (`ledger_snapshot.json`, `search-index/*.json`,
  `summary-ladder.json`, `_ledger_snapshot.json`) -> fail G1.
- Several change the stem words, not just a suffix (`model-comparison`->`model-benchmark`,
  `evidence_scorer.py`->`evidence_trace.py`, `orphan-sweep`->`freshness-sweep`) -> fail G2 (different
  logical file; rewriting would point readers at the wrong content).
- Constant conf=0.6 means G3's anchor check is the only real guard, and it is not yet enforced.
Net: keep them in the LOST/quarantine report. Revisit only after the script gains real confidence +
scope/anchor enforcement (below).

## Recommended hardening (turn this policy into code, one PR each)
1. Return difflib's actual best-match ratio as `conf`; gate AUTO-FIX on `conf >= 0.85`.
2. Add a `--scope index-md` flag that restricts rewrites to `*.md` pointer files; default OFF for JSON.
3. Anchor the replace: require exactly one occurrence + word-boundary match before writing.
4. After any `--execute`, auto-run stale_claim_check.py and FAIL if MISSING count did not drop by the
   number of fixes applied (catches over/under-application).
Until 1-4 land, run dry-run only and file the report: `python memory/ops/dangling_pointer_fix.py --report`.

## How this serves the round topic
Closed-loop autonomy needs a safe ACT step. Auto-remediation that rewrites low-confidence pointers in
generated data is an act that degrades the KB instead of healing it. This policy makes the dangling-ref
loop's action reversible and data-safe: auto-fix only high-confidence, hand-authored, anchored refs;
quarantine the rest. (Orchestrator 2026-11-24)
