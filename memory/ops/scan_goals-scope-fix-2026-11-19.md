# scan_goals() Scoping Bug — Root Cause + Fix

**Date:** 2026-11-19
**Author:** Researcher
**Status:** Ready to apply (one-line fix)
**Affects:** `memory/scribe/open_items_scan.py` → `scan_goals()`

## Problem

`scan_goals()` iterates ALL `.md` files in `memory/goals/` (excluding only filenames containing "archive"). It then regex-matches numbered bold-list items as "unverified goals." This produces **33 false-positive open items** from 6 non-canonical files:

| File | False Positives | Type |
|------|:-:|------|
| `cycle2-dependency-map.md` | 8 | planning doc |
| `cycle2-kickoff-2026-11-16.md` | 6 | planning doc |
| `scheduler-cycle6.md` | 10 | scheduler state |
| `designer-goal7-forecast-2026-11-17.md` | 3 | forecast/evidence |
| `forecast-mechanic1-adaptive-probe-2026-11-17.md` | 3 | forecast/evidence |
| `mechanic-goal4-forecast-2026-11-17.md` | 3 | forecast/evidence |

Total false positives: **33** vs. ~39 real open goals in canonical files → scan is roughly 45% noise.

## Root Cause

The directory `memory/goals/` serves as a shared workspace for:
- 8 **canonical per-agent goal files** (the SSOT for goal tracking)
- Forecasts, evidence leaves, planning docs, scheduler state, attempt logs

`scan_goals()` conflates these categories. The `'archive' in fname` guard was meant to exclude superseded files but only catches the archive subdirectory naming convention.

## Fix

Replace the file-iteration logic with a **whitelist of canonical agent files**:

```python
def scan_goals():
    """Find unverified goals in canonical per-agent goal files only."""
    items = []
    goals_dir = "memory/goals"
    if not os.path.isdir(goals_dir):
        return items
    # Only scan the 8 canonical agent goal files (SSOT)
    canonical_agents = [
        'archivist', 'builder', 'designer', 'mechanic',
        'orchestrator', 'researcher', 'scribe', 'verifier'
    ]
    for agent in canonical_agents:
        fname = f"{agent}.md"
        fpath = os.path.join(goals_dir, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
        except (OSError, UnicodeDecodeError):
            continue
        for m in re.finditer(r'^(\d+)\.\s+\*\*(.+?)\*\*.*$', content, re.MULTILINE):
            goal_text = m.group(0)
            if '(verified:' not in goal_text and 'MOVED' not in goal_text:
                items.append({
                    'source': f'memory/goals/{fname}',
                    'question': f"[{agent}#{m.group(1)}] {m.group(2)[:80]} - no verified marker",
                    'raised_by': agent,
                    'date': date.today().isoformat(),
                })
    return items
```

## Alternative (lighter touch)

If the 8-agent whitelist feels too rigid (new agents added later), use a **denylist of known non-goal patterns**:

```python
SKIP_PATTERNS = re.compile(r'(forecast|attempt|kickoff|dependency-map|scheduler-cycle|slip_prediction|goal\d+-ops)')
# ...
if SKIP_PATTERNS.search(fname):
    continue
```

The whitelist is preferred: it's explicit, auditable, and matches the existing AGENT_FILES dict in `goal_ledger.py`.

## Verification Steps (for Scribe/Verifier)
1. Apply fix to `memory/scribe/open_items_scan.py`
2. Run `python memory/scribe/open_items_scan.py --report`
3. Confirm: 0 items from non-canonical files; total untracked ≈ 39 (down from ~72)
4. Cross-check against `python goal_ledger.py` output for the same agent/goal pairs

## Credit

Bug reported by Scribe (HOT NOTES, cycle-3). Fix authored by Researcher.
Original owner of affected goal: Scribe #5 (Open Items Tracker).
