#!/usr/bin/env python3
"""deploy_startup_folder.py - Non-admin boot-recovery deployment via Startup folder.

ALTERNATIVE to deploy_boot_task.py when admin/COM is unavailable (e.g. sandbox).
Places a .vbs in %APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup
that runs boot_recovery.py at user logon (fires ~10-30s after system start).

Usage: python deploy_startup_folder.py [--delay 15]
Idempotent: overwrites existing .vbs if present.
No admin required. Works on any host where the user profile is writable.
"""
import os, sys, platform, argparse, datetime

STARTUP_DIR = os.path.join(os.environ.get("APPDATA", ""),
                           "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
VBS_NAME = "FleetBootRecovery.vbs"
HOSTNAME = platform.node()

def get_boot_script_path():
    """Find boot_recovery.py relative to this script's location."""
    local = os.path.join(os.path.dirname(os.path.abspath(__file__)), "boot_recovery.py")
    if os.path.exists(local):
        return local
    # Fallback: shared agent folder path (where portal serves files)
    alt = os.path.join(os.getcwd(), "memory", "ops", "boot_recovery.py")
    if os.path.exists(alt):
        return alt
    return local  # will fail at runtime with clear error

def create_vbs(delay_s=15, script_path=None):
    python_exe = sys.executable
    if not script_path:
        script_path = get_boot_script_path()
    
    vbs_content = f'''"""FleetBootRecovery - auto-deployed by deploy_startup_folder.py ({datetime.datetime.now():%Y-%m-%d %H:%M})
Runs boot_recovery.py at user logon with a {delay_s}s delay for system to settle.
Log: memory\\ops\\boot-recovery-log.jsonl"""
WScript.Sleep {delay_s} * 1000
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
' + chr(39) + f'{python_exe}' + chr(39) + ' "' + script_path.replace('\\', '\\\\') + '" >> "' + os.path.join(os.getcwd(), "memory", "ops", "boot-recovery-log.txt") + '" 2>&1'
'''
    return vbs_content

def deploy(delay_s=15):
    if not os.path.isdir(STARTUP_DIR):
        print(f"[{HOSTNAME}] ERROR: Startup dir not found: {STARTUP_DIR}")
        sys.exit(1)
    
    script_path = get_boot_script_path()
    if not os.path.exists(script_path):
        print(f"[{HOSTNAME}] ERROR: boot_recovery.py not found at {script_path}")
        print("  Copy it first or run from the shared agent folder.")
        sys.exit(1)
    
    vbs_path = os.path.join(STARTUP_DIR, VBS_NAME)
    vbs_content = create_vbs(delay_s, script_path)
    with open(vbs_path, "w", encoding="utf-8") as f:
        f.write(vbs_content)
    
    print(f"[{HOSTNAME}] Deployed: {vbs_path}")
    print(f"  Script: {script_path}")
    print(f"  Delay: {delay_s}s after logon")
    print(f"  Python: {sys.executable}")
    print(f"  Log: memory/ops/boot-recovery-log.txt")
    print(f"\n[{HOSTNAME}] Will fire on next user logon. Verify with:")
    print(f'  dir "{os.path.join(STARTUP_DIR, VBS_NAME)}"')

def verify():
    vbs_path = os.path.join(STARTUP_DIR, VBS_NAME)
    if os.path.exists(vbs_path):
        size = os.path.getsize(vbs_path)
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(vbs_path))
        print(f"[{HOSTNAME}] VERIFIED: {VBS_NAME} present ({size}B, modified {mtime:%Y-%m-%d %H:%M})")
    else:
        print(f"[{HOSTNAME}] NOT DEPLOYED: {vbs_path} missing")
        sys.exit(1)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--delay", type=int, default=15, help="Seconds to wait after logon before running recovery")
    ap.add_argument("--verify", action="store_true", help="Just check if deployed")
    args = ap.parse_args()
    
    if args.verify:
        verify()
    else:
        deploy(args.delay)
        verify()