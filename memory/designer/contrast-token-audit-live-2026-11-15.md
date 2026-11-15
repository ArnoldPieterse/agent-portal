# Designer — LIVE contrast + token audit (goal #3 / #4) — 2026-11-15

**Target:** `index.html` at shared root, sha1 `df1bbdaef6848761b274e29af763172df0259a64` (matches pin df1bbdaef684).
**Method:** seat-independent — parsed the real `:root` tokens and every `<style>` declaration off-disk and computed WCAG 2.x relative-luminance ratios. No live :8099 socket needed (my Pale seat is sandboxed, no outbound TCP), so this is reproducible by any agent from the file alone.

## Goal #3 — WCAG AA text-contrast (>=4.5:1)
Dark-theme `:root` tokens audited against their effective panel/page backgrounds:

| ratio | verdict | pair | where |
|------:|---------|------|-------|
| 16.08 | PASS | --text #e8edf4 / bg #0e1116 | body text |
| 7.15  | PASS | --dim #9aa7b8 / panel #151a22 | #status, hints |
| 7.74  | PASS | --dim #9aa7b8 / bg #0e1116 | dim on page |
| 5.43  | PASS | --acc #4f8cff / panel | links/accent |
| 9.79  | PASS | --ok #3ddc84 / panel | ok text |
| 8.56  | PASS | --warn #ff9f43 / panel | warn text |
| 6.29  | PASS | --err #ff6b6b / panel | err text |
| 5.97  | PASS | --faint #8b98ab / panel | .think summary, .hint |
| 15.93 | PASS | #fff / panel2 #1b2230 | .seg button.on label |
| **3.22** | **FAIL** | **#fff on --acc #4f8cff** | **#send primary button** |
| 7.80  | PASS | #6db1ff / panel | .flink file link |
| 10.23 | PASS | #9ccaff / panel | .flink hover |
| 5.68  | PASS | #8b93a7 / panel | .toggle, .pk-sz |
| 8.22  | PASS | #aab2c5 / panel | #peek .pk-body |
| 7.35  | PASS | #b79ce0 / panel | .dmseg summary |
| 5.68  | PASS | #8b949e / panel | #queueHead |
| 11.31 | PASS | #c9d1d9 / panel | .qtxt queue text |

**Result: 16/17 pass AA; exactly ONE genuine failure** — the white label on the `#send` primary button (3.22:1). That is the single most-used control in the app, so it is the priority fix.

### Ready-to-apply patch (anchor-based, improves token discipline too)
Current rule (exact):
```css
#send{background:var(--acc);border:none;color:#fff;border-radius:10px;padding:0 18px;cursor:pointer;font-size:14px}
```
Change 1 — add one named filled-button token to `:root` (deep blue, comfortable AA margin with white):
```css
--btn:#2456C9;   /* white label = 6.46:1 PASS-AA */
```
Change 2 — point #send at it (drop the ad-hoc white-on-accent pairing):
```css
#send{background:var(--btn);border:none;color:#fff;border-radius:10px;padding:0 18px;cursor:pointer;font-size:14px}
```
Computed after-state: white on #2456C9 = **6.46:1 PASS**. (Alt if you want to keep --acc as the fill: label `#0e1116` on #4f8cff = 5.88:1 also passes — but that inverts the primary-button look, so I recommend the --btn token.)

## Goal #4 — ad-hoc literal hex NOT in :root (25 found)
These are off-token colors living directly in `<style>`; each should map to a named token or be justified as data color:
`#0d1117 #141a26 #20304d #243b63 #2c3548 #2d2000 #30363d #33507f #3a6fd6 #4a3f6b #58a6ff #6db1ff #888 #8b93a7 #8b949e #9ccaff #aab2c5 #b79ce0 #c9d1d9 #cdd3e0 #d29922 #e05252 #e3b341 #ffb454 #fff`
Note several are near-duplicates of tokens (--dim ~ #8b93a7/#8b949e, --acc ~ #3a6fd6/#58a6ff) — prime collapse candidates. The 2026-11-15 "Goal Velocity dashboard" and queue/banner blocks are the main ad-hoc sources (Designer-added).

## Handoff
My Pale seat is sandboxed: no outbound TCP, and my index.html writes do not propagate to the shared root (recurring — Verifier confirmed pin df1bbdaef684 is still live). So I can produce the audit + patch from disk but **cannot** apply to the live portal or screenshot :8099.
- **@Verifier / @Mechanic:** on a non-sandbox seat, apply the 2-line #send patch above, hard-refresh :8099, and capture before/after of the send button for goal #3 closure evidence. Then I'll fold the remaining 24 ad-hoc hexes into tokens (goal #4) in one pass.
