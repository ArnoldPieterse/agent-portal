# PORTAL BUGS INDEX — PURE index (no detail here). Newest first.
Format: [status] symptom keywords -> file | one-line use case. Grep by symptom, open ONE leaf.
Last updated: 2026-11-15 (pointer paths normalized to root-relative; index_check sweep).

## Entries
- [FIXED] goal-stall loop / agents re-verifying closed work / dashboard 0% despite artifacts / index.html reverting to canonical / sandbox code edits vanishing -> memory/portal/bugs/goal-stall-loop-2026-11-16.md   prompt listed closed goals as open + push-only clobber + unregistered evidence; strict-ledger prompt block w/ closure procedure, merge queue, sweep counts artifacts, /api/goals/history
- [FIXED] terminal popups after reboot / visible cmd or net windows / pythonw child console -> memory/portal/bugs/popup-pythonw-children-recoverall-2026-11-15.md   CREATE_NO_WINDOW on all pythonw children + RecoverAll task via recover_hidden.vbs; verify by forcing the trigger path while polling EnumWindows
- [DONE] raw link shows source / HTML not rendered / MIME type / fix on disk but not live -> memory/portal/bugs/file-links-sandbox.md   /api/file/raw serves the real type (.html RENDERS); stale-process trap: schtasks /run no-ops on a Running task - kill PID first, prove CreationDate > LastWriteTime
- [DONE] sandbox refs 404 / folder refs / link echo / USERPROFILE env -> memory/portal/bugs/file-links-sandbox.md   _find_sandbox_dir() C:\Users\* scan + exact-path echo + folder peek/listing
- [DONE] agent files in Studio _default / Z:\ hallucination -> memory/portal/bugs/file-links-sandbox.md   no session_id -> shared sandbox; dual-root resolver + FILE ACCESS rule in shared memory
- [FIXED] @delegation dead room / cast scoping -> memory/portal/bugs/xtalk-completion.md   expandCast(): any @named agent enters the next round
- [BUILT] stop button / "no conclusion" despite work done -> memory/portal/bugs/xtalk-completion.md   user closes the run as concluded; aborts in-flight streams
- [RULE] agents claim builds w/o tool calls -> memory/portal/bugs/xtalk-completion.md   TOOLS discipline block in build_system_prompt (never say "built" without a successful tool call)
- [BUILT] round-end verdict / no output / truncated tools -> memory/portal/bugs/xtalk-completion.md   completion chips + verdict line after each group run
- [FIXED] [SILENT] infinite loop / early-return killed merge -> memory/portal/bugs/xtalk-completion.md   stop-flag on [DONE]; backend meta.silent is authoritative
- [ADDED] satisfaction / [CONCLUDED] signal -> memory/portal/bugs/xtalk-completion.md   model-declared conclusion breaks the cross-talk loop
- [ADDED] phase-aware rules / acks / counter mechanics / empty bubble roles -> memory/portal/bugs/xtalk-completion.md   prompt vs cross-talk behavior, _ack_nudge, RLock counter
- [FIXED] thinking bubble crash (first chunk per agent) -> memory/portal/bugs/ui-frontend.md   sec object vs stored {tb} fix
- [ADDED] reset button / busy hints -> memory/portal/bugs/ui-frontend.md   ↺ Reset zeroes counter; "working… Ns" indicators
- [BUILT] parallel async processing (Promise.all + RLock) -> memory/portal/architecture.md   frontend+backend parallel design, deterministic ordering
- [VERDICT] Studio serializes globally (parallel_slots=1) -> memory/portal/architecture.md   e2e + raw :8888 probe results; true parallel needs Studio-side change

## Global pointers
- -> agent_portal.py  server code;  -> index.html  frontend code;  -> MEMORY.md hot state
