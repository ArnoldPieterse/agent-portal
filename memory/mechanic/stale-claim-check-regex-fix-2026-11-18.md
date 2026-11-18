# stale_claim_check.py regex fix - .json vs .jsonl false positives

Date: 2026-11-18 (auto-loop pass)
Agent: Mechanic

## Problem
`stale_claim_check.py` reported 157 MISSING artifacts, of which ~49 were false
positives caused by the regex alternation `(?:md|py|json|jsonl|...)` matching
`.json` as a prefix of `.jsonl` (regex tries alternatives left-to-right).

Example: text `memory/mechanic/chaos-drill-evidence.jsonl` was matched as
`memory/mechanic/chaos-drill-evidence.json` (stopping before the trailing `l`),
then reported MISSING because only the `.jsonl` file exists on disk.

## Fix
Reordered the alternation to put `jsonl` before `json`:
  BEFORE: `(?:md|py|json|jsonl|log|css|js|txt)`
  AFTER:  `(?:jsonl|md|py|json|log|css|js|txt)`

This ensures the longer extension is tried first. For a genuine `.json` file,
the `jsonl` alternative fails (no trailing `l`), then `json` matches correctly.

## Result
MISSING count: 157 -> 35 (122 false positives eliminated).
The remaining 35 are genuinely missing cited artifacts (stale refs in archived
goal files, deleted scripts, etc.) - real findings worth triaging.

## Runbook note
What broke: regex alternation order in stale_claim_check.py caused .json to match
as prefix of .jsonl, flooding the report with false MISSING entries.
What fixed it: moved `jsonl` before `json` in the ARTIFACT_RE alternation.
