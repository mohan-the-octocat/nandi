#!/usr/bin/env python3
"""Antigravity Lifecycle Hook: Google Cloud Model Armor Guard."""

import os
import sys

# Ensure plugin root is in python path
plugin_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if plugin_root not in sys.path:
    sys.path.insert(0, plugin_root)

from src.governance.audit_logger import FSIAuditLogger
from src.hooks.hook_base import AntigravityHookBase
from src.model_armor.client import ModelArmorClient
from src.model_armor.policy_evaluator import ModelArmorPolicyEvaluator


def main() -> None:
    hook = AntigravityHookBase(hook_name="fsi-model-armor-guard")
    client = ModelArmorClient()
    evaluator = ModelArmorPolicyEvaluator()
    audit_logger = FSIAuditLogger()

    text_to_scan, source = hook.extract_text_to_scan()
    if not text_to_scan.strip():
        if hook.tool_call:
            hook.reply_allow("No actionable text in tool arguments")
        else:
            hook.reply_pre_invocation()
        return

    # Call Model Armor Sanitize API
    response = client.sanitize_user_prompt(text_to_scan)
    eval_report = evaluator.evaluate(response)

    if not eval_report.is_allowed:
        audit_logger.log_event(
            hook_name="fsi-model-armor-guard",
            event_type="PRE_TOOL_USE" if hook.tool_call else "PRE_INVOCATION",
            decision=eval_report.decision,
            reason=eval_report.reason,
            risk_score=eval_report.risk_score,
            conversation_id=hook.conversation_id,
            step_idx=hook.step_idx,
            detected_violations=eval_report.violations_detected,
            regulatory_frameworks=eval_report.rbi_compliance_codes + eval_report.sebi_compliance_codes,
            caller_metadata={"source": source, "tool_name": hook.tool_name, "latency_ms": eval_report.latency_ms},
        )

        deny_reason = f"🛡️ [Model Armor Security Gate] {eval_report.reason}"
        if hook.tool_call:
            if eval_report.decision == "force_ask":
                hook.reply_force_ask(deny_reason)
            else:
                hook.reply_deny(deny_reason)
        else:
            hook.reply_block_pre_invocation(deny_reason)

    # Clean execution
    if hook.tool_call:
        hook.reply_allow(eval_report.reason)
    else:
        hook.reply_pre_invocation()


if __name__ == "__main__":
    main()
