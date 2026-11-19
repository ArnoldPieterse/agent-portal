#!/usr/bin/env python3
"""sla_tracker.py - Daily per-agent SLA report generator (Goal 3: Researcher cycle-7).

SLAs:
  - p95 text response < 30s
  - p95 tool-call response < 60s
  - Host availability > 99% per 24h window

Data sources (in priority order):
  1. memory/ops/portal-request-timings.jsonl  (if portal emits it - NOT YET IMPLEMENTED)
  2. memory/ops/watchdog.log                  (downtime events -> availability proxy)
  3. memory/ops/net-egress-log.jsonl          (probe latency -> host reachability)

Output: memory/ops/sla-report-YYYY-MM-DD.md

Usage:
  python memory/researcher/sla_tracker.py               # today's report
  python memory/researcher/sla_tracker.py --date 2026-11-19
"""
import json, os, re, sys, datetime as dt
from pathlib import Path

OPS_DIR = Path("memory/ops")
WATCHDOG_LOG = OPS_DIR / "watchdog.log"
NET_EGRESS_LOG = OPS_DIR / "net-egress-log.jsonl"
REQUEST_TIMINGS = OPS_DIR / "portal-request-timings.jsonl"  # future: portal emits this

SLA_TEXT_P95_S = 30.0
SLA_TOOL_P95_S = 60.0
SLA_AVAILABILITY_PCT = 99.0


