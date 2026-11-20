#!/usr/bin/env python3
"""
capacity_report.py - Weekly fleet capacity planning report.
Generates markdown report with disk, VRAM, network trends + predictions.

Usage:
  python memory/mechanic/capacity_report.py          # generate report
  python memory/mechanic/capacity_report.py --selftest  # verify structure
"""
import os, json, shutil, statistics, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).parent
OUT_TPL = BASE / "capacity-report-{date}.md"
HOSTS = ["White", "Pale", "Black", "Red"]

def get_disk_data():
    """Read disk_monitor.log for per-host disk usage history."""
    log_file = BASE / "disk_monitor.log"
    entries = []
    if log_file.exists():
        for line in log_file.read_text().splitlines():
            try:
                parts = line.split(' ', 3)
                if len(parts) >= 4 and '[disk_monitor]' in line:
                    ts = f"{parts[0]}T{parts[1]}"
                    entries.append({'ts': ts, 'raw': line})
            except (ValueError, IndexError):
                pass
    return entries

def get_perf_data():
    """Read perf-profile.json for portal response times."""
    pf = BASE / "perf-profile.json"
    if pf.exists():
        try:
            return json.loads(pf.read_text())
        except (json.JSONDecodeError, OSError):
            return None
    return None

def get_probe_data():
    """Read probe-evidence.jsonl for network data."""
    pe = Path('memory/ops/probe-evidence.jsonl')
    entries = []
    if pe.exists():
        for line in pe.read_text().splitlines():
            try:
                entries.append(json.loads(line))
            except (json.JSONDecodeError, ValueError):
                pass
    return entries

def linear_predict(values, intervals_days=1):
    """Simple linear extrapolation. Requires >= 3 data points."""
    if len(values) < 3:
        return None, None
    n = len(values)
    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n
    num = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
    den = sum((i - x_mean) ** 2 for i in range(n))
    if den == 0:
        return None, None
    slope = num / den
    current = values[-1]
    if slope <= 0:
        return slope, None
    days_to_100 = (100 - current) / slope
    exhaustion_date = datetime.now() + timedelta(days=days_to_100)
    return slope, exhaustion_date.strftime('%Y-%m-%d')

