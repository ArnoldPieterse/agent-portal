#!/usr/bin/env python3
"""
run_all.py - One-shot baseline capture + manifest + verification.

When a browser (Edge/Chrome) is available, this single command does everything:
  1. Captures all panels at all resolutions
  2. Generates SHA256 manifest
  3. Verifies manifest integrity
  4. Prints summary report

Usage:
  python memory/designer/baseline/run_all.py [--url http://localhost:8099]

Requirements: msedge or chrome on PATH, Pillow (pip install pillow)
"""
import subprocess, sys, os, time, json
from pathlib import Path

HERE = Path(__file__).parent
PARENT = HERE.parent  # memory/designer/

def find_browser():
    """Find an available headless browser."""
    candidates = [
        "msedge", "chrome", "google-chrome",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    ]
    for c in candidates:
        try:
            subprocess.run([c, "--version"], capture_output=True, timeout=5)
            print(f"[OK] Browser found: {c}")
            return c
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    print("[FAIL] No browser found. Install Edge or Chrome.")
    sys.exit(1)

def step_capture(browser, url):
    """Step 1: Capture all panel screenshots."""
    print(f"\n{'='*60}")
    print("STEP 1/3: Capturing baseline screenshots")
    print(f"{'='*60}")
    r = subprocess.run(
        [sys.executable, str(HERE / "capture_baseline.py"), "--url", url],
        capture_output=True, text=True
    )
    print(r.stdout)
    if r.returncode != 0:
        print(f"[WARN] capture exit={r.returncode}: {r.stderr[:200]}")
    return r.returncode == 0

def step_manifest():
    """Step 2: Generate SHA256 manifest."""
    print(f"\n{'='*60}")
    print("STEP 2/3: Generating SHA256 manifest")
    print(f"{'='*60}")
    r = subprocess.run(
        [sys.executable, str(HERE / "manifest.py")],
        capture_output=True, text=True
    )
    print(r.stdout)
    if r.returncode != 0:
        print(f"[FAIL] manifest exit={r.returncode}: {r.stderr[:200]}")
        return False
    return True

def step_verify():
    """Step 3: Verify manifest matches PNGs."""
    print(f"\n{'='*60}")
    print("STEP 3/3: Verifying manifest integrity")
    print(f"{'='*60}")
    r = subprocess.run(
        [sys.executable, str(HERE / "manifest.py"), "--verify"],
        capture_output=True, text=True
    )
    print(r.stdout)
    return r.returncode == 0

def summary():
    """Print final summary."""
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    pngs = sorted(HERE.glob("*.png"))
    manifest_path = HERE / "manifest.json"
    
    total_size = sum(p.stat().st_size for p in pngs)
    print(f"  Screenshots: {len(pngs)} PNGs ({total_size:,} bytes total)")
    if manifest_path.exists():
        with open(manifest_path) as f:
            m = json.load(f)
        entries = m.get("entries", m) if isinstance(m, dict) else m
        print(f"  Manifest:    {len(entries)} entries (generated {m.get('generated','?') if isinstance(m,dict) else '?'})")
    else:
        print(f"  Manifest:    NOT FOUND")
    
    # Check acceptance criteria: >=8 panel screenshots
    ok = len(pngs) >= 8
    print(f"\n  Acceptance (>=8 screenshots): {'PASS' if ok else 'FAIL'} ({len(pngs)}/8)")
    return ok

def main():
    url = "http://localhost:8099"
    # Parse --url arg
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--url" and i + 1 < len(args):
            url = args[i + 1]
    
    print("Goal #10: UI Regression Screenshot Baseline - One-Shot Run")
    print(f"URL: {url}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    browser = find_browser()
    cap_ok = step_capture(browser, url)
    man_ok = step_manifest() if cap_ok else False
    ver_ok = step_verify() if man_ok else False
    acc_ok = summary()
    
    all_ok = cap_ok and man_ok and ver_ok and acc_ok
    print(f"\n  RESULT: {'ALL PASS' if all_ok else 'INCOMPLETE'}")
    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()