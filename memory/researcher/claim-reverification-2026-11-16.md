# Researcher — automated claim re-verification, first run (goal #1, 2026-11-16)

Load-bearing claims from memory, re-measured LIVE from the White shared root this pass (not re-read from notes). Tags: SUPPORTED = live output matches claim; INFERRED = not directly measurable here; DRIFT = claim stale.

| # | Claim (source) | Live check 2026-11-16 ~15:2x | Verdict |
|---|----------------|------------------------------|---------|
| 1 | "PUBLIC REPO LIVE (ArnoldPieterse/agent-portal)" (MEMORY.md GOAL line) | web fetch: github.com/ArnoldPieterse/agent-portal resolves, releases page indexed (search fetch, live today); /api/net/http probe returned 403 (UA-blocked — probe limitation, not repo state) | SUPPORTED (high) |
| 2 | "CHG-0002 ACCEPTED ... island status=living" (MEMORY.md GOAL line, cycle-1 text) | GET /api/evolution/stats: island agent-portal, living=2, born_total=2, survival_pct=100.0, CHG-0001+CHG-0002 listed | SUPPORTED (high) |
| 3 | "White Q8_0 = KEEP ... loaded on GPU1" (MEMORY.md GOAL line) | nvidia-smi: ~27GB VRAM on BOTH GPUs held by ONE llama-server (PID 33560, tensor-split, :57451); Studio alias probe atlas-q8 = 404 not_loaded; second instance (Q4 GPU0) absent | DRIFT — weights are resident but untracked by Studio routing; seat is functionally dead until routing/instances restored. KEEP decision itself stands (user directive) |
| 4 | "index.html pin 2c6399f2d853 carries the design tokens" (Designer #4 verified note, cycle-1 file) | sha1 of live index.html = 2c6399f2d853 exactly; :root defines --sp-4/8/12/16/24 + --fs-11..16; 160+60 var() usages | SUPPORTED (high) — also resolved contradiction C2 |
| 5 | "Fleet 3/3 hosts up" (netcmd fleet claim, 11-15) | GET /api/net/fleet today: Red :8888 open 2.9ms but :8099 timeout/filtered; Pale+Black details need re-pull (truncated in first read) | DRIFT (partial) — Red portal leg degraded since 11-15; H-OUT line opened |
| 6 | "SMB mirror syncs new attachments within 5 min" (Builder #2, cycle-1) | parity_audit.py disk==served + allowlist hash: 0 findings this pass; per-turn workspace sync verified (8/8 files identical between tool cwd and portal HERE — same tree on White) | SUPPORTED (medium — steady-state check, not a timed round-trip) |

**Pipeline note:** this file is the first instance of the standing cadence. Re-run trigger: any claim cited in a new goal closure OR weekly (whichever first). Raw outputs are inline above; no re-derivation from memory.
