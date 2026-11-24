"""Idle Maintenance Rotation Table - role-specific tasks for idle/maintenance passes.

Replaces the generic (a)(b)(c)(d) menu with concrete per-role, per-weekday tasks.
Source spec: memory/ops/idle-maintenance-rotation-2026-11-24.md

Usage:
    from idle_rotation import get_idle_task
    task = get_idle_task("Builder")  # returns the task for today's weekday
"""
import datetime

# Weekday index: Monday=0 ... Friday=4 (weekend falls back to Friday)
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]

# Rotation table: role -> [Mon, Tue, Wed, Thu, Fri]
ROTATION = {
    "Orchestrator": [
        "Validate agents.json aliases resolve (probe each model endpoint)",
        "Check TODO.md sync with /api/goals SSOT",
        "Review blocker log for stale entries >72h",
        "Audit goal files for format consistency",
        "Generate fleet placement snapshot + diff vs prior day",
    ],
    "Researcher": [
        "Run KB freshness scan, flag leaves >3d stale",
        "Cross-check 5 random citations in decision-log.jsonl",
        "Update open-questions log with any newly answerable items",
        "Verify dictionary_*.json coverage of last cycle\'s key terms",
        "Measure retrieval accuracy on 3 held-out queries",
    ],
    "Verifier": [
        "Run one regression self-test from prior cycle (pick oldest)",
        "Check evidence leaves for phantom artifact paths",
        "Validate that /api/fleet/cockpit response <5s",
        "Run pointer integrity check (dangling/orphan/stale)",
        "Spot-check 3 random verified claims against their artifacts",
    ],
    "Scribe": [
        "Compress last auto-loop pass into 1-line decision + open items",
        "Check runbooks for stale commands (do they still match current file layout?)",
        "Update memory/scribe/MEMORY.md hot state",
        "Review cross-talk for unresolved questions needing synthesis",
        "Generate a 3-sentence \"state of the fleet\" summary",
    ],
    "Designer": [
        "Run WCAG contrast check on cockpit panels (wcag_contrast_check.py)",
        "Check UI asset inventory for orphaned files in ui/",
        "Validate that app.css custom properties are all referenced",
        "Screenshot 1 viewport, flag layout overflow issues",
        "Review recent UI changes for consistency with design tokens",
    ],
    "Builder": [
        "Run one self-test from a prior cycle script (verify still passes)",
        "Check git status: any uncommitted changes >24h old?",
        "Validate that /api/fleet/cockpit endpoint responds <3s",
        "Scan for TODO/FIXME comments in code files not tracked as goals",
        "Verify model-swap scripts still work (dry-run mode)",
    ],
    "Archivist": [
        "Run kb_delta.py, verify output is valid JSON + <2KB",
        "Check citation integrity: 5 random pointers resolve",
        "Run freshness heatmap, flag any dir >3d stale",
        "Validate knowledge-index.json fact count matches prior day +/-5%",
        "Check auto-linker: are new leaves getting links?",
    ],
    "Mechanic": [
        "Probe all 4 hosts (ping + port check), log results",
        "Check load-trend for anomalies vs baseline",
        "Validate elev.py helper is responsive (<2s ping)",
        "Review schtasks snapshot: any tasks failing >3 consecutive runs?",
        "Run fleet_probe_v2.py, compare to prior snapshot",
    ],
}


def get_idle_task(role, weekday=None):
    """Return the specific maintenance task for a role on the given weekday.

    Args:
        role: agent name (case-insensitive match against ROTATION keys)
        weekday: 0=Mon..6=Sun (defaults to today). Weekend (5,6) maps to Fri (index 4).

    Returns:
        str: the task text, or None if role not found.
    """
    if weekday is None:
        weekday = datetime.date.today().weekday()
    # Map weekend to Friday
    idx = min(weekday, 4)
    # Case-insensitive role lookup
    for key in ROTATION:
        if key.lower() == role.lower():
            return ROTATION[key][idx]
    return None


def selftest():
    """Verify the rotation table is complete and lookup works."""
    assert len(ROTATION) == 8, "Expected 8 roles"
    for role, tasks in ROTATION.items():
        assert len(tasks) == 5, "%s has %d tasks (expected 5)" % (role, len(tasks))
        for t in tasks:
            assert len(t) > 10, "%s task too short: %r" % (role, t)
    # Test lookup
    assert get_idle_task("builder", 0) == ROTATION["Builder"][0]
    assert get_idle_task("BUILDER", 4) == ROTATION["Builder"][4]
    assert get_idle_task("Mechanic", 5) == ROTATION["Mechanic"][4]  # Sat -> Fri
    assert get_idle_task("Nonexistent") is None
    print("idle_rotation selftest: PASS (8 roles x 5 days, lookup OK)")


if __name__ == "__main__":
    selftest()
