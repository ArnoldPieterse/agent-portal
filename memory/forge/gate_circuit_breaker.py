#!/usr/bin/env python3
"""
Gate Circuit Breaker - prevents cascading failures when the gate pipeline itself is degraded.

If smoke tests or deploys are failing at a sustained high rate (e.g. systemic network issue,
sandbox permission error, port conflict), the circuit breaker PAUSES auto-promotion and
flags the pipeline for diagnosis instead of continuing to trigger rollbacks on false signals.

Exit codes:
  0 = NORMAL (gates active, safe to deploy)
  1 = CIRCUIT_BREAKER (gates paused, do NOT auto-promote)
  2 = RECOVERING (breaker was open, now resetting after consecutive greens)

Usage: python memory/forge/gate_circuit_breaker.py [--window N] [--threshold F]
"""
import json, sys, pathlib, time
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent  # project root
SMOKE_LOG = ROOT / "memory/forge/smoke-results.jsonl"
DEPLOY_LOG = ROOT / "memory/forge/deploy-log.jsonl"
STATE_FILE = ROOT / "memory/forge/gate-breaker-state.json"
INCIDENTS = ROOT / "memory/ops/incidents.jsonl"

# Config (overridable via env or args)
WINDOW = 5          # how many recent runs to consider
THRESHOLD = 0.8     # failure rate that trips the breaker
RECOVERY_GREENS = 3 # consecutive green runs needed to reset


def read_jsonl(path):
    """Read a JSONL file, return list of parsed objects (skip malformed)."""
    if not path.exists():
        return []
    items = []
    for line in path.read_text(encoding="utf-8", errors="replace").strip().split("\n"):
        if not line.strip():
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return items


def smoke_failure_rate(entries, window):
    """Compute failure rate over last `window` smoke runs.
    A run is 'failed' if ALL hosts are CRIT/error or if status=probe_failed."""
    recent = entries[-window:]
    if not recent:
        return None, 0
    failures = 0
    for e in recent:
        # probe_failed = total failure
        if e.get("status") == "probe_failed":
            failures += 1
            continue
        results = e.get("results", [])
        if not results:
            failures += 1
            continue
        # All hosts failed?
        all_bad = all(
            r.get("error") or r.get("status") in ("CRIT", "FAIL", "tcp-fail")
            for r in results
        )
        if all_bad:
            failures += 1
    rate = failures / len(recent)
    return rate, len(recent)


def deploy_rollback_rate(entries, window):
    """Compute rollback rate over last `window` deploys."""
    recent = entries[-window:]
    if not recent:
        return None, 0
    rollbacks = sum(1 for e in recent if "rollback" in str(e.get("status", "")).lower())
    rate = rollbacks / len(recent)
    return rate, len(recent)


def classify(smoke_rate, deploy_rate):
    """Classify pipeline state based on failure rates."""
    # If we have no data, assume normal (can't trip without evidence)
    if smoke_rate is None and deploy_rate is None:
        return "NORMAL", "no recent data"

    reasons = []
    if smoke_rate is not None and smoke_rate >= THRESHOLD:
        reasons.append(f"smoke failure rate {smoke_rate:.0%} >= {THRESHOLD:.0%}")
    if deploy_rate is not None and deploy_rate >= 0.5:
        reasons.append(f"deploy rollback rate {deploy_rate:.0%} >= 50%")

    if reasons:
        return "TRIPPED", "; ".join(reasons)
    return "NORMAL", "all rates within threshold"


def main():
    global WINDOW, THRESHOLD
    import argparse
    ap = argparse.ArgumentParser(description="Gate pipeline circuit breaker")
    ap.add_argument("--window", type=int, default=WINDOW, help="Sliding window size")
    ap.add_argument("--threshold", type=float, default=THRESHOLD, help="Failure rate threshold")
    args = ap.parse_args()

    WINDOW, THRESHOLD = args.window, args.threshold

    smoke_entries = read_jsonl(SMOKE_LOG)
    deploy_entries = read_jsonl(DEPLOY_LOG)

    smoke_rate, smoke_n = smoke_failure_rate(smoke_entries, WINDOW)
    deploy_rate, deploy_n = deploy_rollback_rate(deploy_entries, WINDOW)

    state, reason = classify(smoke_rate, deploy_rate)

    # Load previous state for recovery tracking
    prev_state = {"state": "NORMAL", "green_streak": 0}
    if STATE_FILE.exists():
        try:
            prev_state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    now_iso = datetime.now(timezone.utc).isoformat()

    # State machine
    if state == "TRIPPED":
        new_state = "CIRCUIT_BREAKER"
        prev_state["green_streak"] = 0
        incident = {
            "ts": now_iso,
            "type": "gate_circuit_breaker",
            "severity": "WARN",
            "detail": f"Gates PAUSED: {reason}",
            "smoke_rate": smoke_rate,
            "deploy_rollback_rate": deploy_rate,
            "window": WINDOW,
        }
        INCIDENTS.parent.mkdir(parents=True, exist_ok=True)
        with INCIDENTS.open("a", encoding="utf-8") as f:
            f.write(json.dumps(incident) + "\n")
    elif prev_state.get("state") == "CIRCUIT_BREAKER":
        # Was tripped, now checking for recovery
        if state == "NORMAL":
            streak = prev_state.get("green_streak", 0) + 1
            if streak >= RECOVERY_GREENS:
                new_state = "RECOVERING"
                msg = f"Circuit breaker reset after {streak} consecutive green runs"
            else:
                new_state = "CIRCUIT_BREAKER"
                msg = f"Still in breaker ({streak}/{RECOVERY_GREENS} greens needed)"
        else:
            new_state = "CIRCUIT_BREAKER"
            streak = 0
            msg = f"Re-interrupted: {reason}"
        prev_state["green_streak"] = streak
    else:
        new_state = "NORMAL"
        prev_state["green_streak"] = 0
        msg = "Pipeline healthy"

    # Write state
    out = {
        "state": new_state,
        "reason": reason,
        "smoke_rate": smoke_rate,
        "deploy_rollback_rate": deploy_rate,
        "window": WINDOW,
        "threshold": THRESHOLD,
        "green_streak": prev_state.get("green_streak", 0),
        "recovery_greens_needed": RECOVERY_GREENS,
        "updated_at": now_iso,
    }
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(out, indent=2), encoding="utf-8")

    # Output
    print(f"[gate-breaker] state={new_state}")
    print(f"  smoke_rate={smoke_rate if smoke_rate is not None else 'N/A'} (n={smoke_n})")
    print(f"  deploy_rollback_rate={deploy_rate if deploy_rate is not None else 'N/A'} (n={deploy_n})")
    print(f"  reason: {reason}")
    if new_state == "CIRCUIT_BREAKER":
        print(f"  ACTION: Do NOT auto-promote. Run diagnosis: python memory/forge/smoke_suite.py --diagnose")

    # Exit code
    if new_state == "NORMAL":
        sys.exit(0)
    elif new_state == "CIRCUIT_BREAKER":
        sys.exit(1)
    else:  # RECOVERING
        sys.exit(2)


if __name__ == "__main__":
    main()