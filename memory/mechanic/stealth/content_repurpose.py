"""Content repurposing workflow - transforms a long-form article into 3 short-form variants.

Input: memory/mechanic/stealth/input/article.txt (any text file)
Output: memory/mechanic/stealth/output/variants_<ts>.json

In production, Builder replaces the extractive summarization with LLM calls.
This version uses sentence extraction to prove the pipeline works offline.
"""
import os, json, re
from datetime import datetime

BASE = os.path.dirname(__file__)
INPUT_DIR = os.path.join(BASE, 'input')
OUTPUT_DIR = os.path.join(BASE, 'output')
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_sentences(text):
    """Simple sentence splitter."""
    return re.split(r'(?<=[.!?])\s+', text.strip())

def main():
    input_file = os.path.join(INPUT_DIR, 'article.txt')

    if not os.path.exists(input_file):
        sample = ("AI automation is transforming how small businesses handle repetitive tasks. "
                 "Companies that adopt workflow automation see 40% reduction in manual labor costs. "
                 "The key is identifying which tasks are truly repetitive and rule-based. "
                 "Lead generation, invoice processing, and content repurposing top the list. "
                 "A well-designed workflow can run unattended for weeks without human intervention.")
        with open(input_file, 'w') as f:
            f.write(sample)
        print("[content_repurpose] Created sample article")

    with open(input_file, 'r') as f:
        text = f.read()

    sentences = extract_sentences(text)

    # Generate 3 variants (simplified extractive approach)
    n = len(sentences)
    variants = {
        'twitter': ' '.join(sentences[:2])[:280],
        'linkedin': ' '.join(sentences[:min(4, n)]),
        'newsletter': text  # full article for newsletter format
    }

    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    out_file = os.path.join(OUTPUT_DIR, f'variants_{ts}.json')
    with open(out_file, 'w') as f:
        json.dump({'source': os.path.basename(input_file), 'variants': variants, 
                  'generated_at': datetime.utcnow().isoformat()}, f, indent=2)

    print(f"[content_repurpose] Generated 3 variants from {n} sentences -> {os.path.basename(out_file)}")

if __name__ == '__main__':
    main()
