#!/usr/bin/env python3
"""
Auto-Cycle Trigger: monitors goal completion across all agent goal files.
When ALL goals reach 100%, fires the cycle reset procedure:
  1. Archive current cycle goal files to memory/goals/archive/
  2. Write trigger event to decision-log.jsonl
  3. Create a prompt file for Orchestrator (new cycle kickoff)

Supports --dry-run, --simulate (force 100%), and --status.
"""
import json
import os
import re
import shutil
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GOALS_DIR = os.path.join(BASE, 'memory', 'goals')
ARCHIVE_DIR = os.path.join(GOALS_DIR, 'archive')
DECISION_LOG = os.path.join(BASE, 'decision-log.jsonl')
PROMPT_DIR = os.path.join(BASE, 'memory', 'orchestrator')

# Primary agent goal files (the ones that count for cycle completion)
PRIMARY_GOAL_FILES = [
    'archivist.md', 'builder.md', 'designer.md', 'mechanic.md',
    'orchestrator.md', 'researcher.md', 'scribe.md', 'verifier.md'
]

TRIGGER_MARKER = os.path.join(GOALS_DIR, '.cycle_trigger_fired')
FLEET_MODE_PATH = os.path.join(BASE, 'memory', 'ops', 'fleet-mode.json')


def _read_cycle_estimate():
    """Read the cycle_estimate block from fleet-mode.json (written by
    memory/orchestrator/cycle_estimator.py). Returns dict or None. The trigger
    surfaces this so its timing/visibility is informed by the estimator."""
    try:
        with open(FLEET_MODE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f).get('cycle_estimate')
    except (OSError, json.JSONDecodeError):
        return None


def parse_goal_status(filepath):
    """Parse a goal file and return (total_goals, verified_count)."""
    if not os.path.isfile(filepath):
        return 0, 0
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    total = 0
    verified = 0
    for line in content.split('\n'):
        stripped = line.strip()
        # Match numbered goal lines like "1. **Goal**" or "1. Goal"
        if re.match(r'^\d+\.\s', stripped):
            total += 1
            if '(verified:' in stripped or '(pointer:' in stripped:
                verified += 1
    return total, verified


def check_all_goals():
    """Check all primary goal files. Returns list of (agent, total, verified)."""
    results = []
    for fname in PRIMARY_GOAL_FILES:
        path = os.path.join(GOALS_DIR, fname)
        agent = fname.replace('.md', '')
        total, verified = parse_goal_status(path)
        results.append((agent, total, verified))
    return results


def is_all_complete(results):
    """Check if all agents have 100% goal completion."""
    for agent, total, verified in results:
        if total == 0:
            continue  # skip empty files
        if verified < total:
            return False
    return True


