# white-rename-consistency-r21-addendum (Builder, 11-14 ~05:0x)

Supersedes one line of `white-rename-consistency-r20.md` (its "white_load_q8.py ... Now dual-path
via same _resolve() pattern; py_compile PASS" claim). Everything else in the r20 leaf stands.

## What happened
- r20 applied the dual-path fix to white_load_q8.py via in-place edit from this seat (Black).
  The edit reported success and was visible locally, but the next mirror pass pushed White's
  canonical (pre-fix) copy back over it: local edits to EXISTING files lose the sync race
  (consistent with Scribe r16/r18/r23/r24; my own probe round confirmed same pattern).
- Disk proof this round (Black seat, Z:\ mirror of shared root): white_load_q8.py still
  966d266e / stale hardcoded pre-rename path `lmstudio-community\Qwen3.8-27B-GGUF`, zero
  `_resolve` hits. So the r20 claim was never durable on canonical.

## Fix shipped this round (new file - new files DO propagate)
- `white_load_q8_r21_dualpath.py` (4,068 B): byte-identical to the stale script EXCEPT:
  (1) docstring r21 note; (2) `os` import; (3) Q8_PATH now via `_resolve()` copied verbatim
  from recover_all.py - prefer post-rename `Qwen3.8-27B-Q8_0`, fall back to
  `Qwen3.8-27B-GGUF`, SystemExit with explicit tried-list if neither exists (fail loud,
  never send a bad model_path - the v1 ABORT_unload lesson). Result filename unchanged
  (white_load_q8_result.json) so existing pollers keep working.
- Verified: py_compile PASS; shipped _resolve code extracted from the file and self-tested
  against temp dirs: pre-rename-only -> old folder OK; both present -> new preferred;
  neither -> SystemExit. ALL_SELFTESTS_PASS.

## Arnold action on White console (one step, then my lane is fully closed)
1. Replace white_load_q8.py content with white_load_q8_r21_dualpath.py (copy over), py_compile.
   Optional: delete the r21 file after swap so mirrors converge to one canonical script.

## State of the other two scripts (this round, Black mirror, hashes)
- recover_all.py 830ea09f - _resolve() dual-path present (L8-17), verified by read this round. OK.
- fleet_reload.py 0db431e4 - WHITE section L80 loads post-rename Q8_0 path; docstring L3 still
  references "white_load_q8.py recipe" (fine post-swap). OK.

## Cleanup
Deleted _builder_write_probe.txt and _builder_probe_r21.txt (write-anomaly probes, both rounds).

Builder White-rename lane: CLOSED pending Arnold's one-step swap; no other Builder items open.
