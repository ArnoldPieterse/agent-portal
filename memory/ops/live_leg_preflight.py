#!/usr/bin/env python3
"""Pre-flight check for the non-sandbox live-leg runbook.
Usage: python memory/ops/live_leg_preflight.py
Exit 0 = all items GO; exit 1 = at least one BLOCKED.
Run from a NON-SANDBOX White seat (the one with :8888/:8099 egress + COM).
"""
import socket, subprocess, sys, os, time

def check_port(host, port, timeout=3):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        r = s.connect_ex((host, port))
        return r == 0
    finally:
        s.close()

def check_elev():
    """Returns (ok: bool, detail: str)"""
    if not os.path.exists('elev.py'):
        return False, "elev.py not found in cwd"
    try:
        r = subprocess.run([sys.executable, 'elev.py', 'whoami'],
                           capture_output=True, text=True, timeout=15)
        if r.returncode == 0:
            return True, f"exit 0: {r.stdout.strip()[:40]}"
        elif r.returncode == 5:
            return False, "exit 5 (helper down)"
        else:
            return False, f"exit {r.returncode}: {r.stderr.strip()[:60]}"
    except FileNotFoundError:
        return False, "python not found"
    except subprocess.TimeoutExpired:
        return False, "timeout (15s)"

def check_schtasks():
    """Returns (ok: bool, detail: str)"""
    try:
        r = subprocess.run(['schtasks', '/query', '/tn', 'PortalFleetProbe'],
                           capture_output=True, text=True, timeout=10)
        if 'not found' in r.stderr.lower() or 'ERROR' in r.stdout.upper():
            return False, f"COM/schtasks broken: {r.stderr.strip()[:60]}"
        return True, "schtasks /query OK (PortalFleetProbe exists)"
    except FileNotFoundError:
        return False, "schtasks not found"
    except subprocess.TimeoutExpired:
        return False, "timeout"

def check_script(path):
    if os.path.exists(path):
        try:
            r = subprocess.run([sys.executable, '-m', 'py_compile', path],
                               capture_output=True, text=True, timeout=10)
            return r.returncode == 0
        except Exception:
            return False
    return False

def main():
    print(f"=== Live-Leg Pre-Flight ({time.strftime('%Y-%m-%d %H:%M')}) ===\n")
    
    # Check ports
    p8888 = check_port('127.0.0.1', 8888)
    p8099 = check_port('127.0.0.1', 8099)
    elev_ok, elev_detail = check_elev()
    sch_ok, sch_detail = check_schtasks()
    
    print(f"  :8888 (LM Studio): {'UP' if p8888 else 'DOWN'}")
    print(f"  :8099 (Portal):    {'UP' if p8099 else 'DOWN'}")
    print(f"  elev.py:           {'OK' if elev_ok else 'FAIL'} ({elev_detail})")
    print(f"  schtasks COM:      {'OK' if sch_ok else 'FAIL'} ({sch_detail})\n")
    
    # Per-item assessment
    items = [
        ("1", "Researcher #2 residency matrix", p8888, ":8888"),
        ("2", "Orchestrator #5 binding audit",  p8888, ":8888"),
        ("3", "Orch+Res #1/#3 hotload cycle",   elev_ok and p8888, "elev.py + :8888"),
        ("4", "Verifier #4 perf gate",          p8099, ":8099"),
        ("5", "Mechanic #4 load probe seed",    p8099, ":8099"),
        ("6", "Archivist #3 schtask register",  sch_ok, "COM/schtasks"),
    ]
    
    all_go = True
    for num, name, ok, prereq in items:
        status = "GO" if ok else "BLOCKED"
        if not ok:
            all_go = False
        print(f"  [{status:7s}] Item {num}: {name}  (needs: {prereq})")
    
    # Script existence for item 6
    targets = [
        'memory/archivist/decay_production.py',
        'memory/mechanic/deploy_all_schtasks.py',
    ]
    missing = [t for t in targets if not os.path.exists(t)]
    if missing:
        print(f"\n  WARNING: item 6 target scripts missing: {missing}")
        all_go = False
    
    print(f"\n  Summary: {'ALL GO - proceed with runbook' if all_go else f'{sum(1 for *_,ok,_ in items if not ok)} item(s) BLOCKED'}")
    sys.exit(0 if all_go else 1)

if __name__ == '__main__':
    main()