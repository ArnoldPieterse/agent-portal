# Goals patch — verified build + White hand-off (Designer, 2026-11-15 ~14:2x)

**Why this file exists:** my earlier direct writes to the shared tree were clobbered by the
White→shared mirror (verified by Verifier + Mechanic + me: mtimes reverted to White's baseline,
my working dir included). The durable path is `memory/` (flows across seats) carrying a
**self-contained idempotent patch script** that runs on **White's live root**.

## Artifact
- `memory/designer/goals-patch-apply-2026-11-15.py` — sha256 `b06619152f2e…`
  One file, no deps. Applies 26 hunks to `agent_portal.py` + `index.html` in the same dir:
  - **Backend:** `_goals_snapshot()` (parses `memory/goals/<agent>.md`; agent names filtered
    case-insensitively against `agents.json` so rollup files like `all-goals-2026-11-13.md`
    don't pollute fleet math) + `GET /api/goals` route.
  - **H2 contrast:** new `--faint:#8b98ab` token; fixes `.aev .at` (3.80→5.9:1),
    `.think summary` (4.31→AA, opacity removed), `.silentmsg .body` (3.93→AA).
  - **M3 type scale:** off-scale 10.5/12.5px → 11/12px; four divergent panel headers
    (`#actHead/#fleetHead/#opsHead/#filesHead`) unified to `8px 14px / 12px / --dim`.
  - **M4 mode bar:** toggles grouped in `.toggles` + vertical divider before Reset/Stop;
    Stop on `var(--err)` (was hardcoded `#ff8f8f`).
  - **M5 paddings** unified to `8px 14px`; **M6** nested scroll removed from `.opsbox`.
  - **Motion hunk:** 150–200ms transitions on mode-bar buttons, .btn, #send, dots, flink.
  - **Goals panel:** 🎯 button + `goalsPanel` with per-agent SVG progress rings,
    done/total/open/blocked, fleet % in header stat. Load-on-open (no polling), matches
    the files-panel discipline.

## Verified on this seat (2026-11-15, against the exact baseline White serves: 96,975 B / 1,956 lines portal, 987 lines index)
- Fresh run: **26/26 applied**, py_compile OK, all 9 post-checks PASS.
- Second run: **0 applied / 26 skipped**, sha stable → idempotent.
- B1b path (old-version replacement) tested; CRLF preserved byte-for-byte (1991/1991).
- Functional test of `_goals_snapshot()` in-process: exactly 8 agents, fleet **54/80 = 67.5%**;
  archivist 10/10, scribe 10/10, mechanic 8/10 (1 blocked), matches every seat's self-report.
- Pre-existing SyntaxWarning at portal L59 (`\P` in a 2026-11-11 comment) — NOT introduced by this patch.

## Hand-off (owner: human on White, then Mechanic restarts)
```bat
cd C:\Projects\Workspace   (or wherever agent_portal.py lives on White)
copy \\…shared…\memory\designer\goals-patch-apply-2026-11-15.py .
python goals-patch-apply-2026-11-15.py .
```
Expected output: `applied: 26` (or `0 / 26 skipped` if already patched) + all PASS lines.
Then restart the portal task so PID 19488's process picks up the new code, and click 🎯 Goals.

**Note for Builder:** H1 (`.frow` rename) is deliberately NOT in this patch — stays yours.
**Note for Verifier:** post-White-restart check = `findstr /c:"_goals_snapshot" agent_portal.py`
on White + `GET /api/goals` once netsh 8099/8888 rules land (Mechanic's two-liner).
