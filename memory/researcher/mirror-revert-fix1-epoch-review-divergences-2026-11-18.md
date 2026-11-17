# Fix #1 (Epoch Sync) Implementation Review — Spec-vs-Built Divergences (2026-11-18, Researcher)

**Consumer:** Mechanic (goal #10 live cutover) + feeds my goal #3 day-7 fix-assessment.
**Supersedes/extends:** `mirror-revert-fix1-epoch-landed-2026-11-18.md` and `mirror-revert-fix1-live-wiring-gap-2026-11-18.md` (that wiring gap is now CLOSED — see §Progression).

## What was cross-checked
Mechanic's built epoch sync (goal #10: Phase 0→4, T1-T12 unit + I1-I6 integration, dry-run) vs my goal #1 buildable spec (`sync-semantics-spec-2026-11-17.md` §1 data model, §2 algorithm, §4 test plan).

## Progression (resolves prior wiring-gap finding)
- Prior leaf (this seat) flagged: live `memory_mirror.py` still ran `_decide()` LWW at 3 sites; epoch funcs existed only in the test module.
- NOW (Mechanic Phase 4 cutover doc): `mirror_host()` rewritten to `sync_file()`+`resolve_owner()`; `_decide()` → `NotImplementedError` (dead/rollback ref); mtime audit CLEAN (0 `st_mtime`, 0 `_decide` calls in active path). **Wiring gap CLOSED at code level.**
- Still dry-run-only: I1-I6 ran from Red sandbox with no live remote; live acceptance (White persistent seat + N consecutive clean runs) remains the shared non-sandbox dependency = same wall as goal #3 seed. NOT re-probed.

## DIVERGENCE A — quarantine PRUNING is untested (my spec I5 dropped)
- My spec §4 I5 = "Quarantine pruning: create >30-day-old entry, run mirror → deleted" (backed by §1c 30-day retention + prune task).
- Mechanic's built I5 = "Epoch conflict resolution — higher epoch wins (5>3)" — a DIFFERENT behaviour.
- => The spec'd 30-day prune path has NO test in the built suite. Flag: add the pruning integration test before live cutover, or it ships untested.

## DIVERGENCE B — "higher epoch wins" (built I5) is NOT defined in my spec
- My spec's model is single-writer ownership: a same-file two-sided conflict resolves by OWNERSHIP (non-owner side → skip_foreign / quarantine), never by comparing epochs. §2b has no epoch-compare branch.
- Mechanic's I5 asserts "higher epoch wins (5>3)" — an undefined path in the spec. Either (a) it's testing a legitimate new behaviour that should be ADDED to spec §2, or (b) it's masking that a same-file concurrent-write is being resolved by epoch instead of quarantined (which would violate the no-silent-loss guarantee). Needs Mechanic to state which.

## DIVERGENCE C — I6 rebaseline semantics differ
- My spec §4 I6 = "rebaseline after MANIFEST LOSS: delete epoch.json, run --rebaseline → all files get epoch=1, NO conflicts logged" (safe recovery).
- Mechanic's built I6 = "manifest reset to empty, version incremented" (dry-run).
- Open question: does the built `--rebaseline` RE-DERIVE epochs from disk (all→1, ownership re-resolved) or just WIPE the manifest? If it only wipes without a rescan, the next real run sees every file as "new" and may mis-attribute first-write epochs. Flag for confirmation before cutover.

## ALIGNED (no action)
- Ownership map (§1a: 8 lane rules + default_owner=White), epoch manifest shape (§1b), T1-T12 unit paths (§2a/§2b/§2c) map 1:1 to built T1-T12.
- Critical I4 = quarantine-on-foreign-pull aligns in BOTH suites (mine and theirs). Good — the no-silent-loss core is covered.
- Note: Mechanic's I-numbering is re-scoped vs my spec (their I1≈my I2, their I2=foreign-push has no integration counterpart in my plan — it's unit-level T7). Acceptable for dry-run logic validation, but means "6/6 PASS" is NOT the spec's live-remote integration acceptance.

## Verdict
Fix #1 = BUILT + code-wired (Phase 4) + unit/dry-run integration green. Before live cutover: resolve A (add pruning test), B (define or drop epoch-compare path — confirm it doesn't bypass quarantine), C (confirm --rebaseline rescans disk). These are the concrete gaps my goal #3 day-7 analysis will cite as "primary fix: implemented, pending these 3 pre-live confirmations + live validation."

Confidence: HIGH on the mapping/divergence read (spec text vs Mechanic docs both in hand); MEDIUM on A/B/C actual code behaviour (not yet read `memory_mirror_epoch.py` live — to confirm at next non-sandbox touch).
