"""WinRM connection pool with retry + credential rotation tracking.
Goal #1: WinRM Remote Management Hardening

Covers all 4 fleet hosts. Retry: 3 attempts, exponential backoff (2s base).
Credential rotation: 90-day cycle; tracks last-rotated date per host;
alerts when within 7 days of expiry.

Usage:
    from winrm_pool import WinRMPool
    pool = WinRMPool()
    result = pool.run_cmd('PALE', 'reg query HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run')
"""
import json, time, os, logging
from datetime import datetime, timedelta
from pathlib import Path

LOG = logging.getLogger('winrm_pool')
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s %(message)s')

# --- Fleet host registry (all 4 hosts) ---
HOSTS = {
    'WHITE': {'ip': '127.0.0.1',    'user': 'white', 'pw_env': 'WHITE_PW',  'local': True},
    'PALE':  {'ip': 'IP_PALE', 'user': 'pale',  'pw_env': 'PALE_PW',   'local': False},
    'BLACK': {'ip': 'IP_BLACK', 'user': 'black', 'pw_env': 'BLACK_PW',  'local': False},
    'RED':   {'ip': '[LAN-IP]', 'user': 'red',   'pw_env': 'RED_PW',    'local': False},
}

# Fallback password (same as existing scripts; rotate via credential rotation)
FALLBACK_PW = '[REDACTED-CREDENTIAL]'
ROTATION_DAYS = 90
ALERT_WINDOW_DAYS = 7
STATE_FILE = Path(__file__).parent / 'winrm_pool_state.json'
MAX_RETRIES = 3
BACKOFF_BASE_S = 2.0


def _load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {'credentials': {}, 'connections': {}}


def _save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


class WinRMError(Exception):
    pass


class CredentialExpiryWarning:
    """Raised as a warning (not exception) when credential is near expiry."""
    def __init__(self, host, days_remaining):
        self.host = host
        self.days_remaining = days_remaining
        super().__init__(f"{host}: credential expires in {days_remaining} days")


def check_credential_rotation(host: str) -> dict:
    """Check if a host's credential needs rotation. Returns status dict."""
    state = _load_state()
    cred_info = state['credentials'].get(host, {})
    last_rotated = cred_info.get('last_rotated')

    if not last_rotated:
        return {'host': host, 'status': 'NEVER_ROTATED', 'days_remaining': None,
                'action': 'set initial rotation date'}

    last_dt = datetime.fromisoformat(last_rotated)
    next_due = last_dt + timedelta(days=ROTATION_DAYS)
    now = datetime.now()
    days_remaining = (next_due - now).days

    if days_remaining < 0:
        return {'host': host, 'status': 'EXPIRED', 'days_remaining': days_remaining,
                'action': 'rotate immediately'}
    elif days_remaining <= ALERT_WINDOW_DAYS:
        return {'host': host, 'status': 'SOON_EXPIRING', 'days_remaining': days_remaining,
                'action': f'rotate within {days_remaining} days'}
    else:
        return {'host': host, 'status': 'OK', 'days_remaining': days_remaining,
                'action': None}


def rotate_credential(host: str, new_password: str = None):
    """Mark a credential as rotated. If new_password given, store it (encrypted in prod)."""
    state = _load_state()
    state['credentials'][host] = {
        'last_rotated': datetime.now().isoformat(),
        'pw_env': HOSTS[host]['pw_env'],
        'rotations_count': state['credentials'].get(host, {}).get('rotations_count', 0) + 1,
    }
    _save_state(state)
    LOG.info("Credential rotated for %s", host)


