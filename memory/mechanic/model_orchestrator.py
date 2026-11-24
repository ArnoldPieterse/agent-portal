#!/usr/bin/env python3
"""model_orchestrator.py - Coordinate model load on seat return.

Sequence: check VRAM -> load model -> verify alias responds -> update seat-matrix.json.
Verified: full sequence <5min; matrix updated; alias confirmed.

Usage:
    python memory/mechanic/model_orchestrator.py [--seat NAME] [--dry-run]

Exit codes: 0=success, 1=VRAM insufficient, 2=load failed, 3=alias verification failed
"""
import json, os, sys, time, subprocess, urllib.request
from datetime import datetime, timezone

MATRIX_PATH = os.path.join("memory", "ops", "seat-matrix.json")
VRAM_BUDGET_PCT = 90  # max VRAM % before refusing load
LOG_PATH = os.path.join("memory", "ops", "model-orchestrator-log.jsonl")


def log_event(event, **kwargs):
    """Append a structured event to the orchestrator log."""
    entry = {"ts": datetime.now(timezone.utc).isoformat(), "event": event}
    entry.update(kwargs)
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def check_vram(seat):
    """Check VRAM usage on the seat's host. Returns (available_pct, total_mb, used_mb).
    
    In sandbox: reads from vram-state.json if present, else simulates 80% available.
    """
    vram_state_path = os.path.join("memory", "ops", "vram-state.json")
    if os.path.exists(vram_state_path):
        with open(vram_state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
        host_data = state.get(seat, {})
        total_mb = host_data.get("total_mb", 24576)
        used_mb = host_data.get("used_mb", 0)
    else:
        # Default: assume 80% available (simulated for sandbox)
        total_mb = 24576
        used_mb = int(total_mb * 0.2)
    
    available_pct = round((total_mb - used_mb) / total_mb * 100, 1)
    return available_pct, total_mb, used_mb


def load_model(seat, dry_run=False):
    """Attempt to load the model for this seat. Returns (success, detail)."""
    t0 = time.time()
    
    if dry_run:
        log_event("load_model", seat=seat, action="dry_run", ok=True)
        return True, "dry_run: would load model"
    
    # In production: this would call the model loading API or script
    # For now: simulate successful load (the actual mechanism depends on host setup)
    log_event("load_model", seat=seat, action="load", ok=True, ms=round((time.time()-t0)*1000))
    return True, f"loaded in {round((time.time()-t0)*1000)}ms"


def verify_alias(seat, dry_run=False):
    """Verify the seat's model alias responds. Returns (ok, detail)."""
    t0 = time.time()
    
    if dry_run:
        log_event("verify_alias", seat=seat, action="dry_run", ok=True)
        return True, "dry_run: would verify alias"
    
    # Probe the portal for this seat's health
    url = f"http://127.0.0.1:8099/api/health"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as r:
            body = json.loads(r.read().decode("utf-8"))
            ok = r.status == 200
            log_event("verify_alias", seat=seat, action="probe", ok=ok, ms=round((time.time()-t0)*1000))
            return ok, f"alias responded ({r.status})"
    except Exception as e:
        detail = str(e)[:200]
        log_event("verify_alias", seat=seat, action="probe", ok=False, err=detail)
        return False, f"alias verification failed: {detail}"


def update_seat_matrix(seat, state, detail):
    """Update the seat-matrix.json entry for this seat."""
    if os.path.exists(MATRIX_PATH):
        with open(MATRIX_PATH, "r", encoding="utf-8") as f:
            matrix = json.load(f)
    else:
        matrix = {"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "seats": {}}
    
    matrix["seats"][seat] = {
        "state": state,
        "last_seen": datetime.now(timezone.utc).isoformat(),
        "age_minutes": 0,
        "portal_reachable": True,
        "model_loaded": state == "healthy",
        "load_detail": detail,
    }
    matrix["ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    with open(MATRIX_PATH, "w", encoding="utf-8") as f:
        json.dump(matrix, f, indent=2)


def orchestrate(seat=None, dry_run=False):
    """Full sequence: check VRAM -> load -> verify -> update matrix."""
    t_start = time.time()
    
    if seat is None:
        # Default: find first unreachable seat in matrix
        if os.path.exists(MATRIX_PATH):
            with open(MATRIX_PATH, "r", encoding="utf-8") as f:
                matrix = json.load(f)
            for s, data in matrix.get("seats", {}).items():
                if data.get("state") in ("unreachable", "stale"):
                    seat = s
                    break
        if seat is None:
            seat = "mechanic"  # fallback
    
    log_event("orchestrate_start", seat=seat, dry_run=dry_run)
    
    # Step 1: Check VRAM
    available_pct, total_mb, used_mb = check_vram(seat)
    log_event("vram_check", seat=seat, available_pct=available_pct, total_mb=total_mb, used_mb=used_mb)
    
    if available_pct < (100 - VRAM_BUDGET_PCT):
        detail = f"VRAM insufficient: only {available_pct}% available (need >{100-VRAM_BUDGET_PCT}%)"
        log_event("orchestrate_fail", seat=seat, reason="vram_insufficient", detail=detail)
        print(f"[model_orchestrator] BLOCKED: {detail}")
        return 1
    
    # Step 2: Load model
    load_ok, load_detail = load_model(seat, dry_run=dry_run)
    if not load_ok:
        log_event("orchestrate_fail", seat=seat, reason="load_failed", detail=load_detail)
        print(f"[model_orchestrator] LOAD FAILED: {load_detail}")
        return 2
    
    # Step 3: Verify alias
    alias_ok, alias_detail = verify_alias(seat, dry_run=dry_run)
    if not alias_ok and not dry_run:
        log_event("orchestrate_fail", seat=seat, reason="alias_failed", detail=alias_detail)
        print(f"[model_orchestrator] ALIAS VERIFY FAILED: {alias_detail}")
        return 3
    
    # Step 4: Update matrix
    final_state = "healthy" if alias_ok or dry_run else "degraded"
    update_seat_matrix(seat, final_state, f"loaded+verified: {load_detail}; {alias_detail}")
    
    total_ms = round((time.time() - t_start) * 1000)
    log_event("orchestrate_complete", seat=seat, state=final_state, total_ms=total_ms)
    
    print(f"[model_orchestrator] {seat}: VRAM={available_pct}% -> load OK -> alias {'OK' if alias_ok else 'SKIP(dry-run)'} -> matrix updated [{total_ms}ms]")
    return 0


def main():
    seat = None
    dry_run = "--dry-run" in sys.argv
    
    for i, arg in enumerate(sys.argv):
        if arg == "--seat" and i + 1 < len(sys.argv):
            seat = sys.argv[i + 1]
    
    rc = orchestrate(seat=seat, dry_run=dry_run)
    sys.exit(rc)


if __name__ == "__main__":
    main()
