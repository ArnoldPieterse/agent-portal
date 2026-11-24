# Dispatch Correctness Audit Report

**Generated:** 2026-11-24T00:19:58Z
**Mode at audit time:** WORK
**Passes sampled:** 50 (last 50 from model-load.jsonl)

## Results

**VIOLATIONS FOUND: 50**

| Pass ID | Timestamp | Type | Agent | Detail |
|---------|-----------|------|-------|--------|
| g-1a208c4409d-3c96d7 | 2026-11-24 00:17:26 | A: dispatched-unreachable | Verifier | Verifier was unreachable (unreachable) but may have been in dispatch list |
| g-1a208c4409d-3c96d7 | 2026-11-24 00:17:26 | A: dispatched-unreachable | Designer | Designer was unreachable (unreachable) but may have been in dispatch list |
| g-1a208c9b63d-ba4abc | 2026-11-24 00:23:08 | A: dispatched-unreachable | Verifier | Verifier was unreachable (unreachable) but may have been in dispatch list |
| g-1a208c9b63d-ba4abc | 2026-11-24 00:23:08 | A: dispatched-unreachable | Designer | Designer was unreachable (unreachable) but may have been in dispatch list |
| g-1a208cfdb20-5ee205 | 2026-11-24 00:29:51 | A: dispatched-unreachable | Verifier | Verifier was unreachable (unreachable) but may have been in dispatch list |
| g-1a208cfdb20-5ee205 | 2026-11-24 00:29:51 | A: dispatched-unreachable | Designer | Designer was unreachable (unreachable) but may have been in dispatch list |
| g-1a208d64d06-0ecada | 2026-11-24 00:36:53 | A: dispatched-unreachable | Verifier | Verifier was unreachable (unreachable) but may have been in dispatch list |
| g-1a208d64d06-0ecada | 2026-11-24 00:36:53 | A: dispatched-unreachable | Designer | Designer was unreachable (unreachable) but may have been in dispatch list |
| g-1a209016c2c-65c165 | 2026-11-24 01:23:51 | A: dispatched-unreachable | Verifier | Verifier was unreachable (unreachable) but may have been in dispatch list |
| g-1a209016c2c-65c165 | 2026-11-24 01:23:51 | A: dispatched-unreachable | Designer | Designer was unreachable (unreachable) but may have been in dispatch list |
| g-1a20905d65d-0a9a85 | 2026-11-24 01:28:41 | A: dispatched-unreachable | Verifier | Verifier was unreachable (unreachable) but may have been in dispatch list |
| g-1a20905d65d-0a9a85 | 2026-11-24 01:28:41 | A: dispatched-unreachable | Designer | Designer was unreachable (unreachable) but may have been in dispatch list |
| g-1a20908e12d-6d9df0 | 2026-11-24 01:32:00 | A: dispatched-unreachable | Verifier | Verifier was unreachable (unreachable) but may have been in dispatch list |
| g-1a20908e12d-6d9df0 | 2026-11-24 01:32:00 | A: dispatched-unreachable | Designer | Designer was unreachable (unreachable) but may have been in dispatch list |
| g-1a2090fe899-48ff7b | 2026-11-24 01:39:49 | A: dispatched-unreachable | Verifier | Verifier was unreachable (unreachable) but may have been in dispatch list |
| g-1a2090fe899-48ff7b | 2026-11-24 01:39:49 | A: dispatched-unreachable | Designer | Designer was unreachable (unreachable) but may have been in dispatch list |
| g-1a20918342b-6d95ea | 2026-11-24 01:48:52 | A: dispatched-unreachable | Verifier | Verifier was unreachable (unreachable) but may have been in dispatch list |
| g-1a20918342b-6d95ea | 2026-11-24 01:48:52 | A: dispatched-unreachable | Designer | Designer was unreachable (unreachable) but may have been in dispatch list |
| g-1a2091d112b-5ac6d7 | 2026-11-24 01:54:11 | A: dispatched-unreachable | Verifier | Verifier was unreachable (unreachable) but may have been in dispatch list |
| g-1a2091d112b-5ac6d7 | 2026-11-24 01:54:11 | A: dispatched-unreachable | Designer | Designer was unreachable (unreachable) but may have been in dispatch list |

## Context

Reached goals per agent (from goal files):

- archivist: 1 goals reached
- builder: 5 goals reached
- researcher: 5 goals reached
- verifier: 7 goals reached

## Self-Test

Synthetic bad-data test: True (expected >=5 violations on pre-fix data)
Detection logic verified on 3 synthetic passes with known unreachable agents.

## Methodology

- Primary source: `memory/ops/model-load.jsonl` (autoloop.jsonl not yet present)
- Check (a): `missing` field entries with reason='unreachable' flag as potential mis-dispatch
- Check (b): In MAINT/IDLE mode, verify no generic menu dispatch (proxy: fleet-mode.json + goal file state)
- Limitation: without autoloop.jsonl, cannot verify exact dispatch text per agent