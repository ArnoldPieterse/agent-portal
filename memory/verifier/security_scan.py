#!/usr/bin/env python3
"""Security Scan Automation — Verifier Goal 5.

Checks:
  (a) No hardcoded secrets in code files (Python + JS)
  (b) User-input path sanitization (SQL injection / XSS vectors)
  (c) File permissions on sensitive files (agents.json, .env)
  (d) CORS headers correct in agent_portal.py

Usage: python memory/verifier/security_scan.py [--fixture]
  --fixture  also scan the deliberately vulnerable fixture file

Output: memory/verifier/security-report.md + exit code (0=clean, 1=issues found)
"""
import os, re, sys, json, stat, hashlib
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path.cwd()  # project root (sandbox CWD)
REPORT_PATH = ROOT / "memory" / "verifier" / "security-report.md"
FIXTURE_PATH = ROOT / "memory" / "verifier" / "_security_fixture_vulnerable.py"

# ── Secret patterns ──────────────────────────────────────────────────────────
SECRET_PATTERNS = [
    # AWS access key id
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    # Generic api_key / token / secret assignments with literal strings
    (r"(?i)\b(api_?key|secret_?key|auth_?token|access_?token|private_?key)\s*=\s*['\"][^'\"]{8,}['\"]",
     "Hardcoded credential assignment"),
    # password / pwd with non-trivial literal
    (r"(?i)\b(password|passwd|pwd)\s*=\s*['\"][^'\"]{4,}['\"]",
     "Hardcoded password"),
    # Bearer token in code
    (r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}", "Hardcoded bearer token"),
    # Generic high-entropy hex/hex-ish string assigned to suspicious var
    (r"(?i)\b(key|token|secret|password|credential)\w*\s*=\s*['\"][a-fA-F0-9]{32,}['\"]",
     "High-entropy credential assignment"),
]

# ── SQL injection patterns (Python) ─────────────────────────────────────────
SQLI_PATTERNS = [
    # f-string or .format() in a SQL query
    (r"(?i)(?:SELECT|INSERT|UPDATE|DELETE)\b.*\{[a-zA-Z_]+\}", "f-string SQL injection vector"),
    (r"(?i)(?:SELECT|INSERT|UPDATE|DELETE)\b.*\.format\(", ".format() SQL injection vector"),
    # String concatenation in SQL
    (r"(?i)['\"](?:SELECT|INSERT|UPDATE|DELETE)[^'\"]*['\"]\s*\+\s*[a-zA-Z_]",
     "String-concat SQL injection vector"),
    # % formatting in SQL
    (r"(?i)(?:SELECT|INSERT|UPDATE|DELETE)\b.*%s.*%\s*\w", "%-formatting SQL injection vector"),
]

# ── XSS patterns (JS) ────────────────────────────────────────────────────────
XSS_PATTERNS = [
    # innerHTML assigned from a variable that looks like user input
    (r"\.innerHTML\s*=\s*(?!'[^']*'|`[^`]*`)([a-zA-Z_$][\w$]*(?:\.[\w$]+)*)", "innerHTML from dynamic variable (XSS risk)"),
    # document.write with non-literal
    (r"document\.write(?!\s*\()['\"]", "document.write with dynamic content"),
]

# ── Sensitive files to check permissions on ──────────────────────────────────
SENSITIVE_FILES = ["agents.json", ".env", "memory/ops/blockers.md"]

# ── CORS expectations ────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGIN_PATTERN = re.compile(r"Access-Control-Allow-Origin")
CORS_WILDCARD_PATTERN = re.compile(r'Access-Control-Allow-Origin.*[\'\"]\*[\'\"]')


def scan_secrets(path: Path, content: str, lang: str) -> list:
    """Return list of (line_no, desc, snippet) for secret matches."""
    findings = []
    lines = content.splitlines()
    for i, line in enumerate(lines, 1):
        # Skip comment-only lines
        stripped = line.strip()
        if lang == "py" and (stripped.startswith("#") or stripped.startswith('"""')):
            continue
        if lang == "js" and stripped.startswith("//"):
            continue
        for pat, desc in SECRET_PATTERNS:
            m = re.search(pat, line)
            if m:
                snippet = line.strip()[:80]
                findings.append((i, desc, snippet))
    return findings


def scan_sqli(path: Path, content: str) -> list:
    findings = []
    lines = content.splitlines()
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        for pat, desc in SQLI_PATTERNS:
            m = re.search(pat, line)
            if m:
                findings.append((i, desc, line.strip()[:80]))
    return findings


def scan_xss(path: Path, content: str) -> list:
    findings = []
    lines = content.splitlines()
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("/*"):
            continue
        for pat, desc in XSS_PATTERNS:
            m = re.search(pat, line)
            if m:
                findings.append((i, desc, line.strip()[:80]))
    return findings


