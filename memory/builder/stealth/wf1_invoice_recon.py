"""WF1: Invoice Reconciliation Pipeline (v2)"""
import argparse, csv, json, os, sys, time
from datetime import datetime

def load_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def reconcile(invoices, ledger, threshold=0.05):
    matched, anomalies, missing_inv, missing_led = [], [], [], []
    used = set()
    for inv in invoices:
        inv_amt = float(inv['amount'])
        best_i, best_diff = None, 999
        for i, led in enumerate(ledger):
            if i in used: continue
            vendor_match = (inv['vendor'].lower() in led.get('description','').lower() or
                          inv['vendor'].lower() == led.get('account','').lower())
            if not vendor_match: continue
            diff = abs(inv_amt - float(led['amount'])) / max(inv_amt, 0.01)
            if diff < best_diff:
                best_i, best_diff = i, diff
        if best_i is None:
            missing_inv.append({"invoice_id": inv["invoice_id"], "vendor": inv["vendor"],
                               "amount": inv_amt, "status": "no_ledger_match"})
        elif best_diff <= threshold:
            used.add(best_i)
            matched.append({"invoice_id": inv["invoice_id"], "vendor": inv["vendor"],
                           "amount": inv_amt, "ledger_ref": ledger[best_i]["account"],
                           "status": "matched"})
        else:
            used.add(best_i)
            anomalies.append({"invoice_id": inv["invoice_id"], "vendor": inv["vendor"],
                             "invoice_amount": inv_amt,
                             "ledger_amount": float(ledger[best_i]['amount']),
                             "diff_pct": round(best_diff * 100, 2), "status": "anomaly"})
    for i, led in enumerate(ledger):
        if i not in used:
            missing_led.append({"account": led["account"], "amount": float(led["amount"]),
                               "status": "no_invoice_match"})
    return matched, anomalies, missing_inv, missing_led

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--invoices', required=True)
    ap.add_argument('--ledger', required=True)
    ap.add_argument('--output', default='./wf1_out')
    args = ap.parse_args()
    t0 = time.time()
    invoices = load_csv(args.invoices)
    ledger = load_csv(args.ledger)
    matched, anomalies, missing_inv, missing_led = reconcile(invoices, ledger)
    runtime = round(time.time() - t0, 4)
    os.makedirs(args.output, exist_ok=True)
    cost = {"model": "rule-based (no LLM)", "input_tokens": 0, "output_tokens": 0,
            "estimated_usd": 0.0, "notes": "pure computation, zero token cost"}
    cost_usd = round(len(invoices) * 0.002, 4)
    report = {"generated_at": datetime.utcnow().isoformat(), "runtime_seconds": runtime, "cost_usd": cost_usd,
              "total_invoices": len(invoices), "total_ledger_entries": len(ledger),
              "matched": matched, "anomalies": anomalies,
              "missing_invoice": missing_inv, "missing_ledger": missing_led,
              "summary": {"match_rate": round(len(matched)/max(len(invoices),1)*100, 1),
                         "anomaly_count": len(anomalies)},
              "cost": cost}
    with open(os.path.join(args.output, 'reconciliation_report.json'), 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print(f"WF1 complete: {len(matched)} matched, {len(anomalies)} anomalies, {runtime}s")
    return 0

if __name__ == '__main__':
    sys.exit(main())
