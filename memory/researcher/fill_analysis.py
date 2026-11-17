"""
fill_analysis.py — Researcher goal #3: auto-fill the analysis template from live mirror data.
Usage: python memory/researcher/fill_analysis.py [log_path] [--dry-run]
  --dry-run : print to stdout instead of writing file
Output: memory/researcher/mirror-revert-analysis-YYYY-MM-DD.md (completed leaf)
This makes day-7 closure a single command.
"""
import json, sys, os, re
from collections import Counter
from datetime import datetime

def _parse_ts(s):
    """Tolerant timestamp parse for the confidence line. The writer currently emits
    '%Y-%m-%d %H:%M:%S'; if a future mirror edit changes that (microseconds, ISO-T,
    etc.) day-7 one-command closure must DEGRADE (confidence->LOW) not CRASH.
    Returns None on any unparseable value."""
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S.%f'):
        try:
            return datetime.strptime(s, fmt)
        except (ValueError, TypeError):
            continue
    return None

def load_live_events(path):
    events = []
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get('_test'): continue
            events.append(ev)
    return events

def build_analysis(events, log_path):
    ts = [ev['t'] for ev in events if 't' in ev]
    t_min, t_max = min(ts), max(ts)
    total = len(events)

    # By kind
    kind_counts = Counter(ev.get('kind','?') for ev in events)
    # By (kind, dir/trigger)
    kind_sub = Counter((ev.get('kind','?'), ev.get('dir', ev.get('trigger','?'))) for ev in events)
    # Top reverting files
    path_counts = Counter()
    revert_triggers_by_path = {}
    for ev in events:
        p = ev.get('path', ev.get('file', '?'))
        path_counts[p] += 1
        if ev.get('kind') == 'revert':
            trigger = ev.get('trigger','unknown')
            revert_triggers_by_path.setdefault(p, Counter())[trigger] += 1
    # Top-3 reverting (only reverts)
    revert_paths = Counter(ev.get('path', ev.get('file','?')) for ev in events if ev.get('kind')=='revert')
    top3_reverting = revert_paths.most_common(3)
    # Hourly
    hourly = Counter()
    for ev in events:
        if 't' in ev:
            try:
                dt = datetime.strptime(ev['t'], '%Y-%m-%d %H:%M:%S')
                hourly[dt.strftime('%Y-%m-%d %H:00')] += 1
            except ValueError: pass
    # Trigger distribution (reverts)
    trigger_dist = Counter(ev.get('trigger','?') for ev in events if ev.get('kind')=='revert')
    # Write-reason distribution (why copies happen: new / white-canonical / lww-newer)
    reason_dist = Counter(ev.get('reason','?') for ev in events if ev.get('kind')=='write' and 'reason' in ev)

    # Build markdown
    today = datetime.now().strftime('%Y-%m-%d')
    lines = []
    lines.append(f"# Mirror-Revert Frequency Analysis (goal #3)")
    lines.append(f"\nGenerated: {today} by fill_analysis.py")
    lines.append(f"\n## Data Source")
    lines.append(f"- Log: {log_path}")
    lines.append(f"- Live event window: {t_min} to {t_max}")
    lines.append(f"- Total live events: {total}")
    lines.append(f"- Parse command used: `python memory/researcher/parse_mirror_events.py {log_path}`")
    lines.append(f"\n## Frequency Table")
    lines.append(f"\n### By kind")
    lines.append(f"| kind | count | pct |")
    lines.append(f"|------|-------|-----|")
    for k, c in kind_counts.most_common():
        lines.append(f"| {k} | {c} | {100*c/total:.1f}% |")
    lines.append(f"\n### By (kind, dir/trigger)")
    lines.append(f"| kind | sub | count |")
    lines.append(f"|------|-----|-------|")
    for (k,s), c in kind_sub.most_common():
        lines.append(f"| {k} | {s} | {c} |")
    lines.append(f"\n### Top-3 reverting files")
    lines.append(f"| path | revert count | trigger | notes |")
    lines.append(f"|------|-------------|---------|-------|")
    for p, c in top3_reverting:
        trig = ' / '.join(f"{t}({n})" for t,n in revert_triggers_by_path.get(p,{}).most_common())
        lines.append(f"| {p} | {c} | {trig} | [REVIEW] |")
    if not top3_reverting:
        lines.append(f"| (no reverts observed) | 0 | - | - |")
    lines.append(f"\n### Hourly distribution")
    for h, c in sorted(hourly.items()):
        bar = '#' * min(c, 40)
        lines.append(f"`{h}: {c:3d} {bar}`")
    if reason_dist:
        lines.append(f"\n## Write Reason Distribution")
        total_w = sum(reason_dist.values())
        lines.append(f"| reason | count | pct | notes |")
        lines.append(f"|--------|-------|-----|-------|")
        for r, c in reason_dist.most_common():
            lines.append(f"| {r} | {c} | {100*c/total_w:.1f}% | [REVIEW] |")
    lines.append(f"\n## Revert Trigger Distribution")
    total_reverts = sum(trigger_dist.values())
    for t, c in trigger_dist.most_common():
        pct = 100*c/max(total_reverts,1)
        lines.append(f"- **{t}**: {c} ({pct:.1f}%)")
    lines.append(f"\n## Mechanism Assessment")
    lines.append(f"- Pin_drift dominant? {'YES' if trigger_dist.get('pin_drift',0) > 0.5*sum(trigger_dist.values()) else 'NO'} (pin_drift = {trigger_dist.get('pin_drift',0)}/{sum(trigger_dist.values())} reverts)")
    lines.append(f"- NEW triggers beyond cycle-2 known set? [REVIEW: check list above vs cycle-2 baseline]")
    lines.append(f"- Correlation with agent activity: [REVIEW if applicable]")
    lines.append(f"\n## Targeted Fixes (beyond auto-repair daemon)")
    lines.append(f"\n### Fix 1: Pin-stability guard")
    lines.append(f"Mechanism: pre-write hash check at push_root/push_mem; skip + warn if pinned file drifts.")
    lines.append(f"Implementation hint: sha256 comparison before overwrite; see memory_mirror.py PIN_FILES.")
    lines.append(f"Effort: Low")
    lines.append(f"\n### Fix 2: Per-file epoch stamping (from goal #1 spec)")
    lines.append(f"Mechanism: reject stale writes via per-file epoch in .meta.json.")
    lines.append(f"Implementation hint: memory/researcher/sync-semantics-spec-2026-11-17.md")
    lines.append(f"Effort: Medium")
    lines.append(f"\n### Fix 3: [REVIEW if data reveals third mechanism]")
    lines.append(f"Mechanism: [FILL] | Implementation hint: [FILL] | Effort: [FILL]")
    lines.append(f"\n## Confidence + Residual Uncertainty")
    d_max, d_min = _parse_ts(t_max), _parse_ts(t_min)
    if d_max is not None and d_min is not None:
        days = (d_max - d_min).days + 1
        conf = 'HIGH' if days >= 6 and total >= 50 else ('MEDIUM' if days >= 3 and total >= 20 else 'LOW')
    else:
        # Unparseable timestamps: degrade, don't crash the single-command closure.
        days = -1
        conf = 'LOW'
        lines.append(f"- WARN: timestamp format unrecognised ({t_min!r}); confidence forced LOW.")
    lines.append(f"- Dataset: {total} events / {days} days -> confidence: **{conf}**")
    lines.append(f"- Known limitations: [REVIEW - e.g. shorter than 7-day window]")
    lines.append(f"- What would change this analysis: [REVIEW]")
    lines.append(f"\n## Cross-references")
    lines.append(f"- Instrumentation: memory/researcher/mirror-revert-instrumentation-2026-11-17.md")
    lines.append(f"- Pipeline validation: memory/researcher/mirror-revert-pipeline-validation-2026-11-17.md")
    lines.append(f"- Closure runbook + contingency: memory/researcher/mirror-revert-closure-runbook-2026-11-17.md")
    lines.append(f"- Sync semantics spec (goal #1): memory/researcher/sync-semantics-spec-2026-11-17.md")

    return '\n'.join(lines)

def main():
    dry = '--dry-run' in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    log_path = args[0] if args else 'Z:\\mirror_events.log'
    events = load_live_events(log_path)
    if not events:
        print("No live events yet. Cannot generate analysis.")
        sys.exit(1)
    md = build_analysis(events, log_path)
    if dry:
        print(md)
    else:
        out = f"memory/researcher/mirror-revert-analysis-{datetime.now().strftime('%Y-%m-%d')}.md"
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, 'w') as f:
            f.write(md)
        print(f"Wrote {out} ({len(md)} chars, {len(events)} events)")

if __name__ == '__main__':
    main()
