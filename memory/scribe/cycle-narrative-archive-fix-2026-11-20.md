# cycle_narrative.py - archive-mode fix (2026-11-20)

**Problem:** `generate_narrative()` called `get_goal_completion(cycle_num)` without forwarding `goals_dir`/`since`/`until`, so goal counts always read live files (`memory/goals/<agent>.md`) rather than the archive for the target cycle window.

**Fix applied to `memory/scribe/cycle_narrative.py`:**
1. `get_goal_completion()` now accepts `goals_dir=None, since=None, until=None`.
   - When `goals_dir` is set, it globs `memory/goals/archive/<agent>-YYYY-MM-DD.md` files within `[since, until]` and concatenates them.
   - Falls back to live files when no window is given.
2. `generate_narrative()` now passes `goals_dir="memory/goals/archive"` whenever `since` or `until` is provided.

**Verification:**
- `python memory/scribe/cycle_narrative.py --cycle 2 --since 2026-11-13 --until 2026-11-19 --dry-run` → ACCEPTANCE PASS (uses archive)
- `python memory/scribe/cycle_narrative.py --cycle 3 --dry-run` → ACCEPTANCE PASS (live-file fallback intact)

**File changed:** `memory/scribe/cycle_narrative.py`
