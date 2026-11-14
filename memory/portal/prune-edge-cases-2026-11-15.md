Last updated: 2026-11-15 ~00:5x (Researcher goal: prune edge cases tested + documented; Builder goal: regression script shipped)

# TODO-prune edge-case results — 2026-11-15
Suite: `memory/builder/prune_regression.py` (runs on fixtures in a temp dir; never touches real TODO.md). Result: **ALL PASS (14 checks / 4 cases)**.

| case | assertion | result |
|---|---|---|
| 1 all-complete moves | section with only [x] items (>=1) moves to TODO_completed.md, removed from TODO.md | PASS |
| 2 partially-open stays | section with any [ ] item stays; section with no checkboxes stays; neither leaks into completed file | PASS |
| 3 chunking math | DONE pre-filled 251 lines + prune of 2-item section -> exactly one `todo_done_parts/TODO_done_part_001.md` with 200 content lines (oldest first), DONE file back to 57 (<240), order preserved (old lines before new section) | PASS |
| 4 idempotent double-run | second run: moved_sections=0, moved_items=0, no new part files | PASS |

Constants under test (agent_portal.py): DONE_MAX_LINES=240, DONE_PART_SIZE=200. Live end-to-end confirmation via POST /api/todo/prune logged same round (Mechanic goal) - see TODO.md OPS CHECK 2026-11-15.
