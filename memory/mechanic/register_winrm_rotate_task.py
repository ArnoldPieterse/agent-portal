#!/usr/bin/env python3
"""register_winrm_rotate_task.py - Register the daily WinRM credential rotation schtask.

Goal 1 sub-item: "rotation schtask"

Registers a Windows scheduled task (WinRM_CredRotate) that runs winrm_rotate.py
daily at 06:00 as SYSTEM. After registration, performs an immediate smoke test
run and writes JSONL evidence.

Usage:
    python memory/mechanic/register_winrm_rotate_task.py [--dry-run]

Exit codes:
    0 = success (task registered + smoke test passed)
    1 = registration failed (COM unavailable / permission denied)
    2 = smoke test failed (task registered but rotation run errored)
"""
import sys, json, subprocess, logging
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
EVIDENCE_FILE = HERE / 'goal1-winrm-evidence.jsonl'
TASK_NAME = 'WinRM_CredRotate'
SCHEDULE_TIME = '06:00'
ROTATE_SCRIPT = str(HERE / 'winrm_rotate.py')

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('register_winrm_rotate')


def write_evidence(entry: dict):
    entry['ts'] = datetime.now(timezone.utc).isoformat()
    with open(EVIDENCE_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')
    log.info(f"Evidence written to {EVIDENCE_FILE.name}")


def register_task(dry_run: bool = False) -> bool:
    """Register the daily schtask. Returns True on success."""
    # Find python executable (prefer the one running this script)
    python_exe = sys.executable
    cmd = [
        'schtasks', '/create',
        '/tn', TASK_NAME,
        '/tr', f'"{python_exe}" "{ROTATE_SCRIPT}"',
        '/sc', 'daily',
        '/st', SCHEDULE_TIME,
        '/ru', 'SYSTEM',
        '/rl', 'HIGHEST',
        '/f',  # force overwrite if exists
    ]
    log.info(f"Registering task: {' '.join(cmd)}")

    if dry_run:
        log.info("[DRY-RUN] Would register task. Skipping actual registration.")
        return True

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            log.info(f"Task {TASK_NAME} registered successfully.")
            return True
        else:
            err = result.stderr.strip() or result.stdout.strip()
            log.error(f"schtasks failed (rc={result.returncode}): {err}")
            write_evidence({
                'type': 'register_winrm_rotate',
                'status': 'FAILED',
                'error': err,
                'command': ' '.join(cmd),
            })
            return False
    except FileNotFoundError:
        log.error("schtasks not found (COM unavailable in sandbox?)")
        write_evidence({
            'type': 'register_winrm_rotate',
            'status': 'FAILED',
            'error': 'schtasks not found / COM unavailable',
        })
        return False
    except subprocess.TimeoutExpired:
        log.error("schtasks timed out after 30s")
        write_evidence({
            'type': 'register_winrm_rotate',
            'status': 'FAILED',
            'error': 'timeout',
        })
        return False


def smoke_test(dry_run: bool = False) -> bool:
    """Run winrm_rotate.py once immediately to verify it works."""
    cmd = [sys.executable, ROTATE_SCRIPT]
    log.info(f"Smoke test: {' '.join(cmd)}")

    if dry_run:
        log.info("[DRY-RUN] Skipping smoke test.")
        return True

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            log.info(f"Smoke test PASSED. Output: {result.stdout.strip()[:200]}")
            return True
        else:
            err = result.stderr.strip()
            log.warning(f"Smoke test non-zero exit (rc={result.returncode}): {err[:300]}")
            # Non-zero may be acceptable if it's just "hosts unreachable" in sandbox
            write_evidence({
                'type': 'register_winrm_rotate',
                'status': 'SMOKE_WARN',
                'exit_code': result.returncode,
                'stderr': err[:500],
                'note': 'Task registered; smoke test non-zero (expected in sandbox without LAN egress)',
            })
            return False
    except subprocess.TimeoutExpired:
        log.warning("Smoke test timed out after 60s")
        write_evidence({
            'type': 'register_winrm_rotate',
            'status': 'SMOKE_TIMEOUT',
        })
        return False


def verify_task_registered() -> bool:
    """Verify the task exists by querying schtasks."""
    cmd = ['schtasks', '/query', '/tn', TASK_NAME]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0 and TASK_NAME in result.stdout:
            log.info(f"Task {TASK_NAME} confirmed registered.")
            return True
        else:
            log.warning(f"Task not found in query: {result.stderr.strip()[:100]}")
            return False
    except Exception as e:
        log.warning(f"Could not verify task (may be sandbox COM wall): {e}")
        return False


def main():
    dry_run = '--dry-run' in sys.argv
    log.info(f"=== register_winrm_rotate_task.py {'(DRY-RUN)' if dry_run else ''} ===")

    # Step 1: Register
    reg_ok = register_task(dry_run)
    if not reg_ok:
        log.error("Registration failed. See evidence for details.")
        sys.exit(1)

    # Step 2: Verify (skip in dry-run since we didn't actually register)
    if not dry_run:
        verify_task_registered()

    # Step 3: Smoke test
    smoke_ok = smoke_test(dry_run)

    # Final evidence
    write_evidence({
        'type': 'register_winrm_rotate',
        'status': 'SUCCESS' if (reg_ok and smoke_ok) else ('REGISTERED_SMOKE_WARN' if reg_ok else 'FAILED'),
        'task_name': TASK_NAME,
        'schedule': f'daily {SCHEDULE_TIME}',
        'script': ROTATE_SCRIPT,
        'dry_run': dry_run,
    })

    if reg_ok and smoke_ok:
        log.info("DONE: Task registered + smoke test passed.")
        sys.exit(0)
    elif reg_ok:
        log.warning("DONE: Task registered; smoke test had warnings (see evidence).")
        sys.exit(2)
    else:
        log.error("FAILED: Could not register task.")
        sys.exit(1)


if __name__ == '__main__':
    main()
