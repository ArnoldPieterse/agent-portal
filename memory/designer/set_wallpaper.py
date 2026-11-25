"""set_wallpaper.py - set or cycle the fleet wallpaper range (Designer, 2026-11-25).
Usage: python set_wallpaper.py [file|next]   (no arg = next in range)"""
import os, sys, json, ctypes
HERE = os.path.dirname(os.path.abspath(__file__))
rng = json.load(open(os.path.join(HERE, "wallpaper-range.json"), encoding="utf-8"))
P = os.path.join(HERE, "lumen", "portraits")
arg = sys.argv[1] if len(sys.argv) > 1 else "next"
if arg == "next":
    cur = (ctypes.windll.user32.SystemParametersInfoW(0x001D, 0, None, 4) or "").strip()  # SPI_GETDESKWALLPAPER
    names = [e["file"] for e in rng["range"]]
    i = names.index(os.path.basename(cur)) + 1 if os.path.basename(cur) in names else 0
    pick = names[i % len(names)]
else:
    pick = arg
path = os.path.abspath(os.path.join(P, pick))
assert os.path.isfile(path), "no such wallpaper: " + path
ok = bool(ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3))
print(("set " if ok else "FAILED ") + pick)
