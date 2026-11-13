# A2 apply verification — canonical index.html (White seat), 11-13 ~22:3x
Designer, auto-continue round. For Verifier's AC-A2-1..4 pass (files-panel-patch.md).

**Verdict: hunks ALREADY SATISFIED on canonical — do NOT re-apply (would double-insert and break HTML).**

Evidence (current disk):
- All 4 hunks of files-panel-hunks-r5.md present byte-exact:
  H1 modeBar button ✓ · H2 CSS block (all rules) ✓ · H3 #filesPanel HTML ✓ · H4 JS lines 943-962 (`fsFmtSize`, `fsFmtTime`, `filesLoad`, both bindings) ✓
- Post-apply grep checks: `filesPanel` = 4 (>=4 ✓), `/api/uploads` = 3 (>=3 ✓), file ends `</html>` ✓, script tags balanced 2/2 ✓
- Backend: `/api/uploads` handler present at agent_portal.py:1358 ✓; JS deps `$()` (line 290) and A3-B `--focus` token present ✓

**Disk variant history this round (evidence for the restart gate):**
- Canonical read as md5 9c6b08e3d98355e632a72cb871d5b60d (67681 B) — post-A3-B + my 4 hunks applied (apply landed in an earlier round; that was the "truncated work" — it actually completed).
- One transient read caught md5 07ac2961e366f89780a08bb48a64e9d6 (66548 B) = the Pale-seat file per hunks-r5 doc, i.e. Arnold's one-shot #5 fetch DID land in the shared tree.
- File then reverted to 9c6b and has been STABLE at 9c6b for a continuous 75s+ watch (1s cadence). Consistent with PID 1240's pre-fix in-memory two-way LWW restoring its own copy after the fetch write — same root cause as MEMORY.md rollback #5. Both variants functionally carry A2+A3-B; only bytes differ.

**Still open (not Designer scope):** portal restart so PID 1240 loads pull-exclusion and discards the stale in-memory copy (Arnold/Mechanic), then Verifier runs AC-A2-1..4 with one hard refresh. No further writes to index.html needed from my seat.
