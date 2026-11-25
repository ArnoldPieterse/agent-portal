"""WF2: Social Media Content Scheduler (v2)"""
import argparse, csv, json, os, sys, time
from datetime import datetime, timedelta

TONE_TEMPLATES = {
    "friendly_expert": "{hook} {body} Follow for more tips! {cta}",
    "bold_direct": "{hook} Stop wasting time. {body} {cta}",
    "data_driven": "{hook} The numbers don't lie: {body} {cta}"
}
CTAS = ["Link in bio.", "DM us 'START' to begin.", "Save this post."]

def generate_posts(brief):
    posts = []
    start_date = datetime.strptime(brief.get("start_date", "2026-12-01"), "%Y-%m-%d")
    days_per_week = brief.get("days_per_week", 3)
    platforms = brief.get("platforms", ["instagram"])
    tone = brief.get("tone", "friendly_expert")
    template = TONE_TEMPLATES.get(tone, TONE_TEMPLATES["friendly_expert"])
    day_offsets = [0, 1, 2, 3, 4, 5, 6][:days_per_week]
    for topic in brief.get("topics", []):
        hook = topic.get("hook", topic["name"].upper() + "!")
        body = topic.get("body", f"Here's what you need to know about {topic['name'].lower()}.")
        cta = CTAS[hash(topic["name"]) % len(CTAS)]
        for i, day_off in enumerate(day_offsets):
            post_date = start_date + timedelta(days=i * (7 // max(days_per_week, 1)) + day_off)
            for plat in platforms:
                text = template.format(hook=hook, body=body, cta=cta)
                tags = " ".join(f"#{t}" for t in topic.get("hashtags", [topic["name"].lower().replace(" ", "")]))
                posts.append({"date": post_date.strftime("%Y-%m-%d"), "platform": plat,
                             "post_text": text[:280], "hashtags": tags,
                             "topic": topic["name"]})
    return posts

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--brief', required=True)
    ap.add_argument('--output', default='./wf2_out')
    args = ap.parse_args()
    t0 = time.time()
    with open(args.brief, encoding='utf-8') as f:
        brief = json.load(f)
    posts = generate_posts(brief)
    runtime = round(time.time() - t0, 4)
    os.makedirs(args.output, exist_ok=True)
    cost = {"model": "rule-based (no LLM)", "input_tokens": 0, "output_tokens": 0,
            "estimated_usd": 0.0, "notes": f"template generation for {len(posts)} posts"}
    cost_usd = round(len(posts) * 0.001, 4)
    result = {"generated_at": datetime.utcnow().isoformat(), "runtime_seconds": runtime, "cost_usd": cost_usd,
              "total_posts": len(posts), "platforms": brief.get("platforms", []),
              "posts": posts, "cost": cost}
    with open(os.path.join(args.output, 'scheduled_posts.json'), 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    print(f"WF2 complete: {len(posts)} posts scheduled, {runtime}s")
    return 0

if __name__ == '__main__':
    sys.exit(main())
