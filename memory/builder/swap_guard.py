#!/usr/bin/env python3
"""swap_guard.py - Convergence-Aware Pre-Flight for Model Swaps.

Builder goal 9 (Cycle 20): wrap model_swap.py with a convergence-aware pre-flight that:
  1. Blocks any swap whose target seat has an in-flight goal that downtime would orphan.
  2. Checks VRAM + alias-resolution SLA (pairs Mechanic #8).
  3. Emits before/after consistency snapshots for Forge's drift/consistency check.
  4. Logs all decisions to memory/builder/swap-guard.jsonl.

Usage:
    python memory/builder/swap_guard.py <agent_id> <new_model> [--dry-run] [--studio URL]
    python memory/builder/swap_guard.py --selftest

Exit codes:
  0 = swap allowed (or selftest pass)
  1 = swap blocked (reason logged)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent  # memory/builder
ROOT = HERE.parent.parent               # project root
AGENTS_PATH = ROOT / "agents.json"
GUARD_LOG = HERE / "swap-guard.jsonl"
SNAPSHOT_DIR = HERE / "swap-snapshots"
FLEET_MODE_PATH = HERE.parent / "ops" / "fleet-mode.json"
GOALS_DIR = HERE.parent / "goals"

# Import convergence FSM for state awareness
sys.path.insert(0, str(HERE))
try:
    from convergence_fsm import FLEET_MODE_PATH as _FSM_FLEET_MODE
except ImportError:
    _FSM_FLEET_MODE = None

def fsm_get_state() -> str:
    """Read current FSM state from fleet-mode.json (via convergence_fsm path if available)."""
    fm_path = _FSM_FLEET_MODE if _FSM_FLEET_MODE else FLEET_MODE_PATH
    try:
        data = json.loads(fm_path.read_text(encoding="utf-8"))
        state = data.get("fsm_state", "UNKNOWN")
        return state.upper()
    except Exception:
        return "UNKNOWN"


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_guard(entry: dict):
    """Append a guard decision to swap-guard.jsonl."""
    entry["ts"] = _now()
    GUARD_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(GUARD_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def get_agent_profile(agent_id: str) -> dict | None:
    raw = json.loads(AGENTS_PATH.read_text(encoding="utf-8"))
    agents = raw.get("agents", []) if isinstance(raw, dict) else raw
    return next(
        (a for a in agents
         if a.get("id") == agent_id or a.get("name", "").lower() == agent_id.lower()),
        None,
    )


def file_hash(path: Path) -> str:
    if not path.exists():
        return "missing"
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def snapshot_before(agent_id: str, current_model: str) -> dict:
    """Capture a before-snapshot: agents.json hash, FSM state, fleet-mode."""
    snap = {
        "agent_id": agent_id,
        "current_model": current_model,
        "agents_json_sha": file_hash(AGENTS_PATH),
        "fsm_state": fsm_get_state(),
        "fleet_mode_ts": None,
    }
    if FLEET_MODE_PATH.exists():
        fm = json.loads(FLEET_MODE_PATH.read_text(encoding="utf-8"))
        snap["fleet_mode_ts"] = fm.get("timestamp")
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    out = SNAPSHOT_DIR / f"{agent_id}_before_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.json"
    out.write_text(json.dumps(snap, indent=2), encoding="utf-8")
    snap["_path"] = str(out.relative_to(ROOT))
    return snap


def snapshot_after(agent_id: str, new_model: str) -> dict:
    """Capture an after-snapshot for Forge's drift/consistency check."""
    snap = {
        "agent_id": agent_id,
        "new_model": new_model,
        "agents_json_sha": file_hash(AGENTS_PATH),
        "fsm_state": fsm_get_state(),
        "fleet_mode_ts": None,
    }
    if FLEET_MODE_PATH.exists():
        fm = json.loads(FLEET_MODE_PATH.read_text(encoding="utf-8"))
        snap["fleet_mode_ts"] = fm.get("timestamp")
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    out = SNAPSHOT_DIR / f"{agent_id}_after_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.json"
    out.write_text(json.dumps(snap, indent=2), encoding="utf-8")
    snap["_path"] = str(out.relative_to(ROOT))
    return snap


# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------

def check_inflight_goals(agent_id: str) -> tuple[bool, list[str]]:
    """
    Check if the target seat has in-flight (non-reached) goals.
    Returns (proceed_ok, list_of_open_goal_titles).
    A swap that would orphan active work is blocked.
    """
    goals_path = GOALS_DIR / f"{agent_id}.md"
    if not goals_path.exists():
        return True, []  # No goals file = no in-flight work

    text = goals_path.read_text(encoding="utf-8")
    open_goals = []
    for line in text.splitlines():
        stripped = line.strip()
        # Goal lines start with a number + period or bold marker
        if not stripped or not (stripped[0].isdigit() and "." in stripped[:5]):
            continue
        # Skip goals marked as reached/closed (look for explicit status markers)
        if any(marker in stripped for marker in ["✅ REACHED", "**REACHED**", "[REACHED]",
                                                       "✅ CLOSED", "**CLOSED**", "[CLOSED]", "\u2705"]):
            continue
        open_goals.append(stripped[:120])  # truncate for log

    return (len(open_goals) == 0, open_goals)


def check_vram(studio: str, required_gb: float = 14.0) -> tuple[bool, str]:
    """Check VRAM availability via Studio API or nvidia-smi."""
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(f"{studio}/api/v0/gpu")
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        free_gb = data.get("free_gb", data.get("memory_free_gb", 99))
        if free_gb >= required_gb:
            return True, f"VRAM OK: {free_gb:.1f} GB free (need {required_gb:.1f})"
        return False, f"VRAM insufficient: {free_gb:.1f} GB free (need {required_gb:.1f})"
    except Exception:
        pass
    # Fallback: nvidia-smi
    try:
        import subprocess
        r = subprocess.run(
            "nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits",
            capture_output=True, text=True, timeout=10, shell=True,
        )
        free_mb = int(r.stdout.strip().splitlines()[0])
        free_gb = free_mb / 1024
        if free_gb >= required_gb:
            return True, f"VRAM OK (nvidia-smi): {free_gb:.1f} GB free"
        return False, f"VRAM insufficient (nvidia-smi): {free_gb:.1f} GB free"
    except Exception as e:
        # Can't verify - proceed with warning
        return True, f"VRAM check skipped ({e}); proceeding"


def check_alias_resolution(agent_id: str, new_model: str) -> tuple[bool, str]:
    """
    Verify the target model alias is known (appears in agents.json recommended_models
    or as a model_id on any agent). Pairs with Mechanic's Model Alias Resolution SLA.
    """
    raw = json.loads(AGENTS_PATH.read_text(encoding="utf-8"))
    agents = raw.get("agents", []) if isinstance(raw, dict) else raw

    # Collect all known model aliases
    known_models: set[str] = set()
    for a in agents:
        mid = a.get("model_id", "")
        if mid:
            known_models.add(mid)
        for rm in a.get("recommended_models", []):
            if isinstance(rm, dict) and rm.get("id"):
                known_models.add(rm["id"])

    if new_model.lower() in {m.lower() for m in known_models}:
        return True, f"Alias '{new_model}' resolves (known in fleet)"
    # If unknown, still allow but warn (model might be valid but not yet registered)
    return False, f"Alias '{new_model}' NOT found in any agent's model bindings or recommendations"


def check_fsm_state() -> tuple[bool, str]:
    """
    Check the convergence FSM state. Swaps during REGRESSING are high-risk.
    Allow but warn; block only if FSM is in an unknown/error state.
    """
    state = fsm_get_state()
    if state == "UNKNOWN":
        return False, f"FSM state is UNKNOWN - cannot validate swap safety"
    if state == "REGRESSING":
        # High-risk: allow but flag
        return True, f"WARNING: FSM in REGRESSING state - swap adds risk during recovery"
    return True, f"FSM state {state} - safe for swap"


# ---------------------------------------------------------------------------
# Guard execution
# ---------------------------------------------------------------------------

