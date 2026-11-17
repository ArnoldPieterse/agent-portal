"""
Goal #10: UI Regression Screenshot Baseline
=============================================
Run this script from a NON-SANDBOX seat with Chrome + Playwright installed.
Prerequisites:
  pip install playwright
  python -m playwright install chromium

Usage:
  python memory/designer/baseline/capture_baseline.py [--url http://127.0.0.1:8099]

Output:
  memory/designer/baseline/shots/*.png   (one per panel x resolution)
  memory/designer/baseline/MANIFEST.json (SHA256 + metadata)
"""
import argparse, hashlib, json, os, sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: pip install playwright && python -m playwright install chromium")
    sys.exit(1)

PANELS = [
    ("dashboard", "?panel=dashboard"),
    ("fleet", "?panel=fleet"),
    ("goals", "?panel=goals"),
    ("ops", "?panel=ops"),
    ("memory-tree", "?panel=memory"),
    ("uploads", "?panel=uploads"),
    ("chat", "?panel=chat"),
    ("settings", "?panel=settings"),
]

RESOLUTIONS = [
    (1920, 1080, "fullhd"),
    (1366, 768, "laptop"),
    (1024, 768, "tablet-landscape"),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8099")
    ap.add_argument("--out", default=str(Path(__file__).parent))
    args = ap.parse_args()

    out_dir = Path(args.out)
    shots_dir = out_dir / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)

    manifest = {"version": 1, "url": args.url, "panels": []}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for w, h, label in RESOLUTIONS:
            ctx = browser.new_context(viewport={"width": w, "height": h})
            page = ctx.new_page()
            errors = []
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

            for panel_id, query in PANELS:
                url = f"{args.url}/{query}"
                try:
                    page.goto(url, wait_until="networkidle", timeout=15000)
                    page.wait_for_timeout(500)  # let animations settle
                    fname = f"{panel_id}_{label}.png"
                    fpath = shots_dir / fname
                    page.screenshot(path=str(fpath), full_page=True)
                    digest = sha256_file(fpath)
                    manifest["panels"].append({
                        "panel": panel_id,
                        "resolution": label,
                        "width": w,
                        "height": h,
                        "file": f"shots/{fname}",
                        "sha256": digest,
                        "size_bytes": fpath.stat().st_size,
                        "console_errors": errors[:5],  # first 5 only
                    })
                    print(f"  OK  {fname} ({digest[:8]})")
                except Exception as e:
                    manifest["panels"].append({
                        "panel": panel_id, "resolution": label,
                        "file": None, "error": str(e),
                    })
                    print(f"  ERR {panel_id}_{label}: {e}")
            ctx.close()

        browser.close()

    manifest_path = out_dir / "MANIFEST.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    ok = sum(1 for p in manifest["panels"] if p.get("sha256"))
    total = len(manifest["panels"])
    print(f"\nDone: {ok}/{total} screenshots captured.")
    print(f"Manifest: {manifest_path}")

    if ok < 8:
        print("WARNING: fewer than 8 successful captures - baseline incomplete.")
        sys.exit(2)


if __name__ == "__main__":
    main()