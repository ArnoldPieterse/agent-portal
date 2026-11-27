#!/usr/bin/env python3
"""Outlet Hard Verification Gate (goal #4).

Blocks posts with FAILED/CONTRADICTED factual claims from reaching ready-for-human
state. Distinguishes between:
  - VERIFIED: claim checked and confirmed -> PASS
  - PENDING: claim awaiting Verifier sign-off -> PASS (normal for new posts)
  - FAILED / FALSE / UNVERIFIED / CONTRADICTED: claim actively contradicted -> BLOCK

Usage:
  python memory/outlet/verify_gate.py             # check all queue entries
  python memory/outlet/verify_gate.py selftest    # prove block + pass in temp dir

Gate log: memory/outlet/gate-log.jsonl (one entry per run, per post)
"""
import json, sys, re, datetime, pathlib

HERE = pathlib.Path(__file__).resolve().parent
QUEUE = HERE / "queue"
GATE_LOG = HERE / "gate-log.jsonl"

# Claim status keywords that indicate a BLOCKED state
BLOCK_STATUSES = {"failed", "false", "unverified", "contradicted", "refuted", "incorrect"}
# Claim status keywords that are PASS (normal states)
PASS_STATUSES = {"verified", "pending", "source", "high", "confirmed"}


def _ts():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _log(entry):
    GATE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(GATE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": _ts(), **{k: str(v) if not isinstance(v, (str,int,float,bool,list)) else v for k,v in entry.items()}}) + "\n")


def parse_claims(text):
    """Extract fact-check claims and their status from a post.
    
    Looks for lines like:
      - claim 'X' -> source: Y (confidence: verified)
      - claim 'X' -> VERIFIED by Verifier 2026-11-26
      - PENDING Verifier sign-off on the pct figure before ship.
      - claim 'X' -> FAILED (contradicted by source Z)
    
    Returns list of {claim, status, raw}.
    """
    claims = []
    # Find the fact-check section
    fc_match = re.search(r'fact-check:\s*\n(.*?)(?=\n##|\Z)', text, re.DOTALL)
    if not fc_match:
        return claims
    
    fc_block = fc_match.group(1)
    for line in fc_block.splitlines():
        line = line.strip()
        if not line or not line.startswith('-'):
            continue
        content = line.lstrip('-').strip()
        # Determine status from keywords in the line
        lower = content.lower()
        
        status = "pending"  # default: unmarked claims are pending
        for bs in BLOCK_STATUSES:
            if bs in lower:
                status = bs
                break
        if status == "pending":
            for ps in PASS_STATUSES:
                if ps in lower:
                    status = ps
                    break
        
        # Extract claim text (between quotes or before '->')
        quote_match = re.search(r"claim\s*'(.+?)'", content)
        if quote_match:
            claim_text = quote_match.group(1)
        else:
            arrow_split = content.split('->')
            claim_text = arrow_split[0].strip()[:80] if '->' in content else content[:80]
        
        claims.append({"claim": claim_text, "status": status, "raw": content})
    return claims


def check_post(path):
    """Check one post. Returns {file, blocked, reasons, claims_count, blocked_claims}."""
    text = path.read_text(encoding="utf-8")
    claims = parse_claims(text)
    
    blocked_claims = [c for c in claims if c["status"] in BLOCK_STATUSES]
    blocked = len(blocked_claims) > 0
    reasons = [f"claim BLOCKED ({c['status']}): {c['claim'][:60]}" for c in blocked_claims]
    
    result = {
        "file": path.name,
        "blocked": blocked,
        "reasons": reasons,
        "claims_count": len(claims),
        "blocked_claims": len(blocked_claims),
        "statuses": {c["status"] for c in claims},
    }
    _log({"gate": "verify_gate", **result})
    return result


def run_all():
    """Check all queue entries. Returns (all_pass, results_list)."""
    if not QUEUE.exists():
        return True, []
    results = []
    for fp in sorted(QUEUE.glob("*.md")):
        if fp.name == "INDEX.md":
            continue
        r = check_post(fp)
        results.append(r)
    all_pass = all(not r["blocked"] for r in results)
    return all_pass, results


def selftest():
    """Prove: a post with a FAILED claim is blocked; a post with PENDING claims passes."""
    import tempfile
    from contextlib import redirect_stdout
    import io
    
    results = {"bad_blocked": False, "good_passes": False, "pending_passes": False}
    
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        qd = td / "queue"
        gl = td / "gate-log.jsonl"
        qd.mkdir()
        
        # Post with a FAILED claim (should be BLOCKED)
        bad = ("# Test blocked\ndate: 2026-11-26\nkind: upload\nplatform: fleet-default\n"
               "status: ready-for-human\ntopic: Bad claim\n\n"
               "## Body\nThis claim was proven wrong.\n\n"
               "## Rationale\n- Test post\n\n"
               "## Evidence / sources (for Verifier fact-check before ship)\n- Source X\n\n"
               "fact-check:\n- claim 'fleet has 100 GPUs' -> FAILED (contradicted by seat-matrix.json: only 4 hosts)\n\n"
               "## Notes for ship\n- None\n")
        (qd / "bad.md").write_text(bad, encoding="utf-8")
        
        # Post with PENDING claims (should PASS)
        pending = ("# Test pending\ndate: 2026-11-26\nkind: upload\nplatform: fleet-default\n"
                   "status: ready-for-human\ntopic: Pending verification\n\n"
                   "## Body\nFleet at 27% completion this cycle.\n\n"
                   "## Rationale\n- Test post\n\n"
                   "## Evidence / sources (for Verifier fact-check before ship)\n- goal_ledger.py output\n\n"
                   "fact-check:\n- claim '27% completion' -> PENDING Verifier sign-off (source: goal_ledger.py live output)\n- claim '4 hosts' -> source: seat-matrix.json (confidence: verified)\n\n"
                   "## Notes for ship\n- None\n")
        (qd / "pending.md").write_text(pending, encoding="utf-8")
        
        # Post with VERIFIED claims (should PASS)
        good = ("# Test verified\ndate: 2026-11-26\nkind: upload\nplatform: fleet-default\n"
                "status: ready-for-human\ntopic: Verified claim\n\n"
                "## Body\nWe closed 36 goals this cycle.\n\n"
                "## Rationale\n- Test post\n\n"
                "## Evidence / sources (for Verifier fact-check before ship)\n- goal_ledger.py\n\n"
                "fact-check:\n- claim '36 goals closed' -> VERIFIED by goal_ledger.py 2026-11-26 (live count)\n\n"
                "## Notes for ship\n- None\n")
        (qd / "good.md").write_text(good, encoding="utf-8")
        
        # Run checks
        global QUEUE, GATE_LOG
        saved = (QUEUE, GATE_LOG)
        QUEUE, GATE_LOG = qd, gl
        try:
            r_bad = check_post(qd / "bad.md")
            results["bad_blocked"] = r_bad["blocked"] and len(r_bad["reasons"]) > 0
            
            r_pend = check_post(qd / "pending.md")
            results["pending_passes"] = not r_pend["blocked"]
            
            r_good = check_post(qd / "good.md")
            results["good_passes"] = not r_good["blocked"]
        finally:
            QUEUE, GATE_LOG = saved
    
    print(json.dumps(results, indent=2))
    ok = all(results.values())
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "selftest":
        return selftest()
    
    all_pass, results = run_all()
    for r in results:
        status = "BLOCKED" if r["blocked"] else "PASS"
        print(f"{status:8} {r['file']} (claims={r['claims_count']}, blocked={r['blocked_claims']})")
        for reason in r["reasons"]:
            print(f"         {reason}")
    
    total = len(results)
    blocked = sum(1 for r in results if r["blocked"])
    print(f"\nverify_gate: {total} posts checked, {blocked} blocked")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
