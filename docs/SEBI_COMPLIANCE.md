# SEBI Cybersecurity & Cyber Resilience Framework (CSCRF 2024) Compliance Mapping

This document details the compliance architecture of **Nandi** for Securities and Exchange Board of India (SEBI) regulated entities, including Stock Brokers, Asset Management Companies (AMCs), Depositories, and Qualified RTAs.

---

## 1. SEBI CSCRF Control Mapping Matrix

| SEBI CSCRF Control ID | Control Description | Technical Enforcement in Antigravity | Audit Evidence |
| :--- | :--- | :--- | :--- |
| **SEBI-CSCRF-AI-01** | **Input Validation & Algorithmic Guardrails (Part III, Rule 6.2)**: Mandatory verification of inputs before processing by automated AI/ML models to prevent prompt injection and data poisoning. | `fsi-model-armor-guard` hook executing `SanitizeUserPrompt` on Google Cloud Model Armor API in `asia-south1`. | `AuditEvent.detected_violations` containing `PI_AND_JAILBREAK` score and confidence. |
| **SEBI-CSCRF-DP-02** | **Client Non-Public Financial Data (Part II, Rule 4.1)**: Protection of Client PAN, Demat Account ID, Bank Account Number, and GSTIN identifiers. | `fsi-pii-guard` hook validating PAN, GSTIN Mod-36 checksum, and Indian CBS account grammars. | `AuditEvent.masked_entities` with zero raw data exposure. |
| **SEBI-CSCRF-NET-03** | **Malicious Network & URI Defense (Part II, Rule 5.3)**: Automated interception of unapproved external links, phishing vectors, and command-and-control URIs. | Model Armor Malicious URI filter scanning prompt links against Google Threat Intelligence feeds. | Real-time `decision: deny` with blocked URI domain logged. |
| **SEBI-CSCRF-LOG-04** | **Cryptographic Audit Trail Preservation (Part IV, Rule 8.4)**: Preserving tamper-evident logs of all security evaluations with SHA-256 cryptographic hashing. | `FSIAuditLogger` maintaining unbroken SHA-256 hash chains across all prompt evaluations. | `grc_admin.py show-audit` verifying chain integrity. |

---

## 2. SEBI AI/ML Governance Checklist for Institutional Deployments

- [x] **Pre-Execution Guard**: Prompts and tool parameters are validated before dispatch to AI backends.
- [x] **Fail-Closed Architecture**: In the event of network disconnection, the security gateway defaults to `DENY`.
- [x] **Zero Raw PII Storage**: Audit logs record only format-preserved masked tokens (e.g. `ABXXXXX34F`).
- [x] **Domestic Data Residency**: Model Armor and DLP inspection configured for Indian GCP regions (`asia-south1` Mumbai / `asia-south2` Delhi).
- [x] **Multi-Lingual Threat Detection**: Protection extends across English and 7 major Indian scheduled languages.
