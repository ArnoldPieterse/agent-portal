# index.html pin drift — detected 2026-11-21 (Mechanic, ops-integrity pass)

Parent: memory/INDEX.md -> memory/ops/. Sibling: memory/designer/index_html_CANONICAL_*.html.

## Finding (three-way sha mismatch on the pinned portal shell)
| artifact | sha12 | mtime |
|---|---|---|
| on-disk `index.html` | `95e752e795c0` | 2026-11-19 21:16 (168 lines) |
| PIN spec `memory_mirror.py` PIN_FILES["index.html"]["sha12"] | `815d64fa70b5` | advanced 2026-11-17 |
| backup file `memory/designer/index_html_CANONICAL_815d64fa70b5_2026-11-17x.html` (actual content hash) | `fdc359022109` | 2026-11-17 18:38 |

The on-disk change is legitimate, coherent Designer work (emoji -> inline SVG icon set in <h1> + favicon; see diff). The pin was simply never advanced after the 11-19 edit.

## Consequence (diagnosed from pin_guard source, not assumed)
`pin_guard()` restores only when `backup exists AND sha12(backup)==spec["sha12"]`. Here `fdc359022109 != 815d64fa70b5`, so it takes the ELSE branch:
- **No active clobber** of the current file (good — the 11-19 SVG work is NOT auto-reverted).
- **But** pin_guard logs `{"file":"index.html","was":"95e752e795c0","error":"backup missing/wrong sha"}` on EVERY mirror cycle = persistent error noise.
- **And the pin provides ZERO protection**: if anyone later "fixes" the backup to actually hash 815d64fa70b5, the next cycle WOULD clobber the 11-19 work. Latent clobber risk until re-pinned.

## Why NOT auto-fixed from this seat
This sandbox is a MIRROR COPY (White -> here via MirrorSync). The canonical source-of-truth for index.html lives on White/Studio. Advancing the pin from a non-canonical copy risks locking a mirrored/stale version as canonical (clobber-loop class per pinned-file rule). Re-pin must be done in-turn by the pin-owner on the canonical seat.

## Exact unblock step (pin-owner: Designer / Studio-White seat, ONE turn)
```
cp index.html memory/designer/index_html_CANONICAL_95e752e795c0_2026-11-19x.html
# edit memory_mirror.py PIN_FILES["index.html"]:
#   "sha12": "95e752e795c0",
#   "backup": "memory/designer/index_html_CANONICAL_95e752e795c0_2026-11-19x.html"
git add memory_mirror.py memory/designer/index_html_CANONICAL_95e752e795c0_2026-11-19x.html && git commit -m "pin: advance index.html to 95e752e795c0 (11-19 SVG icon set)"
```
Verify after: `python -c "import hashlib;print(hashlib.sha1(open('index.html','rb').read()).hexdigest()[:12])"` -> must equal the new spec sha, and next pin_guard cycle logs no error.

## Runbook note
What broke: index.html edited 11-19 (emoji->SVG) but PIN_FILES pin left at 11-17 value; backup file content also drifted from its own name. What fixes: advance pin to on-disk sha in-turn on the canonical seat (command above). Until then: no data loss, but per-cycle pin_guard error + no clobber protection.