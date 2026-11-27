"""Run all 3 stealth workflows end-to-end with sample data. Demonstrates input->output for each.

Usage: python run_demo.py
Output: demo_output_*.json/.md files + stdout summary
"""
import json, sys
from pathlib import Path

BASE = Path(__file__).parent

def run_wf1():
    print("=" * 50)
    print("WF1: AR Follow-up (invoices.json -> reminders.json)")
    print("=" * 50)
    invoices = json.loads((BASE / "sample_invoices.json").read_text(encoding="utf-8"))
    print(f"  INPUT: {len(invoices)} invoices")
    for inv in invoices:
        print(f"    {inv['id']}: {inv['client']} ${inv['amount']} due {inv['due_date']} [{inv['status']}]")
    
    sys.path.insert(0, str(BASE))
    from wf1_ar_followup import process
    from datetime import date
    result = process(invoices, date.today())
    out = BASE / "demo_output_reminders.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    total = sum(len(v) for v in result["batches"].values())
    print(f"  OUTPUT: {total} reminders -> {out.name}")
    for tier, items in result["batches"].items():
        if items:
            for i in items:
                print(f"    [{tier}] {i['invoice_id']} {i['client']} ${i['amount']} ({i['days_overdue']}d overdue)")

def run_wf2():
    print("\n" + "=" * 50)
    print("WF2: Weekly Report (metrics.jsonl -> report.md)")
    print("=" * 50)
    lines = [l for l in (BASE / "sample_metrics.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"  INPUT: {len(lines)} metric rows")
    
    sys.path.insert(0, str(BASE))
    from wf2_weekly_report import load_metrics, compute_report
    from datetime import date
    records = load_metrics(BASE / "sample_metrics.jsonl")
    report = compute_report(records, date.today())
    out = BASE / "demo_output_report.md"
    out.write_text(report, encoding="utf-8")
    print(f"  OUTPUT: {out.name}")
    for line in report.splitlines():
        if line.startswith("- "):
            print(f"    {line}")

def run_wf3():
    print("\n" + "=" * 50)
    print("WF3: Reminder Pipeline (schedule.json -> reminders.json)")
    print("=" * 50)
    schedule = json.loads((BASE / "sample_schedule.json").read_text(encoding="utf-8"))
    print(f"  INPUT: {len(schedule)} appointments")
    for s in schedule:
        reminded = " [reminded]" if s.get("reminded") else ""
        print(f"    {s['id']}: {s['client']} - {s['title']} @ {s['datetime_iso']}{reminded}")
    
    sys.path.insert(0, str(BASE))
    from wf3_reminder_pipeline import find_due
    from datetime import datetime
    result = find_due(schedule, datetime.now(), window_hours=48)
    out = BASE / "demo_output_task_reminders.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"  OUTPUT: {result['due_count']} due, {result['skipped_already_reminded']} skipped -> {out.name}")
    for r in result["reminders"]:
        print(f"    DUE: {r['id']} {r['client']} - {r['title']} (in {r['hours_until']}h)")

if __name__ == "__main__":
    run_wf1()
    run_wf2()
    run_wf3()
    print("\n" + "=" * 50)
    print("ALL 3 WORKFLOWS COMPLETE")
    print("=" * 50)
