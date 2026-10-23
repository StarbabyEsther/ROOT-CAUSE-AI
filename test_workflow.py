
import unittest
from unittest.mock import patch, MagicMock

from workflow import run_workflow


class WorkflowTests(unittest.TestCase):

    def test_unknown_scenario_rejected(self):
        with self.assertRaises(ValueError):
            run_workflow("unknown_scenario")

    @patch("workflow.subprocess.run")
    def test_duplicate_workflow_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Completed",
            stderr=""
        )

        with patch("workflow.Path.unlink"), \
             patch("workflow.Path.exists", return_value=True), \
             patch("workflow.Path.read_text") as mock_read:

            mock_read.side_effect = [
                '{"verdict": "verified_fixed"}',
                '{"root_cause": "Duplicate transaction"}'
            ]

            result = run_workflow("duplicate_transaction")

        self.assertTrue(result["verified"])
        self.assertEqual(
            result["verification"]["verdict"],
            "verified_fixed"
        )

    @patch("workflow.subprocess.run")
    def test_refund_workflow_failure(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Repair failed"
        )

        with patch("workflow.Path.unlink"), \
             patch("workflow.Path.exists", return_value=False):

            result = run_workflow("incorrect_refund")

        self.assertFalse(result["verified"])

    @patch("workflow.subprocess.run")
    def test_blocked_execution_handled(self, mock_run):
        mock_run.side_effect = OSError(
            "Application Control policy blocked execution"
        )

        result = run_workflow("duplicate_transaction")

        self.assertFalse(result["verified"])
        self.assertIn("blocked", result["logs"])

        
    @patch("workflow.subprocess.run")
    def test_corrupted_verification_report(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Completed",
            stderr=""
        )

        with patch("workflow.Path.unlink"), \
             patch("workflow.Path.exists", return_value=True), \
             patch("workflow.Path.read_text", return_value="{invalid json"):

            result = run_workflow("duplicate_transaction")

        self.assertFalse(result["verified"])



if __name__ == "__main__":
    unittest.main()
