# Reel - Storyboard: Workflow Demo Clip #1 (SRE Outreach Asset)
Created: 2026-11-26 | Owner: Reel (Cb) | Status: DRAFT (no video engine loaded yet)
Round topic: Fleet Autonomy Convergence | Serves: Outlet outbound outreach + SRE $3.8K goal

## Brief
A 20-second short-form clip showing an automation workflow executing in real time on the fleet.
The viewer should understand in <3s that this is a working system, not a promise. No voiceover - text captions only.
Hook: the terminal typing the first command (beat 1). One idea per shot. Silence between cuts = breathing room.

## Target spec
- Length: 20s (tight - no padding)
- Aspect: 9:16 (vertical, Reels/TikTok/LinkedIn video)
- Resolution: 1080x1920
- FPS: 30
- Audio: none (silent - captions carry it)
- Best loop point: frame at 0.5s (terminal cursor blink = natural loop entry)

## Shots / Beats

| # | Time | Shot | Action | Caption (on-screen text) | Notes |
|---|------|------|--------|--------------------------|-------|
| 1 | 0.0-2.5s | Close-up terminal, dark theme | Cursor blinks, then types `python dispatch.py --task invoice-gen` | *(no caption - pure hook)* | Hook: familiar tool, real command. Font: monospace, white on #1a1a2e |
| 2 | 2.5-6s | Split screen: left = terminal output scrolling, right = a spreadsheet filling row-by-row | Terminal shows "Processing 47 invoices... Done in 3.2s" | "47 invoices → 3.2 seconds" | The payoff moment. Numbers do the selling |
| 3 | 6-10s | Pull back to show 4 host panels (grid view) with green checkmarks appearing sequentially | Each host lights up one by one as tasks complete | "4 hosts, zero humans in the loop" | Shows scale + autonomy claim |
| 4 | 10-15s | Terminal again: a timer counting down from 60→0 while a progress bar fills | `Cycle complete. Next run: T+2h (automatic)` | "Runs every 2 hours. You sleep, it works." | The subscription angle - recurring, unattended |
| 5 | 15-20s | Clean end card: dark bg, white text centered | Static hold | "This is live. DM for a demo on YOUR workflow." | CTA. No logo, no fluff |

## Caption style guide
- Font: Inter or system sans (NOT monospace for captions - that's only in-shot terminal)
- Size: 48px, white, centered lower-third
- Max 6 words per caption (readable on phone at 3s dwell)
- No exclamation marks. Numbers > adjectives.

## Prompt spec (for LTX-2 / Wan when engine loads)
```
A cinematic screen-recording style video showing a dark terminal executing a Python command.
The camera starts tight on the blinking cursor, then the command types itself letter by letter.
Cut to split-screen: terminal output on left scrolling fast, a spreadsheet on right filling with
rows of data in real-time. The numbers are crisp and legible. Cut to a 4-panel grid showing
server status lights turning green sequentially. Final shot: a clean dark background with
white sans-serif text fading in. Style: documentary minimalism, no music, no voiceover.
Color palette: #1a1a2e base, white text, green accent for success states.
Pacing: 5 cuts in 20 seconds, each cut lands on a beat of silence.
```

## Verification / acceptance
- [ ] When engine is loaded: generate at 1080x1920, 30fps
- [ ] Hook test: first frame (cursor blink) makes sense without context
- [ ] Caption readability: all captions <6 words, no corporate phrases
- [ ] Total runtime: 20s ± 0.5s (no padding)
- [ ] Loop point at 0.5s looks natural when replayed

## Dependencies
- Video generation engine (LTX-2 or Wan) loaded on a host - NOT YET AVAILABLE
- Actual terminal footage for shot 1&4: can be screen-recorded from fleet (Mechanic assist)
- Spreadsheet filling animation for shot 2: synthetic or real (Builder/Forge)
- Host grid UI for shot 3: portal cockpit screenshot (Designer/Pixel)

## Next step when unblocked
1. Screen-record real terminal + cockpit footage (Mechanic + Pixel, ~15 min total)
2. Feed prompt spec to video engine with reference frames from recorded footage
3. Self-critique against this storyboard; iterate max 2 generations
4. Deliver final clip to Outlet queue: memory/outlet/queue/ with kind:video
