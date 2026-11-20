
## Additional finding: Mechanic Goal 1 closure claim vs evidence

The goals file (mechanic.md bottom note, 03:4x UTC) claims "GOAL 1 CLOSED" but:
- Goal 1 text has NO `(verified:` marker; ledger correctly counts it as open.
- `winrm-legs.jsonl` entry at 15:52 UTC (same day) says: "Goal 1 remaining: live 4-host WinRM exec blocked by NTLM 401 on PALE/BLACK + TCP timeout on RED."
- The 03:4x note describes schtask registration (a sub-step), not the acceptance criterion ("remote command execution succeeds on all 4 hosts").

Assessment: The closure claim in the goals file is premature. The goal remains open per evidence. No ledger action needed; the absence of a verified marker is correct.
