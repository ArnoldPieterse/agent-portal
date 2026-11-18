# Builder cross-assist handoff (2026-11-16)

## For @Mechanic (non-sandbox seat, White terminal):

### Close Builder #10 (commit discipline) — 1 command:
```bash
cd <shared-root>
git log --oneline --author="Builder" | grep -c "verified:"
# Then compare to total:
git log --oneline --author="Builder" | wc -l
```
If all commits carry "verified:", stamp `memory/goals/builder.md` goal #10 as verified.
My check script (alternative): `python memory/builder/check_commit_discipline.py`

### Close Builder #2 (uploads→remote mirror) — verification:
The SMB mirror is running (documented in architecture.md). To close:
1. Upload a test file via POST /api/upload (or drop in uploads/)
2. Wait ≤5 min for SMB sync
3. On each of Black/Red/Pale, confirm the file exists + is readable by that host's tools
4. Record: `memory/builder/remote-mirror-verify-2026-11-16.md`

### Designer patch REBASE WARNING:
Designer's `index-patched-v2.html` (sha12 376e88033931) is based on **stale pin df1bbdaef684**.
Live root is now **37549a041412** (Arnold's JS catch-block repair, L827).
Copying Designer's file over live would REVERT Arnold's fix.

**Correct action:** Apply Designer's 4 CSS/JS changes as targeted edits on top of the current pin.
The changes are additive (new CSS vars, new media queries, :active rules) — no overlap with L827.
See `memory/designer/patch-v2-evidence-2026-11-16.md` for the exact diff.

## Status: Builder 8/10
Open: #2 (needs remote verification), #10 (needs git log access)
Both unblock with one non-sandbox terminal session.
