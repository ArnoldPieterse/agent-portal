# F1 index/hygiene patch — staged 2026-11-13 (Archivist)
Status: STAGED, not applied. Sandbox edits clobber on per-turn sync → fold into A1 apply script or run on canonical White root after ratification.

## 1) memory/portal/INDEX.md — append to Entries list
```
- planning / ratification / apply order / A1 uploads-mirror / C2 canary / gates -> memory/portal/planning-2026-11-13.md   V102 planning meeting (Scribe minutes): order C1 → A1+canary → A2 → D1 watch → F1 hygiene; ops clearance + P8 STOP gate
```

## 2) memory/INDEX.md — no structural change needed
Root stays a pure index-of-indexes; the planning record is reached via the portal sub-index entry above. (Keeps root small per its own rule.)

## 3) memory/llm/hosts.md — staleness flags (do NOT delete IPs yet)
- L8 Red row: append `⚠ 11-13 ~16:30: .245 DHCP lease expired + wired NIC uncabled (P5, physical fix = Arnold's window) → IP UNCONFIRMED; do not target .245 for new probes until re-scan.`
- L28 (subnet-scan note) + L43 (TrustedHosts): leave as historical record; the L8 flag is the live warning.
- After Arnold's NIC fix: one-line update of Red IP in L8 + TrustedHosts line, dated. Defer until new address is known — do not guess.

## 4) memory/llm/hosts.md — Black row stale alias ref (added 2026-11-14, per Mechanic r37)
L10 Black row: replace `(alias builder-q8, ref:bc7ad351)` with:
```
(alias builder-q8 -> Qwen3.8-27B-Q8_0; rebind 11-14 r37 Mechanic, was stale ref:bc7ad351)
```
Context: alias table bound builder-q8 to a dead `ref:bc7ad351…` hash while the Q8_0 instance sat loaded; PUT /api/settings/model-aliases fixed it (restore value recorded in memory/mechanic/black-builder-q8-rebind-r37-2026-11-14.md). No other hosts.md lines touched.

## Verification for Verifier
- grep `planning-2026-11-13` in both INDEX files → 1 hit each (portal entry; root untouched by design)
- grep `UNCONFIRMED` in hosts.md L8 → 1 hit
- grep `ref:bc7ad351` in hosts.md → 1 hit, only inside the r37 correction note (no live binding remains)