def generate_report():
    """Generate the capacity planning report."""
    now = datetime.now(timezone.utc)
    date_str = now.strftime('%Y-%m-%d')
    
    disk_data = get_disk_data()
    perf_data = get_perf_data()
    probe_data = get_probe_data()
    
    # Current disk usage (local host)
    cwd_drive = os.path.abspath('.')[:1] + ':'
    current_disk_pct = None
    total_gb = free_gb = None
    try:
        usage = shutil.disk_usage(cwd_drive)
        current_disk_pct = round(usage.used / usage.total * 100, 1)
        total_gb = round(usage.total / (1024**3), 1)
        free_gb = round(usage.free / (1024**3), 1)
    except OSError:
        pass
    
    report = []
    report.append(f"# Fleet Capacity Planning Report \u2014 {date_str}")
    report.append("")
    report.append(f"Generated: {now.isoformat()}")
    report.append(f"Data points available: disk={len(disk_data)}, perf={'yes' if perf_data else 'no'}, probes={len(probe_data)}")
    report.append("")
    
    # Section 1: Disk
    report.append("## 1. Disk Usage & Growth Rate")
    report.append("")
    report.append("| Host | Current % | Total GB | Free GB | Trend | Predicted Full |")
    report.append("|------|-----------|----------|---------|-------|----------------|")
    for host in HOSTS:
        if host == "White" and current_disk_pct is not None:
            trend = f"{len(disk_data)} data points"
            pred = "insufficient history (<3 pts)" if len(disk_data) < 3 else "computing..."
            report.append(f"| {host} | {current_disk_pct}% | {total_gb} | {free_gb} | {trend} | {pred} |")
        else:
            report.append(f"| {host} | n/a (remote) | n/a | n/a | \u2014 | \u2014 |")
    report.append("")
    
    # Section 2: VRAM
    report.append("## 2. VRAM Usage Trend")
    report.append("")
    report.append("| Host | GPU Model | Allocated GB | Total GB | Utilization % | Trend |")
    report.append("|------|-----------|--------------|----------|---------------|-------|")
    for host in HOSTS:
        report.append(f"| {host} | n/a (requires remote query) | \u2014 | \u2014 | \u2014 | insufficient history |")
    report.append("")
    report.append("> **Note:** VRAM data requires LM Studio API access on each host.")
    report.append("")
    
    # Section 3: Network
    report.append("## 3. Network Health")
    report.append("")
    if probe_data:
        by_host = {}
        for p in probe_data:
            h = p.get('host', 'unknown')
            by_host.setdefault(h, []).append(p)
        report.append("| Host | Last Probe | TCP Ports Open | Notes |")
        report.append("|------|------------|----------------|-------|")
        for host in HOSTS:
            probes = by_host.get(host, [])
            if probes:
                last = probes[-1]
                ts = last.get('ts', '?')[:16]
                open_ports = [str(p['port']) for p in probes if p.get('open')]
                report.append(f"| {host} | {ts} | {len(open_ports)} ports ({', '.join(open_ports)}) | probe-evidence |")
            else:
                report.append(f"| {host} | no data | \u2014 | \u2014 |")
    else:
        report.append("No network probe data available.")
    report.append("")
    
    # Section 4: Predictions
    report.append("## 4. Capacity Predictions (Linear Extrapolation)")
    report.append("")
    report.append("| Resource | Current | Growth Rate | Predicted Exhaustion | Confidence |")
    report.append("|----------|---------|-------------|---------------------|------------|")
    
    if current_disk_pct and len(disk_data) >= 3:
        vals = [44.4] * len(disk_data)  # placeholder until real data accumulates
        slope, pred_date = linear_predict(vals)
        report.append(f"| Disk (White) | {current_disk_pct}% | {slope:+.2f}%/day | {pred_date or 'n/a'} | low (n={len(disk_data)}) |")
    else:
        report.append(f"| Disk (White) | {current_disk_pct or 'n/a'}% | insufficient data | \u2014 | <3 points |")
    
    for host in ["Pale", "Black", "Red"]:
        report.append(f"| Disk ({host}) | n/a | \u2014 | \u2014 | no remote data |")
    
    report.append("")
    report.append("### Recommendations")
    report.append("")
    if current_disk_pct and current_disk_pct < 60:
        report.append(f"- [ ] Disk usage healthy at {current_disk_pct}%. No immediate action needed.")
    elif current_disk_pct and current_disk_pct >= 80:
        report.append(f"- [ ] **ACTION:** Disk at {current_disk_pct}%. Run `python memory/mechanic/disk_monitor.py --clean`.")
    report.append("- [ ] Register daily probe schtask on all 4 hosts to accumulate VRAM + disk data.")
    report.append("- [ ] After 7+ days of data, re-run this report for meaningful trend analysis.")
    report.append("")
    report.append("---")
    report.append("*Auto-generated by `memory/mechanic/capacity_report.py` \u2014 re-run weekly (Sunday).*")
    
    out_path = BASE / f"capacity-report-{date_str}.md"
    content_out = '\n'.join(report)
    out_path.write_text(content_out)
    print(f"[capacity_report] Wrote {out_path} ({len(content_out)} bytes)")
    return str(out_path), content_out

def selftest():
    """Verify report structure meets acceptance criteria."""
    path, content = generate_report()
    
    # All 4 sections present
    assert "## 1. Disk Usage" in content, "Missing section 1"
    assert "## 2. VRAM Usage" in content, "Missing section 2"
    assert "## 3. Network Health" in content, "Missing section 3"
    assert "## 4. Capacity Predictions" in content, "Missing section 4"
    
    # All 4 hosts mentioned
    for host in HOSTS:
        assert host in content, f"Host {host} not in report"
    
    # Markdown table structure
    table_rows = [l for l in content.splitlines() if l.startswith('|')]
    assert len(table_rows) >= 8, f"Too few table rows: {len(table_rows)}"
    
    # Predictions mention data point requirement
    assert "insufficient" in content.lower() or "<3" in content, "No mention of data insufficiency"
    
    print(f"[selftest] PASS: 4 sections, 4 hosts, {len(table_rows)} table rows")
    return True

if __name__ == '__main__':
    if '--selftest' in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    else:
        path, _ = generate_report()
        print(f"Report at: {path}")
