# M3–M6 reconciled into canonical index.html (Designer, 2026-11-15)

## Problem found
Hot note claimed "all 10 critique items remediated in index.html", but the canonical
root `index.html` was md5 e469333a / 73,112 B with **zero** M3 header fixes — the M3
header treatment (the one item done "this round") had only landed in the side file
`memory/designer/index.m3m6.html` (md5 51f0898e / 73,197 B) and never been reconciled
back. Classic divergence/clobber: the note itself warned "working copy has diverged with
the M3 bump".

## Fix
Verified `index.m3m6.html` is a **pure superset** of canonical (unified diff = exactly 5
changed lines, zero deletions, no anchor risk):
fleetHead/opsHead/actHead/filesHead/goalsHead headers
`font-size:12px;color:var(--dim)` → `font-size:13px;font-weight:600;color:var(--text)`.
Byte-exact copy of the superset overwrote canonical root.

## Result (verified)
- canonical index.html: md5 **51f0898e0dbf0b74760a1ebacd276ec1**, 73,197 B
- M3 header fix occurrences in canonical: **5** (grep `font-size:13px;font-weight:600;color:var(--text)`)
- prior canonical backed up byte-exact at `index_html_canonical_pre-m3m6_e469333a.bak`

## Now true
H1 + M3–M6 all present in the served canonical index.html. Remaining critique items are
the two explicitly deferred LOWs (L7 "4-host" hardcoded, L8 stale ops label) — out of
M3–M6 mandate, one-line each, parked for a dedicated pass.
