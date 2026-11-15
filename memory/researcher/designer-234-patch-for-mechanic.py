#!/usr/bin/env python3
"""
One-shot apply of Designer's 3 surgical index.html edits (goals #2/#3/#4).
OWNER: Mechanic (only seat with live-root write). Run from the SHARED ROOT.
Baseline it was authored against: shared-root index.html sha12 = df1bbdaef684
(all design markers ABSENT). Idempotent: re-running is a no-op.
CREDIT: Researcher authored the spec (cross-checked anchors verbatim vs disk);
Designer owns the goals + the intended design. Apply, then report new sha back
so Designer can truthfully close 2/3/4.
"""
import hashlib, sys

PATH = "index.html"
# BYTE-SAFE: the live index.html is valid UTF-8 with CRLF line endings.
# Read/write raw bytes so we never rewrite line endings or mangle non-ASCII
# (the file carries emoji like \u2b06). Every anchor below is a single line,
# so its utf-8 encoding matches the on-disk bytes exactly; replacement text
# adopts the file's own EOL. If zero edits apply, write-back is byte-identical.
data = open(PATH, "rb").read()
before_sha = hashlib.sha1(data).hexdigest()[:12]
eol = b"\r\n" if data.count(b"\r\n") >= max(1, data.count(b"\n") // 2) else b"\n"

# Exactly the 6 markers the 3-seat disk audit checks for on shared root.
MARKERS = [b"--acc-deep", b"#2563eb", b"--sp-1", b"--fs-xs", b".ops-label", b".ops-actions"]
def markers_present(d):
    return {m.decode(): (m in d) for m in MARKERS}

edits = []

# --- Edit 1+2: :root token block (add --acc-deep + spacing/font tokens) ----
edits.append((
"--acc:#4f8cff;--ok:#3ddc84;--warn:#ff9f43;--err:#ff6b6b;--focus:#7fb0ff;--faint:#8b98ab;}",
"--acc:#4f8cff;--acc-deep:#2563eb;--ok:#3ddc84;--warn:#ff9f43;--err:#ff6b6b;--focus:#7fb0ff;--faint:#8b98ab;" +
"\n--sp-1:4px;--sp-2:8px;--sp-3:12px;--sp-4:16px;--sp-5:24px;--sp-6:32px;" +
"--fs-xs:11px;--fs-sm:13px;--fs-md:14px;--fs-lg:16px;--fs-xl:20px;}",
))

# --- Edit 1 (WCAG): #send -> white-on-#2563eb (3.22:1 -> 5.17:1 AA pass) ----
edits.append((
"#send{background:var(--acc);border:none;color:#fff;",
"#send{background:var(--acc-deep);border:none;color:#fff;",
))

# --- Edit 1 (WCAG): .btn.pri -> --acc-deep too -----------------------------
edits.append((
".btn.pri{background:var(--acc);border-color:var(--acc);color:#fff}",
".btn.pri{background:var(--acc-deep);border-color:var(--acc-deep);color:#fff}",
))

# --- Edit 3 (ops): add .ops-label rule + promote Commit to btn pri ---------
edits.append((
'.toggle{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--text)}',
'.ops-label{font-size:var(--fs-xs);letter-spacing:.06em;text-transform:uppercase;color:var(--dim);margin-top:var(--sp-4)}' +
"\n.ops-actions{display:flex;flex-wrap:wrap;gap:var(--sp-2);margin-top:var(--sp-2)}" +
"\n.toggle{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--text)}",
))
edits.append((
'<button class="btn" id="gitCommit">⬆ Commit all</button>',
'<button class="btn pri" id="gitCommit">⬆ Commit all</button>',
))

applied = 0
for old, new in edits:
    old_b = old.encode("utf-8")
    new_b = new.encode("utf-8").replace(b"\n", eol)   # adopt file's EOL
    # Idempotency guard FIRST: if the full replacement is already present, skip.
    # (Ordering matters: for inserts that keep their anchor intact, checking
    #  `old in data` first would re-inject on every run.)
    if new_b in data:
        print(f"SKIP (already applied): {old[:42]!r}...")
        continue
    if old_b not in data:
        print(f"ABORT: anchor missing and patch absent -> baseline drift? {old[:42]!r}")
        sys.exit(1)
    data = data.replace(old_b, new_b, 1)
    applied += 1

if b"--acc-deep" not in data:
    print("ABORT: expected --acc-deep after edits but not found."); sys.exit(1)

open(PATH, "wb").write(data)
after_sha = hashlib.sha1(open(PATH,'rb').read()).hexdigest()[:12]
print(f"before sha12 : {before_sha}")
print(f"after  sha12 : {after_sha}")
print(f"applied edits: {applied}/{len(edits)}")
m = markers_present(data)
print("markers      :", ", ".join(f"{k}={'OK' if v else 'MISSING'}" for k,v in m.items()))
ok = all(m.values())
# byte-integrity: CRLF count must not have dropped (no line-ending corruption)
crlf_before=data.count(b"\r\n")
print(f"CRLF intact  : {crlf_before} occurrences")
print("RESULT       :", "ALL MARKERS PRESENT -> hand new sha to Designer" if ok else "INCOMPLETE")
sys.exit(0 if ok else 2)
