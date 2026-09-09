"""Unit tests for Audit Logger, Hash Chaining, and Control Mappings."""

import os
import sys
import tempfile
import unittest

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
client_root = os.path.join(repo_root, "client")
if client_root not in sys.path:
    sys.path.insert(0, client_root)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
from src.governance.audit_logger import FSIAuditLogger
from src.governance.rbi_controls import RBIComplianceController
from src.governance.sebi_controls import SEBIComplianceController


class TestGovernance(unittest.TestCase):

    def test_audit_hash_chain_integrity(self):
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            logger = FSIAuditLogger(log_file_path=tmp_path, emit_to_stderr=False)
            
            # Log 3 events
            e1 = logger.log_event("hook_1", "PRE_INVOCATION", "allow", "Clean prompt", 0.0, "conv-1")
            e2 = logger.log_event("hook_2", "PRE_TOOL_USE", "deny", "PII Aadhaar detected", 0.9, "conv-1")
            e3 = logger.log_event("hook_3", "PRE_INVOCATION", "deny", "Jailbreak blocked", 0.95, "conv-1")

            self.assertEqual(e2.prev_event_hash, e1.event_hash)
            self.assertEqual(e3.prev_event_hash, e2.event_hash)

            # Re-instantiate logger and verify recovery
            logger2 = FSIAuditLogger(log_file_path=tmp_path, emit_to_stderr=False)
            self.assertEqual(logger2.last_hash, e3.event_hash)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_rbi_control_mapping(self):
        violations = ["Aadhaar Number (UIDAI) (XXXX-XXXX-1234)", "Card CVV ([REDACTED_CVV])"]
        controls = RBIComplianceController.map_violations_to_controls(violations)
        self.assertIn("RBI-ITG-SEC-01", controls)
        self.assertIn("RBI-DPSC-03", controls)

    def test_sebi_control_mapping(self):
        violations = ["Prompt Injection Attack", "Permanent Account Number (PAN)"]
        controls = SEBIComplianceController.map_violations_to_controls(violations)
        self.assertIn("SEBI-CSCRF-AI-01", controls)
        self.assertIn("SEBI-CSCRF-DP-02", controls)


if __name__ == "__main__":
    unittest.main()
