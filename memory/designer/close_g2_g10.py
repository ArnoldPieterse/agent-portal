#!/usr/bin/env python3
"""Designer goal #2 + #10 closure runner.
Run from a NON-SANDBOX seat (White ops terminal, RDP, or any host with LAN egress to 127.0.0.1:8099).
Prerequisites: portal running on :8099, Edge or Chrome installed.

Usage: python memory/designer/close_g2_g10.py [--url http://localhost:8099]
"""
import subprocess, hashlib, json, os, sys, argparse, time, re

BASE = os.path.join(os.path.dirname(__file__), "baseline")
os.makedirs(BASE, exist_ok=True)

PANELS = [
    ("chat",       None),
    ("fleet",      "document.getElementById('fleetBtn')&&document.getElementById('fleetBtn').click()"),
    ("ops",        "document.getElementById('actBtn')&&document.getElementById('actBtn').click()"),
    ("files",      "document.getElementById('filesBtn')&&document.getElementById('filesBtn').click()"),
    ("goals",      "document.getElementById('goalsBtn')&&document.getElementById('goalsBtn').click()"),
    ("memory",     "document.getElementById('memBtn')&&document.getElementById('memBtn').click()"),
]

WIDTH, HEIGHT = 1920, 1080

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()[:12]

def find_browser():
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    print("ERROR: No browser found. Install Edge or Chrome, or use --browser <path>")
    sys.exit(1)

def capture_panel(browser, url, panel_id, js=None):
    out_path = os.path.join(BASE, f"baseline-{panel_id}-1920.png")
    
    if js is None:
        target_url = url + "/"
    else:
        # Use a data: URL that loads the portal and opens the panel
        wrapper = f"""<html><body style="margin:0">
<script>
fetch('{url}/').then(r=>r.text()).then(html=>{{
  document.open();document.write(html);document.close();
  setTimeout(()=>{{{js}}},500);
}});
</script></body></html>"""
        wrapper_path = os.path.join(BASE, f"_tmp_{panel_id}.html")
        with open(wrapper_path, 'w') as f:
            f.write(wrapper)
        target_url = "file:///" + wrapper_path.replace("\\", "/")
    
    cmd = [browser, "--headless=new", "--disable-gpu",
           f"--window-size={WIDTH},{HEIGHT}",
           f"--screenshot={out_path}",
           "--hide-scrollbars",
           "--virtual-time-budget=3000",
           target_url]
    
    print(f"  [{panel_id}] ", end="", flush=True)
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=30)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            size = os.path.getsize(out_path)
            h = sha256(out_path)
            print(f"OK ({size:,} B, {h})")
            return {"panel": panel_id, "file": os.path.basename(out_path), "size": size, "sha256_12": h}
        else:
            err = r.stderr[:80].decode(errors='replace') if r.stderr else "no output"
            print(f"FAIL ({err})")
            return None
    except subprocess.TimeoutExpired:
        print("TIMEOUT")
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8099")
    ap.add_argument("--browser", default=None)
    args = ap.parse_args()
    
    browser = args.browser or find_browser()
    print(f"Browser: {browser}")
    print(f"URL:     {args.url}")
    print(f"Output:  {BASE}\n")
    
    manifest = []
    for panel_id, js in PANELS:
        result = capture_panel(browser, args.url, panel_id, js)
        if result:
            manifest.append(result)
        time.sleep(1)
    
    # Write manifest
    manifest_path = os.path.join(BASE, "MANIFEST.json")
    with open(manifest_path, 'w') as f:
        json.dump({"captured_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "viewport": f"{WIDTH}x{HEIGHT}",
                   "url": args.url,
                   "screenshots": manifest}, f, indent=2)
    
    ok = len(manifest)
    total = len(PANELS)
    print(f"\nCaptured {ok}/{total} panels. Manifest: {manifest_path}")
    
    if ok >= 8:
        print("GOAL #10 ACCEPTANCE MET (>=8 screenshots)")
    elif ok >= 5:
        print(f"Partial: {ok}/{total}. Try again or check which panels failed.")
    else:
        print("FAIL: too few captures. Check portal is running and browser works.")
    
    sys.exit(0 if ok == total else 1)

if __name__ == "__main__":
    main()
