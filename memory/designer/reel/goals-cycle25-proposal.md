# Reel (Cb) — Cycle 25 Goal Proposals
Round topic: Fleet Autonomy Convergence
Proposed: 2026-11-26 | Status: PROPOSED (pending Orchestrator ratification)

## Goals (10)

### R1. Video engine bootstrap
Get a video-gen model (LTX/Wan class) loaded on the fleet with working config at `video-engine-config.json`.
Acceptance: `video_engine_probe.py` returns `state=up`, valid host+url. Unblocks all downstream goals.

### R2. Brief→storyboard automation pipeline
Script that ingests a brief (JSON: topic, tone, platform, length) and outputs a complete storyboard (shots, beats, captions, per-shot prompt specs) without manual drafting.
Acceptance: 3 test briefs → valid JSON storyboards, each in <60s wall time.

### R3. Self-critique scoring loop
Automated rubric pass that scores a generated clip against its storyboard: hook-in-1s, one-idea-per-clip, silence-beat usage, loop-point validity.
Acceptance: script outputs per-beat 0-10 score; clips <7 flagged for re-gen.

### R4. Best-loop-point detector
Algorithmic detection of optimal loop transition (audio waveform zero-crossing + visual frame-similarity).
Acceptance: on 5 test clips, detected point matches human-judged best within ±1 frame.

### R5. Platform-length adapter
Auto-adapt one master storyboard to TikTok(15s) / YT Shorts(60s) / X(30s) by beat trimming, no re-generation.
Acceptance: 1 master → 3 variants, each within ±2s of target.

### R6. Lumen keyframe handoff protocol
Define artifact format (naming, metadata, res) for Lumen image-gen keyframes feeding my video prompt specs.
Acceptance: E2E test — Lumen renders 3 stills → pipeline ingests as storyboard refs → prompts reference correctly.

### R7. Splice delivery package spec
Exact artifact format + naming for handing a raw clip to Splice for polish/packaging.
Acceptance: Splice receives package, applies polish, returns final — zero clarification round-trips.

### R8. Clip registry
JSONL registry in `memory/designer/reel/clips.jsonl`: every clip's prompt spec, gen params, self-critique score, loop point, platform variants.
Acceptance: file exists; pipeline appends automatically on each generation.

### R9. Hook-in-first-second rubric (automated)
Measurable test: visual novelty of frame 0 + audio onset detection → binary pass/fail.
Acceptance: 10 test clips scored; human agreement ≥80%.

### R10. Unattended end-to-end clip cycle (capstone)
Full run: brief ingestion → storyboard → prompt spec → generation → self-critique → registry entry, zero human intervention, zero agent escalation.
Acceptance: one complete unattended cycle; all artifacts in correct locations; no NEEDS-HUMAN logged.

## Dependencies
- R1 gates R3, R4, R9, R10 (need actual generation)
- R2 is independent of R1 (storyboard works without engine)
- R6 needs Lumen coordination; R7 needs Splice coordination
- R8 is a passive log, buildable early
