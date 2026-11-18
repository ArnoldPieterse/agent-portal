# stale_claim_check.py — suffix-fallback fix
Date: 2026-11-18 (Mechanic)
Problem: 131 MISSING flags, most caused by systematic .json vs .jsonl mismatch
Fix: added suffix-swap fallback in path resolution (.json ↔ .jsonl)
Result: 131 → 33 truly-missing artifacts (genuine gaps, not naming drift)
File: memory/ops/stale_claim_check.py (one block inserted after rabs construction)