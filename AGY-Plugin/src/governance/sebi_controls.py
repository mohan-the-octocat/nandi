"""SEBI Cybersecurity and Cyber Resilience Framework (CSCRF) Controls."""

from typing import Any, Dict, List


class SEBIComplianceController:
    """Evaluator for Securities and Exchange Board of India (SEBI) CSCRF (2024)."""

    SEBI_CONTROLS = {
        "SEBI-CSCRF-AI-01": {
            "title": "AI/ML Input Validation & Algorithmic Guardrails",
            "reference": "SEBI CSCRF 2024, Part III, Rule 6.2",
            "requirement": "Mandatory real-time input verification to prevent algorithmic exploitation, prompt injection, and unauthorized data leakage.",
            "target_entities": ["PROMPT_INJECTION", "JAILBREAK", "RESPONSIBLE_AI"],
        },
        "SEBI-CSCRF-DP-02": {
            "title": "Client Financial Data Protection",
            "reference": "SEBI CSCRF 2024, Part II, Rule 4.1",
            "requirement": "Protection of client PAN, Demat, Bank Account, and GSTIN identifiers from unauthorized AI prompt processing.",
            "target_entities": ["PAN", "GSTIN", "BANK_ACCOUNT_IN", "CIN_IN", "PASSPORT_IN"],
        },
        "SEBI-CSCRF-NET-03": {
            "title": "Malicious Network & URI Defense",
            "reference": "SEBI CSCRF 2024, Part II, Rule 5.3",
            "requirement": "Interception of unapproved external links, phishing vectors, and command-and-control URIs.",
            "target_entities": ["MALICIOUS_URIS"],
        },
        "SEBI-CSCRF-LOG-04": {
            "title": "Cryptographic Audit Preservation",
            "reference": "SEBI CSCRF 2024, Part IV, Rule 8.4",
            "requirement": "Immutable SHA-256 hashed audit preservation of all AI policy evaluations and security blocks.",
            "target_entities": ["AUDIT_PRESERVATION"],
        },
    }

    @classmethod
    def get_control_details(cls, control_id: str) -> Dict[str, Any]:
        return cls.SEBI_CONTROLS.get(control_id, {})

    @classmethod
    def map_violations_to_controls(cls, violations: List[str]) -> List[str]:
        matched = set()
        for v in violations:
            v_upper = v.upper()
            if any(k in v_upper for k in ["PAN", "GSTIN", "ACCOUNT", "CIN", "PASSPORT"]):
                matched.add("SEBI-CSCRF-DP-02")
            if any(k in v_upper for k in ["PROMPT INJECTION", "JAILBREAK", "RESPONSIBLE AI"]):
                matched.add("SEBI-CSCRF-AI-01")
            if any(k in v_upper for k in ["MALICIOUS", "PHISHING", "URI"]):
                matched.add("SEBI-CSCRF-NET-03")
        return sorted(list(matched))
