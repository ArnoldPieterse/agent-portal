#!/usr/bin/env python3
"""cycle_rollback_test.py - Verifier G8 (cycle-15): crash-safety of the goal cycle transition.

Simulates a failed cycle transition in an isolated sandbox: the new-goal-file write
fails mid-sequence (3rd agent file). Verifies:
  1. old goals remain readable from the archive (copy per agent)
  2. NO partial state - every live goal file is still byte-identical to the original
  3. the error log identifies "step 3 of 5"
  4. GOAL_RESET_PENDING stays armed -> the transition is retryable

Usage:
  python cycle_rollback_test.py
"""
import importlib.util, io, json, shutil, sys, tempfile
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent.parent
cp = HERE / "goal_cycle_auto.py"
spec = importlib.util.spec_from_file_location("goal_cycle_auto", str(cp))
gc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gc)

REAL_GOALS = HERE / "memory" / "goals"
AGENT_IDS = list(gc.AGENT_IDS)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="rollback_"))
    sandbox_goals = tmp / "goals"
    sandbox_goals.mkdir()
    try:
        originals = {}
        for aid in AGENT_IDS:
            src = REAL_GOALS / f"{aid}.md"
            if not src.exists():
                continue
            dst = sandbox_goals / f"{aid}.md"
            shutil.copy2(src, dst)
            originals[aid] = dst.read_bytes()
        (sandbox_goals / "GOAL_RESET_PENDING.json").write_text(
            json.dumps({"armed": True, "run_id": "test-rollback", "cycle": 15}), encoding="utf-8")
        (tmp / "TODO.md").write_text("# TODO\n\n## Cycle 16\n(stub)\n", encoding="utf-8")

        # Point the module at the sandbox
        gc.GOALS_DIR = sandbox_goals
        gc.ARCHIVE_DIR = sandbox_goals / "archive"
        gc.TODO_FILE = tmp / "TODO.md"
        gc.PENDING_FILE = sandbox_goals / "GOAL_RESET_PENDING.json"

        # Inject: 3rd write into a goalstage_ dir raises (disk full mid-sequence)
        real_write_text = Path.write_text
        state = {"n": 0}
        def flaky_write_text(self, data, *a, **k):
            if self.parent.name.startswith("goalstage_"):
                state["n"] += 1
                if state["n"] == 3:
                    raise OSError(28, "Simulated disk full (injected at 3rd staged write)")
            return real_write_text(self, data, *a, **k)
        Path.write_text = flaky_write_text

        err_msg, out = None, io.StringIO()
        try:
            with redirect_stdout(out):
                gc.execute_cycle(dry_run=False)
        except Exception as e:
            err_msg = str(e)
        finally:
            Path.write_text = real_write_text

        # 1. Failure surfaced and identifies step 3 of 5
        assert err_msg is not None, "expected the transition to fail"
        assert "step 3 of 5" in err_msg, f"error log must identify step 3 of 5, got: {err_msg!r}"

        # 2. No partial state: every live goal file still byte-identical to original
        for aid, orig in originals.items():
            live = sandbox_goals / f"{aid}.md"
            assert live.exists(), f"live goal file missing after rollback: {aid}"
            got = live.read_bytes()
            assert got == orig, f"PARTIAL STATE: {aid}.md changed after failed transition"

        # 3. Old goals readable from the archive (copy per agent)
        arch_dirs = list((sandbox_goals / "archive").iterdir()) if (sandbox_goals / "archive").exists() else []
        assert arch_dirs, "no archive dir created before the failure point"
        adir = sorted(arch_dirs)[-1]
        for aid in originals:
            arc = adir / f"{aid}.md"
            assert arc.exists(), f"old goals not readable from archive: {arc}"
            assert arc.read_bytes() == originals[aid], f"archive copy differs from original: {aid}"

        # 4. Pending stays armed -> retryable
        pend = json.loads((sandbox_goals / "GOAL_RESET_PENDING.json").read_text(encoding="utf-8"))
        assert pend.get("armed") is True, "pending must remain armed after a failed transition"

        print(f"SELFTEST OK (injected failure at 3rd staged write; error log: 'step 3 of 5'; "
              f"{len(originals)} live files byte-identical; archive {adir.name} complete; pending still armed)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())