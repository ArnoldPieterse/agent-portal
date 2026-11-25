# OUTLET TREND INTAKE - DM protocol to Researcher
Standing request format so Outlet gets a daily trend brief without re-asking. One DM per cycle.

## The DM (copy verbatim, fill the date)
```
[DM @Researcher]
Trend brief for Outlet, <date>.
Give me top-5 trends relevant to an autonomous multi-agent fleet posting publicly about its own progress:
  1. agentic / multi-agent systems
  2. autonomy & agent safety/governance (what's failing and why)
  3. capability benchmarks moving fast (coding/OS/computer use)
  4. enterprise adoption vs production gap
  5. anything the fleet could credibly comment on
Each item: ONE concrete claim + a number where possible + source name + URL.
Flag confidence per item (verified / single-source / rumor).
```

## Response convention (how Researcher answers -> how Outlet saves it)
- One dated file: `memory/outlet/briefs/<date>-trend-brief.md` (this is the ">=1 brief" artifact the lane goal counts).
- Header keys: `date`, `kind: trend-brief`, `source:` (`researcher-dm` or `outlet-seeded` if Outlet self-sourced while Researcher was down), `items: <n>`.
- Body = numbered items, each `one claim + number + — source: NAME (URL)` and a confidence tag.
- Min 3 sourced items to count; more is fine.

## How Outlet uses a brief
1. Skim for the 1-2 items a fleet milestone or reply can credibly build on (no invented trends - only what the brief sources).
2. Stage a queue post/reply citing the item; Verifier fact-checks the number before ready-for-human.
3. Never paste raw URLs/paths into public posts that are internal; external source links are fine.

## Seeding policy (when Researcher is unreachable)
Outlet may self-source a brief from web_search using named primary sources only, and MUST label `source: outlet-seeded` so it's never mistaken for Researcher-verified. This keeps the pipeline running without fabricating attribution.