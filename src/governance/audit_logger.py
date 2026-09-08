"""Tamper-Resistant Structured Audit Logger for India FSI Compliance."""

import dataclasses
import datetime
import hashlib
import json
import os
import sys
import uuid
from typing import Any, Dict, List, Optional


@dataclasses.dataclass
class AuditEvent:
    """Immutable audit event record conforming to RBI & SEBI log preservation standards."""
    event_id: str
    timestamp_utc: str
    timestamp_ist: str
    conversation_id: str
    step_idx: Optional[int]
    hook_name: str
    event_type: str  # PRE_INVOCATION, PRE_TOOL_USE, etc.
    decision: str    # allow, deny, force_ask, ask
    reason: str
    risk_score: float
    detected_violations: List[str]
    masked_entities: List[Dict[str, Any]]
    regulatory_frameworks: List[str]
    caller_metadata: Dict[str, Any]
    prev_event_hash: str
    event_hash: str = ""

    def compute_hash(self, salt: str = "FSI_GRC_SALT_2026") -> str:
        payload = {
            "event_id": self.event_id,
            "timestamp_utc": self.timestamp_utc,
            "conversation_id": self.conversation_id,
            "step_idx": self.step_idx,
            "hook_name": self.hook_name,
            "decision": self.decision,
            "risk_score": self.risk_score,
            "detected_violations": self.detected_violations,
            "prev_event_hash": self.prev_event_hash,
            "salt": salt,
        }
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp_utc": self.timestamp_utc,
            "timestamp_ist": self.timestamp_ist,
            "conversation_id": self.conversation_id,
            "step_idx": self.step_idx,
            "hook_name": self.hook_name,
            "event_type": self.event_type,
            "decision": self.decision,
            "reason": self.reason,
            "risk_score": self.risk_score,
            "detected_violations": self.detected_violations,
            "masked_entities": self.masked_entities,
            "regulatory_frameworks": self.regulatory_frameworks,
            "caller_metadata": self.caller_metadata,
            "prev_event_hash": self.prev_event_hash,
            "event_hash": self.event_hash,
        }


class FSIAuditLogger:
    """Audit logger ensuring compliance with RBI Master Direction (2023) and SEBI CSCRF (2024)."""

    def __init__(
        self,
        log_file_path: Optional[str] = None,
        emit_to_stderr: bool = True,
        salt: str = "FSI_GRC_SALT_INDIA_2026",
    ):
        if not log_file_path:
            env_log_path = os.environ.get("FSI_AUDIT_LOG_PATH")
            if env_log_path:
                log_file_path = env_log_path
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                log_file_path = os.path.join(base_dir, "logs", "fsi_audit.log")

        self.log_file_path = log_file_path
        self.emit_to_stderr = emit_to_stderr
        self.salt = salt
        self.last_hash = "GENESIS_BLOCK_FSI_INDIA_0000000000000000"

        try:
            os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
        except OSError:
            pass
        self._recover_last_hash()

    def _recover_last_hash(self) -> None:
        """Reads the last line of the audit log to maintain hash chain continuity."""
        if not os.path.exists(self.log_file_path):
            return

        try:
            with open(self.log_file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    if last_line:
                        entry = json.loads(last_line)
                        self.last_hash = entry.get("event_hash", self.last_hash)
        except Exception:
            pass

    def log_event(
        self,
        hook_name: str,
        event_type: str,
        decision: str,
        reason: str,
        risk_score: float,
        conversation_id: str,
        step_idx: Optional[int] = None,
        detected_violations: Optional[List[str]] = None,
        masked_entities: Optional[List[Dict[str, Any]]] = None,
        regulatory_frameworks: Optional[List[str]] = None,
        caller_metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Records and persists an immutable audit event."""
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        ist_offset = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        now_ist = now_utc.astimezone(ist_offset)

        event = AuditEvent(
            event_id=f"FSI-{uuid.uuid4().hex[:12].upper()}",
            timestamp_utc=now_utc.isoformat(),
            timestamp_ist=now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
            conversation_id=conversation_id,
            step_idx=step_idx,
            hook_name=hook_name,
            event_type=event_type,
            decision=decision,
            reason=reason,
            risk_score=risk_score,
            detected_violations=detected_violations or [],
            masked_entities=masked_entities or [],
            regulatory_frameworks=regulatory_frameworks or ["RBI_MD_IT_2023", "SEBI_CSCRF_2024", "DPDP_ACT_2023"],
            caller_metadata=caller_metadata or {},
            prev_event_hash=self.last_hash,
        )

        event.event_hash = event.compute_hash(self.salt)
        self.last_hash = event.event_hash

        entry_json = json.dumps(event.to_dict())

        # Write to log file
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(entry_json + "\n")
        except OSError:
            pass

        # Emit to stderr if enabled
        if self.emit_to_stderr:
            sys.stderr.write(f"[FSI-AUDIT] {event.timestamp_ist} | {event.hook_name} | {decision.upper()} | Risk: {risk_score} | {reason}\n")
            sys.stderr.flush()

        return event
