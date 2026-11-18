"""Scribe Goal #3 - Context Handoff Template Validator.

Usage: python memory/scribe/validate_handoff.py <handoff_file> [more_files...]
Exits 0 if all files pass, 1 if any fail.
Acceptance: 3 test handoffs pass validation; template covers all required fields.
"""
import os, re, sys
from datetime import datetime

AGENT_NAMES = ['Orchestrator', 'Researcher', 'Builder', 'Verifier', 'Designer', 'Archivist', 'Scribe', 'Mechanic']
REQUIRED_SECTIONS = ['Task', 'Completed Steps', 'Current State', 'Blockers', 'Next Action', 'Relevant Files']

def validate(filepath):
    errors = []
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Check From/To fields
    from_m = re.search(r'\*\*From:\*\*\s*(.+)', text)
    to_m = re.search(r'\*\*To:\*\*\s*(.+)', text)
    if not from_m:
        errors.append("Missing **From:** field")
    elif from_m.group(1).strip() not in AGENT_NAMES:
        errors.append(f"From '{from_m.group(1).strip()}' is not a valid agent name")
    if not to_m:
        errors.append("Missing **To:** field")
    elif to_m.group(1).strip() not in AGENT_NAMES:
        errors.append(f"To '{to_m.group(1).strip()}' is not a valid agent name")
    
    # Check Date
    date_m = re.search(r'\*\*Date:\*\*\s*(\d{4}-\d{2}-\d{2})', text)
    if not date_m:
        errors.append("Missing **Date:** field with YYYY-MM-DD format")
    else:
        try:
            datetime.strptime(date_m.group(1), '%Y-%m-%d')
        except ValueError:
            errors.append(f"Invalid date: {date_m.group(1)}")
    
    # Check required sections
    for section in REQUIRED_SECTIONS:
        if f'## {section}' not in text:
            errors.append(f"Missing section: ## {section}")
    
    # Check Completed Steps has content (at least one bullet or 'none')
    cs_m = re.search(r'## Completed Steps\s*\n(.*?)(?=\n## |\Z)', text, re.DOTALL)
    if cs_m:
        body = cs_m.group(1).strip()
        bullets = [l for l in body.split('\n') if l.strip().startswith('- ')]
        if not bullets and 'none' not in body.lower() and 'new' not in body.lower():
            errors.append("Completed Steps has no content (need at least one bullet or 'none'")
    
    # Check Relevant Files paths are relative
    rf_m = re.search(r'## Relevant Files\s*\n(.*?)(?=\n## |\Z)', text, re.DOTALL)
    if rf_m:
        for line in rf_m.group(1).split('\n'):
            path_m = re.match(r'\s*-\s+`([^`]+)`', line)
            if path_m:
                p = path_m.group(1)
                if os.path.isabs(p) or re.match(r'^[A-Za-z]:\\', p):
                    errors.append(f"Relevant Files path is absolute: {p}")
    
    # Check Next Action is concise (single sentence/bullet, not multi-paragraph)
    na_m = re.search(r'## Next Action\s*\n(.*?)(?=\n## |\Z)', text, re.DOTALL)
    if na_m:
        body = na_m.group(1).strip()
        non_empty_lines = [l for l in body.split('\n') if l.strip()]
        if len(non_empty_lines) > 3:
            errors.append(f"Next Action too long ({len(non_empty_lines)} lines); keep to 1-2 sentences")
    
    return errors

def main():
    if len(sys.argv) < 2:
        print("Usage: python memory/scribe/validate_handoff.py <handoff_file> [more_files...]")
        sys.exit(1)
    all_pass = True
    for fp in sys.argv[1:]:
        if not os.path.exists(fp):
            print(f"ERROR: {fp} not found")
            all_pass = False
            continue
        errors = validate(fp)
        status = "PASS" if not errors else "FAIL"
        if errors:
            all_pass = False
        print(f"\n{fp}: {status}")
        for e in errors:
            print(f"  - {e}")
    sys.exit(0 if all_pass else 1)

if __name__ == '__main__':
    main()
