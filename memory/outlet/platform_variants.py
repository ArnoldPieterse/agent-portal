#!/usr/bin/env python3
"""Outlet Per-Platform Voice Variants + Lint (goal #5).

Takes a source draft and generates platform-specific variants:
  - X/Twitter: <=280 chars, punchy, one claim
  - LinkedIn: structured, professional, can be longer

Auto-lint enforces platform constraints. Voice consistency scored against
the fleet default voice guide (banned phrases, tone markers).

Verification: 10 source drafts -> 20 platform variants; 100% pass platform
constraints; voice consistency score >85%.
"""
import re, sys, datetime, tempfile, pathlib, json

HERE = pathlib.Path(__file__).resolve().parent
QUEUE = HERE / "queue"

BANNED_PHRASES = [
    "revolutionary", "game-changing", "unleash", "supercharge",
    "delve", "dive deep", "in todays fast-paced", "harness the power",
    "cutting-edge", "next-generation", "synergy", "leverage our",
]

def extract_body(text):
    m = re.search(r"## Body\n(.*?)(?=\n##)", text, re.DOTALL)
    return m.group(1).strip() if m else ""

def generate_x_variant(body):
    """X/Twitter: <=280 chars, punchy. Preserve key numbers + hook."""
    sentences = re.split(r"(?<=[.!?])\s+", body)
    # Strategy: pick the sentence(s) with the most data (numbers), stay under 280
    num_sents = [s for s in sentences if re.search(r"\d", s)]
    other_sents = [s for s in sentences if not re.search(r"\d", s)]
    
    draft = ""
    # Start with the most data-rich sentence
    if num_sents:
        draft = num_sents[0]
    elif sentences:
        draft = sentences[0]
    
    # Add a hook/context sentence if room allows
    for s in (other_sents + [n for n in num_sents if n != draft]):
        if len(draft) + len(" " + s.strip()) <= 275:
            draft = draft + " " + s.strip()
    
    # If still too long, hard truncate
    if len(draft) > 280:
        draft = draft[:274].rsplit(" ", 1)[0] + " ..."
    
    # If we lost all numbers (edge case), prepend a stat
    if not re.search(r"\d", draft):
        first_num_sent = num_sents[0] if num_sents else ""
        if first_num_sent and len(first_num_sent) <= 280:
            draft = first_num_sent
    
    return draft

def generate_linkedin_variant(body):
    """LinkedIn: structured, professional. Body + context framing."""
    lead = body
    # Add a professional framing line at top
    linkedin = f"Quick update from our fleet:\n\n{lead}\n\nThis is part of an ongoing convergence effort — the goal is fewer human touchpoints between event and shipped output, with human approval as the final gate.\n\n#AIagents #automation #convergence"
    return linkedin

def lint_x(variant):
    """X constraints: <=280 chars, no banned phrases, starts with hook."""
    fails = []
    if len(variant) > 280:
        fails.append(f"length {len(variant)} > 280")
    for p in BANNED_PHRASES:
        if p in variant.lower():
            fails.append(f"banned phrase: '{p}'")
    return fails

def lint_linkedin(variant):
    """LinkedIn constraints: <=3000 chars, no banned phrases, has structure (newlines)."""
    fails = []
    if len(variant) > 3000:
        fails.append(f"length {len(variant)} > 3000")
    for p in BANNED_PHRASES:
        if p in variant.lower():
            fails.append(f"banned phrase: '{p}'")
    # LinkedIn should have some structure (at least 2 newlines)
    if variant.count("\n") < 2:
        fails.append("insufficient structure (need >=2 line breaks)")
    return fails

def voice_consistency_score(variant, original_body):
    """Score how well the variant preserves the original voice.
    Check: same key numbers present, no hype added, tone markers preserved."""
    score = 100.0
    # Numbers preservation
    orig_nums = re.findall(r"\d+(?:\.\d+)?", original_body)
    var_nums = re.findall(r"\d+(?:\.\d+)?", variant)
    if orig_nums:
        missing = [n for n in orig_nums if n not in var_nums]
        score -= len(missing) * 10  # lose 10 per missing key number
    # Banned phrase penalty (already checked but double-count for consistency)
    for p in BANNED_PHRASES:
        if p in variant.lower():
            score -= 15
    # Tone check: should not be all caps or overly formal
    caps_ratio = sum(1 for c in variant if c.isupper()) / max(len(variant), 1)
    if caps_ratio > 0.3:
        score -= 20
    return max(score, 0)

def process_post(path):
    text = path.read_text(encoding="utf-8")
    body = extract_body(text)
    if not body:
        return {"file": path.name, "ok": False, "reason": "no body"}
    
    x_var = generate_x_variant(body)
    li_var = generate_linkedin_variant(body)
    
    x_fails = lint_x(x_var)
    li_fails = lint_linkedin(li_var)
    
    x_score = voice_consistency_score(x_var, body)
    li_score = voice_consistency_score(li_var, body)
    
    all_pass = not x_fails and not li_fails
    avg_score = (x_score + li_score) / 2
    
    return {
        "file": path.name, "ok": all_pass,
        "x_variant": x_var[:100] + ("..." if len(x_var) > 100 else ""),
        "linkedin_chars": len(li_var),
        "x_fails": x_fails, "li_fails": li_fails,
        "x_voice_score": x_score, "li_voice_score": li_score,
        "avg_consistency": avg_score,
    }

def selftest():
    global QUEUE
    saved = QUEUE
    with tempfile.TemporaryDirectory() as td:
        qd = pathlib.Path(td) / "queue"
        qd.mkdir()
        QUEUE = qd
        
        good_post = """# Test post
date: 2026-11-26
kind: upload
platform: test
status: ready-for-human
topic: Test

## Body
Level 12 is live. We closed 108 of 131 fleet goals this cycle, hitting 27 percent completion. The remaining work is recovery and handoffs - the unglamorous end where real progress shows.

## Rationale
- Test post for selftest.

## Evidence / sources
- fact-check: claim '108/131 = 27%' VERIFIED inline.

## Notes for ship
- Local test only.
"""
        (qd / "good.md").write_text(good_post, encoding="utf-8")
        
        r = process_post(qd / "good.md")
        QUEUE = saved
    
    print(json.dumps(r, indent=2))
    ok = r.get("ok") and r.get("avg_consistency", 0) > 85
    print(f"SELFTEST {'PASS' if ok else 'FAIL'} (consistency={r.get('avg_consistency')})")
    return 0 if ok else 1

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        return selftest()
    
    results = []
    for p in sorted(QUEUE.glob("*.md")):
        if p.name == "INDEX.md":
            continue
        r = process_post(p)
        results.append(r)
    
    total = len(results)
    passed = sum(1 for r in results if r.get("ok"))
    avg_consistency = sum(r.get("avg_consistency", 0) for r in results) / max(total, 1)
    
    print(f"platform_variants: {total} source drafts -> {total*2} platform variants")
    print(f"  X variants pass: {sum(1 for r in results if not r.get('x_fails'))}/{total}")
    print(f"  LinkedIn variants pass: {sum(1 for r in results if not r.get('li_fails'))}/{total}")
    print(f"  avg voice consistency: {avg_consistency:.0f}%")
    
    ok = (passed == total) and (avg_consistency > 85)
    print(f"OVERALL: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
