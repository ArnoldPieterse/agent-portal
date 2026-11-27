"""WF1: Accounts Receivable Follow-up Automation

Input : invoices.json  (list of {id, client, amount, due_date, status})
Output: reminders.json (escalated reminder batches) + stdout summary
Logic : Day 7 / 14 / 21 past-due escalation tiers; idempotent (skips sent).

Usage:
    python wf1_ar_followup.py --selftest
    python wf1_ar_followup.py --input invoices.json --output reminders.json
"""
import json, sys, argparse
from datetime import date, timedelta
from pathlib import Path

TIERS = [(7, "gentle", "friendly reminder"), (14, "firm", "payment overdue notice"), (21, "final", "final notice before escalation")]

def classify(invoice: dict, today: date) -> str | None:
    """Return tier label if invoice is past-due and not yet sent at that tier."""
    if invoice.get("status") == "paid":
        return None
    due = date.fromisoformat(invoice["due_date"])
    days_overdue = (today - due).days
    if days_overdue < 7:
        return None
    sent_tiers = set(invoice.get("sent_tiers", []))
    for threshold, label, _ in TIERS:
        if days_overdue >= threshold and label not in sent_tiers:
            return label
    return None

def process(invoices: list[dict], today: date) -> dict:
    batches = {t[1]: [] for t in TIERS}
    for inv in invoices:
        tier = classify(inv, today)
        if tier:
            batch = batches[tier]
            batch.append({
                "invoice_id": inv["id"],
                "client": inv["client"],
                "amount": inv["amount"],
                "days_overdue": (today - date.fromisoformat(inv["due_date"])).days,
                "tier": tier,
            })
    return {"generated": today.isoformat(), "batches": batches}

def selftest():
    today = date(2026, 11, 25)
    invoices = [
        {"id": "INV-001", "client": "Acme Co", "amount": 1200, "due_date": "2026-11-01", "status": "unpaid", "sent_tiers": ["gentle"]},
        {"id": "INV-002", "client": "Beta LLC", "amount": 3400, "due_date": "2026-11-10", "status": "unpaid", "sent_tiers": []},
        {"id": "INV-003", "client": "Gamma Inc", "amount": 800,  "due_date": "2026-11-20", "status": "unpaid", "sent_tiers": []},
        {"id": "INV-004", "client": "Delta Corp","amount": 5000, "due_date": "2026-11-20", "status": "paid",   "sent_tiers": ["gentle"]},
    ]
    result = process(invoices, today)
    # INV-001: 24 days overdue, sent gentle -> next tier is 'firm'
    # INV-002: 15 days overdue, no tiers sent -> first qualifying tier is 'gentle'
    # INV-003: 5 days overdue -> None (below threshold)
    # INV-004: paid -> None
    assert len(result["batches"]["gentle"]) == 1, f"expected 1 gentle, got {len(result['batches']['gentle'])}"
    assert result["batches"]["gentle"][0]["invoice_id"] == "INV-002"
    assert len(result["batches"]["firm"]) == 1, f"expected 1 firm, got {len(result['batches']['firm'])}"
    assert result["batches"]["firm"][0]["invoice_id"] == "INV-001"
    assert len(result["batches"]["final"]) == 0
    print("WF1 selftest PASS: 4/4 assertions")
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--input", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    if args.selftest:
        sys.exit(0 if selftest() else 1)
    invoices = json.loads(args.input.read_text(encoding="utf-8"))
    result = process(invoices, date.today())
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    total = sum(len(v) for v in result["batches"].values())
    print(f"WF1: {total} reminders generated -> {args.output}")

if __name__ == "__main__":
    main()