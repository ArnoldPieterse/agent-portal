---
date: 2026-11-17
suite: test-report-format-standard
pass: 1
fail: 48
total: 49
evidence_path: memory/verifier/test-report-standard.md
---
# Verifier Test Report Canonical Format (Cycle 3)

## Required YAML Frontmatter
| Field | Type | Description |
|-------|------|-------------|
| date | ISO-8601 | Timestamp of report generation |
| suite | string | Test suite name (kebab-case) |
| pass | int | Number of passing cases |
| fail | int | Number of failing cases |
| total | int | Total cases (= pass + fail) |
| evidence_path | path | Relative path to this file |

## Optional Fields
- agent: which agent authored/owns the report
- notes: freeform context

## Body Requirements
1. Must have an H1 or H2 heading
2. Must contain at least one result per case (line, table row, or section)
3. FAIL cases must include: claim stated, actual finding, root cause

## Lint Script
Run: `python memory/verifier/lint_reports.py` - checks all .md files in memory/verifier/ against this standard.

## Current Compliance
Scanned 49 candidate reports: 1 conform, 48 non-conform.
