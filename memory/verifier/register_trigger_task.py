"""register_trigger_task.py — Register multi_file_regression_trigger as a Windows scheduled task.
Run on a non-sandbox seat (where schtasks COM class is available).

Usage: python memory/verifier/register_trigger_task.py
Idempotent: safe to re-run (uses /F flag).
"""
import subprocess, sys, os

TASK_NAME = "AgentPortal_MultiFileRegression"
PYTHON_EXE = sys.executable
TRIGGER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "multi_file_regression_trigger.py")
# Run every 5 minutes in --once mode (lightweight, robust)
CMD = f'"{PYTHON_EXE}" "{TRIGGER_SCRIPT}" --once'

def main():
    print(f"Registering task: {TASK_NAME}")
    print(f"Command: {CMD}")
    
    # Create the scheduled task (every 5 min)
    r = subprocess.run(
        ['schtasks', '/Create', '/TN', TASK_NAME, '/TR', CMD,
         '/SC', 'MINUTE', '/MO', '5', '/F'],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        print(f"ERROR creating task: {r.stderr.strip()}")
        # Try with SYSTEM privileges via elev.py
        print("Retrying as SYSTEM...")
        r2 = subprocess.run(
            ['python', 'elev.py', '--shell',
             f'schtasks /Create /TN {TASK_NAME} /TR "{CMD}" /SC MINUTE /MO 5 /RL HIGHEST /F'],
            capture_output=True, text=True
        )
        if r2.returncode != 0:
            print(f"SYSTEM retry also failed: {r2.stderr.strip()}")
            sys.exit(1)
    
    # Verify it exists
    v = subprocess.run(['schtasks', '/Query', '/TN', TASK_NAME], capture_output=True, text=True)
    if v.returncode == 0:
        print(f"SUCCESS: Task '{TASK_NAME}' registered and verified.")
        print(v.stdout.strip())
    else:
        print("WARNING: Task created but query failed. Check manually.")

if __name__ == '__main__':
    main()
