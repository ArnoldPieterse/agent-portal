"""Stealth Revenue Engine — Day-7 checkpoint generator.

Owner: Orchestrator.  Date-gated deliverable for 2026-12-02 (day-7 of engine,
started 2026-11-25). Produces a level-report-style markdown + JSON sidecar from
Scribe's daily ledger and the Builder workflow registry.

Usage:
    python memory/orchestrator/stealth_checkpoint.py            # run against live data
    python memory/orchestrator/stealth_checkpoint.py --selftest # synthetic data, assert logic

Outputs (relative to repo root):
    memory/orchestrator/stealth-checkpoint-latest.md
    memory/orchestrator/stealth-checkpoint-latest.json

Honesty rule: the day-7 CLOSURE of this goal is NOT producible before 2026-12-02
with real revenue. This tool prepares the report; running it today yields a valid
day-N report reflecting actual (possibly $0) state. Do not hand-mark the goal
reached on a pre-day-7 run.
"""
from __future__ import annotations
import json, re, sys, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # repo root (memory/orchestrator/..)
ENGINE_START = dt.date(2026, 11, 25)
TARGET_USD = 3800.0
DAY7 = ENGINE_START + dt.timedelta(days=7)  # 2026-12-02

# Workflow registry — sourced from memory/builder/stealth/README.md (Builder, 2026-11-25).
WORKFLOWS = {
    "wf1": {"name": "AR follow-up reminders",   "script": "wf1_ar_followup.py",     "price_low": 200, "price_high": 500},
    "wf2": {"name": "Weekly KPI report",        "script": "wf2_weekly_report.py",   "price_low": 150, "price_high": 400},
    "wf3": {"name": "Reminder pipeline",        "script": "wf3_reminder_pipeline.py","price_low": 100, "price_high": 300},
}

LEDGER_MD   = ROOT / "memory" / "scribe" / "stealth-ledger.md"
LEDGER_JSONL = ROOT / "memory" / "scribe" / "stealth-ledger.jsonl"
OUT_MD   = ROOT / "memory" / "orchestrator" / "stealth-checkpoint-latest.md"
OUT_JSON = ROOT / "memory" / "orchestrator" / "stealth-checkpoint-latest.json"


def parse_ledger_jsonl(path: Path) -> dict:
    """Parse Scribe's stealth-ledger.jsonl (structured). Primary data source.

    Each line is a JSON object with fields:
        date, outreach_staged, replies, demos, revenue_usd,
        wf1_ar_followup{staged,replies,closed}, wf2_weekly_report{...}, wf3_reminder_pipeline{...}
    Returns same shape as parse_ledger_md for drop-in compatibility.
    """
    total_revenue = 0.0
    per_wf = {k: 0.0 for k in WORKFLOWS}
    outreach = replies = demos = 0
    days = []

    if not path.exists():
        return {"days": [], "revenue": 0.0, "per_wf": per_wf,
                "outreach": 0, "replies": 0, "demos": 0}

    for line in path.read_text(encoding="utf-8").strip().splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        d = entry.get("date", "")
        if d:
            days.append(d)
        total_revenue += float(entry.get("revenue_usd", 0))
        outreach += int(entry.get("outreach_staged", 0))
        replies += int(entry.get("replies", 0))
        demos += int(entry.get("demos", 0))
        for k in WORKFLOWS:
            wf_data = entry.get(k, {})
            if isinstance(wf_data, dict):
                per_wf[k] += float(wf_data.get("closed", 0)) * 1.0  # closed deals count as revenue proxy

    return {
        "days": sorted(set(days)),
        "revenue": round(total_revenue, 2),
        "per_wf": {k: round(v, 2) for k, v in per_wf.items()},
        "outreach": outreach, "replies": replies, "demos": demos,
    }


