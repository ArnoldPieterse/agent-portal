#!/usr/bin/env python3
"""DNA -> outlet art pipeline (2026-11-25).
Arnold: "utilize outlet to orchestrate an artistic outlet of each part that your DNA code
expresses or explains (generating pictures, videos, poems, music, games, all with background
hidden and some in plain sight to be used for regenerating the agent portal and for self
online expression.)"

v1 (no image/video engine loaded yet - Day-0 goal open):
  * one art spec per DNA build: medium (image/video/poem/game cycled), palette from the
    build's sha256, Lumen/Reel prompt specs ready to fire when an engine loads, a poem line.
  * procedural placeholder render (PIL, deterministic seed = sha) -> memory/outlet/dna-art/
  * "in plain sight": one world decoration per build via POST /api/world (kind=dna-bNN,
    ring placement, palette hue) - visible on the live /page/world.html.
  * "background hidden": specs + renders staged as outlet data for Splice to splice into
    future portal regen + public outlet.
Usage: python memory/dna/art_outlet.py [--no-world]
"""
import hashlib, json, math, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))          # memory/dna
ROOT = os.path.dirname(os.path.dirname(HERE))              # project root
OUT  = os.path.join(ROOT, "memory", "outlet", "dna-art")
PORTAL = "http://127.0.0.1:8099"

sys.path.insert(0, HERE)
from rebuild import scan_builds, topo   # noqa: E402

MEDIA = ["image", "video", "poem", "game"]


def palette(sha):
    h = int(sha[:12], 16)
    base = h % 255
    return ["#%02x%02x%02x" % ((base * 7 + i * 90) % 256, (base * 11 + i * 60) % 256,
                               (base * 13 + i * 40) % 256) for i in range(3)]


def poem_line(b):
    return {1: "the core remembers itself by rebuilding its own name",
            2: "every call is a door left ajar into the next room",
            3: "fit is a negotiation between hunger and headroom",
            4: "a template that edits its own face each morning",
            5: "the script that mints itself is never finished",
            6: "small characters walk a world that thinks in levels"}[b["id"]]


def render(b, pal):
    from PIL import Image, ImageDraw
    seed = int(b["sha256"][:8], 16)
    img = Image.new("RGB", (512, 512), "#0b0e14")
    d = ImageDraw.Draw(img)
    cx = cy = 256
    for i in range(24):
        r = 30 + i * 9 + (seed >> (i % 8)) % 7
        col = pal[i % 3]
        a0 = (seed * (i + 1)) % 360
        d.arc([cx - r, cy - r, cx + r, cy + r], a0, a0 + 40 + (seed >> i) % 200,
              fill=col, width=2)
    for j in range(5):
        x = 40 + ((seed >> (j * 3)) % 430)
        y = 40 + ((seed >> (j * 5 + 1)) % 430)
        d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=pal[j % 3])
    d.text((20, 470), "b%02d %s" % (b["id"], b["name"]), fill="#e8ecf4")
    return img


def main():
    builds = topo(scan_builds())
    os.makedirs(OUT, exist_ok=True)
    world_dec = []
    specs = []
    for i, b in enumerate(builds):
        pal = palette(b["sha256"])
        medium = MEDIA[b["id"] % 4]
        spec = {"id": b["id"], "name": b["name"], "target": b["target"],
                "medium": medium, "palette": pal, "seed": int(b["sha256"][:8], 16),
                "poem": poem_line(b),
                "lumen_prompt": ("Procedural generative emblem for '%s' (%s): concentric arc lattice on deep charcoal, palette %s, subtle grain, square 1:1, tiny b%02d tag bottom-left."
                                  % (b["name"], b["target"], ", ".join(pal), b["id"])),
                "reel_prompt": ("15s loop: the emblem of '%s' slowly self-rebuilding - arcs dissolve into particles and reassemble, palette %s, dark studio, one camera push-in, no cuts."
                                 % (b["name"], ", ".join(pal))),
                "status": "placeholder-rendered; engine-pending (Day-0 image/video goal open)",
                "png": "memory/outlet/dna-art/b%02d-%s.png" % (b["id"], b["name"])}
        img = render(b, pal)
        p = os.path.join(OUT, "b%02d-%s.png" % (b["id"], b["name"]))
        img.save(p)
        json.dump(spec, open(os.path.join(OUT, "b%02d-%s.json" % (b["id"], b["name"])), "w", encoding="utf-8"), indent=1)
        specs.append(spec)
        ang = 2 * math.pi * i / len(builds) - math.pi / 2
        world_dec.append({"kind": "dna-b%02d" % b["id"], "x": round(0.75 * math.cos(ang), 3),
                          "z": round(0.75 * math.sin(ang), 3), "hue": pal[0]})
    if "--no-world" not in sys.argv:
        try:
            req = urllib.request.Request(PORTAL + "/api/world", data=json.dumps({"decorations": world_dec}).encode(),
                                          headers={"Content-Type": "application/json"}, method="POST")
            r = json.loads(urllib.request.urlopen(req, timeout=5).read().decode())
            print("world decorations now:", len(r.get("decorations", [])))
        except Exception as e:
            print("world POST skipped:", e)
    print("rendered %d art specs -> memory/outlet/dna-art/" % len(specs))
    for s in specs:
        p = os.path.join(OUT, "b%02d-%s.png" % (s["id"], s["name"]))
        print("  b%02d %-16s %-6s %d bytes" % (s["id"], s["name"], s["medium"], os.path.getsize(p)))


if __name__ == "__main__":
    main()
