"""One-shot deploy: close Mechanic goals #1 + #7 from a non-sandbox White seat.
Run: python memory/mechanic/deploy_remaining.py
Requires: LAN egress to :8099, WinRM access to PALE/BLACK/RED, elev.py present."""

import subprocess, sys, json, datetime, pathlib

def run(cmd, timeout=3700):
    print(f"\n{'='*60}\n$ {cmd}\n{'='*60}")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    print(r.stdout[-2000:] if len(r.stdout) > 2000 else r.stdout)
    if r.stderr:
        print("STDERR:", r.stderr[-1000:])
    return r.returncode == 0

def main():
    results = {}
    
    # Goal 7: Performance Profiling (1-hour live run)
    print("[Goal 7] Running perf_profile.py for 3600s...")
    ok7 = run("python memory/mechanic/perf_profile.py --duration 3600", timeout=3700)
    results["goal7_perf_profile"] = "PASS" if ok7 else "FAIL"
    
    # Goal 7 verify on live data
    ok7v = run("python memory/mechanic/perf_profile.py --verify")
    results["goal7_verify"] = "PASS" if ok7v else "FAIL"
    
    # Goal 1: WinRM remote exec on PALE/BLACK/RED
    print("[Goal 1] Running winrm_verify_legs.py...")
    ok1 = run("python memory/mechanic/winrm_verify_legs.py", timeout=120)
    results["goal1_remote_exec"] = "PASS" if ok1 else "FAIL"
    
    # Goal 1: Register rotation schtask (needs elev.py)
    print("[Goal 1] Registering WinRM rotation schtask via elev.py...")
    ok1s = run('python elev.py --shell "schtasks /create /tn WinRMRotation /tr \\"python Z:\\memory\\mechanic\\winrm_rotate.py\\"" /sc daily /st 03:00 /ru SYSTEM /rl HIGHEST /f"')
    results["goal1_rotation_schtask"] = "PASS" if ok1s else "FAIL"
    
    # Record evidence
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    all_pass = all(v == "PASS" for v in results.values())
    record = {
        "ts": ts,
        "deploy_remaining": results,
        "all_pass": all_pass,
        "ledger_commands": [
            "python memory/researcher/goal_ledger.py --record mechanic 7 --note 'live perf profile 3600s + verify PASS'",
            "python memory/researcher/goal_ledger.py --record mechanic 1 --note 'remote exec PALE/BLACK/RED + rotation schtask registered'"
        ] if all_pass else []
    }
    
    ev_path = pathlib.Path("memory/mechanic/deploy-remaining-evidence.jsonl")
    with open(ev_path, "a") as f:
        f.write(json.dumps(record) + "\n")
    
    print(f"\n{'='*60}")
    print(f"RESULT: {'ALL PASS - run ledger commands above' if all_pass else 'SOME FAILED - see details'}")
    print(f"Evidence: {ev_path}")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