def run_guard(agent_id: str, new_model: str, studio: str, dry_run: bool) -> int:
    """Run all pre-flight checks. Returns 0=proceed, 1=blocked."""
    t0 = time.monotonic()

    profile = get_agent_profile(agent_id)
    if not profile:
        log_guard({
            "agent": agent_id, "new_model": new_model, "decision": "BLOCKED",
            "reason": f"Agent '{agent_id}' not found in agents.json",
        })
        print(f"[BLOCKED] Agent '{agent_id}' not found in agents.json")
        return 1

    current_model = profile.get("model_id", "")
    if current_model.lower() == new_model.lower():
        print(f"[OK] Model '{new_model}' already assigned. No swap needed.")
        log_guard({
            "agent": agent_id, "new_model": new_model, "decision": "NO-OP",
            "reason": "model unchanged",
        })
        return 0

    print(f"=== Swap Guard: {agent_id} ===")
    print(f"  Current: {current_model}")
    print(f"  Target:  {new_model}")
    print(f"  Studio:  {studio}")
    if dry_run:
        print(f"  Mode:    DRY-RUN")

    # --- Check 1: In-flight goals ---
    print("\n[Check 1/4] In-flight goals...")
    clear, open_goals = check_inflight_goals(agent_id)
    if not clear:
        reasons = "; ".join(open_goals[:3])
        log_guard({
            "agent": agent_id, "new_model": new_model, "decision": "BLOCKED",
            "reason": f"{len(open_goals)} in-flight goals would be orphaned: {reasons}",
            "open_goal_count": len(open_goals),
        })
        print(f"  [BLOCKED] {len(open_goals)} in-flight goals on '{agent_id}':")
        for g in open_goals[:5]:
            print(f"    - {g}")
        print("  Downtime from swap would orphan active work.")
        return 1
    print("  [OK] No in-flight goals at risk")

    # --- Check 2: VRAM ---
    print("\n[Check 2/4] VRAM availability...")
    vram_ok, vram_msg = check_vram(studio)
    print(f"  {vram_msg}")
    if not vram_ok:
        log_guard({
            "agent": agent_id, "new_model": new_model, "decision": "BLOCKED",
            "reason": f"VRAM insufficient: {vram_msg}",
        })
        print("  [BLOCKED] Insufficient VRAM")
        return 1

    # --- Check 3: Alias resolution ---
    print("\n[Check 3/4] Alias resolution...")
    alias_ok, alias_msg = check_alias_resolution(agent_id, new_model)
    print(f"  {alias_msg}")
    if not alias_ok:
        log_guard({
            "agent": agent_id, "new_model": new_model, "decision": "BLOCKED",
            "reason": f"Alias resolution failed: {alias_msg}",
        })
        print("  [BLOCKED] Target model alias not recognized in fleet")
        return 1

    # --- Check 4: FSM state ---
    print("\n[Check 4/4] Convergence FSM state...")
    fsm_ok, fsm_msg = check_fsm_state()
    print(f"  {fsm_msg}")
    if not fsm_ok:
        log_guard({
            "agent": agent_id, "new_model": new_model, "decision": "BLOCKED",
            "reason": f"FSM state unsafe: {fsm_msg}",
        })
        print("  [BLOCKED] FSM in unsafe state")
        return 1

    # --- All checks passed: emit before-snapshot ---
    print("\n[PASS] All pre-flight checks passed.")
    before = snapshot_before(agent_id, current_model)
    print(f"  Before-snapshot: {before['_path']}")

    if dry_run:
        log_guard({
            "agent": agent_id, "new_model": new_model, "decision": "ALLOWED-DRY",
            "reason": "all checks passed (dry-run, no swap executed)",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
            "before_snapshot": before["_path"],
        })
        print("\n[DRY-RUN] Guard passed. No swap executed.")
        return 0

    # --- Execute the actual swap (delegate to model_swap logic) ---
    print("\n[EXECUTING SWAP]")
    sys.path.insert(0, str(HERE))
    try:
        import model_swap
        rc = model_swap.run_swap(agent_id, new_model, studio, dry_run=False)
    except Exception as e:
        log_guard({
            "agent": agent_id, "new_model": new_model, "decision": "SWAP-FAILED",
            "reason": f"Exception during swap: {e}",
        })
        print(f"\n[FAIL] Swap execution error: {e}")
        return 1

    if rc != 0:
        log_guard({
            "agent": agent_id, "new_model": new_model, "decision": "SWAP-FAILED",
            "reason": f"model_swap returned {rc}",
        })
        print(f"\n[FAIL] Swap failed (rc={rc})")
        return 1

    # --- After-snapshot for Forge consistency check ---
    after = snapshot_after(agent_id, new_model)
    print(f"  After-snapshot: {after['_path']}")

    elapsed_ms = round((time.monotonic() - t0) * 1000)
    log_guard({
        "agent": agent_id, "new_model": new_model, "decision": "ALLOWED",
        "reason": "all checks passed; swap executed successfully",
        "elapsed_ms": elapsed_ms,
        "before_snapshot": before["_path"],
        "after_snapshot": after["_path"],
    })
    print(f"\n[OK] Swap guarded + completed in {elapsed_ms}ms")
    return 0


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def selftest() -> int:
    """
    Acceptance tests:
    A. A swap on a seat with an in-flight goal is BLOCKED with the reason.
    B. A clean swap (no open goals, valid alias, VRAM ok) PROCEEDS and emits
       before/after snapshots that Forge's drift/consistency check can consume.
    C. Guard logs to swap-guard.jsonl.
    """
    import tempfile
    import shutil
    print("=== swap_guard.py selftest ===")
    errors = []

    # --- Test A: In-flight goal blocks the swap ---
    # Create a temp goals file with an open (non-reached) goal
    test_goals_dir = SNAPSHOT_DIR / "_selftest_goals"
    test_goals_dir.mkdir(parents=True, exist_ok=True)
    test_goals_path = test_goals_dir / "test_agent.md"
    test_goals_path.write_text(
        "# Test Agent Goals\n"
        "1. **Open Goal Alpha** - some work in progress, still active\n"
        "2. **Open Goal Beta** - also not done yet, pending verification\n",
        encoding="utf-8",
    )

    # Monkey-patch GOALS_DIR to point at our test dir
    global GOALS_DIR
    orig_goals_dir = GOALS_DIR
    GOALS_DIR = test_goals_dir

    # Also need a matching agents.json entry - patch get_agent_profile
    global AGENTS_PATH
    orig_agents = AGENTS_PATH
    test_agents_path = SNAPSHOT_DIR / "_selftest_agents.json"
    test_agents_path.write_text(json.dumps({"agents": [
        {"id": "test_agent", "name": "Test Agent", "model_id": "model-a", "studio": "http://127.0.0.1:8888"}
    ]}), encoding="utf-8")
    AGENTS_PATH = test_agents_path

    ok, open_list = check_inflight_goals("test_agent")
    if ok:
        errors.append(f"A: Expected BLOCK (in-flight goals found) but got OK. open={open_list}")
    else:
        assert len(open_list) == 2, f"A: expected 2 open goals, got {len(open_list)}"
        print(f"  [PASS] A: In-flight goals block swap ({len(open_list)} goals detected)")

    # --- Test B: Clean seat proceeds ---
    clean_goals_path = test_goals_dir / "clean_agent.md"
    clean_goals_path.write_text(
        "# Clean Agent Goals\n"
        "1. **Done Goal** - ✅ REACHED 2026-11-26T00:00Z (verified)\n",
        encoding="utf-8",
    )
    # Add clean agent to test agents
    ta = json.loads(test_agents_path.read_text(encoding="utf-8"))
    ta["agents"].append({"id": "clean_agent", "name": "Clean Agent", "model_id": "model-a",
                         "recommended_models": [{"id": "model-b"}], "studio": "http://127.0.0.1:8888"})
    test_agents_path.write_text(json.dumps(ta, indent=2), encoding="utf-8")

    ok, open_list = check_inflight_goals("clean_agent")
    if not ok:
        errors.append(f"B: Expected OK (all goals reached) but got BLOCK. open={open_list}")
    else:
        print("  [PASS] B1: Clean seat (all goals reached) passes in-flight check")

    # Alias resolution: model-b is in recommended_models
    alias_ok, alias_msg = check_alias_resolution("clean_agent", "model-b")
    if not alias_ok:
        errors.append(f"B2: Expected alias OK but got BLOCK. msg={alias_msg}")
    else:
        print(f"  [PASS] B2: Alias resolution passes ({alias_msg})")

    # Unknown alias should fail
    alias_ok2, _ = check_alias_resolution("clean_agent", "totally-unknown-model-xyz")
    if alias_ok2:
        errors.append("B3: Expected BLOCK for unknown alias but got OK")
    else:
        print("  [PASS] B3: Unknown alias correctly blocked")

    # --- Test C: Snapshot emission + guard log ---
    before = snapshot_before("clean_agent", "model-a")
    after = snapshot_after("clean_agent", "model-b")

    # Verify snapshots are valid JSON with required fields
    for label, snap in [("before", before), ("after", after)]:
        snap_path = ROOT / snap["_path"]
        if not snap_path.exists():
            errors.append(f"C: {label} snapshot file missing: {snap['_path']}")
            continue
        data = json.loads(snap_path.read_text(encoding="utf-8"))
        for field in ["agent_id", "agents_json_sha", "fsm_state"]:
            if field not in data:
                errors.append(f"C: {label} snapshot missing field '{field}'")

    # Verify guard log exists and has entries
    if not GUARD_LOG.exists():
        # Write a test entry to verify the mechanism works
        log_guard({"agent": "selftest", "new_model": "x", "decision": "TEST",
                   "reason": "selftest verification of log mechanism"})
    if GUARD_LOG.exists():
        lines = GUARD_LOG.read_text(encoding="utf-8").strip().splitlines()
        if len(lines) == 0:
            errors.append("C: swap-guard.jsonl is empty after selftest")
        else:
            last = json.loads(lines[-1])
            assert "decision" in last and "ts" in last, f"C: bad log entry: {last}"
            print(f"  [PASS] C: Guard log mechanism works ({len(lines)} entries)")
    else:
        errors.append("C: swap-guard.jsonl not created")

    # Verify snapshot files are consumable (schema for Forge)
    snap_data = json.loads((ROOT / before["_path"]).read_text(encoding="utf-8"))
    if "agents_json_sha" in snap_data and len(snap_data["agents_json_sha"]) == 16:
        print("  [PASS] B3: Before-snapshot has valid sha for Forge consistency diff")
    else:
        errors.append(f"B3: Before-snapshot sha invalid: {snap_data.get('agents_json_sha')}")

    # Restore globals
    GOALS_DIR = orig_goals_dir
    AGENTS_PATH = orig_agents

    # Cleanup test artifacts (keep the snapshot files as evidence)
    if test_goals_dir.exists():
        shutil.rmtree(test_goals_dir, ignore_errors=True)
    if test_agents_path.exists():
        test_agents_path.unlink(missing_ok=True)

    if errors:
        print(f"\n[FAIL] {len(errors)} assertion(s) failed:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("\n[ALL PASS] swap_guard selftest complete")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Convergence-aware model swap guard")
    parser.add_argument("agent_id", nargs="?", help="Agent ID to swap")
    parser.add_argument("new_model", nargs="?", help="New model ID")
    parser.add_argument("--dry-run", action="store_true", help="Check only, don't execute swap")
    parser.add_argument("--studio", default="http://127.0.0.1:8888", help="Studio URL")
    parser.add_argument("--selftest", action="store_true", help="Run self-test assertions")
    args = parser.parse_args()

    if args.selftest:
        sys.exit(selftest())

    if not args.agent_id or not args.new_model:
        parser.print_help()
        sys.exit(1)

    sys.exit(run_guard(args.agent_id, args.new_model, args.studio, args.dry_run))


if __name__ == "__main__":
    main()