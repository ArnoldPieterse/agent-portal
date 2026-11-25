# WF3: CRM Data Entry Automation
## Input -> Output
- **Input**: `raw_contacts.json` — unstructured entries {name, email?, phone?, company?, source, notes}
  + `crm_schema.json` — field definitions (required, type, validation regex)
- **Output**:
  - `cleaned_records.json` — validated, normalized CRM records
  - `rejected.csv` — entries that failed validation with reason
  - `stats.md` — import summary (total, accepted, rejected, by-field error rates)

## Runbook
```bash
python memory/builder/stealth/wf3_crm_entry.py --input raw_contacts.json --schema crm_schema.json --output ./wf3_out/
```

## Cost Model (per run)
- Runtime: <1s for 500 contacts (regex + normalization, no API calls)
- Token cost: $0 (deterministic validation; NLP optional upgrade path)
- Human time saved: ~10 hrs/mo at $25/hr = $250/mo

## Acceptance Tests
1. All valid records pass through with correct field normalization
2. Records missing required fields rejected with specific reason
3. Email/phone formats normalized (lowercase, E.164)
4. Duplicate detection: same email+name flagged
5. Output files valid; stats.md counts match actual file line counts
