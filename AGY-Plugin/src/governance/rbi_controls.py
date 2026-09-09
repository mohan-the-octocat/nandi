"""RBI Master Direction IT & Payment Security Governance Controls."""

from typing import Any, Dict, List


class RBIComplianceController:
    """Evaluator for Reserve Bank of India (RBI) Regulatory Frameworks."""

    RBI_CONTROLS = {
        "RBI-ITG-SEC-01": {
            "title": "Customer Data Protection & Privacy",
            "reference": "RBI Master Direction on IT Governance 2023, Chapter III, Para 11",
            "requirement": "Prevention of unauthorized disclosure of customer PII and sensitive financial data.",
            "target_entities": ["AADHAAR", "PAN", "BANK_ACCOUNT_IN", "CREDIT_DEBIT_CARD", "CARD_CVV", "UPI_VPA", "PHONE_IN"],
        },
        "RBI-ITG-SEC-02": {
            "title": "Adversarial Threat & AI Safety Defense",
            "reference": "RBI Master Direction on IT Governance 2023, Chapter III, Para 14",
            "requirement": "Automated security controls against prompt injection, jailbreak attacks, and malicious payloads.",
            "target_entities": ["PROMPT_INJECTION", "MALICIOUS_URIS", "CSAM", "TOXICITY"],
        },
        "RBI-DPSC-03": {
            "title": "Card Data Security & Non-Storage",
            "reference": "RBI Digital Payment Security Controls 2021, Section 4",
            "requirement": "Strict prohibition of raw PAN/CVV transmission and prompt exposure.",
            "target_entities": ["CREDIT_DEBIT_CARD", "CARD_CVV"],
        },
        "RBI-ITG-AUD-04": {
            "title": "Tamper-Resistant Audit Trail",
            "reference": "RBI Master Direction on IT Governance 2023, Chapter V, Para 22",
            "requirement": "7-year cryptographic log retention for automated system interactions.",
            "target_entities": ["AUDIT_TRAIL"],
        },
    }

    @classmethod
    def get_control_details(cls, control_id: str) -> Dict[str, Any]:
        return cls.RBI_CONTROLS.get(control_id, {})

    @classmethod
    def map_violations_to_controls(cls, violations: List[str]) -> List[str]:
        matched_controls = set()
        for v in violations:
            v_upper = v.upper()
            if any(k in v_upper for k in ["AADHAAR", "PAN", "ACCOUNT", "PHONE", "UPI"]):
                matched_controls.add("RBI-ITG-SEC-01")
            if any(k in v_upper for k in ["CARD", "CVV"]):
                matched_controls.add("RBI-DPSC-03")
                matched_controls.add("RBI-ITG-SEC-01")
            if any(k in v_upper for k in ["PROMPT INJECTION", "JAILBREAK", "MALICIOUS", "PHISHING", "RESPONSIBLE AI"]):
                matched_controls.add("RBI-ITG-SEC-02")
        return sorted(list(matched_controls))
