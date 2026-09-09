"""Data structures and definitions for PII entities and detection results."""

import dataclasses
from enum import Enum
from typing import Any, Dict, List, Optional


class PIICategory(str, Enum):
    """Categories of Personally Identifiable Information."""
    NATIONAL_ID = "NATIONAL_ID"
    TAX_AND_FINANCIAL_ID = "TAX_AND_FINANCIAL_ID"
    BANKING_DATA = "BANKING_DATA"
    CARD_DATA = "CARD_DATA"
    AUTHENTICATION_DATA = "AUTHENTICATION_DATA"
    PAYMENT_IDENTIFIER = "PAYMENT_IDENTIFIER"
    CONTACT_INFO = "CONTACT_INFO"
    TRAVEL_DOCUMENT = "TRAVEL_DOCUMENT"
    LOCATION_DATA = "LOCATION_DATA"
    CORPORATE_IDENTIFIER = "CORPORATE_IDENTIFIER"


class PIISeverity(str, Enum):
    """Risk severity levels for PII leakage."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

    def __ge__(self, other: "PIISeverity") -> bool:
        order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        return order.get(self.value, 0) >= order.get(other.value, 0)

    def __gt__(self, other: "PIISeverity") -> bool:
        order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        return order.get(self.value, 0) > order.get(other.value, 0)


@dataclasses.dataclass
class PIIMatch:
    """Represents an individual PII entity match in text."""
    entity_type: str
    entity_name: str
    category: PIICategory
    severity: PIISeverity
    raw_value: str
    masked_value: str
    start_index: int
    end_index: int
    confidence: float
    checksum_valid: bool
    regulatory_frameworks: List[str] = dataclasses.field(default_factory=list)
    metadata: Dict[str, Any] = dataclasses.field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_type": self.entity_type,
            "entity_name": self.entity_name,
            "category": self.category.value,
            "severity": self.severity.value,
            "masked_value": self.masked_value,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "confidence": self.confidence,
            "checksum_valid": self.checksum_valid,
            "regulatory_frameworks": self.regulatory_frameworks,
            "metadata": self.metadata,
        }


@dataclasses.dataclass
class PIIDetectionReport:
    """Aggregated report of all PII entities detected in a given prompt or input."""
    contains_pii: bool
    matches: List[PIIMatch]
    total_matches: int
    highest_severity: Optional[PIISeverity]
    blocked_by_policy: bool
    violation_summary: str
    redacted_text: str
    scanned_length: int
    elapsed_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contains_pii": self.contains_pii,
            "total_matches": self.total_matches,
            "highest_severity": self.highest_severity.value if self.highest_severity else None,
            "blocked_by_policy": self.blocked_by_policy,
            "violation_summary": self.violation_summary,
            "redacted_text": self.redacted_text,
            "scanned_length": self.scanned_length,
            "elapsed_ms": self.elapsed_ms,
            "matches": [m.to_dict() for m in self.matches],
        }
