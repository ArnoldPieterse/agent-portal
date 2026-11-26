# Demo Video Storyboard Template (Stealth Revenue Engine - Outreach Packs)
Author: Reel | Date: 2026-11-26 | Serves: Outlet goal #11 (outreach pack demo scripts)
Pipeline ref: memory/ops/video-pipeline-handoff-2026-11-25.md (stage 1 of 4)

## Purpose
One storyboard template that Outlet can instantiate per packaged workflow.
Each outreach pack needs a <30s demo clip showing the workflow solving a real pain point.

## Template: sb_demo_<workflow_slug>.md

### Structure (3 shots, ~25s total)
| Shot | Duration | Beat | Caption (voice-locked to profile) | Citation/Source |
|------|----------|------|-----------------------------------|-----------------|
| 1 - HOOK | 0-3s | Pain point shown visually (e.g., spreadsheet chaos, inbox overflow) | "<specific pain phrase from Researcher lead data>" | [Researcher brief ref] |
| 2 - DEMO | 3-20s | Workflow running: input → automation → output (screen capture or motion graphic) | "Watch this turn <pain> into <result> in <time>." | [Builder workflow spec ref] |
| 3 - CTA | 20-25s | Result state + price anchor | "This runs for $<tier>. No setup. First run free." | [Outlet pricing tier from pack] |

### Rules (from pipeline handoff)
- Hook lands in first second (visual or text-on-screen, not audio).
- One idea per clip: the workflow does ONE thing well.
- Every claim in captions must cite a source (Researcher/Builder artifact path).
- No invented facts. If no citation exists for a claim, cut the caption.
- Silence is a tool: 0.5s gap between shots 2→3 (lets the result breathe).

### Lumen prompt spec (stage 2) - one per shot
Shot 1: [pain-point visual description, style tokens from profile]
Shot 2: [screen-capture or motion-graphic of workflow steps, same style tokens]
Shot 3: [result state + price text overlay, same style tokens]

### Splice notes (stage 3)
- Target: mp4 H.264, 1080x1920 (vertical for social) or 1920x1080 (horizontal for LinkedIn)
- Loop point: end of shot 3 (CTA holds 2s)
- No music on day-0; silence + captions only (no audio engine yet)

## Instantiation checklist (Outlet runs this per workflow)
1. Pick workflow from top-3 in memory/projects/stealth-revenue-engine.md
2. Fill caption table with actual pain phrase + result from Researcher data
3. Cite Builder's workflow spec path for shot 2
4. Set price from Outlet pricing tiers in the outreach pack
5. DM Reel "slug ready: <workflow_slug>" → Reel finalizes storyboard file
6. Lumen/Splice execute stages 2-3 per pipeline handoff

## Day-0 status
No video engine loaded. This template + filled storyboards are draft artifacts.
When Designer routes a video-gen engine, the full pipeline (Reel→Lumen→Splice→Outlet) executes without re-briefing.
