#!/usr/bin/env python3
"""
batch_tier_b.py - One-shot script to execute ALL Mechanic Tier-B items from a
non-sandbox White session (ops terminal / RDP / elevated). Run ONCE.

Usage:  python batch_tier_b.py [--dry-run]
Requires: White host, admin/elevated, portal running on :8099
"""
import subprocess, json, os, sys, time, datetime

DRY = "--dry-run" in sys.argv
BASE = os.path.dirname(os.path.abspath(__file__))  # memory/ops/
ROOT = os.path.dirname(BASE)                       # memory/
EVIDENCE = os.path.join(os.path.dirname(ROOT), "memory", "mechanic")

def run(cmd, desc=""):
    print(f"\n{'='*60}")
    print(f"[{desc}] {cmd}")
    if DRY:
        print("  (dry-run: not executing)")
        return None
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"  exit={r.returncode}")
    if r.stdout: print(f"  stdout: {r.stdout[:500]}")
    if r.stderr: print(f"  stderr: {r.stderr[:500]}")
    return r

def step1_mirror_heal():
    """Goal #2: Register MirrorHeal schtask (every 15 min)."""
    desc = "Goal #2: MirrorHeal schtask"
    cmd = ('schtasks /create /tn MirrorHeal '
           '/tr "python Z:\\memory\\ops\\mirror_heal.py" '
           '/sc minute /mo 15 /ru SYSTEM /f')
    r = run(cmd, desc)
    if not DRY and r and r.returncode == 0:
        # Fire once to seed evidence
        run("python Z:\\memory\\ops\\mirror_heal.py", "Goal #2: initial fire")

def step2_schtask_dep_gen():
    """Goal #6: Register SchTaskDepGen weekly task + run first snapshot."""
    desc = "Goal #6: SchTaskDepGen schtask"
    cmd = ('schtasks /create /tn SchTaskDepGen '
           '/tr "python Z:\\memory\\ops\\schtask_dep_gen.py --snapshot" '
           '/sc weekly /d MON /st 06:15 /ru SYSTEM /f')
    r = run(cmd, desc)
    if not DRY and r and r.returncode == 0:
        # Run first snapshot now
        run("python Z:\\memory\\ops\\schtask_dep_gen.py --snapshot", "Goal #6: first snapshot")

def step3_load_probe():
    """Goal #1: Ensure PortalLoadProbe schtask exists + run today's probe."""
    desc = "Goal #1: PortalLoadProbe schtask"
    cmd = ('schtasks /create /tn PortalLoadProbe '
           '/tr "python Z:\\memory\\ops\\load_probe.py" '
           '/sc daily /st 06:00 /ru SYSTEM /f')
    r = run(cmd, desc)
    if not DRY and r and r.returncode == 0:
        # Run today's probe immediately
        run("python Z:\\memory\\ops\\load_probe.py", "Goal #1: today's probe")

def step4_reboot_dryrun():
    """Goal #4: Reboot-recovery dry-run on all reachable hosts."""
    desc = "Goal #4: Reboot recovery dry-run"
    run("python Z:\\memory\\mechanic\\reboot_recovery_test.py --dry-run", desc)

def step5_chaos_drill_prep():
    """Goal #8: Verify portal is running (precondition for chaos drill)."""
    desc = "Goal #8: Chaos drill precondition check"
    if DRY:
        print(f"\n{'='*60}\n[Goal #8] Would verify portal :8099 is up")
        return
    import socket
    s = socket.socket()
    s.settimeout(3)
    try:
        r = s.connect_ex(("127.0.0.1", 8099))
        print(f"\n{'='*60}\n[Goal #8] Portal :8099 -> {'OK' if r==0 else f'FAIL {r}'}")
    finally:
        s.close()

def main():
    ts = datetime.datetime.now().isoformat()
    print(f"batch_tier_b.py started at {ts} (dry_run={DRY})")
    
    steps = [step1_mirror_heal, step2_schtask_dep_gen, step3_load_probe,
             step4_reboot_dryrun, step5_chaos_drill_prep]
    
    results = {}
    for fn in steps:
        try:
            fn()
            results[fn.__name__] = "done"
        except Exception as e:
            results[fn.__name__] = f"error: {e}"
    
    # Write summary
    summary = {"ts": ts, "dry_run": DRY, "results": results}
    out_path = os.path.join(EVIDENCE, "batch-tier-b-run.json")
    if not DRY:
        os.makedirs(EVIDENCE, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"\nSummary written to {out_path}")
    
    print("\nDONE.")

if __name__ == "__main__":
    main()
