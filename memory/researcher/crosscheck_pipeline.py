"""
crosscheck_pipeline.py — Cross-Check Pipeline (Researcher Goal #2)

Usage:
    python memory/researcher/crosscheck_pipeline.py <claim_text> [--evidence-file PATH]

For any Researcher finding/claim, generates 2 independent verification queries
(different search terms, different source types) and records agreement/disagreement.

Exit codes:
    0 = pipeline ran, evidence file written
    1 = error (missing args, etc.)
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def slugify(text: str) -> str:
    """Generate a short slug from claim text for file naming."""
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return slug[:60] or 'claim'


def generate_queries(claim: str) -> list[dict]:
    """
    Generate 2 independent verification queries for a claim.
    Strategy: 
      Query A — rephrase with synonyms (lexical variation, same source type)
      Query B — invert/contradict + broader context (different framing, different source type)
    """
    # Extract key terms (simple heuristic: words > 3 chars, not stopwords)
    stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at',
                 'to', 'for', 'of', 'and', 'or', 'but', 'that', 'this', 'it',
                 'its', 'with', 'from', 'by', 'as', 'be', 'has', 'have', 'had'}
    words = re.findall(r'\b\w{4,}\b', claim.lower())
    key_terms = [w for w in words if w not in stopwords][:5]

    # Query A: synonym-based rephrasing (same type: web articles)
    query_a = f"{' '.join(key_terms[:3])} definition verification"
    
    # Query B: inverted + broader context (different type: academic/technical docs)
    query_b = f"evidence against OR supporting: {' '.join(key_terms[1:4] or key_terms)}"

    return [
        {
            "id": "A",
            "type": "lexical_variation",
            "description": "Rephrased with synonyms; searches for corroborating web sources",
            "query": query_a,
        },
        {
            "id": "B",
            "type": "inversion_context",
            "description": "Inverted/contradictory framing; searches academic or technical documentation",
            "query": query_b,
        },
    ]


def assess_agreement(claim: str, queries: list[dict]) -> dict:
    """
    Heuristic agreement assessment (offline mode).
    In live mode this would call web_search for each query.
    For now, records the structure and marks as 'pending' with instructions.
    """
    return {
        "status": "pending",
        "agreement": None,  # will be filled after live search
        "notes": "Run with --live flag or integrate into agent loop for actual search results.",
        "queries_generated": len(queries),
    }


def write_evidence(claim: str, queries: list[dict], assessment: dict, 
                   evidence_path: Path) -> Path:
    """Write the cross-check evidence file."""
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    claim_hash = hashlib.sha256(claim.encode()).hexdigest()[:12]

    content = f"""# Cross-Check Evidence — {now}

## Claim
> {claim}

Claim hash: `{claim_hash}`

## Generated Verification Queries

### Query A ({queries[0]['type']})
- **Description:** {queries[0]['description']}
- **Query:** `{queries[0]['query']}`
- **Result:** (pending — run live search)

### Query B ({queries[1]['type']})
- **Description:** {queries[1]['description']}
- **Query:** `{queries[1]['query']}`
- **Result:** (pending — run live search)

## Agreement Assessment
- **Status:** {assessment['status']}
- **Agreement:** {assessment['agreement']}
- **Notes:** {assessment['notes']}

## Conclusion
(Pending live verification. Fill in after running both queries against web sources.)
"""
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(content, encoding='utf-8')
    return evidence_path


def main():
    parser = argparse.ArgumentParser(description="Cross-Check Pipeline for Researcher findings")
    parser.add_argument("claim", help="The claim/finding to verify")
    parser.add_argument("--evidence-file", type=Path, default=None,
                        help="Output path (default: auto-generated in memory/researcher/)")
    args = parser.parse_args()

    queries = generate_queries(args.claim)
    assessment = assess_agreement(args.claim, queries)

    if args.evidence_file:
        out_path = args.evidence_file
    else:
        slug = slugify(args.claim)
        date = datetime.now().strftime('%Y-%m-%d')
        out_path = Path("memory/researcher") / f"crosscheck-{slug}-{date}.md"

    write_evidence(args.claim, queries, assessment, out_path)
    
    # Also print JSON summary for programmatic use
    summary = {
        "claim": args.claim[:100],
        "queries": [{"id": q["id"], "query": q["query"], "type": q["type"]} for q in queries],
        "assessment": assessment,
        "evidence_file": str(out_path),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
