#!/usr/bin/env python3
"""Remote verification runner - executes CDP/perf tasks on PALE via WinRM.
Unblocks Designer G6 (CDP screenshots) + Mechanic G7 (live perf run).
Usage: python memory/ops/run_remote_verify.py [cdp|perf]
"""
import sys, os, json, base64, time

try:
    import winrm
except ImportError:
    print("FATAL: pip install pywinrm")
    sys.exit(1)

HOST = "IP_PALE"  # PALE (has portal + Edge)
USER = "pale"
PWD = ""
WSMAN = {"transport": "ntlm", "username": USER, "password": PWD}

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "cdp"
    s = winrm.Session("http://" + HOST + ":5985/wsman", auth=(USER, PWD), transport="ntlm")
    print("Connected to PALE via WinRM")

    # Step 1: copy the CDP script to remote
    local_script = "memory/designer/bp_capture_goal6.py"
    with open(local_script) as f:
        code = f.read()
    b64 = base64.b64encode(code.encode()).decode()

    # Use PowerShell to write file (avoids f-string backslash issues)
    ps_write = "[IO.File]::WriteAllBytes('C:\\FleetOps\\bp_capture_goal6.py', [Convert]::FromBase64String('" + b64 + "'))"
    r = s.run_ps(ps_write)
    if r.status_code != 0:
        print("FAIL writing remote script:", r.std_err.decode())
        sys.exit(1)
    print("Remote script deployed to C:\\FleetOps\\bp_capture_goal6.py")

    # Step 2: run it with the correct Edge path for PALE
    ps_run = "cd C:\\FleetOps; python bp_capture_goal6.py 2>&1"
    r = s.run_ps(ps_run)
    out = r.std_out.decode(errors="replace")
    err = r.std_err.decode(errors="replace")
    print("=== STDOUT ===")
    print(out[:3000])
    if err:
        print("=== STDERR ===")
        print(err[:1000])

    # Step 3: retrieve results JSON
    ps_read = "Get-Content 'C:\\FleetOps\\breakpoint-results-*.json' -ErrorAction SilentlyContinue | Select-Object -Last 1"
    r2 = s.run_ps(ps_read)
    result_text = r2.std_out.decode(errors="replace").strip()
    if result_text:
        print("\n=== RESULTS ===")
        print(result_text)
        # Save locally
        os.makedirs("memory/designer/breakpoint-evidence", exist_ok=True)
        with open("memory/designer/breakpoint-evidence/remote-cdp-results.json", "w") as f:
            f.write(result_text)
        print("Saved to memory/designer/breakpoint-evidence/remote-cdp-results.json")
    else:
        print("No results JSON found on remote (script may still be running or failed)")

if __name__ == "__main__":
    main()
