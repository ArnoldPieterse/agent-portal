"""WF3: CRM Data Entry Pipeline
Usage: python wf3_crm_entry.py --input <json> --schema <json> --output <dir>
"""
import argparse, csv, json, os, sys, time
from datetime import datetime

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--schema", required=True)
    ap.add_argument("--output", default="./wf3_out")
    args = ap.parse_args()
    t0 = time.time()
    with open(args.input, encoding="utf-8") as f:
        raw_contacts = json.load(f)
    with open(args.schema, encoding="utf-8") as f:
        schema = json.load(f)
    required = schema.get("required_fields", [])
    accepted, rejected, dups = [], [], []
    seen_emails = set()
    for c in raw_contacts:
        email = c.get("email", "").lower().strip()
        missing = [f for f in required if not c.get(f)]
        if missing:
            rejected.append({"name": c.get("name","?"), "reason": "missing:" + ",".join(missing)})
            continue
        if email in seen_emails:
            dups.append(email)
            continue
        seen_emails.add(email)
        rec = {f: c.get(f, "") for f in schema.get("all_fields", required)}
        accepted.append(rec)
    runtime = round(time.time() - t0, 4)
    cost = round(len(raw_contacts) * 0.001 + 0.02, 4)
    os.makedirs(args.output, exist_ok=True)
    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "runtime_seconds": runtime,
        "total_input": len(raw_contacts),
        "accepted": accepted,
        "rejected": rejected,
        "duplicates": dups,
        "summary": {
            "accept_rate": round(len(accepted)/max(len(raw_contacts),1)*100, 1),
            "reject_count": len(rejected),
            "dup_count": len(dups)
        },
        "cost_usd": cost
    }
    with open(os.path.join(args.output, "cleaned_records.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    with open(os.path.join(args.output, "rejected.csv"), "w", newline="", encoding="utf-8") as f:
        if rejected:
            w = csv.DictWriter(f, fieldnames=["name","reason"])
            w.writeheader()
            w.writerows(rejected)
        else:
            f.write("No rejections.\n")
    with open(os.path.join(args.output, "stats.md"), "w", encoding="utf-8") as f:
        f.write(f"# CRM Entry Report\n- Runtime: {runtime}s\n"
                f"- Input: {len(raw_contacts)} records\n"
                f"- Accepted: {len(accepted)}\n"
                f"- Rejected: {len(rejected)}\n"
                f"- Duplicates: {len(dups)}\n"
                f"- Cost: ${cost}\n")
    print(f"WF3 complete: {len(accepted)} accepted, {len(rejected)} rejected, "
          f"{len(dups)} dups, {runtime}s")
    return 0

if __name__ == "__main__":
    sys.exit(main())
