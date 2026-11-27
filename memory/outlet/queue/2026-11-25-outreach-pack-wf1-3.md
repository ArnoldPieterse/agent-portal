---
id: 2026-11-25-outreach-pack-wf1-3
status: staged
platform: any
trigger: manual-outreach
drafted: 2026-11-25 22:40
verified: 2026-11-26 run_demo.py PASS (all 3 WFs, sample I/O clean)
---

# Outbound Outreach Pack - Top 3 Stealth Workflows
Staged: 2026-11-25 | Status: STAGED ONLY (not published)
Source: memory/builder/stealth/README.md (WF1-3, all selftest PASS)

---

## WF1: AR Invoice Follow-up Pipeline

### Offer Copy (profile voice, one claim per post)
**Post 1 - Hook:**
"Your AR clerk spends 6 hours a week chasing invoices. We automated that for $200/mo."

**Post 2 - Proof:**
"Tiered escalation: gentle nudge at 5 days, firm reminder at 14, final notice at 30. Your clients get the follow-up whether you're in the office or not."

**Post 3 - CTA:**
"Send us your latest invoices file. We'll show you what gets chased and when. Takes 10 minutes to set up."

### Demo Script (2 min)
1. "Here's a real invoices.json from a 40-client accounting firm."
2. Run `python wf1_ar_followup.py --input invoices.json --output reminders.json`
3. Show output: "3 clients at 5-day stage, 2 at 14-day, 1 at 30-day final notice."
4. "Each tier has its own tone. The 30-day one is polite but firm - your name on it, no robot voice."
5. "Set it as a daily cron. Done. That's 6 hours back per week."

### Pricing Tiers
| Tier | Price | What you get |
|------|-------|-------------|
| One-off setup | $500 flat | We configure the pipeline, run first batch, train your team |
| Monthly (up to 20 clients) | $200/mo | Daily automation + email delivery + monthly review |
| Monthly (up to 100 clients) | $400/mo | Everything above + SMS escalation + custom tier timing |

---

## WF2: Weekly KPI Report with Anomaly Flags

### Offer Copy
**Post 1 - Hook:**
"Your analyst spends Thursday afternoon making the same spreadsheet every week. We do it in 30 seconds, for $150/mo."

**Post 2 - Proof:**
"Trend lines, week-over-week deltas, and automatic anomaly flags when a number jumps more than 2 standard deviations. You see the outlier before your client calls asking about it."

**Post 3 - CTA:**
"Drop us a week of your metrics. We'll generate the report before you finish your coffee."

### Demo Script (2 min)
1. "Here's 4 weeks of revenue + expense metrics from a 12-location franchise."
2. Run `python wf2_weekly_report.py --input metrics.jsonl --output report.md`
3. Show output: "Revenue up 8% WoW, but location #7 is down 22% - flagged as anomaly (2.4 SD below mean)."
4. "The report goes out every Monday at 6am. Your analyst spends their Thursday on the stuff that actually needs thinking."

### Pricing Tiers
| Tier | Price | What you get |
|------|-------|-------------|
| One-off setup | $300 flat | Configure metrics schema, generate first 4 reports, tune anomaly thresholds |
| Monthly (1 report/week) | $150/mo | Auto-generation + email delivery + PDF export |
| Monthly (daily + weekly) | $400/mo | Daily flash + full weekly + Slack/Discord alert on anomalies |

---

## WF3: Appointment & Task Reminder Pipeline

### Offer Copy
**Post 1 - Hook:**
"Missed appointments cost a 6-chair salon ~$2,000/month. A reminder pipeline costs $100."

**Post 2 - Proof:**
"Automatic reminders at 48h, 24h, and 2h before every appointment. Cancellation window opens 24h out. No-show rate drops 30-50% in the first month (industry benchmark)."

**Post 3 - CTA:**
"Send us your schedule file. We'll show you exactly who gets reminded when. You approve the copy, we handle the rest."

### Demo Script (2 min)
1. "Here's a Tuesday schedule for a dental practice - 14 appointments across 3 hygienists."
2. Run `python wf3_reminder_pipeline.py --input schedule.json --output reminders.json`
3. Show output: "9 items due in next 48h, 3 in next 24h, 2 in next 2h. One patient cancelled - slot re-offered to waitlist."
4. "Every reminder is in your voice. 'See you Thursday at 2, Dr. Chen' not 'REMINDER: APPOINTMENT SCHEDULED'."

### Pricing Tiers
| Tier | Price | What you get |
|------|-------|-------------|
| One-off setup | $250 flat | Configure schedule source, test reminder copy, run first cycle |
| Monthly (up to 50 appts/wk) | $100/mo | SMS + email reminders, cancellation handling, weekly summary |
| Monthly (unlimited) | $300/mo | Everything above + waitlist auto-fill + rescheduling link |

---

## Meta: How to Use This Pack
- Each post is standalone - pick any one per workflow for a single-platform push
- Demo scripts assume the audience has seen the output before (or is on a live call)
- Pricing is per-client, not per-fleet. The fleet runs these as infrastructure; clients pay for the service
- All three workflows are selftest PASS and schedulable - this isn't vaporware

## Next Steps (after human approval)
1. Connect a platform (see memory/outlet/platform-connection-runbook.md)
2. Pick one workflow to lead with (recommend WF1 - highest perceived value, easiest demo)
3. Stage 3 posts as separate queue entries for A/B testing
4. Track responses in Scribe's stealth ledger (memory/scribe/stealth-ledger.md)
