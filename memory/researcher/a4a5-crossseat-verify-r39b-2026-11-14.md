# Researcher r39b — cross-seat verification of Verifier's A4+A5 lineage FAIL + new index.html variant (2026-11-14)

Seat: Researcher (sandbox _default). Method: full-tree md5 sweep (every file incl. `.git` objects, `uploads/`, `memory/`) + unified diff vs local canonical copy.

## Findings (all first-party, deterministic hashes → high confidence)

1. **Second independent confirmation of Verifier r39 absence.** NO file anywhere on this seat has md5 `45323d09717ac3a9dc0e098015863d81` (claimed A4+A5 applied pin, 68,633 B). The claimed bytes now exist on ZERO of three swept seats (Verifier r39 + this sweep). The close path "Arnold stamps 45323d09" rests on an unsourced hash with no byte source on disk.

2. **Transform artifacts absent here too.** Neither `a4a5_sim.py` nor `apply_a4_a5_r35.py` exists anywhere on this seat — only the Builder/Verifier leaf docs reference them (`memory/builder/a4a5-apply-r35-closeout-…`, `a4a5-lineage-and-revert-r38-…`; `memory/verifier/a4a5-verify-r38-…` 4fae67fc, `a4a5-lineage-repro-r39-…` 39057e1b). Verifier's repro base (`a4a5_sim.py` → a22ec518/68,634 B) is seat-local to his tree; the authoritative generator is missing from both trees.

3. **NEW — not in the record: this seat's root `index.html` = `8ef4e2227a7afd506ed2b55dc9dd170d` / 67,681 B ≠ canonical.** Diff vs canonical (`9c6b08e3…`, local copies at `memory/mechanic/index_html_pre-r14-9c6b08e3.html` and `memory/designer/index_html_black_5.html`) is EXACTLY ONE line, L140: `.aev .at{color:#6b7688;flex:none;width:64px}` → `#8b93a7` (activity-timeline timestamp color, lighter variant). Same byte-length → same 67,681 B size. This seat was already at 8ef4e222 in prior rounds (I reported it then) but it is NOT in the Orchestrator's per-file divergence table (which covered TODO.md/hosts.md/agents.json only), and Designer's "zero drift since r19 re-pin" is seat-local, not fleet-wide.

## Implications / asks
- **Arnold's White-console reference pair should include `index.html`:** expected canonical `9c6b08e3d98355e632a72cb871d5b60d`/67,681 B. If White disk shows `45323d09…` (claimed applied) or `8ef4e222…` (this seat's one-line variant), the lineage question resolves directly from ground truth.
- **@Builder:** persist the authoritative transform OR candidate as a NEW shared file (new files propagate; existing-file edits lose the mirror race — proven r16/r18/r23/r24). Verifier will re-run vs `.bak` and require byte-exact `45323d09…` or a corrected pin.
- **@Orchestrator:** add index.html to the per-file seat-divergence table: canonical 9c6b08e3 (Designer/Verifier seats) vs 8ef4e222 (Researcher seat, one-line `.aev .at` color delta).

## Open / uncertain
- Whether 8ef4e222 is a leftover A5 contrast experiment variant or an unpropagated applied edit — the single-line CSS delta is consistent with either; no leaf records its origin.
- What the missing 1 byte between a22ec518 (68,634 B) and claimed 45323d09 (68,633 B) was — not derivable without the authoritative script; not guessable without fabrication.
