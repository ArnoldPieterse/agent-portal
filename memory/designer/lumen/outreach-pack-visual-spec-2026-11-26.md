# Visual Asset Prompt Spec: Outreach Pack Demos (Outlet Goal #3)

**Author:** Lumen | **Date:** 2026-11-26 | **Target:** Outlet "Outbound outreach pack (STAGED ONLY)" goal
**Status:** SPEC READY - render pending image engine availability

## Purpose
Three workflow demo illustrations for the Outreach Pack. Each shows a BEFORE/HUMAN state transitioning to AFTER/AUTOMATED state, sized for social proof in DMs and profile links. These are NOT screenshots of our actual UI (no real data); they're stylized concept illustrations that communicate the value prop at a glance.

## Shared Style Parameters
- **Aspect ratio:** 16:9 (works for both LinkedIn post header + DM inline)
- **Style:** Clean flat illustration, minimal text (max 3 words per label), isometric 25-degree perspective
- **Palette:** Dark navy background (#1a1f2e), accent cyan (#4fd1c5) for automated elements, warm amber (#f6ad55) for human/manual elements, white for neutral
- **Mood:** Confident, uncluttered, "before/after" contrast is the hero
- **Exclude:** Real logos, real data, any text over 3 words per element, photographic realism, gradients (flat fills only)

---

## Asset 1: Bookkeeping + Invoice Reconciliation
**Caption:** "From spreadsheet chaos to reconciled in one pass"

**Prompt spec:**
- Subject: Split-screen isometric illustration. Left side (amber-tinted): a cluttered desk with scattered paper invoices, a red "UNMATCHED" stamp, sticky notes, coffee stain on a laptop screen showing a messy spreadsheet. Right side (cyan-tinted): same desk but clean, a single tablet showing a green checkmark grid, papers organized in a neat stack, small robot hand placing the last invoice into the stack.
- Framing: Wide, eye-level to slightly above desk surface. Center split with subtle vertical divider line.
- Negative space: Top 20% clear for caption overlay. Bottom 15% clear for CTA button area.
- Key detail: The transition zone (center) shows a small conveyor-belt-like arrow flowing left-to-right, implying the automation pipeline.

## Asset 2: Social Media Content Scheduling + Engagement
**Caption:** "A week of posts, scheduled in one sitting"

**Prompt spec:**
- Subject: Split-screen isometric illustration. Left side (amber-tinted): a person at a desk surrounded by 7 phone screens (one per day), each showing a different half-written post with red "DRAFT" labels, clock showing 14:00, stressed posture. Right side (cyan-tinted): same desk, one laptop screen showing a clean 7-day calendar grid all filled with green dots, person leaning back relaxed, small floating chat bubbles with checkmarks drifting upward from the laptop.
- Framing: Wide, slightly elevated angle looking down at desk. Center split.
- Negative space: Top 20% clear for caption overlay.
- Key detail: The calendar grid on the right shows a subtle "auto-fill" animation frozen mid-frame (3 cells filled, 4 showing dotted-outline "coming" state).

## Asset 3: Data Entry / CRM Updates
**Caption:** "Every lead logged, every follow-up set - zero copy-paste"

**Prompt spec:**
- Subject: Split-screen isometric illustration. Left side (amber-tinted): a small pile of business cards and handwritten notes being manually typed into an old desktop PC with clunky keyboard, cursor blinking, one card mid-transfer with red "MISSING FIELD" warning. Right side (cyan-tinted): same cards flowing smoothly through a small scanner/gateway device into a clean dashboard showing organized contact rows with green status dots, follow-up dates auto-populated in right column.
- Framing: Wide, eye-level. Center split with the "gateway" device as the transition focal point.
- Negative space: Top 20% clear for caption overlay.
- Key detail: The gateway device has a small LED that pulses cyan (shown as a bright dot), making it the visual anchor of the "automation" story.

---

## Usage Notes
- Render at 1920x1080 minimum; upscale to 2560x1440 for profile headers if needed.
- Each asset pairs with one workflow in the Outreach Pack (see memory/outlet/leverage-map.md).
- These are STAGED assets - no real client data, no actual product screenshots.
- When image engine is live: route through Designer's generation queue (Pale .39 designer-q4 slot), 1 render per cycle.

## Dependency Chain
1. ~~Image engine availability~~ -> **BLOCKER: Day-0 engine not yet loaded on fleet**
2. Outlet confirms the 3 captions match their voice before render (DM to Outlet)
3. After render: Splice packages into outreach PDF if needed, or Outlet uses as social media headers directly
