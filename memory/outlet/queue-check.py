#!/usr/bin/env python3
"""queue-check.py - Outlet queue shape-contract validator.

Runs against every .md in memory/outlet/queue/. For each entry it checks:
  * YAML front-matter block present at top (--- ... ---)
  * required fields non-empty: id, status, platform, drafted
  * status is a known value
  * id is unique across the queue
  * no internal secrets leaked: private IPs, local drive/abs paths, key/token patterns

Exit 0 = all pass; exit 1 = one or more FAIL (reasons printed). Read-only.
"""
import re, sys, pathlib, datetime

REQUIRED = ["id", "status", "platform", "drafted"]
VALID_STATUS = {"ready-for-human", "staged", "published", "rejected", "draft"}

# internal-secret patterns (must NOT appear in a publishable queue entry)
SECRET_PATTERNS = [
    (re.compile(r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"), "private-IP"),
    (re.compile(r"[A-Za-z]:\\", re.I), "windows-drive-path"),
    (re.compile(r"(?i)sk-[a-z0-9]{20,}"), "secret-key-token"),
    (re.compile(r"(?i)AKIA[0-9A-Z]{16}"), "aws-access-key"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private-key-block"),
]

def parse_front_matter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    fm, i = {}, 1
    while i < len(lines):
        line = lines[i]
        if line.strip() == "---":
            return fm
        m = re.match(r"^([A-Za-z][\w-]*)\s*:\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip()
        i += 1
    return None  # unterminated

def check_file(path, seen_ids):
    errs = []
    text = path.read_text(encoding="utf-8")
    fm = parse_front_matter(text)
    if fm is None:
        return ["no YAML front-matter block at top (--- ... ---)"]
    for f in REQUIRED:
        v = fm.get(f, "").strip()
        if not v:
            errs.append(f"missing/empty required field: {f}")
    status = fm.get("status", "").strip()
    if status and status not in VALID_STATUS:
        errs.append(f"invalid status '{status}' (valid: {sorted(VALID_STATUS)})")
    fid = fm.get("id", "").strip()
    if fid:
        if fid in seen_ids:
            errs.append(f"duplicate id '{fid}' across queue")
        seen_ids.add(fid)
    for pat, label in SECRET_PATTERNS:
        m = pat.search(text)
        if m:
            line_no = text[:m.start()].count("\n") + 1
            errs.append(f"SECRET/INTERNAL leak [{label}] at line {line_no}: {m.group(0)!r}")
    return errs

def main():
    qdir = pathlib.Path("memory/outlet/queue")
    if not qdir.exists():
        print(f"FAIL: queue dir missing: {qdir}")
        return 1
    files = sorted(qdir.glob("*.md"))
    if not files:
        print("WARN: no .md entries in queue (nothing to validate)")
        return 0
    seen, total_fail = set(), 0
    for f in files:
        errs = check_file(f, seen)
        if errs:
            total_fail += 1
            print(f"FAIL {f.name}")
            for e in errs:
                print(f"     - {e}")
        else:
            fm = parse_front_matter(f.read_text(encoding="utf-8"))
            print(f"PASS {f.name}  (status={fm.get('status')}, id={fm.get('id')})")
    print("-" * 50)
    print(f"{len(files)-total_fail}/{len(files)} queue entries pass shape contract")
    return 1 if total_fail else 0

if __name__ == "__main__":
    sys.exit(main())
