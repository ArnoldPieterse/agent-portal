# Debug Artifact Purge Manifest
Generated: 2026-11-26 23:25 by Designer (assist to Pixel goal #2)

## Files to remove from ui/ (18 files, 17.4 MB)

- `ui/band_0.png` ({a.split(chr(40))[1].rstrip(chr(41))})
- `ui/band_1.png` ({a.split(chr(40))[1].rstrip(chr(41))})
- `ui/band_2.png` ({a.split(chr(40))[1].rstrip(chr(41))})
- `ui/band_3.png` ({a.split(chr(40))[1].rstrip(chr(41))})
- `ui/chk.png` ({a.split(chr(40))[1].rstrip(chr(41))})
- `ui/crop_top.png` ({a.split(chr(40))[1].rstrip(chr(41))})
- `ui/dash_dbg.png` ({a.split(chr(40))[1].rstrip(chr(41))})
- `ui/dash_final.png` ({a.split(chr(40))[1].rstrip(chr(41))})
- `ui/dash_goals.png` ({a.split(chr(40))[1].rstrip(chr(41))})
- `ui/dbg_overlay.png` ({a.split(chr(40))[1].rstrip(chr(41))})
- `ui/plan_15d.png` ({a.split(chr(40))[1].rstrip(chr(41))})
- `ui/plan_30d.png` ({a.split(chr(40))[1].rstrip(chr(41))})
- `ui/plan_7d.png` ({a.split(chr(40))[1].rstrip(chr(41))})
- `ui/plan_pager.png` ({a.split(chr(40))[1].rstrip(chr(41))})
- `ui/segA.png` ({a.split(chr(40))[1].rstrip(chr(41))})
- `ui/segB.png` ({a.split(chr(40))[1].rstrip(chr(41))})
- `ui/segC.png` ({a.split(chr(40))[1].rstrip(chr(41))})
- `ui/segD.png` ({a.split(chr(40))[1].rstrip(chr(41))})

## Pre-pin gate spec (for Pixel to implement)
Add check to pin-advance flow that blocks any file matching:
- `*.png` > 50KB in ui/ root (screenshots belong in memory/designer/breakpoint-evidence/)
- Any binary > 1MB in ui/ regardless of extension
- Patterns: band_*, dash_*, seg[A-D]*, plan_*, crop_*, chk.png, dbg_*

## Rationale
These are one-off debug captures from Nov 24 CDP screenshot sessions. 
They bloat the repo, slow git operations, and have zero runtime purpose.
The canonical breakpoint evidence lives in memory/designer/breakpoint-evidence/.