def log_decision(event_type, detail):
    """Append an entry to decision-log.jsonl."""
    entry = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'agent': 'builder',
        'type': event_type,
        'detail': detail,
        'outcome': 'success'
    }
    with open(DECISION_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')
    return entry


def archive_cycle(cycle_label):
    """Archive current goal files to memory/goals/archive/ with timestamp prefix."""
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    archived = []
    for fname in PRIMARY_GOAL_FILES:
        src = os.path.join(GOALS_DIR, fname)
        if not os.path.isfile(src):
            continue
        # Add timestamp to avoid overwriting previous archives
        agent = fname.replace('.md', '')
        dest_name = f"{agent}-{cycle_label}.md"
        dest = os.path.join(ARCHIVE_DIR, dest_name)
        shutil.copy2(src, dest)
        archived.append(dest_name)
    return archived


def create_orchestrator_prompt(cycle_label, results):
    """Create a prompt file for Orchestrator to plan the next cycle."""
    os.makedirs(PROMPT_DIR, exist_ok=True)
    prompt_path = os.path.join(PROMPT_DIR, f'cycle_kickoff_{cycle_label}.md')
    lines = [
        f"# Cycle Kickoff Prompt - {cycle_label}",
        "",
        f"Generated: {datetime.utcnow().isoformat()}Z by auto_cycle_trigger.py",
        "",
        "Previous cycle completion summary:",
        ""
    ]
    for agent, total, verified in results:
        pct = (verified / total * 100) if total > 0 else 0
        lines.append(f"- {agent}: {verified}/{total} ({pct:.0f}%)")
    lines += [
        "",
        "Action required: Generate new cycle goals for all agents based on",
        "the round topic and remaining work. Update memory/goals/*.md files.",
        ""
    ]
    with open(prompt_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    return prompt_path


def already_fired():
    """Check if the trigger has already fired (prevents double-trigger)."""
    return os.path.isfile(TRIGGER_MARKER)


def mark_fired(cycle_label, results):
    """Write the trigger marker to prevent re-firing."""
    data = {
        'fired_at': datetime.utcnow().isoformat() + 'Z',
        'cycle_label': cycle_label,
        'completion': {a: f'{v}/{t}' for a, t, v in results}
    }
    with open(TRIGGER_MARKER, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def run(simulate=False, dry_run=False):
    """Main trigger logic."""
    print("=== Auto-Cycle Trigger ===")
    print(f"Mode: {'DRY-RUN' if dry_run else 'LIVE'} | Simulate: {simulate}")

    # Check double-trigger guard
    if already_fired():
        with open(TRIGGER_MARKER, 'r', encoding='utf-8') as f:
            marker = json.load(f)
        print(f"ALREADY FIRED at {marker['fired_at']} (cycle: {marker['cycle_label']})")
        print("No action taken (double-trigger prevention).")
        return {'status': 'already_fired', 'action': None}

    # Check goal completion
    results = check_all_goals()
    total_goals = sum(t for _, t, _ in results)
    total_verified = sum(v for _, _, v in results)
    print(f"\nGoal status: {total_verified}/{total_goals} verified")
    for agent, total, verified in results:
        pct = (verified / total * 100) if total > 0 else 0
        status = 'OK' if (total == 0 or verified >= total) else 'INCOMPLETE'
        print(f"  {agent:15s}: {verified}/{total} ({pct:.0f}%) [{status}]")

    all_complete = is_all_complete(results)
    if simulate:
        print("\n[SIMULATE] Forcing 100% completion for test.")
        all_complete = True

    # Surface estimator's cycle_estimate so trigger timing/visibility uses it (goal #2 wiring)
    est = _read_cycle_estimate()
    if est:
        print(f"\nCycle estimate: ~{est.get('estimate_h')}h remaining, "
              f"estimated completion {est.get('estimated_completion')} (confidence={est.get('confidence')})")

    if not all_complete:
        print(f"\nNOT TRIGGERED: {total_verified}/{total_goals} goals complete.")
        return {'status': 'not_ready', 'action': None, 'progress': f'{total_verified}/{total_goals}',
                'cycle_estimate': est}

    # Fire the trigger
    cycle_label = datetime.now().strftime('%Y-%m-%d')
    print(f"\n*** TRIGGER FIRED: All goals complete. Starting cycle reset ***")

    if dry_run:
        print("[DRY-RUN] Would archive, log decision, create prompt.")
        return {'status': 'triggered_dry', 'action': 'dry_run'}

    # Step 1: Archive
    archived = archive_cycle(cycle_label)
    print(f"Archived {len(archived)} files to memory/goals/archive/")

    # Step 2: Log decision
    entry = log_decision('cycle_trigger', {
        'cycle_label': cycle_label,
        'completion': {a: f'{v}/{t}' for a, t, v in results},
        'archived_files': archived
    })
    print(f"Decision logged: {entry['timestamp']}")

    # Step 3: Create orchestrator prompt
    prompt_path = create_orchestrator_prompt(cycle_label, results)
    print(f"Orchestrator prompt created: {os.path.relpath(prompt_path, BASE)}")

    # Step 4: Mark as fired
    mark_fired(cycle_label, results)
    print(f"Trigger marker written.")

    return {'status': 'triggered', 'action': 'cycle_reset', 'archived': archived, 'prompt': prompt_path,
            'cycle_estimate': est}


def status():
    """Show current trigger status."""
    if already_fired():
        with open(TRIGGER_MARKER, 'r', encoding='utf-8') as f:
            print(f"Trigger FIRED: {json.dumps(json.load(f), indent=2)}")
    else:
        print("Trigger NOT yet fired.")
    results = check_all_goals()
    total_g = sum(t for _, t, _ in results)
    total_v = sum(v for _, _, v in results)
    print(f"Progress: {total_v}/{total_g} goals verified")


if __name__ == '__main__':
    args = sys.argv[1:]
    if '--status' in args:
        status()
    elif '--simulate' in args:
        dry = '--dry-run' in args
        run(simulate=True, dry_run=dry)
    else:
        dry = '--dry-run' in args
        run(simulate=False, dry_run=dry)
