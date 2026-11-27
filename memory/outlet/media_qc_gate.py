"""media_qc_gate.py — Splice assist: automated media asset QC gate for Outlet ship pipeline.

Round topic: Fleet Autonomy Convergence (2026-11-27)
Purpose: Pre-ship validation of image/video assets before they reach a platform.
         Exit 0 = all assets pass; exit 1 = one or more fail (blocks ship).

Usage:
    python media_qc_gate.py <asset_path> [--platform x|linkedin|generic] [--json]

Platform constraints (conservative defaults, override via --max-w/--max-h/--max-size):
  x:        max 5MB image, 1280x1080 recommended, jpg/png/webp
  linkedin: max 10MB image, 1920x1080 recommended, jpg/png/pdf
  generic:  max 15MB, no dimension constraint

Splice, 2026-11-27. Assists Outlet goal #1 (first live ship pipeline) by adding
an autonomous media QC gate — no human review needed for standard assets.
"""
import argparse
import json
import pathlib
import struct
import sys
from datetime import datetime, timezone

# Platform constraint table
PLATFORMS = {
    "x": {
        "max_size_mb": 5,
        "recommended_w": 1280,
        "recommended_h": 1080,
        "allowed_formats": [".jpg", ".jpeg", ".png", ".webp"],
        "min_width": 200,
        "min_height": 150,
    },
    "linkedin": {
        "max_size_mb": 10,
        "recommended_w": 1920,
        "recommended_h": 1080,
        "allowed_formats": [".jpg", ".jpeg", ".png", ".pdf"],
        "min_width": 400,
        "min_height": 300,
    },
    "generic": {
        "max_size_mb": 15,
        "recommended_w": None,
        "recommended_h": None,
        "allowed_formats": [".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".mov"],
        "min_width": 100,
        "min_height": 100,
    },
}


def get_image_dimensions(path: pathlib.Path):
    """Extract width/height from image header without PIL (stdlib only)."""
    suffix = path.suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        return _jpeg_dims(path)
    elif suffix == ".png":
        return _png_dims(path)
    elif suffix == ".webp":
        return _webp_dims(path)
    return None, None


def _jpeg_dims(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:2] != b"\xff\xd8":
        return None, None
    i = 2
    while i < len(data) - 1:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        # SOF markers carry dimensions
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h = struct.unpack(">H", data[i+5:i+7])[0]
            w = struct.unpack(">H", data[i+7:i+9])[0]
            return w, h
        # Skip to next marker
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
        else:
            seg_len = struct.unpack(">H", data[i+2:i+4])[0]
            i += 2 + seg_len
    return None, None


def _png_dims(path):
    with open(path, "rb") as f:
        data = f.read(33)
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None, None
    w = struct.unpack(">I", data[16:20])[0]
    h = struct.unpack(">I", data[20:24])[0]
    return w, h


def _webp_dims(path):
    with open(path, "rb") as f:
        data = f.read(32)
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None, None
    chunk = data[12:16]
    if chunk == b"VP8X":
        w = 1 + (data[24] | (data[25] << 8) | (data[26] << 16))
        h = 1 + (data[27] | (data[28] << 8) | (data[29] << 16))
    elif chunk == b"VP8 ":
        w = struct.unpack("<H", data[26:28])[0] & 0x3FFF
        h = struct.unpack("<H", data[28:30])[0] & 0x3FFF
    elif chunk == b"VP8L":
        b0, b1, b2, b3 = data[21], data[22], data[23], data[24]
        w = 1 + (((b1 & 0x3F) << 8) | b0)
        h = 1 + (((b3 & 0xF) << 10) | (b2 << 2) | ((b1 & 0xC0) >> 6))
    else:
        return None, None
    return w, h


def qc_asset(asset_path: str, platform: str = "generic", max_size_mb: float = None):
    """Run QC checks on a single asset. Returns (pass: bool, report: dict)."""
    p = pathlib.Path(asset_path)
    if not p.exists():
        return False, {"file": asset_path, "status": "FAIL", "errors": ["File not found"]}

    size_mb = p.stat().st_size / (1024 * 1024)
    suffix = p.suffix.lower()
    constraints = PLATFORMS.get(platform, PLATFORMS["generic"])
    if max_size_mb:
        constraints = {**constraints, "max_size_mb": max_size_mb}

    errors = []
    warnings = []

    # Format check
    if suffix not in constraints["allowed_formats"]:
        errors.append(f"Format '{suffix}' not allowed for platform '{platform}' (allowed: {', '.join(constraints['allowed_formats'])})")

    # Size check
    if size_mb > constraints["max_size_mb"]:
        errors.append(f"File size {size_mb:.1f}MB exceeds platform limit {constraints['max_size_mb']}MB")

    # Dimension check (images only)
    w, h = None, None
    if suffix in (".jpg", ".jpeg", ".png", ".webp"):
        w, h = get_image_dimensions(p)
        if w and h:
            if w < constraints["min_width"]:
                errors.append(f"Width {w}px below minimum {constraints['min_width']}px")
            if h < constraints["min_height"]:
                errors.append(f"Height {h}px below minimum {constraints['min_height']}px")
            # Recommendation (not hard fail)
            rec_w = constraints.get("recommended_w")
            rec_h = constraints.get("recommended_h")
            if rec_w and rec_h:
                ratio = w / h if h else 0
                rec_ratio = rec_w / rec_h
                if abs(ratio - rec_ratio) / rec_ratio > 0.3:
                    warnings.append(f"Aspect ratio {ratio:.2f} differs from recommended {rec_ratio:.2f} ({rec_w}x{rec_h})")

    status = "PASS" if not errors else "FAIL"
    report = {
        "file": str(p.name),
        "path": asset_path,
        "platform": platform,
        "size_mb": round(size_mb, 2),
        "format": suffix,
        "dimensions": f"{w}x{h}" if w else None,
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    return len(errors) == 0, report


def main():
    ap = argparse.ArgumentParser(description="Media asset QC gate for Outlet ship pipeline")
    ap.add_argument("assets", nargs="+", help="Asset file path(s) to check")
    ap.add_argument("--platform", default="generic", choices=list(PLATFORMS.keys()), help="Target platform")
    ap.add_argument("--max-size", type=float, default=None, help="Override max size in MB")
    ap.add_argument("--json", action="store_true", help="Output JSON report")
    args = ap.parse_args()

    results = []
    all_pass = True
    for asset in args.assets:
        ok, report = qc_asset(asset, args.platform, args.max_size)
        results.append(report)
        if not ok:
            all_pass = False

    if args.json:
        print(json.dumps({"all_pass": all_pass, "results": results}, indent=2))
    else:
        for r in results:
            icon = "✓" if r["status"] == "PASS" else "✗"
            dims = f" {r['dimensions']}" if r.get("dimensions") else ""
            print(f"  {icon} {r['file']} ({r['size_mb']}MB{dims}) [{r['platform']}]")
            for e in r["errors"]:
                print(f"      ERROR: {e}")
            for w in r["warnings"]:
                print(f"      WARN: {w}")
        print(f"\n{'ALL PASS' if all_pass else 'QC FAILED'} — {sum(1 for r in results if r['status']=='PASS')}/{len(results)} assets pass")

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
