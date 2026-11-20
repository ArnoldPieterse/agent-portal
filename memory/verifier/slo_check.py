#!/usr/bin/env python3
"""slo_check.py (cycle-8 goal #8, Verifier): daily SLO enforcement.

SLOs:
  - p95 /api/chat  < 30 s
  - p95 /api/file  <  5 s
  - uptime         > 99 %

Data source: GET /api/perf (60-min rolling window) + GET /api/uptime.
Output: memory/ops/slo-YYYY-MM-DD.md  (PASS/BREACH per SLO line).
Exit codes: 0 = all pass, 1 = one or more BREACH, 2 = data source unreachable,
            3 = invalid/incomplete perf data.

--simulate MODE|BREACH  run against synthetic data for logic verification
                        (no :8099 access needed)."""
import json, sys, os, datetime, urllib.request, argparse

PORTAL = "http://127.0.0.1:8099"
SLO_CHAT_P95_MS  = 30_000   # 30 s
SLO_FILE_P95_MS  =  5_000   #  5 s
SLO_UPTIME_PCT   =  99.0    # percent

def fetch_json(path, timeout=15):
    with urllib.request.urlopen(PORTAL + path, timeout=timeout) as r:
        return json.loads(r.read())

def collect_live():
    """Return (chat_p95, file_p95, uptime_pct) from live portal."""
    perf = fetch_json("/api/perf")
    chat_p95 = file_p95 = None
    for e in perf.get("endpoints", []):
        if e["path"] == "/api/chat":
            chat_p95 = e.get("p95_ms")
        elif e["path"] == "/api/file":
            file_p95 = e.get("p95_ms")
    try:
        up = fetch_json("/api/uptime")
        uptime_pct = up.get("uptime_pct", up.get("uptime_percent"))
    except Exception:
        uptime_pct = None
    return chat_p95, file_p95, uptime_pct

def collect_simulate(mode="PASS"):
    """Synthetic data for logic verification."""
    if mode == "PASS":
        return 1_200, 800, 99.7   # well within SLOs
    elif mode == "BREACH_CHAT":
        return 45_000, 800, 99.7  # chat p95 over 30 s
    elif mode == "BREACH_FILE":
        return 1_200, 12_000, 99.7  # file p95 over 5 s
    elif mode == "BREACH_UPTIME":
        return 1_200, 800, 97.2   # uptime below 99 %
    elif mode == "BREACH_ALL":
        return 60_000, 20_000, 95.0
    else:
        raise ValueError(f"unknown simulate mode: {mode}")

def evaluate(chat_p95, file_p95, uptime_pct):
    """Return list of (label, value_str, threshold_str, passed) tuples."""
    rows = []
    def ms(v): return f"{v:,} ms" if v is not None else "N/A"
    # chat p95
    ok = chat_p95 is not None and chat_p95 < SLO_CHAT_P95_MS
    rows.append(("p95 /api/chat", ms(chat_p95), f"< {SLO_CHAT_P95_MS:,} ms", ok))
    # file p95
    ok = file_p95 is not None and file_p95 < SLO_FILE_P95_MS
    rows.append(("p95 /api/file", ms(file_p95), f"< {SLO_FILE_P95_MS:,} ms", ok))
    # uptime
    ok = uptime_pct is not None and uptime_pct > SLO_UPTIME_PCT
    rows.append(("uptime", f"{uptime_pct:.2f}%" if uptime_pct is not None else "N/A",
                 f"> {SLO_UPTIME_PCT} %", ok))
    return rows

def write_report(rows, source="live"):
    today = datetime.date.today().isoformat()
    os.makedirs("memory/ops", exist_ok=True)
    path = f"memory/ops/slo-{today}.md"
    breaches = [r[0] for r in rows if not r[3]]
    verdict = "PASS" if not breaches else f"BREACH ({', '.join(breaches)})"
    lines = [
        f"# SLO Check Report - {today}",
        f"",
        f"Source: {source}  |  Generated: {datetime.datetime.now().isoformat(timespec='seconds')}",
        f"",
        f"| SLO | Value | Threshold | Status |",
        f"|-----|-------|-----------|--------|",
    ]
    for label, val, thresh, ok in rows:
        lines.append(f"| {label} | {val} | {thresh} | {'PASS' if ok else '**BREACH**'} |")
    lines += [f"", f"**Verdict: {verdict}**", ""]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path, verdict

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--simulate", nargs="?", const="PASS",
                    help="Run against synthetic data (PASS|BREACH_CHAT|BREACH_FILE|BREACH_UPTIME|BREACH_ALL)")
    args = ap.parse_args()

    if args.simulate:
        chat_p95, file_p95, uptime_pct = collect_simulate(args.simulate)
        source = f"simulate:{args.simulate}"
    else:
        try:
            chat_p95, file_p95, uptime_pct = collect_live()
            source = "live"
        except Exception as e:
            print(f"slo_check: data source unreachable: {e}", file=sys.stderr)
            sys.exit(2)

    rows = evaluate(chat_p95, file_p95, uptime_pct)
    path, verdict = write_report(rows, source)
    print(f"slo_check: {verdict}  ->  {path}")
    for label, val, thresh, ok in rows:
        print(f"  {'OK ' if ok else 'BREACH'} {label}: {val} (threshold {thresh})")
    sys.exit(0 if verdict == "PASS" else 1)

if __name__ == "__main__":
    main()
