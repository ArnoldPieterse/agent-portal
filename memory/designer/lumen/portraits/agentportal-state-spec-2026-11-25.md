# agentportal-state portrait - prompt spec (Lumen, 2026-11-25)
<!-- lane: memory/designer/lumen/ | execution arm: Studio assistant (no image engine resident yet - Day-0 goal open) -->

## Status
SPEC READY / RENDER PENDING. No image-generation model is loaded on any fleet host
(verified 2026-11-25: white/pale/black/red all text-only; LTX-2.5 hub-only on white, ~14GB,
disk at 90.7%). Procedural concept renders shipped as placeholders in ./portraits/ until the
Day-0 engine lands; then re-run this spec verbatim and swap the wallpaper range.

## Prompt (HiRes, FLUX/SDXL class)
A vast dark observatory interior seen from a low angle: four massive luminous pillars stand in a
square - one warm white, one pale blue-grey, one deep black edged in silver, one muted red - each
pillar wrapped in slowly orbiting rings of fine golden light like gyroscopes. Between the pillars,
a web of thin glowing filaments connects them in pairs, some filaments thicker than others, a few
pulsing with slow data-light. At the exact center floats a translucent cockpit ring, concentric and
precise, with tiny bright nodes arranged along it like agents in formation, and a soft white core
of light where all filaments converge. The floor is polished dark stone reflecting the pillars;
dust motes drift in the light beams. Mood: calm, engineered wonder - a machine that thinks about
itself. Palette: near-black navy base, warm white, pale blue-grey, muted red, antique gold accents.
Style: cinematic 3D render, volumetric lighting, shallow depth of field at the edges, ultra-detailed,
high resolution wallpaper composition with negative space in the upper third for a title.

## Artistic flow control
- guidance/cfg: 3.5 (flow over rigidity - let the light breathe; raise to 6 only if composition scatters)
- steps: 40 | sampler: euler-bench (FLUX) or DPM++ 2M Karras (SDXL)
- resolution: 1920x1080 base, upscale x1.5 with a HiRes-fix pass (denoise 0.35) to ~2880x1620 for wallpaper
- seed: record the winner; negative: "text, watermark, people, hands, cluttered foreground"

## Caption + rationale (persona format)
Caption: "The four hosts hold the light steady while the fleet learns its own shape."
Rationale: one image must say what changed this cycle - 72 API calls, device+login manifests, and a
UI that now renders from the process layer instead of carrying it.

## Swap procedure (when engine lands)
1. Load FLUX/SDXL on any host (dual-GPU request via POST /api/gpu/request if >30GB).
2. Generate 3 variants (seeds +-1) from the prompt above; self-critique each against the caption.
3. Copy winners to memory/designer/lumen/portraits/ (overwrite placeholders, keep .concept.png names distinct).
4. Update memory/designer/wallpaper-range.json entries + run set_wallpaper.py <file> for the new lead.
