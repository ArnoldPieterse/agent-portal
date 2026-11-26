#!/usr/bin/env python3
"""Pre-pin asset gate (pixel goal #9).

Blocks stray raster images / large binaries from landing in ui/. The UI is
all-SVG/CSS/JS: it references ZERO .png files (verified 2026-11-27, 38 source
files scanned). Debug screenshots (band_*, dash_*, segA-D, plan_*, crop_top,
chk, dbg_overlay) are never loaded by the UI and were purged from ui/.

Rules (fail = exit 1):
  * any raster image in ui/  -> .png/.jpg/.jpeg/.gif/.webp/.bmp/.ico
  * any NON-text binary file > --max-kb (default 64 KB) in ui/

Usage:
  python memory/pixel/prepin_asset_gate.py            # scan ui/; exit 0 clean / 1 offenders / 2 error
  python memory/pixel/prepin_asset_gate.py --selftest # prove it rejects an injected test .png

Wired as a pre-pin check: run before advancing any index.html pin, alongside
memory/pixel/prepin_token_gate.py.
"""
import os, sys, glob

RASTER_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico")
DEFAULT_MAX_KB = 64

def repo_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def is_binary(path, sample=8192):
    """Cheap binary sniff: NUL byte or high non-text ratio in the head chunk."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(sample)
    except OSError:
        return False
    if not head:
        return False
    if b"\x00" in head:
        return True
    non_text = sum(1 for b in head if (b < 9 or 13 < b < 32))
    return (non_text / len(head)) > 0.30

def scan_ui(ui, max_kb):
    """Return list of (file, reason, size_bytes) offenders."""
    out = []
    for p in sorted(glob.glob(os.path.join(ui, "*"))):
        if not os.path.isfile(p):
            continue
        low = p.lower()
        size = os.path.getsize(p)
        if low.endswith(RASTER_EXT):
            out.append((p, "raster image in ui/", size))
        elif size > max_kb * 1024 and is_binary(p):
            out.append((p, "binary > %dKB in ui/" % max_kb, size))
    return out

def selftest(max_kb=DEFAULT_MAX_KB):
    """Inject a tiny test .png into ui/, assert the gate flags it, then remove it."""
    ui = os.path.join(repo_root(), "ui")
    probe = os.path.join(ui, "_asset_gate_selftest.png")
    # 1x1 transparent PNG (67 bytes) - minimal valid raster
    png_b64 = ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M8AAAM"
               "BAQAY3d2fAAAAAElFTkSuQmCC")
    import base64
    created = False
    try:
        with open(probe, "wb") as fh:
            fh.write(base64.b64decode(png_b64))
        created = True
        offenders = scan_ui(ui, max_kb)
        flagged = any(os.path.basename(f) == "_asset_gate_selftest.png" for f, _, _ in offenders)
        print("selftest: injected test .png -> flagged=%s (offenders=%d)" % (flagged, len(offenders)))
        ok = flagged
    finally:
        if created and os.path.exists(probe):
            os.remove(probe)
    print("SELFTEST " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1

def main():
    max_kb = DEFAULT_MAX_KB
    args = sys.argv[1:]
    if "--selftest" in args:
        return selftest(max_kb)
    if "--max-kb" in args:
        i = args.index("--max-kb")
        try:
            max_kb = int(args[i + 1])
        except (IndexError, ValueError):
            print("GATE ERROR: --max-kb needs an integer argument")
            return 2
    ui = os.path.join(repo_root(), "ui")
    if not os.path.isdir(ui):
        print("GATE ERROR: ui/ directory not found at %s" % ui)
        return 2
    offenders = scan_ui(ui, max_kb)
    if offenders:
        for f, reason, size in offenders:
            print("OFFENDER %s  (%d KB)  [%s]" % (os.path.relpath(f, repo_root()), round(size / 1024, 1), reason))
        print("GATE FAIL: %d stray raster/binary asset(s) in ui/ (UI is all-SVG/CSS/JS; rasters belong in uploads/ or as data-URI/SVG)" % len(offenders))
        return 1
    n_files = len([f for f in glob.glob(os.path.join(ui, "*")) if os.path.isfile(f)])
    print("PASS: 0 stray raster/large-binary assets in ui/ (%d files scanned; rasters blocked)" % n_files)
    return 0

if __name__ == "__main__":
    sys.exit(main())
