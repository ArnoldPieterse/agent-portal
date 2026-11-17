"""WinRM verification for Pale + Black reboot-recovery legs.
Run FROM WHITE interactive session (not sandbox): python winrm_verify_legs.py
Requires: pip install pywinrm  (or use PowerShell Invoke-Command equivalent)
Verifies: HKCU Run entry + Studio :8888 model state on each remote."""
import json, time

HOSTS = {
    'PALE': {'ip': '192.168.1.39', 'user': 'pale',   'pw_env': 'PALE_PW'},
    'BLACK': {'ip': '192.168.1.99', 'user': 'black',  'pw_env': 'BLACK_PW'},
}

def verify(host, cfg):
    import winrm
    pw = os.environ.get(cfg['pw_env'], '131991Apiet')  # fallback to known password
    s = winrm.Session(f'http://{cfg["ip"]}:5985/wsman', auth=(cfg['user'], pw), transport='ntlm')
    results = {'host': host, 'ts': time.strftime('%Y-%m-%dT%H:%M:%S'), 'checks': {}}

    # 1. HKCU Run entry (Unsloth --hidden)
    r = s.run_cmd('reg', ['query', r'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run'])
    run_key = 'OK' if r.status_code == 0 and 'Unsloth' in r.std_out.decode() else 'MISSING'
    results['checks']['hkcu_run'] = run_key

    # 2. Studio :8888 reachable + model state (via local curl from remote)
    r2 = s.run_cmd('powershell', ['-NoProfile', '-Command',
        "try { $r = Invoke-RestMethod -Uri http://127.0.0.1:8888/api/health -TimeoutSec 5; "
        "$m = Invoke-RestMethod -Uri http://127.0.0.1:8888/api/inference/loaded-models -TimeoutSec 5; "
        "'health=' + $r.inference_active + ' models=' + ($m | ForEach-Object { $_.id }) -join ',' } catch { 'ERR:' + $_.Exception.Message }"])
    results['checks']['studio'] = r2.std_out.decode().strip()[:300]

    # 3. Scheduled tasks present (RecoverAll / PortalRun relevant)
    r3 = s.run_cmd('schtasks', ['/query', '/fo', 'csv', '/nh'])
    task_count = len([l for l in r3.std_out.decode().splitlines() if 'Portal' in l or 'Recover' in l])
    results['checks']['relevant_tasks'] = f'{task_count} found'

    return results

if __name__ == '__main__':
    all_results = []
    for host, cfg in HOSTS.items():
        try:
            res = verify(host, cfg)
            all_results.append(res)
            print(f"{host}: hkcu_run={res['checks']['hkcu_run']} studio={res['checks']['studio'][:80]}")
        except Exception as e:
            all_results.append({'host': host, 'error': str(e)[:200]})
            print(f"{host}: ERROR {e}")

    out = {'ts': time.strftime('%Y-%m-%dT%H:%M:%S'), 'results': all_results}
    with open('winrm_verify_result.json', 'w') as f:
        json.dump(out, f, indent=2)
    print(f"\nDone. Results -> winrm_verify_result.json")
