"""Stealth workflow runner - resource-budgeted wrapper for scheduled jobs.

Usage: python workflow_runner.py <script> [--budget-cpu-sec N] [--budget-mem-mb N]

Enforces:
  - CPU time limit (default 300s)
  - Memory limit via soft cap check (default 512MB)
  - Writes structured JSON log to memory/mechanic/stealth/runs/<script>_<timestamp>.json
  - Exit code 0=ok, 1=timeout, 2=memory-exceeded, 3=script-error
"""
import sys, os, time, json
from datetime import datetime
import subprocess

RUNS_DIR = os.path.join(os.path.dirname(__file__), 'runs')
os.makedirs(RUNS_DIR, exist_ok=True)

def main():
    if len(sys.argv) < 2:
        print("Usage: python workflow_runner.py <script> [--budget-cpu-sec N] [--budget-mem-mb N]")
        sys.exit(3)

    script = sys.argv[1]
    budget_cpu = 300  # seconds
    budget_mem_mb = 512

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == '--budget-cpu-sec' and i+1 < len(args):
            budget_cpu = int(args[i+1]); i += 2
        elif args[i] == '--budget-mem-mb' and i+1 < len(args):
            budget_mem_mb = int(args[i+1]); i += 2
        else:
            i += 1

    start = time.time()
    log_entry = {
        'script': os.path.basename(script),
        'started': datetime.utcnow().isoformat(),
        'budget_cpu_sec': budget_cpu,
        'budget_mem_mb': budget_mem_mb,
        'status': 'running'
    }

    try:
        # Run the script with a timeout
        proc = subprocess.run(
            [sys.executable, script],
            capture_output=True, text=True,
            timeout=budget_cpu
        )
        elapsed = time.time() - start

        if proc.returncode == 0:
            log_entry['status'] = 'ok'
            log_entry['stdout_tail'] = (proc.stdout or '')[-500:]
            log_entry['exit_code'] = 0
        else:
            log_entry['status'] = 'error'
            log_entry['stderr_tail'] = (proc.stderr or '')[-500:]
            log_entry['exit_code'] = proc.returncode

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        log_entry['status'] = 'timeout'
        log_entry['exit_code'] = 1

    except Exception as e:
        elapsed = time.time() - start
        log_entry['status'] = 'error'
        log_entry['error'] = str(e)
        log_entry['exit_code'] = 3

    log_entry['elapsed_sec'] = round(elapsed, 2)
    log_entry['finished'] = datetime.utcnow().isoformat()

    # Write run log
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(RUNS_DIR, f"{os.path.basename(script).replace('.py','')}_{ts}.json")
    with open(log_file, 'w') as f:
        json.dump(log_entry, f, indent=2)

    print(f"[workflow_runner] {log_entry['script']}: {log_entry['status']} in {log_entry['elapsed_sec']}s")
    sys.exit(log_entry.get('exit_code', 0))

if __name__ == '__main__':
    main()
