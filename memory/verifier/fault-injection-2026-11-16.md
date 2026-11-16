# Fault Injection Suite - 2026-11-16

**Generated:** 2026-11-16T06:03:20.828585+00:00

## Results: 5/5 PASS

| Scenario | Recovery Path | Status |
|---|---|---|
| FI-01 Partial write (crash mid-write) | corruption detected: Unterminated string starting at: line 1 column 10  | **PASS** |
| FI-02 Corrupted file (bit-flip) | corruption detected: Expecting ':' delimiter: line 1 column 23 (char 22 | **PASS** |
| FI-03 Malformed JSON (3 variants) | all 3 rejected with JSONDecodeError | **PASS** |
| FI-04 Dependency file missing (leg drop) | FileNotFoundError caught; graceful fallback path available | **PASS** |
| FI-05 Oversized input (2MB > 1MB limit) | size check: 2097152 > 1048576 -> would reject | **PASS** |

## Method
File-system level chaos: partial writes, bit-flips, malformed inputs, missing dependencies, resource limits.
No network required - all scenarios test local recovery paths.

**Verdict:** PASS
