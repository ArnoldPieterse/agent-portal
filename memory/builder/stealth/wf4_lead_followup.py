"""WF4: Lead Follow-up & Chasing Pipeline  (Stealth Revenue Engine)

Maps to Researcher task-inventory gap candidate #5 (Lead follow-up scheduling
& chasing): auto-escalation on silence. Adjacent to WF3 reminder logic.

Input : leads.json (list of {id, name, source, stage, value,
                             last_contact_iso, silent_days_threshold,
                             status? , last_escalated_iso?, cooldown_days?})
Output: followups.json ({generated, due_count, by_tier, actions[], skipped_closed})
        + stdout summary.

Logic : For each OPEN lead (status not in {won,lost,closed}), compute days since
        last contact. If days_silent >= silent_days_threshold the lead is DUE for
        a follow-up; assign an escalation tier by how far past threshold it is:
          excess < 3   -> tier1 nudge      "Send follow-up email"
          excess < 7   -> tier2 call       "Schedule a call"
          excess < 14  -> tier3 offer      "Present offer / incentive"
          else         -> tier4 manager    "Escalate to manager (final touch)"
        Idempotent: leads already escalated within cooldown_days are skipped
        (counted in skipped_cooldown), closed leads counted in skipped_closed.

Usage:
    python wf4_lead_followup.py --selftest
    python wf4_lead_followup.py --input leads.json --output followups.json
"""
import json, sys, argparse
from datetime import datetime
from pathlib import Path

CLOSED = {"won", "lost", "closed"}

TIERS = [
    (3, 1, "nudge",   "Send follow-up email"),
    (7, 2, "call",    "Schedule a call"),
    (14, 3, "offer",  "Present offer / incentive"),
    (float("inf"), 4, "manager", "Escalate to manager (final touch)"),
]

def _days(a: datetime, b: datetime) -> float:
    return (b - a).total_seconds() / 86400.0

def tier_for(excess: float):
    for cap, num, name, action in TIERS:
        if excess < cap:
            return num, name, action
    return 4, "manager", "Escalate to manager (final touch)"

def find_due(leads: list[dict], now: datetime) -> dict:
    due, skipped_closed, skipped_cooldown = [], 0, 0
    by_tier = {1: 0, 2: 0, 3: 0, 4: 0}
    for lead in leads:
        if (lead.get("status") or "open").lower() in CLOSED:
            skipped_closed += 1
            continue
        last_contact = datetime.fromisoformat(lead["last_contact_iso"])
        days_silent = _days(last_contact, now)
        threshold = lead.get("silent_days_threshold", 7)
        if days_silent < threshold:
            continue  # not yet due
        # idempotency: cooldown on recent escalation
        last_esc = lead.get("last_escalated_iso")
        cooldown = lead.get("cooldown_days", 3)
        if last_esc and _days(datetime.fromisoformat(last_esc), now) < cooldown:
            skipped_cooldown += 1
            continue
        excess = days_silent - threshold
        num, name, action = tier_for(excess)
        by_tier[num] += 1
        due.append({
            "id": lead["id"],
            "name": lead.get("name", ""),
            "source": lead.get("source", ""),
            "stage": lead.get("stage", "new"),
            "value": lead.get("value", 0),
            "days_silent": round(days_silent, 1),
            "tier": num,
            "tier_name": name,
            "action": action,
        })
    due.sort(key=lambda r: (-r["value"], -r["days_silent"]))
    return {
        "generated": now.isoformat(),
        "due_count": len(due),
        "by_tier": by_tier,
        "skipped_closed": skipped_closed,
        "skipped_cooldown": skipped_cooldown,
        "actions": due,
    }

def selftest():
    now = datetime(2026, 11, 25, 9, 0, 0)
    leads = [
        # 8 days silent, threshold 7 -> excess 1 -> tier1 nudge
        {"id": "L1", "name": "Acme Corp", "source": "web", "stage": "qualified",
         "value": 5000, "last_contact_iso": "2026-11-17T09:00:00", "silent_days_threshold": 7},
        # 20 days silent, threshold 7 -> excess 13 -> tier3 offer
        {"id": "L2", "name": "Beta Ltd", "source": "referral", "stage": "proposal",
         "value": 9000, "last_contact_iso": "2026-11-05T09:00:00", "silent_days_threshold": 7},
        # 30 days silent, threshold 7 -> excess 23 -> tier4 manager
        {"id": "L3", "name": "Gamma Inc", "source": "cold", "stage": "lead",
         "value": 1200, "last_contact_iso": "2026-10-26T09:00:00", "silent_days_threshold": 7},
        # only 3 days silent, threshold 7 -> not due
        {"id": "L4", "name": "Delta Co", "source": "web", "stage": "lead",
         "value": 2000, "last_contact_iso": "2026-11-22T09:00:00", "silent_days_threshold": 7},
        # closed won -> skipped_closed
        {"id": "L5", "name": "Epsilon", "source": "web", "stage": "closed",
         "value": 3000, "last_contact_iso": "2026-11-01T09:00:00", "silent_days_threshold": 7,
         "status": "won"},
        # due but escalated 1 day ago (cooldown 3) -> skipped_cooldown
        {"id": "L6", "name": "Zeta", "source": "web", "stage": "qualified",
         "value": 4000, "last_contact_iso": "2026-11-10T09:00:00", "silent_days_threshold": 7,
         "last_escalated_iso": "2026-11-24T09:00:00", "cooldown_days": 3},
    ]
    r = find_due(leads, now)
    assert r["due_count"] == 3, f"expected 3 due, got {r['due_count']}"
    # sorted by value desc: L2(9000) tier3, L1(5000) tier1, L3(1200) tier4
    assert [a["id"] for a in r["actions"]] == ["L2", "L1", "L3"], r["actions"]
    assert r["by_tier"] == {1: 1, 2: 0, 3: 1, 4: 1}, r["by_tier"]
    assert r["skipped_closed"] == 1 and r["skipped_cooldown"] == 1, (r["skipped_closed"], r["skipped_cooldown"])
    print("WF4 selftest PASS: 4/4 assertions")
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--input", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    if args.selftest:
        sys.exit(0 if selftest() else 1)
    leads = json.loads(args.input.read_text(encoding="utf-8"))
    result = find_due(leads, datetime.now())
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"WF4: {result['due_count']} follow-ups due "
          f"(tiers {result['by_tier']}); {result['skipped_closed']} closed, "
          f"{result['skipped_cooldown']} in cooldown -> {args.output}")

if __name__ == "__main__":
    main()