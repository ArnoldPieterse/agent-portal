#!/usr/bin/env python3
"""mode_reconcile.py - fleet-mode.json Drift Reconciler.

Each pass, recomputes ground-truth mode from (open-goal count via goal_ledger)
+ seat reachability, diffs against fleet-mode.json; on mismatch self-heals the
SSOT and appends a drift event to memory/ops/mode-drift.jsonl.

Ground-truth logic:
  - If any agent has open goals -> mode should be WORK
  - If all reached + <6h since activity -> MAINTENANCE
  - If all reached + >=6h since activity -> IDLE

Also reconciles convergence_state (from convergence-asymptote.json if present).

Usage:
    python memory/orchestrator/mode_reconcile.py            # reconcile + heal
    python memory/orchestrator/mode_reconcile.py --dry-run  # report only, no writes
"""
import pathlib, json, sys
from datetime import datetime, timezone

MEM = pathlib.Path("memory")
FLEET_MODE_FILE = MEM / "ops" / "fleet-mode.json"
DRIFT_LOG = MEM / "ops" / "mode-drift.jsonl"
CONVERGENCE_FILE = MEM / "orchestrator" / "convergence-asymptote.json"
ACTIVITY_FILES = [
    MEM / "ops" / "scheduler-log.jsonl",
    MEM / "ops" / "fleet-snapshots.jsonl",
    MEM / "ops" / "decision-log.jsonl",
    MEM / "ops" / "autonomous-actions.jsonl",
]

IDLE_THRESHOLD_HOURS = 6.0

# Goal files to scan for open goals
AGENT_GOAL_FILES = {
    "orchestrator": "orchestrator.md",
    "researcher":   "researcher.md",
    "builder":      "builder.md",
    "archivist":    "archivist.md",
    "scribe":       "scribe.md",
    "verifier":     "verifier.md",
    "designer":     "designer.md",
    "mechanic":     "mechanic.md",
    "outlet":       "outlet.md",
    "pixel":        "pixel.md",
    "forge":        "forge.md",
}


def compute_ground_truth_mode() -> dict:
    """Compute the correct mode from current state."""
    import re

    goals_dir = MEM / "goals"
    total_goals = 0
    reached_goals = 0

    for agent, fname in AGENT_GOAL_FILES.items():
        path = goals_dir / fname
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for line in text.split("\n"):
            m = re.match(r'^\s*(\d+)\.\s+\*\*', line)
            if not m:
                continue
            total_goals += 1
            # Check for verified/reached markers
            if ("(verified:" in line or "[x]" in line.lower() or
                    "(pointer:" in line and _pointer_exists(line)):
                reached_goals += 1

    open_count = total_goals - reached_goals
    goal_pct = (reached_goals / total_goals * 100) if total_goals > 0 else 100.0

    # Determine mode
    hours_since = None
    if open_count > 0:
        mode = "WORK"
    else:
        # All reached - check time since activity
        last_activity = _last_activity_ts()
        hours_since = (datetime.now(timezone.utc) - last_activity).total_seconds() / 3600 if last_activity else float('inf')
        if hours_since < IDLE_THRESHOLD_HOURS:
            mode = "MAINTENANCE"
        else:
            mode = "IDLE"

    return {
        "mode": mode,
        "goal_pct": round(goal_pct, 1),
        "goals_total": total_goals,
        "goals_reached": reached_goals,
        "goals_open": open_count,
        "elapsed_since_activity_h": round(hours_since, 2) if (hours_since is not None and hours_since != float('inf')) else None,
    }


def _pointer_exists(line: str) -> bool:
    """Check if a (pointer: path) reference points to an existing file."""
    import re
    m = re.search(r'\(pointer:\s*([^)]+)\)', line)
    if m:
        return (MEM / m.group(1).strip()).exists()
    return False


def _last_activity_ts():
    """Find the most recent activity timestamp from known files."""
    latest = None
    for f in ACTIVITY_FILES:
        if not f.exists():
            continue
        try:
            content = f.read_text(encoding="utf-8").strip()
            if not content:
                continue
            last_line = content.split("\n")[-1].strip()
            if last_line:
                rec = json.loads(last_line)
                ts_str = rec.get("ts") or rec.get("timestamp") or rec.get("computed_at")
                if ts_str:
                    try:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if latest is None or ts > latest:
                            latest = ts
                    except (ValueError, TypeError):
                        pass
        except (json.JSONDecodeError, OSError):
            continue
    return latest


