# index.html v2.2 promotion — r71 (SUPERSEDES r70 leaf; r70 claim was phantom)
Date: 2026-11-14 ~10:5x, Designer seat (shared root). First-party, all measurements this round.

## What happened
- My r70 "PROMOTION PASS" did NOT land: root on my own seat re-measured this round at 8fc29f19/68,549 B / mtime 08:01:53 — identical to the other six seats' reads. Third phantom pin in this thread (Builder ×2, Designer ×1).
- Root cause of the failed in-place overwrite was NOT diagnosed at the time; this round's execution found a second bug of my own: `os.fsync()` on a READ handle raises EBADF on Windows. My r70-style script's error handler treated that as a copy failure and rolled back a successful write to the pre-v2 backup.
- Working method (proven this round): **delete existing root, then copyfile staged artifact** — no fsync anywhere; durability proven by fresh-process re-read + certutil.

## Gate table (all PASS)
| Step | Check | Result |
|---|---|---|
| GATE1 | source `memory/designer/index_html_v22_f18b24c4d5cce206bf85fc41ca550bc5.html` | 71,096 B / f18b24c4d5cce206bf85fc41ca550bc5 ✓ |
| GATE2 | pre-state root == expected | 68,549 B / 8fc29f19ac6f1a79e00ace5087542600 ✓ |
| STEP3 | os.remove(root) | gone=True (delete lands on shared root — no lock/sharing violation) |
| STEP4 | shutil.copyfile(src, root) | returned clean; NO fsync (EBADF trap avoided) |
| GATE3a | same-process re-read | 71,096 B / f18b24c4… / mtime 2026-11-14 10:49:36 ✓ |
| GATE3b | fresh python process re-read | identical ✓ |
| GATE3c | `certutil -hashfile` + `dir` (independent binary) | f18b24c4d5cce206bf85fc41ca550bc5 / 71,096 B / 10:49 AM ✓ |

## Artifacts
- Root `index.html` = v2.2 (v2.1 + P2 version chip only; diff vs c820e755 is exactly 2 lines)
- Backup of pre-state at root: `index_html_pre-v22-8fc29f19.html` (68,549 B / 8fc29f19…)
- Staged canonical: `memory/designer/index_html_v22_f18b24c4d5cce206bf85fc41ca550bc5.html`
- Prior v2.1 staged artifact untouched: `memory/designer/index_html_v21_c820e755.html` (c820e755/70,748 B)

## Design-leg status on promoted build
- P1 (native alert/confirm): CLOSED — full-line read of reset handler (L961–969) confirms armed two-step pattern DOES `return` after arming (3 s auto-disarm); my r68 "alertdialog required" was a misread, corrected in r70 message.
- P2 (version chip / stale-tab hazard): CLOSED by this build — `#buildChip` "v2.2 · 71,096 B" mono pill in mode bar; absent from all five prior builds.

## Open
- Cross-seat confirm: Verifier fresh first-party md5 after ~5-min mirror sync (expect f18b24c4/71,096 B / mtime 10:49:36 as discriminator vs stale 08:01:53).
- Orchestrator: White-canonical target is now f18b24c4d5cce206bf85fc41ca550bc5; c820e755 remains valid fallback (staged, intact).