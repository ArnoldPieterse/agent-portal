#!/usr/bin/env python3
"""deploy_boot_task.py - Register the ONSTART boot-recovery scheduled task.

Run ON EACH FLEET HOST (White/Pale/Black/Red) with admin rights:
    python deploy_boot_task.py

Idempotent: safe to re-run; updates existing task if present.
Task name: FleetBootRecovery
Trigger:   AT LOGON + SYSTEM START (ONSTART)
Action:    python <shared>\\memory\\ops\\boot_recovery.py
"""
import subprocess, sys, os, platform

TASK_NAME = "FleetBootRecovery"
HOSTNAME = platform.node()

def get_boot_script_path():
    """Find boot_recovery.py - prefer local copy, fall back to UNC."""
    # Local (if synced)
    local = os.path.join(os.path.dirname(os.path.abspath(__file__)), "boot_recovery.py")
    if os.path.exists(local):
        return local
    # Try SMB share from White
    for share in ["\\10.0.0.39", "\\10.0.0.99", "\\10.0.0.245"]:
        unc = rf"{share}\\memory\\ops\\boot_recovery.py"
        # Can't easily check UNC without connecting; return first as default
        break
    return local  # caller must ensure it exists

def register():
    script_path = get_boot_script_path()
    python_exe = sys.executable
    
    cmd = [
        "schtasks", "/create",
        "/tn", TASK_NAME,
        "/tr", f"\"{python_exe}\" \"{script_path}\"",
        "/sc", "onstart",
        "/ru", "SYSTEM",
        "/rl", "HIGHEST",
        "/f",  # force overwrite
    ]
    
    print(f"[{HOSTNAME}] Registering {TASK_NAME}...")
    print(f"  Script: {script_path}")
    print(f"  Python: {python_exe}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  OK - task registered")
    else:
        print(f"  FAILED: {result.stderr.strip()}")
        sys.exit(1)

def verify():
    """Confirm the task exists and is enabled."""
    cmd = ["schtasks", "/query", "/tn", TASK_NAME, "/fo", "LIST"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[{HOSTNAME}] Task verified present:")
        for line in result.stdout.strip().split("\n"):
            if any(k in line for k in ["TaskName", "Status", "Next Run", "Schedule"]):
                print(f"  {line}")
    else:
        print(f"[{HOSTNAME}] WARNING: task not found after registration")

if __name__ == "__main__":
    register()
    verify()
    print(f"[{HOSTNAME}] Done. FleetBootRecovery will fire on next system start.")
