# Goal-progress state 2026-11-16 (Orchestrator, non-sandbox seat White)

## ROOT CAUSE FIXED (this turn)
memory/researcher/goal_ledger.py repo_root(): old code went up ONE level and tested
<root>/memory/memory (never exists) -> returned memory/researcher as root -> EVERY
(pointer:) leaf validated 'leaf missing' -> 5 evidence-backed goals stuck open.
FIXED: two levels up, test <root>/memory. All 5 pointer leaves now validate ok.
Strict parse: 61/80 -> 66/80 immediately (no restart needed for /api/goals: _goals_snapshot
re-imports the module per call; POST/sweep paths use cached mod -> restart to refresh).

## LIVE index.html REGRESSION FOUND
Current C:\Projects\Workspace\index.html = sha12 5908b45891d3, mtime 2026-11-15 19:13:02, 85653B.
NO design tokens (--sp-*/--fs-* ABSENT), NO @media queries, NO autofocus/tabindex,
33 distinct px literals. Designer evidence all references pin df1bbdaef684 (WCAG) /
37549a0412 (px-scale target) / 9df704ce020d (token refactor candidate).
=> Live file is an OLDER copy; mirror LWW flapping suspected. dir /s /b found df1bbdaef684
somewhere on disk (see _idx_where.txt - unread, window exhausted). NEXT: locate canonical,
restore, add to pin-registry/quarantine so mirror cannot clobber again.

## PER-GOAL STATUS (66/80; 14 open)
builder #2 [CLOSED via root fix] pointer memory/builder/MEMORY.md validates.
builder #5 OPEN - REAL: group_e2e.py LOST its truncation code (0 'truncat' hits); test
  fixture memory/builder/test_truncation_detect.py also gone. Evidence file describes the
  original change set (portal_chat finish_reason=length OR unbalanced function tags;
  truncated bool in return dict; TRUNCATED tag on prints; truncated_agents + has_truncation
  in result JSON). ACTION: re-implement + recreate fixture, run it.
builder #8 OPEN - testing.md exists (4838B) with per-endpoint edge-case tables; count
  cases per endpoint then append verified note to goal line.
builder #9 OPEN - curl examples exist in memory/builder/curl-examples-prune-git-2026-11-15.md
  (1708B, builder blocked by LWW from Black seat) but architecture.md has ZERO curl lines.
  ACTION: merge block into architecture.md 'Ops processes' section; run examples live vs :8099.
builder #10 OPEN - HONEST: last 40 commits (single identity 'Agent Portal') contain NO
  'verified:' line anywhere in subjects or bodies. Ongoing discipline not demonstrated.
  Leave open; do NOT fabricate.
designer #2 [CLOSED via root fix] pointer validates.
designer #3 OPEN - contrast evidence files solid (sweep: 16 pairs, all pass post-fix on
  pin df1bbdaef684) BUT live file is 5908b45891d3 -> must confirm WCAG pairs on the RESTORED
  file, then note.
designer #4 OPEN - px-scale was SPEC'D + ROUTED (px-scale-spec-2026-11-15.md) but live file
  has 33 unlisted px values -> not deployed. Honest: open until deployed+grepped.
designer #5 OPEN - keydown listeners exist in live file (2) = Enter/Shift+Enter base;
  autofocus/tabindex ABSENT in live file. Evidence says landed on sha 5b228d745716 (local).
  Needs restore check.
designer #6 [CLOSED via root fix] pointer validates.
designer #7 OPEN - NO @media in live file; responsive pass evidence references other pins.
designer #8 OPEN - component-reference.html exists (30a93b154d43); verify it uses real tokens.
designer #9 OPEN - needs empty-console check on restored portal (browser panel).
designer #10 OPEN - ui-tokens.md exists (3862B); check TODO cites it, then note.
mechanic #1 OPEN - uptime >=99% this week; tally at week end (today 2026-11-16 = Sunday?
  confirm weekday). Outage inputs: 5 planned restarts ~10s each + 18:25 wedge (see
  memory/ops/portal-outage-2026-11-15-1825.md) + portal-down-2026-11-15.md.
researcher #9 OPEN - TIME-GATED until ~2026-11-20. Leave open (honest).
verifier #5 OPEN - check test-report-2026-11-15.md / smoke-sweep for exact-command repros +
  non-repro filings; note if complete.
verifier #8 [CLOSED via root fix] pointer validates.
verifier #9 [CLOSED via root fix] pointer mirror-clobber-2026-11-15.md validates (note:
  TODO said 'only prune+git fresh' - the pointer itself is valid evidence per ledger rules).

## PENDING ACTIONS (next turns)
1. Locate df1bbdaef684 copy (dir /s /b output in _idx_where.txt), restore index.html,
   pin-protect it; restart portal per RESTART TRAP.
2. B5: re-implement truncation detection in group_e2e.py + fixture; run test.
3. B9: merge curl block into architecture.md; live-run vs :8099.
4. Append (verified:) notes ONLY where evidence holds after restore: B8, D3, D10 (+D5/D7 if
   restored file has them), V5 if repros documented.
5. Mechanic #1 tally at week end; researcher #9 stays open until 11-20.
