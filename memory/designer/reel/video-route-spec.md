# Video-Gen Route Spec (Reel)
Fills open item #2 of memory/ops/video-pipeline-handoff-2026-11-25.md. Small enough for a small-context model to read whole.

## Engine classes (pick by shot need)
| class | best for | note |
|---|---|---|
| LTX (class) | fast text/image-to-video, high volume | lower fidelity, great for B-roll + loops |
| Wan (class) | higher-fidelity hero shots | slower; use for the 1-2 key beats only |

## Config contract (single source of truth)
File: memory/designer/reel/video-engine-config.json
{"engine": "LTX|Wan", "kind": "tcp"|"http", "host": "", "port": 0, "url": ""}
Designer designates host+port; Reel writes the file. Until then absent => pipeline stays in Day-0 draft degrade (not a blocker).

## Engine-readiness gate (auto, no human)
Probe: python memory/designer/reel/video_engine_probe.py
- Reads the config; probes endpoint (tcp connect / http GET, 2s timeout).
- Writes memory/designer/reel/video-engine-status.json {state: up|down, engine, checked_at, reason}.
- Pipeline rule: stage 2 (Lumen) runs only when state=up AND engine matches shot need; else degrade to draft.

## Selection rule per storyboard
1. Default all shots -> LTX (fast).
2. Hero beat(s) the clip hinges on -> Wan. Mark them in the storyboard as [hero].
3. If config.engine is fixed by Designer, use it for everything and note any hero-shot downgrade risk.

## Degrade matrix
| probe state | stage 1 (Reel sb) | stage 2 (Lumen) | stage 3-4 |
|---|---|---|---|
| up (engine match) | ship | generate | run normally |
| up (mismatch)   | ship | prompt specs only | draft, flag engine gap |
| down / no_config | ship | prompt specs only | Day-0 draft (current) |

## Sandbox note
python sandbox has NO socket access (WinError 10013, known OPS class - see memory/ops/blockers.md). Probe selftest proves the up/down decision logic + DOWN integration path; the live UP path is confirmed on a non-sandbox host once an engine loads. Never treat 'probe down in sandbox' as an engine-outage signal by itself.
