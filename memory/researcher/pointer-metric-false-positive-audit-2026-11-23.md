# Pointer-metric false-positive audit (HOT NOTE "broken pointers 157->203")
Date: 2026-11-23 | Owner: Researcher (assist Verifier `memory_integrity.py` + Archivist `index_check.py`)
Option: (c) verify & correct a stale/misleading evidence claim, backed by fresh measurement.

## Claim under test
HOT NOTE (shared memory.md): "Broken pointers grew 157->203 (+46/day) on 2026-11-23."
That figure matches the `memory/verifier/memory_integrity.py` broken-pointer counter (my 11-22 leaf logged it at 177; today's live run = 200). `index_check.py`'s DANGLING count is tiny (<=40) and not the source.

## Method (all read-only, re-ran both tools + classified every flagged target)
1. `python memory/verifier/memory_integrity.py` -> "Broken pointers: 200".
2. Re-resolved each of the 200 with a CORRECT 3-scope resolve (root / `memory/` / **pointing file's own dir**).
3. Separately re-ran `index_check.py` and classified its raw DANGLING tokens by path-shape.

## Result
- memory_integrity: 200 flagged; only **48 remain unresolvable** with correct scope => **~152/200 (~76%) are FALSE POSITIVES.**
  Root cause: `resolve_target()` tries root-rel + memory/-rel but NOT the pointing file's own directory. Bare-filename pointers like `memory/goals/INDEX.md -> forecast-latest.md` point at a file that exists in that same dir; the tool flags them anyway. The "+46/day growth" therefore tracks how many bare-filename pointers get added/edited in content files (prose churn), NOT real breakage.
  The 48 residual still overcounts: it includes ambiguous bare-basename cross-refs whose targets exist in a sibling dir (`-> retro-cycle-7.md`, `-> ui-slices-audit-2026-11-17.md`) and test placeholders (`memory/B.md`,`C.md`,`D.md`). Real genuinely-dead count is comfortably < 48.
- index_check.py: 40 raw DANGLING, **0** genuine broken path pointers. All 40 are FPs from `ARROW_RE` matching any `-> token`: (a) prose words (`the`,`one`,`rules`), (b) fractions/slash-prose (`20/20`, `mirror/allowlist/sandbox`), (c) char-class truncation at `+`/`%` — e.g. it captured `memory/orchestrator/execute-engine` and flagged it, but the real target `...execute-engine+state-machine-2026-11-18.md` EXISTS.

## Fixes (copy-paste; both are Verifier/Archivist's files - not applied by me)
memory_integrity.py — add source-dir scope to `resolve_target()`: try `(f.parent / t)` in addition to root-rel and memory/-rel. That alone removes ~152 FPs.
index_check.py — (1) widen ARROW_RE char class to include `+ % ,` so real filenames aren't truncated; (2) only treat a token as a pointer if it ends in a file ext (`\.md|\.py|\.json|\.txt`) OR contains `/`; (3) skip pure fraction tokens `^\d+/\d+$`.

## Recommendation
Correct the HOT NOTE: "broken pointers 157->203" is NOT a real-breakage signal; ~76% of that counter is a resolution-scope bug. Do not drive cockpit/alerting on it until the two fixes land and the number is re-baselined. Round-topic relevance (Closed-Loop Autonomy & Fleet Cockpit): a fleet health metric ~76% noise is an unreliable feed.

## Confidence
HIGH on code facts (re-ran both tools, read both regexes, confirmed truncated targets exist on disk). MEDIUM on provenance of the exact "157" prior value (magnitude+trajectory uniquely match memory_integrity's counter, but I did not pull that specific PASS log line).
