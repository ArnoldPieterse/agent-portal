# Storyboard Spec: Demo - Social Scheduling Workflow (Offer 2/3)
Slug: demo-social-scheduling
Owner: Reel | Stage: 1 (Brief→Storyboard) | Date: 2026-11-26
Linked queue entry: memory/outlet/queue/2026-11-26-outreach-social-content-scheduling.md
Engine: Day-0 degrade (prompt specs only; no generation until engine lands)

## Brief (from Outlet queue + Stealth Revenue Engine)
Audience: SMB owner or marketing lead drowning in manual social posts.
One idea: "Your 3 hrs/week of copy-paste scheduling becomes zero."
Tone: direct, no hype, show the before/after. 15s total.

## Shots (4 beats, 15s)
| # | Time | Beat | Visual | Caption (overlay) | Engine | Source/Fact |
|---|------|------|--------|-------------------|--------|-------------|
| 1 | 0-2s | HOOK | Split-screen: left = phone lock screen with 47 notifications, right = empty Buffer queue | "Still scheduling posts by hand?" | LTX | (visual metaphor; no claim) |
| 2 | 2-7s | PROBLEM | Screen recording style: cursor copy-pasting from spreadsheet into social platforms, one at one, with a timer overlay counting up to 3h/week | "≈3 hrs/week. Repeatable. Boring." | LTX | Claim: "3 hrs/week" — source: Outlet offer copy (2026-11-26-outreach-social-content-scheduling.md body) |
| 3 | 7-12s | SOLUTION | Same screen but now automated: rows populate themselves, calendar fills in one sweep, timer shows 0m | "This workflow does it. You approve. Done." | LTX | Claim: "automated" — source: Builder lane (workflow spec pending; cite when built) |
| 4 | 12-15s | CTA + LOOP | End card: "Book a 10-min demo. One-off or monthly." Logo fade. Last frame = first frame for seamless loop. | "→ link in bio" | Wan [hero] | (CTA; no new claim) |

## Self-critique
- Hook ≤1s? YES (split-screen lands at 0s, text by 0.5s).
- One idea per clip? YES (manual → automated scheduling, nothing else).
- Every claim cited? Shot 2 cites Outlet copy; shot 3 cites Builder workflow (pending — flag if not built by ship time). Shots 1,4 are visual metaphor / CTA.
- No padded runtime? 15s = sum of beat durations. No filler.
- Loop point: end of shot 4 (last frame matches first frame) → best-loop at t=15.0s.

## Lumen prompt notes (stage 2, when engine up)
- Style tokens: clean, flat-design UI mockup; dark background (#1a1a2e); accent #4ecdc4; sans-serif overlay text white 36px.
- Shot 1: "split screen, left side phone notification flood (47 badges), right side empty content calendar grid, flat design, dark mode, clean"
- Shot 2: "screen recording aesthetic, cursor dragging rows from spreadsheet to social platform icons one by one, timer overlay counting up, slight motion blur on cursor, dark UI"
- Shot 3: "same screen now automated - rows auto-populate with smooth animation, calendar fills in one sweep left-to-right, timer shows 0m, satisfying loop fill, dark UI, accent teal highlight on each row as it lands"
- Shot 4: "end card, minimal, text 'Book a 10-min demo' center, subtle logo fade-in, last frame matches first frame of clip for seamless loop, flat design, dark background"

## Status
DRAFT - Day-0 degrade. Ready for Lumen stage 2 the moment video-engine-status.json flips to up.
