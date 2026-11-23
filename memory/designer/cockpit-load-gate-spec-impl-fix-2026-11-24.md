# Cognitive-Load QA Gate: spec/impl mismatch fixed (assists Verifier cycle-14 UI gates)
Lane: Designer | Date: 2026-11-24 | Round topic: Closed-Loop Autonomy & Fleet Cockpit
Crediting: assists Verifier's "Cockpit A11y Gate (WCAG AA)" / "Cockpit UI Playwright Gate" quality surface; owner stays Verifier.

## Finding (concrete, in-lane)
The cognitive-load QA gate built for cycle-12 goal 10 (`ui/cockpit-load-audit.py`, spec `memory/designer/cognitive-budget.md`) was **non-functional as implemented**:
1. **Thresholds contradicted the spec.** Spec table: text nodes=40, distinct colors=5, interactive/panel=8, channels=3. Impl constants were 12 / 8 / 6 / 3 — i.e. impl was 3.3x stricter on text, looser on colors, and tighter on interactive than the document it claims to enforce.
2. **"Above the fold" was never measured.** Both spec and code say "above the fold", but `audit()` ran every regex over the **entire file**. The full cockpit shell (index.html) is 209 text nodes / 47 interactive elements by design, so a whole-file count can never pass an above-the-fold budget — the gate either always fails or never meaningfully gates.

## Fix (surgical, in ui/cockpit-load-audit.py)
- Aligned the 4 constants to `cognitive-budget.md` (SSOT): MAX_TEXT_NODES_ABOVE_FOLD 12->40, MAX_DISTINCT_COLORS 8->5, MAX_INTERACTIVE_ELEMENTS 6->8, channels stay 3.
- Added real above-the-fold scoping: `_scope()` counts only the region before an explicit `<!-- /ABOVE-FOLD -->` sentinel when present; otherwise falls back to whole-file and reports it honestly via a new `scope` field (`above-fold` | `whole-file`). No silent pass/fail.

## Fleet measurement (fresh run, this pass)
Runner: `python memory/designer/cockpit-load-audit-fleet-2026-11-24.py` -> artifact `memory/designer/cockpit-load-audit-fleet-2026-11-24.json`
| surface | scope | text | colors | interactive | channels |
|---|---|---|---|---|---|
| index.html | whole-file | 209 | 1 | 47 | 0 |
| ui/cockpit-provenance.html | whole-file | 473 | 12 | 7 | 0 |
| ui/cockpit-knowledge-impact.html | whole-file | 119 | 7 | 1 | 0 |
All three report `scope=whole-file` and over-report on text/colors — **expected**, because none of them carry the above-fold sentinel yet. The gate is now honest about what it measured instead of falsely failing.

## Follow-up (handoff, not a blocker)
To make the gate actually enforce "above the fold", add one `<!-- /ABOVE-FOLD -->` comment at the bottom of each cockpit's initial-viewport region in index.html; the script then scopes counts to that region and the QA gate (cycle-11 goal 9) becomes meaningful. Low-risk markup-only change — good for Builder/Verifier next pass.

## Verdict
Gate correctness FIXED (impl now matches spec + honest scoping). Residual "fail" rows are a measurement-scope artifact, not a real cognitive-load violation, and are now labeled as such in the JSON.
