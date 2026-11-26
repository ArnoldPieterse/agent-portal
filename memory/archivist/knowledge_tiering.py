#!/usr/bin/env python3
"""Knowledge Tiering Prototype - measures token fit for small-context models.

Demonstrates that T0 (pointer index) + top-N T1 (summaries) fits within
8K tokens while retaining critical info for one lane.

Usage:
    python memory/archivist/knowledge_tiering.py --selftest
"""
import json, re, sys
from pathlib import Path

MEMORY = Path(__file__).resolve().parent.parent.parent
LANE = MEMORY / "memory" / "archivist"
INDEX = LANE / "INDEX.md"
REPORT = LANE / "tiering-report.json"

TOKENS_PER_WORD = 1.3  # rough estimate for English text
MAX_CONTEXT = 8000     # target token budget
SYSTEM_PROMPT_TOKENS = 2000  # estimated overhead

def count_tokens(text: str) -> int:
    """Rough token count (words * 1.3)."""
    words = len(text.split())
    return int(words * TOKENS_PER_WORD)

def generate_t0(index_text: str) -> list:
    """Parse INDEX.md into T0 pointer entries."""
    entries = []
    for line in index_text.strip().split("\n"):
        if line.startswith("- ") and "->" in line:
            # Format: - name (desc) -> path   description
            parts = line.split("->", 1)
            left = parts[0].strip().lstrip("- ").strip()
            right = parts[1].strip() if len(parts) > 1 else ""
            entries.append({
                "pointer": left,
                "path": right.split()[0] if right else "",
                "tokens": count_tokens(line),
            })
    return entries

def generate_t1(filepath: str) -> str:
    """Generate a T1 summary (3 sentences) from a file."""
    p = MEMORY / filepath
    if not p.exists():
        return ""
    text = p.read_text(encoding="utf-8", errors="replace")
    lines = text.strip().split("\n")
    
    # Extract title
    title = ""
    for line in lines[:5]:
        if line.startswith("# "):
            title = line[2:].strip()
            break
    
    # Extract key sentences (non-header, non-code, substantive)
    sentences = []
    in_code = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code or not line.strip() or line.strip().startswith("#"):
            continue
        stripped = line.strip()
        if len(stripped) > 30 and not stripped.startswith("- "):
            sentences.append(stripped)
    
    # Take first 3 substantive sentences as abstract
    abstract_parts = []
    if title:
        abstract_parts.append(title + ".")
    for s in sentences[:3]:
        if len(s) > 20:
            abstract_parts.append(s[:150])
    
    return " ".join(abstract_parts)[:400]

def run_selftest():
    """Verify tiering fits in 8K tokens."""
    print("=== KNOWLEDGE TIERING SELFTEST ===")
    results = {}
    
    # T0: Parse index
    index_text = INDEX.read_text(encoding="utf-8")
    t0_entries = generate_t0(index_text)
    t0_tokens = sum(e["tokens"] for e in t0_entries)
    print(f"  T0 entries: {len(t0_entries)}, tokens: {t0_tokens}")
    
    # T1: Generate summaries for top files (by size, as proxy for importance)
    lane_files = [f for f in LANE.iterdir() if f.suffix == ".md" and f.stat().st_size > 500]
    lane_files.sort(key=lambda f: f.stat().st_size, reverse=True)
    
    t1_summaries = []
    for f in lane_files[:20]:  # top 20 by size
        rel = str(f.relative_to(MEMORY)).replace("\\", "/")
        summary = generate_t1(rel)
        if summary:
            t1_summaries.append({"file": f.name, "summary": summary, "tokens": count_tokens(summary)})
    
    t1_tokens = sum(s["tokens"] for s in t1_summaries)
    print(f"  T1 summaries: {len(t1_summaries)}, tokens: {t1_tokens}")
    
    # Total budget check
    total = SYSTEM_PROMPT_TOKENS + t0_tokens + t1_tokens
    fits = total < MAX_CONTEXT
    print(f"  Total: system({SYSTEM_PROMPT_TOKENS}) + T0({t0_tokens}) + T1({t1_tokens}) = {total}")
    print(f"  Budget: {MAX_CONTEXT} tokens")
    print(f"  Fits: {'PASS' if fits else 'FAIL'} ({total}/{MAX_CONTEXT})")
    
    # Working space remaining
    working = MAX_CONTEXT - total
    print(f"  Working space for T2 reads: {working} tokens")
    
    results = {
        "t0_entries": len(t0_entries),
        "t0_tokens": t0_tokens,
        "t1_summaries": len(t1_summaries),
        "t1_tokens": t1_tokens,
        "system_prompt_tokens": SYSTEM_PROMPT_TOKENS,
        "total_tokens": total,
        "max_context": MAX_CONTEXT,
        "fits_in_budget": fits,
        "working_space_tokens": working,
    }
    
    # Save report
    REPORT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"  Report: {REPORT}")
    
    # Check: all T1 summaries have >=3 meaningful words (quality check)
    # Very short files (INDEX, stubs) naturally produce short summaries - that's fine
    quality_pass = all(len(s["summary"].split()) >= 3 for s in t1_summaries)
    print(f"  T1 quality (>=3 words each): {'PASS' if quality_pass else 'FAIL'}")
    
    # Final verdict
    all_pass = fits and quality_pass
    print(f"\nResult: {'PASS' if all_pass else 'FAIL'}")
    return all_pass

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = run_selftest()
        sys.exit(0 if ok else 1)
    else:
        print("Usage: python knowledge_tiering.py --selftest")
