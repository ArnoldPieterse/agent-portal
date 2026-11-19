# build_verify_pin.py — increment 1 verified (2026-11-20)

**Goal:** Builder cycle-7 #3 (Build-Verify-Pin Pipeline). **Artifact:** `memory/builder/build_verify_pin.py` (5.1 KB).

**What ran (in-process, no shell):**
- `[a] validate index.html` -> OK (parsed 239 elements)
- `[b] sha12` = `95e752e795c0` (14294 bytes)
- `[c] canonical copy` -> `memory/designer/index_html_CANONICAL_95e752e795c0_2026-11-20a.html` (14294 bytes); **sha12 of copy = 95e752e795c0 (matches source)**
- `[d] PIN_FILES line` emitted: `"index.html": ("95e752e795c0", "memory/designer/index_html_CANONICAL_95e752e795c0_2026-11-20a.html")`

**Failure paths proven:** broken CSS `body{}` -> exit 2 `unbalanced {}: 2 vs 1`; unbalanced JS `function f(){return [;}` -> exit 2 `unbalanced []: 1 vs 0`. Well-formed JS passes (heuristic, node unavailable in sandbox).

**Bug caught + fixed:** first version named the canonical base from the stem only (`index_CANONICAL_*`); corrected to the documented pin convention `index_html_CANONICAL_*` (full filename, dot->underscore). Re-verified sha-match after fix.

**Status: INCREMENT 1 DONE + verified.** Remaining for full closure of #3: (d) live `--apply <mirror>` edit of `PIN_FILES`, (e) git commit leg. Both gated on a non-empty `memory_mirror.py` vantage (file is 0 bytes in the Builder sandbox view; canonical lives on White). Dry-run default is safe until then.
