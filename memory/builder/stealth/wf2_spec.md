# WF2: Social Media Content Scheduler
## Input -> Output
- **Input**: `content_brief.json` — {brand_voice, topics[], platforms[], frequency}
- **Output**:
  - `scheduled_posts.json` — platform-specific posts with timestamps
  - `calendar.csv` — flat calendar view (date, platform, post_text, hashtags)
  - `engagement_plan.md` — suggested engagement actions per post

## Runbook
```bash
python memory/builder/stealth/wf2_content_scheduler.py --brief sample_brief.json --output ./wf2_out/
```

## Cost Model (per run)
- Runtime: <1s for 30 posts (template-based, no API calls)
- Token cost: $0 (rule-based templating; LLM optional upgrade path)
- Human time saved: ~6 hrs/mo at $50/hr = $300/mo

## Acceptance Tests
1. Posts generated for every platform in brief
2. Frequency constraint met (posts/week within ±1 of target)
3. No duplicate post text across the calendar
4. Hashtags present on all social posts
5. Output files valid; calendar.csv parseable by pandas/csv module
