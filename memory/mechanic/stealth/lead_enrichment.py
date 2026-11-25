"""Lead enrichment workflow - enriches a CSV of company names with contact patterns.

Input: memory/mechanic/stealth/input/leads.csv (columns: company, website)
Output: memory/mechanic/stealth/output/enriched_leads_<ts>.csv

In production, Builder replaces the heuristic enrichment with real API calls.
This version works offline to prove the hosting pipeline.
"""
import csv, os, json, re
from datetime import datetime

BASE = os.path.dirname(__file__)
INPUT_DIR = os.path.join(BASE, 'input')
OUTPUT_DIR = os.path.join(BASE, 'output')
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def guess_email_domain(company, website):
    """Generate likely email patterns from company name."""
    domain = website.replace('https://', '').replace('http://', '').split('/')[0] if website else ''
    slug = re.sub(r'[^a-z0-9]', '', company.lower())[:12]
    patterns = [f"info@{domain}", f"hello@{domain}", f"contact@{domain}"]
    return patterns, domain

def main():
    input_file = os.path.join(INPUT_DIR, 'leads.csv')

    # If no input file, create a sample for demo
    if not os.path.exists(input_file):
        with open(input_file, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['company', 'website'])
            w.writerow(['Acme Logistics', 'acmelogistics.com'])
            w.writerow(['BrightPath Marketing', 'brightpath.io'])
            w.writerow(['CoreStack Analytics', 'corestack.dev'])
        print("[lead_enrichment] Created sample input (3 leads)")

    rows = []
    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            patterns, domain = guess_email_domain(row['company'], row.get('website', ''))
            rows.append({
                'company': row['company'],
                'website': row.get('website', ''),
                'domain': domain,
                'email_patterns': '|'.join(patterns),
                'enriched_at': datetime.utcnow().isoformat()
            })

    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    out_file = os.path.join(OUTPUT_DIR, f'enriched_leads_{ts}.csv')
    with open(out_file, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['company','website','domain','email_patterns','enriched_at'])
        w.writeheader()
        w.writerows(rows)

    print(f"[lead_enrichment] Enriched {len(rows)} leads -> {os.path.basename(out_file)}")

if __name__ == '__main__':
    main()
