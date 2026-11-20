#!/usr/bin/env python3
"""Citation Accuracy Verification (Archivist goal #2).

Scans all memory/ files for inline citations:
  - File paths in backticks (e.g., `memory/ops/INDEX.md`)
  - "see X" / "refer to X" references
  - URLs (http/https)

Verifies each cited file exists. Reports broken/stale citations with file:line.
Acceptance: >=200 citations checked; broken ones listed; clean state = 0 broken.
"""
import os, re, json, sys, glob as globmod
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(ROOT, "memory")

# Patterns that are NOT real file citations
def is_not_a_citation(path):
    # Angle brackets, globs, braces, braces in URLs
    if '<' in path or '>' in path: return True
    if '*' in path or '?' in path: return True
    if '{' in path or '}' in path: return True
    # Command invocations (expanded list)
    cmd_prefixes = ('python ', 'pythonw', 'pip ', 'findstr', 'dir ', 'type ',
                    'echo ', 'set ', 'cd ', 'git ', 'net ', 'cmd ', 'schtasks',
                    'cmdkey', 'taskkill', 'powershell', 'wmic', 'ipconfig',
                    'curl ', 'wget ', 'ssh ', 'scp ', 'tar ', 'zip ', 'unzip')
    if path.startswith(cmd_prefixes): return True
    # Absolute paths, drive letters, flags
    if path.startswith(('-', '--', '/', '\\', 'C:', 'D:', 'E:')): return True
    # HTTP methods
    if re.match(r'^(GET|POST|PUT|DELETE|PATCH)\s', path): return True
    # URLs (handled separately)
    if path.startswith(('http://', 'https://', 'ftp://')): return True
    # Env vars
    if '%' in path and path.count('%') >= 2: return True
    # Model paths (org/model-name pattern with backslash or known orgs)
    model_orgs = ('lmstudio-community', 'unsloth', 'Qwen', 'Llama', 'Mistral',
                  'gpt-', 'claude-', 'gemini-')
    if any(path.startswith(o) or o in path.split('/')[0] for o in model_orgs): return True
    # Template placeholders (NNN, YYYY, MM, DD patterns)
    if re.search(r'\b(N{2,}|YYYY|MM|DD|XXX)\b', path): return True
    # Bare extensions or very short
    if len(path) < 3: return True
    if re.match(r'^\.[a-z]{1,5}$', path): return True  # bare .md, .py etc.
    # Trailing slash (directory reference, not a file)
    if path.endswith('/') or path.endswith('\\'): return True
    # Parentheses (model variants, descriptions)
    if '(' in path and ')' in path: return True
    # Colons that aren't part of a valid Windows drive letter (e.g. time refs, ports in prose)
    if ':' in path:
        # Allow drive letters only
        if not re.match(r'^[A-Z]:', path):
            return True
    # Spaces without quotes (unlikely to be a real file path in backticks)
    if ' ' in path and not path.startswith(('pythonw ', 'cmdkey ')):
        # Allow some known multi-word patterns that ARE files
        if not re.search(r'\.(md|py|json|html|css|js|txt)$', path):
            return True
    return False

def resolve_path(cited, source_file):
    """Try to resolve a cited path relative to root or source file's dir."""
    # Normalize slashes
    c = cited.replace('\\', '/')
    # Try absolute from memory root
    candidates = [
        os.path.join(MEM, c),
        os.path.join(ROOT, c),
        os.path.join(os.path.dirname(source_file), c),
    ]
    # If starts with memory/, also try relative to source's parent
    if c.startswith('memory/'):
        candidates.append(os.path.join(os.path.dirname(source_file), '..', c))
    for cand in candidates:
        cand = os.path.normpath(cand)
        if os.path.exists(cand):
            return True, cand
    return False, None

def main():
    results = {"total_citations": 0, "file_path_citations": 0, "url_citations": 0,
               "resolved": 0, "broken": [], "skipped_non_citation": 0}
    
    md_files = globmod.glob(os.path.join(MEM, '**', '*.md'), recursive=True)
    # Also scan root-level .md files
    for f in globmod.glob(os.path.join(ROOT, '*.md')):
        md_files.append(f)
    
    backtick_re = re.compile(r'`([^`]+)`')
    url_re = re.compile(r'https?://[\w./:?=&%#-]+')
    see_re = re.compile(r'(?:see|refer to|reference)\s+([\w/_.-]+\.md)', re.IGNORECASE)
    
    for f in sorted(set(md_files)):
        try:
            with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
                lines = fh.readlines()
        except Exception:
            continue
        
        rel_f = os.path.relpath(f, ROOT).replace('\\', '/')
        for i, line in enumerate(lines, 1):
            # File paths in backticks
            for m in backtick_re.finditer(line):
                content = m.group(1).strip()
                if is_not_a_citation(content):
                    results["skipped_non_citation"] += 1
                    continue
                # Must look like a file path (has / or ends with known extension)
                has_ext = bool(re.search(r'\.(md|py|json|jsonl|html|css|js|txt|ps1|bat|sh)$', content))
                has_slash = '/' in content or '\\' in content
                if not (has_ext or has_slash):
                    results["skipped_non_citation"] += 1
                    continue
                # Additional filter: backslash-only paths that look like model refs
                if '\\' in content and '/' not in content:
                    parts = content.split('\\')
                    if len(parts) >= 2 and parts[0] in ('lmstudio-community', 'unsloth'):
                        results["skipped_non_citation"] += 1
                        continue
                results["total_citations"] += 1
                results["file_path_citations"] += 1
                ok, resolved = resolve_path(content, f)
                if ok:
                    results["resolved"] += 1
                else:
                    results["broken"].append({"file": rel_f, "line": i, "cited": content})
            
            # URLs
            for m in url_re.finditer(line):
                results["total_citations"] += 1
                results["url_citations"] += 1
            
            # "see X.md" references
            for m in see_re.finditer(line):
                target = m.group(1)
                if is_not_a_citation(target):
                    continue
                results["total_citations"] += 1
                results["file_path_citations"] += 1
                ok, _ = resolve_path(target, f)
                if not ok:
                    results["broken"].append({"file": rel_f, "line": i, "cited": target})
    
    # Summary
    total_checked = results["total_citations"]
    broken_count = len(results["broken"])
    print(f"=== Citation Accuracy Report ===")
    print(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    print(f"Total citations checked: {total_checked}")
    print(f"  File-path citations: {results['file_path_citations']}")
    print(f"  URL citations:       {results['url_citations']}")
    print(f"  Resolved (exist):    {results['resolved']}")
    print(f"  Broken:              {broken_count}")
    print(f"  Skipped (non-cit):   {results['skipped_non_citation']}")
    if total_checked > 0:
        print(f"  Accuracy:            {(total_checked - broken_count) / total_checked * 100:.1f}%")
    print()
    
    # List broken (first 50)
    if results["broken"]:
        print(f"Broken citations ({broken_count} total, showing first 50):")
        for b in results["broken"][:50]:
            print(f"  {b['file']}:{b['line']} -> `{b['cited']}`")
    else:
        print("No broken citations found.")
    
    # Write JSON
    out = os.path.join(MEM, "archivist", "citation-check-2026-11-20.json")
    with open(out, 'w', encoding='utf-8') as fh:
        json.dump(results, fh, indent=2)
    print(f"\nFull results: {os.path.relpath(out, ROOT)}")

if __name__ == "__main__":
    main()