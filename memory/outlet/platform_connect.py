#!/usr/bin/env python3
"""Outlet Platform Connection helper + runbook auditor (goal #10).

Companion to memory/outlet/platform-connection-runbook.md. Two jobs:
  1) Pre-wire the fleet-default profile + verify a platform is "wired" without printing secrets.
  2) Audit the runbook: every step must be a runnable command OR a [HUMAN] action.

Subcommands:
  register --platform P --handle H   upsert the live row in memory/outlet/profiles.md (idempotent; no secrets)
  wired-check [--platform P]         verify wiring present; prints OK/MISSING, NEVER the secret value
  audit-runbook                      parse the runbook, assert every step is command|[HUMAN]; exit 0 iff PASS
  selftest                           isolated temp-dir proof of register idempotency + real audit

Secrets live in memory/outlet/.secrets/<platform>.txt (0600). This tool reads PRESENCE only.
"""
import argparse, os, re, sys, stat, tempfile, pathlib, json

HERE = pathlib.Path(__file__).resolve().parent          # memory/outlet
PROFILES = HERE / "profiles.md"
SECRETS = HERE / ".secrets"
RUNBOOK = HERE / "platform-connection-runbook.md"

CMD_RE = re.compile(r"^(?:\s*[-*]\s+)?(?:python[0-9.]*|py|elev\.py|schtasks|git|bsky|ls|test|true|false|printenv)\b")
STEP_NUM_RE = re.compile(r"^\s*(?:\d+[.)]|[-*])\s+(.*)$")


def _read_profiles():
    return PROFILES.read_text(encoding="utf-8")


def register(platform, handle):
    """Idempotently mark the fleet-default template row as connected for `platform`."""
    text = _read_profiles()
    plat_l = platform.lower()
    lines = [ln.rstrip("\n") for ln in text.splitlines()]
    flipped = False
    new_lines = []
    for ln in lines:
        cells = [c.strip() for c in ln.split("|")]
        if cells and plat_l in " ".join(cells).lower() and any("TEMPLATE" in c.upper() for c in cells):
            kept = ln.split("|")[:-1]                    # drop trailing empty after final |
            new_lines.append("|".join([' connected (pre-wired by outlet) ' if 'TEMPLATE' in c.upper() else c for c in ln.split('|')]))
            flipped = True
        else:
            new_lines.append(ln)
    if flipped:
        PROFILES.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        print(f"registered {platform} {handle}: TEMPLATE row -> connected in profiles.md")
    else:
        if "connected (pre-wired by outlet)" in text and plat_l in text.lower():
            print(f"{platform} {handle}: already connected (no change)")
            return
        line = (f"| FLEET-LIVE | {platform} | {handle} | fleet default | 1 post/wk + replies as-needed "
                f"| no internal details | connected (pre-wired by outlet) |")
        PROFILES.write_text(_read_profiles().rstrip() + "\n" + line + "\n", encoding="utf-8")
        print(f"registered new live row for {platform} {handle} in profiles.md")


def wired_check(platform):
    SECRETS.mkdir(exist_ok=True)
    f = SECRETS / (platform.lower() + ".txt")
    if f.exists() and f.stat().st_size > 0:
        print(f"wired-check {platform}: OK (secret present at .secrets/{f.name}; value not shown)")
        return True
    print(f"wired-check {platform}: MISSING (no .secrets/{f.name})")
    return False


def audit_runbook():
    if not RUNBOOK.exists():
        print(f"NO runbook at {RUNBOOK}")
        return 1
    lines = RUNBOOK.read_text(encoding="utf-8").splitlines()
    steps, bad = [], []
    for ln in lines:
        m = STEP_NUM_RE.match(ln)
        if not m:
            continue
        content = m.group(1).strip().strip("`")
        if not content:
            continue
        is_cmd = bool(CMD_RE.match(content))
        is_human = "[HUMAN]" in content.upper()
        steps.append((content, is_cmd or is_human))
        if not (is_cmd or is_human):
            bad.append(content)
    total = len(steps)
    ok = total > 0 and not bad
    print(f"audit-runbook: {total} step(s), command-or-HUMAN {sum(1 for _, k in steps if k)}, PROSE_ONLY {len(bad)}")
    for b in bad:
        print("   PROSE_ONLY:", b[:80])
    print("audit-runbook:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def selftest():
    global PROFILES, SECRETS
    saved = (PROFILES, SECRETS)
    with tempfile.TemporaryDirectory() as td:
        tdp = pathlib.Path(td)
        pro = tdp / "profiles.md"
        sec = tdp / ".secrets"
        pro.write_text(
            "| Profile | Platform | Handle | Voice notes | Cadence | Hard lines | Status |\n"
            "|---|---|---|---|---|---|---|\n"
            "| FLEET-TEMPLATE | Bluesky | @fleet.example | fleet default | 1/wk | none | TEMPLATE (fill when connected) |\n",
            encoding="utf-8")
        PROFILES, SECRETS = pro, sec
        try:
            register("bluesky", "@fleet.example")
            t1 = pro.read_text(encoding="utf-8")
            assert "TEMPLATE (fill when connected)" not in t1 and "connected" in t1, "register did not mark live"
            n_before = t1.count("connected (pre-wired by outlet)")
            register("bluesky", "@fleet.example")
            t2 = pro.read_text(encoding="utf-8")
            assert t2.count("connected (pre-wired by outlet)") == n_before, "register not idempotent"
            sec.mkdir(exist_ok=True)
            ok_missing = not wired_check("bluesky")
            (sec / "bluesky.txt").write_text("x" * 20, encoding="utf-8")
            os.chmod(str(sec / "bluesky.txt"), stat.S_IRUSR | stat.S_IWUSR)
            ok_present = wired_check("bluesky")
        finally:
            PROFILES, SECRETS = saved
    rc_audit = audit_runbook()  # audit the REAL runbook (must exist + pass)
    res = {"register_marks_live": True, "register_idempotent": True,
           "wired_missing_flagged": ok_missing, "wired_present_ok": ok_present,
           "audit_runbook_pass": rc_audit == 0}
    print(json.dumps(res, indent=2))
    good = all(res.values())
    print("SELFTEST", "PASS" if good else "FAIL")
    return 0 if good else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("register"); r.add_argument("--platform", required=True); r.add_argument("--handle", required=True)
    wc = sub.add_parser("wired-check"); wc.add_argument("--platform", default="bluesky")
    sub.add_parser("audit-runbook")
    sub.add_parser("selftest")
    args = ap.parse_args()
    if args.cmd == "register":
        register(args.platform, args.handle); return 0
    if args.cmd == "wired-check":
        return 0 if wired_check(args.platform) else 1
    if args.cmd == "audit-runbook":
        return audit_runbook()
    if args.cmd == "selftest":
        return selftest()
    ap.print_help(); return 2


if __name__ == "__main__":
    sys.exit(main())
