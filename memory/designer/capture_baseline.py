#!/usr/bin/env python3
"""capture_baseline.py - Goal #10: UI regression screenshot baseline.
Captures full-page screenshots of all portal panels at 1920x1080 (desktop) and
stores them in memory/designer/baseline/ with SHA256 hash manifest.

Requires: Edge or Chrome installed, portal running on :8099, non-sandbox seat.
Usage: python memory/designer/capture_baseline.py [--url http://localhost:8099]
"""
import subprocess, hashlib, json, os, sys, argparse, time

BASE = os.path.join(os.path.dirname(__file__), "baseline")
os.makedirs(BASE, exist_ok=True)

# Panels to capture (panel ID -> URL fragment or JS to open it)
PANELS = [
    ("chat",       None),           # default view
    ("fleet",      "document.getElementById('fleetBtn').click()"),
    ("ops",        "document.getElementById('actBtn').click()"),
    ("files",      "document.getElementById('filesBtn').click()"),
    ("goals",      "document.getElementById('goalsBtn').click()"),
]

WIDTH, HEIGHT = 1920, 1080

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()[:12]

def capture(browser, url, panel_id, js=None, out_path=None):
    """Capture a single panel screenshot using Edge/Chrome headless."""
    if out_path is None:
        out_path = os.path.join(BASE, f"baseline-{panel_id}-1920.png")
    
    # Build JS to open the panel and wait for render
    js_code = js or "void 0"
    full_js = f"({js_code}); new Promise(r=>setTimeout(r,800));"
    
    cmd = [browser, "--headless", "--disable-gpu",
           f"--window-size={WIDTH},{HEIGHT}",
           f"--screenshot={out_path}",
           "--hide-scrollbars",
           url]
    
    # For panels needing JS interaction, use --virtual-time-budget
    if js:
        cmd.insert(-1, "--virtual-time-budget=2000")
    
    print(f"  Capturing {panel_id} -> {os.path.basename(out_path)}...")
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=30)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            size = os.path.getsize(out_path)
            h = sha256(out_path)
            print(f"    OK ({size:,} B, sha256={h})")
            return out_path, size, h
        else:
            print(f"    FAIL (no output or too small): {r.stderr[:100].decode()}")
            return None
    except subprocess.TimeoutExpired:
        print(f"    TIMEOUT")
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8099")
    ap.add_argument("--browser", default=None, help="Path to Edge/Chrome binary")
    args = ap.parse_args()
    
    # Find browser
    if args.browser:
        browser = args.browser
    else:
        candidates = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        ]
        browser = next((c for c in candidates if os.path.exists(c)), None)
        if not browser:
            print("ERROR: No browser found. Use --browser <path>")
            sys.exit(1)
    
    print(f"Browser: {browser}")
    print(f"URL: {args.url}")
    print(f"Output: {BASE}\n")
    
    # For panels needing JS, we need to use CDP or a different approach.
    # Simplest: capture the default view, then use --run-all-compositor-stages-before-draw
    # for the default state. For other panels, we'll generate a wrapper HTML that
    # opens the panel on load.
    
    manifest = []
    for panel_id, js in PANELS:
        if js is None:
            result = capture(browser, args.url + "/", panel_id)
        else:
            # Create a temporary HTML that loads the portal and opens the panel
            wrapper_html = f"""<html><body style="margin:0">
<script>
fetch('{args.url}/').then(r=>r.text()).then(html=>{{
  document.open();document.write(html);document.close();
  setTimeout(()=>{{{js}}},500);
}});
</script></body></html>"""
            wrapper_path = os.path.join(BASE, f"_tmp_{panel_id}.html")
            with open(wrapper_path, 'w') as f:
                f.write(wrapper_html)
            result = capture(browser, wrapper_path.replace('\', '/'), panel_id)
    
        if result:
            path, size, h = result
            manifest.append({"panel": panel_id, "file": os.path.basename(path), "size": size, "sha256_12": h})
            time.sleep(0.5)  # let browser clean up
    
    # Write manifest
    manifest_path = os.path.join(BASE, "MANIFEST.json")
    with open(manifest_path, 'w') as f:
        json.dump({"captured_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "viewport": f"{WIDTH}x{HEIGHT}",
                   "screenshots": manifest}, f, indent=2)
    
    print(f"\nManifest written: {manifest_path}")
    print(f"Captured {len(manifest)}/{len(PANELS)} panels")
    sys.exit(0 if len(manifest) == len(PANELS) else 1)

if __name__ == "__main__":
    main()
