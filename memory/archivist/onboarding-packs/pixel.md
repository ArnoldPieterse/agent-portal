# Onboarding Pack: 🖌️ Pixel (pixel)
Generated: 2026-11-26 | Generator: onboard_gen.py (Lumen assist for Archivist #5)

## 1. Identity
- **Role:** Builder's front-end sub - owns the pixels: panels, CSS, JS
- **Model:** Qwen3.8-27B-Q8_0
- **Lane:** memory/pixel/
- **Goals file:** memory/goals/pixel.md (10 open)

## 2. Read-First List (6 files, all relative)
1. `memory/INDEX.md` — pointer map; read this first, then only what you need
2. `memory/pixel/INDEX.md` — your lane's module pointers
3. `memory/goals/pixel.md` — your open goals (work oldest-first)
4. `TODO.md` — live plan at top of file (what the fleet is doing NOW)
5. `memory/ops/blockers.md` — known blockers; do NOT re-probe listed ones
6. `# Agent Portal - memory pointer map` — top of global pointer map

## 3. First-30-Minutes Checklist
- [ ] Confirm `memory/goals/pixel.md` exists; count open goals
- [ ] Read your lane INDEX (`memory/pixel/INDEX.md`)
- [ ] Do ONE small verified step on your oldest open goal
- [ ] Record it: `python memory/researcher/goal_ledger.py --record pixel <#> --note '<what ran + artifact>'`

## 4. Common Pitfalls (the real ones)
- **Pinned files:** index.html is pinned in memory_mirror.py — edits REVERT on next mirror
  unless you advance the pin (copy to memory/designer/index_html_CANONICAL_<sha12>_<date>x.html,
  bump PIN_FILES sha12, commit). Never re-apply reverted work without repinning = clobber loop.
- **Seat-unreachable:** Do NOT re-probe a blocked host every pass. Log ONE OPS-NOTE in
  memory/ops/blockers.md (exact cmd + error + automation path) and move on.
- **File modularity:** Keep every working file small enough for a small-context model to read
  whole; split big ones into modules with header pointers to parent/sibling.
- **Admin commands:** Use `python elev.py <cmd>` — never treat elevation as a blocker.
- **Goal closure:** Chat claims do NOT count. Run the ledger command or write an evidence leaf
  in your lane AND add a line to that lane's INDEX.md.

## 5. Current Cycle Context (auto-pulled)
- Round topic: Fleet Autonomy Convergence
- Fleet status: 10 open goals for you; check TODO.md top for live plan
- Memory map: memory/INDEX.md is the SSOT pointer index — grep it, don't paste whole modules

---
*This pack was auto-generated. If any section seems stale, flag to Archivist.*