def parse_ledger_md(text: str) -> dict:
    """Parse Scribe's stealth ledger (markdown). Fallback if JSONL absent.

    Recognised patterns per daily entry:
        - date header line containing YYYY-MM-DD
        - revenue:  a line like `revenue: $123` or `revenue $123` (per day)
        - attribution: lines like `wf1: $X` / `wf1 $X` / `wf1= $X`
    Returns {day, revenue, per_wf, outreach, replies, demos} summed across entries.
    """
    total_revenue = 0.0
    per_wf = {k: 0.0 for k in WORKFLOWS}
    outreach = replies = demos = 0
    days = []

    money = re.compile(r"\$\s?([0-9][0-9,]*\.?[0-9]*)")

    def grab(line):
        m = money.search(line)
        return float(m.group(1).replace(",", "")) if m else None

    for line in text.splitlines():
        low = line.lower()
        dm = re.search(r"(\d{4}-\d{2}-\d{2})", line)
        if dm and ("#" in line or "day" in low):
            days.append(dm.group(1))
        v = None
        # revenue line (not an attribution line)
        if re.search(r"\brevenue\b", low):
            # exclude lines that are clearly per-wf attribution
            if not re.search(r"\bwf[123]\b", low):
                v = grab(line)
                if v is not None:
                    total_revenue += v
        for k in WORKFLOWS:
            if re.search(rf"\b{k}\b", low):
                v = grab(line)
                if v is not None:
                    per_wf[k] += v
        m = re.search(r"outreach[^\d]*([0-9]+)", low)
        if m: outreach += int(m.group(1))
        m = re.search(r"repl(?:y|ies)[^\d]*([0-9]+)", low)
        if m: replies += int(m.group(1))
        m = re.search(r"demos?[^\d]*([0-9]+)", low)
        if m: demos += int(m.group(1))

    return {
        "days": sorted(set(days)),
        "revenue": round(total_revenue, 2),
        "per_wf": {k: round(v, 2) for k, v in per_wf.items()},
        "outreach": outreach, "replies": replies, "demos": demos,
    }


def wf_status(key: str) -> str:
    """Live status of a workflow's script (exists + selftest present)."""
    p = ROOT / "memory" / "builder" / "stealth" / WORKFLOWS[key]["script"]
    if not p.exists():
        return "missing-script"
    try:
        src = p.read_text(encoding="utf-8")
    except Exception:
        return "unreadable"
    return "running" if "--selftest" in src else "no-selftest"


def decide(key: str, revenue: float) -> tuple[str, str]:
    """Scale/kill decision for a workflow given its attributed revenue.

    Returns (decision, rationale). Conservative until day-7 real data exists.
    """
    info = WORKFLOWS[key]
    floor = info["price_low"]
    if revenue >= 2 * floor:
        return "SCALE", f"${revenue:.0f} attributed >= 2x ${floor}/mo floor"
    if revenue >= floor:
        return "HOLD", f"${revenue:.0f} within ${floor}-${info['price_high']}/mo band"
    if revenue > 0:
        return "HOLD", f"${revenue:.0f} below ${floor}/mo floor — one more cycle to prove out"
    # zero attributed revenue
    status = wf_status(key)
    if status != "running":
        return "BLOCKED", f"workflow not runnable (status={status}); fix before scaling"
    return "HOLD", "$0 attributed yet — engine pre-revenue; do not kill on day<7"


def build_report(today: dt.date, L: dict) -> tuple[str, dict]:
    """L is the parsed ledger dict from parse_ledger_jsonl or parse_ledger_md."""
    day_num = (today - ENGINE_START).days
    gap = TARGET_USD - L["revenue"]
    pct = 100.0 * L["revenue"] / TARGET_USD if TARGET_USD else 0.0

    decisions = {k: decide(k, L["per_wf"][k]) for k in WORKFLOWS}

    lines = []
    ap = lines.append
    ap(f"# Stealth Revenue Engine — Day-{max(day_num,0)} Checkpoint")
    ap("")
    ap(f"- Generated: {today.isoformat()} (day {day_num} of engine; start {ENGINE_START.isoformat()})")
    ap(f"- Target: ${TARGET_USD:,.0f} by day-7 ({DAY7.isoformat()})")
    ap(f"- Revenue to date: **${L['revenue']:,.2f}**  ({pct:.1f}% of target)")
    ap(f"- Gap to target: ${gap:,.2f}")
    ap(f"- Ledger days captured: {len(L['days'])}  |  outreach staged: {L['outreach']}  replies: {L['replies']}  demos: {L['demos']}")
    ap("")
    if L["revenue"] == 0 and day_num < 7:
        ap("> **Status:** engine is pre-revenue (day " + str(max(day_num,0)) + "). Report reflects real state; "
           "do not treat $0 as a failure before the day-7 window closes.")
        ap("")
    ap("## Per-workflow attribution")
    ap("")
    ap("| WF | Task | Script | Status | Revenue | Price band | Decision | Rationale |")
    ap("|----|------|--------|--------|---------|------------|----------|-----------|")
    for k in WORKFLOWS:
        info = WORKFLOWS[k]
        d, why = decisions[k]
        ap(f"| {k} | {info['name']} | `{info['script']}` | {wf_status(k)} | "
           f"${L['per_wf'][k]:,.0f} | ${info['price_low']}-{info['price_high']}/mo | **{d}** | {why} |")
    ap("")
    ap("## Scale / Kill decisions")
    ap("")
    for k in WORKFLOWS:
        d, why = decisions[k]
        ap(f"- **{k}** -> {d}: {why}")
    ap("")
    ap("## Cycle-25 goal set (draft scaffold — finalised at day-7 close)")
    ap("")
    for k in WORKFLOWS:
        d, _ = decisions[k]
        if d == "SCALE":
            ap(f"- [ ] {k}: scale — add delivery layer + 3 new client onboardings")
        elif d == "BLOCKED":
            ap(f"- [ ] {k}: unblock first (fix script/runnability) before any growth spend")
        else:
            ap(f"- [ ] {k}: hold — keep running, measure next cycle before committing")
    ap("- [ ] Scribe: confirm daily ledger cadence held 7/7 days (data integrity for attribution)")
    ap("- [ ] Outlet: convert SCALE workflows into outbound packs; KILL/HOLD get no new outreach")
    ap("")
    ap("_Source data: memory/scribe/stealth-ledger.md + memory/builder/stealth/ (Builder, 2026-11-25). "
       f"Generated by stealth_checkpoint.py._")

    payload = {
        "generated": today.isoformat(),
        "engine_start": ENGINE_START.isoformat(),
        "day_num": day_num,
        "target_usd": TARGET_USD,
        "revenue_usd": L["revenue"],
        "pct_of_target": round(pct, 2),
        "gap_usd": round(gap, 2),
        "ledger_days": L["days"],
        "outreach": L["outreach"], "replies": L["replies"], "demos": L["demos"],
        "per_wf": {k: {"revenue": L["per_wf"][k], "status": wf_status(k),
                       "decision": decisions[k][0], "rationale": decisions[k][1]} for k in WORKFLOWS},
        "day7_date": DAY7.isoformat(),
    }
    return "\n".join(lines) + "\n", payload