def reconcile(dry_run: bool = False) -> dict:
    """Run reconciliation. Returns result dict."""
    # Load current fleet-mode.json
    current = {}
    if FLEET_MODE_FILE.exists():
        try:
            current = json.loads(FLEET_MODE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            current = {}

    # Compute ground truth
    truth = compute_ground_truth_mode()

    # Also check convergence_state if we have a recent computation
    convergence_state = None
    if CONVERGENCE_FILE.exists():
        try:
            conv = json.loads(CONVERGENCE_FILE.read_text(encoding="utf-8"))
            convergence_state = conv.get("convergence_state")
        except (json.JSONDecodeError, OSError):
            pass

    # Diff
    drifts = []

    # Check mode field
    if current.get("mode") != truth["mode"]:
        drifts.append({
            "field": "mode",
            "was": current.get("mode"),
            "now": truth["mode"],
            "cause": f"open_goals={truth['goals_open']}, activity_h={truth['elapsed_since_activity_h']}",
        })

    # Check goal counts
    for field in ["goal_pct", "goals_total", "goals_reached", "goals_open"]:
        if current.get(field) != truth[field]:
            drifts.append({
                "field": field,
                "was": current.get(field),
                "now": truth[field],
                "cause": "recomputed from goal files",
            })

    # Check convergence_state
    if convergence_state and current.get("convergence_state") != convergence_state:
        drifts.append({
            "field": "convergence_state",
            "was": current.get("convergence_state"),
            "now": convergence_state,
            "cause": "from convergence-asymptote.json",
        })

    # Self-heal
    healed = False
    if drifts and not dry_run:
        for d in drifts:
            current[d["field"]] = d["now"]
        current["timestamp"] = datetime.now(timezone.utc).isoformat()
        current["reconciled_at"] = datetime.now(timezone.utc).isoformat()
        FLEET_MODE_FILE.write_text(json.dumps(current, indent=2), encoding="utf-8")
        healed = True

    # Log drift events
    if drifts and not dry_run:
        DRIFT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(DRIFT_LOG, "a", encoding="utf-8") as f:
            for d in drifts:
                event = {"ts": datetime.now(timezone.utc).isoformat(), **d}
                f.write(json.dumps(event) + "\n")

    return {
        "dry_run": dry_run,
        "drift_count": len(drifts),
        "drifts": drifts,
        "healed": healed,
        "ground_truth": truth,
    }


def run_selftest() -> bool:
    """Test with synthetic stale mode."""
    import tempfile, shutil

    print("=== SELFTEST ===")
    all_pass = True

    # Test 1: Inject a stale mode, verify reconciler heals it
    test_mode_file = MEM / "ops" / "fleet-mode-test.json"
    test_drift_log = MEM / "ops" / "mode-drift-test.jsonl"

    try:
        # Set up a stale fleet-mode
        stale = {
            "mode": "IDLE",  # Wrong - should be WORK since we have open goals
            "goal_pct": 100.0,
            "goals_total": 10,
            "goals_reached": 10,
            "goals_open": 0,
        }
        test_mode_file.write_text(json.dumps(stale), encoding="utf-8")

        # Monkey-patch the module-level constants for testing
        global FLEET_MODE_FILE, DRIFT_LOG
        orig_mode_file = FLEET_MODE_FILE
        orig_drift_log = DRIFT_LOG
        FLEET_MODE_FILE = test_mode_file
        DRIFT_LOG = test_drift_log

        # Run reconcile
        result = reconcile(dry_run=False)
        print(f"  Pass 1: drifts={result['drift_count']}, healed={result['healed']}")

        if result["drift_count"] == 0:
            print("  FAIL: expected drift (stale mode not detected)")
            all_pass = False
        elif not result["healed"]:
            print("  FAIL: expected heal but got none")
            all_pass = False
        else:
            # Verify the file was healed
            healed_data = json.loads(test_mode_file.read_text(encoding="utf-8"))
            if healed_data.get("mode") != "WORK":
                print(f"  FAIL: mode not healed (got {healed_data.get('mode')})")
                all_pass = False
            else:
                print("  PASS: stale mode detected + healed to WORK")

        # Test 2: Idempotent - 2nd run should have 0 drifts
        result2 = reconcile(dry_run=False)
        print(f"  Pass 2 (idempotent): drifts={result2['drift_count']}")
        if result2["drift_count"] != 0:
            print("  FAIL: expected 0 drifts on idempotent re-run")
            all_pass = False
        else:
            print("  PASS: idempotent (2nd run 0 events)")

        # Test 3: No false positive when mode is correct
        correct_mode_file = MEM / "ops" / "fleet-mode-test2.json"
        truth = compute_ground_truth_mode()
        correct = {
            "mode": truth["mode"],
            "goal_pct": truth["goal_pct"],
            "goals_total": truth["goals_total"],
            "goals_reached": truth["goals_reached"],
            "goals_open": truth["goals_open"],
        }
        correct_mode_file.write_text(json.dumps(correct), encoding="utf-8")
        FLEET_MODE_FILE = correct_mode_file

        result3 = reconcile(dry_run=False)
        print(f"  Pass 3 (no false positive): drifts={result3['drift_count']}")
        # Note: convergence_state might still cause a drift if it differs
        real_drifts = [d for d in result3["drifts"] if d["field"] in ("mode", "goal_pct", "goals_total", "goals_reached", "goals_open")]
        if len(real_drifts) != 0:
            print(f"  FAIL: false positive on correct mode: {real_drifts}")
            all_pass = False
        else:
            print("  PASS: no false positive when mode is already correct")

    finally:
        # Restore originals + cleanup
        FLEET_MODE_FILE = orig_mode_file
        DRIFT_LOG = orig_drift_log
        for f in [test_mode_file, test_drift_log, MEM / "ops" / "fleet-mode-test2.json"]:
            if f.exists():
                f.unlink()

    print(f"\n{'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
    return all_pass


def main():
    dry_run = "--dry-run" in sys.argv
    if "--selftest" in sys.argv:
        ok = run_selftest()
        sys.exit(0 if ok else 1)

    result = reconcile(dry_run=dry_run)
    print(f"Mode reconciliation {'(DRY RUN)' if dry_run else ''}")
    print(f"  Drifts found: {result['drift_count']}")
    for d in result["drifts"]:
        print(f"    {d['field']}: {d['was']} -> {d['now']} ({d['cause']})")
    if result["healed"]:
        print("  Self-healed fleet-mode.json")
    elif result["drift_count"] == 0:
        print("  No drift - SSOT is consistent")


if __name__ == "__main__":
    main()
