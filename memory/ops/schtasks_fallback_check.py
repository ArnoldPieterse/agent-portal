#!/usr/bin/env python3
"""schtasks_fallback_check.py — Companion for schtasks-cli-fallback-workflow-2026-11-23.md.
Verifies the schtasks CLI is accessible (primary) and logs fallback path if not.
Exit: 0=CLI works, 1=CLI unavailable (fallback needed), 2=error.
"""
import subprocess, sys, json

def main():
    try:
        r = subprocess.run(["schtasks", "/?"], capture_output=True, text=True, timeout=10)
        if r.returncode in (0, -1073741510):  # 0 or STATUS_INVALID_DWORD (help exits non-zero on some Win versions)
            print(json.dumps({"status": "OK", "method": "schtasks CLI"}))
            sys.exit(0)
        else:
            print(json.dumps({"status": "FALLBACK_NEEDED", "returncode": r.returncode,
                              "stderr": r.stderr[:200] if r.stderr else ""}))
            sys.exit(1)
    except FileNotFoundError:
        print(json.dumps({"status": "FALLBACK_NEEDED", "error": "schtasks not in PATH"}))
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(json.dumps({"status": "ERROR", "error": "timeout querying schtasks"}))
        sys.exit(2)

if __name__ == "__main__":
    main()
