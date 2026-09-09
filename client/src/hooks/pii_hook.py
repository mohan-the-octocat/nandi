#!/usr/bin/env python3
"""Antigravity Lifecycle Hook: Indian PII Regex & Algorithmic Guard."""

import os
import sys

# Ensure plugin root is in python path
plugin_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if plugin_root not in sys.path:
    sys.path.insert(0, plugin_root)

from src.governance.audit_logger import FSIAuditLogger
from src.hooks.hook_base import AntigravityHookBase
from src.pii_guard.detector import PIIDetector


def main() -> None:
    hook = AntigravityHookBase(hook_name="fsi-pii-guard")
    detector = PIIDetector()
    audit_logger = FSIAuditLogger()

    text_to_scan, source = hook.extract_text_to_scan()
    if not text_to_scan.strip():
        if hook.tool_call:
            hook.reply_allow("No actionable text in tool arguments")
        else:
            hook.reply_pre_invocation()
        return

    # Scan text for Indian PII
    report = detector.scan(text_to_scan, action_mode="BLOCK")

    if report.contains_pii and report.blocked_by_policy:
        # Format masked entities for audit log
        masked_list = [m.to_dict() for m in report.matches]
        violations = [f"{m.entity_name} ({m.masked_value})" for m in report.matches]

        audit_logger.log_event(
            hook_name="fsi-pii-guard",
            event_type="PRE_TOOL_USE" if hook.tool_call else "PRE_INVOCATION",
            decision="deny",
            reason=report.violation_summary,
            risk_score=0.90 if report.highest_severity and report.highest_severity.value == "CRITICAL" else 0.70,
            conversation_id=hook.conversation_id,
            step_idx=hook.step_idx,
            detected_violations=violations,
            masked_entities=masked_list,
            regulatory_frameworks=["RBI_MD_IT_2023", "SEBI_CSCRF_2024", "DPDP_ACT_2023"],
            caller_metadata={"source": source, "tool_name": hook.tool_name},
        )

        deny_reason = f"🚫 [RBI & SEBI Governance Block] {report.violation_summary}"
        if hook.tool_call:
            hook.reply_deny(deny_reason)
        else:
            hook.reply_pre_invocation(inject_message=deny_reason)

    # Clean execution
    if hook.tool_call:
        hook.reply_allow("Clean: No sensitive Indian PII detected")
    else:
        hook.reply_pre_invocation()


if __name__ == "__main__":
    main()
