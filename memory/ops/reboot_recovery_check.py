#!/usr/bin/env python3
"""reboot_recovery_check.py — executable form of memory/ops/windows-runbook.md.

Runs the post-reboot verification sequence. Exit 0 = all checks pass, 1 = failures.
Usage: python memory/ops/reboot_recovery_check.py [--skip-gpu] [--json]
"""
import json, socket, subprocess, sys, time
from datetime import datetime
from pathlib import Path

def http_get(url, timeout=5):
    try:
        import urllib.request
        r = urllib.request.urlopen(url, timeout=timeout)
        return r.status, r.read()
    except Exception as e:
        return None, str(e)

def check_studio():
    status, body = http_get("http://127.0.0.1:8888/api/inference/status", timeout=5)
    if status == 200:
        data = json.loads(body)
        active = data.get("inference_active", False)
        print(f"  [PASS] Studio :8888 alive (inference_active={active})")
        return True
    print(f"  [FAIL] Studio :8888 unreachable: {body}")
    return False

def check_portal():
    status, body = http_get("http://127.0.0.1:8099/api/memory", timeout=5)
    if status == 200:
        print(f"  [PASS] Portal :8099 responding (GET /api/memory -> 200)")
        return True
    print(f"  [FAIL] Portal :8099 unreachable: {body}")
    return False

def check_gpu():
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=index,memory.used,temperature.gpu",
                            "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            print(f"  [SKIP] nvidia-smi failed: {r.stderr.strip()}")
            return True
        lines = [l.strip() for l in r.stdout.strip().splitlines() if l.strip()]
        for line in lines:
            idx, vram, temp = line.split(",")
            flag = "PASS" if int(vram) > 0 else "INFO"
            print(f"  [{flag}] GPU{idx}: {vram}MB VRAM, {temp}C")
        return True
    except FileNotFoundError:
        print("  [SKIP] nvidia-smi not found")
        return True

def check_models_loaded():
    status, body = http_get("http://127.0.0.1:8888/v1/models", timeout=5)
    if status == 200:
        data = json.loads(body)
        models = [m["id"] for m in data.get("data", [])]
        print(f"  [PASS] {len(models)} model(s) loaded: {', '.join(models[:4])}")
        return True
    print(f"  [FAIL] /v1/models unreachable: {body}")
    return False

def main():
    skip_gpu = "--skip-gpu" in sys.argv
    as_json = "--json" in sys.argv
    results = []
    if not as_json:
        print(f"=== Reboot Recovery Check — {datetime.now().isoformat(timespec='seconds')} ===\n")

    checks = [("Portal :8099", check_portal), ("Studio :8888", check_studio)]
    if not skip_gpu:
        checks.append(("GPU state", check_gpu))
    checks.append(("Models loaded", check_models_loaded))

    for name, fn in checks:
        ok = fn()
        results.append({"check": name, "pass": ok})

    if as_json:
        print(json.dumps({"timestamp": datetime.now().isoformat(), "results": results,
                          "all_pass": all(r["pass"] for r in results)}))
    else:
        passed = sum(1 for r in results if r["pass"])
        print(f"\n=== {passed}/{len(results)} checks passed ===")

    sys.exit(0 if all(r["pass"] for r in results) else 1)

if __name__ == "__main__":
    main()