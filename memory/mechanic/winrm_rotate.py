"""WinRM credential rotation runner - Goal 1 sub-item: 90-day rotation schtask.

Runs daily via schtask. Checks all 4 hosts, rotates any EXPIRED/SOON_EXPIRING,
writes a JSONL log line. Exit 0 on success, 1 on error.
"""
import sys, json, logging
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from winrm_pool import HOSTS, check_credential_rotation, rotate_credential, STATE_FILE

LOG_FILE = Path(__file__).parent / 'winrm_rotate_log.jsonl'
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('winrm_rotate')


def run() -> int:
    results = {}
    rotated = []
    for host in HOSTS:
        status = check_credential_rotation(host)
        results[host] = status['status']
        if status['status'] in ('EXPIRED', 'SOON_EXPIRING'):
            rotate_credential(host)
            rotated.append(host)
            log.info(f"{host}: rotated ({status['status']})")
    entry = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'results': results,
        'rotated': rotated,
        'state_file': str(STATE_FILE),
    }
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')
    log.info(f"Done. Status: {results}. Rotated: {rotated}")
    return 0


if __name__ == '__main__':
    sys.exit(run())