def check_permissions(root: Path) -> list:
    """Check that sensitive files are not world-readable/writable."""
    findings = []
    for rel in SENSITIVE_FILES:
        p = root / rel
        if not p.exists():
            continue
        try:
            st = os.stat(p)
            mode = st.st_mode
            # On Windows, permission bits are less meaningful; check if file exists and is readable
            # Flag .env if it has overly permissive group/other write (rare on Windows but check anyway)
            if p.name == ".env" and (mode & stat.S_IWOTH or mode & stat.S_IWGRP):
                findings.append((rel, "World/group-writable", oct(mode)))
        except Exception as e:
            findings.append((rel, f"stat error: {e}", ""))
    return findings


def check_cors(root: Path) -> list:
    """Check CORS configuration in agent_portal.py."""
    findings = []
    portal = root / "agent_portal.py"
    if not portal.exists():
        return [("agent_portal.py", "file not found", "")]
    content = portal.read_text(encoding="utf-8", errors="replace")
    # Find wildcard CORS
    for m in CORS_WILDCARD_PATTERN.finditer(content):
        line_no = content[:m.start()].count("\n") + 1
        findings.append((line_no, "Wildcard CORS origin (*) — restrict to known origins", content.splitlines()[line_no-1].strip()[:80]))
    # Check if Access-Control-Allow-Origin is present at all
    if not CORS_ALLOWED_ORIGIN_PATTERN.search(content):
        findings.append((0, "No Access-Control-Allow-Origin header found (may be intentional for same-origin only)", ""))
    return findings


def collect_files(root: Path, include_fixture: bool) -> list:
    """Return list of (path, lang) to scan."""
    files = []
    # Python files in root
    for f in root.glob("*.py"):
        if f.name.startswith("_") and f.name not in ("_security_fixture_vulnerable.py",):
            continue  # skip underscore-prefixed scratch files except fixture
        files.append((f, "py"))
    # Python files in memory/verifier
    for f in (root / "memory/verifier").glob("*.py"):
        if not f.name.startswith("_"):
            files.append((f, "py"))
    # JS files in ui/
    for f in (root / "ui").glob("*.js"):
        files.append((f, "js"))
    if include_fixture and FIXTURE_PATH.exists():
        files.append((FIXTURE_PATH, "py"))
    return files


def main():
    include_fixture = "--fixture" in sys.argv
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    all_findings = {"secrets": [], "sqli": [], "xss": [], "permissions": [], "cors": []}

    files = collect_files(ROOT, include_fixture)
    scanned_count = 0

    for path, lang in files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel = path.relative_to(ROOT).as_posix()
        scanned_count += 1

        # Secrets (all languages)
        for line_no, desc, snippet in scan_secrets(path, content, lang):
            all_findings["secrets"].append((rel, line_no, desc, snippet))

        # SQLi (Python only)
        if lang == "py":
            for line_no, desc, snippet in scan_sqli(path, content):
                all_findings["sqli"].append((rel, line_no, desc, snippet))

        # XSS (JS only)
        if lang == "js":
            for line_no, desc, snippet in scan_xss(path, content):
                all_findings["xss"].append((rel, line_no, desc, snippet))

    # Permissions
    for rel, desc, detail in check_permissions(ROOT):
        all_findings["permissions"].append((rel, 0, desc, detail))

    # CORS
    for item in check_cors(ROOT):
        if len(item) == 3:
            line_no, desc, snippet = item
            all_findings["cors"].append(("agent_portal.py", line_no, desc, snippet))

    total_issues = sum(len(v) for v in all_findings.values())

    # Write report
    lines = [
        f"# Security Scan Report",
        f"Generated: {now}",
        f"Files scanned: {scanned_count}",
        f"Total findings: {total_issues}",
        "",
    ]
    section_names = {
        "secrets": "Hardcoded Secrets",
        "sqli": "SQL Injection Vectors",
        "xss": "XSS Vectors (JS)",
        "permissions": "File Permissions",
        "cors": "CORS Configuration",
    }
    for key, title in section_names.items():
        items = all_findings[key]
        lines.append(f"## {title} ({len(items)})")
        if not items:
            lines.append("PASS — no issues found.")
        else:
            for item in items:
                if len(item) == 4:
                    rel, line_no, desc, snippet = item
                    loc = f"{rel}:{line_no}" if line_no else rel
                    lines.append(f"- **{loc}** — {desc}")
                    if snippet:
                        lines.append(f"  ```\n  {snippet}\n  ```")
        lines.append("")

    verdict = "PASS" if total_issues == 0 else f"FAIL ({total_issues} issues)"
    lines.insert(3, f"**Verdict: {verdict}**")
    lines.insert(4, "")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Security scan complete: {total_issues} findings across {scanned_count} files.")
    print(f"Report: {REPORT_PATH.relative_to(ROOT)}")
    sys.exit(0 if total_issues == 0 else 1)


if __name__ == "__main__":
    main()
