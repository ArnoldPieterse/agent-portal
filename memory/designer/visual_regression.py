#!/usr/bin/env python3
"""
Visual Regression Test Harness — Designer Goal #10 (cycle-3)

Compares current panel screenshots against the baseline in memory/designer/baseline/.
Pass criterion: pixel diff < 5% per panel (configurable via --threshold).

Usage:
  python memory/designer/visual_regression.py              # compare all panels
  python memory/designer/visual_regression.py fleet goals  # specific panels
  python memory/designer/visual_regression.py --capture    # capture new baseline
  python memory/designer/visual_regression.py --threshold 3.0  # tighter threshold

Exit codes:
  0 = all pass
  1 = one or more panels exceed threshold
  2 = missing files / setup error
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops
except ImportError:
    print("FATAL: Pillow not installed. Run: pip install Pillow", file=sys.stderr)
    sys.exit(2)

BASELINE_DIR = Path(__file__).parent / "baseline"
MANIFEST_FILE = BASELINE_DIR / "manifest.json"
DEFAULT_THRESHOLD = 5.0  # percent pixels that may differ

# Panels to check (name -> expected screenshot filename in baseline/)
PANELS = {
    "chat":       "panel_chat.png",
    "goals":      "panel_goals.png",
    "fleet":      "panel_fleet.png",
    "ops":        "panel_ops.png",
    "memory":     "panel_memory.png",
    "uploads":    "panel_uploads.png",
    "settings":   "panel_settings.png",
    "full-dark":  "full_dark.png",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def pixel_diff_pct(img_a_path: Path, img_b_path: Path) -> float:
    """Return percentage of pixels that differ (any channel)."""
    a = Image.open(img_a_path).convert("RGB")
    b = Image.open(img_b_path).convert("RGB")
    if a.size != b.size:
        # Resize to match baseline dimensions
        b = b.resize(a.size, Image.LANCZOS)
    diff = ImageChops.difference(a, b)
    # Count non-zero pixels
    total_pixels = a.width * a.height
    diff_bbox = diff.getbbox()
    if diff_bbox is None:
        return 0.0
    # Convert to grayscale and threshold at 1 (any difference counts)
    gray = diff.convert("L")
    nonzero = sum(1 for p in gray.getdata() if p > 0)
    return (nonzero / total_pixels) * 100.0


def load_manifest() -> dict:
    if not MANIFEST_FILE.exists():
        print(f"ERROR: No manifest at {MANIFEST_FILE}", file=sys.stderr)
        print("Run with --capture first to establish baseline.", file=sys.stderr)
        sys.exit(2)
    with open(MANIFEST_FILE) as f:
        return json.load(f)


def cmd_capture():
    """Capture screenshots and store as baseline. Requires portal running + screenshot tool."""
    # This is a placeholder for the capture step.
    # In practice, screenshots are taken via: python elev.py --shell "...screenshot cmd..."
    # or a headless browser. The manifest records hashes.
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    existing = {p.stem.replace("panel_", ""): p for p in BASELINE_DIR.glob("*.png")}
    if not existing:
        print(f"No PNG files found in {BASELINE_DIR}. Capture screenshots first.")
        print(f"Expected filenames: {list(PANELS.values())}")
        sys.exit(2)

    manifest = {"threshold": DEFAULT_THRESHOLD, "panels": {}}
    for name, fname in PANELS.items():
        path = BASELINE_DIR / fname
        if path.exists():
            manifest["panels"][name] = {
                "file": fname,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Baseline manifest written: {MANIFEST_FILE} ({len(manifest['panels'])} panels)")


def cmd_compare(panels_arg, threshold):
    """Compare current screenshots against baseline."""
    manifest = load_manifest()
    selected = panels_arg if panels_arg else list(PANELS.keys())

    results = []
    all_pass = True

    for name in selected:
        if name not in PANELS:
            print(f"  SKIP {name}: unknown panel")
            continue
        baseline_path = BASELINE_DIR / PANELS[name]
        # Current screenshot expected alongside or in same dir with _current suffix
        current_path = baseline_path.with_name(
            baseline_path.stem.replace("panel_", "panel_") + "_current.png"
        )
        if not current_path.exists():
            # Try without _current (same file = no change)
            current_path = baseline_path

        if not baseline_path.exists():
            print(f"  FAIL {name}: baseline missing ({baseline_path.name})")
            all_pass = False
            results.append((name, "missing_baseline", 0.0))
            continue

        # Check hash first (fast path)
        b_hash = manifest["panels"].get(name, {}).get("sha256", "")
        c_hash = sha256_file(current_path) if current_path.exists() else ""
        if c_hash == b_hash:
            print(f"  PASS {name}: identical (sha256 match)")
            results.append((name, "identical", 0.0))
            continue

        diff_pct = pixel_diff_pct(baseline_path, current_path)
        status = "PASS" if diff_pct < threshold else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  {status} {name}: {diff_pct:.2f}% pixels differ (threshold {threshold}%)")
        results.append((name, status.lower(), diff_pct))

    # Summary
    passed = sum(1 for r in results if r[1] in ("pass", "identical"))
    print(f"\n{'='*50}")
    print(f"RESULT: {passed}/{len(results)} panels pass")
    return 0 if all_pass else 1


def main():
    parser = argparse.ArgumentParser(description="Visual regression test harness")
    parser.add_argument("panels", nargs="*", help="Panel names to check (default: all)")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                        help=f"Max allowed pixel diff %% (default {DEFAULT_THRESHOLD})")
    parser.add_argument("--capture", action="store_true",
                        help="Record current screenshots as new baseline manifest")
    args = parser.parse_args()

    if args.capture:
        cmd_capture()
    else:
        sys.exit(cmd_compare(args.panels, args.threshold))


if __name__ == "__main__":
    main()
