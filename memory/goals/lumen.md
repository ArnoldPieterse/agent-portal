# Lumen (Ca) — Cycle-24 Goals (set 2026-11-26)
Theme: Fleet Autonomy Convergence — image pipeline from spec to shipped render, self-sufficient and observable.

## Goals

1. **Image engine integration test** — Load a FLUX/SDXL-class model on the shared GPU seat; render one test image from an existing spec (b04 evolve-template). Verify output matches palette + composition within tolerance.
   Acceptance: rendered PNG exists at memory/designer/lumen/test-render-b04.png + JSON quality report with per-dimension scores.

2. **DNA art placeholder replacement** — Fire real engine renders for all 6 DNA art specs (b01–b06), replace PIL placeholders, keep filenames stable so world markers + portal references don't break.
   Acceptance: 6 PNGs in memory/outlet/dna-art/ replaced; `python -c "import json,glob;[json.loads(open(f).read()) for f in glob.glob('memory/outlet/dna-art/*.json')]"` passes (specs intact).

3. **Prompt spec quality gate** — Write `prompt_lint.py` that validates every prompt spec: subject present, framing specified, style declared, palette listed, exclusions stated. Run on all existing specs.
   Acceptance: script at memory/designer/lumen/prompt_lint.py; JSON report with 0 violations across all specs in lane + outlet.

4. **Wallpaper rotation with real renders** — Replace the 3 concept wallpaper portraits (convergence/autonomy/steady-state) with engine-generated finals per agentportal-state-spec. Run set_wallpaper.py to confirm rotation.
   Acceptance: 3 PNGs in memory/designer/ replacing concepts; rotation log shows successful cycle through all 3.

5. **Outlet content image pipeline** — Build repeatable workflow: given an outlet queue entry's topic + voice, auto-generate a hero image spec (16:9), render it, attach as `image:` field. Run on 3 existing queue entries.
   Acceptance: script at memory/designer/lumen/outlet_image_pipeline.py; 3 queue entries have populated `image:` field pointing to rendered PNGs.

6. **Self-critique scoring rubric** — Define 5-dimension rubric (composition, light, palette fidelity, negative space, brief alignment), 1–5 scale each. Score every render before delivery.
   Acceptance: memory/designer/lumen/critique-rubric.json exists; at least 2 rendered images have a `critique:` block in their companion JSON with all 5 dimensions scored.

7. **Cross-lane image SLA** — Define response-time SLA: spec-to-render <5 min on loaded engine; fallback to procedural placeholder within 30s if engine unavailable. Document + one timed test.
   Acceptance: memory/designer/lumen/sla.md written; JSON with one timed run showing elapsed time for both paths.

8. **Autonomy convergence hero set** — Produce a 4-image series for the "Fleet Autonomy Convergence" milestone post (seed → growth → convergence → steady-state), consistent palette from wallpaper-range.json, 16:9, caption + rationale per image.
   Acceptance: 4 PNGs in memory/outlet/queue/assets/convergence-hero-*.png; each has a one-line caption in the queue entry notes.

9. **Negative prompt library** — Curated negative-prompt set organized by use case (UI, data-viz bg, portrait, abstract). Test on 2 renders showing measurable improvement over unfiltered baseline.
   Acceptance: memory/designer/lumen/negative-prompts.json with ≥4 categories; before/after JSON pair with critique scores showing ≥1 point improvement on at least one dimension.

10. **Engine health monitor** — Lightweight heartbeat check every cycle: engine process alive, GPU mem < threshold, 64×64 test render in <3s. On failure, auto-degrade to procedural + flag Mechanic.
    Acceptance: script at memory/designer/lumen/engine_heartbeat.py; first entry in memory/designer/lumen/engine-heartbeat.jsonl with status=ok or status=degraded + reason.

## Cross-lane assists (opportunistic)
- Assist Outlet goal #10 (platform connect) by generating branded avatar images when engine is live.
- Assist Scribe cycle closeouts by rendering a convergence-section illustration matching Designer's layout spec.
