#!/usr/bin/env python3
"""Stopgap patch: H1 .frow collision + 2 WCAG AA contrast failures.

Why this exists (2026-11-15, Verifier):
  - Shared-tree index.html still has the .frow class collision (L92 flex rule for
    dialog form rows vs L120 padding/border rule for #fleetBody host rows).
  - The durable script memory/designer/goals-patch-apply-2026-11-15.py is missing
    the active-tab contrast hunk (white on --acc #4f8cff = 3.22:1, needs >=4.5).
  This script applies ONLY those three hunks. Idempotent; safe to run after the
  Designer patch on the SAME root. Run on the portal's serving root (White) before
  restarting :8099:
      python stopgap_h1_contrast_patch.py <portal-root>     # default: .
      python stopgap_h1_contrast_patch.py --selftest        # dry-run vs local index.html copy

Contrast math (verified by Verifier against --panel #151a22):
  #6b7688 on #151a22 = 3.80 FAIL -> #8b98ab = 5.97 PASS
  #fff    on #4f8cff = 3.22 FAIL -> #fff on #3a6fd6 = 4.75 PASS (--acc kept elsewhere)
"""
import sys, os, shutil, datetime

HUNKS = [
    # (id, description, old, new)
    ("H1-flex", "scope flex rule to dialog form rows only",
     '.frow{display:flex;gap:10px}.frow>div{flex:1}',
     'dialog .frow{display:flex;gap:10px}dialog .frow>div{flex:1}'),
    ("H1-padded", "scope padding/border rule to fleet rows only",
     '.frow{padding:7px 0;border-bottom:1px dashed var(--line);font-size:12.5px}',
     '#fleetBody .frow{padding:7px 0;border-bottom:1px dashed var(--line);font-size:12.5px}'),
    ("H1-lastchild", "scope :last-child to fleet rows",
     '.frow:last-child{border-bottom:none}',
     '#fleetBody .frow:last-child{border-bottom:none}'),
    ("C-at", ".aev .at timestamp contrast 3.80 -> 5.97",
     '.aev .at{color:#6b7688;flex:none;width:64px}',
     '.aev .at{color:#8b98ab;flex:none;width:64px}'),
    ("C-tab", "active Solo/Group tab contrast 3.22 -> 4.75",
     '.seg button.on{background:var(--acc);color:#fff}',
     '.seg button.on{background:#3a6fd6;color:#fff}'),
]

def apply(path, dry=False):
    src = open(path, encoding="utf-8").read()
    out, applied, skipped, failed = src, [], [], []
    for hid, desc, old, new in HUNKS:
        if new in out:
            skipped.append(hid)          # already applied -> idempotent (check FIRST:
                                         # some 'new' strings contain 'old' as substring)
        elif old in out:
            out = out.replace(old, new, 1)
            applied.append(hid)
        else:
            failed.append((hid, desc))   # neither present -> file drifted
    if failed:
        print("DRIFT DETECTED - not writing. Missing expected source text for:")
        for hid, desc in failed:
            print(f"  {hid}: {desc}")
        return 1
    if dry:
        print(f"[dry] would apply {len(applied)} hunk(s): {', '.join(applied) or 'none'}; "
              f"already-present: {', '.join(skipped) or 'none'}")
        return 0
    if applied:
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        shutil.copy2(path, path + f".bak-{ts}")
        open(path, "w", encoding="utf-8").write(out)
        print(f"backup -> {os.path.basename(path)}.bak-{ts}")
        print(f"applied {len(applied)}: {', '.join(applied)}")
    else:
        print("no hunks to apply (all present) - file unchanged")
    # post-write verification
    chk = open(path, encoding="utf-8").read()
    for hid, desc, old, new in HUNKS:
        if new not in chk:
            print(f"POST-CHECK FAIL: {hid} missing after write"); return 2
    if chk.count("<div") != chk.count("</div"):
        pass  # div balance is a Designer-patch concern; this patch touches CSS lines only
    print("post-check: all hunks present. OK")
    return 0

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        here = os.path.dirname(os.path.abspath(__file__))
        cand = ["index.html", os.path.join(here, "..", "..", "index.html")]
        src = next((c for c in cand if os.path.exists(c)), None)
        if not src:
            print("selftest: no index.html found to test against"); sys.exit(3)
        import tempfile
        tmp = os.path.join(tempfile.gettempdir(), "stopgap_selftest_index.html")
        shutil.copy2(src, tmp)
        import io, contextlib
        buf1, buf2 = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf1): rc1 = apply(tmp)   # first run: apply 5
        with contextlib.redirect_stdout(buf2): rc2 = apply(tmp)   # second run: MUST be no-op
        final = open(tmp, encoding="utf-8").read()
        n_applied_r2 = len([l for l in buf2.getvalue().splitlines() if l.startswith("applied ") and "none" not in l])
        doubled = (final.count("#fleetBody #fleetBody") + final.count("dialog dialog")
                   + final.count("color:#8b98ab;color:") + final.count("background:#3a6fd6;background:"))
        ok = (rc1 == 0 and rc2 == 0 and n_applied_r2 == 0 and doubled == 0
              and all(new in final for _, _, _, new in HUNKS))
        print(buf1.getvalue()); print(buf2.getvalue())
        print(f"selftest: {'PASS' if ok else 'FAIL'} (rc={rc1},{rc2}, run2-applied={n_applied_r2}, doubled-prefixes={doubled}) against {src}")
        sys.exit(0 if ok else 4)
    root = next((a for a in sys.argv[1:] if not a.startswith("-")), ".")
    target = os.path.join(root, "index.html")
    if not os.path.exists(target):
        print(f"no index.html at {target}"); sys.exit(3)
    dry = "--dry" in sys.argv
    sys.exit(apply(target, dry=dry))
