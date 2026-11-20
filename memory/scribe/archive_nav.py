"""archive_nav.py - Auto-updating archive navigation index for memory/synthesis/.

Usage:
  python memory/scribe/archive_nav.py --auto    # diff + update in-place
  python memory/scribe/archive_nav.py --check   # report diffs without writing
"""

import os
import re
import sys
import json
from datetime import datetime

SYNTHESIS_DIR = "memory/synthesis"
NAV_FILE = os.path.join(SYNTHESIS_DIR, "archive-nav.md")

# Theme classification rules: (theme_name, [keywords in filename or first 200 chars])
THEME_RULES = [
    ("Round Records & Closeouts", ["round-record", "closeout", "auto-loop", r"r\d+", "round record"]),
    ("Planning & Strategy", ["planning", "strategy", "goal-proposal", "dream-big-planning", "upgrade-planning"]),
    ("Adjudication, Rulings & Decisions", ["adjudicat", "ruling", "decision", "contradiction", "supersession-policy", "decisions.jsonl"]),
    ("Index & Pointer Operations", ["index-regen", "pointer", "nav", "replay"]),
]

DEFAULT_THEME = "Other"


def classify_file(filepath):
    """Classify a synthesis file into a theme based on filename + content."""
    basename = os.path.basename(filepath).lower()
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            head = f.read(300).lower()
    except Exception:
        head = ""

    text = basename + " " + head
    for theme, keywords in THEME_RULES:
        for kw in keywords:
            if re.search(kw, text):
                return theme
    return DEFAULT_THEME


def parse_nav(nav_path):
    """Parse archive-nav.md into {theme: [(title, filepath, description), ...]}."""
    themes = {}
    current_theme = None
    with open(nav_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip()
            # Theme header: ## Theme Name (count)
            m = re.match(r"^## (.+?) \((\d+)\)", line)
            if m:
                current_theme = m.group(1)
                themes[current_theme] = []
                continue
            # Entry line: - **Title** (`path`) - description
            m = re.match(r"^- \*\*(.+)\*\* \(`(.+?)`\) - (.*)", line)
            if m and current_theme:
                title, path, desc = m.group(1), m.group(2), m.group(3)
                themes[current_theme].append((title, path, desc))
    return themes


def scan_synthesis(synthesis_dir):
    """Scan synthesis dir for all indexable files (md, json, jsonl; excluding nav + verify)."""
    exts = (".md", ".json", ".jsonl")
    files = set()
    for f in os.listdir(synthesis_dir):
        if not f.endswith(exts):
            continue
        # Exclude the nav file itself and verification artifacts
        if f == "archive-nav.md":
            continue
        if f.startswith("archive-nav-verify") or f.startswith("archive-nav-verified"):
            continue
        files.add(f"memory/synthesis/{f}")
    return files


def build_nav(themes, synthesis_dir):
    """Build the full nav markdown from themes dict."""
    lines = [
        "# Synthesis Archive Navigation Index",
        "",
        f"Curated index of all files in `memory/synthesis/`, organized by theme. "
        f"Auto-generated {datetime.now().strftime('%Y-%m-%d %H:%M')} by archive_nav.py --auto.",
        "",
    ]

    # Fixed theme order, then any new themes alphabetically
    fixed_order = [t[0] for t in THEME_RULES] + [DEFAULT_THEME]
    all_themes = list(themes.keys())
    ordered = [t for t in fixed_order if t in all_themes]
    ordered += sorted(t for t in all_themes if t not in fixed_order)

    for theme in ordered:
        entries = themes[theme]
        lines.append(f"## {theme} ({len(entries)})")
        lines.append("")
        for title, path, desc in sorted(entries, key=lambda x: x[1]):
            lines.append(f"- **{title}** (`{path}`) - {desc}")
        lines.append("")

    return "\n".join(lines)


def extract_title(filepath):
    """Extract a title from the first heading or filename."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re.match(r"^# (.+)", line.strip())
                if m:
                    return m.group(1).strip()
    except Exception:
        pass
    # Fallback: filename without date prefix and extension
    basename = os.path.basename(filepath)
    name = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", basename)
    name = re.sub(r"\.md$", "", name)
    return name.replace("-", " ").title()


def extract_desc(filepath):
    """Extract a short description from the first non-heading paragraph."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            in_content = False
            for line in f:
                stripped = line.strip()
                if not in_content:
                    if stripped.startswith("#"):
                        in_content = True
                    continue
                if not stripped:
                    break
                # Take first sentence or first 120 chars
                return stripped[:120] + ("..." if len(stripped) > 120 else "")
    except Exception:
        pass
    return ""


def auto_update(nav_path, synthesis_dir):
    """Diff and update the nav file in-place. Returns (added, removed, unchanged)."""
    existing = parse_nav(nav_path)
    # Flatten existing entries to a set of paths
    existing_paths = set()
    for theme, entries in existing.items():
        for title, path, desc in entries:
            existing_paths.add(path)

    current_files = scan_synthesis(synthesis_dir)

    added = current_files - existing_paths
    removed = existing_paths - current_files

    # Build new themes dict
    new_themes = {}
    for theme, entries in existing.items():
        new_themes[theme] = [(t, p, d) for t, p, d in entries if p not in removed]

    # Add new files
    for filepath in sorted(added):
        theme = classify_file(filepath)
        title = extract_title(filepath)
        desc = extract_desc(filepath)
        if theme not in new_themes:
            new_themes[theme] = []
        new_themes[theme].append((title, filepath, desc))

    # Deduplicate: if a path appears in multiple themes, keep only the first occurrence
    seen_paths = set()
    deduped_themes = {}
    for theme, entries in new_themes.items():
        kept = []
        for title, path, desc in entries:
            if path not in seen_paths:
                seen_paths.add(path)
                kept.append((title, path, desc))
        deduped_themes[theme] = kept
    new_themes = {t: e for t, e in deduped_themes.items() if e}

    # Write
    nav_content = build_nav(new_themes, synthesis_dir)
    with open(nav_path, "w", encoding="utf-8") as f:
        f.write(nav_content)

    return sorted(added), sorted(removed), len(existing_paths) - len(removed)


def check_only(nav_path, synthesis_dir):
    """Report diffs without writing."""
    existing = parse_nav(nav_path)
    existing_paths = set()
    for theme, entries in existing.items():
        for title, path, desc in entries:
            existing_paths.add(path)

    current_files = scan_synthesis(synthesis_dir)
    added = sorted(current_files - existing_paths)
    removed = sorted(existing_paths - current_files)

    result = {
        "added": added,
        "removed": removed,
        "unchanged_count": len(existing_paths & current_files),
    }
    print(json.dumps(result, indent=2))
    return result


def main():
    if "--auto" in sys.argv:
        added, removed, unchanged = auto_update(NAV_FILE, SYNTHESIS_DIR)
        print(f"[archive_nav --auto] +{len(added)} added, -{len(removed)} removed, {unchanged} unchanged")
        for f in added:
            print(f"  + {f}")
        for f in removed:
            print(f"  - {f}")
    elif "--check" in sys.argv:
        check_only(NAV_FILE, SYNTHESIS_DIR)
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
