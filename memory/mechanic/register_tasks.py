"""register_tasks.py - Register fleet monitoring scripts as Windows scheduled tasks.
Run from an elevated shell: python memory/mechanic/register_tasks.py
Idempotent: safe to re-run (uses /f flag).
"""
import subprocess, sys, os

PYTHON = sys.executable
BASE = os.path.dirname(os.path.abspath(__file__))

TASKS = [
    # (task_name, script, schedule_type, interval)
    ("FleetDiskMonitor", "disk_monitor.py", "minute", 15),
    ("FleetNetProbe", "net_probe.py", "minute", 30),
    ("FleetLogRotate", "log_rotate.py", "daily", 1),
    ("FleetCapacityReport", "capacity_report.py", "weekly", 1),
]

def register():
    ok = 0
    for name, script_file, sched_type, interval in TASKS:
        script_path = os.path.join(BASE, script_file)
        if not os.path.exists(script_path):
            print(f"  [SKIP] {name}: {script_file} not found")
            continue
        
        # Build the command
        cmd = f'"{PYTHON}" "{script_path}" --run-once'
        
        # Build schtasks args
        args = ["schtasks", "/create", "/tn", name, "/tr", cmd, "/sc", sched_type]
        if sched_type == "minute":
            args += ["/mo", str(interval)]
        elif sched_type == "weekly":
            args += ["/d", "SUN"]
        
        result = subprocess.run(args + ["/f"], capture_output=True, text=True)
        status = "OK" if result.returncode == 0 else f"FAIL ({result.stderr.strip()})"
        print(f"  [{status}] {name} -> {script_file} every {interval} {sched_type}")
        if result.returncode == 0:
            ok += 1
    
    print(f"\nDone: {ok}/{len(TASKS)} tasks registered.")
    return ok

if __name__ == "__main__":
    print("Registering fleet monitoring scheduled tasks...")
    register()
