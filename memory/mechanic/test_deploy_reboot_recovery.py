#!/usr/bin/env python3
"""Unit tests for deploy_reboot_recovery_all.py - validates command construction logic.

Runs IN SANDBOX (no schtasks COM needed): mocks subprocess to capture the exact
schtasks arguments that WOULD be sent, verifying they are correct.

Run: python memory/mechanic/test_deploy_reboot_recovery.py
"""
import sys, os, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

# Import the deploy script as a module
SCRIPT_PATH = Path(__file__).parent / "deploy_reboot_recovery_all.py"
sys.path.insert(0, str(SCRIPT_PATH.parent))
import importlib.util
spec = importlib.util.spec_from_file_location("deploy", SCRIPT_PATH)
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


class TestDeployLocal(unittest.TestCase):
    """Test deploy_local() command construction via mocked subprocess."""

    def test_create_command_correct(self):
        with patch.object(deploy.subprocess, "run") as mock_run:
            # First call = /create (success), second call = /query verify (success)
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="OK", stderr=""),
                MagicMock(returncode=0, stdout=f"TaskName: {deploy.TASK_NAME}\nStatus: Ready", stderr=""),
            ]
            result = deploy.deploy_local()

            # Verify the /create call had correct args
            create_call = mock_run.call_args_list[0]
            cmd = create_call[0][0]  # positional arg
            self.assertIn("/create", cmd)
            self.assertIn("/tn", cmd)
            self.assertIn(deploy.TASK_NAME, cmd)
            self.assertIn("/sc", cmd)
            self.assertIn("onstart", cmd)
            self.assertIn("/ru", cmd)
            self.assertIn("SYSTEM", cmd)
            self.assertIn("/rl", cmd)
            self.assertIn("HIGHEST", cmd)
            self.assertIn("/f", cmd)

            # Result should show registered + verified
            self.assertTrue(result["registered"])
            self.assertTrue(result["verified"])

    def test_create_failure_reported(self):
        with patch.object(deploy.subprocess, "run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="ERROR: Access denied")
            result = deploy.deploy_local()
            self.assertFalse(result["registered"])
            self.assertIn("Access denied", result["error"])


class TestVerifyLocal(unittest.TestCase):
    def test_task_exists(self):
        with patch.object(deploy.subprocess, "run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=f"TaskName: {deploy.TASK_NAME}\nStatus: Ready", stderr="")
            result = deploy.verify_local()
            self.assertTrue(result["verified"])

    def test_task_missing(self):
        with patch.object(deploy.subprocess, "run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="ERROR: Task does not exist")
            result = deploy.verify_local()
            self.assertFalse(result["verified"])


class TestDeployRemote(unittest.TestCase):
    def test_pywinrm_missing_returns_graceful_error(self):
        # Simulate pywinrm not installed
        with patch.dict(sys.modules, {"winrm": None}):
            result = deploy.deploy_remote("PALE", {"ip": "IP_PALE", "user": "pale", "pw": "x"})
            self.assertFalse(result["registered"])
            self.assertIn("pywinrm", result["error"])


class TestLogEntry(unittest.TestCase):
    def test_log_writes_valid_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_file = Path(tmp) / "test.jsonl"
            entry = {"ts": datetime.now(timezone.utc).isoformat(), "type": "test", "ok": True}
            # Monkey-patch LOG_FILE
            orig = deploy.LOG_FILE
            deploy.LOG_FILE = log_file
            try:
                deploy.log_entry(entry)
                with open(log_file) as f:
                    lines = f.readlines()
                self.assertEqual(len(lines), 1)
                parsed = json.loads(lines[0])
                self.assertEqual(parsed["type"], "test")
            finally:
                deploy.LOG_FILE = orig


if __name__ == "__main__":
    unittest.main(verbosity=2)
