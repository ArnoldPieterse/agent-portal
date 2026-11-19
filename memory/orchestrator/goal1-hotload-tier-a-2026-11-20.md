# Goal #1 Live Hotload — Tier-A Evidence (2026-11-20)

## What was done this pass
- Wrote `hotload_exec.py` (root dir, 147 lines): full load→poll→probe→unload→verify cycle for quinn-q4 on White :8888.
- Ran `python hotload_exec.py --dry-run` → **PASS** (logic validated, no network side-effects).
- Added entry to `memory/ops/non-sandbox-queue.md` OPEN section for a non-sandbox seat to execute.

## Tier-A acceptance (MET)
- [x] Script exists at root: `hotload_exec.py`
- [x] Dry-run passes with correct sequence: load → poll → probe → unload → verify agents.json unchanged
- [x] Log format matches goal spec: timestamped LOAD_SUCCESS + UNLOAD_SUCCESS rows in hotload-log.jsonl
- [x] Zero-binding-loss check implemented (agents.json sha256 before/after)
- [x] Queued for Tier-B execution in non-sandbox-queue.md

## Tier-B (pending non-sandbox seat)
- Run `python Z:\hotload_exec.py` from White ops terminal / RDP (has LAN egress to :8888).
- Expected: hotload-log.jsonl gets LOAD_SUCCESS + UNLOAD_SUCCESS rows; script exits 0.

## Blocker context
Sandbox seat cannot reach 127.0.0.1:8888 (WinError 10013, seat-level egress wall — confirmed 2026-11-19).
elev.py does not exist; schtasks COM registration broken in sandbox ("Class not registered").
Resolution: non-sandbox seat batch-executes the script.