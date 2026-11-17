# Goal #6: XML parsing path added to schtask_dep_gen.py

Date: 2026-11-18
Agent: Mechanic

## What was done
Extended `memory/ops/schtask_dep_gen.py` with a second input mode: `--xml-dir`
scans a directory of Task Scheduler XML files (e.g. C:/Windows/System32/Tasks) and
parses them into the same task dict format as CSV mode.

Also added `--prev-snapshot` for diffing against a prior JSON output (useful when
the input source is XML rather than CSV).

## Test results (all PASS)
- 4 synthetic task XMLs parsed: state=Ready, type=TimeTrigger correctly extracted
- Week-2 with 5 tasks: FleetChaosDrill correctly flagged as ADDED in diff
- 4 dependency edges inferred from known task names
- No removals detected (correct)

## Files modified
- memory/ops/schtask_dep_gen.py (3.2 KB -> 5.3 KB, added parse_task_xml + parse_xml_dir)

## Remaining for closure
- Register weekly schtask on White (same COM wall blocker as goals #1/#2/#8)
- Two real weekly generations with correct diff (needs live task access)
- One test task addition flagged in production

## Runbook note
When COM wall blocks `schtasks /query`, use `--xml-dir C:/Windows/System32/Tasks`
(elevated) as alternative input. Script handles both namespace and non-namespace XML.