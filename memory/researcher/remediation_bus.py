#!/usr/bin/env python3
"""remediation_bus.py - Self-Healing Remediation Bus

Consumes detector outputs and applies safe, idempotent fixes:
  1. stale_claim_scan  -> flag missing artifacts + write correction notes
  2. dispatch_desync   -> compare autoloop.json open counts vs actual goal files
  3. reach_matrix      -> build agent x goal reach status matrix
  4. clobber-manifest  -> detect recent file clobber events from clobber-events.jsonl

Idempotency: safe to run multiple times; only adds, never deletes or overwrites
existing evidence. Corrections are appended with timestamps so re-runs are no-ops
when nothing new is found.

Usage:
  python memory/researcher/remediation_bus.py --dry-run   # report only
  python memory/researcher/remediation_bus.py             # apply fixes
"""
import json, os, re, sys, datetime, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

def now():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

# --- 1. STALE CLAIM SCAN ---
def run_stale_claim_scan():
    """Run stale_claim_check.py --json and return its output."""
    try:
        r = subprocess.run(
            [sys.executable, "memory/ops/stale_claim_check.py", "--json"],
            capture_output=True, text=True, timeout=60
        )
        if r.returncode == 0:
            return json.loads(r.stdout) if r.stdout.strip() else {"missing": [], "stale": []}
        # Return code 1 = missing claims found; parse stdout anyway
        if r.stdout.strip():
            return json.loads(r.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
        print(f"  [warn] stale_claim_scan failed: {e}")
    return {"missing": [], "stale": []}

def apply_stale_claim_fixes(scan_result, dry_run):
    """Write a correction note for MISSING claims (idempotent: skip if already noted)."""
    missing = scan_result.get("missing", [])
    fixes = []
    corr_path = os.path.join("memory", "researcher", "stale-claim-corrections.md")
    
    new_items = []
    for m in missing:
        ref = m.get("ref", "") if isinstance(m, dict) else str(m)
        # Check if already noted (idempotent guard)
        if os.path.exists(corr_path):
            content = open(corr_path, encoding="utf-8").read()
            if ref in content:
                continue
        new_items.append(f"- MISSING: `{ref}`")
    
    if new_items and not dry_run:
        ts = now()
        header = "# Stale-Claim Corrections (auto-maintained by remediation_bus.py)"
        body = "\n".join(new_items) + "\n"
        if os.path.exists(corr_path):
            with open(corr_path, "a", encoding="utf-8") as f:
                f.write(f"\n## {ts} (remediation_bus append)\n{body}")
        else:
            with open(corr_path, "w", encoding="utf-8") as f:
                f.write(header + "\n\n## " + ts + "\n" + body)
        fixes.append(f"Wrote {len(new_items)} new stale-claim corrections to {corr_path}")
    elif new_items and dry_run:
        fixes.append(f"[DRY] Would write {len(new_items)} stale-claim corrections")
    
    return fixes

# --- 2. DISPATCH DESYNC DETECTOR ---
def detect_dispatch_desync():
    """Compare autoloop.json last_pass 'why' field vs actual open-goal counts."""
    issues = []
    al_path = os.path.join("memory", "ops", "autoloop.json")
    if not os.path.exists(al_path):
        return issues
    
    with open(al_path, encoding="utf-8") as f:
        al = json.load(f)
    
    last_pass = al.get("last_pass", {})
    why = last_pass.get("why", "")
    
    # Parse "agent:N-open" tokens from why string
    tokens = re.findall(r"(\w+):(\d+)-open", why)
    
    # Actual open-goal counts from goal files
    actual = {}
    for agent in ["researcher", "builder", "verifier", "designer",
                  "mechanic", "orchestrator", "archivist", "scribe"]:
        gf = os.path.join("memory", "goals", f"{agent}.md")
        if not os.path.exists(gf):
            continue
        text = open(gf, encoding="utf-8").read()
        # Count goals that don't have a verified/reached marker
        open_count = 0
        for line in text.split("\n"):
            if re.match(r"^\d+\. \*\*", line):
                if "verified:" not in line and "[REACHED" not in line:
                    # Check next few lines for evidence markers too
                    open_count += 1
        actual[agent] = open_count
    
    for agent, claimed_open in tokens:
        real_open = actual.get(agent, None)
        if real_open is not None and int(claimed_open) != real_open:
            issues.append({
                "agent": agent,
                "claimed_open": int(claimed_open),
                "actual_open": real_open,
                "severity": "high" if abs(int(claimed_open) - real_open) > 2 else "low"
            })
    
    return issues

def apply_dispatch_desync_fixes(issues, dry_run):
    """Log desync findings to an ops note (idempotent: only if not already logged today)."""
    fixes = []
    if not issues:
        return fixes
    
    log_path = os.path.join("memory", "ops", "dispatch-desync-log.md")
    ts = now()
    date_str = ts[:10]  # YYYY-MM-DD
    
    # Idempotency: skip if already logged today for same agents
    if os.path.exists(log_path):
        content = open(log_path, encoding="utf-8").read()
        agents_today = {i["agent"] for i in issues}
        if date_str in content and all(a in content for a in agents_today):
            return fixes  # already logged
    
    lines = [f"\n## {ts} dispatch desync (remediation_bus)\n"]
    for iss in issues:
        lines.append(f"- {iss['agent']}: autoloop claims {iss['claimed_open']} open, actual={iss['actual_open']}")
    
    if not dry_run:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("".join(lines))
        fixes.append(f"Logged {len(issues)} dispatch desync issues to {log_path}")
    else:
        fixes.append(f"[DRY] Would log {len(issues)} dispatch desync issues")
    
    return fixes

# --- 3. REACH MATRIX ---
def build_reach_matrix():
    """Build agent x goal reach status matrix from goal files."""
    matrix = {}
    agents = ["researcher", "builder", "verifier", "designer",
              "mechanic", "orchestrator", "archivist", "scribe"]
    
    for agent in agents:
        gf = os.path.join("memory", "goals", f"{agent}.md")
        if not os.path.exists(gf):
            continue
        text = open(gf, encoding="utf-8").read()
        goals = []
        current_goal = None
        for line in text.split("\n"):
            m = re.match(r"^(\d+)\. \*\*(.+?)\*\*", line)
            if m:
                if current_goal:
                    goals.append(current_goal)
                current_goal = {
                    "num": int(m.group(1)),
                    "title": m.group(2).strip(),
                    "reached": False,
                    "evidence": None
                }
            elif current_goal and re.search(r"\(verified:|\[REACHED", line):
                current_goal["reached"] = True
                current_goal["evidence"] = line.strip()[:120]
        if current_goal:
            goals.append(current_goal)
        
        reached = sum(1 for g in goals if g["reached"])
        matrix[agent] = {
            "total": len(goals),
            "reached": reached,
            "open": len(goals) - reached,
            "pct": f"{100*reached/len(goals):.0f}%" if goals else "N/A",
            "goals": goals
        }
    
    return matrix

def apply_reach_matrix_fixes(matrix, dry_run):
    """Write reach matrix as a JSON artifact (idempotent: overwrite is safe)."""
    fixes = []
    out_path = os.path.join("memory", "researcher", "reach-matrix.json")
    ts = now()
    
    summary = {"generated": ts, "matrix": matrix}
    
    if not dry_run:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        total_goals = sum(v["total"] for v in matrix.values())
        total_reached = sum(v["reached"] for v in matrix.values())
        fixes.append(f"Wrote reach-matrix.json ({total_reached}/{total_goals} goals fleet-wide)")
    else:
        total_goals = sum(v["total"] for v in matrix.values())
        total_reached = sum(v["reached"] for v in matrix.values())
        fixes.append(f"[DRY] Would write reach-matrix.json ({total_reached}/{total_goals} goals)")
    
    return fixes

# --- 4. CLOBBER MANIFEST ---
def detect_clobber_events():
    """Parse clobber-events.jsonl for recent events (last 24h)."""
    events = []
    cl_path = os.path.join("memory", "ops", "clobber-events.jsonl")
    if not os.path.exists(cl_path):
        return events
    
    cutoff = datetime.datetime.now() - datetime.timedelta(hours=24)
    try:
        with open(cl_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                    # clobber-events.jsonl may have a different schema; handle flexibly
                    ts_str = ev.get("timestamp", ev.get("ts", ""))
                    if ts_str:
                        try:
                            ev_ts = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00")).replace(tzinfo=None)
                            if ev_ts >= cutoff:
                                events.append(ev)
                        except (ValueError, TypeError):
                            pass
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"  [warn] clobber manifest read failed: {e}")
    
    return events

def apply_clobber_fixes(events, dry_run):
    """Log recent clobber events to a manifest summary (idempotent)."""
    fixes = []
    if not events:
        return fixes
    
    out_path = os.path.join("memory", "researcher", "clobber-manifest-summary.md")
    ts = now()
    
    # Idempotency: check if same event count already logged today
    date_str = ts[:10]
    if os.path.exists(out_path):
        content = open(out_path, encoding="utf-8").read()
        marker = f"## {date_str}"
        if marker in content:
            return fixes  # already logged today
    
    lines = [f"\n## {ts} clobber manifest (remediation_bus)\n"]
    lines.append(f"- {len(events)} clobber event(s) in last 24h\n")
    
    if not dry_run:
        with open(out_path, "a", encoding="utf-8") as f:
            f.write("".join(lines))
        fixes.append(f"Logged {len(events)} clobber events to manifest summary")
    else:
        fixes.append(f"[DRY] Would log {len(events)} clobber events")
    
    return fixes

# --- MAIN ---
def main():
    dry_run = "--dry-run" in sys.argv
    
    print("=" * 60)
    print(f"  REMEDIATION BUS - {now()} {'(DRY RUN)' if dry_run else '(APPLY)'}")
    print("=" * 60)
    
    all_fixes = []
    
    # 1. Stale claim scan
    print("\n[1/4] Stale-Claim Scan...")
    scan = run_stale_claim_scan()
    missing_count = len(scan.get("missing", []))
    stale_count = len(scan.get("stale", []))
    print(f"  Found: {missing_count} MISSING, {stale_count} STALE claims")
    all_fixes.extend(apply_stale_claim_fixes(scan, dry_run))
    
    # 2. Dispatch desync
    print("\n[2/4] Dispatch Desync Check...")
    desync = detect_dispatch_desync()
    print(f"  Found: {len(desync)} desync issue(s)")
    all_fixes.extend(apply_dispatch_desync_fixes(desync, dry_run))
    
    # 3. Reach matrix
    print("\n[3/4] Reach Matrix...")
    matrix = build_reach_matrix()
    total_g = sum(v["total"] for v in matrix.values())
    total_r = sum(v["reached"] for v in matrix.values())
    print(f"  Fleet: {total_r}/{total_g} goals reached")
    all_fixes.extend(apply_reach_matrix_fixes(matrix, dry_run))
    
    # 4. Clobber manifest
    print("\n[4/4] Clobber Manifest...")
    clobbers = detect_clobber_events()
    print(f"  Found: {len(clobbers)} recent clobber event(s)")
    all_fixes.extend(apply_clobber_fixes(clobbers, dry_run))
    
    # Summary
    print("\n" + "=" * 60)
    print("  REMEDIATION SUMMARY")
    print("=" * 60)
    if all_fixes:
        for f in all_fixes:
            print(f"  - {f}")
    else:
        print("  No fixes needed (all clean or already applied).")
    
    # Write run log (idempotent append)
    if not dry_run:
        log_path = os.path.join("memory", "researcher", "remediation-bus-log.jsonl")
        entry = {
            "ts": now(),
            "mode": "apply",
            "fixes_applied": len(all_fixes),
            "stale_missing": missing_count,
            "dispatch_desync": len(desync),
            "fleet_reached": f"{total_r}/{total_g}",
            "clobber_events_24h": len(clobbers)
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    
    print(f"\n  Exit: {len(all_fixes)} fix(es) {'would apply' if dry_run else 'applied'}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
