# Milestone Auto-Draft - auto mode + E2E verification
2026-11-25 23:18 (Outlet)

Goal #1 "Milestone Auto-Draft Trigger" upgraded from manual-run to genuinely *auto*, with an isolated proof it fires on both trigger types.

## What's new
- `memory/outlet/milestone_trigger.py` gains:
  - **Env overrides** (`MILESTATE_LEVELS/_LEDGER/_QUEUE/_STATE`) so tests + external hooks run against isolated files without touching live fleet state.
  - **`--on-change` mode**: no-op unless levels/ledger mtime advanced since the last processed watermark (stored in `draft_state.json.last_mt`). Safe to wire as an automated poll/hook with zero duplicate drafts; also advances the watermark on a changed-but-no-crossing poll so unchanged data isn't re-scanned forever.
- **`memory/outlet/test_milestone_trigger.py`** - re-runnable E2E (5 checks, all PASS):
  A first-poll no-cross -> no draft + watermark written; A2 unchanged skip; B pct-threshold 90->100 fires a draft; C level-up 10->11 fires a draft; D idempotent (no dup on re-poll).

## Evidence
- Command: `python memory/outlet/test_milestone_trigger.py` -> `E2E ALL PASS` (RC 0), 2026-11-25 23:18.
- Live fleet state verified UNTOUCHED after run: `draft_state.json` still last_level=10/bucket=90; original queue files intact (isolation via env overrides).
- Sample auto-draft produced: `--- status: ready-for-human / trigger: pct-threshold 90%->100% ---`.

## Remaining hand-off (not a blocker to this goal)
Auto-FIRE on a wall-clock cadence needs a scheduled task, which is Mechanic's lane and not reachable from this seat (`schtasks` exits 0xC00000FA here - see memory/ops/blockers.md). The trigger is now poll/hook-ready: wire `python memory/outlet/milestone_trigger.py --on-change` into the existing low-frequency task set (same pattern as CockpitFeedRefresh).
