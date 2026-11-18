# Evidence Hash Chain - Proof of Operation (2026-11-16)

**Goal #3: SHA256-chained verification log, tamper-evident from genesis to present.**

## Architecture
- File: `evidence_chain.jsonl` (append-only)
- Each entry: `{seq, ts, content, prev_hash, entry_hash}`
- `entry_hash = SHA256(prev_hash + "|" + content)`
- Genesis: `prev_hash = "0"*64`

## Proof Sequence (this run)
| Step | Action | Result |
|------|--------|--------|
| 1 | Build genesis (seq=0) | hash=236a9407d1407cc11cfab55c... |
| 2 | Append entry seq=1 | hash=c8fe1709b6ae79b858bf6df5... |
| 3 | Append entry seq=2 | hash=0c5e33f3a0a4b15c3c382a14... |
| 4 | Append entry seq=3 | hash=9a3658da80eeaeb76ee00f0f... |
| 5 | Validate intact chain | PASS (4/4 verified) |
| 6 | Tamper seq=1 content | — |
| 7 | Validate tampered chain | **FAIL at seq=1** (exact break point) |
| 8 | Restore + recompute hash | — |
| 9 | Validate restored chain | PASS (4/4 verified) |

## Verdict: PASS
Tamper-evident from genesis to present. Mutating any historical entry is detected
at the exact break point by `validate()`. Recovery = restore content + recompute hash.

Script: `evidence_hash_chain.py` (append/validate CLI)
Chain file: `evidence_chain.jsonl`
