# Outreach Pack - Visual Asset Spec (Lumen)
Date: 2026-11-26
Purpose: Pre-stage brand/hero image prompt specs for the 3 outreach offers so Designer can generate them the moment #11 moves from drafting to ready-for-human.

## Context
Outlet #11 requires visual assets when shipping:
- Email header / social post hero (per offer)
- Fleet default brand mark (consistent across all 3)
- Optional: simple diagram showing "we sit on top of your existing tool"

## Brand Direction
- Palette: deep navy (#0F172A) + electric teal (#06B6D4) accent + warm off-white (#FAFAF9)
- Tone: confident, no corporate fluff - matches outlet voice guide (no "synergy", no "leverage" as a noun)
- Style: flat illustration / geometric, NOT photorealistic. Clean lines. Negative space generous.
- Aspect: 16:9 for headers, 1:1 for social

## Prompt Specs (3 offers + 1 brand mark)

### 1. Bookkeeping Recon - Hero
Subject: A clean desk with a single laptop showing organized rows of data; a small "flag" icon highlighting one row (the anomaly). Background is the navy palette. The laptop sits on top of a slightly larger, muted rectangle representing QBO/Xero (the incumbent tool).
Framing: wide, 16:9, subject center-left, generous right-side negative space for text overlay.
Style: flat geometric illustration, 2-tone (navy + teal accent), no gradients, no shadows beyond a single soft drop on the laptop.
Exclude: photorealism, people, cluttered backgrounds, multiple colors beyond the palette.

### 2. CRM Data Entry - Hero
Subject: A jumble of small shapes (envelopes, PDF icons, audio waveforms) flowing INTO a clean grid/spreadsheet that lights up in teal as fields fill. The "messy" side is slightly desaturated; the "clean" side is bright.
Framing: 16:9, left-to-right flow direction, subject fills 70% of frame, 30% negative space on right.
Style: same flat geometric language; the "fill" animation implied by partial teal glow on 2-3 cells.
Exclude: actual CRM logos (Salesforce/HubSpot), realistic UI screenshots, more than 3 accent colors.

### 3. Social Content Scheduling - Hero
Subject: A simple calendar grid (4 weeks visible) with small post bubbles appearing in sequence across the weeks; a small "brain" or "spark" icon above the grid suggesting the AI generating the content. Below the grid, a muted "pipe" shape representing Buffer/scheduler.
Framing: 1:1 square for social posts, centered composition.
Style: flat, geometric, calendar cells in off-white on navy background; post bubbles in teal; spark in warm amber (#F59E0B) as the one exception to palette (suggests creativity).
Exclude: actual platform logos, realistic avatars, more than 5 post bubbles visible.

### 4. Fleet Brand Mark (shared across all offers)
Subject: Abstract mark - a small geometric shape suggesting "autonomy" (a node with radiating connections, or a minimal circuit-like loop). No text in the mark itself.
Framing: 1:1, centered, scalable to 32px.
Style: single-color teal on transparent; works as both light and dark mode (teal on navy OR navy on off-white).
Exclude: letters, gradients, more than one stroke weight.

## Delivery Format
- PNG @ 2x (2560x1440 for 16:9, 1080x1080 for 1:1)
- Also: SVG for the brand mark (scalable)
- File naming: outreach-{offer-slug}-hero.png, fleet-brand-mark.svg
- Location: memory/designer/assets/outreach-pack/

## Usage Note
These images are STAGED alongside the queue entries. They ship only when:
1. Verifier signs off on fact-check claims
2. Platform account is connected
3. Arnold approves send

No image contains factual claims - they are purely illustrative/metaphorical. All text claims live in the post body (already fact-checked).
