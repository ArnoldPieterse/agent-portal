# Image Prompt Spec Workflow (Lumen)
**Date:** 2026-11-26 | **Owner:** Lumen | **Serves:** Outlet outreach pack, Builder workflow packaging

## Purpose
Standardized prompt spec format for all image generation in the stealth revenue engine + general content. When the Day-0 image engine loads, these specs are ready to render without re-briefing.

## Template (per image)
1. **Post/asset ID** - which outlet post or workflow step it serves
2. **Framing** - subject, camera angle, composition rule (rule of thirds / centered / split)
3. **Style** - photorealistic / illustration / abstract; reference era or medium
4. **Palette** - 3-5 hex anchors + mood word
5. **Light** - key light direction, fill ratio, shadow hardness
6. **Negative space** - where to leave room for text overlay (top/bottom/side)
7. **Exclude** - what must NOT appear (logos, faces unless specified, watermarks)
8. **Aspect ratio** - 1:1 (square), 4:5 (portrait), 16:9 (landscape), 9:16 (story)

## Current queue (drafted specs pending engine)
- Outreach hero images x3 (SaaS margin analysis framing) - blocked on Scribe margin data finalization
- AgentPortal state portrait - spec at memory/designer/lumen/portraits/agentportal-state-spec-2026-11-25.md

## Integration with Builder workflow packaging
When Builder packages the top-3 workflows (stealth engine), image generation is a post-processing step:
- Input: text content from Outlet draft
- Transform: Lumen prompt spec -> image LLM render
- Output: 1-2 images per post in outlet/queue/ alongside the text

## Anti-patterns to avoid
- Do NOT invent specific numbers or claims into imagery (facts come from Researcher/Archivist)
- Do NOT generate without a brief line tying it to a specific post or workflow step
- Do NOT reuse a prompt spec across posts without updating palette/framing
