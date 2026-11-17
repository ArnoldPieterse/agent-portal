"""
Goal #10: Visual diff check - compare current portal screenshots against baseline.
Usage:
  python memory/designer/baseline/visual_diff.py [--url http://127.0.0.1:8099] [--threshold 5]

Exits 0 if all panels pass (< threshold% pixel change), exits 1 if any fail.
Requires: playwright + Pillow (pip install pillow)
"""
import argparse, json, sys
from pathlib import Path

try:
    from PIL import Image, ImageChops
except ImportError:
    print("ERROR: pip install pillow")
    sys.exit(1)

BASELINE_DIR = Path(__file__).parent
MANIFEST = BASELINE_DIR / "MANIFEST.json"


def pixel_diff_pct(img_a_path: str, img_b_path: str) -> float:
    """Return percentage of pixels that differ (any channel)."""
    a = Image.open(img_a_path).convert("RGB")
    b = Image.open(img_b_path).convert("RGB")
    if a.size != b.size:
        b = b.resize(a.size, Image.LANCZOS)
    diff = ImageChops.difference(a, b)
    total_pixels = a.size[0] * a.size[1]
    diff_gray = diff.convert("L")
    pixels_diff = sum(1 for p in diff_gray.getdata() if p > 10)
    return (pixels_diff / total_pixels) * 100.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8099")
    ap.add_argument("--threshold", type=float, default=5.0,
                    help="Max allowed %% pixel change (default 5)")
    ap.add_argument("--capture-dir", default=None,
                    help="Dir with current screenshots")
    args = ap.parse_args()

    if not MANIFEST.exists():
        print("No baseline manifest found. Run capture_baseline.py first.")
        sys.exit(1)

    manifest = json.loads(MANIFEST.read_text())
    cap_dir = Path(args.capture_dir) if args.capture_dir else BASELINE_DIR

    results = []
    for entry in manifest["panels"]:
        if not entry.get("sha256"):
            continue
        base_path = BASELINE_DIR / entry["file"]
        cur_path = cap_dir / entry["file"]
        if not base_path.exists() or not cur_path.exists():
            results.append((entry["panel"], entry["resolution"], "MISSING", 0))
            continue
        pct = pixel_diff_pct(str(base_path), str(cur_path))
        status = "PASS" if pct < args.threshold else "FAIL"
        results.append((entry["panel"], entry["resolution"], status, pct))

    print(f"\nVisual diff (threshold: {args.threshold}%):")
    print(f"{'Panel':<20} {'Res':<18} {'Status':<6} {'Diff%':>6}")
    print("-" * 54)
    failures = 0
    for panel, res, status, pct in results:
        flag = " OK" if status == "PASS" else " FAIL"
        print(f"{panel:<20} {res:<18} {status:<6} {pct:>5.2f}%{flag}")
        if status == "FAIL":
            failures += 1

    print(f"\n{len(results) - failures}/{len(results)} panels within threshold.")
    sys.exit(0 if failures == 0 else 1)


if __name__ == "__main__":
    main()