def parse_watchdown_events():
    """Parse watchdog.log for DOWN events with timestamps."""
    events = []
    if not WATCHDOG_LOG.exists():
        return events
    patterns = [
        re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"),  # ISO-like
        re.compile(r"^(\d{2}/\d{1,2}/\d{4} [AP]M)", ),              # Windows format
    ]
    with open(WATCHDOG_LOG, "r", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or "DOWN" not in line:
                continue
            ts = None
            m = patterns[0].match(line)
            if m:
                try:
                    ts = dt.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass
            else:
                m = patterns[1].match(line)
                if m:
                    try:
                        # "16/11/2026 6:44:14 PM" -> parse
                        raw = m.group(1)
                        ts = dt.datetime.strptime(raw, "%d/%m/%Y %I:%M:%S %p")
                    except ValueError:
                        pass
            if ts:
                events.append(ts)
    return sorted(events)


def parse_net_egress(target_date):
    """Parse net-egress-log.jsonl for probes within target_date's 24h window."""
    probes = []
    if not NET_EGRESS_LOG.exists():
        return probes
    day_start = dt.datetime.combine(target_date, dt.time.min)
    day_end = day_start + dt.timedelta(days=1)
    with open(NET_EGRESS_LOG, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts_str = obj.get("ts", "")
            try:
                ts = dt.datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                try:
                    ts = dt.datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue
            if day_start <= ts < day_end:
                probes.append({"ts": ts, "ok": obj.get("ok", False), "ms": obj.get("ms", 0)})
    return probes


def parse_request_timings(target_date):
    """Parse portal-request-timings.jsonl if it exists (future data source)."""
    timings = []
    if not REQUEST_TIMINGS.exists():
        return timings
    day_start = dt.datetime.combine(target_date, dt.time.min)
    day_end = day_start + dt.timedelta(days=1)
    with open(REQUEST_TIMINGS, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts_str = obj.get("ts", "")
            try:
                ts = dt.datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                try:
                    ts = dt.datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue
            if day_start <= ts < day_end:
                timings.append(obj)
    return timings


def percentile(values, p):
    """Compute p-th percentile from a list of numbers."""
    if not values:
        return None
    sorted_v = sorted(values)
    k = (len(sorted_v) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_v) - 1)
    if f == c:
        return sorted_v[f]
    return sorted_v[f] + (sorted_v[c] - sorted_v[f]) * (k - f)


def generate_report(target_date):
    """Generate the daily SLA report."""
    lines = []
    lines.append(f"# SLA Report - {target_date.strftime('%Y-%m-%d')}")
    lines.append("")
    lines.append(f"Generated: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Section 1: Request timing SLAs
    lines.append("## 1. Response-Time SLAs")
    lines.append("")
    timings = parse_request_timings(target_date)
    if timings:
        text_times = [t["duration_s"] for t in timings if t.get("type") == "text"]
        tool_times = [t["duration_s"] for t in timings if t.get("type") == "tool"]
        text_p95 = percentile(text_times, 95)
        tool_p95 = percentile(tool_times, 95)
        lines.append(f"| Metric | Target | Actual (p95) | Status |")
        lines.append(f"|--------|--------|--------------|--------|")
        if text_p95 is not None:
            status = "PASS" if text_p95 < SLA_TEXT_P95_S else "FAIL"
            lines.append(f"| Text p95 | < {SLA_TEXT_P95_S:.0f}s | {text_p95:.1f}s | **{status}** |")
        if tool_p95 is not None:
            status = "PASS" if tool_p95 < SLA_TOOL_P95_S else "FAIL"
            lines.append(f"| Tool-call p95 | < {SLA_TOOL_P95_S:.0f}s | {tool_p95:.1f}s | **{status}** |")
    else:
        lines.append("> **DATA GAP**: Portal does not yet emit per-request timing logs.")
        lines.append("> (expected at `memory/ops/portal-request-timings.jsonl`).")
        lines.append("> Request-level SLA tracking is INACTIVE until that instrumentation lands.")
        lines.append("")

    # Section 2: Availability from watchdog events
    lines.append("## 2. Portal Availability (from watchdog DOWN events)")
    lines.append("")
    down_events = parse_watchdown_events()
    day_start = dt.datetime.combine(target_date, dt.time.min)
    day_end = day_start + dt.timedelta(days=1)
    today_downtime = [e for e in down_events if day_start <= e < day_end]
    total_seconds = 86400.0
    # Each DOWN event implies at minimum a gap until next probe (assume ~5 min recovery)
    estimated_downtime_s = len(today_downtime) * 300.0  # conservative: 5 min per event
    availability_pct = max(0, (total_seconds - estimated_downtime_s) / total_seconds * 100.0)
    status = "PASS" if availability_pct >= SLA_AVAILABILITY_PCT else "FAIL"
    lines.append(f"| Metric | Target | Actual | Status |")
    lines.append(f"|--------|--------|--------|--------|")
    lines.append(f"| Uptime | > {SLA_AVAILABILITY_PCT:.0f}% | ~{availability_pct:.1f}% (est.) | **{status}** |")
    lines.append("")
    lines.append(f"DOWN events in window: {len(today_downtime)}")
    for e in today_downtime:
        lines.append(f"  - {e.strftime('%H:%M:%S')}")
    if not today_downtime:
        lines.append("  (none)")
    lines.append("")

    # Section 3: Host reachability from net-egress probes
    lines.append("## 3. Host Reachability (from fleet probes)")
    lines.append("")
    probes = parse_net_egress(target_date)
    if probes:
        ok_count = sum(1 for p in probes if p["ok"])
        total = len(probes)
        reach_pct = ok_count / total * 100.0 if total else 0
        latencies = [p["ms"] for p in probes if p["ok"] and p["ms"] > 0]
        lat_p95 = percentile(latencies, 95) if latencies else None
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Probes in window | {total} |")
        lines.append(f"| Success rate | {reach_pct:.1f}% |")
        if lat_p95 is not None:
            lines.append(f"| Probe latency p95 | {lat_p95:.0f} ms |")
    else:
        lines.append("> No fleet probes recorded in this window.")
    lines.append("")

    # Section 4: Per-agent breakdown (placeholder until request logs exist)
    lines.append("## 4. Per-Agent Breakdown")
    lines.append("")
    if timings:
        agents = {}
        for t in timings:
            a = t.get("agent", "unknown")
            agents.setdefault(a, []).append(t["duration_s"])
        lines.append(f"| Agent | Requests | p95 (s) | SLA Target | Status |")
        lines.append(f"|-------|----------|---------|------------|--------|")
        for agent, times in sorted(agents.items()):
            p95 = percentile(times, 95)
            target = SLA_TEXT_P95_S if all(t.get("type") == "text" for t in times) else SLA_TOOL_P95_S
            status = "PASS" if p95 < target else "FAIL"
            lines.append(f"| {agent} | {len(times)} | {p95:.1f} | <{target:.0f}s | **{status}** |")
    else:
        lines.append("> Not available (requires `portal-request-timings.jsonl`).")
        lines.append(">")
        lines.append("> **Recommended next step**: Add timing instrumentation to `agent_portal.py` request handler")
        lines.append("> to append `{ts, agent, type, duration_s}` to the JSONL file per request.")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append(f"*Generated by `memory/researcher/sla_tracker.py` | Data sources: watchdog.log, net-egress-log.jsonl*".replace('""', '"'))

    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    target_date = dt.date.today()
    for i, a in enumerate(args):
        if a == "--date":
            try:
                target_date = dt.datetime.strptime(args[i + 1], "%Y-%m-%d").date()
            except (ValueError, IndexError):
                print(f"FATAL: bad --date value", file=sys.stderr)
                return 2

    report = generate_report(target_date)
    out_path = OPS_DIR / f"sla-report-{target_date.strftime('%Y-%m-%d')}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"SLA report written: {out_path}")
    print(report[:500])
    return 0


if __name__ == "__main__":
    sys.exit(main())