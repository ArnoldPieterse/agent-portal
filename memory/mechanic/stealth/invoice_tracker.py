"""Invoice tracking workflow - parses expense/invoice CSV and produces status summary.

Input: memory/mechanic/stealth/input/invoices.csv (columns: vendor, amount, due_date, status)
Output: memory/mechanic/stealth/output/invoice_summary_<ts>.json

In production, Builder adds PDF parsing + email ingestion.
This version works with CSV to prove the scheduling pipeline.
"""
import csv, os, json
from datetime import datetime

BASE = os.path.dirname(__file__)
INPUT_DIR = os.path.join(BASE, 'input')
OUTPUT_DIR = os.path.join(BASE, 'output')
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    input_file = os.path.join(INPUT_DIR, 'invoices.csv')

    if not os.path.exists(input_file):
        with open(input_file, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['vendor', 'amount', 'due_date', 'status'])
            w.writerow(['CloudHost Inc', 299.00, '2026-12-01', 'pending'])
            w.writerow(['DataPipe API', 49.99, '2026-11-30', 'paid'])
            w.writerow(['SaaS Metrics', 149.00, '2026-12-15', 'pending'])
        print("[invoice_tracker] Created sample input (3 invoices)")

    rows = []
    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['amount'] = float(row['amount'])
            rows.append(row)

    total = sum(r['amount'] for r in rows)
    pending = sum(r['amount'] for r in rows if r['status'] == 'pending')
    paid = sum(r['amount'] for r in rows if r['status'] == 'paid')

    summary = {
        'total_invoices': len(rows),
        'total_amount': round(total, 2),
        'pending_amount': round(pending, 2),
        'paid_amount': round(paid, 2),
        'pending_count': sum(1 for r in rows if r['status'] == 'pending'),
        'generated_at': datetime.utcnow().isoformat()
    }

    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    out_file = os.path.join(OUTPUT_DIR, f'invoice_summary_{ts}.json')
    with open(out_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"[invoice_tracker] Processed {len(rows)} invoices (${total:.2f} total) -> {os.path.basename(out_file)}")

if __name__ == '__main__':
    main()
