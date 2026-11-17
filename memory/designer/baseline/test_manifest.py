#!/usr/bin/env python3
"""
test_manifest.py - Integration test for manifest.py using synthetic PNG fixtures.
Proves the full generate/verify pipeline works without a live browser.

Run: python memory/designer/baseline/test_manifest.py
Exit 0 = all pass, 1 = failure detected.
"""
import os, sys, json, tempfile, shutil
from PIL import Image, ImageDraw

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MANIFEST_PY = os.path.join(BASE_DIR, "manifest.py")

def run():
    tmpdir = tempfile.mkdtemp(prefix="manifest_test_")
    try:
        # Create 8 synthetic panel screenshots
        panels = [
            ("goals-panel-1920.png",   (1920, 1080), (30, 40, 50)),
            ("fleet-panel-1920.png",   (1920, 1080), (50, 30, 70)),
            ("ops-panel-1920.png",     (1920, 1080), (70, 50, 30)),
            ("memory-panel-1920.png",  (1920, 1080), (40, 60, 80)),
            ("uploads-panel-1920.png", (1920, 1080), (60, 80, 40)),
            ("goals-panel-1024.png",   (1024, 768),  (30, 50, 40)),
            ("fleet-panel-1024.png",   (1024, 768),  (50, 40, 60)),
            ("ops-panel-1024.png",     (1024, 768),  (40, 70, 50)),
        ]
        for name, size, color in panels:
            img = Image.new("RGB", size, color)
            d = ImageDraw.Draw(img)
            for i in range(0, size[1], 40):
                d.line([(0, i), (size[0], i)], fill=(min(color[0]+50,255), min(color[1]+50,255), min(color[2]+50,255)))
            img.save(os.path.join(tmpdir, name))

        # Import manifest module with patched BASE
        import importlib.util
        spec = importlib.util.spec_from_file_location("manifest", MANIFEST_PY)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.BASE = tmpdir
        mod.MANIFEST = os.path.join(tmpdir, "manifest.json")

        # Test 1: generate produces valid manifest with closure met
        rc = mod.generate()
        assert rc == 0, f"generate() returned {rc}"
        with open(mod.MANIFEST) as f:
            m = json.load(f)
        assert m["file_count"] == 8
        assert m["meets_closure"] is True
        print("[1/5] PASS: generate() -> 8 files, closure met")

        # Test 2: verify passes on intact baseline
        rc = mod.verify()
        assert rc == 0, f"verify() returned {rc} on intact files"
        print("[2/5] PASS: verify() clean on intact baseline")

        # Test 3: detect modification
        target = os.path.join(tmpdir, "fleet-panel-1920.png")
        with open(target, "ab") as f:
            f.write(b"tamper")
        rc = mod.verify()
        assert rc == 1, f"verify() returned {rc}, expected 1 (tamper)"
        print("[3/5] PASS: verify() detects modified file")

        # Test 4: detect missing file
        os.remove(os.path.join(tmpdir, "ops-panel-1920.png"))
        rc = mod.verify()
        assert rc == 1, f"verify() returned {rc}, expected 1 (missing)"
        print("[4/5] PASS: verify() detects missing file")

        # Test 5: detect untracked file
        Image.new("RGB", (100, 100), (255, 0, 0)).save(os.path.join(tmpdir, "rogue.png"))
        rc = mod.verify()
        assert rc == 1, f"verify() returned {rc}, expected 1 (untracked)"
        print("[5/5] PASS: verify() detects untracked file")

        print("\nALL 5 TESTS PASSED - manifest.py pipeline validated end-to-end.")
        return 0
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    sys.exit(run())