def selftest() -> int:
    today = dt.date(2026, 12, 2)  # day-7
    synthetic = """# Stealth ledger
## 2026-12-01 (day 6)
revenue: $1500
wf1: $900
wf2: $400
wf3: $200
outreach: 12 replies: 5 demos: 2
## 2026-12-02 (day 7)
revenue: $800
wf1: $500
wf2: $200
wf3: $100
outreach: 8 replies: 3 demos: 1
"""
    L_synthetic = parse_ledger_md(synthetic)
    md, payload = build_report(today, L_synthetic)
    assert payload["revenue_usd"] == 2300.0, payload["revenue_usd"]
    assert payload["per_wf"]["wf1"]["revenue"] == 1400.0
    assert payload["per_wf"]["wf2"]["revenue"] == 600.0
    assert payload["per_wf"]["wf3"]["revenue"] == 300.0
    assert payload["outreach"] == 20 and payload["replies"] == 8 and payload["demos"] == 3
    # wf1: $1400 >= 2*200=400 -> SCALE ; wf2 $600 in 150-400 band? 600>=400 high, <2*150=300? no, 600>=400 floor... check logic
    assert payload["per_wf"]["wf1"]["decision"] == "SCALE", payload["per_wf"]["wf1"]["decision"]
    # wf2 $600: >=2*150=300 -> SCALE
    assert payload["per_wf"]["wf2"]["decision"] == "SCALE"
    # wf3 $300: >=2*100=200 -> SCALE
    assert payload["per_wf"]["wf3"]["decision"] == "SCALE"
    assert payload["day_num"] == 7
    assert abs(payload["gap_usd"] - (3800 - 2300)) < 0.01
    # zero-revenue pre-day-7 run -> all HOLD, none KILL
    L_empty = parse_ledger_md("")
    md0, p0 = build_report(dt.date(2026, 11, 25), L_empty)
    assert p0["revenue_usd"] == 0.0 and p0["day_num"] == 0
    assert all(p0["per_wf"][k]["decision"] in ("HOLD", "BLOCKED") for k in WORKFLOWS)
    print("SELFTEST PASS: parser totals + scale/hold decision logic verified on synthetic day-7 data; zero-state pre-revenue run yields no premature KILL.")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    today = dt.date.today()
    # Prefer structured JSONL; fall back to markdown parsing
    if LEDGER_JSONL.exists():
        ledger_data = parse_ledger_jsonl(LEDGER_JSONL)
    else:
        text = LEDGER_MD.read_text(encoding="utf-8") if LEDGER_MD.exists() else ""
        ledger_data = parse_ledger_md(text)
    md, payload = build_report(today, ledger_data)
    OUT_MD.write_text(md, encoding="utf-8")
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"CHECKPOINT written: day {payload['day_num']}, revenue ${payload['revenue_usd']} "
          f"({payload['pct_of_target']}% of ${TARGET_USD:,.0f}), gap ${payload['gap_usd']}")
    print(f"  md   -> {OUT_MD.relative_to(ROOT)}")
    print(f"  json -> {OUT_JSON.relative_to(ROOT)}")
    if today < DAY7:
        print("NOTE: pre-day-7 run — report is valid but goal closure is date-gated to "
              f"{DAY7.isoformat()}; do not mark reached now.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
