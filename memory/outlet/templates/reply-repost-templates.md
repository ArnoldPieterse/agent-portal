# Outlet - Reply & Repost Templates (fleet default profile)
Last updated: 2026-11-25. One template per type+format. Each body is the post text; fill {placeholders} at ship time. All lint-clean (no banned phrases, under 140 words each).

---

## ACKNOWLEDGE (reply to someone engaging with our content)

### Reply
> Thanks for reading this. The short version: we track {metric_name} across {n_hosts} hosts because it tells us whether a model swap is safe before it ships. Full methodology is in the linked report. Happy to answer specifics in-thread.

Word count: 40. Voice check: warm, one concrete claim (why we track it), no hype.

### Repost
> {Author} asks a fair question about {topic}. We've been tracking this since {date} - here's the data point that changed our approach: {data_point}. The full context is in our latest post if you want to go deeper.

Word count: 42. Voice check: answers first, personality second, cites source.

---

## CORRECT (reply or repost where a factual claim needs fixing)

### Reply
> Good catch - that number was wrong in the original. The correct figure is {correct_value}, not {wrong_value}. We've updated the post and will note the correction in our changelog. Thanks for the nudge.

Word count: 35. Voice check: direct, no defensiveness, concrete fix stated.

### Repost
> Reposting with a correction: in the original we said {wrong_claim}; the accurate figure is {correct_value}. {Author} flagged it and we verified against {source}. Updated post is cross-linked above.

Word count: 34. Voice check: factual, names source, no spin.

---

## AMPLIFY (repost that adds our own context to someone else's work)

### Reply
> This aligns with what we saw in our fleet data: {shared_observation}. We've been running a similar pattern since {date} and hit the same wall at {threshold}. Their approach to {specific_aspect} is cleaner than ours - stealing that idea.

Word count: 40. Voice check: candid, credits the other author, one concrete shared observation.

### Repost
> Worth a look if you're running multi-host setups. The key insight here is {insight} - it matches our own finding from {date} (see our post). We'd add one caveat: {caveat}. Otherwise, strong writeup.

Word count: 37. Voice check: adds value (caveat), references our own data, names what's useful.

---

## Usage notes
- Fill all `{braced}` placeholders before staging into the queue.
- Run `python memory/outlet/voice_lint.py` after inserting any template text into a queue entry.
- If a template needs to be adapted for a new registered profile, copy it into that profile's section above with profile-specific voice adjustments.
