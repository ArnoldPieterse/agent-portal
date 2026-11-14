#!/usr/bin/env python3
"""
apply_staged_patches.py — Archivist, 2026-11-14.
Bundles the 3 staged patches (F1 index/hygiene + F2 fleet-md5 + ops git-hygiene line)
into ONE idempotent, exact-guarded apply. Run on the CANONICAL WHITE root so each
edit's mtime is local to the authoritative host (sidesteps the cross-host mtime-guard /
clobber race that blocks existing-file edits from a remote seat).

Modes:
  --dry-run   (default) prove every guard matches exactly once; write nothing.
  --apply     apply any not-yet-applied patch, then re-read and run the verification greps.
  --check     read-only: run the verification greps against current files (post-apply confirm).

Safety model per patch:
  * applied_marker present in file  -> ALREADY_APPLIED (idempotent skip; never double-applies)
  * else old_string count == 1      -> apply (exact single-site guard; no blind replace)
  * else                            -> GUARD_FAIL (report match count; do NOT touch the file)
"""
import sys, os

# Root auto-resolves to the workspace root (the dir containing memory/INDEX.md) by walking up
# from this file -- location-independent, works from <root>/archivist/ OR <root>/memory/archivist/.
# Override with ARCHIVIST_ROOT for a sandboxed end-to-end test so we never touch the live tree.
def _find_root(start_dir):
    d = os.path.abspath(start_dir)
    for _ in range(8):
        if os.path.isfile(os.path.join(d, "memory", "INDEX.md")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROOT = os.environ.get("ARCHIVIST_ROOT") or _find_root(os.path.dirname(os.path.abspath(__file__)))
def P(rel): return os.path.join(ROOT, rel.replace("/", os.sep))

# Each patch: label, file (relative), old (verbatim single-site anchor), new, marker (present after apply).
PATCHES = [
    # ---- F1a: portal/INDEX.md — append planning-2026-11-13 entry to the Entries list ----
    dict(
        label="F1a portal/INDEX planning entry",
        file="memory/portal/INDEX.md",
        old=("- TODO pruning / prune / TODO_completed / auto-chunk / todo_done_parts / git repo / MinGit / mingit / "
             "commit / .gitignore allowlist / Ops panel / /api/git -> memory/portal/architecture.md   NEW OPS processes "
             "(2026-11-13): prune endpoint + chunk splitting, local git via portable MinGit, GET/POST /api/git, \U0001F527 Ops UI"),
        new=("- TODO pruning / prune / TODO_completed / auto-chunk / todo_done_parts / git repo / MinGit / mingit / "
             "commit / .gitignore allowlist / Ops panel / /api/git -> memory/portal/architecture.md   NEW OPS processes "
             "(2026-11-13): prune endpoint + chunk splitting, local git via portable MinGit, GET/POST /api/git, \U0001F527 Ops UI\n"
             "- planning / ratification / apply order / A1 uploads-mirror / C2 canary / gates -> memory/portal/planning-2026-11-13.md   "
             "V102 planning meeting (Scribe minutes): order C1 \u2192 A1+canary \u2192 A2 \u2192 D1 watch \u2192 F1 hygiene; ops clearance + P8 STOP gate"),
        marker="planning-2026-11-13",
    ),
    # ---- F1b: llm/hosts.md L8 Red row — append DHCP/NIC staleness flag into the State cell ----
    dict(
        label="F1b hosts.md Red UNCONFIRMED flag",
        file="memory/llm/hosts.md",
        old="FUTURE: move .245 to the wired NIC for ~100x transfers |",
        new=("FUTURE: move .245 to the wired NIC for ~100x transfers; \u26A0 11-13 ~16:30: .245 DHCP lease expired + "
             "wired NIC uncabled (P5, physical fix = Arnold's window) \u2192 IP UNCONFIRMED; do not target .245 for new probes until re-scan |"),
        marker="IP UNCONFIRMED",
    ),
    # ---- F1c: llm/hosts.md L10 Black row — correct stale alias ref (r37 Mechanic) ----
    dict(
        label="F1c hosts.md Black builder-q8 rebind note",
        file="memory/llm/hosts.md",
        old="Q8_0->GPU1 (alias builder-q8, ref:bc7ad351)",
        new="Q8_0->GPU1 (alias builder-q8 -> Qwen3.8-27B-Q8_0; rebind 11-14 r37 Mechanic, was stale ref:bc7ad351)",
        marker="rebind 11-14 r37",
    ),
    # ---- F2: portal/fleet-status.md — append record-integrity discrepancy note under Verification evidence ----
    dict(
        label="F2 fleet-status md5 discrepancy note",
        file="memory/portal/fleet-status.md",
        old=("- Portal restart: PID 24808 killed -> relaunched detached via one-shot schtask (wmic removed on this OS; "
             "`start` children are reaped by the terminal wrapper) -> new PID 21988, task deleted immediately after."),
        new=("- Portal restart: PID 24808 killed -> relaunched detached via one-shot schtask (wmic removed on this OS; "
             "`start` children are reaped by the terminal wrapper) -> new PID 21988, task deleted immediately after.\n"
             "- Record discrepancy (2026-11-13, Archivist): the L27 baseline 2ba0b031\u2026 does not reproduce \u2014 current agent_portal.py "
             "first-1600-chars md5 = ae20e867fb5ae0a091e94916aa3cafbf on BOTH Pale and Black seats (mtimes 13:37:22 / 14:37:22 local, "
             "same file state; last edit ~13:37 predates the ~14:0x verification). Treated as mis-recorded baseline, not an undocumented "
             "edit. Ground truth on White: recompute md5 of first 1600 chars of the canonical file; if ae20e867\u2026, correct this line in place."),
        marker="Record discrepancy (2026-11-13, Archivist)",
    ),
    # ---- ops/INDEX.md — append git-hygiene entry to the Entries list ----
    dict(
        label="ops/INDEX git-hygiene line",
        file="memory/ops/INDEX.md",
        old=("- PDF reports / fpdf2 / _gen_report.py pattern / report layout pitfalls / PNG verify step -> "
             "memory/ops/pdf-reporting.md   Archivist's repeatable PDF-reporting recipe"),
        new=("- PDF reports / fpdf2 / _gen_report.py pattern / report layout pitfalls / PNG verify step -> "
             "memory/ops/pdf-reporting.md   Archivist's repeatable PDF-reporting recipe\n"
             "- git hygiene / commit conventions / cite-hash-not-paste / commit-after-verification -> memory/ops/git-hygiene.md   "
             "fleet commit rules (feat|fix|docs|chore + agent tag)"),
        marker="git-hygiene.md",
    ),
]

# Verification greps (from the staged notes). Each: label, file, needle, expected_min_hits.
CHECKS = [
    ("F1a portal INDEX has planning entry", "memory/portal/INDEX.md", "planning-2026-11-13", 1),
    ("F1b hosts Red row UNCONFIRMED flag",   "memory/llm/hosts.md",      "IP UNCONFIRMED",     1),
    ("F1c hosts Black rebind note present",  "memory/llm/hosts.md",      "rebind 11-14 r37",   1),
    ("F2 fleet-status discrepancy note",     "memory/portal/fleet-status.md", "Record discrepancy (2026-11-13, Archivist)", 1),
    ("ops INDEX git-hygiene line",           "memory/ops/INDEX.md",      "git-hygiene.md",     1),
]

def read(rel):
    with open(P(rel), encoding="utf-8") as f:
        return f.read()

def write(rel, content):
    path = P(rel)
    tmp = path + ".tmp_archivist"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    os.replace(tmp, path)  # atomic on same volume

def run_checks():
    print("\n--- verification greps ---")
    ok = True
    for label, rel, needle, minhits in CHECKS:
        try:
            n = read(rel).count(needle)
        except FileNotFoundError:
            n = -1
        good = n >= minhits
        ok = ok and good
        print(f"  [{'PASS' if good else 'FAIL'}] {label}: '{needle}' x{n} (need >={minhits})")
    return ok

def main():
    mode = "--dry-run"
    for a in sys.argv[1:]:
        if a in ("--apply", "--check", "--dry-run"):
            mode = a
    if mode == "--check":
        ok = run_checks()
        print("\nCHECK:", "ALL PASS" if ok else "SOME FAILED")
        return 0 if ok else 2

    apply = (mode == "--apply")
    files = {}   # rel -> current content (lazy)
    changed = set()
    would_apply = []
    print(f"--- {'APPLY' if apply else 'DRY-RUN'}: {len(PATCHES)} staged patches ---")
    for p in PATCHES:
        rel = p["file"]
        if rel not in files:
            try:
                files[rel] = read(rel)
            except FileNotFoundError:
                print(f"  [FAIL] {p['label']}: file missing {rel}")
                continue
        content = files[rel]
        if p["marker"] in content:
            print(f"  [SKIP] {p['label']}: already applied (marker present)")
            continue
        n = content.count(p["old"])
        if n == 1:
            files[rel] = content.replace(p["old"], p["new"], 1)
            changed.add(rel)
            would_apply.append(p["label"])
            print(f"  [{'APPLY' if apply else 'WOULD'}] {p['label']}: guard ok (1 exact match)")
        else:
            print(f"  [GUARD_FAIL] {p['label']}: expected 1 match, found {n} -- NOT touching file")

    if apply and changed:
        for rel in sorted(changed):
            write(rel, files[rel])
            print(f"  wrote {rel}")
        ok = run_checks()
        print("\nRESULT:", "APPLIED + ALL CHECKS PASS" if ok else "APPLIED BUT SOME CHECKS FAILED")
        return 0 if ok else 2
    elif not apply:
        print(f"\nDRY-RUN: {len(would_apply)} patch(es) would apply; run with --apply on the canonical White root to commit.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
