#!/usr/bin/env python3
"""Outlet voice linter - checks staged posts against the fleet voice guide.

Runs over memory/outlet/queue/*.md and flags, per Body section:
  1. length cap        -> FAIL if body > HARD_CAP chars (voice: short posts)
  2. banned phrases    -> FAIL on any corporate/hype phrase (voice: never corporate, zero hype)
  3. one-claim heuristic -> WARN only if > MAX_FIGURES distinct numeric figures (voice: one concrete claim)
Exit 1 if any FAIL; warnings do not fail the run.
"""
import re, sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent
QUEUE = HERE / "queue"
HARD_CAP = 600          # hard body length cap (chars). Real milestone post is ~349.
SOFT_CAP = 500          # soft: warn above this, still under the hard cap
MAX_FIGURES = 3         # distinct numeric figures before we WARN about one-claim-per-post
# Corporate / hype phrases banned by the voice guide (never corporate, zero hype).
BANNED = ["synergy", "synergies", "game-changer", "game changer", "cutting-edge",
          "state-of-the-art", "world-class", "best-in-class", "seamless", "groundbreaking",
          "revolutionary", "disruptive", "paradigm shift", "excited to announce",
          "thrilled to share", "we're thrilled", "unlock the power", "leverage our synergies",
          "supercharge", "skyrocket"]


def body_of(text):
    lines = text.splitlines(); out = []; grab = False
    for ln in lines:
        s = ln.strip()
        if s.startswith("##"):
            if "body" in s.lower():
                grab = True; continue
            elif grab:
                break
            else:
                continue
        elif grab:
            out.append(ln)
    return "\n".join(out).strip()


def lint_body(body):
    fails, warns = [], []
    n = len(body)
    if n > HARD_CAP:
        fails.append(f"body too long: {n} chars > hard cap {HARD_CAP}")
    elif n > SOFT_CAP:
        warns.append(f"body long: {n} chars (soft cap {SOFT_CAP})")
    low = body.lower()
    for b in BANNED:
        if b in low:
            fails.append(f"banned corporate/hype phrase: '{b}'")
    figs = set(re.findall(r"\d+(?:\.\d+)?%|\d+/\d+", body))
    if len(figs) > MAX_FIGURES:
        warns.append(f"{len(figs)} distinct numeric figures (voice: one concrete claim)")
    return fails, warns


def main():
    files = [p for p in sorted(QUEUE.glob("*.md")) if p.name != "INDEX.md"]
    total_fails = 0
    for p in files:
        fails, warns = lint_body(body_of(p.read_text(encoding="utf-8")))
        tag = "FAIL" if fails else ("OK(warn)" if warns else "OK")
        print(f"{tag}   {p.name}")
        for x in fails: print("   - [fail]", x)
        for x in warns: print("   - [warn]", x)
        total_fails += len(fails)
    print(f"\nvoice_lint: {len(files)} entries, {total_fails} fail(s)")
    return 1 if total_fails else 0


if __name__ == "__main__":
    sys.exit(main())