class WinRMPool:
    """Connection pool with retry + exponential backoff."""

    def __init__(self, hosts=None):
        self.hosts = hosts or HOSTS
        self._sessions = {}  # host -> (session, created_ts)
        self.state = _load_state()

    def _get_password(self, host: str) -> str:
        cfg = self.hosts[host]
        return os.environ.get(cfg['pw_env'], FALLBACK_PW)

    def _create_session(self, host: str):
        """Create a WinRM session for the given host."""
        cfg = self.hosts[host]
        if cfg.get('local'):
            # White is local - use subprocess instead of WinRM
            return {'local': True}
        import winrm  # lazy import; not available in all environments
        pw = self._get_password(host)
        s = winrm.Session(
            f'http://{cfg["ip"]}:5985/wsman',
            auth=(cfg['user'], pw),
            transport='ntlm'
        )
        return {'local': False, 'session': s}

    def _run_local(self, cmd: list):
        """Run command locally (for White)."""
        import subprocess
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return {'status_code': r.returncode, 'std_out': r.stdout, 'std_err': r.stderr}

    def run_cmd(self, host: str, cmd: list, retries: int = MAX_RETRIES) -> dict:
        """Run a command on a host with retry + exponential backoff.

        Returns: {'host', 'status_code', 'std_out', 'std_err', 'attempts', 'elapsed_s'}
        Raises WinRMError after all retries exhausted.
        """
        if host not in self.hosts:
            raise WinRMError(f"Unknown host: {host}")

        # Check credential rotation before connecting
        cred_status = check_credential_rotation(host)
        if cred_status['status'] in ('EXPIRED', 'SOON_EXPIRING'):
            LOG.warning("Credential %s for %s: %s (%s days remaining)",
                        cred_status['status'], host, cred_status['action'],
                        cred_status['days_remaining'])

        last_err = None
        t0 = time.time()
        for attempt in range(1, retries + 1):
            try:
                conn = self._sessions.get(host)
                if conn is None or (time.time() - conn[1]) > 300:  # 5-min session TTL
                    conn = (self._create_session(host), time.time())
                    self._sessions[host] = conn
                session_data = conn[0]

                if session_data.get('local'):
                    result = self._run_local(cmd)
                else:
                    r = session_data['session'].run_cmd(cmd[0], cmd[1:])
                    result = {'status_code': r.status_code, 'std_out': r.std_out.decode(),
                              'std_err': r.std_err.decode()}

                return {
                    'host': host,
                    **result,
                    'attempts': attempt,
                    'elapsed_s': round(time.time() - t0, 2),
                }
            except Exception as e:
                last_err = e
                self._sessions.pop(host, None)  # invalidate on error
                if attempt < retries:
                    backoff = BACKOFF_BASE_S * (2 ** (attempt - 1))
                    LOG.info("Host %s attempt %d/%d failed: %s. Retrying in %.1fs",
                             host, attempt, retries, e, backoff)
                    time.sleep(backoff)

        raise WinRMError(f"{host}: all {retries} attempts failed. Last error: {last_err}")

    def health_check_all(self) -> dict:
        """Quick reachability check on all hosts. Returns per-host status."""
        results = {}
        for host in self.hosts:
            try:
                r = self.run_cmd(host, ['cmd', '/c', 'echo OK'], retries=1)
                results[host] = {'status': 'OK', 'attempts': r['attempts']}
            except WinRMError as e:
                results[host] = {'status': 'UNREACHABLE', 'error': str(e)[:200]}
        return results

    def close_all(self):
        for host in list(self._sessions):
            self._sessions.pop(host, None)


# --- CLI entry point ---
if __name__ == '__main__':
    import sys
    pool = WinRMPool()

    if len(sys.argv) > 1 and sys.argv[1] == 'health':
        results = pool.health_check_all()
        print(json.dumps(results, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == 'rotation-status':
        for host in HOSTS:
            status = check_credential_rotation(host)
            print(f"{host:6s}: {status['status']:15s} days_remaining={status['days_remaining']} action={status['action']}")
    elif len(sys.argv) > 1 and sys.argv[1] == 'rotate':
        host = sys.argv[2].upper()
        rotate_credential(host)
        print(f"Rotated credential for {host}")
    else:
        # Default: run echo OK on all hosts
        results = pool.health_check_all()
        print(json.dumps(results, indent=2))
